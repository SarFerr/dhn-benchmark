#
# synthetic_district.py
#
# SYNTHETIC URBAN DISTRICT GENERATOR — DHN BENCHMARK
#
# Classes:
#   DistrictGenerator      — synthetic urban district with centreline streets
#   StreetGraphBuilder     — builds and validates the support street graph
#   ThermalNetworkBuilder  — DHN topology via constrained Steiner tree
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
    def plot_district(self, ax=None, show=True):
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 9))
        ax.set_facecolor('#AAAAAA')
        colors = ['#F0EEE8', '#EDEAE0', '#F2F0EA', '#EDE8E0']
        for idx, b in enumerate(self.blocks):
            ax.add_patch(patches.Rectangle(
                (b["x"], b["y"]), b["width"], b["height"],
                facecolor=colors[idx % len(colors)],
                edgecolor='none', zorder=1))
        xs = [b["x"] for b in self.buildings]
        ys = [b["y"] for b in self.buildings]
        ax.scatter(xs, ys, color='#CC2200', s=50, marker='s',
                   edgecolors='white', linewidths=0.4, zorder=5,
                   label='Substations')
        ax.set_xlim(-20, self.width+20)
        ax.set_ylim(-20, self.height+20)
        ax.set_title("Synthetic Urban District", fontweight="bold", fontsize=12)
        ax.set_aspect('equal'); ax.axis('off')
        if show:
            plt.tight_layout(); plt.show()


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


# =====================================================================


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
# Topology generation via the constrained Steiner algorithm with multiple sources
# Reference: Vieth et al. (2025), Algorithm 2.

import hashlib
import time

