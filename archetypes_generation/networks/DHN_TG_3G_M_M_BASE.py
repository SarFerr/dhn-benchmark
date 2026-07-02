# DHN_TG_3G_M_M_BASE.py
#
# Benchmark archetype: Technology Assessment, 3GDH, Meshed, Medium scale
#
# Methodology II — Algorithmic Topology Generation
# by synthetic_net.py
#
# Operational Parameters & Control Strategy:
#   Inherited 3GDH standards from validation framework (CF-VT Control)
#
# Outputs (dhn_benchmark/archetypes/DHN_TG_3G_M_M_BASE/):
#   nodes.csv             — Nodes table with complete boundary conditions
#   pipes.csv             — Pipes table with thermo-physical and structural sizing
#   incidence_matrix.csv  — Connected network topology matrix
#   topology.png          — Network topology plot (300 dpi)

import os
import sys
import csv
import math
import importlib
import networkx as nx
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# PATHS & ENVIRONMENT SETUP
# ---------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR = os.path.join(THIS_DIR, "..", "archetypes", "DHN_TG_3G_M_M_BASE")
os.makedirs(OUT_DIR, exist_ok=True)

# Ensure the framework packages can be found
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co
import archetypes_generation.demand_profile as dp
import archetypes_generation.plotting as pl
import synthetic_net as sn

importlib.reload(co)
importlib.reload(dp)
importlib.reload(pl)
importlib.reload(sn)

from archetypes_generation.constants import (
    GEN_OPERATING, PIPE_CATALOGUE,
    LAMBDA_STEEL, LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL,
    ROUGHNESS_STEEL, BURIAL_DEPTH, T_GROUND, H_EXT,
    RHO_STEEL, CP_STEEL,
    RHO_PUR, CP_PUR,
    RHO_HDPE, CP_HDPE,
)
from archetypes_generation.demand_profile import Q_PEAK_W
from synthetic_net import DistrictGenerator, ThermalNetworkBuilder

# ---------------------------------------------------------------------------
# PROCESSING TOPOLOGY (Methodology II via Project Imports)
# ---------------------------------------------------------------------------
print("Executing Imported Algorithmic Topology Generation for DHN_TG_3G_M_M_BASE...")
district = DistrictGenerator(n_substations=100, seed=42)
district.generate()

PLANT_POS = (5, 0)

builder = ThermalNetworkBuilder(district)
builder.build_network(plant_position=PLANT_POS)

# SALVATAGGIO DELL'ALBERO FONDAMENTALE: copiamo lo stato prima della cerchiatura
baseline_tree = builder.main_network.copy()

# Iniezione delle maglie di cerchiatura (Modifica builder.main_network in place)
builder.add_mesh_layers(max_extra_edges=6)

# ---------------------------------------------------------------------------
# OPERATIONAL MAPPING & THERMO-HYDRAULIC SIZING (3GDH Framework Match - CF-VT)
# ---------------------------------------------------------------------------
print("Mapping thermo-hydraulic operational parameters (Control: CF-VT)...")
gp = GEN_OPERATING["3G"]
RHO = gp["rho"]
CP = gp["cp"]
DELTA_T = gp["delta_T_nom"]
V_MAX = gp["v_max"]
T_SUPPLY = gp["T_supply_nom"]
P_NOM = gp["P_nom_bar"]

HEAT_LOSS_FACTOR = 1.05


def u_linear(d_o, d_casing):
    R_ins = math.log(d_casing / d_o) / (2 * math.pi * LAMBDA_PUR)
    R_soil = math.log(2 * BURIAL_DEPTH / d_casing) / (2 * math.pi * LAMBDA_SOIL)
    return round(1.0 / (R_ins + R_soil), 4)


def select_dn(Q_w):
    mdot = Q_w / (CP * DELTA_T)
    for dn, (di, do, s, dc, sc) in sorted(PIPE_CATALOGUE.items()):
        A = math.pi * di ** 2 / 4.0
        v = mdot / (RHO * A)
        if v <= V_MAX:
            return dn, di, do, dc, s, sc, round(mdot, 4), round(v, 3)
    dn, (di, do, s, dc, sc) = sorted(PIPE_CATALOGUE.items())[-1]
    A = math.pi * di ** 2 / 4.0
    return dn, di, do, dc, s, sc, round(mdot, 4), round(mdot / (RHO * A), 3)


