#
# methodology_II.py
#
# METHODOLOGY II — ALGORITHMIC GENERATION OF SYNTHETIC DHN BENCHMARK NETWORKS
#
# In the spirit of the ACTIVSg and SimBench power-system benchmarks, a network is generated
# in three steps:
#   Step 1  synthetic urban district: blocks, centreline streets and substations
#           (DistrictGenerator)
#   Step 2  support street graph (StreetGraphBuilder)
#   Step 3  DHN layout routed along the streets: the substations and the source(s) are
#           projected onto the street graph and connected by a constrained Steiner tree
#           (ThermalNetworkBuilder, Algorithm 2 of Vieth et al. 2025)
#
# Helpers for exporting the generated network:
#   extract_nodes(tnb, dhn)                      node table and graph-node -> node-id map
#   downstream_substations(tnb, dhn, source)     substations downstream of every pipe
#
# Example
#   from archetypes_generation.networks.methodology_II import (
#       DistrictGenerator, StreetGraphBuilder, ThermalNetworkBuilder,
#       extract_nodes, downstream_substations)
#
#   district = DistrictGenerator(width=1200, height=800, rows=5, cols=7,
#                                n_substations=100, seed=42).generate()
#   streets  = StreetGraphBuilder(district).build()
#   tnb      = ThermalNetworkBuilder(streets, district, generator_pos=(50, 40))
#   tnb.build_routing_graph()
#   dhn      = tnb.constrained_steiner_tree(beta=1.0)
#   node_rows, node_id = extract_nodes(tnb, dhn)
#   pipes    = downstream_substations(tnb, dhn)     # [(from, to, n_downstream, length), ...]
#
# Note: the random generator of DistrictGenerator is the global `random` module, seeded
# with `seed` at construction, so that a given seed always gives the same district.
#
import math
import random
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Point, LineString
from networkx.algorithms.approximation import steiner_tree as nx_steiner_tree


