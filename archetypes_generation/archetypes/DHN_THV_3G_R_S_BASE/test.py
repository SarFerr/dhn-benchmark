#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DHN_THV_3G_R_S_BASE  —  pyDHN dynamic simulation
"""

import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pydhn
from pydhn.fluids import Fluid
from pydhn.soils import Soil
from pydhn.solving import SimpleStep, Scheduler

# ===========================================================================
# 1. SIMULATION PARAMETERS
# ===========================================================================
STEPSIZE      = 600    # time step [s]  (10 min)
NUM_SIM_STEPS = 1008   # 7 days × 144 steps/day
INIT_STEPS    = 6      # pre-heating steps (1 h)

# ===========================================================================
# 2. FILE PATHS
# ===========================================================================
PIPES_FILE          = "pipes.csv"
NODES_FILE          = "nodes.csv"
DEMAND_PROFILE_FILE = "../../data/demand_profile.csv"

# ===========================================================================
# 3. LOAD INPUT DATA
# ===========================================================================
pipe_data           = pd.read_csv(PIPES_FILE)
node_data           = pd.read_csv(NODES_FILE)
demand_profile_data = pd.read_csv(DEMAND_PROFILE_FILE)
demand_profile_data = demand_profile_data[:NUM_SIM_STEPS]

time_sim   = demand_profile_data["timestep"].values * STEPSIZE  # [s]
heat_demand = demand_profile_data["Q_W"]                        # Series [W]

print(f"Loaded {len(node_data)} nodes, {len(pipe_data)} pipes, "
      f"{len(demand_profile_data)} time steps.")

# ===========================================================================
# 4. FLUID AND SOIL
# ===========================================================================
p0 = pipe_data.iloc[0]

fluid = Fluid(
    name       = "Water",
    isconstant = True,
    cp         = p0["fluid_cp_JkgK"],
    mu         = p0["fluid_mu_Pas"],
    rho        = p0["fluid_rho_kgm3"],
    k          = p0["fluid_lambda_WmK"],
)

soil = Soil(
    k    = p0["soil_lambda_WmK"],
    temp = p0["T_ground_degC"],
)

# ===========================================================================
# 5. BUILD NETWORK
# ===========================================================================
net = pydhn.Network()

# --- Nodes, consumers, producer ---
for i in node_data.index:
    row       = node_data.loc[i]
    name      = row["node_id"]
    node_type = row["node_type"]
    X, Y      = row["x_m"], row["y_m"]

    name_s = name + "_s"
    name_r = name + "_r"

    net.add_node(name=name_s, x=X, y=Y)
    net.add_node(name=name_r, x=X, y=Y)

    # Substation (consumer)
    if node_type == "substation":
        delta_t = float(row["delta_T_nom_K"])
        net.add_consumer(
            name              = name,
            start_node        = name_s,
            end_node          = name_r,
            control_type      = "energy",
            setpoint_type_hx  = "delta_t",
            setpoint_value_hx = -delta_t,          # K, negative = extraction
            design_delta_t    = delta_t,
            t_out_min_hx      = 10,                # floor on return temp [°C]
            stepsize          = STEPSIZE,
        )

    # Central producer
    elif node_type == "source":
        t_supply = float(row["T_supply_set_degC"])
        net.add_producer(
            name              = name,
            start_node        = name_r,
            end_node          = name_s,
            setpoint_type_hx  = "t_out",
            setpoint_value_hx = t_supply,
            stepsize          = STEPSIZE,
        )

# --- Pipes ---
for i in pipe_data.index:
    row  = pipe_data.loc[i]
    name = row["pipe_id"]
    frm  = row["from_node"]
    to   = row["to_node"]

    common = dict(
        diameter                = row["d_inner_m"],
        length                  = row["length_m"],
        internal_pipe_thickness = row["wall_m"],
        insulation_thickness    = row["insulation_thickness_m"],
        casing_thickness        = row["casing_thickness_m"],
        roughness               = row["roughness_mm"],
        k_insulation            = row["PUR_lambda_WmK"],
        k_internal_pipe         = row["steel_lambda_WmK"],
        rho_wall                = row["steel_rho_kgm3"],
        cp_wall                 = row["steel_cp_JkgK"],
        k_casing                = row["HDPE_lambda_WmK"],
        depth                   = row["burial_depth_m"],
        h_ext                   = row["h_ext_Wm2K"],
        stepsize                = STEPSIZE,
    )

    net.add_lagrangian_pipe(
        name       = f"{name}_s",
        start_node = f"{frm}_s",
        end_node   = f"{to}_s",
        line       = "supply",
        **common,
    )
    net.add_lagrangian_pipe(
        name       = f"{name}_r",
        start_node = f"{to}_r",
        end_node   = f"{frm}_r",
        line       = "return",
        **common,
    )

print("Network build complete.")

# ===========================================================================
# 6. SCHEDULES
# ===========================================================================
consumer_demand_schedule  = pd.DataFrame()
consumer_names = []

for i in node_data.index:
    row       = node_data.loc[i]
    name      = row["node_id"]
    node_type = row["node_type"]

    if node_type == "substation":
        consumer_names.append(name)
        consumer_demand_schedule[name] = -heat_demand.values   # [W], negative = extraction

consumer_demand_schedule = consumer_demand_schedule[consumer_names]

schedules = {
    "heat_demand": consumer_demand_schedule
}

print(f"Schedules built: {len(consumer_names)} consumers × {NUM_SIM_STEPS} steps.")

# ===========================================================================
# 7. PRE-HEATING
# ===========================================================================
print("--- Initializing Network (Pre-heating for stability) ---")

init_demand_consumer = pd.DataFrame(
    np.tile(consumer_demand_schedule.iloc[0].values, (INIT_STEPS, 1)),
    columns=consumer_demand_schedule.columns,
)

init_schedules = {
    "heat_demand": init_demand_consumer
}

base_loop_init = SimpleStep(
    hydraulic_sim_kwargs={"error_threshold": 1,    "verbose": False},
    thermal_sim_kwargs  ={"error_threshold": 1e-10, "verbose": False},
    with_thermal=True,
)

scheduler_init = Scheduler(
    base_loop=base_loop_init,
    schedules=init_schedules,
    steps=INIT_STEPS,
)

t0 = time.perf_counter()
_  = scheduler_init.execute(net=net, fluid=fluid, soil=soil)
print(f"--- Network initialized over {INIT_STEPS} steps "
      f"({INIT_STEPS * STEPSIZE / 3600:.1f} h). ---")
print(f"Pre-heating time: {time.perf_counter() - t0:.2f} s")

# ===========================================================================
# 8. FULL SIMULATION
# ===========================================================================
print("--- Running with Scheduler (Full Simulation) ---")

base_loop_scheduler = SimpleStep(
    hydraulic_sim_kwargs={"error_threshold": 1,    "verbose": False},
    thermal_sim_kwargs  ={"error_threshold": 1e-10, "verbose": False},
    with_thermal=True,
)

scheduler = Scheduler(
    base_loop=base_loop_scheduler,
    schedules=schedules,
    steps=NUM_SIM_STEPS,
)

t0 = time.perf_counter()
results_scheduler = scheduler.execute(net=net, fluid=fluid, soil=soil)
sim_time_total = time.perf_counter() - t0

print("--- Simulation complete ---")
print(f"Total simulation time: {sim_time_total:.2f} s")

# ===========================================================================
# 9. RESULTS
# ===========================================================================
res = results_scheduler.to_dataframes()

t_nodes    = res["nodes"]["temperature"]   # [°C]
p_nodes    = res["nodes"]["pressure"]      # [Pa]
mdot_pipes = res["edges"]["mass_flow"]     # [kg/s]
dp_pipes   = res["edges"]["delta_p"]       # [Pa]
t_pipes    = res["edges"]["temperature"]   # [°C]
qloss_pipes= res["edges"]["delta_q"]       # [Wh]

# ===========================================================================
# 10. PLOT NODE TEMPERATURES
# ===========================================================================
fig, ax = plt.subplots(figsize=(12, 5))

for col in t_nodes.columns:
    ax.plot(t_nodes[col].values, label=col)

ax.set_xlabel("Time step")
ax.set_ylabel("Temperature [°C]")
ax.set_title("Node temperatures — DHN_THV_3G_R_S_BASE")
ax.legend(loc="upper right", fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("node_temperatures.png", dpi=150)
plt.show()

print("Done.")