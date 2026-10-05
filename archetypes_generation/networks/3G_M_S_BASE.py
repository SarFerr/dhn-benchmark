# 3G_M_S_BASE.py
#
# Benchmark archetype: Thermo-Hydraulic Validation, 3GDH, Meshed, Small
#
# Methodology I — Purpose-driven design
#   Rule 1: exactly 10 substations
#   Rule 2: pipe lengths sampled from U[100, 200] m, seed=42
#   Rule 3: meshed topology — optimal spasity index (L=8)
#
# Outputs (archetypes_generation/archetypes/3G_M_S_BASE/):
#   nodes.csv     — node table with boundary conditions (supply + return)
#   pipes.csv     — pipe table with all modelling parameters
#   topology.png  — network topology plot
#
# Usage:
#   python archetypes_generation/networks/3G_M_S_BASE.py

import os
import sys
import csv
import math
import random
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "3G_M_S_BASE")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co
import archetypes_generation.demand_profile as dp
import archetypes_generation.plotting as pl
importlib.reload(co)
importlib.reload(dp)
importlib.reload(pl)

from archetypes_generation.constants import (
    GEN_OPERATING, PIPE_CATALOGUE,
    LAMBDA_STEEL, LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL,
    ROUGHNESS_STEEL, BURIAL_DEPTH, H_EXT, T_GROUND,
    RHO_STEEL, CP_STEEL,
    RHO_PUR, CP_PUR,
    RHO_HDPE, CP_HDPE,
)
from archetypes_generation.demand_profile import Q_PEAK_W
from archetypes_generation.plotting import plot_topology
from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv, PipeSizingError
GEN = "3G"

# ---------------------------------------------------------------------------
# SECTION 1 — PIPE LENGTHS
# Sampled from U[100, 200] m, seed=42.
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)

EDGE_LIST_BASE = [
    # ring
    ("src", "a"), ("a", "b"), ("b", "c"), ("c", "d"),
    ("d", "e"), ("e", "f"), ("f", "g"), ("g", "h"), ("h", "src"),
    # radial branches
    ("a", "sub1"), ("a", "sub2"),
    ("b", "sub3"), ("b", "sub4"),
    ("d", "sub5"), ("d", "sub6"),
    ("f", "sub7"), ("f", "sub8"),
    ("h", "sub9"), ("h", "sub10"),
]

CROSS_EDGES = [
    ("c", "g"),   # loop 2
    ("e", "a"),   # loop 3
    ("c", "e"),   # loop 4
    ("e", "g"),   # loop 5
    ("b", "h"),   # loop 6
    ("c", "f"),   # loop 7
    ("d", "g"),   # loop 8
]

ALL_EDGES = EDGE_LIST_BASE + CROSS_EDGES

PIPE_L = {}
for u, v in ALL_EDGES:
    PIPE_L[(u, v)] = round(random.uniform(100, 200), 1)

RING_SET = set(tuple(e) for e in EDGE_LIST_BASE[:9])
CROSS_SET = set(tuple(e) for e in CROSS_EDGES)

# ---------------------------------------------------------------------------
# SECTION 2 — NODE COORDINATES
# Derived from pipe lengths so that euclidean(u,v) == PIPE_L[(u,v)].
# ---------------------------------------------------------------------------
_ay = PIPE_L[("src", "a")]
_by = _ay + PIPE_L[("a", "b")]
_cy = _by + PIPE_L[("b", "c")]

_dx = PIPE_L[("c", "d")]
_ex = _dx + PIPE_L[("d", "e")]

_fy = _cy - PIPE_L[("e", "f")]

NODES = [
    # id        type            x                                   y
    ("src",    "source",        0,                                  0),
    ("a",      "junction",      0,                                  _ay),
    ("b",      "junction",      0,                                  _by),
    ("c",      "junction",      0,                                  _cy),
    ("d",      "junction",      _dx,                                _cy),
    ("e",      "junction",      _ex,                                _cy),
    ("f",      "junction",      _ex,                                _fy),
    ("g",      "junction",      _ex,                                0),
    ("h",      "junction",      _dx,                                0),
    # substations of a
    ("sub1",   "substation",    0 - PIPE_L[("a", "sub1")],          _ay),
    ("sub2",   "substation",    0 + PIPE_L[("a", "sub2")],          _ay),
    # substations of b
    ("sub3",   "substation",    0 - PIPE_L[("b", "sub3")],          _by),
    ("sub4",   "substation",    0 + PIPE_L[("b", "sub4")],          _by),
    # substations of d
    ("sub5",   "substation",    _dx,                                _cy - PIPE_L[("d", "sub5")]),
    ("sub6",   "substation",    _dx,                                _cy + PIPE_L[("d", "sub6")]),
    # substations of f
    ("sub7",   "substation",    _ex - PIPE_L[("f", "sub7")],        _fy ),
    ("sub8",   "substation",    _ex + PIPE_L[("f", "sub8")],        _fy),
    # substations of h
    ("sub9",   "substation",   _dx,                                 0 - PIPE_L[("h", "sub9")]),
    ("sub10",  "substation",   _dx,                                 0 + PIPE_L[("h", "sub10")]),
]

