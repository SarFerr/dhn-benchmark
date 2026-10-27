# 5G_M_M_BASE.py
#
# Benchmark archetype: 5GDHC, Meshed, Medium
#
# Description
#   Builds the 5G_M_M network with Methodology II (algorithmic generation, methodology_II.py)
#   on the same synthetic district as 3G_M_M (same seed, footprint and beta), with one
#   centralised backup source and 10 prosumers that inject heat into the loop. It defines the
#   prosumer production profile, sizes the pipes with the N-1 criterion on the net flow and
#   exports the simulation-ready files. The same inputs and the same seed give the same network.
#
# Procedure (Methodology II)
#   Steps 1-2  District synthesis and building allocation   DistrictGenerator, StreetGraphBuilder
#   Prosumers  Selection of the 10 prosumer buildings        deterministic, one per zone of the footprint
#   Step 3     Network topology, constrained Steiner tree   ThermalNetworkBuilder (beta = 1.00)
#   Step 4     Pipe sizing on the N-1 design flow           n1_design_flows, select_dn
#   Export     nodes.csv, pipes.csv, prosumer_production_profile.csv, pipe_design_flows.csv,
#              topology.png, incidence_matrix.csv
#
# Operating conditions (5GDH):
#   Control        : VF-CT (variable flow, constant temperature) + prosumership
#
#   PRIMARY sources — DECENTRALISED, injecting heat into the ambient loop
#     N_PROSUMER_SRC = 10 substations (10 % of the total), ALL injecting heat.
#     ONE generation profile, built ad hoc for the benchmark (no claim of
#     physical realism), the same for every prosumer and repeated identically
#     over the 7 days like the demand profile. It is a base-load profile: a
#     heating-day plateau. Each prosumer first covers its OWN load
#     (self-consumption) and injects the SURPLUS into the loop; the rating is
#     chosen so that the surplus of the 10 prosumers covers BASE_SHARE (70 %)
#     of the base load of the pure consumers (F_STEADY of the peak).
#     The source technology is deliberately not specified (waste heat,
#     storage-backed heat pump, ...).
#   SECONDARY source — ONE CENTRALISED plant at the 3G_M_M position.
#    It acts as slack in the simulation: it covers the morning peak and the
#    share of the base load not covered by the prosumers (1 - BASE_SHARE).
#    It never has to absorb a prosumer surplus (BASE_SHARE < 1).
#
#   T_supply       : 20°C (temperature set-point)
#   delta_T        : 5 K at substations
#   p_ref          : 6 bar
#   N_sources      : 1 backup (central)
#   N_prosumer_src : 10 (10% of substations, spatially distributed)
#   Q_peak_sub : 175 kW/substation (uniform, base scenario)
#
# Outputs (archetypes_generation/archetypes/5G_M_M_BASE/):
#   nodes.csv                       - node table with boundary conditions
#   pipes.csv                       - pipe table with all modelling parameters
#   prosumer_production_profile.csv - weekly heat injection profile of each prosumer
#   prosumer_profile_preview.png    - plot of the typical day of the profile
#   pipe_design_flows.csv           - N-1 design flow, velocity and DN of every pipe
#   topology.png                    - network topology plot
#   incidence_matrix.csv            - node-pipe incidence matrix
#
# Usage:
#   python archetypes_generation/networks/5G_M_M_BASE.py

import os
import sys
import csv
import math
import importlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import networkx as nx
import numpy as np


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
OUT_DIR = os.path.join(THIS_DIR, "..", "archetypes", "5G_M_M_BASE")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, REPO_ROOT)

import archetypes_generation.constants as co

importlib.reload(co)
from archetypes_generation.constants import GEN_OPERATING

from archetypes_generation.demand_profile import (
    Q_PEAK_W, DT_MIN, N_DAY, N_WEEK, WEEKLY_SHAPE, F_STEADY, timestep_labels,
)

from archetypes_generation.pipe_system import (
    select_dn, pipe_record, write_pipes_csv,
)

