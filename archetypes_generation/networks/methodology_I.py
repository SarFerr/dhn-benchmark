# methodology_I.py
#
# METHODOLOGY I — PURPOSE-DRIVEN DESIGN OF SYNTHETIC DHN BENCHMARK NETWORKS
#
# Networks are built from prescribed rules, in the spirit of the IEEE test feeders:
#   Rule 1  number of substations                       (fixed by the user)
#   Rule 2  pipe lengths sampled from U[l_min, l_max]   (reproducible random seed)
#   Rule 3  prescribed topology, obtained by nesting:
#             radial  — the reference tree given by the user                    (L = 0)
#             ring    — radial + one closing pipe between two branches          (L = 1)
#             meshed  — ring + straight pipes between opposite sides of the ring (L > 1)
#
# Pipe lengths are sampled in the order of the pipe list. Node coordinates are derived from
# the sampled lengths and from a direction assigned to the pipes that reach a new node.
# Optional alignment constraints (e.g. to obtain a rectangular ring) move given nodes, and
# every node downstream of them, to a prescribed coordinate.
# Two length modes:
#   "geometric" — pipe length = euclidean distance between the end nodes (consistent layout)
#   "sampled"   — pipe length = sampled value; the layout is a schematic drawing
#
# Two ways of building a network:
#   build_from_coordinates(...)  the user prescribes the coordinates of every node; pipe
#                                lengths are the euclidean distances (used for the THV archetypes)
#   build_network(...)           lengths sampled from U[l_min, l_max] and directions (Rule 2 above)
#
# Main functions
#   build_from_coordinates(...)  nodes, pipes and lengths from prescribed coordinates
#   build_network(...)           nodes, pipes and lengths from sampled lengths and directions
#   design_loads(...)            design heat load of every pipe, used to select the pipe diameter
#                                ("half" or "tree" rule for looped networks)
#
# Example
#   from archetypes_generation.networks.methodology_I import build_network, design_loads
#
#   E, S = (1, 0), (0, 1)
#   edges = [("src", "a"), ("a", "sub1"), ("a", "b"), ("b", "sub2")]
#   dirs  = {("src", "a"): E, ("a", "sub1"): S, ("a", "b"): E, ("b", "sub2"): S}
#   net   = build_network(edges, dirs, seed=42)
#   loads = design_loads(net, q_peak_w=175e3, heat_loss_factor=1.05)
#
# Conventions: x to the east, y to the south (y axis pointing down), lengths in metres.

import itertools
import math
import random

import networkx as nx

TOPOLOGIES = ("radial", "ring", "meshed")

# Unit directions (x to the east, y to the south)
E, W, S, N = (1, 0), (-1, 0), (0, 1), (0, -1)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _place(edge_list, directions, lengths, source, fixed=None, digits=None):
    """Coordinates from lengths and directions; `fixed` overrides the position of given
    nodes, and every node downstream of them follows. Pipes between two nodes that are
    already placed (loop-closing pipes) do not move any node."""
    rnd = (lambda x: x) if digits is None else (lambda x: round(x, digits))
    fixed, pos = fixed or {}, {source: (0, 0)}
    for u, v in edge_list:
        if u in pos and v in pos:
            continue
        if u not in pos:
            raise ValueError(f"Pipe ({u}, {v}) is listed before its upstream node {u} is placed.")
        if (u, v) not in directions:
            raise ValueError(f"No direction given for pipe ({u}, {v}).")
        dx, dy = directions[(u, v)]
        x = pos[u][0] if dx == 0 else rnd(pos[u][0] + dx * lengths[(u, v)])
        y = pos[u][1] if dy == 0 else rnd(pos[u][1] + dy * lengths[(u, v)])
        pos[v] = fixed.get(v, (x, y))
    return pos


