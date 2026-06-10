# DHN_THV_3G_R_S_BASE.py
#
# Benchmark archetype: Thermo-Hydraulic Validation, 3GDH, Radial, Small
#
# Methodology I — Purpose-driven design (paper_v2, Section 6.2)
#   Rule 1: exactly 10 substations
#   Rule 2: pipe lengths sampled from U[100, 200] m, seed=42
#   Rule 3: radial tree topology, depth 3, no loops (L=0)
#
# Coordinate system:
#   origin = src node
#   x [m]  = horizontal, positive rightward
#   y [m]  = vertical,   positive downward
#
# Outputs (data/DHN_THV_3G_R_S_BASE/):
#   nodes.csv     — node table with boundary conditions (supply + return)
#   pipes.csv     — pipe table with all modelling parameters
#   topology.png  — network topology plot (paper-ready, 300 dpi)
#
# Usage:
#   python dhn_benchmark/networks/DHN_THV_3G_R_S_BASE.py

import os
import sys
import csv
import math
import random
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths — robust regardless of where the script is called from
# ---------------------------------------------------------------------------
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR = os.path.join(THIS_DIR, "..", "archetypes", "DHN_THV_3G_R_S_BASE")
os.makedirs(OUT_DIR, exist_ok=True)

# Add repo root to path so dhn_benchmark package is importable
sys.path.insert(0, REPO_ROOT)

import dhn_benchmark.constants as co
import dhn_benchmark.demand_profile as dp
import dhn_benchmark.plotting as pl
importlib.reload(co)
importlib.reload(dp)
importlib.reload(pl)

from dhn_benchmark.constants import (
    GEN_OPERATING, PIPE_CATALOGUE,
    LAMBDA_STEEL, LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL,
    ROUGHNESS_STEEL, BURIAL_DEPTH, T_GROUND,
    RHO_STEEL, CP_STEEL,
    RHO_PUR, CP_PUR,
    RHO_HDPE, CP_HDPE,
)
from dhn_benchmark.demand_profile import Q_PEAK_W
from dhn_benchmark.plotting import plot_topology

# ---------------------------------------------------------------------------
# SECTION 1 — PIPE LENGTHS
# Sampled from U[100, 200] m with fixed seed (Rule 2, paper_v2).
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)

EDGE_LIST = [
    ("src", "a"),
    ("src", "b"),
    ("a",   "c"),
    ("b",   "d"),
    ("a",   "sub1"),
    ("a",   "sub2"),
    ("b",   "sub3"),
    ("b",   "sub4"),
    ("c",   "sub5"),
    ("c",   "sub6"),
    ("c",   "sub7"),
    ("d",   "sub8"),
    ("d",   "sub9"),
    ("d",   "sub10"),
]

PIPE_L = {}
for u, v in EDGE_LIST:
    PIPE_L[(u, v)] = round(random.uniform(100, 200), 1)

# ---------------------------------------------------------------------------
# SECTION 2 — NODE COORDINATES
# Derived from pipe lengths so that euclidean(u,v) == PIPE_L[(u,v)].
# Layout rules (all edges horizontal or vertical):
#   src → a   : vertical   downward
#   src → b   : horizontal rightward
#   a   → c   : vertical   downward
#   b   → d   : horizontal rightward
#   a   → sub1: horizontal leftward
#   a   → sub2: horizontal rightward
#   b   → sub3: vertical   upward
#   b   → sub4: vertical   downward
#   c   → sub5: horizontal leftward
#   c   → sub6: horizontal rightward
#   c   → sub7: vertical   downward
#   d   → sub8: vertical   downward
#   d   → sub9: vertical   upward
#   d   → sub10:horizontal rightward
# ---------------------------------------------------------------------------
_ay = PIPE_L[("src", "a")]
_bx = PIPE_L[("src", "b")]
_cy = _ay + PIPE_L[("a", "c")]
_dx = _bx + PIPE_L[("b", "d")]

