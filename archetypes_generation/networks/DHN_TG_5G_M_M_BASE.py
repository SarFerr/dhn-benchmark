# DHN_TG_5G_M_M_BASE.py
#
# Benchmark archetype: Technology Assessment, 5GDHC, Meshed, Medium
#
# Methodology II — Algorithmic generation
#   Step 1: Synthetic urban district
#   Step 2: Street graph
#   Step 3: Constrained Steiner tree beta=1.00 — single backup source
#
# Operating conditions (Section 5.2.2 — 5GDHC, heating-only BASE scenario):
#   Network type   : Bidirectional ambient loop
#   T_loop         : 10–25°C (near-constant shared loop temperature)
#   delta_T        : 5 K (nominal temperature difference across HP)
#   p_ref          : 4 bar
#   N_sources      : 1 backup (central ground-coupled HP / borehole field)
#   N_prosumer_src : 5 (5% of substations, spatially distributed)
#                    — substations capable of heat injection into the loop
#                    — active only when local HP has surplus heat
#                    — in BASE scenario (heating week): act as consumers
#   Q_peak_sub     : from demand_profile [W/substation]
#
# Node typology:
#   src            — 1 centralised backup source at footprint centroid.
#                    Maintains loop T in [10,25°C]. Active for balancing only.
#   prosumer_source — 5 substations (5%) with reversible HP. Marked in CSV
#                    as prosumer=True and backup_fallback=True. In the
#                    BASE (heating week) scenario they act as consumers.
#                    In non-production mode all nodes are served by backup.
#   substation     — remaining 95 substations, consumers only.
#                    backup_fallback=True: always reachable from src by
#                    construction of the Steiner tree.
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
OUT_DIR   = os.path.join(THIS_DIR, "..", "archetypes", "DHN_TG_5G_M_M_BASE")
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

sys.path.insert(0, os.path.join(REPO_ROOT, "dhn_benchmark", "networks"))
from synthetic_district import (
    DistrictGenerator,
    StreetGraphBuilder,
    ThermalNetworkBuilder,
)

# ---------------------------------------------------------------------------
# SECTION 1 — DESIGN PARAMETERS
# ---------------------------------------------------------------------------

# District — identical to TG-3/TG-4 for topology comparability
SEED           = 42
WIDTH, HEIGHT  = 1200, 800
ROWS,  COLS    = 5, 7
STREET_W       = 15
N_SUB_TARGET   = 100
BLOCK_VAR      = 0.25
PERTURBATION   = 7

# Network
BETA           = 1.00
N_PROSUMER_SRC = 5          # 5% of N_sub

# 5GDHC operating parameters
gp         = GEN_OPERATING["5G"]
RHO        = gp["rho"]
CP         = gp["cp"]
DELTA_T    = gp["delta_T_nom"]    # 5 K
V_MAX      = gp["v_max"]
T_LOOP_NOM = gp["T_supply_nom"]   # ~17.5°C
T_LOOP_MIN = 10.0                  # °C
T_LOOP_MAX = 25.0                  # °C
P_REF_BAR  = gp["P_nom_bar"]      # 4 bar
Q_PEAK_W   = Q_PEAK_W
HLF        = 1.02

def unpack_pipe(vals):
    # PIPE_CATALOGUE: (di, do, s, dc, sc)
    return vals[0], vals[1], vals[2], vals[3], vals[4]

