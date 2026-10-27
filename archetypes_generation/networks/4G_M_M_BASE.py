# 4G_M_M_BASE.py
#
# Benchmark archetype: 4GDH, Meshed, Medium
#
# Description
#   Builds the 4G_M_M network with Methodology II (algorithmic generation, methodology_II.py)
#   on the same synthetic district as 3G_M_M (same seed, footprint and beta), with two heat
#   sources: a primary source and a secondary waste-heat source. It sizes the pipes with the
#   N-1 criterion, defines the schedule of the secondary source and exports the simulation-ready
#   files. The same inputs and the same seed always give the same network.
#
# Procedure (Methodology II)
#   Steps 1-2  District synthesis and building allocation   DistrictGenerator, StreetGraphBuilder
#   Step 3     Network topology, constrained Steiner tree   ThermalNetworkBuilder (beta = 1.00, 2 sources)
#   Step 4     Pipe sizing on the N-1 design flow           n1_design_flows, select_dn
#   Export     nodes.csv, pipes.csv, src1_mdot_profile.csv, topology.png, incidence_matrix.csv
#
# Operating conditions (4GDH, mixed dispatch):
#   Control    : (variable flow, constant temperature)
#                but the TWO SOURCES have different, complementary roles:
#
#   src0 — primary source, VF-CT
#          Hydraulic  : "pressure" reference (the network's hydraulic anchor)
#          Thermal    : fixed T_out = 60°C (nominal, BASE peak-winter scenario)
#          Mass flow  : FREE — result of the solver's hydraulic balance
#                       (covers whatever src1 does not supply)
#
#   src1 — secondary source (e.g. industrial waste heat), scheduled CF-CT
#          Hydraulic  : imposed "mass_flow", ON/OFF schedule (Section 6bis):
#                       M_FLOW_NOM_SRC1 (~11 kg/s) Mon-Fri 07:00-20:00,
#                       0 kg/s at night and at weekends
#          Thermal    : fixed T_out = 60°C
#
#   Network-level control: VF-CT — src0 follows the demand at constant T,
#   src1 injects a scheduled constant flow at constant T.
#
# Pipe sizing: as if src0 ALONE supplied the full peak demand (same N-1 rule as
#   3G_M_M_BASE). src1 is non-dispatchable and OFF at weekends, so the worst
#   case is src0-only; src1 is a point injection whose service pipe is sized
#   on its own nominal mass flow.
#
#   delta_T    : 20 K at substations (design)
#   p_ref      : 8 bar (reference pressure at src0)
#   N_sources  : 2 (primary + 1 secondary)
#   Q_peak_sub : 175 kW/substation (uniform, base scenario)
#
# Outputs (archetypes_generation/archetypes/4G_M_M_BASE/):
#   nodes.csv             - node table with boundary conditions
#   pipes.csv             - pipe table with all modelling parameters
#   src1_mdot_profile.csv - weekly mass-flow schedule of the secondary source
#   topology.png          - network topology plot
#   incidence_matrix.csv  - node-pipe incidence matrix
#
# Usage:
#   python archetypes_generation/networks/4G_M_M_BASE.py

import os
import sys
import csv
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR = os.path.join(THIS_DIR, "..", "archetypes", "4G_M_M_BASE")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co

importlib.reload(co)
from archetypes_generation.constants import GEN_OPERATING

from archetypes_generation.demand_profile import (
    Q_PEAK_W, DT_MIN, N_DAY, N_WEEK, DAYS, F_STEADY, timestep_labels,
)

from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv
GEN = "4G"

import archetypes_generation.networks.methodology_II as m2
importlib.reload(m2)
from archetypes_generation.networks.methodology_II import (
    DistrictGenerator,
    StreetGraphBuilder,
    ThermalNetworkBuilder,
    n1_design_flows,
)

# ---------------------------------------------------------------------------
# SECTION 1 — DESIGN PARAMETERS
# Function: all inputs of the archetype in one place (district, constrained Steiner factor,
# 4GDH operating parameters from constants.GEN_OPERATING, peak load and heat-loss factor).
# Call: edit the values here only; the following sections read them.
# ---------------------------------------------------------------------------

# District — identical to 3G_M_M for topology comparability
SEED = 42
WIDTH, HEIGHT = 1200, 800
ROWS, COLS = 5, 7
STREET_W = 15
N_SUB_TARGET = 100
BLOCK_VAR = 0.25
PERTURBATION = 7

# Network
BETA = 1.00  # constrained Steiner flexibility factor

