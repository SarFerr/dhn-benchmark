# 3G_M_L_BASE.py
#
# Benchmark archetype 3G_M_L: 3GDH, Meshed, Large.
#
# Description
#   Builds the 3G_M_L network with Methodology II (algorithmic generation, methodology_II.py),
#   sizes its pipes and exports the simulation-ready files. The network is generated on a
#   synthetic urban district with a single centralised source; the same inputs and the same
#   seed always give the same network.
#
# Procedure (Methodology II)
#   Steps 1-2  District synthesis and building allocation   DistrictGenerator, StreetGraphBuilder
#   Step 3     Network topology, constrained Steiner tree   ThermalNetworkBuilder (beta = 1.00)
#   Step 4     Pipe sizing on the N-1 design flow           n1_design_flows, select_dn
#   Export     nodes.csv, pipes.csv, topology.png, incidence_matrix.csv
#
# Operating conditions (3GDH, Table 1 of the paper)
#   Control    : VF-CT (variable flow, constant temperature)
#   T_supply   : 80 degC (temperature set-point)
#   delta_T    : 30 K at substations
#   p_ref      : 10 bar (relative, at source)
#   N_sources  : 1 (CHP plant, peripheral position)
#   Q_peak_sub : 175 kW/substation (uniform, base scenario)
#
# Outputs (archetypes_generation/archetypes/3G_M_L_BASE/):
#   nodes.csv             - node table with boundary conditions
#   pipes.csv             - pipe table with all modelling parameters
#   topology.png          - network topology plot
#   incidence_matrix.csv  - node-pipe incidence matrix
#
# Usage:
#   python archetypes_generation/networks/3G_M_L_BASE.py

import os
import sys
import csv
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "3G_M_L_BASE")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co
importlib.reload(co)
from archetypes_generation.constants import GEN_OPERATING
from archetypes_generation.demand_profile import Q_PEAK_W
from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv
GEN = "3G"

import archetypes_generation.networks.methodology_II as m2
importlib.reload(m2)
from archetypes_generation.networks.methodology_II import (
    DistrictGenerator,
    StreetGraphBuilder,
    ThermalNetworkBuilder,
    extract_nodes,
    n1_design_flows,
)

# ---------------------------------------------------------------------------
# SECTION 1 — DESIGN PARAMETERS
# Function: all inputs of the archetype in one place (district, constrained Steiner factor,
# 3GDH operating parameters from constants.GEN_OPERATING, peak load and heat-loss factor).
# Call: edit the values here only; the following sections read them.
# ---------------------------------------------------------------------------

# District
SEED            = 42
WIDTH, HEIGHT   = 4000, 3000  # m
ROWS,  COLS     = 12,  16
STREET_W        = 15          # m
N_SUB_TARGET    = 400
BLOCK_VAR       = 0.25
PERTURBATION    = 8           # m

# Network
BETA            = 1.00        # constrained Steiner flexibility factor

# 3GDH operating parameters (VF-CT)
gp          = GEN_OPERATING["3G"]
DELTA_T     = gp["delta_T_nom"]    # 30 K
T_SUPPLY    = gp["T_supply_nom"]   # 80°C
P_REF_BAR   = gp["P_nom_bar"]      # bar

HLF         = 1.25                 # heat loss factor