class ThermalNetworkBuilder:
    """
    Builds the DHN routing graph G_rou by orthogonally projecting the
    consumer substations and the heat source onto the support street
    graph (edge splitting), then finds the optimal DHN topology G_dhn
    via the constrained Steiner tree algorithm (Vieth et al. 2025).

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

        # Primary generator_pos (single source, backward compatible)
        self.generator_pos  = self._generator_positions[0]

        self.rou            = None
        self.dhn            = None
        self.generator_node = None          # primary source node
        self.generator_nodes = []           # all source nodes (multi-source)
        self.building_nodes  = []
        self._proj_counter   = 0

    # ------------------------------------------------------------------
    def build_routing_graph(self):
        """Projects every substation and source(s) onto the closest
        street edge, splitting it at the projection point."""
        self.rou            = self.street_graph.copy()
        self.building_nodes = []
        self.generator_nodes= []

        for b in self.district.buildings:
            node_id = self._connect_point(
                ("sub", b["id"]), b["x"], b["y"], kind="substation")
            self.building_nodes.append(node_id)

        for k, pos in enumerate(self._generator_positions):
            node_id = self._connect_point(
                ("gen", k), pos[0], pos[1], kind="generator")
            self.generator_nodes.append(node_id)

        # Primary generator node (backward compatible)
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
                best_uv, best_proj, best_dist = (u,v), proj_pt, d

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
            key = f"{u}|{v}" if str(u)<str(v) else f"{v}|{u}"
            tb  = int(hashlib.md5(key.encode()).hexdigest(),16) % 10_000 / 10_000.0
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
        dhn.add_node(self.generator_node, **self.rou.nodes[self.generator_node])
        for n in self.building_nodes:
            self._add_path(dhn, paths[n])
        return dhn

    # ------------------------------------------------------------------
    def constrained_steiner_tree(self, beta=1.25, delta_eps=0.05,
                                  weight="length"):
        """
        Constrained Steiner tree (Algorithm 2, Vieth et al. 2025).

        For multi-source networks, the DHN is initialised with all
        generator nodes and l_max is computed from the closest source.

        Parameters
        ----------
        beta      : float >= 1 — flexibility factor (1.25 for TG family)
        delta_eps : float — fallback step size
        weight    : str — physical length attribute
        """
        if self.rou is None:
            raise RuntimeError("Call build_routing_graph() first.")
        if beta < 1:
            raise ValueError("beta must be >= 1.")

        rou       = self.rou
        tb        = self._TB_ATTR
        terminals = list(self.building_nodes)

        # l_max: from the closest generator to furthest terminal
        # Single source: identical to original algorithm
        # Multi-source: use minimum distance across all sources
        if len(self.generator_nodes) == 1:
            g = self.generator_nodes[0]
            sp_len, _ = nx.single_source_dijkstra(rou, g, weight=weight)
            l_sp_max  = max(sp_len[n] for n in terminals)
        else:
            l_sp_max = 0.0
            for g in self.generator_nodes:
                sp_len, _ = nx.single_source_dijkstra(rou, g, weight=weight)
                for n in terminals:
                    if n in sp_len:
                        l_sp_max = max(l_sp_max, sp_len[n])

        l_max = beta * l_sp_max

        # Initialise DHN with all generator nodes
        dhn = nx.Graph()
        for g in self.generator_nodes:
            dhn.add_node(g, **rou.nodes[g])

        # Primary generator for single-source path checks
        g_primary = self.generator_nodes[0]

        unprocessed = set(terminals)

        while unprocessed:
            best_path, best_len = None, math.inf

            # Greedy pass (Eq. 3)
            for r in unprocessed:
                added_len, path_r = nx.multi_source_dijkstra(
                    rou, sources=set(dhn.nodes), target=r, weight=tb)
                if added_len >= best_len:
                    continue
                dhn_hat = dhn.copy()
                self._add_path(dhn_hat, path_r)
                # Check l_max constraint from nearest generator
                try:
                    l_gr = nx.shortest_path_length(
                        dhn_hat, g_primary, r, weight=weight)
                except nx.NetworkXNoPath:
                    l_gr = math.inf
                if l_gr <= l_max:
                    best_path, best_len = path_r, added_len

            # Fallback (Eq. 4-5)
            if best_path is None:
                eps = delta_eps
                while True:
                    def w(u, v, d, _eps=eps):
                        c = 0.0 if dhn.has_edge(u, v) else d[tb]
                        return _eps * d[tb] + (1.0 - _eps) * c

                    w_len, w_paths = nx.single_source_dijkstra(
                        rou, g_primary, weight=w)
                    reachable = {n: w_len[n] for n in unprocessed
                                 if n in w_len}
                    r       = min(reachable, key=reachable.get)
                    path_r  = w_paths[r]
                    dhn_hat = dhn.copy()
                    self._add_path(dhn_hat, path_r)
                    try:
                        l_gr = nx.shortest_path_length(
                            dhn_hat, g_primary, r, weight=weight)
                    except nx.NetworkXNoPath:
                        l_gr = math.inf
                    if l_gr <= l_max or eps >= 1.0:
                        best_path = path_r
                        break
                    eps = min(eps + delta_eps, 1.0)

            self._add_path(dhn, best_path)
            unprocessed.remove(best_path[-1])

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
    def metrics(self, dhn=None, weight="length"):
        dhn = dhn if dhn is not None else self.dhn
        if dhn is None:
            raise RuntimeError("No DHN topology available.")
        l_sum = sum(d[weight] for _,_,d in dhn.edges(data=True))
        l_cc  = max(
            nx.shortest_path_length(dhn, self.generator_node, n,
                                     weight=weight)
            for n in self.building_nodes)
        N = dhn.number_of_nodes()
        E = dhn.number_of_edges()
        L = E - N + 1
        return {
            "l_sum_m"  : l_sum,
            "l_cc_m"   : l_cc,
            "n_nodes"  : N,
            "n_edges"  : E,
            "is_meshed": not nx.is_tree(dhn),
            "n_loops"  : L,
        }

    # ------------------------------------------------------------------
    def plot(self, dhn=None, ax=None, show=True,
             with_district=True, title="DHN_TG_3G_M_M_BASE"):
        dhn = dhn if dhn is not None else self.dhn
        if dhn is None:
            raise RuntimeError("No DHN topology to plot.")
        if ax is None:
            fig, ax = plt.subplots(figsize=(14,9))
        if with_district:
            self.district.plot_district(ax=ax, show=False)
        pos = nx.get_node_attributes(self.rou, "pos")
        nx.draw_networkx_edges(dhn, pos, ax=ax,
                               edge_color="#CC2200", width=2.2, alpha=0.9)
        sub_nodes = [n for n in dhn.nodes if n in self.building_nodes]
        nx.draw_networkx_nodes(dhn, pos, nodelist=sub_nodes, ax=ax,
                               node_color="#222222", node_size=22, linewidths=0)
        nx.draw_networkx_nodes(dhn, pos, nodelist=self.generator_nodes,
                               ax=ax, node_color="#FFB300", node_size=140,
                               edgecolors="black", linewidths=1.0)
        ax.set_title(title, fontweight="bold", fontsize=12)
        if show:
            plt.tight_layout(); plt.show()
        return ax

    # ------------------------------------------------------------------
    def assign_heat_demand(self, seed=1, mu=3.5, sigma=0.6, constant=None):
        if not self.building_nodes:
            raise RuntimeError("Call build_routing_graph() first.")
        if constant is not None:
            self.heat_demand = {n: float(constant) for n in self.building_nodes}
            return self.heat_demand
        rng = random.Random(seed)
        self.heat_demand = {n: rng.lognormvariate(mu, sigma)
                             for n in self.building_nodes}
        return self.heat_demand

    # ------------------------------------------------------------------
    def run_benchmark(self, betas=(1.0, 1.25, 1.5), weight="length"):
        """Runs shortest-path, constrained Steiner (each beta), and Kou."""
        if self.rou is None:
            raise RuntimeError("Call build_routing_graph() first.")
        results = []
        t0  = time.perf_counter()
        dhn = self.shortest_path_topology(weight=weight)
        results.append(("shortest path search", dhn,
                         {**self.metrics(dhn,weight),
                          "t_comp_s": time.perf_counter()-t0}))
        for beta in betas:
            t0  = time.perf_counter()
            dhn = self.constrained_steiner_tree(beta=beta, weight=weight)
            results.append((f"constrained Steiner (beta={beta:g})", dhn,
                             {**self.metrics(dhn,weight),
                              "t_comp_s": time.perf_counter()-t0}))
        t0  = time.perf_counter()
        dhn = self.steiner_tree_topology(weight=weight)
        results.append(("Kou (networkX)", dhn,
                         {**self.metrics(dhn,weight),
                          "t_comp_s": time.perf_counter()-t0}))
        self.benchmark_results = results
        self.dhn = results[1][1]
        return results

    # ------------------------------------------------------------------
    def print_benchmark_table(self, results=None):
        results = results or getattr(self,"benchmark_results",None)
        if results is None:
            raise RuntimeError("Call run_benchmark() first.")
        hdr = (f"{'Algorithm':32s} {'l_sum [km]':>11s} {'l_cc [km]':>11s} "
               f"{'t_comp [s]':>11s} {'meshed':>8s} {'loops':>6s}")
        print(hdr); print("-"*len(hdr))
        for label,_,m in results:
            print(f"{label:32s} {m['l_sum_m']/1000:11.3f} "
                  f"{m['l_cc_m']/1000:11.3f} {m['t_comp_s']:11.3f} "
                  f"{str(m['is_meshed']):>8s} {m['n_loops']:>6d}")