print("=" * 60)
print("DHN_TG_5G_M_M_BASE — 5GDHC | Meshed | Medium | Heating BASE")
print("=" * 60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
# ---------------------------------------------------------------------------
print("\nStep 1 — District generation (seed=42, identical to TG-3/TG-4)...")
district = DistrictGenerator(
    width=WIDTH, height=HEIGHT,
    rows=ROWS,   cols=COLS,
    street_width    = STREET_W,
    n_substations   = N_SUB_TARGET,
    block_variation = BLOCK_VAR,
    perturbation    = PERTURBATION,
    seed            = SEED,
).generate()

N_SUB = len(district.buildings)
print(f"  Blocks      : {COLS}×{ROWS} = {COLS*ROWS}")
print(f"  Substations : {N_SUB}")

# ---------------------------------------------------------------------------
# SECTION 3 — STREET GRAPH
# ---------------------------------------------------------------------------
print("\nStep 2 — Street graph...")
street_graph = StreetGraphBuilder(district).build()
print(f"  Nodes: {street_graph.number_of_nodes()}, "
      f"Edges: {street_graph.number_of_edges()}")

# ---------------------------------------------------------------------------
# SECTION 4 — PROSUMER SOURCE SELECTION
#
# Select N_PROSUMER_SRC substations as prosumer injection nodes.
# Strategy: divide the footprint into N_PROSUMER_SRC spatial zones and
# select the substation nearest to each zone centroid.
# Zones arranged as N / NE / SE / SW / NW for N=5.
# Deterministic and independent of the random seed.
# ---------------------------------------------------------------------------
print(f"\nSelecting {N_PROSUMER_SRC} prosumer sources (spatially distributed)...")

zone_centroids = [
    (WIDTH * 0.50, HEIGHT * 0.85),   # North
    (WIDTH * 0.85, HEIGHT * 0.65),   # NE
    (WIDTH * 0.85, HEIGHT * 0.20),   # SE
    (WIDTH * 0.15, HEIGHT * 0.20),   # SW
    (WIDTH * 0.15, HEIGHT * 0.65),   # NW
]

prosumer_src_ids = []
used_ids         = set()

for zx, zy in zone_centroids:
    best_dist, best_b = float("inf"), None
    for b in district.buildings:
        if b["id"] in used_ids:
            continue
        d = math.hypot(b["x"] - zx, b["y"] - zy)
        if d < best_dist:
            best_dist, best_b = d, b
    prosumer_src_ids.append(best_b["id"])
    used_ids.add(best_b["id"])
    print(f"  Zone ({zx:.0f},{zy:.0f}) → building {best_b['id']} "
          f"@ ({best_b['x']:.0f},{best_b['y']:.0f})")

prosumer_src_set = set(prosumer_src_ids)

# ---------------------------------------------------------------------------
# SECTION 5 — NETWORK TOPOLOGY
# Backup source only as generator_pos.
# Prosumer nodes are substations already in the terminal set —
# distinguished only in the CSV (not in the Steiner tree construction).
# Connectivity from backup to all nodes guaranteed by construction.
# ---------------------------------------------------------------------------
print(f"\nStep 3 — Constrained Steiner tree (β={BETA}, backup source only)...")

# Backup source
src_block  = district.blocks[0 * district.rows + 0]
backup_pos = (src_block["x"] + src_block["width"]  / 5,
              src_block["y"] + src_block["height"] / 5)
print(f"  Backup source (bottom-left): {backup_pos}")

tnb = ThermalNetworkBuilder(street_graph, district, backup_pos)
tnb.build_routing_graph()
dhn = tnb.constrained_steiner_tree(beta=BETA)

m = tnb.metrics(dhn)
print(f"\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 6 — FALLBACK CONNECTIVITY CHECK
# Verify all nodes reachable from backup source (N-1 condition).
# ---------------------------------------------------------------------------
print("\nFallback connectivity check (backup → all nodes)...")
backup_gnode = tnb.generator_nodes[0]
n_reachable  = sum(1 for n in dhn.nodes()
                   if nx.has_path(dhn, backup_gnode, n))
assert n_reachable == dhn.number_of_nodes(), \
    f"[ERROR] Only {n_reachable}/{dhn.number_of_nodes()} nodes reachable!"
print(f"  All {n_reachable}/{dhn.number_of_nodes()} nodes reachable ✓")

# Verify prosumer sources are reachable
rou = tnb.rou
for b in district.buildings:
    if b["id"] not in prosumer_src_set:
        continue
    # Find the corresponding node in DHN
    proj_node = ("sub", b["id"])
    if proj_node in dhn.nodes():
        assert nx.has_path(dhn, backup_gnode, proj_node), \
            f"[ERROR] Prosumer {b['id']} not reachable from backup!"
print(f"  All {N_PROSUMER_SRC} prosumer sources backup-reachable ✓")

# ---------------------------------------------------------------------------
# SECTION 7 — NODE EXTRACTION
# ---------------------------------------------------------------------------
node_id_map  = {}
node_rows    = []
idx_j        = 0
psrc_counter = 0

# Backup source
for k, gnode in enumerate(tnb.generator_nodes):
    pos = rou.nodes[gnode]["pos"]
    nid = "src"
    node_id_map[gnode] = nid
    node_rows.append((nid, "source", round(pos[0],2), round(pos[1],2)))

# All nodes in DHN — distinguish prosumer_source from substation
for n in dhn.nodes():
    if n in node_id_map:
        continue
    kind = rou.nodes[n].get("kind", "junction")
    pos  = rou.nodes[n]["pos"]
    if kind == "substation":
        b_idx = tnb.building_nodes.index(n)
        if b_idx in prosumer_src_set:
            nid   = f"psrc{prosumer_src_ids.index(b_idx)}"
            ntype = "prosumer_source"
            psrc_counter += 1
        else:
            nid   = f"sub{b_idx}"
            ntype = "substation"
    else:
        nid   = f"jun{idx_j}"
        ntype = "junction"
        idx_j += 1
    node_id_map[n] = nid
    node_rows.append((nid, ntype, round(pos[0],2), round(pos[1],2)))

print(f"\nNodes: {len(node_rows)} "
      f"(1 backup + {psrc_counter} prosumer_src + "
      f"{idx_j} junctions + {N_SUB - psrc_counter} substations)")

# ---------------------------------------------------------------------------
# SECTION 8 — PIPE SIZING
# ---------------------------------------------------------------------------
def u_linear(d_o, d_casing):
    R_ins  = math.log(d_casing/d_o)            / (2*math.pi*LAMBDA_PUR)
    R_soil = math.log(2*BURIAL_DEPTH/d_casing) / (2*math.pi*LAMBDA_SOIL)
    return round(1.0/(R_ins+R_soil), 4)

def select_dn(Q_w):
    mdot = Q_w / (CP * DELTA_T)
    for dn, vals in sorted(PIPE_CATALOGUE.items()):
        di, do, s, dc, sc = unpack_pipe(vals)
        A = math.pi * di**2 / 4.0
        if mdot / (RHO * A) <= V_MAX:
            return dn, di, do, dc, s, sc, round(mdot, 4)
    dn, vals = sorted(PIPE_CATALOGUE.items())[-1]
    di, do, s, dc, sc = unpack_pipe(vals)
    A = math.pi * di**2 / 4.0
    return dn, di, do, dc, s, sc, round(mdot, 4)

src_gnode = tnb.generator_nodes[0]
G_dir     = nx.DiGraph(nx.bfs_tree(dhn, src_gnode))
sub_set   = set(tnb.building_nodes)

N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, "
      f"is_meshed={not nx.is_tree(dhn)}")

def downstream_sub_count(node):
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
    dn, di, do, dc, s, sc, mdot = select_dn(Q)
    ins_t  = round((dc - do) / 2 - sc, 5)
    UL     = u_linear(do, dc)
    uid    = node_id_map.get(from_n, str(from_n))
    vid    = node_id_map.get(to_n,   str(to_n))
    pid    = f"{uid}_{vid}"
    PIPE_SIZING[pid] = {
        "from_node"              : uid,
        "to_node"                : vid,
        "length_m"               : Lp,
        "DN_mm"                  : dn,
        "d_inner_m"              : di,
        "d_outer_m"              : do,
        "wall_m"                 : s,
        "insulation_thickness_m" : ins_t,
        "casing_thickness_m"     : sc,
        "d_casing_m"             : dc,
        "roughness_mm"           : ROUGHNESS_STEEL,
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
        "h_ext_Wm2K"             : H_EXT,
        "U_linear_WmK"           : UL,
        "U_Wm2K"                 : round(UL / (math.pi * do), 4),
    }

L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
print(f"\nPipes: {len(PIPE_SIZING)} sized")
print(f"  L_tot  = {L_tot/1000:.2f} km")
print(f"  Q_tot  = {N_SUB*Q_PEAK_W/1e6:.2f} MW  (heating mode, BASE)")

# ---------------------------------------------------------------------------
# SECTION 9 — CSV EXPORT
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")

with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m",
        "Q_peak_heat_W",
        "m_flow_nom_kg_s",
        "T_loop_min_degC", "T_loop_max_degC",
        "delta_T_nom_K", "p_ref_bar",
        "prosumer",
        "backup_fallback",
    ])
    for nid, ntype, x, y in node_rows:
        if ntype == "source":
            # Backup — balancing only, not always active
            w.writerow([nid, ntype, x, y,
                        "",           # Q_peak_heat — variable
                        "",           # m_flow free
                        T_LOOP_MIN,   # 10°C
                        T_LOOP_MAX,   # 25°C
                        "",
                        P_REF_BAR,
                        "False",      # not a prosumer
                        "False"])     # is the backup itself
        elif ntype == "prosumer_source":
            # Prosumer — heating mode only in BASE scenario
            w.writerow([nid, ntype, x, y,
                        "demand_profile.csv",
                        "",           # m_flow free
                        "",
                        "",
                        DELTA_T,      # 5 K across HP
                        "",
                        "True",       # prosumer node
                        "True"])      # reachable from backup ✓
        elif ntype == "substation":
            # Standard consumer
            w.writerow([nid, ntype, x, y,
                        "demand_profile.csv",
                        "",           # m_flow free
                        "",
                        "",
                        DELTA_T,      # 5 K across HP
                        "",
                        "False",
                        "True"])      # reachable from backup ✓
        else:
            w.writerow([nid, ntype, x, y,
                        "", "", "", "", "", "", "", ""])

