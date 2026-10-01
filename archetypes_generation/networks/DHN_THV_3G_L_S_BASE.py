# DHN_THV_3G_L_S_BASE.py
#
# Benchmark archetype: Thermo-Hydraulic Validation, 3GDH, Ring, Small
#
# Methodology I — Purpose-driven design
#   Rule 1: exactly 10 substations
#   Rule 2: pipe lengths sampled from U[100, 200] m, seed=42
#   Rule 3: ring topology — single closed main loop, 1 independent hydraulic loop
#
# Outputs (archetypes_generation/archetypes/DHN_THV_3G_L_S_BASE/):
#   nodes.csv     — node table with boundary conditions (supply + return)
#   pipes.csv     — pipe table with all modelling parameters
#   topology.png  — network topology plot (paper-ready, 300 dpi)
#
# Usage:
#   python archetypes_generation/networks/DHN_THV_3G_L_S_BASE.py

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
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "DHN_THV_3G_L_S_BASE")
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

# ---------------------------------------------------------------------------
# SECTION 1 — PIPE LENGTHS
# Sampled from U[100, 200] m, seed=42.
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)

EDGE_LIST = [
    # ring — 9 pipes forming the closed loop
    ("src", "a"),
    ("a",   "b"),
    ("b",   "c"),
    ("c",   "d"),
    ("d",   "e"),
    ("e",   "f"),
    ("f",   "g"),
    ("g",   "h"),
    ("h",   "src"),
    # radial branches — 2 substations per junction
    ("a",   "sub1"),
    ("a",   "sub2"),
    ("b",   "sub3"),
    ("b",   "sub4"),
    ("d",   "sub5"),
    ("d",   "sub6"),
    ("f",   "sub7"),
    ("f",   "sub8"),
    ("h",   "sub9"),
    ("h",   "sub10"),
]

PIPE_L = {}
for u, v in EDGE_LIST:
    PIPE_L[(u, v)] = round(random.uniform(100, 200), 1)

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

EDGES = EDGE_LIST

# ---------------------------------------------------------------------------
# SECTION 3 — TOPOLOGY CHECKS
# ---------------------------------------------------------------------------
N = len(NODES)
E = len(EDGES)
L = E - N + 1

assert N == 19, f"Expected 19 nodes, got {N}"
assert E == 19, f"Expected 19 edges, got {E}"
assert L == 1,  f"Expected 1 loop, got {L}"
assert sum(1 for n in NODES if n[1] == "source")     == 1
assert sum(1 for n in NODES if n[1] == "junction")   == 8
assert sum(1 for n in NODES if n[1] == "substation") == 10

print(f"Topology OK — N={N}, E={E}, L={L}")

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
    "network_code"     : "DHN_THV_3G_L_S_BASE",
    "generation"       : "3G",
    "topology"         : "ring",
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
    R_ins  = math.log(d_casing / d_o)              / (2 * math.pi * LAMBDA_PUR)
    R_soil = math.log(2 * BURIAL_DEPTH / d_casing) / (2 * math.pi * LAMBDA_SOIL)
    return round(1.0 / (R_ins + R_soil), 4)


def select_dn(Q_w):
    mdot = Q_w / (CP * DELTA_T)
    for dn, (di, do, s, dc, sc) in sorted(PIPE_CATALOGUE.items()):
        A = math.pi * di**2 / 4.0
        v = mdot / (RHO * A)
        if v <= V_MAX:
            return dn, di, do, dc, s, sc
    dn, (di, do, s, dc, sc) = sorted(PIPE_CATALOGUE.items())[-1]
    return dn, di, do, dc, s, sc


# --- NUOVO: identifica i 9 tratti dell'anello principale ---
RING_SET = {
    ("src", "a"), ("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"),
    ("e", "f"), ("f", "g"), ("g", "h"), ("h", "src"),
}

Q_total = n_sub * Q_PEAK_W * HEAT_LOSS_FACTOR