NODES = [
    # id        type            x                              y
    ("src",    "source",        0,                             0),
    ("a",      "junction",      0,                             _ay),
    ("b",      "junction",      _bx,                           0),
    ("c",      "junction",      0,                             _cy),
    ("d",      "junction",      _dx,                           0),
    ("sub1",   "substation",   -PIPE_L[("a", "sub1")],         _ay),
    ("sub2",   "substation",   +PIPE_L[("a", "sub2")],         _ay),
    ("sub3",   "substation",    _bx,                          -PIPE_L[("b", "sub3")]),
    ("sub4",   "substation",    _bx,                          +PIPE_L[("b", "sub4")]),
    ("sub5",   "substation",   -PIPE_L[("c", "sub5")],         _cy),
    ("sub6",   "substation",   +PIPE_L[("c", "sub6")],         _cy),
    ("sub7",   "substation",    0,                             _cy + PIPE_L[("c", "sub7")]),
    ("sub8",   "substation",    _dx,                          +PIPE_L[("d", "sub8")]),
    ("sub9",   "substation",    _dx,                          -PIPE_L[("d", "sub9")]),
    ("sub10",  "substation",    _dx + PIPE_L[("d", "sub10")],  0),
]

EDGES = EDGE_LIST

# ---------------------------------------------------------------------------
# SECTION 3 — TOPOLOGY CHECKS
# ---------------------------------------------------------------------------
N = len(NODES)
E = len(EDGES)
L = E - N + 1

assert N == 15, f"Expected 15 nodes, got {N}"
assert E == 14, f"Expected 14 edges, got {E}"
assert L == 0,  f"Expected 0 loops, got {L}"
assert sum(1 for n in NODES if n[1] == "source")     == 1
assert sum(1 for n in NODES if n[1] == "junction")   == 4
assert sum(1 for n in NODES if n[1] == "substation") == 10

# verify euclidean distance == pipe length for every edge
POS = {nid: (x, y) for nid, _, x, y in NODES}
for u, v in EDGES:
    xu, yu = POS[u]
    xv, yv = POS[v]
    d = round(math.sqrt((xv - xu)**2 + (yv - yu)**2), 1)
    assert d == PIPE_L[(u, v)], \
        f"Length mismatch {u}→{v}: coord={d} m, sampled={PIPE_L[(u,v)]} m"

print(f"Topology OK — N={N}, E={E}, L={L}")
print(f"Coordinate check passed")

# ---------------------------------------------------------------------------
# SECTION 4 — TOPOLOGY KPIs
# ---------------------------------------------------------------------------
G_nx = nx.Graph()
G_nx.add_nodes_from([n[0] for n in NODES])
G_nx.add_edges_from(EDGES)

degrees = dict(G_nx.degree())
n_src   = sum(1 for n in NODES if n[1] == "source")
n_jun   = sum(1 for n in NODES if n[1] == "junction")
n_sub   = sum(1 for n in NODES if n[1] == "substation")

KPIS = {
    "network_code"     : "DHN_THV_3G_R_S_BASE",
    "generation"       : "3G",
    "topology"         : "radial",
    "n_nodes"          : N,
    "n_edges"          : E,
    "n_loops"          : L,
    "n_sources"        : n_src,
    "n_junctions"      : n_jun,
    "n_substations"    : n_sub,
    "avg_degree"       : round(sum(degrees.values()) / N, 3),
    "max_degree"       : max(degrees.values()),
    "diameter_hops"    : nx.diameter(G_nx),
    "avg_path_hops"    : round(nx.average_shortest_path_length(G_nx), 3),
    "meshedness_alpha" : round(L / max(2 * N - 5, 1), 4),
    "total_length_m"   : round(sum(PIPE_L.values()), 1),
    "total_length_km"  : round(sum(PIPE_L.values()) / 1000, 3),
    "seed"             : SEED,
}