GEN = "5G"

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
# prosumer settings, sizing case, 5GDHC operating parameters from constants.GEN_OPERATING).
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
BETA = 1.00

# --- Decentralised sources (primary): 10 prosumers, all injecting --------------
N_PROSUMER_SRC = 10  # 10 % of the substations
BASE_SHARE = 0.70  # share of the consumers' base load covered by the prosumers' SURPLUS
BASE_ON_H = 6.0  # start of the heating day [h]
BASE_OFF_H = 22.0  # end of the heating day  [h]
BASE_RAMP_H = 0.75  # smooth ramp up / down [h]

# --- Central source / pipe design -----------------------------------------
CENTRAL_MARGIN = 0.10  # capacity margin on the weekly peak residual load (informative)
SIZING_CASE = "daily_envelope"  # "daily_envelope" | "central_only"

# 5GDHC operating parameters
gp = GEN_OPERATING["5G"]
CP = gp["cp"]
DELTA_T = gp["delta_T_nom"]
V_MAX = gp["v_max"]
T_SUPPLY = gp["T_supply_nom"]
P_REF_BAR = gp["P_nom_bar"]

HLF = 1.02  # heat loss factor on the loop demand

assert SIZING_CASE in ("daily_envelope", "central_only")

print("=" * 60)
print("5G_M_M_BASE — 5GDHC | Meshed | Medium | Heating BASE")
print("=" * 60)

# ---------------------------------------------------------------------------
# SECTION 2 — DISTRICT GENERATION
# Function: Methodology II, Steps 1-2. DistrictGenerator creates the block grid and distributes
# the substations on the block frontages, with the seed above.
# Call: DistrictGenerator(...).generate() returns the district object.
# ---------------------------------------------------------------------------
print("\nStep 1 — District generation (seed=42, identical to 3G_M_M)...")
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
# Function: StreetGraphBuilder turns the street centrelines of the district into the weighted
# graph on which the network is routed.
# Call: StreetGraphBuilder(district).build() returns the street graph.
# ---------------------------------------------------------------------------
print("\nStep 2 — Street graph...")
street_graph = StreetGraphBuilder(district).build()
print(f"  Nodes: {street_graph.number_of_nodes()}, "
      f"Edges: {street_graph.number_of_edges()}")


# ---------------------------------------------------------------------------
# SECTION 4 — SELECTION OF THE DECENTRALISED SOURCE BUILDINGS
# Function: chooses which substations are prosumers (see the description below).
# Call: spatial_zone_centroids(...) gives the zone centroids, pick_buildings(...) the building ids;
# the result is the set prosumer_src_set.
#
# Deterministic, independent of the random seed: the footprint is divided into
# zones and the free building nearest to each zone centroid is selected.
#   N_PROSUMER_SRC zones on a regular grid, spread over the footprint.
# ---------------------------------------------------------------------------
def spatial_zone_centroids(n, width, height):
    """n zone centroids spread evenly over the footprint (grid of cells, row-major)."""
    cols = max(1, math.ceil(math.sqrt(n * width / height)))
    rows = math.ceil(n / cols)
    cells = [((i + 0.5) / cols * width, (j + 0.5) / rows * height)
             for j in range(rows) for i in range(cols)]
    step = (len(cells) - 1) / max(n - 1, 1)
    return [cells[round(k * step)] for k in range(n)]


def pick_buildings(zone_centroids, used_ids):
    """Nearest free building to each zone centroid (ids appended to used_ids)."""
    picked = []
    for zx, zy in zone_centroids:
        best_dist, best_b = float("inf"), None
        for b in district.buildings:
            if b["id"] in used_ids:
                continue
            d = math.hypot(b["x"] - zx, b["y"] - zy)
            if d < best_dist:
                best_dist, best_b = d, b
        picked.append(best_b["id"])
        used_ids.add(best_b["id"])
    return picked


zones = spatial_zone_centroids(N_PROSUMER_SRC, WIDTH, HEIGHT)
assert len(zones) == N_PROSUMER_SRC