PIPE_SIZING = {}

print(f"\n{'pipe_id':<14} {'from':<8} {'to':<10} "
      f"{'L m':>7} {'Q kW':>7} {'DN':>5} "
      f"{'d_i mm':>8} {'d_o mm':>8}  type")
print("-" * 85)

for u, v in EDGES:

    pid = f"{u}_{v}"
    Lp  = PIPE_L[(u, v)]

    # --- NUOVO: distinzione tra tratto di anello e ramo alla sottostazione ---
    if (u, v) in RING_SET:
        Q = round(Q_total / 2, 1)   # anello: ripartizione simmetrica del carico totale
        ptype = "ring"
    else:
        Q = round(Q_PEAK_W * HEAT_LOSS_FACTOR, 1)   # ramo: singola sottostazione
        ptype = "branch"

    dn, di, do, dc, s, sc = select_dn(Q)

    ins_t = round((dc - do) / 2 - sc, 5)

    PIPE_SIZING[pid] = {
        # --- identification ---
        "from_node"              : u,
        "to_node"                : v,
        # --- geometry ---
        "length_m"               : Lp,
        "DN_mm"                  : dn,
        "d_inner_m"              : di,
        "d_outer_m"              : do,
        "wall_m"                 : s,
        "insulation_thickness_m" : ins_t,
        "casing_thickness_m"     : sc,
        "d_casing_m"             : dc,
        # --- hydraulic ---
        "roughness_mm"            : ROUGHNESS_STEEL,
        # --- fluid properties ---
        "fluid_rho_kgm3"         : RHO,
        "fluid_cp_JkgK"          : CP,
        "fluid_mu_Pas"           : gp["mu"],
        "fluid_lambda_WmK"       : gp["lambda"],
        # --- steel carrier pipe ---
        "steel_rho_kgm3"         : RHO_STEEL,
        "steel_cp_JkgK"          : CP_STEEL,
        "steel_lambda_WmK"       : LAMBDA_STEEL,
        # --- PUR foam insulation ---
        "PUR_rho_kgm3"           : RHO_PUR,
        "PUR_cp_JkgK"            : CP_PUR,
        "PUR_lambda_WmK"         : LAMBDA_PUR,
        # --- HDPE casing ---
        "HDPE_rho_kgm3"          : RHO_HDPE,
        "HDPE_cp_JkgK"           : CP_HDPE,
        "HDPE_lambda_WmK"        : LAMBDA_HDPE,
        # --- burial and soil ---
        "burial_depth_m"         : BURIAL_DEPTH,
        "soil_lambda_WmK"        : LAMBDA_SOIL,
        "T_ground_degC"          : T_GROUND,
        "h_ext_Wm2K"             : H_EXT,
        # --- heat loss coefficients ---
        "U_linear_WmK"           : u_linear(do, dc),
        "U_Wm2K"                 : round(u_linear(do, dc) / (math.pi * do), 4),
    }

    print(f"{pid:<14} {u:<8} {v:<10} "
          f"{Lp:>7.1f} {Q/1000:>7.1f} {dn:>5} "
          f"{di*1000:>8.1f} {do*1000:>8.1f}  {ptype}")

print("-" * 85)
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"  L_tot      = {L_tot/1000:.2f} km   target: 1–5 km ✓")
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
with open(os.path.join(OUT_DIR, "pipes.csv"), "w", newline="") as f:
    fieldnames = ["pipe_id"] + list(next(iter(PIPE_SIZING.values())).keys())
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for pid, d in PIPE_SIZING.items():
        w.writerow({"pipe_id": pid, **d})
print(f"  pipes.csv    -> {len(PIPE_SIZING)} rows, "
      f"{len(next(iter(PIPE_SIZING.values())))+1} columns")

# ---------------------------------------------------------------------------
# SECTION 7 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
fig, ax = plot_topology(
    NODES, EDGES,
    title="DHN_THV_3G_L_S_BASE",
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