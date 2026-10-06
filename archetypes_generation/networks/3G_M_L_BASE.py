# 3G_M_L_BASE.py
#
# Benchmark archetype: 3GDH, Meshed, Large
#
# Methodology II — Algorithmic generation
#   Step 1: Synthetic urban district (DistrictGenerator)
#   Step 2: Street graph (StreetGraphBuilder)
#   Step 3: Constrained Steiner tree beta=1.00 (ThermalNetworkBuilder)
#
# # Operating conditions (3GDH):
#   Control    : VF-CT (variable flow, constant temperature)
#   T_supply   : 80°C (temperature set-point)
#   delta_T    : 30 K at substations
#   p_ref      : 10 bar (relative, at source)
#   N_sources  : 1 (CHP plant, peripheral position)
#   Q_peak_sub : 175 kW/substation (uniform, base scenario)
#
# Outputs:
#   nodes.csv, pipes.csv, topology.png

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
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "3G_M_L_BASE")
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
from archetypes_generation.demand_profile import Q_PEAK_W
from archetypes_generation.pipe_system import select_dn, pipe_record, write_pipes_csv, PipeSizingError
GEN = "3G"

sys.path.insert(0, os.path.join(REPO_ROOT, "dhn_benchmark", "networks"))
from synthetic_district import (
    DistrictGenerator,
    StreetGraphBuilder,
    ThermalNetworkBuilder,
)

# ---------------------------------------------------------------------------
# SECTION 1 — DESIGN PARAMETERS
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
MESH_EDGES      = max(1, round(0.05 * N_SUB_TARGET))   # loop-closing edges = 5 % of substations


# 3GDH operating parameters (VF-CT)
gp          = GEN_OPERATING["3G"]
RHO         = gp["rho"]
CP          = gp["cp"]
DELTA_T     = gp["delta_T_nom"]    # 30 K
V_MAX       = gp["v_max"]          # 2.5 m/s
T_SUPPLY    = gp["T_supply_nom"]   # 80°C
P_REF_BAR   = gp["P_nom_bar"]      # bar

Q_PEAK_W    = Q_PEAK_W             # W per substation
HLF         = 1.25                 # heat loss factor

def unpack_pipe(vals):
    # PIPE_CATALOGUE: (di, do, s, dc, sc)
    return vals[0], vals[1], vals[2], vals[3], vals[4]

print("="*60)
print("3G_M_L_BASE — 3GDH | Meshed | Large | VF-CT")
print("="*60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
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
# ---------------------------------------------------------------------------
print("\nStep 2 — Street graph...")
street_graph = StreetGraphBuilder(district).build()
sg_stats     = StreetGraphBuilder(district)
sg_stats.graph = street_graph
print(f"  Nodes: {street_graph.number_of_nodes()}, "
      f"Edges: {street_graph.number_of_edges()}")

# ---------------------------------------------------------------------------
# SECTION 4 — NETWORK TOPOLOGY (constrained Steiner)
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
print(f"\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 5 — NODE EXTRACTION
# ---------------------------------------------------------------------------
rou = tnb.rou
node_id_map  = {}
node_rows    = []
idx_j = 0

# Source(s)
for k, gnode in enumerate(tnb.generator_nodes):
    pos = rou.nodes[gnode]["pos"]
    nid = "src" if k == 0 else f"src_{k}"
    node_id_map[gnode] = nid
    node_rows.append((nid, "source", round(pos[0],2), round(pos[1],2)))

# All nodes in DHN
for n in dhn.nodes():
    if n in node_id_map:
        continue
    kind = rou.nodes[n].get("kind", "junction")
    pos  = rou.nodes[n]["pos"]
    if kind == "substation":
        b_idx = tnb.building_nodes.index(n)
        nid   = f"sub{b_idx}"
        ntype = "substation"
    else:
        nid   = f"jun{idx_j}"
        ntype = "junction"
        idx_j += 1
    node_id_map[n] = nid
    node_rows.append((nid, ntype, round(pos[0],2), round(pos[1],2)))

print(f"\nNodes: {len(node_rows)} "
      f"(1 source + {idx_j} junctions + {N_SUB} substations)")

# ---------------------------------------------------------------------------
# SECTION 6 — PIPE SIZING
# ---------------------------------------------------------------------------



# Orient network from source via BFS for downstream load
# Orient network from source via BFS — used ONLY for downstream load
# G_dir is used to compute load direction, NOT to enumerate pipes
# All edges of dhn (including loop-closing edges) are sized
src_gnode = tnb.generator_nodes[0]
G_dir     = nx.DiGraph(nx.bfs_tree(dhn, src_gnode))
sub_set   = set(tnb.building_nodes)

# Topology check
N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, "
      f"is_tree={nx.is_tree(dhn)}, is_meshed={not nx.is_tree(dhn)}")

def downstream_sub_count(node):
    """Substations reachable downstream from node (via BFS orientation)."""
    try:
        desc = nx.descendants(G_dir, node) | {node}
    except Exception:
        desc = {node}
    return sum(1 for n in desc if n in sub_set)

PIPE_SIZING = {}

for u, v in dhn.edges():
    if G_dir.has_edge(u, v):
        from_n, to_n = u, v
    elif G_dir.has_edge(v, u):
        from_n, to_n = v, u
    else:
        from_n, to_n = u, v

    n_down = max(downstream_sub_count(to_n), 1)
    Q      = n_down * Q_PEAK_W * HLF
    data   = dhn.edges[u, v]
    Lp     = round(data.get("length", 0.0), 2)
    e = select_dn(GEN, Q)
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
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn,
         title=f"3G_M_L_BASE",
         show=False)

import matplotlib.pyplot as plt
plot_path = os.path.join(OUT_DIR,"topology.png")
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