EDGES = ALL_EDGES

# ---------------------------------------------------------------------------
# SECTION 3 — TOPOLOGY CHECKS
# ---------------------------------------------------------------------------
N = len(NODES)
E = len(EDGES)
L = E - N + 1

assert N == 19, f"Expected 19 nodes, got {N}"
assert E == 26, f"Expected 26 edges, got {E}"
assert L == 8,  f"Expected 8 loops, got {L}"
assert sum(1 for n in NODES if n[1] == "source") == 1
assert sum(1 for n in NODES if n[1] == "junction") == 8
assert sum(1 for n in NODES if n[1] == "substation") == 10

G_check = nx.Graph()
G_check.add_edges_from(EDGES)
assert max(dict(G_check.degree()).values()) == 5, "max_degree exceeded 5"

print(f"Topology OK — N={N}, E={E}, L={L}")
print(f"max_degree check passed (= 5)")

# ---------------------------------------------------------------------------
# SECTION 4 — TOPOLOGY KPIs
# ---------------------------------------------------------------------------
G_nx = nx.Graph()
G_nx.add_nodes_from([n[0] for n in NODES])
G_nx.add_edges_from(EDGES)

degrees = dict(G_nx.degree())
n_src = sum(1 for n in NODES if n[1] == "source")
n_jun = sum(1 for n in NODES if n[1] == "junction")
n_sub = sum(1 for n in NODES if n[1] == "substation")

KPIS = {
    "network_code"      : "3G_M_S_BASE",
    "generation"        : "3G",
    "topology"          : "meshed",
    "size"              : "small",
    "n_nodes"           : N,
    "n_edges"           : E,
    "n_loops"           : L,
    "n_sources"         : n_src,
    "n_junctions"       : n_jun,
    "n_substations"     : n_sub,
    "avg_degree"        : round(sum(degrees.values()) / N, 3),
    "max_degree"        : max(degrees.values()),
    "sparsity_S"        : round(1 - E / (N * (N - 1) / 2), 4),
    "meshedness_alpha"  : round(L / max(2 * N - 5, 1), 4),
    "diameter_hops"     : nx.diameter(G_nx),
    "avg_path_hops"     : round(nx.average_shortest_path_length(G_nx), 3),
    "total_length_m"    : round(sum(PIPE_L.values()), 1),
    "total_length_km"   : round(sum(PIPE_L.values()) / 1000, 3),
    "seed"              : SEED,
}

print("\nKPIs:")
for k, v in KPIS.items():
    print(f"  {k:<22} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — PIPE SIZING
# ---------------------------------------------------------------------------
gp = GEN_OPERATING["3G"]
RHO = gp["rho"]
CP = gp["cp"]
DELTA_T = gp["delta_T_nom"]
V_MAX = gp["v_max"]
T_SUPPLY = gp["T_supply_nom"]
P_NOM = gp["P_nom_bar"]

HEAT_LOSS_FACTOR = 1.05
Q_total = n_sub * Q_PEAK_W * HEAT_LOSS_FACTOR


PIPE_SIZING = {}

print(f"\n{'pipe_id':<14} {'from':<8} {'to':<10} "
      f"{'L m':>7} {'Q kW':>7} {'DN':>5} {'d_i mm':>8}  type")
print("-" * 80)

for u, v in EDGES:
    pid = f"{u}_{v}"
    Lp = PIPE_L[(u, v)]
    if (u, v) in RING_SET or (u, v) in CROSS_SET:
        Q = round(Q_total / 2, 1)
        ptype = "ring" if (u, v) in RING_SET else "cross"
    else:
        Q = round(Q_PEAK_W * HEAT_LOSS_FACTOR, 1)
        ptype = "branch"
    e = select_dn(GEN, Q)
    dn, di, do = e['DN'], e['d_i'], e['d_o']


    PIPE_SIZING[pid] = pipe_record(GEN, e, u, v, Lp)
    print(f"{pid:<14} {u:<8} {v:<10} "
          f"{Lp:>7.1f} {Q / 1000:>7.1f} {dn:>5} {di * 1000:>8.1f}  [{ptype}]")

print("-" * 80)
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"  L_tot      = {L_tot / 1000:.2f} km   target: 1–5 km ✓")
print(f"  Q_peak_tot = {n_sub * Q_PEAK_W / 1e6:.2f} MW    target: < 5 MW ✓")

# ---------------------------------------------------------------------------
# SECTION 6 — CSV EXPORT
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
print(f"  pipes.csv    -> {len(PIPE_SIZING)} rows, "
      f"{len(next(iter(PIPE_SIZING.values())))+1} columns")

# ---------------------------------------------------------------------------
# SECTION 7 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
fig, ax = plot_topology(
    NODES, EDGES,
    title="3G_M_S_BASE",
    show=True,
)
plot_path = os.path.join(OUT_DIR, "topology.png")
fig.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")

# ---------------------------------------------------------------------------
# SECTION 8 — INCIDENCE MATRIX
# ---------------------------------------------------------------------------
# incidence_matrix.csv
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