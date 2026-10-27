# 3G_R_S_BASE.py
#
# Benchmark archetype: 3GDH, Radial, Small
#
# Description
#   Builds the 3G_R_S network, the radial network (tree of two feeders, L = 0), with Methodology I
#   (purpose-driven design, methodology_I.py): the layout of a 500 m x 500 m district with 10
#   substations is prescribed, the pipes are sized on design loads and the simulation-ready
#   files are exported. The three THV archetypes (3G_R_S, 3G_L_S, 3G_M_S) share the same radial
#   base and differ only in the topological template. The result is fully deterministic.
#
# Procedure (Methodology I, build_from_coordinates)
#   Rule 1: exactly 10 substations in a 500 m x 500 m footprint, source in the north-west
#           corner; node coordinates prescribed, pipe length = euclidean distance
#   Rule 2: topological template, nested on a common radial base — radial: tree of two feeders (L = 0)
#   Rule 3: pipe sizing — "tree" design loads (design_loads) and DN with v <= V_LIM = 1.5 m/s
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
from archetypes_generation.networks.methodology_I import build_from_coordinates, design_loads

GEN      = "3G"

# ---------------------------------------------------------------------------
# SECTION 1 — LAYOUT
# Function: prescribes the layout (node coordinates, radial base) and builds the network with the
# nesting rule of Methodology I; pipe length = euclidean distance between the end nodes.
# Call: build_from_coordinates(EDGE_LIST, POSITIONS, topology=..., [ring_closure, chords])
# returns NET (nodes, edges, lengths, added pipes) and checks the expected number of loops.
# Common radial base of the three THV archetypes (3G_R_S, 3G_L_S, 3G_M_S): two feeders along
# the perimeter of a 500 m x 500 m square, source at the north-west corner.
# Coordinates in metres, origin at the source, x to the east, y to the SOUTH.
# Pipe length = euclidean distance between the end nodes.
# Radial: the base itself (L = 0).
# ---------------------------------------------------------------------------
POSITIONS = {
    "src": (0, 0),
    # north feeder (y = 0)
    "a": (200, 0),   "b": (400, 0),   "c": (500, 0),
    # west feeder (x = 0) and south side (y = 500)
    "d": (0, 160),   "e": (0, 330),   "f": (0, 500),
    "g": (120, 500), "h": (300, 500), "i": (420, 500), "j": (500, 500), "k": (500, 450),
    # substations — 20 m service pipes
    "sub1": (200, 20),  "sub2": (400, -20), "sub3": (520, 0),    "sub4": (-20, 160),
    "sub5": (20, 330),  "sub6": (-20, 500), "sub7": (120, 480),  "sub8": (300, 520),
    "sub9": (420, 520), "sub10": (520, 450),
}
EDGE_LIST = [   # radial base: (from_node, to_node) = flow direction of the supply pipe
    ("src", "a"), ("a", "sub1"), ("a", "b"), ("b", "sub2"), ("b", "c"), ("c", "sub3"),
    ("src", "d"), ("d", "sub4"), ("d", "e"), ("e", "sub5"), ("e", "f"), ("f", "sub6"),
    ("f", "g"), ("g", "sub7"), ("g", "h"), ("h", "sub8"), ("h", "i"), ("i", "sub9"),
    ("i", "j"), ("j", "k"), ("k", "sub10"),
]

NET = build_from_coordinates(EDGE_LIST, POSITIONS, topology="radial",
                             expected_loops=0)
NODES, EDGES, PIPE_L = NET["nodes"], NET["edges"], NET["lengths"]

print("Pipe lengths [m]:")
for (u, v), l in PIPE_L.items():
    print(f"  {u:>4} -> {v:<6} {l:7.1f}{'   (added)' if (u, v) in NET['added'] else ''}")

# ---------------------------------------------------------------------------
# SECTION 2 — TOPOLOGY CHECKS (connectivity and L are also checked in build_from_coordinates)
# Function: sanity checks on the built network (number of loops, one source, 10 substations).
# Call: plain asserts; the script stops if the topology is not the intended one.
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
# Function: computes the topological descriptors (N, E, L, alpha, degrees, diameter, total length).
# Call: KPIS dict, printed for reference; the values go into Table A2 of the paper.
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
}

print("\nKPIs:")
for k, v in KPIS.items():
    print(f"  {k:<22} {v}")

# ---------------------------------------------------------------------------
# SECTION 4 — PIPE SIZING
# Function: assigns a design load to every pipe and selects its diameter.
# Call: design_loads(NET, ...) gives the load of each pipe, select_dn(...) the smallest DN with
# v <= V_LIM, pipe_record(...) builds the pipe row stored in PIPE_SIZING.
# "tree" design loads (design_loads): every pipe of the radial base carries the load of the
# substations downstream of it (pieces of a pipe split by a chord inherit it); the closing pipe
# and the chords are sized on ADDED_SUBS substations. DN = smallest catalogue size with
# v <= V_LIM at the design mass flow (select_dn).
# ---------------------------------------------------------------------------
gp       = GEN_OPERATING["3G"]
DELTA_T  = gp["delta_T_nom"]
T_SUPPLY = gp["T_supply_nom"]
P_NOM    = gp["P_nom_bar"]

HEAT_LOSS_FACTOR = 1.05
SIZING_METHOD    = "tree"
ADDED_SUBS       = 2
V_LIM            = 1.5             # m/s, sizing velocity (v_max = 2.5 m/s)

LOADS       = design_loads(NET, Q_PEAK_W, HEAT_LOSS_FACTOR, method=SIZING_METHOD, added_subs=ADDED_SUBS)
SUBSTATIONS = {n[0] for n in NODES if n[1] == "substation"}
ADDED       = set(NET["added"])

PIPE_SIZING = {}

print(f"\n{'pipe_id':<14} {'from':<8} {'to':<10} "
      f"{'L m':>7} {'Q kW':>7} {'DN':>5} {'d_i mm':>8} {'v m/s':>6}  type")
print("-" * 88)

for u, v in EDGES:
    pid   = f"{u}_{v}"
    Lp    = PIPE_L[(u, v)]
    Q     = LOADS[(u, v)]
    ptype = "service" if v in SUBSTATIONS else ("added" if (u, v) in ADDED else "distribution")
    e     = select_dn(GEN, Q, v_lim=V_LIM)
    PIPE_SIZING[pid] = pipe_record(GEN, e, u, v, Lp)
    print(f"{pid:<14} {u:<8} {v:<10} "
          f"{Lp:>7.1f} {Q / 1000:>7.1f} {e['DN']:>5} {e['d_i'] * 1000:>8.1f} {e['velocity']:>6.2f}  [{ptype}]")

print("-" * 88)
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"  L_tot      = {L_tot / 1000:.2f} km   target: 1–5 km {'✓' if 1e3 <= L_tot <= 5e3 else '✗'}")
print(f"  Q_peak_tot = {n_sub * Q_PEAK_W / 1e6:.2f} MW    target: < 5 MW {'✓' if n_sub * Q_PEAK_W < 5e6 else '✗'}")

# ---------------------------------------------------------------------------
# SECTION 5 — CSV EXPORT
# Function: writes nodes.csv (boundary conditions at source and substations) and pipes.csv.
# Call: runs at import; files are written to OUT_DIR.
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
# Function: saves the topology plot (topology.png).
# Call: plot_topology(NODES, EDGES, ...) from plotting.py.
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
# Function: writes the node-pipe incidence matrix (-1 at the starting node, +1 at the end node).
# Call: built from NODES and EDGES; saved as incidence_matrix.csv.
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