prosumer_src_ids = pick_buildings(zones, set())
prosumer_src_set = set(prosumer_src_ids)
assert len(prosumer_src_set) == N_PROSUMER_SRC

print(
    f"\nSelected {N_PROSUMER_SRC} prosumer sources ({100 * N_PROSUMER_SRC / N_SUB:.0f} % of substations, all injecting)")

# ---------------------------------------------------------------------------
# SECTION 5 — NETWORK TOPOLOGY
# Function: Methodology II, Step 3. Places the central source and grows the network with the
# constrained Steiner algorithm; prosumers are ordinary substations of the same graph.
# Call: ThermalNetworkBuilder(...), build_routing_graph(), constrained_steiner_tree(beta).
# One central source (the only generator of the Steiner construction).
# Decentralised sources are substations already in the terminal set,
# distinguished only in the CSV (same graph as 3G_M_M).
# ---------------------------------------------------------------------------
print(f"\nStep 3 — Constrained Steiner tree (β={BETA}, one central source)...")

src_block = district.blocks[0 * district.rows + 0]
central_pos = (src_block["x"] + src_block["width"] / 5,
               src_block["y"] + src_block["height"] / 5)
print(f"  Central source: ({central_pos[0]:.1f}, {central_pos[1]:.1f})")

tnb = ThermalNetworkBuilder(street_graph, district, central_pos)
tnb.build_routing_graph()
dhn = tnb.constrained_steiner_tree(beta=BETA)

m = tnb.metrics(dhn)
print("\nTopological metrics:")
for k, v in m.items():
    print(f"  {k:<15} {v}")

# ---------------------------------------------------------------------------
# SECTION 6 — CONNECTIVITY CHECK
# Function: verifies that every node is reachable from the central source and that the prosumers
# belong to the network.
# Call: plain asserts; the script stops otherwise.
# ---------------------------------------------------------------------------
print("\nConnectivity check (central source → all nodes)...")
g0 = tnb.generator_nodes[0]
n_reach = sum(1 for n in dhn.nodes() if nx.has_path(dhn, g0, n))
assert n_reach == dhn.number_of_nodes(), f"[ERROR] only {n_reach}/{dhn.number_of_nodes()} reachable"
print(f"  All {n_reach}/{dhn.number_of_nodes()} nodes reachable ✓")

rou = tnb.rou
bid_of = {n: n[1] for n in tnb.building_nodes}  # node ("sub", id) -> building id
for n, bid in bid_of.items():
    if bid in prosumer_src_set:
        assert n in dhn.nodes(), f"prosumer source {bid} not in the network"

# ---------------------------------------------------------------------------
# SECTION 7 — NODE EXTRACTION
# Function: converts the graph nodes into the node table (source, prosumers, consumers, junctions).
# Call: builds node_rows and node_id_map (graph node -> node id used in the pipe ids).
# ---------------------------------------------------------------------------
node_id_map = {}
node_rows = []  # (nid, ntype, x, y, building_id)
idx_j = 0

pos = rou.nodes[g0]["pos"]
node_id_map[g0] = "src"
node_rows.append(("src", "source", round(pos[0], 2), round(pos[1], 2), None))

for n in dhn.nodes():
    if n in node_id_map:
        continue
    kind = rou.nodes[n].get("kind", "junction")
    pos = rou.nodes[n]["pos"]
    bid = None
    if kind == "substation":
        bid = bid_of[n]
        nid = f"sub{bid}"
        ntype = "prosumer" if bid in prosumer_src_set else "substation"
    else:
        nid, ntype = f"jun{idx_j}", "junction"
        idx_j += 1
    node_id_map[n] = nid
    node_rows.append((nid, ntype, round(pos[0], 2), round(pos[1], 2), bid))

n_pro = sum(1 for r in node_rows if r[1] == "prosumer")
n_con = sum(1 for r in node_rows if r[1] == "substation")
assert n_pro == N_PROSUMER_SRC
print(f"\nNodes: {len(node_rows)} (1 central source + {n_pro} prosumers + "
      f"{idx_j} junctions + {n_con} consumers)")