# 4GDH operating parameters
gp = GEN_OPERATING["4G"]
CP = gp["cp"]
DELTA_T = gp["delta_T_nom"]         # 20 K
T_SUPPLY_SRC0 = gp["T_supply_nom"]  # 60°C — primary source
T_SUPPLY_SRC1 = 60.0                # 60°C — secondary source
P_REF_BAR = gp["P_nom_bar"]         # 8 bar, reference pressure at src0

HLF = 1.10  # heat loss factor


print("=" * 60)
print("4G_M_M_BASE — 4GDH | Meshed | Medium | src0, src1")
print("=" * 60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
# Function: Methodology II, Steps 1-2. DistrictGenerator creates the block grid and distributes
# the substations on the block frontages, with the seed above.
# Call: DistrictGenerator(...).generate() returns the district object.
# ---------------------------------------------------------------------------
print("\nStep 1 — District generation...")
district = DistrictGenerator(
    width=WIDTH, height=HEIGHT,
    rows=ROWS, cols=COLS,
    street_width=STREET_W,
    n_substations=N_SUB_TARGET,
    block_variation=BLOCK_VAR,
    perturbation=PERTURBATION,
    seed=SEED,
).generate()

N_SUB = len(district.buildings)
print(f"  Blocks      : {COLS}×{ROWS} = {COLS * ROWS}")
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
# Function: Methodology II, Step 3. Places the two sources (src0 primary, src1 secondary) and grows
# the network from them with the constrained Steiner algorithm.
# Call: ThermalNetworkBuilder(..., generator_pos=[src0, src1]), build_routing_graph(),
# constrained_steiner_tree(beta); metrics() prints N, E, L, alpha.
# ---------------------------------------------------------------------------
print(f"\nStep 3 — Constrained Steiner tree (β={BETA}, 2 sources)...")

# src0 — bottom-left peripheral (col=0, row=0) — main/backup plant
src0_block = district.blocks[0 * district.rows + 0]
gen_pos0   = (src0_block["x"] + src0_block["width"]  / 5,
              src0_block["y"] + src0_block["height"] / 5)

# src1 — right-centre (col=5, row=2) — secondary plant (scheduled CF-CT)
src1_col   = int(COLS * 0.75)
src1_row   = ROWS // 2
src1_block = district.blocks[src1_col * district.rows + src1_row]
gen_pos1   = (src1_block["x"] + src1_block["width"]  * 2/3,
              src1_block["y"] + src1_block["height"] * 2/3)

print(f"  src0 position: {gen_pos0}")
print(f"  src1 position: {gen_pos1}")

tnb = ThermalNetworkBuilder(
    street_graph,
    district,
    generator_pos=[gen_pos0, gen_pos1],
)
tnb.build_routing_graph()
dhn = tnb.constrained_steiner_tree(beta=BETA)

m = tnb.metrics(dhn)
print("\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — NODE EXTRACTION
# Function: converts the graph nodes into the node table (src0, src1, junctions, substations) and a
# map graph node -> node id used in the pipe ids.
# Call: loops over tnb.generator_nodes and dhn.nodes(); returns node_rows and node_id_map.
# ---------------------------------------------------------------------------
rou = tnb.rou
node_id_map = {}
node_rows = []
idx_j = 0

# Sources
for k, gnode in enumerate(tnb.generator_nodes):
    pos = rou.nodes[gnode]["pos"]
    nid = f"src{k}"
    node_id_map[gnode] = nid
    node_rows.append((nid, "source", round(pos[0], 2), round(pos[1], 2)))

# All nodes in DHN
for n in dhn.nodes():
    if n in node_id_map:
        continue
    kind = rou.nodes[n].get("kind", "junction")
    pos = rou.nodes[n]["pos"]
    if kind == "substation":
        b_idx = tnb.building_nodes.index(n)
        nid = f"sub{b_idx}"
        ntype = "substation"
    else:
        nid = f"jun{idx_j}"
        ntype = "junction"
        idx_j += 1
    node_id_map[n] = nid
    node_rows.append((nid, ntype, round(pos[0], 2), round(pos[1], 2)))

print(f"\nNodes: {len(node_rows)} "
      f"(2 sources + {idx_j} junctions + {N_SUB} substations)")


# ---------------------------------------------------------------------------
# SECTION 6 — PIPE SIZING
# Function: Methodology II, Step 4. Pipes are sized on the N-1 design flow of the network supplied by
# src0 alone; the src1 service pipe is sized on the nominal flow of src1.
# Call: n1_design_flows(dhn, [src0], loads) gives (from, to, Q, length, in_loop) per pipe; select_dn
# picks the smallest DN with v <= v_max (Table 1); pipe_record builds the pipe row.
# ---------------------------------------------------------------------------
# The network is sized as if src0 alone supplied the whole peak demand
# (same rule as 3G_M_M_BASE, for comparability). src1 is OFF at night and
# at weekends, so the hydraulic worst case (weekend morning peak) is
# src0-only. src1 is connected as a point injection: its service pipe is
# sized on the src1 nominal mass flow (Section 6bis).
src0_gnode, src1_gnode = tnb.generator_nodes[0], tnb.generator_nodes[1]

# Nominal mass flows (also used in Section 6bis)
M_FLOW_NOM_TOTAL  = round(N_SUB * Q_PEAK_W / (CP * DELTA_T), 3)
M_FLOW_BASE_LOAD  = round(F_STEADY * M_FLOW_NOM_TOTAL, 3)
SRC1_SUPPORT_FRAC = 0.15
M_FLOW_NOM_SRC1   = round(SRC1_SUPPORT_FRAC * M_FLOW_BASE_LOAD, 3)
Q_NOM_SRC1_W      = M_FLOW_NOM_SRC1 * CP * DELTA_T

sub_set = set(tnb.building_nodes)

N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, "
      f"is_meshed={not nx.is_tree(dhn)}")

if dhn.degree(src1_gnode) != 1:
    raise RuntimeError("src1 is expected to be a leaf of the DHN graph "
                       "(single service pipe); revise the src1 sizing rule.")


# N-1 sizing (Methodology II, Step 4): maximum, over the intact network and over every
# single-pipe outage, of the peak load of the substations downstream of the pipe
N1_ROWS   = n1_design_flows(dhn, [src0_gnode], {n: Q_PEAK_W * HLF for n in sub_set},
                            q_min=Q_PEAK_W * HLF)
N1_Q      = {frozenset((a, b)): q      for a, b, q, _, _ in N1_ROWS}
N1_ORIENT = {frozenset((a, b)): (a, b) for a, b, _, _, _ in N1_ROWS}   # BFS orientation from src0

PIPE_SIZING = {}

for u, v in dhn.edges():
    if src1_gnode in (u, v):
        # src1 service pipe: oriented in the injection direction and sized
        # on the nominal src1 flow (it never carries demand-driven flow)
        from_n = src1_gnode
        to_n   = v if u == src1_gnode else u
        Q      = Q_NOM_SRC1_W
    else:
        from_n, to_n = N1_ORIENT[frozenset((u, v))]
        Q = N1_Q[frozenset((u, v))]
    data = dhn.edges[u, v]
    Lp = round(data.get("length", 0.0), 2)
    e = select_dn(GEN, Q)
    uid = node_id_map.get(from_n, str(from_n))
    vid = node_id_map.get(to_n, str(to_n))
    pid = f"{uid}_{vid}"
    PIPE_SIZING[pid] = pipe_record(GEN, e, uid, vid, Lp)

L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"\nPipes: {len(PIPE_SIZING)} sized")
print(f"  L_tot  = {L_tot / 1000:.2f} km")
print(f"  Q_tot  = {N_SUB * Q_PEAK_W / 1e6:.2f} MW")