# =====================================================================
# 1. DISTRICT GENERATOR
# =====================================================================
class DistrictGenerator:
    """
    Generates a synthetic urban district grid where roads are modelled as
    single-line centrelines to avoid double-pipe routing artefacts.

    Parameters
    ----------
    width, height    : footprint dimensions [m]
    rows, cols       : number of block rows/columns
    street_width     : uniform street width [m]
    n_substations    : total number of consumer substations
    block_variation  : relative variation of block dimensions (±fraction)
    perturbation     : max jitter on building position along frontage [m]
    seed             : random seed for full reproducibility
    """

    def __init__(self, width=1200, height=800, rows=5, cols=7,
                 street_width=15, n_substations=100,
                 block_variation=0.12, perturbation=5, seed=42):
        self.width           = width
        self.height          = height
        self.rows            = rows
        self.cols            = cols
        self.street_width    = street_width
        self.n_substations   = n_substations
        self.block_variation = block_variation
        self.perturbation    = perturbation
        self.seed            = seed

        random.seed(seed)
        self.blocks       = []
        self.buildings    = []
        self.street_nodes = {}
        self.street_edges = []
        self.street_graph = nx.Graph()

    # ------------------------------------------------------------------
    def random_partition(self, total, n):
        mean   = total / n
        values = [mean * (1 + random.uniform(-self.block_variation,
                                              self.block_variation))
                  for _ in range(n)]
        scale  = total / sum(values)
        values = [v * scale for v in values]
        values[-1] = total - sum(values[:-1])
        return values

    # ------------------------------------------------------------------
    def build_street_grid(self):
        usable_w = self.width  - (self.cols + 1) * self.street_width
        usable_h = self.height - (self.rows  + 1) * self.street_width

        self.block_widths  = self.random_partition(usable_w, self.cols)
        self.block_heights = self.random_partition(usable_h, self.rows)

        # Block boundary coordinates
        self.x = [0]
        for bw in self.block_widths:
            self.x.append(self.x[-1] + self.street_width)
            self.x.append(self.x[-1] + bw)

        self.y = [0]
        for bh in self.block_heights:
            self.y.append(self.y[-1] + self.street_width)
            self.y.append(self.y[-1] + bh)

        # Street centreline coordinates
        cx = [(self.x[i] + self.x[i+1]) / 2 if i+1 < len(self.x)
              else self.x[i] for i in range(0, len(self.x), 2)]
        cy = [(self.y[j] + self.y[j+1]) / 2 if j+1 < len(self.y)
              else self.y[j] for j in range(0, len(self.y), 2)]

        for i, x in enumerate(cx):
            for j, y in enumerate(cy):
                self.street_nodes[(i, j)] = (x, y)

        for i in range(len(cx) - 1):
            for j in range(len(cy)):
                self.street_edges.append(((i, j), (i+1, j)))
        for i in range(len(cx)):
            for j in range(len(cy) - 1):
                self.street_edges.append(((i, j), (i, j+1)))

        for node, pos in self.street_nodes.items():
            self.street_graph.add_node(node, pos=pos)
        for n1, n2 in self.street_edges:
            x1, y1 = self.street_nodes[n1]
            x2, y2 = self.street_nodes[n2]
            self.street_graph.add_edge(n1, n2,
                                       length=abs(x2-x1)+abs(y2-y1))

    # ------------------------------------------------------------------
    def build_blocks(self):
        block_id = 0
        for c in range(self.cols):
            for r in range(self.rows):
                x0 = self.x[2*c + 1]
                y0 = self.y[2*r + 1]
                self.blocks.append({
                    "id": block_id, "x": x0, "y": y0,
                    "col": c, "row": r,
                    "width":  self.block_widths[c],
                    "height": self.block_heights[r],
                    "area":   self.block_widths[c] * self.block_heights[r],
                })
                block_id += 1

    # ------------------------------------------------------------------
    def build_buildings(self):
        building_id = 0
        block_index = 0
        MARGIN  = self.street_width * 0.5
        MIN_GAP = 15.0

        for c in range(self.cols):
            for r in range(self.rows):
                block = self.blocks[block_index]
                x0, y0 = block["x"], block["y"]
                bw, bh  = block["width"], block["height"]

                available = []
                if r < self.rows - 1: available.append("N")
                if r > 0:             available.append("S")
                if c < self.cols - 1: available.append("E")
                if c > 0:             available.append("W")

                if not available:
                    block_index += 1
                    continue

                n = self._allocation[block_index]
                front_lens   = {"N": bw, "S": bw, "E": bh, "W": bh}
                avail_lens   = {s: front_lens[s] for s in available}
                total_len    = sum(avail_lens.values())
                sides_sorted = sorted(avail_lens, key=avail_lens.get,
                                      reverse=True)
                front_counts = {}
                assigned     = 0
                for i, side in enumerate(sides_sorted):
                    if i == len(sides_sorted) - 1:
                        front_counts[side] = n - assigned
                    else:
                        cnt = max(0, round(n * avail_lens[side] / total_len))
                        front_counts[side] = cnt
                        assigned += cnt

                for side, cnt in front_counts.items():
                    if cnt <= 0:
                        continue
                    if side in ("N", "S"):
                        axis_len, axis_start = bw, x0
                        fixed = y0 + bh - MARGIN if side == "N" \
                                else y0 + MARGIN
                    else:
                        axis_len, axis_start = bh, y0
                        fixed = x0 + bw - MARGIN if side == "E" \
                                else x0 + MARGIN

                    spacing = max(axis_len / (cnt + 1), MIN_GAP)
                    for k in range(cnt):
                        pos = axis_start + spacing * (k + 1)
                        pos += random.uniform(-self.perturbation,
                                              self.perturbation)
                        pos = max(axis_start + MIN_GAP,
                                  min(axis_start + axis_len - MIN_GAP, pos))
                        bx, by = (pos, fixed) if side in ("N", "S") \
                                  else (fixed, pos)
                        self.buildings.append({
                            "id": building_id,
                            "x": bx, "y": by,
                            "block": block["id"],
                        })
                        building_id += 1
                block_index += 1

    # ------------------------------------------------------------------
    def generate(self):
        self.build_street_grid()
        self.build_blocks()

        n_blocks    = len(self.blocks)
        avail_cnts  = []
        for idx in range(n_blocks):
            c, r = idx // self.rows, idx % self.rows
            cnt  = sum([r < self.rows-1, r > 0,
                        c < self.cols-1, c > 0])
            avail_cnts.append(max(cnt, 1))

        total_avail = sum(avail_cnts)
        raw         = [self.n_substations * a / total_avail
                       for a in avail_cnts]
        allocation  = [max(1, round(v)) for v in raw]
        diff        = self.n_substations - sum(allocation)
        for i in range(abs(diff)):
            allocation[i % n_blocks] += 1 if diff > 0 else -1
            allocation[i % n_blocks]  = max(0, allocation[i % n_blocks])

        self._allocation = allocation
        self.build_buildings()
        return self

    # ------------------------------------------------------------------
    def plot_district(self, ax=None, show=True, show_buildings=True):
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 9))
        ax.set_facecolor('#AAAAAA')
        colors = ['#F0EEE8', '#EDEAE0', '#F2F0EA', '#EDE8E0']
        for idx, b in enumerate(self.blocks):
            ax.add_patch(patches.Rectangle(
                (b["x"], b["y"]), b["width"], b["height"],
                facecolor=colors[idx % len(colors)],
                edgecolor='none', zorder=1))
        if show_buildings:
            xs = [b["x"] for b in self.buildings]
            ys = [b["y"] for b in self.buildings]
            ax.scatter(xs, ys, facecolor='#CCCCFF', s=50, marker='o',
                       edgecolors='blue', linewidths=0.4, zorder=5,
                       label='Substations')
        ax.set_xlim(-20, self.width + 20)
        ax.set_ylim(-20, self.height + 20)
        ax.set_aspect('equal')
        ax.axis('off')
        if show:
            plt.tight_layout()
            plt.show()