# ---------------------------------------------------------------------------
# SECTION 8 — PROSUMER PRODUCTION PROFILE (BASE scenario)
# Function: defines the weekly heat-injection profile of the prosumers (heating-day plateau with
# smooth ramps), sizes their rating and prints an energy budget of the loop.
# Call: runs at import; writes prosumer_production_profile.csv and prosumer_profile_preview.png.
# ONE profile, built ad hoc to cover the base load of the loop: the same for the
# N_PROSUMER_SRC prosumers, defined on one day and repeated over the 7 days
# exactly like the demand profile. No stochastic component.
#   f(t) = heating-day plateau BASE_ON_H-BASE_OFF_H with smooth ramps, in [0, 1]
#   Q(t) = f(t) * Q_PROSUMER_HEAT_W
# Q_PROSUMER_HEAT_W = own base load + surplus, where the surplus of the
# N_PROSUMER_SRC prosumers covers BASE_SHARE of the base load of the pure
# consumers (F_STEADY of their coincident peak). The central plant covers the
# rest of the base load and the morning peak.
# ---------------------------------------------------------------------------
labels = timestep_labels()
dt_h = DT_MIN / 60.0
STEPS_H = 60 // DT_MIN
N_DAYS = N_WEEK // N_DAY
assert N_DAYS * N_DAY == N_WEEK


def hour_of(t):
    return (t % N_DAY) / STEPS_H


def smooth_step(x):
    x = min(1.0, max(0.0, x))
    return 0.5 * (1.0 - math.cos(math.pi * x))


D_PEAK_W = N_SUB * Q_PEAK_W * HLF  # coincident peak loop demand [W]
D_STEADY_W = D_PEAK_W * F_STEADY

N_CONSUMERS    = N_SUB - N_PROSUMER_SRC
Q_OWN_BASE_W   = Q_PEAK_W * F_STEADY                           # prosumer own load at base load
D_STEADY_NET_W = N_CONSUMERS * Q_PEAK_W * F_STEADY * HLF       # base load of the pure consumers
SURPLUS_BASE_W = BASE_SHARE * D_STEADY_NET_W / N_PROSUMER_SRC  # surplus injected per prosumer

# rated heat per prosumer, rounded DOWN to 1 kW (the surplus never exceeds the target share)
Q_PROSUMER_HEAT_W = math.floor((Q_OWN_BASE_W + SURPLUS_BASE_W) / 1e3) * 1e3

PROSUMER_DAILY_F = [round(smooth_step((hour_of(t) - BASE_ON_H) / BASE_RAMP_H)
                          * smooth_step((BASE_OFF_H - hour_of(t)) / BASE_RAMP_H), 4)
                    for t in range(N_DAY)]
PROSUMER_WEEKLY_F = PROSUMER_DAILY_F * N_DAYS  # same day repeated, as the demand
PROSUMER_WEEKLY_Q = [round(f * Q_PROSUMER_HEAT_W, 2) for f in PROSUMER_WEEKLY_F]

Q_max = max(PROSUMER_WEEKLY_Q)
Q_mean = sum(PROSUMER_WEEKLY_Q) / N_WEEK
n_active = sum(1 for q in PROSUMER_WEEKLY_Q if q > 0)

print("\nProsumer production profile (BASE — winter week, base-load):")
print(f"  Plateau {BASE_ON_H:.0f}:00-{BASE_OFF_H:.0f}:00, ramps {BASE_RAMP_H * 60:.0f} min")
print(f"  Q_prosumer_rated = {Q_PROSUMER_HEAT_W / 1e3:.0f} kW per prosumer "
      f"(own base load {Q_OWN_BASE_W / 1e3:.1f} kW + surplus "
      f"{(Q_PROSUMER_HEAT_W - Q_OWN_BASE_W) / 1e3:.1f} kW)")