# Setup di un grafo orientato basato sulla copia dell'albero aciclico fondamentale
G_dir = nx.DiGraph()
for u, v in baseline_tree.edges():
    if nx.has_path(baseline_tree, PLANT_POS, u):
        G_dir.add_edge(u, v)
    else:
        G_dir.add_edge(v, u)

Q_node = {f"proj_b_{b['id']}": Q_PEAK_W for b in district.buildings}


def downstream_tree_load(from_node, to_node):
    if G_dir.has_edge(from_node, to_node):
        target = to_node
    elif G_dir.has_edge(to_node, from_node):
        target = from_node
    else:
        return 0.0
    reachable = nx.descendants(G_dir, target) | {target}
    return round(sum(Q_node.get(n, 0.0) for n in reachable) * HEAT_LOSS_FACTOR, 1)


# Costruzione tabelle di OUTPUT conformi
NODES_TABLE = []
node_mapping = {}
node_index = 1

# Aggiunta nodo centrale sorgente
plant_x, plant_y = builder.network_graph.nodes[PLANT_POS]["pos"]
node_mapping[PLANT_POS] = "src"
NODES_TABLE.append(["src", "source", plant_x, plant_y, "", P_NOM, T_SUPPLY, ""])

# Mappatura incroci stradali e nodi derivati di utenza
for node in builder.main_network.nodes():
    if node == PLANT_POS: continue
    pos = builder.network_graph.nodes[node]["pos"]
    if str(node).startswith("proj_b_"):
        b_id = builder.projection_to_building[node]["id"]
        junc_id = f"junc_b_{b_id}"
        node_mapping[node] = junc_id
        NODES_TABLE.append([junc_id, "junction", pos[0], pos[1], "", "", "", ""])

        sub_id = f"sub{b_id + 1}"
        b_x, b_y = builder.projection_to_building[node]["x"], builder.projection_to_building[node]["y"]
        NODES_TABLE.append([sub_id, "substation", b_x, b_y, "demand_profile.csv", "", "", DELTA_T])
    else:
        junc_str_id = f"junc_str_{node_index}"
        node_mapping[node] = junc_str_id
        NODES_TABLE.append([junc_str_id, "junction", pos[0], pos[1], "", "", "", ""])
        node_index += 1

PIPE_SIZING = {}
# Sizing dei rami di rete principale (Trasmissione e Cerchiatura)
for u, v, data in builder.main_network.edges(data=True):
    pid = f"{node_mapping[u]}_{node_mapping[v]}"
    Lp = round(data["length"], 2)

    # Se l'arco apparteneva all'albero fondamentale calcoliamo la cascata termica, altrimenti assegniamo quota ad anello
    if baseline_tree.has_edge(u, v):
        Q = downstream_tree_load(u, v)
    else:
        Q = Q_PEAK_W * 2.5  # Quota cautelativa di cerchiatura loops

    dn, di, do, dc, s, sc, mdot, vel = select_dn(Q)
    ins_t = round((dc - do) / 2 - sc, 5)

    PIPE_SIZING[pid] = {
        "from_node": node_mapping[u], "to_node": node_mapping[v], "length_m": Lp,
        "DN_mm": dn, "d_inner_m": di, "d_outer_m": do, "wall_m": s, "insulation_thickness_m": ins_t,
        "casing_thickness_m": sc, "d_casing_m": dc, "roughness_mm": ROUGHNESS_STEEL,
        "fluid_rho_kgm3": RHO, "fluid_cp_JkgK": CP, "fluid_mu_Pas": gp["mu"], "fluid_lambda_WmK": gp["lambda"],
        "steel_rho_kgm3": RHO_STEEL, "steel_cp_JkgK": CP_STEEL, "steel_lambda_WmK": LAMBDA_STEEL,
        "PUR_rho_kgm3": RHO_PUR, "PUR_cp_JkgK": CP_PUR, "PUR_lambda_WmK": LAMBDA_PUR,
        "HDPE_rho_kgm3": RHO_HDPE, "HDPE_cp_JkgK": CP_HDPE, "HDPE_lambda_WmK": LAMBDA_HDPE,
        "burial_depth_m": BURIAL_DEPTH, "soil_lambda_WmK": LAMBDA_SOIL, "T_ground_degC": T_GROUND, "h_ext_Wm2K": H_EXT,
        "U_linear_WmK": u_linear(do, dc), "U_Wm2K": round(u_linear(do, dc) / (math.pi * do), 4)
    }