# =====================================================================
# 2. STREET GRAPH BUILDER
# =====================================================================
class StreetGraphBuilder:
    """
    Builds and validates the support street graph from a DistrictGenerator.
    """

    def __init__(self, district):
        if not district.street_nodes:
            raise ValueError("Call district.generate() first.")
        self.district = district
        self.graph    = nx.Graph()

    def build(self):
        d = self.district
        for node_id, (x, y) in d.street_nodes.items():
            self.graph.add_node(node_id, pos=(x, y), kind="intersection")
        for n1, n2 in d.street_edges:
            x1, y1 = d.street_nodes[n1]
            x2, y2 = d.street_nodes[n2]
            length  = math.hypot(x2-x1, y2-y1)
            geom    = LineString([(x1,y1),(x2,y2)])
            self.graph.add_edge(n1, n2, length=length,
                                geometry=geom, kind="street")
        self._validate()
        return self.graph

    def _validate(self):
        if not nx.is_connected(self.graph):
            raise ValueError("Street graph is not connected.")
        zero = [(u,v) for u,v,l in self.graph.edges(data="length")
                if l is not None and l < 1e-6]
        if zero:
            print(f"[WARN] {len(zero)} near-zero-length edges detected.")

    def stats(self):
        lengths = list(nx.get_edge_attributes(self.graph,"length").values())
        return {
            "n_nodes"           : self.graph.number_of_nodes(),
            "n_edges"           : self.graph.number_of_edges(),
            "total_length_m"    : sum(lengths),
            "mean_edge_length_m": sum(lengths)/len(lengths) if lengths else 0,
        }

    def plot(self, ax=None, show=True):
        if ax is None:
            fig, ax = plt.subplots(figsize=(14,9))
        pos = nx.get_node_attributes(self.graph, "pos")
        nx.draw_networkx_edges(self.graph, pos, ax=ax,
                               edge_color="#AAAAAA", width=0.8, alpha=0.5)
        nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                               node_color="#666666", node_size=8)
        ax.set_title("Street graph", fontsize=11)
        ax.axis("off")
        if show:
            plt.tight_layout(); plt.show()
        return ax


# =====================================================================
# 3. THERMAL NETWORK BUILDER
# =====================================================================
# Topology generation via the constrained Steiner algorithm.
# Supports single and multiple source configurations.
# Reference: Vieth et al. (2025), Algorithm 2.

import hashlib
import time