print(f"  nodes.csv  → {len(node_rows)} rows")

with open(os.path.join(OUT_DIR, "pipes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "pipe_id", "from_node", "to_node",
        "length_m", "DN_mm", "d_inner_m", "d_outer_m", "wall_m",
        "insulation_thickness_m", "casing_thickness_m", "d_casing_m",
        "roughness_mm",
        "fluid_rho_kgm3", "fluid_cp_JkgK", "fluid_mu_Pas", "fluid_lambda_WmK",
        "steel_rho_kgm3", "steel_cp_JkgK", "steel_lambda_WmK",
        "PUR_rho_kgm3", "PUR_cp_JkgK", "PUR_lambda_WmK",
        "HDPE_rho_kgm3", "HDPE_cp_JkgK", "HDPE_lambda_WmK",
        "burial_depth_m", "soil_lambda_WmK", "T_ground_degC",
        "h_ext_Wm2K", "U_linear_WmK", "U_Wm2K"])
    for pid, d in PIPE_SIZING.items():
        w.writerow([
            pid, d["from_node"], d["to_node"],
            d["length_m"], d["DN_mm"], d["d_inner_m"], d["d_outer_m"],
            d["wall_m"], d["insulation_thickness_m"],
            d["casing_thickness_m"], d["d_casing_m"],
            d["roughness_mm"],
            d["fluid_rho_kgm3"], d["fluid_cp_JkgK"],
            d["fluid_mu_Pas"],   d["fluid_lambda_WmK"],
            d["steel_rho_kgm3"], d["steel_cp_JkgK"], d["steel_lambda_WmK"],
            d["PUR_rho_kgm3"],   d["PUR_cp_JkgK"],   d["PUR_lambda_WmK"],
            d["HDPE_rho_kgm3"],  d["HDPE_cp_JkgK"],  d["HDPE_lambda_WmK"],
            d["burial_depth_m"], d["soil_lambda_WmK"], d["T_ground_degC"],
            d["h_ext_Wm2K"], d["U_linear_WmK"], d["U_Wm2K"]])
print(f"  pipes.csv  → {len(PIPE_SIZING)} rows")

# ---------------------------------------------------------------------------
# SECTION 10 — TOPOLOGY PLOT
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn, title="DHN_TG_5G_M_M_BASE", show=False)

ax  = plt.gca()
pos_rou = nx.get_node_attributes(tnb.rou, "pos")
for n in tnb.building_nodes:
    b_idx = tnb.building_nodes.index(n)
    if b_idx in prosumer_src_set:
        x, y = pos_rou[n]
        ax.add_patch(plt.Circle((x, y), radius=8,
                                facecolor="#CCCCFF",
                                edgecolor="blue",
                                linewidth=2.0, zorder=6))

import matplotlib.lines as mlines
handles, labels = ax.get_legend_handles_labels()
prosumer_handle = mlines.Line2D([], [], color='none',
                                marker='o',
                                markersize=10,
                                markerfacecolor="#CCCCFF",
                                markeredgecolor="blue",
                                markeredgewidth=2.0,
                                label="Prosumers")


plot_path = os.path.join(OUT_DIR, "topology.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")