# Sizing dei rami di allacciamento utenze (Service Pipes) derivate direttamente dalla mappa di proiezione
for proj_node, building in builder.projection_to_building.items():
    b_id = building["id"]
    junc_id = f"junc_b_{b_id}"
    sub_id = f"sub{b_id + 1}"
    pid = f"{junc_id}_{sub_id}"

    pos_junc = builder.network_graph.nodes[proj_node]["pos"]
    Lp = round(math.hypot(building["x"] - pos_junc[0], building["y"] - pos_junc[1]), 2)

    Q = Q_PEAK_W * HEAT_LOSS_FACTOR
    dn, di, do, dc, s, sc, mdot, vel = select_dn(Q)
    ins_t = round((dc - do) / 2 - sc, 5)

    PIPE_SIZING[pid] = {
        "from_node": junc_id, "to_node": sub_id, "length_m": Lp,
        "DN_mm": dn, "d_inner_m": di, "d_outer_m": do, "wall_m": s, "insulation_thickness_m": ins_t,
        "casing_thickness_m": sc, "d_casing_m": dc, "roughness_mm": ROUGHNESS_STEEL,
        "fluid_rho_kgm3": RHO, "fluid_cp_JkgK": CP, "fluid_mu_Pas": gp["mu"], "fluid_lambda_WmK": gp["lambda"],
        "steel_rho_kgm3": RHO_STEEL, "steel_cp_JkgK": CP_STEEL, "steel_lambda_WmK": LAMBDA_STEEL,
        "PUR_rho_kgm3": RHO_PUR, "PUR_cp_JkgK": CP_PUR, "PUR_lambda_WmK": LAMBDA_PUR,
        "HDPE_rho_kgm3": RHO_HDPE, "HDPE_cp_JkgK": CP_HDPE, "HDPE_lambda_WmK": LAMBDA_HDPE,
        "burial_depth_m": BURIAL_DEPTH, "soil_lambda_WmK": LAMBDA_SOIL, "T_ground_degC": T_GROUND, "h_ext_Wm2K": H_EXT,
        "U_linear_WmK": u_linear(do, dc), "U_Wm2K": round(u_linear(do, dc) / (math.pi * do), 4)
    }

# ---------------------------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------------------------
print(f"Exporting files to repository directory: {OUT_DIR}")

# 1. nodes.csv
with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m",
        "Q_peak_W", "p_pump_set_bar",
        "T_supply_set_degC", "delta_T_nom_K",
    ])
    w.writerows(NODES_TABLE)
print(f"  nodes.csv    → {len(NODES_TABLE)} rows")

# 2. pipes.csv
with open(os.path.join(OUT_DIR, "pipes.csv"), "w", newline="") as f:
    fieldnames = ["pipe_id"] + list(next(iter(PIPE_SIZING.values())).keys())
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for pid, d in PIPE_SIZING.items():
        w.writerow({"pipe_id": pid, **d})
print(f"  pipes.csv    → {len(PIPE_SIZING)} rows")

# 3. incidence_matrix.csv
node_ids = [n[0] for n in NODES_TABLE]
edge_ids = list(PIPE_SIZING.keys())

with open(os.path.join(OUT_DIR, "incidence_matrix.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["node_id"] + edge_ids)
    for node in node_ids:
        row = [node]
        for pid in edge_ids:
            u_id = PIPE_SIZING[pid]["from_node"]
            v_id = PIPE_SIZING[pid]["to_node"]

            if node == u_id:
                row.append(-1)
            elif node == v_id:
                row.append(+1)
            else:
                row.append(0)
        w.writerow(row)
print(f"  incidence_matrix.csv → {len(node_ids)} x {len(edge_ids)}")

# ---------------------------------------------------------------------------
# VISUAL RENDERING EXPORT
# ---------------------------------------------------------------------------
print(f"Generating network topology plot via synthetic_net internal plotter...")

original_show = plt.show

def save_and_show_patch():

    plt.title("DHN_TG_3G_M_M_BASE", fontsize=12, fontweight="bold", pad=12)
    plt.gcf().savefig(os.path.join(OUT_DIR, "topology.png"), dpi=300, bbox_inches="tight")
    plt.close()


plt.show = save_and_show_patch
builder.plot_network()
plt.show = original_show

print(f"Done → Archetype files completed in {OUT_DIR}")