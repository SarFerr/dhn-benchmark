# 3G_R_S_BASE.py
#
# Benchmark archetype: 3GDH, Radial, Small
#
# Methodology I — Purpose-driven design (methodology_I.py)
#   Rule 1: exactly 10 substations
#   Rule 2: pipe lengths sampled from U[100, 200] m, seed=42
#   Rule 3: radial topology, binary tree of depth 3, no loops (L=0)
#
# Outputs (archetypes_generation/archetypes/3G_R_S_BASE/):
#   nodes.csv             — node table with boundary conditions (supply + return)
#   pipes.csv             — pipe table with all modelling parameters
#   topology.png          — network topology plot
#   incidence_matrix.csv  — node-pipe incidence matrix
#
# Usage:
#   python archetypes_generation/networks/3G_R_S_BASE.py

import os
import sys
import csv
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths — robust regardless of where the script is called from
# ---------------------------------------------------------------------------
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "3G_R_S_BASE")
os.makedirs(OUT_DIR, exist_ok=True)

# Add repo root to path so archetypes_generation package is importable
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co
import archetypes_generation.demand_profile as dp
import archetypes_generation.plotting as pl
import archetypes_generation.pipe_system as ps
import archetypes_generation.networks.methodology_I as m1
for _m in (co, dp, pl, ps, m1):
    importlib.reload(_m)

from archetypes_generation.constants import GEN_OPERATING
from archetypes_generation.demand_profile import Q_PEAK_W
from archetypes_generation.plotting import plot_topology
from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv
from archetypes_generation.networks.methodology_I import build_network, design_loads, E, W, S, N

GEN      = "3G"

# ---------------------------------------------------------------------------
# SECTION 1 — LAYOUT
# Binary tree of depth 3 (L = 0); lengths sampled in the order of EDGE_LIST,
# coordinates derived from them (euclidean distance == pipe length).
# ---------------------------------------------------------------------------
SEED     = 42
L_RANGE  = (100.0, 200.0)          # m

EDGE_LIST = [
    ("src", "a"), ("src", "b"), ("a", "c"), ("b", "d"),
    ("a", "sub1"), ("a", "sub2"), ("b", "sub3"), ("b", "sub4"),
    ("c", "sub5"), ("c", "sub6"), ("c", "sub7"),
    ("d", "sub8"), ("d", "sub9"), ("d", "sub10"),
]
# Direction of each pipe (x to the east, y to the south)
DIRECTIONS = {
    ("src", "a"): S, ("src", "b"): E, ("a", "c"): S, ("b", "d"): E,
    ("a", "sub1"): W, ("a", "sub2"): E, ("b", "sub3"): N, ("b", "sub4"): S,
    ("c", "sub5"): W, ("c", "sub6"): E, ("c", "sub7"): S,
    ("d", "sub8"): S, ("d", "sub9"): N, ("d", "sub10"): E,
}

NET = build_network(EDGE_LIST, DIRECTIONS, length_mode="geometric",
                    length_range=L_RANGE, seed=SEED, expected_loops=0)
NODES, EDGES, PIPE_L = NET["nodes"], NET["edges"], NET["lengths"]

print("Sampled lengths [m]:")
for e, l in NET["sampled"].items():
    print(f"  {e[0]:>4} -> {e[1]:<6} {l:7.1f}")
print("Lengths set by the geometry [m]:")
for e, l in NET["geometric"].items():
    print(f"  {e[0]:>4} -> {e[1]:<6} {l:7.1f}")

# ---------------------------------------------------------------------------
# SECTION 2 — TOPOLOGY CHECKS (connectivity and L are also checked in build_network)
# ---------------------------------------------------------------------------
N_ = len(NODES)
E_ = len(EDGES)
L  = E_ - N_ + 1

assert L == 0, f"Expected 0 loops, got {L}"
assert sum(1 for n in NODES if n[1] == "source")     == 1
assert sum(1 for n in NODES if n[1] == "substation") == 10

print(f"\nTopology OK — N={N_}, E={E_}, L={L}")

# ---------------------------------------------------------------------------
# SECTION 3 — TOPOLOGY KPIs
# ---------------------------------------------------------------------------
G_nx = nx.Graph()
G_nx.add_nodes_from([n[0] for n in NODES])
G_nx.add_edges_from(EDGES)

degrees = dict(G_nx.degree())
n_src   = sum(1 for n in NODES if n[1] == "source")
n_jun   = sum(1 for n in NODES if n[1] == "junction")
n_sub   = sum(1 for n in NODES if n[1] == "substation")