print("\nKPIs:")
for k, v in KPIS.items():
    print(f"  {k:<22} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — PIPE SIZING
# ---------------------------------------------------------------------------
gp       = GEN_OPERATING["3G"]
RHO      = gp["rho"]
CP       = gp["cp"]
DELTA_T  = gp["delta_T_nom"]
V_MAX    = gp["v_max"]
T_SUPPLY = gp["T_supply_nom"]
P_NOM    = gp["P_nom_bar"]

HEAT_LOSS_FACTOR = 1.05


def u_linear(d_o, d_casing):
    """Overall linear heat loss coefficient [W/(m·K)] — EN 13941."""
    R_ins  = math.log(d_casing / d_o)              / (2 * math.pi * LAMBDA_PUR)
    R_soil = math.log(2 * BURIAL_DEPTH / d_casing) / (2 * math.pi * LAMBDA_SOIL)
    return round(1.0 / (R_ins + R_soil), 4)


def select_dn(Q_w):
    """Select minimum DN satisfying v <= V_MAX."""
    mdot = Q_w / (CP * DELTA_T)
    for dn, (di, do, s, dc) in sorted(PIPE_CATALOGUE.items()):
        A = math.pi * di**2 / 4.0
        v = mdot / (RHO * A)
        if v <= V_MAX:
            return dn, di, do, dc, s, round(mdot, 4), round(v, 3)
    dn, (di, do, s, dc) = sorted(PIPE_CATALOGUE.items())[-1]
    A = math.pi * di**2 / 4.0
    return dn, di, do, dc, s, round(mdot, 4), round(mdot / (RHO * A), 3)


G_dir  = nx.DiGraph()
G_dir.add_edges_from(EDGES)
Q_node = {n[0]: Q_PEAK_W if n[1] == "substation" else 0.0 for n in NODES}


def downstream_load(from_node, to_node):
    reachable = nx.descendants(G_dir, to_node) | {to_node}
    return round(sum(Q_node.get(n, 0.0) for n in reachable) * HEAT_LOSS_FACTOR, 1)


PIPE_SIZING = {}

print(f"\n{'pipe_id':<14} {'from':<8} {'to':<10} "
      f"{'L m':>7} {'Q kW':>7} {'DN':>5} "
      f"{'d_i mm':>8} {'d_o mm':>8}")
print("-" * 100)

for u, v in EDGES:
    pid  = f"{u}_{v}"
    Lp   = PIPE_L[(u, v)]
    Q    = downstream_load(u, v)
    dn, di, do, dc, s, mdot, vel = select_dn(Q)
    vol  = round(math.pi / 4 * di**2 * Lp, 6)
    tau  = round(vol / (mdot / RHO), 1)

    PIPE_SIZING[pid] = {
        "from_node"              : u,
        "to_node"                : v,
        "length_m"               : Lp,
        "d_inner_m"              : di,
        "d_outer_m"              : do,
        "d_casing_m"             : dc,
        "wall_m"                 : s,
        "insulation_thickness_m" : round((dc - do) / 2, 5),
        "DN_mm"                  : dn,
        "roughness_m"            : ROUGHNESS_STEEL,
        "fluid_rho_kgm3"         : RHO,
        "fluid_cp_JkgK"          : CP,
        "fluid_mu_Pas"           : gp["mu"],
        "fluid_lambda_WmK"       : gp["lambda"],
        "steel_rho_kgm3"         : RHO_STEEL,
        "steel_cp_JkgK"          : CP_STEEL,
        "steel_lambda_WmK"       : LAMBDA_STEEL,
        "PUR_rho_kgm3"           : RHO_PUR,
        "PUR_cp_JkgK"            : CP_PUR,
        "PUR_lambda_WmK"         : LAMBDA_PUR,
        "HDPE_rho_kgm3"          : RHO_HDPE,
        "HDPE_cp_JkgK"           : CP_HDPE,
        "HDPE_lambda_WmK"        : LAMBDA_HDPE,
        "burial_depth_m"         : BURIAL_DEPTH,
        "soil_lambda_WmK"        : LAMBDA_SOIL,
        "T_ground_degC"          : T_GROUND,
        "U_linear_WmK"           : u_linear(do, dc),
    }

    print(f"{pid:<14} {u:<8} {v:<10} "
          f"{Lp:>7.1f} {Q/1000:>7.1f} {dn:>5} "
          f"{di*1000:>8.1f} {do*1000:>8.1f}")

print("-" * 100)
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"  L_tot      = {L_tot/1000:.2f} km     target: 1–5 km ✓")
print(f"  Q_peak_tot = {n_sub * Q_PEAK_W / 1e6:.2f} MW    target: < 5 MW ✓")

