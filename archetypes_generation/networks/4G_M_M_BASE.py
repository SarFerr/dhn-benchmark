# 4G_M_M_BASE.py
#
# Benchmark archetype: 4GDH, Meshed, Medium
#
# Methodology II — Algorithmic generation
#   Step 1: Synthetic urban district
#   Step 2: Street graph
#   Step 3: Constrained Steiner tree beta=1.00
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
# Pipe sizing: as if src0 ALONE supplied the full peak demand (same rule as
#   3G_M_M_BASE). src1 is non-dispatchable and OFF at weekends, so the worst
#   case is src0-only; src1 is a point injection whose service pipe is sized
#   on its own nominal mass flow.
#
#   delta_T    : 20 K at substations (design)
#   p_ref      : 8 bar (reference pressure at src0)
#   N_sources  : 2 (primary + 1 secondary)
#   Q_peak_sub : 175 kW/substation (uniform, base scenario)
#
# Outputs:
#   nodes.csv, pipes.csv, topology.png, src1_mdot_profile.csv

import os
import sys
import csv
import math
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
from archetypes_generation.constants import (
    GEN_OPERATING, PIPE_CATALOGUE,
    LAMBDA_STEEL, LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL,
    ROUGHNESS_STEEL, BURIAL_DEPTH, H_EXT, T_GROUND,
    RHO_STEEL, CP_STEEL,
    RHO_PUR, CP_PUR,
    RHO_HDPE, CP_HDPE,
)

from archetypes_generation.demand_profile import (
    Q_PEAK_W, DT_MIN, N_DAY, N_WEEK, DAYS, WEEKLY_SHAPE, F_STEADY, timestep_labels,
)

from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv, PipeSizingError
GEN = "4G"

import archetypes_generation.networks.methodology_II as m2
importlib.reload(m2)
from archetypes_generation.networks.methodology_II import (
    DistrictGenerator,
    StreetGraphBuilder,
    ThermalNetworkBuilder,
)

# ---------------------------------------------------------------------------
# SECTION 1 — DESIGN PARAMETERS
# ---------------------------------------------------------------------------

# District — identical to TG-3 for topology comparability
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
RHO = gp["rho"]
CP = gp["cp"]
DELTA_T = gp["delta_T_nom"]         # 20 K
V_MAX = gp["v_max"]
T_SUPPLY_SRC0 = gp["T_supply_nom"]  # 60°C — primary source
T_SUPPLY_SRC1 = 60.0                # 60°C — secondary source
P_REF_BAR = gp["P_nom_bar"]         # 8 bar, reference pressure at src0

Q_PEAK_W = Q_PEAK_W  # W per substation
HLF = 1.10  # heat loss factor


def unpack_pipe(vals):
    # PIPE_CATALOGUE: (di, do, s, dc, sc)
    return vals[0], vals[1], vals[2], vals[3], vals[4]


print("=" * 60)
print("4G_M_M_BASE — 4GDH | Meshed | Medium | src0, src1")
print("=" * 60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
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
# ---------------------------------------------------------------------------
print("\nStep 2 — Street graph...")
street_graph = StreetGraphBuilder(district).build()
print(f"  Nodes: {street_graph.number_of_nodes()}, "
      f"Edges: {street_graph.number_of_edges()}")

# ---------------------------------------------------------------------------
# SECTION 4 — NETWORK TOPOLOGY (constrained Steiner)
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
print(f"\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — NODE EXTRACTION
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
# ---------------------------------------------------------------------------
# The network is sized as if src0 alone supplied the whole peak demand
# (same rule as 3G_M_M_BASE, for TG comparability). src1 is OFF at night and
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

# Orient the network from src0 via BFS — used ONLY for downstream load.
# All edges of dhn (including loop-closing edges) are sized.
G_dir   = nx.DiGraph(nx.bfs_tree(dhn, src0_gnode))
sub_set = set(tnb.building_nodes)

N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, "
      f"is_meshed={not nx.is_tree(dhn)}")

if dhn.degree(src1_gnode) != 1:
    raise RuntimeError("src1 is expected to be a leaf of the DHN graph "
                       "(single service pipe); revise the src1 sizing rule.")


def downstream_sub_count(node):
    """Substations reachable downstream from node (BFS orientation from src0)."""
    try:
        desc = nx.descendants(G_dir, node) | {node}
    except Exception:
        desc = {node}
    return sum(1 for n in desc if n in sub_set)


PIPE_SIZING = {}

for u, v in dhn.edges():
    if src1_gnode in (u, v):
        # src1 service pipe: oriented in the injection direction and sized
        # on the nominal src1 flow (it never carries demand-driven flow)
        from_n = src1_gnode
        to_n   = v if u == src1_gnode else u
        Q      = Q_NOM_SRC1_W
    else:
        if G_dir.has_edge(u, v):
            from_n, to_n = u, v
        elif G_dir.has_edge(v, u):
            from_n, to_n = v, u
        else:
            from_n, to_n = u, v
        n_down = max(downstream_sub_count(to_n), 1)
        Q = n_down * Q_PEAK_W * HLF
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
# ---------------------------------------------------------------------------
# The nominal flow delivered by src1 (M_FLOW_NOM_SRC1, computed in Section 6)
# is 15% of the flow needed to cover the network base load (F_STEADY).

print(f"\nSecondary source sizing (src1, industrial waste heat, base-load coupled):")
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

print(f"  {SRC1_PROFILE_FILE} → {N_WEEK} righe "
      f"(peak {max(SRC1_WEEKLY_MDOT):.2f} kg/s, min {min(SRC1_WEEKLY_MDOT):.2f} kg/s)")

# ---------------------------------------------------------------------------
# SECTION 7 — CSV EXPORT
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
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn, title="4G_M_M_BASE", show=False)
plot_path = os.path.join(OUT_DIR, "topology.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")

# ---------------------------------------------------------------------------
# SECTION 9 — INCIDENCE MATRIX
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