class ThermalNetworkBuilder:
    """
    Builds the DHN routing graph G_rou by orthogonally projecting the
    consumer substations and the heat source onto the support street
    graph (edge splitting), then finds the optimal DHN topology G_dhn
    via the constrained Steiner tree algorithm (Vieth et al. 2025).

    Workflow:
        1. build_routing_graph()         — project all nodes onto streets
        2. constrained_steiner_tree()    — topology optimization
        3. metrics() / plot()            — analysis and visualisation

    Parameters
    ----------
    street_graph    : nx.Graph — output of StreetGraphBuilder.build()
    district        : DistrictGenerator — generated district
    generator_pos   : tuple (x,y) or list of tuples [(x1,y1),(x2,y2),...]
                      Single source: (x, y)
                      Multi-source:  [(x1,y1), (x2,y2)]
    snap_tol        : float — snap tolerance [m]
    """

    _TB_ATTR = "length_tb"

    def __init__(self, street_graph, district, generator_pos, snap_tol=1.0):
        self.street_graph  = street_graph
        self.district      = district
        self.snap_tol      = snap_tol

        # Normalise: always store as list of (x,y)
        if (isinstance(generator_pos, tuple) and
                len(generator_pos) == 2 and
                not isinstance(generator_pos[0], (tuple, list))):
            self._generator_positions = [generator_pos]
        else:
            self._generator_positions = list(generator_pos)

        self.generator_pos   = self._generator_positions[0]
        self.rou             = None
        self.dhn             = None
        self.generator_node  = None   # primary source node
        self.generator_nodes = []     # all source nodes
        self.building_nodes  = []
        self._proj_counter   = 0

    # ------------------------------------------------------------------
    def build_routing_graph(self):
        """Projects every substation and source(s) onto the closest
        street edge, splitting it at the projection point."""
        self.rou             = self.street_graph.copy()
        self.building_nodes  = []
        self.generator_nodes = []

        for b in self.district.buildings:
            node_id = self._connect_point(
                ("sub", b["id"]), b["x"], b["y"], kind="substation")
            self.building_nodes.append(node_id)

        for k, pos in enumerate(self._generator_positions):
            node_id = self._connect_point(
                ("gen", k), pos[0], pos[1], kind="generator")
            self.generator_nodes.append(node_id)

        self.generator_node = self.generator_nodes[0]
        self._assign_tiebreak_weights()

        if not nx.is_connected(self.rou):
            raise ValueError(
                "The routing graph is not connected after projection.")
        return self.rou

    # ------------------------------------------------------------------
    def _connect_point(self, node_id, x, y, kind):
        p = Point(x, y)
        best_uv, best_proj, best_dist = None, None, math.inf

        for u, v, data in self.rou.edges(data=True):
            if data.get("kind") != "street":
                continue
            geom    = data["geometry"]
            proj_pt = geom.interpolate(geom.project(p))
            d       = proj_pt.distance(p)
            if d < best_dist:
                best_uv, best_proj, best_dist = (u, v), proj_pt, d

        if best_uv is None:
            raise RuntimeError("No street edge available to project onto.")

        u, v     = best_uv
        u_pos    = self.rou.nodes[u]["pos"]
        v_pos    = self.rou.nodes[v]["pos"]
        proj_pos = (best_proj.x, best_proj.y)

        if math.dist(proj_pos, u_pos) <= self.snap_tol:
            crossing = u
        elif math.dist(proj_pos, v_pos) <= self.snap_tol:
            crossing = v
        else:
            crossing = ("proj", self._proj_counter)
            self._proj_counter += 1
            self.rou.add_node(crossing, pos=proj_pos, kind="crossing")
            self.rou.remove_edge(u, v)
            for a, a_pos, b_, b_pos in ((u, u_pos, crossing, proj_pos),
                                        (crossing, proj_pos, v, v_pos)):
                seg = LineString([a_pos, b_pos])
                self.rou.add_edge(a, b_, length=seg.length,
                                   geometry=seg, kind="street")

        self.rou.add_node(node_id, pos=(x, y), kind=kind)
        svc = LineString([(x, y), proj_pos])
        self.rou.add_edge(node_id, crossing,
                           length=max(svc.length, 1e-6),
                           geometry=svc, kind="service")
        return node_id

    # ------------------------------------------------------------------
    def _assign_tiebreak_weights(self, weight="length", eps=1e-9):
        for u, v, d in self.rou.edges(data=True):
            key = f"{u}|{v}" if str(u) < str(v) else f"{v}|{u}"
            tb  = int(hashlib.md5(key.encode()).hexdigest(), 16) % 10_000 / 10_000.0
            d[self._TB_ATTR] = d[weight] * (1.0 + eps * tb)

    # ------------------------------------------------------------------
    def _add_path(self, graph, path):
        for n in path:
            if n not in graph:
                graph.add_node(n, **self.rou.nodes[n])
        for u, v in zip(path[:-1], path[1:]):
            if not graph.has_edge(u, v):
                graph.add_edge(u, v, **self.rou.edges[u, v])

    # ------------------------------------------------------------------
    def shortest_path_topology(self, weight="length"):
        """Baseline: star topology via shortest paths from generator."""
        if self.rou is None:
            raise RuntimeError("Call build_routing_graph() first.")
        _, paths = nx.single_source_dijkstra(
            self.rou, self.generator_node, weight=self._TB_ATTR)
        dhn = nx.Graph()
        dhn.add_node(self.generator_node,
                     **self.rou.nodes[self.generator_node])
        for n in self.building_nodes:
            self._add_path(dhn, paths[n])
        return dhn

    # ------------------------------------------------------------------
    def constrained_steiner_tree(self, beta=1.25, delta_eps=0.05,
                                  weight="length"):
        """
        Constrained Steiner tree (Algorithm 2, Vieth et al. 2025).
        Produces a radial base topology with L hydraulic loops.

        Parameters
        ----------
        beta      : float >= 1 — flexibility factor
        delta_eps : float — fallback step size
        weight    : str   — physical length edge attribute
        """
        if self.rou is None:
            raise RuntimeError("Call build_routing_graph() first.")
        if beta < 1:
            raise ValueError("beta must be >= 1.")

        rou       = self.rou
        tb        = self._TB_ATTR
        terminals = list(self.building_nodes)

        # l_max: single-source uses g directly; multi-source uses
        # minimum distance from any generator to each terminal
        if len(self.generator_nodes) == 1:
            g = self.generator_nodes[0]
            sp_len, _ = nx.single_source_dijkstra(rou, g, weight=weight)
            l_sp_max  = max(sp_len[n] for n in terminals)
        else:
            l_sp_max = 0.0
            for n in terminals:
                min_d = math.inf
                for g in self.generator_nodes:
                    try:
                        d = nx.shortest_path_length(rou, g, n, weight=weight)
                        min_d = min(min_d, d)
                    except nx.NetworkXNoPath:
                        continue
                if min_d != math.inf:
                    l_sp_max = max(l_sp_max, min_d)

        l_max = beta * l_sp_max

        # Initialise DHN with all generator nodes
        dhn = nx.Graph()
        dhn.add_node(self.generator_nodes[0],
                     **rou.nodes[self.generator_nodes[0]])
        for g in self.generator_nodes[1:]:
            _, path = nx.single_source_dijkstra(
                rou, self.generator_nodes[0], target=g, weight=tb)
            self._add_path(dhn, path)

        unprocessed = set(terminals)

        while unprocessed:
            best_path, best_len = None, math.inf

            # Greedy pass: cheapest admissible connection
            for r in unprocessed:
                added_len, path_r = nx.multi_source_dijkstra(
                    rou, sources=set(dhn.nodes), target=r, weight=tb)
                if added_len >= best_len:
                    continue
                dhn_hat = dhn.copy()
                self._add_path(dhn_hat, path_r)
                # Check constraint from nearest generator
                l_gr = math.inf
                for g in self.generator_nodes:
                    if g in dhn_hat:
                        try:
                            d = nx.shortest_path_length(
                                dhn_hat, g, r, weight=weight)
                            l_gr = min(l_gr, d)
                        except nx.NetworkXNoPath:
                            continue
                if l_gr <= l_max:
                    best_path, best_len = path_r, added_len

            # Fallback: weighted search reusing existing pipes
            if best_path is None:
                eps = delta_eps
                while True:
                    def w(u, v, d, _eps=eps):
                        c = 0.0 if dhn.has_edge(u, v) else d[tb]
                        return _eps * d[tb] + (1.0 - _eps) * c

                    w_len, w_paths = nx.multi_source_dijkstra(
                        rou, sources=set(self.generator_nodes), weight=w)
                    reachable = {n: w_len[n] for n in unprocessed
                                 if n in w_len}
                    if not reachable:
                        break
                    r       = min(reachable, key=reachable.get)
                    path_r  = w_paths[r]
                    dhn_hat = dhn.copy()
                    self._add_path(dhn_hat, path_r)
                    l_gr = math.inf
                    for g in self.generator_nodes:
                        if g in dhn_hat:
                            try:
                                d = nx.shortest_path_length(
                                    dhn_hat, g, r, weight=weight)
                                l_gr = min(l_gr, d)
                            except nx.NetworkXNoPath:
                                continue
                    if l_gr <= l_max or eps >= 1.0:
                        best_path = path_r
                        break
                    eps = min(eps + delta_eps, 1.0)

            if best_path is not None:
                self._add_path(dhn, best_path)
                unprocessed.remove(best_path[-1])
            else:
                r = unprocessed.pop()
                _, path_r = nx.multi_source_dijkstra(
                    rou, sources=set(dhn.nodes), target=r, weight=tb)
                self._add_path(dhn, path_r)

        self.dhn = dhn
        return dhn

    # ------------------------------------------------------------------
    def steiner_tree_topology(self, weight="length", method="kou"):
        """Unconstrained Steiner tree (Kou/Mehlhorn via networkX)."""
        if self.rou is None:
            raise RuntimeError("Call build_routing_graph() first.")
        terminals = set(self.building_nodes) | set(self.generator_nodes)
        try:
            return nx_steiner_tree(self.rou, terminals,
                                    weight=weight, method=method)
        except TypeError:
            return nx_steiner_tree(self.rou, terminals, weight=weight)

    # ------------------------------------------------------------------
    def metrics(self, dhn=None):
        """Topological metrics. Supports multi-source configurations."""
        dhn = dhn if dhn is not None else self.dhn
        if dhn is None:
            raise RuntimeError("No DHN topology available.")

        l_tot = sum(d.get("length", 0.0)
                    for _, _, d in dhn.edges(data=True))

        l_cc = 0.0
        for n in self.building_nodes:
            if n not in dhn:
                continue
            min_d = math.inf
            for g in self.generator_nodes:
                if g in dhn:
                    try:
                        d = nx.shortest_path_length(dhn, g, n, weight="length")
                        min_d = min(min_d, d)
                    except nx.NetworkXNoPath:
                        continue
            if min_d != math.inf:
                l_cc = max(l_cc, min_d)

        N = dhn.number_of_nodes()
        E = dhn.number_of_edges()
        C = nx.number_connected_components(dhn)
        L = E - N + 1
        return {
            "L_tot_m": round(l_tot, 2),
            "L_cc_m": round(l_cc, 2),
            "N_nodes": N,
            "N_edges": E,
            "N_components": C,
            "L_loops": L,
            "alpha": round(L / max(2 * N - 5, 1), 4),
            "is_meshed": L > 0 and C == 1,
            "connected": C == 1,
        }

    # ------------------------------------------------------------------
    def plot(self, dhn=None, ax=None, show=True,
             with_district=True, title="DHN topology"):

        dhn = dhn if dhn is not None else self.dhn

        if dhn is None:
            raise RuntimeError("No DHN topology to plot.")

        if ax is None:

            fig, ax = plt.subplots(figsize=(14,9))

        if with_district:
            self.district.plot_district(ax=ax, show=False)

        pos = nx.get_node_attributes(self.rou, "pos")

        # edges
        nx.draw_networkx_edges(dhn, pos, ax=ax,
                               edge_color="black", width=1.0, alpha=1.0)

        # substations
        sub_nodes = [n for n in dhn.nodes if n in self.building_nodes]

        nx.draw_networkx_nodes(dhn, pos, nodelist=sub_nodes, ax=ax,
                               node_color="#CCCCFF", node_size=22,
                               edgecolors="blue", linewidths=1.2)

        # source
        nx.draw_networkx_nodes(dhn, pos, nodelist=self.generator_nodes, ax=ax,
                               node_color="blue", node_size=140,
                               edgecolors="blue", linewidths=1.2)

        # internal junctions
        junction_nodes = [n for n in dhn.nodes
                          if n not in self.building_nodes
                          and n not in self.generator_nodes]

        nx.draw_networkx_nodes(dhn, pos, nodelist=junction_nodes, ax=ax,
                               node_color="black", node_size=22, linewidths=0)

        ax.set_title(title, fontweight="bold", fontsize=12)

        if show:
            plt.tight_layout(); plt.show()

        return ax