def _ray_hit(p, d, a, b):
    """Intersection of the ray p + t d (t > 0) with segment a-b: (t, point) or None."""
    (px, py), (dx, dy), (ax, ay), (bx, by) = p, d, a, b
    ex, ey = bx - ax, by - ay
    den = dx * ey - dy * ex
    if abs(den) < 1e-9:
        return None
    t = ((ax - px) * ey - (ay - py) * ex) / den
    s = ((ax - px) * dy - (ay - py) * dx) / den
    return (t, (px + t * dx, py + t * dy)) if t > 1e-6 and -1e-9 <= s <= 1 + 1e-9 else None


def _split(edges, e, n):
    i = edges.index(e)
    return edges[:i] + [(e[0], n), (n, e[1])] + edges[i + 1:]


def _crosses(pos, e, f):
    """True if two pipes cross (pipes sharing an end node do not cross)."""
    if set(e) & set(f):
        return False
    (p1, p2), (p3, p4) = (pos[e[0]], pos[e[1]]), (pos[f[0]], pos[f[1]])
    o = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    sgn = lambda x: (x > 1e-9) - (x < -1e-9)
    return (sgn(o(p1, p2, p3)) != sgn(o(p1, p2, p4)) and
            sgn(o(p3, p4, p1)) != sgn(o(p3, p4, p2)))