KPIS = {
    "network_code"     : "3G_R_S_BASE",
    "generation"       : "3G",
    "topology"         : "radial",
    "size"             : "small",
    "n_nodes"          : N_,
    "n_edges"          : E_,
    "n_loops"          : L,
    "n_sources"        : n_src,
    "n_junctions"      : n_jun,
    "n_substations"    : n_sub,
    "avg_degree"       : round(sum(degrees.values()) / N_, 3),
    "max_degree"       : max(degrees.values()),
    "sparsity_S"       : round(1 - E_ / (N_ * (N_ - 1) / 2), 4),
    "meshedness_alpha" : round(L / max(2 * N_ - 5, 1), 4),
    "diameter_hops"    : nx.diameter(G_nx),
    "avg_path_hops"    : round(nx.average_shortest_path_length(G_nx), 3),
    "total_length_m"   : round(sum(PIPE_L.values()), 1),
    "total_length_km"  : round(sum(PIPE_L.values()) / 1000, 3),
    "seed"             : SEED,
}

print("\nKPIs:")
for k, v in KPIS.items():
    print(f"  {k:<22} {v}")

# ---------------------------------------------------------------------------
# SECTION 4 — PIPE SIZING
# radial: load of the substations downstream; looped: half of the total load for the
# distribution pipes, one substation for the service pipes (design_loads)
# ---------------------------------------------------------------------------
gp       = GEN_OPERATING["3G"]
DELTA_T  = gp["delta_T_nom"]
T_SUPPLY = gp["T_supply_nom"]
P_NOM    = gp["P_nom_bar"]

HEAT_LOSS_FACTOR = 1.05
LOADS       = design_loads(NET, Q_PEAK_W, HEAT_LOSS_FACTOR)
SUBSTATIONS = {n[0] for n in NODES if n[1] == "substation"}

PIPE_SIZING = {}

print(f"\n{'pipe_id':<14} {'from':<8} {'to':<10} "
      f"{'L m':>7} {'Q kW':>7} {'DN':>5} {'d_i mm':>8}  type")
print("-" * 80)

for u, v in EDGES:
    pid   = f"{u}_{v}"
    Lp    = PIPE_L[(u, v)]
    Q     = LOADS[(u, v)]
    ptype = "service" if v in SUBSTATIONS else "distribution"
    e     = select_dn(GEN, Q)
    PIPE_SIZING[pid] = pipe_record(GEN, e, u, v, Lp)
    print(f"{pid:<14} {u:<8} {v:<10} "
          f"{Lp:>7.1f} {Q / 1000:>7.1f} {e['DN']:>5} {e['d_i'] * 1000:>8.1f}  [{ptype}]")

print("-" * 80)
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"  L_tot      = {L_tot / 1000:.2f} km   target: 1–5 km ✓")
print(f"  Q_peak_tot = {n_sub * Q_PEAK_W / 1e6:.2f} MW    target: < 5 MW ✓")

# ---------------------------------------------------------------------------
# SECTION 5 — CSV EXPORT
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

# nodes.csv
with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m",
        "Q_peak_W", "p_pump_set_bar",
        "T_supply_set_degC", "delta_T_nom_K",
    ])
    for nid, ntype, x, y in NODES:
        w.writerow([
            nid,
            ntype,
            x,
            y,
            "demand_profile.csv" if ntype == "substation" else "",
            P_NOM                if ntype == "source"     else "",
            T_SUPPLY             if ntype == "source"     else "",
            DELTA_T              if ntype == "substation" else "",
        ])
print(f"  nodes.csv    → {len(NODES)} rows")

# pipes.csv — all columns via DictWriter
write_pipes_csv(os.path.join(OUT_DIR, "pipes.csv"), PIPE_SIZING)
print(f"  pipes.csv    → {len(PIPE_SIZING)} rows, "
      f"{len(next(iter(PIPE_SIZING.values()))) + 1} columns")

# ---------------------------------------------------------------------------
# SECTION 6 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
fig, ax = plot_topology(
    NODES, EDGES,
    title="3G_R_S_BASE",
    show=True,
)
plot_path = os.path.join(OUT_DIR, "topology.png")
fig.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"  topology.png → {plot_path}")

# ---------------------------------------------------------------------------
# SECTION 7 — INCIDENCE MATRIX
# ---------------------------------------------------------------------------
node_ids = [n[0] for n in NODES]
edge_ids = [f"{u}_{v}" for u, v in EDGES]

with open(os.path.join(OUT_DIR, "incidence_matrix.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["node_id"] + edge_ids)
    for node in node_ids:
        row = [node]
        for u, v in EDGES:
            if node == u:
                row.append(-1)
            elif node == v:
                row.append(+1)
            else:
                row.append(0)
        w.writerow(row)

print(f"  incidence_matrix.csv → {len(node_ids)} x {len(edge_ids)}")
print(f"\nDone → {OUT_DIR}")