print(f"  Surplus of the {N_PROSUMER_SRC} prosumers at base load = "
      f"{N_PROSUMER_SRC * (Q_PROSUMER_HEAT_W - Q_OWN_BASE_W) / 1e6:.2f} MW = "
      f"{100 * N_PROSUMER_SRC * (Q_PROSUMER_HEAT_W - Q_OWN_BASE_W) / D_STEADY_NET_W:.1f} % "
      f"of the consumers' base load ({D_STEADY_NET_W / 1e6:.2f} MW)")
print(f"  Q_prosumer_mean  = {Q_mean / 1e3:.1f} kW  (weekly average)")
print(f"  Active timesteps : {n_active}/{N_WEEK}  ({100 * n_active / N_WEEK:.1f}%)")
print(f"  Weekly energy    : {sum(PROSUMER_WEEKLY_Q) * dt_h / 1e6:.3f} MWh/week per prosumer")
print(f"  Network total    : {sum(PROSUMER_WEEKLY_Q) * dt_h * N_PROSUMER_SRC / 1e6:.3f} MWh/week "
      f"({N_PROSUMER_SRC} prosumers)")

# Export prosumer_production_profile.csv (same format as before)
PROSUMER_PROFILE_FILE = "prosumer_production_profile.csv"

with open(os.path.join(OUT_DIR, PROSUMER_PROFILE_FILE), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "timestep",  # integer index [0, N_WEEK]
        "label",  # human-readable timestamp (e.g. Mon 00:00)
        "f_normalised",  # fraction of Q_PROSUMER_HEAT_W [0, 1]
        "Q_W",  # heat injected into loop per prosumer [W]
    ])
    for t in range(N_WEEK):
        w.writerow([t, labels[t], PROSUMER_WEEKLY_F[t], PROSUMER_WEEKLY_Q[t]])
print(f"  {PROSUMER_PROFILE_FILE} → {N_WEEK} rows, {N_DAYS} identical days x {N_DAY} steps/day")

# ---- sanity budget (printed only: the balance is done in the network simulation) ---
# Each prosumer self-consumes first; the loop sees the consumers' demand, the
# residual demand of the prosumers and the prosumers' surplus injection.
E_D = E_P = E_C = E_S = 0.0
P_C_MAX = 0.0
P_C_MIN = float("inf")
for t in range(N_WEEK):
    own  = WEEKLY_SHAPE[t] * Q_PEAK_W * HLF
    prod = PROSUMER_WEEKLY_Q[t]
    D    = N_CONSUMERS * own + N_PROSUMER_SRC * max(own - prod, 0.0)   # loop demand
    g    = N_PROSUMER_SRC * max(prod - own, 0.0)                       # surplus injected
    up   = min(D, g)
    c    = D - up                                                      # central plant
    E_D += D * dt_h
    E_P += up * dt_h
    E_C += c * dt_h
    E_S += (g - up) * dt_h
    P_C_MAX = max(P_C_MAX, c)
    if WEEKLY_SHAPE[t] > 0:
        P_C_MIN = min(P_C_MIN, c)
Q_CENTRAL_W = math.ceil(P_C_MAX * (1 + CENTRAL_MARGIN) / 1e3) * 1e3
print(f"  Loop demand          : peak {D_PEAK_W / 1e6:.2f} MW, {E_D / 1e6:.1f} MWh/week")
print(f"  Indicative shares    : prosumers {100 * E_P / E_D:.1f} %  central {100 * E_C / E_D:.1f} %  "
      f"| surplus {E_S / 1e6:.3f} MWh/week")
print(f"  Central source       : peak residual {P_C_MAX / 1e6:.2f} MW (indicative rating "
      f"{Q_CENTRAL_W / 1e6:.2f} MW with {100 * CENTRAL_MARGIN:.0f} % margin), "
      f"min while heating {P_C_MIN / 1e6:.2f} MW")
assert E_S == 0.0, "prosumer surplus exceeds the loop demand: the central plant would absorb heat"