print("="*60)
print("3G_M_L_BASE — 3GDH | Meshed | Large | VF-CT")
print("="*60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
# Function: Methodology II, Steps 1-2. DistrictGenerator creates the block grid and distributes
# the substations on the block frontages, with the seed above.
# Call: DistrictGenerator(...).generate() returns the district object.
# ---------------------------------------------------------------------------
print("\nStep 1 — District generation...")
district = DistrictGenerator(
    width=WIDTH, height=HEIGHT,
    rows=ROWS,   cols=COLS,
    street_width     = STREET_W,
    n_substations    = N_SUB_TARGET,
    block_variation  = BLOCK_VAR,
    perturbation     = PERTURBATION,
    seed             = SEED,
).generate()

N_SUB = len(district.buildings)
print(f"  Blocks      : {COLS}×{ROWS} = {COLS*ROWS}")
print(f"  Substations : {N_SUB}")

# ---------------------------------------------------------------------------
# SECTION 3 — STREET GRAPH
# Function: StreetGraphBuilder turns the street centrelines of the district into the weighted
# graph on which the network is routed.
# Call: StreetGraphBuilder(district).build() returns the street graph.
# ---------------------------------------------------------------------------
print("\nStep 2 — Street graph...")
street_graph = StreetGraphBuilder(district).build()
print(f"  Nodes: {street_graph.number_of_nodes()}, "
      f"Edges: {street_graph.number_of_edges()}")

# ---------------------------------------------------------------------------
# SECTION 4 — NETWORK TOPOLOGY (constrained Steiner)
# Function: Methodology II, Step 3. ThermalNetworkBuilder projects substations and source on the
# street graph and grows the network from the source with the constrained Steiner algorithm.
# Call: build_routing_graph(), then constrained_steiner_tree(beta); metrics() prints N, E, L, alpha.
# ---------------------------------------------------------------------------
print(f"\nStep 3 — Constrained Steiner tree (β={BETA})...")

# Source position — bottom-left peripheral block (col=0, row=0)
src_block = district.blocks[0 * district.rows + 0]
gen_pos   = (src_block["x"] + src_block["width"]  / 5,
             src_block["y"] + src_block["height"] / 5)

# Single source — pass as tuple (identical to test_1 usage)
tnb = ThermalNetworkBuilder(street_graph, district, gen_pos)
tnb.build_routing_graph()
dhn = tnb.constrained_steiner_tree(beta=BETA)

m = tnb.metrics(dhn)
print("\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — NODE EXTRACTION
# Function: converts the graph nodes into the node table (source, junctions, substations) and a
# map graph node -> node id used in the pipe ids.
# Call: extract_nodes(tnb, dhn) returns (node_rows, node_id_map).
# ---------------------------------------------------------------------------
node_rows, node_id_map = extract_nodes(tnb, dhn)
idx_j = sum(1 for r in node_rows if r[1] == "junction")

print(f"\nNodes: {len(node_rows)} "
      f"(1 source + {idx_j} junctions + {N_SUB} substations)")

# ---------------------------------------------------------------------------
# SECTION 6 — PIPE SIZING
# Function: Methodology II, Step 4. Every pipe is sized on its N-1 design flow: the maximum, over the
# intact network and every single-pipe outage, of the peak load of the downstream substations
# (times the heat-loss factor). select_dn picks the smallest DN with v <= v_max (Table 1).
# Call: n1_design_flows(dhn, sources, loads) returns (from, to, Q, length, in_loop) per pipe;
# pipe_record builds the pipe row.
# ---------------------------------------------------------------------------



# Topology check
N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, "
      f"is_tree={nx.is_tree(dhn)}, is_meshed={not nx.is_tree(dhn)}")

# N-1 sizing (Methodology II, Step 4): the design flow of each pipe is the maximum, over the
# intact network and over every single-pipe outage, of the peak load of the substations
# downstream of it (BFS orientation from the source in each scenario)
PIPE_SIZING = {}
SUB_LOAD    = {n: Q_PEAK_W * HLF for n in tnb.building_nodes}
N1_ROWS     = n1_design_flows(dhn, [tnb.generator_nodes[0]], SUB_LOAD, q_min=Q_PEAK_W * HLF)

for from_n, to_n, Q, length, in_loop in N1_ROWS:
    Lp    = round(length, 2)
    e     = select_dn(GEN, Q)
    uid   = node_id_map.get(from_n, str(from_n))
    vid   = node_id_map.get(to_n,   str(to_n))
    pid   = f"{uid}_{vid}"
    PIPE_SIZING[pid] = pipe_record(GEN, e, uid, vid, Lp)

L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"\nPipes: {len(PIPE_SIZING)} sized")
print(f"  L_tot  = {L_tot/1000:.2f} km")
print(f"  Q_tot  = {N_SUB*Q_PEAK_W/1e6:.2f} MW")

# ---------------------------------------------------------------------------
# SECTION 7 — CSV EXPORT
# Function: writes nodes.csv (boundary conditions at source and substations) and pipes.csv.
# Call: runs at import; files are written to OUT_DIR.
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

with open(os.path.join(OUT_DIR,"nodes.csv"),"w",newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m",
        "Q_peak_W", "p_pump_set_bar",
        "T_supply_set_degC", "delta_T_nom_K",
    ])
    for nid, ntype, x, y in node_rows:
        if ntype == "source":
            w.writerow([nid,ntype,x,y,
                        "",            # Q_peak — not applicable
                        P_REF_BAR,
                        T_SUPPLY])
        elif ntype == "substation":
            w.writerow([nid,ntype,x,y,
                        "demand_profile.csv",
                        "",
                        "",
                        DELTA_T])
        else:
            w.writerow([nid,ntype,x,y,"","","",""])

print(f"  nodes.csv  → {len(node_rows)} rows")

write_pipes_csv(os.path.join(OUT_DIR, "pipes.csv"), PIPE_SIZING)
print(f"  pipes.csv  → {len(PIPE_SIZING)} rows")

# ---------------------------------------------------------------------------
# SECTION 8 — TOPOLOGY PLOT
# Function: saves the topology plot (topology.png) of the generated network.
# Call: tnb.plot(dhn=dhn, ...) draws it, then it is saved with matplotlib.
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn,
         title="3G_M_L_BASE",
         show=False)

plot_path = os.path.join(OUT_DIR,"topology.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")

# ---------------------------------------------------------------------------
# SECTION 9 — INCIDENCE MATRIX
# Function: writes the node-pipe incidence matrix (-1 at the starting node, +1 at the end node).
# Call: built from PIPE_SIZING and node_rows; saved as incidence_matrix.csv.
# ---------------------------------------------------------------------------

node_ids  = [r[0] for r in node_rows]
edge_ids  = list(PIPE_SIZING.keys())                      # pipe_id = "<from>_<to>"
node_pos  = {n: i for i, n in enumerate(node_ids)}
edge_ends = [(node_pos[d["from_node"]], node_pos[d["to_node"]])
             for d in PIPE_SIZING.values()]

with open(os.path.join(OUT_DIR, "incidence_matrix.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["node_id"] + edge_ids)
    for i, node in enumerate(node_ids):
        w.writerow([node] + [-1 if u == i else (1 if v == i else 0)
                             for u, v in edge_ends])

print(f"  incidence_matrix.csv → {len(node_ids)} x {len(edge_ids)}")