def _add_chords(pos, ring_edges, chords, is_sub, return_parent=False):
    """Straight pipes from the given nodes, in the given directions, up to the first
    distribution pipe they meet. Junctions are created where a chord meets a pipe (m1, m2, ...)
    and where two chords cross (x1, x2, ...); a chord ending on an existing node uses it.
    With return_parent=True also returns a dict final pipe -> pipe it comes from (an input
    pipe for the pieces of a split pipe, the whole chord (node, end) for the chord pieces)."""
    edges, chord_segs = list(ring_edges), []
    parent = {e: e for e in edges}
    for k, (node, d) in enumerate(chords, start=1):
        hits = [(h[0], h[1], e) for e in edges if node not in e and not is_sub(e[1])
                for h in [_ray_hit(pos[node], d, pos[e[0]], pos[e[1]])] if h]
        if not hits:
            raise ValueError(f"The chord from {node} does not meet the ring.")
        _, q, e = min(hits)
        end = next((n for n in e if math.dist(pos[n], q) < 1.0), None)
        if end is None:
            end = f"m{k}"
            pos[end] = (round(q[0], 1), round(q[1], 1))
            edges = _split(edges, e, end)
            parent[(e[0], end)] = parent[(end, e[1])] = parent.pop(e)
        chord_segs.append((node, end))
    xk, pieces = 0, {c: [c] for c in chord_segs}
    for c1, c2 in itertools.combinations(chord_segs, 2):
        for e1 in list(pieces[c1]):
            for e2 in list(pieces[c2]):
                p, q = pos[e1[0]], pos[e1[1]]
                h = _ray_hit(p, (q[0] - p[0], q[1] - p[1]), pos[e2[0]], pos[e2[1]])
                if h and h[0] < 1 - 1e-6 and len(set(e1) | set(e2)) == 4:
                    xk += 1
                    x = f"x{xk}"
                    pos[x] = (round(h[1][0], 1), round(h[1][1], 1))
                    pieces[c1] = _split(pieces[c1], e1, x)
                    pieces[c2] = _split(pieces[c2], e2, x)
    parent.update({e: c for c in chord_segs for e in pieces[c]})
    edges = edges + [e for c in chord_segs for e in pieces[c]]
    return (edges, parent) if return_parent else edges


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_network(edge_list, directions, topology=None, *,
                  source="src", substation_prefix="sub",
                  ring_closure=None, chords=None, align=None,
                  length_mode="geometric", length_range=(100.0, 200.0), seed=42,
                  digits=None, expected_loops=None):
    """Build a Methodology I network.

    Parameters
    ----------
    edge_list         : list of (from_node, to_node) in sampling order. Each pipe that reaches
                        a new node needs a direction; pipes between nodes already placed
                        (loop-closing pipes) do not.
    directions        : dict (from_node, to_node) -> unit vector (dx, dy)
                        (use the constants E, W, S, N of this module).
    topology          : None (network as given by edge_list), or "radial", "ring", "meshed"
                        to obtain nested topologies from a radial edge_list:
                        ring = radial + ring_closure; meshed = ring + chords.
    source            : id of the source node (placed at the origin).
    substation_prefix : nodes whose id starts with this prefix are substations.
    ring_closure      : (node_a, node_b) — closing pipe added for "ring" and "meshed".
    chords            : list of (node, direction) — straight pipes added for "meshed", from the
                        node up to the first distribution pipe they meet.
    align             : list of (node, axis, reference) with axis "x" or "y": the node takes
                        the coordinate of the reference node along that axis (evaluated on
                        the unconstrained layout); downstream nodes follow.
    length_mode       : "geometric" (length = distance between the end nodes) or
                        "sampled" (length = sampled value, layout as a schematic drawing).
    length_range      : (l_min, l_max) of the uniform length distribution [m] (Rule 2).
    seed              : random seed (Rule 2).
    digits            : rounding of the coordinates (None = no rounding).
    expected_loops    : if given, the number of independent loops L is checked against it.

    Returns
    -------
    dict with
      nodes      : list of (node_id, node_type, x_m, y_m); node_type in
                   {"source", "junction", "substation"}
      edges      : list of (from_node, to_node), in the order of edge_list (added pipes last)
      lengths    : dict (from_node, to_node) -> length [m]
      positions  : dict node_id -> (x_m, y_m)
      sampled    : dict of the sampled lengths, in sampling order
      geometric  : dict of the pipes whose length differs from the sampled value
                   (geometric mode only)
      loops      : number of independent loops L = E - N + 1
      source     : id of the source node
      added      : pipes added to the radial edge_list by the topology (closing pipe, chords
                   and their pieces); empty for topology=None or "radial"
    """
    if topology not in (None,) + TOPOLOGIES:
        raise ValueError(f"topology must be None or one of {TOPOLOGIES}")
    if topology in ("ring", "meshed") and ring_closure is None:
        raise ValueError("ring and meshed networks need ring_closure")
    if topology == "meshed" and not chords:
        raise ValueError("meshed networks need chords")
    if length_mode not in ("geometric", "sampled"):
        raise ValueError('length_mode must be "geometric" or "sampled"')

    rnd = random.Random(seed)
    sampled = {e: round(rnd.uniform(*length_range), 1) for e in edge_list}

    pos = _place(edge_list, directions, sampled, source, digits=digits)
    if align:
        fixed = {}
        for node, axis, ref in align:
            x, y = fixed.get(node, pos[node])
            fixed[node] = (pos[ref][0], y) if axis == "x" else (x, pos[ref][1])
        pos = _place(edge_list, directions, sampled, source, fixed, digits=digits)

    is_sub = lambda n: str(n).startswith(substation_prefix)
    edges  = list(edge_list)
    parent = {e: e for e in edges}
    if topology in ("ring", "meshed"):
        edges = edges + [tuple(ring_closure)]
        parent[tuple(ring_closure)] = tuple(ring_closure)
    if topology == "meshed":
        edges, parent = _add_chords(pos, edges, chords, is_sub, return_parent=True)
    base  = set(edge_list)
    added = [e for e in edges if parent[e] not in base]     # closing pipe and chords (and their pieces)

    used  = list(dict.fromkeys(n for e in edges for n in e))
    ntype = lambda n: "source" if n == source else ("substation" if is_sub(n) else "junction")
    nodes = [(n, ntype(n), pos[n][0], pos[n][1]) for n in used]
    if length_mode == "sampled":
        missing = [e for e in edges if e not in sampled]
        if missing:
            raise ValueError(f"Pipes without a sampled length: {missing}")
        lengths = {e: sampled[e] for e in edges}
    else:
        lengths = {e: round(math.dist(pos[e[0]], pos[e[1]]), 1) for e in edges}

    # ---- checks ------------------------------------------------------------
    G = nx.Graph()
    G.add_edges_from(edges)
    loops = G.number_of_edges() - G.number_of_nodes() + 1
    if not nx.is_connected(G):
        raise ValueError("The network is not connected.")
    if expected_loops is not None and loops != expected_loops:
        raise ValueError(f"Expected L = {expected_loops}, got L = {loops}.")
    if topology == "radial" and loops != 0:
        raise ValueError("The radial network must be a tree.")
    if length_mode == "geometric":
        crossing = [(e, f) for e, f in itertools.combinations(edges, 2) if _crosses(pos, e, f)]
        if crossing:
            raise ValueError(f"Crossing pipes: {crossing}")

    geometric = ({} if length_mode == "sampled" else
                 {e: l for e, l in lengths.items() if e not in sampled or abs(l - sampled[e]) > 0.05})
    return {"nodes": nodes, "edges": edges, "lengths": lengths, "positions": pos,
            "sampled": sampled, "geometric": geometric, "loops": loops, "source": source,
            "added": added}