# ---- preview plot: the typical day --------------------------------------------------
hh = [t / STEPS_H for t in range(N_DAY)]
dem = [WEEKLY_SHAPE[t] * D_PEAK_W / 1e6 for t in range(N_DAY)]
fig, axs = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
axs[0].plot(hh, [v / 1e3 for v in PROSUMER_WEEKLY_Q[:N_DAY]], color="tab:green", lw=1.8)
axs[0].set_ylabel("heat injected per prosumer [kW]")
axs[0].set_title("Prosumer production profile — typical day (identical for the 7 days)")
axs[1].plot(hh, dem, color="grey", ls="--", lw=1.5, label="loop demand (all substations)")
axs[1].plot(hh, [N_PROSUMER_SRC * v / 1e6 for v in PROSUMER_WEEKLY_Q[:N_DAY]], color="tab:green", lw=1.8,
            label=f"{N_PROSUMER_SRC} prosumers")
axs[1].set_ylabel("[MW]");
axs[1].set_xlabel("hour of the day");
axs[1].legend(fontsize=8)
axs[1].set_xlim(0, 24);
axs[1].set_xticks(range(0, 25, 2))
for a in axs:
    a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "prosumer_profile_preview.png"), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# SECTION 9 — PIPE SIZING (N-1)
# Function: Methodology II, Step 4. Sizes every pipe on the N-1 design flow of the loop, taking the
# net flow (demand minus prosumer injection) into account.
# Call: n1_design_flows(dhn, sources, DEMAND, INJECTION) gives (from, to, Q, length, in_loop) per pipe;
# select_dn picks the smallest DN with v <= v_max (Table 1); pipe_record builds the pipe row.
# Flow in the pipe feeding node v (central source = slack), at timestep t:
#       Q_t(v) = max( | sum over the subtree of v of (demand - injection) | ,
#                     demand(v), injection(v) )
# Design flow = maximum over the day (SIZING_CASE; the profiles repeat every day) and over
# the intact network and every single-pipe outage (n1_design_flows, Methodology II Step 4).
# ---------------------------------------------------------------------------
sub_nodes = set(tnb.building_nodes)
use_injection = SIZING_CASE != "central_only"

SHAPE_DAY = np.array([WEEKLY_SHAPE[t] for t in range(N_DAY)], dtype=float)
DEMAND    = {n: SHAPE_DAY * Q_PEAK_W * HLF for n in sub_nodes}
INJECTION = ({n: np.array(PROSUMER_WEEKLY_Q[:N_DAY], dtype=float)
              for n in sub_nodes if bid_of[n] in prosumer_src_set}
             if use_injection else None)

N1_ROWS = n1_design_flows(dhn, tnb.generator_nodes, DEMAND, INJECTION, q_min=Q_PEAK_W * HLF)

N_dhn = dhn.number_of_nodes()
E_dhn = dhn.number_of_edges()
L_dhn = E_dhn - N_dhn + 1
trunk_Q = max(r[2] for r in N1_ROWS)
print(f"\nDHN topology: N={N_dhn}, E={E_dhn}, L={L_dhn}, is_meshed={not nx.is_tree(dhn)}")
print(f"Pipe sizing case: {SIZING_CASE}  (largest design flow {trunk_Q / 1e6:.2f} MW)")

PIPE_SIZING, DESIGN_ROWS = {}, []
for from_n, to_n, Q, length, loop_edge in N1_ROWS:
    Lp = round(length, 2)
    e = select_dn(GEN, Q)
    uid = node_id_map.get(from_n, str(from_n))
    vid = node_id_map.get(to_n, str(to_n))
    pid = f"{uid}_{vid}"
    PIPE_SIZING[pid] = pipe_record(GEN, e, uid, vid, Lp)
    DESIGN_ROWS.append((pid, round(Q, 1), e["mdot"], e["velocity"], e["DN"], loop_edge))

