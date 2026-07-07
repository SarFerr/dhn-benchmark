# DHN_TG_3G_M_M_BASE.py
#
# Benchmark archetype: Technology Assessment, 3GDH, Meshed, Medium
#
# Methodology II — Algorithmic generation
#   Step 1: Synthetic urban district (DistrictGenerator)
#   Step 2: Street graph (StreetGraphBuilder)
#   Step 3: Constrained Steiner tree beta=1.25 (ThermalNetworkBuilder)
#
# # Operating conditions:
#   Control    : CF-VT (constant flow, variable temperature)
#   T_supply   : 80°C nominal (variable in operation)
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
import random
import importlib
import matplotlib.pyplot as plt
import networkx as nx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "DHN_TG_3G_M_M_BASE")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co
importlib.reload(co)
from archetypes_generation.constants import (
    GEN_OPERATING, PIPE_CATALOGUE,
    LAMBDA_STEEL, LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL,
    ROUGHNESS_STEEL, BURIAL_DEPTH, T_GROUND,
    RHO_STEEL, CP_STEEL, RHO_PUR, CP_PUR, RHO_HDPE, CP_HDPE,
)

# Import classes from synthetic_district.py
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
WIDTH, HEIGHT   = 1200, 800   # m
ROWS,  COLS     = 5,  7
STREET_W        = 15          # m
N_SUB_TARGET    = 100
BLOCK_VAR       = 0.25
PERTURBATION    = 7           # m

# Network
BETA            = 1.00        # constrained Steiner flexibility factor

# 3GDH operating parameters (CF-VT)
gp          = GEN_OPERATING["3G"]
RHO         = gp["rho"]
CP          = gp["cp"]
DELTA_T     = gp["delta_T_nom"]    # 30 K
V_MAX       = gp["v_max"]          # 2.5 m/s
T_SUPPLY    = gp["T_supply_nom"]   # 80°C
P_REF_BAR   = gp["P_nom_bar"]      # bar (reference pressure at source)
Q_PEAK_W    = 175_000              # W per substation
HLF         = 1.05                 # heat loss factor

# CF-VT: source nominal mass flow (peak load balance)
# Computed after district generation when N_SUB is known
# m_nom = N_SUB * Q_peak * HLF / (cp * dT)

def unpack_pipe(vals):
    return vals[0], vals[1], vals[2], vals[3]

print("="*60)
print("DHN_TG_3G_M_M_BASE — 3GDH | Meshed | Medium | CF-VT")
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

# CF-VT nominal mass flow
M_FLOW_NOM = round(N_SUB * Q_PEAK_W * HLF / (CP * DELTA_T), 3)
print(f"  m_flow_nom  : {M_FLOW_NOM} kg/s  (CF-VT peak)")

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
# SECTION 4 — NETWORK TOPOLOGY (constrained Steiner, beta=1.25)
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
# Node types from routing graph attributes
# "generator" → source
# "substation" → consumer substation
# "crossing"   → projection node on street (junction)
# "intersection" → original street intersection in network

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
        # find building id from building_nodes list
        b_idx = tnb.building_nodes.index(n)
        nid   = f"sub_{b_idx}"
        ntype = "substation"
    else:
        nid   = f"jun_{idx_j}"
        ntype = "junction"
        idx_j += 1
    node_id_map[n] = nid
    node_rows.append((nid, ntype, round(pos[0],2), round(pos[1],2)))

print(f"\nNodes: {len(node_rows)} "
      f"(1 source + {idx_j} junctions + {N_SUB} substations)")

# ---------------------------------------------------------------------------
# SECTION 6 — PIPE SIZING
# ---------------------------------------------------------------------------
def u_linear(d_o, d_casing):
    R_ins  = math.log(d_casing/d_o)            / (2*math.pi*LAMBDA_PUR)
    R_soil = math.log(2*BURIAL_DEPTH/d_casing) / (2*math.pi*LAMBDA_SOIL)
    return round(1.0/(R_ins+R_soil), 4)

def u_per_area(U_lin, d_o):
    return round(U_lin/(math.pi*d_o), 4)

def select_dn(Q_w):
    mdot = Q_w/(CP*DELTA_T)
    for dn, vals in sorted(PIPE_CATALOGUE.items()):
        di, do, s, dc = unpack_pipe(vals)
        A = math.pi*di**2/4.0
        if mdot/(RHO*A) <= V_MAX:
            return dn, di, do, dc, s, round(mdot,4)
    dn, vals = sorted(PIPE_CATALOGUE.items())[-1]
    di, do, s, dc = unpack_pipe(vals)
    A = math.pi*di**2/4.0
    return dn, di, do, dc, s, round(mdot,4)

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