def build_from_coordinates(edge_list, positions, topology=None, *,
                           source="src", substation_prefix="sub",
                           ring_closure=None, chords=None, chord_end_names=None,
                           expected_loops=None):
    """Build a Methodology I network from prescribed node coordinates.

    The user places every node; the pipe length is the euclidean distance between its end
    nodes (consistent layout). Nested topologies are obtained from a radial edge_list as in
    build_network: ring = radial + ring_closure; meshed = ring + chords.

    Parameters
    ----------
    edge_list       : list of (from_node, to_node) of the radial base (supply flow direction).
    positions       : dict node_id -> (x_m, y_m) for every node of edge_list
                      (convention: x to the east, y to the south).
    topology        : None (network as given by edge_list), "radial", "ring" or "meshed".
    source          : id of the source node.
    substation_prefix : nodes whose id starts with this prefix are substations.
    ring_closure    : (node_a, node_b) — closing pipe added for "ring" and "meshed".
    chords          : list of (node, direction) — straight pipes added for "meshed", from the
                      node up to the first distribution pipe they meet (directions E, W, S, N).
                      Junctions are created where a chord meets a pipe and where two chords cross.
    chord_end_names : optional names of the junctions where the chords end, in the order of
                      `chords` (default m1, m2, ...); crossing junctions are named x1, x2, ...
    expected_loops  : if given, the number of independent loops L is checked against it.

    Returns
    -------
    dict with the same keys as build_network: nodes, edges, lengths, positions, sampled (empty),
    geometric (empty), loops, source, added (closing pipe, chords and their pieces).
    """
    if topology not in (None,) + TOPOLOGIES:
        raise ValueError(f"topology must be None or one of {TOPOLOGIES}")
    if topology in ("ring", "meshed") and ring_closure is None:
        raise ValueError("ring and meshed networks need ring_closure")
    if topology == "meshed" and not chords:
        raise ValueError("meshed networks need chords")
    missing = {n for e in edge_list for n in e} - set(positions)
    if missing:
        raise ValueError(f"Nodes without coordinates: {sorted(missing)}")

    is_sub = lambda n: str(n).startswith(substation_prefix)
    pos    = {n: tuple(p) for n, p in positions.items()}
    edges  = list(edge_list)
    parent = {e: e for e in edges}
    if topology in ("ring", "meshed"):
        edges = edges + [tuple(ring_closure)]
        parent[tuple(ring_closure)] = tuple(ring_closure)
    if topology == "meshed":
        edges, parent = _add_chords(pos, edges, chords, is_sub, return_parent=True)
        ren = {f"m{k}": nm for k, nm in enumerate(chord_end_names or [], start=1) if f"m{k}" in pos}
        clash = set(ren.values()) & (set(pos) - set(ren))
        if clash:
            raise ValueError(f"chord_end_names already used by other nodes: {sorted(clash)}")
        rn     = lambda e: (ren.get(e[0], e[0]), ren.get(e[1], e[1]))
        edges  = [rn(e) for e in edges]
        parent = {rn(e): rn(p) for e, p in parent.items()}
        pos    = {ren.get(n, n): p for n, p in pos.items()}
    base  = set(edge_list)
    added = [e for e in edges if parent[e] not in base]     # closing pipe and chords (and their pieces)

    used    = list(dict.fromkeys(n for e in edges for n in e))
    ntype   = lambda n: "source" if n == source else ("substation" if is_sub(n) else "junction")
    nodes   = [(n, ntype(n), pos[n][0], pos[n][1]) for n in used]
    lengths = {e: round(math.dist(pos[e[0]], pos[e[1]]), 1) for e in edges}

    # ---- checks ------------------------------------------------------------
    G = nx.Graph()
    G.add_edges_from(edges)
    loops = G.number_of_edges() - G.number_of_nodes() + 1
    if not nx.is_connected(G):
        raise ValueError("The network is not connected.")
    if expected_loops is not None and loops != expected_loops:
        raise ValueError(f"Expected L = {expected_loops}, got L = {loops}.")
    if topology == "radial" and loops != 0:
        raise ValueError("The radial network must be a tree.")
    if any(l <= 0 for l in lengths.values()):
        raise ValueError(f"Zero-length pipes: {[e for e, l in lengths.items() if l <= 0]}")
    crossing = [(e, f) for e, f in itertools.combinations(edges, 2) if _crosses(pos, e, f)]
    if crossing:
        raise ValueError(f"Crossing pipes: {crossing}")

    return {"nodes": nodes, "edges": edges, "lengths": lengths, "positions": pos,
            "sampled": {}, "geometric": {}, "loops": loops, "source": source, "added": added}