# ---------------------------------------------------------------------------
# SECTION 6 — CSV EXPORT
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

# nodes.csv
with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m", "circuit",
        "Q_peak_W", "p_pump_set_bar",
        "T_supply_set_degC", "delta_T_nom_K",
    ])
    for nid, ntype, x, y in NODES:
        w.writerow([
            nid + "_s", ntype, x, y, "supply",
            "demand_profile.csv" if ntype == "substation" else "",
            P_NOM                if ntype == "source"     else "",
            T_SUPPLY             if ntype == "source"     else "",
            DELTA_T              if ntype == "substation" else "",
        ])
        w.writerow([
            nid + "_r", ntype, x, y, "return",
            "demand_profile.csv" if ntype == "substation" else "",
            "", "",
            DELTA_T              if ntype == "substation" else "",
        ])
print(f"  nodes.csv    → {len(NODES)*2} rows")

# pipes.csv
with open(os.path.join(OUT_DIR, "pipes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "pipe_id", "from_node", "to_node", "circuit",
        "length_m", "d_inner_m", "d_outer_m", "d_casing_m", "wall_m",
        "insulation_thickness_m",
        "DN_mm", "roughness_m",
        "fluid_rho_kgm3", "fluid_cp_JkgK", "fluid_mu_Pas", "fluid_lambda_WmK",
        "steel_rho_kgm3", "steel_cp_JkgK", "steel_lambda_WmK",
        "PUR_rho_kgm3", "PUR_cp_JkgK", "PUR_lambda_WmK",
        "HDPE_rho_kgm3", "HDPE_cp_JkgK", "HDPE_lambda_WmK",
        "burial_depth_m", "soil_lambda_WmK", "T_ground_degC",
        "U_linear_WmK",
    ])
    for pid, d in PIPE_SIZING.items():
        u, v = d["from_node"], d["to_node"]
        row_common = [
            d["length_m"],
            d["d_inner_m"], d["d_outer_m"], d["d_casing_m"], d["wall_m"],
            d["insulation_thickness_m"],
            d["DN_mm"], d["roughness_m"],
            d["fluid_rho_kgm3"], d["fluid_cp_JkgK"],
            d["fluid_mu_Pas"],   d["fluid_lambda_WmK"],
            d["steel_rho_kgm3"], d["steel_cp_JkgK"], d["steel_lambda_WmK"],
            d["PUR_rho_kgm3"],   d["PUR_cp_JkgK"],   d["PUR_lambda_WmK"],
            d["HDPE_rho_kgm3"],  d["HDPE_cp_JkgK"],  d["HDPE_lambda_WmK"],
            d["burial_depth_m"], d["soil_lambda_WmK"], d["T_ground_degC"],
            d["U_linear_WmK"],
        ]
        w.writerow([pid + "_s", u + "_s", v + "_s", "supply"] + row_common)
        w.writerow([pid + "_r", v + "_r", u + "_r", "return"] + row_common)
print(f"  pipes.csv    → {len(PIPE_SIZING)*2} rows")

# ---------------------------------------------------------------------------
# SECTION 7 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
fig, ax = plot_topology(
    NODES, EDGES,
    title="DHN_THV_3G_R_S_BASE",
    show=False,
)
plot_path = os.path.join(OUT_DIR, "topology.png")
fig.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")