# ← CHIAVE: itera su dhn.edges() non G_dir.edges()
# Questo include gli archi di loop che bfs_tree escluderebbe
for u, v in dhn.edges():
    # Determine flow orientation from BFS tree
    if G_dir.has_edge(u, v):
        from_n, to_n = u, v
    elif G_dir.has_edge(v, u):
        from_n, to_n = v, u
    else:
        # Loop-closing edge not in BFS tree: use arbitrary orientation
        from_n, to_n = u, v

    n_down = max(downstream_sub_count(to_n), 1)
    Q      = n_down * Q_PEAK_W * HLF
    data   = dhn.edges[u, v]
    Lp     = round(data.get("length", 0.0), 2)
    dn, di, do, dc, s, mdot = select_dn(Q)
    UL  = u_linear(do, dc)
    uid = node_id_map.get(from_n, str(from_n))
    vid = node_id_map.get(to_n,   str(to_n))
    pid = f"{uid}_{vid}"
    PIPE_SIZING[pid] = {
        "from_node"              : uid,
        "to_node"                : vid,
        "length_m"               : Lp,
        "d_inner_m"              : di,
        "d_outer_m"              : do,
        "d_casing_m"             : dc,
        "wall_m"                 : s,
        "insulation_thickness_m" : round((dc-do)/2, 5),
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
        "U_linear_WmK"           : UL,
        "U_Wm2K"                 : u_per_area(UL, do),
    }

L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"\nPipes: {len(PIPE_SIZING)} sized")
print(f"  L_tot  = {L_tot/1000:.2f} km")
print(f"  Q_tot  = {N_SUB*Q_PEAK_W/1e6:.2f} MW")
print(f"  m_nom  = {M_FLOW_NOM} kg/s")

# ---------------------------------------------------------------------------
# SECTION 7 — CSV EXPORT
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

with open(os.path.join(OUT_DIR,"nodes.csv"),"w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["node_id","node_type","x_m","y_m",
                "Q_peak_W","m_flow_nom_kg_s",
                "T_supply_nom_degC","delta_T_nom_K","p_ref_bar"])
    for nid, ntype, x, y in node_rows:
        if ntype == "source":
            w.writerow([nid,ntype,x,y,
                        "",            # Q_peak — not applicable
                        M_FLOW_NOM,    # CF-VT: fixed mass flow
                        T_SUPPLY,      # nominal supply temperature
                        "",
                        P_REF_BAR])
        elif ntype == "substation":
            w.writerow([nid,ntype,x,y,
                        "demand_profile.csv",
                        "",            # free — computed by solver
                        "",
                        DELTA_T,
                        ""])
        else:
            w.writerow([nid,ntype,x,y,"","","","",""])

print(f"  nodes.csv  → {len(node_rows)} rows")

with open(os.path.join(OUT_DIR,"pipes.csv"),"w",newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "pipe_id","from_node","to_node",
        "length_m","d_inner_m","d_outer_m","d_casing_m","wall_m",
        "insulation_thickness_m","DN_mm","roughness_m",
        "fluid_rho_kgm3","fluid_cp_JkgK","fluid_mu_Pas","fluid_lambda_WmK",
        "steel_rho_kgm3","steel_cp_JkgK","steel_lambda_WmK",
        "PUR_rho_kgm3","PUR_cp_JkgK","PUR_lambda_WmK",
        "HDPE_rho_kgm3","HDPE_cp_JkgK","HDPE_lambda_WmK",
        "burial_depth_m","soil_lambda_WmK","T_ground_degC",
        "U_linear_WmK","U_Wm2K"])
    for pid, d in PIPE_SIZING.items():
        w.writerow([
            pid,d["from_node"],d["to_node"],
            d["length_m"],d["d_inner_m"],d["d_outer_m"],
            d["d_casing_m"],d["wall_m"],d["insulation_thickness_m"],
            d["DN_mm"],d["roughness_m"],
            d["fluid_rho_kgm3"],d["fluid_cp_JkgK"],
            d["fluid_mu_Pas"],d["fluid_lambda_WmK"],
            d["steel_rho_kgm3"],d["steel_cp_JkgK"],d["steel_lambda_WmK"],
            d["PUR_rho_kgm3"],d["PUR_cp_JkgK"],d["PUR_lambda_WmK"],
            d["HDPE_rho_kgm3"],d["HDPE_cp_JkgK"],d["HDPE_lambda_WmK"],
            d["burial_depth_m"],d["soil_lambda_WmK"],d["T_ground_degC"],
            d["U_linear_WmK"],d["U_Wm2K"]])
print(f"  pipes.csv  → {len(PIPE_SIZING)} rows")

# ---------------------------------------------------------------------------
# SECTION 8 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn,
         title=f"DHN_TG_3G_M_M_BASE",
         show=True)

import matplotlib.pyplot as plt
plot_path = os.path.join(OUT_DIR,"topology.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")