# =====================================================================
# 4. EXPORT HELPERS
# =====================================================================
def extract_nodes(tnb, dhn, digits=2, source_ids=None):
    """Node table of a generated network.

    Sources come first, then the other nodes of `dhn` in graph order: substations are named
    sub<k> (k = index in district.buildings), junctions jun0, jun1, ...

    Parameters
    ----------
    tnb        : ThermalNetworkBuilder used to generate `dhn`
    dhn        : nx.Graph — the network topology
    digits     : rounding of the coordinates [m]
    source_ids : list of ids for the sources; default "src" for a single source,
                 "src0", "src1", ... for several sources

    Returns
    -------
    node_rows : list of (node_id, node_type, x_m, y_m)
    node_id   : dict graph node -> node_id
    """
    rou = tnb.rou
    if source_ids is None:
        n_src = len(tnb.generator_nodes)
        source_ids = ["src"] if n_src == 1 else [f"src{k}" for k in range(n_src)]
    node_id, node_rows, idx_j = {}, [], 0
    for gnode, nid in zip(tnb.generator_nodes, source_ids):
        pos = rou.nodes[gnode]["pos"]
        node_id[gnode] = nid
        node_rows.append((nid, "source", round(pos[0], digits), round(pos[1], digits)))
    for n in dhn.nodes():
        if n in node_id:
            continue
        pos = rou.nodes[n]["pos"]
        if rou.nodes[n].get("kind", "junction") == "substation":
            nid, ntype = f"sub{tnb.building_nodes.index(n)}", "substation"
        else:
            nid, ntype = f"jun{idx_j}", "junction"
            idx_j += 1
        node_id[n] = nid
        node_rows.append((nid, ntype, round(pos[0], digits), round(pos[1], digits)))
    return node_rows, node_id