assert all(r[3] <= V_MAX + 1e-9 for r in DESIGN_ROWS), "velocity above v_max"
L_tot = sum(d["length_m"] for d in PIPE_SIZING.values())
dns = sorted({r[4] for r in DESIGN_ROWS})
print(f"\nPipes: {len(PIPE_SIZING)} sized  |  DN {dns[0]}-{dns[-1]}  |  "
      f"max velocity {max(r[3] for r in DESIGN_ROWS):.2f} m/s (limit {V_MAX})")
print(f"  L_tot  = {L_tot / 1000:.2f} km")
print(f"  Q_tot  = {N_SUB * Q_PEAK_W / 1e6:.2f} MW  (heating mode, BASE)")

# ---------------------------------------------------------------------------
# SECTION 10 — CSV EXPORT
# Function: writes nodes.csv (boundary conditions at the source, prosumers and consumers), pipes.csv
# and pipe_design_flows.csv.
# Call: runs at import; files are written to OUT_DIR.
# ---------------------------------------------------------------------------
print(f"\nExporting to: {OUT_DIR}")
PROSUMER_PROFILE_FILE = "prosumer_production_profile.csv"  # written in Section 8

with open(os.path.join(OUT_DIR, "nodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "node_id", "node_type", "x_m", "y_m",
        "Q_peak_heat_W",  # peak heating demand [W]
        "Q_prosumer_W",  # prosumer production profile file
        "T_supply_set_degC",
        "delta_T_nom_K",
        "p_ref_bar",
        "prosumer",
    ])
    for nid, ntype, x, y, bid in node_rows:
        if ntype == "source":
            # central source — balancing (slack) in the simulation
            w.writerow([nid, ntype, x, y, "", "", T_SUPPLY, "", P_REF_BAR, "False"])
        elif ntype == "prosumer":
            w.writerow([nid, ntype, x, y, "demand_profile.csv", PROSUMER_PROFILE_FILE,
                        T_SUPPLY, DELTA_T, "", "True"])
        elif ntype == "substation":
            w.writerow([nid, ntype, x, y, "demand_profile.csv", "", "", DELTA_T, "", "False"])
        else:
            w.writerow([nid, ntype, x, y, "", "", "", "", "", ""])
print(f"  nodes.csv  → {len(node_rows)} rows")

write_pipes_csv(os.path.join(OUT_DIR, "pipes.csv"), PIPE_SIZING)
print(f"  pipes.csv  → {len(PIPE_SIZING)} rows")

with open(os.path.join(OUT_DIR, "pipe_design_flows.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pipe_id", "Q_design_W", "mdot_kgs", "velocity_ms", "DN_mm", "in_loop"])
    w.writerows(DESIGN_ROWS)
print("  prosumer_profile_preview.png, pipe_design_flows.csv written")

# ---------------------------------------------------------------------------
# SECTION 11 — TOPOLOGY PLOT
# Function: saves the topology plot (topology.png) with the prosumers highlighted.
# Call: tnb.plot(dhn=dhn, ...) draws it, then circles are added on the prosumers.
# ---------------------------------------------------------------------------
tnb.plot(dhn=dhn, title="5G_M_M_BASE", show=False)

ax = plt.gca()
pos_rou = nx.get_node_attributes(tnb.rou, "pos")
for n in tnb.building_nodes:
    if bid_of[n] in prosumer_src_set:
        x, y = pos_rou[n]
        ax.add_patch(plt.Circle((x, y), radius=8, facecolor="#CCCCFF", edgecolor="blue",
                                linewidth=2.0, zorder=6))

handles, labs = ax.get_legend_handles_labels()
handles.append(mlines.Line2D([], [], color="none", marker="o", markersize=10,
                             markerfacecolor="#CCCCFF", markeredgecolor="blue",
                             markeredgewidth=2.0))
labs.append("Prosumers")
ax.legend(handles, labs, loc="best", fontsize=8)

plot_path = os.path.join(OUT_DIR, "topology.png")
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"  topology.png → {plot_path}")
print(f"\nDone → {OUT_DIR}")

# ---------------------------------------------------------------------------
# SECTION 12 — INCIDENCE MATRIX
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