def design_loads(net, q_peak_w, heat_loss_factor=1.0, method="half", added=None, added_subs=2):
    """Design heat load [W] of every pipe of a Methodology I network.

    radial network : each pipe carries the peak load of the substations downstream of it.
    looped network, method = "half" : distribution pipes are sized on half of the total peak
                     load (the load is shared between at least two paths), service pipes on
                     one substation.
    looped network, method = "tree" : the network is seen as its radial base plus the added
                     pipes (closing pipe, chords). The pipes of the radial base, including
                     the pieces of a pipe split by a chord, carry the load of the substations
                     downstream of them in the radial base; the added pipes are sized on
                     `added_subs` substations.
    All loads are multiplied by the heat loss factor.

    Parameters
    ----------
    added      : pipes that are not part of the radial base (default: net["added"], filled by
                 build_network when the network is built with topology="ring" / "meshed").
                 Give them explicitly for a looped network built with topology=None.
    added_subs : number of substations used to size the added pipes ("tree" only).

    Returns a dict (from_node, to_node) -> design load [W], in the order of net["edges"].
    """
    if method not in ("half", "tree"):
        raise ValueError('method must be "half" or "tree"')
    subs = {n for n, t, _, _ in net["nodes"] if t == "substation"}
    if net["loops"] == 0 or method == "tree":
        added = set(map(tuple, net.get("added", []) if added is None else added))
        G = nx.Graph([e for e in net["edges"] if e not in added])
        if not (net["source"] in G and subs <= set(G) and nx.is_tree(G)):
            raise ValueError("The pipes without the added ones must form a tree that reaches every "
                             "substation: build the network with topology='ring'/'meshed' or pass `added`.")
        T = nx.bfs_tree(G, net["source"])
        loads = {}
        for u, v in net["edges"]:
            if (u, v) in added:
                loads[(u, v)] = round(added_subs * q_peak_w * heat_loss_factor, 1)
                continue
            down = v if T.has_edge(u, v) else u
            n_down = len(subs & (nx.descendants(T, down) | {down}))
            loads[(u, v)] = round(n_down * q_peak_w * heat_loss_factor, 1)
        return loads
    q_half = len(subs) * q_peak_w * heat_loss_factor / 2
    return {(u, v): round(q_peak_w * heat_loss_factor, 1) if v in subs else round(q_half, 1)
            for u, v in net["edges"]}