def downstream_substations(tnb, dhn, source=None):
    """Orientation and downstream load of every pipe of a generated network.

    The network is oriented from `source` (default: the first source) with a breadth-first
    search; each pipe is oriented along the search and associated with the number of
    substations downstream of it (at least 1, also for loop-closing pipes).

    Returns a list of (from_node, to_node, n_downstream, length_m), in the order of
    dhn.edges(), with graph nodes as returned by the ThermalNetworkBuilder.
    """
    source  = tnb.generator_nodes[0] if source is None else source
    G_dir   = nx.DiGraph(nx.bfs_tree(dhn, source))
    sub_set = set(tnb.building_nodes)

    def n_down(node):
        try:
            desc = nx.descendants(G_dir, node) | {node}
        except Exception:
            desc = {node}
        return sum(1 for n in desc if n in sub_set)

    out = []
    for u, v in dhn.edges():
        if G_dir.has_edge(u, v):
            a, b = u, v
        elif G_dir.has_edge(v, u):
            a, b = v, u
        else:
            a, b = u, v
        out.append((a, b, max(n_down(b), 1), dhn.edges[u, v].get("length", 0.0)))
    return out


# =====================================================================
# EXAMPLE
# =====================================================================
if __name__ == "__main__":

    # --- District ---
    district = DistrictGenerator(
        width=1200, height=800,
        rows=5, cols=7,
        street_width=15,
        n_substations=100,
        block_variation=0.25,
        perturbation=7,
        seed=42
    )
    district.generate()
    district.plot_district()

    streets = StreetGraphBuilder(district).build()
    tnb = ThermalNetworkBuilder(streets, district, generator_pos=(50, 40))
    tnb.build_routing_graph()
    dhn = tnb.constrained_steiner_tree(beta=1.0)
    print(tnb.metrics(dhn))
    tnb.plot(dhn)