# ---------------------------------------------------------------------------
# SECTION 6bis — SECONDARY SOURCE (src1) SIZING + DISPATCH-COUPLED PROFILE
# Function: sizes the nominal flow of src1 (15 % of the base-load flow) and writes its weekly
# schedule (ON Mon-Fri 07:00-20:00, OFF otherwise).
# Call: runs at import; writes src1_mdot_profile.csv to OUT_DIR.
# ---------------------------------------------------------------------------
# The nominal flow delivered by src1 (M_FLOW_NOM_SRC1, computed in Section 6)
# is 15% of the flow needed to cover the network base load (F_STEADY).

print("\nSecondary source sizing (src1, industrial waste heat, base-load coupled):")
print(f"  Total network capacity: {M_FLOW_NOM_TOTAL} kg/s")
print(f"  Network base-load flow: {M_FLOW_BASE_LOAD} kg/s (F_STEADY={F_STEADY})")
print(f"  Mass flow cap for src1 : {M_FLOW_NOM_SRC1} kg/s "
      f"({SRC1_SUPPORT_FRAC*100:.0f}% of base-load flow, "
      f"{100*M_FLOW_NOM_SRC1/M_FLOW_NOM_TOTAL:.1f}% of total network capacity)")
print(f"  Equivalent thermal power: {M_FLOW_NOM_SRC1 * CP * DELTA_T / 1e6:.2f} MW")
print(f"  T_supply src1          : {T_SUPPLY_SRC1} °C (fixed)")

F_SHIFT_ON  = 1.00
F_SHIFT_OFF = 0.00
WEEKEND_DAYS = {"Sat", "Sun"}

def _build_src1_daily_shape():
    shape = []
    for t in range(N_DAY):
        h_frac = t / (60 // DT_MIN)
        f = F_SHIFT_ON if 7.0 <= h_frac < 20.0 else F_SHIFT_OFF
        shape.append(round(f, 4))
    return shape

SRC1_DAILY_SHAPE = _build_src1_daily_shape()

SRC1_WEEKLY_SHAPE_POTENTIAL = []
for day in DAYS:
    if day in WEEKEND_DAYS:
        SRC1_WEEKLY_SHAPE_POTENTIAL += [F_SHIFT_OFF] * N_DAY
    else:
        SRC1_WEEKLY_SHAPE_POTENTIAL += SRC1_DAILY_SHAPE

# src1 schedule: constant nominal flow when ON, zero when OFF.
# (During the ON window the network demand never drops below the base load,
#  ~73 kg/s >> M_FLOW_NOM_SRC1, so no curtailment is ever needed.)
SRC1_WEEKLY_MDOT = [round(f * M_FLOW_NOM_SRC1, 4) for f in SRC1_WEEKLY_SHAPE_POTENTIAL]

SRC1_PROFILE_FILE = "src1_mdot_profile.csv"
labels = timestep_labels()

with open(os.path.join(OUT_DIR, SRC1_PROFILE_FILE), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestep", "label", "f_normalised", "mdot_kg_s"])
    for t in range(N_WEEK):
        f_norm = round(SRC1_WEEKLY_MDOT[t] / M_FLOW_NOM_SRC1, 4) if M_FLOW_NOM_SRC1 > 0 else 0
        w.writerow([t, labels[t], f_norm, SRC1_WEEKLY_MDOT[t]])

print(f"  {SRC1_PROFILE_FILE} → {N_WEEK} rows "
      f"(peak {max(SRC1_WEEKLY_MDOT):.2f} kg/s, min {min(SRC1_WEEKLY_MDOT):.2f} kg/s)")

# ---------------------------------------------------------------------------
# SECTION 7 — CSV EXPORT
# Function: writes nodes.csv (boundary conditions at the two sources and the substations) and pipes.csv.
# Call: runs at import; files are written to OUT_DIR.
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

# Per-source parameters, keyed by the same "src{k}" id used in node_rows
SOURCE_PARAMS = {
    "src0": {"m_flow_nom": "",                 "T_supply": T_SUPPLY_SRC0},
    "src1": {"m_flow_nom": SRC1_PROFILE_FILE,  "T_supply": T_SUPPLY_SRC1},
}

with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["node_id", "node_type", "x_m", "y_m",
                "Q_peak_W", "m_flow_set_kg_s",
                "T_supply_set_degC", "delta_T_nom_K", "p_pump_set_bar"])
    for nid, ntype, x, y in node_rows:
        if ntype == "source":
            sp = SOURCE_PARAMS[nid]
            w.writerow([nid, ntype, x, y,
                        "",                  # Q_peak — not applicable
                        sp["m_flow_nom"],    # "" for src0 (free), fixed for src1
                        sp["T_supply"],      # 60°C src0, 60°C src1
                        "",
                        P_REF_BAR if nid == "src0" else ""])
        elif ntype == "substation":
            w.writerow([nid, ntype, x, y,
                        "demand_profile.csv",
                        "",  # free — computed by solver
                        "",
                        DELTA_T,  # 20 K
                        ""])
        else:
            w.writerow([nid, ntype, x, y, "", "", "", "", ""])

print(f"  nodes.csv  → {len(node_rows)} rows")

write_pipes_csv(os.path.join(OUT_DIR, "pipes.csv"), PIPE_SIZING)
print(f"  pipes.csv  → {len(PIPE_SIZING)} rows")

# ---------------------------------------------------------------------------
# SECTION 8 — TOPOLOGY PLOT
# Function: saves the topology plot (topology.png) of the generated network.
# Call: tnb.plot(dhn=dhn, ...) draws it, then it is saved with matplotlib.
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn, title="4G_M_M_BASE", show=False)
plot_path = os.path.join(OUT_DIR, "topology.png")
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
