"""
simulate_DHN_THV_3G_R_S_BASE.py

Pandapipes time-series simulation of DHN_THV_3G_R_S_BASE.
Benchmark archetype: Thermo-Hydraulic Validation, 3GDH, Radial, Small.

Inputs:
    nodes.csv               — node table
    pipes.csv               — pipe table
    ../../data/demand_profile.csv — weekly heat demand profile (dt=10 min)

Outputs:
    - Snapshot simulation over time

Usage:
    python simulate_DHN_THV_3G_R_S_BASE.py
"""

import os
import time
import numpy as np
import pandas as pd
import pandapipes as pp
import matplotlib.pyplot as plt

from pandapipes.properties.fluids import create_constant_fluid
from pandapower.timeseries import DFData, OutputWriter
from pandapower.control.controller.const_control import ConstControl
from pandapipes.timeseries import run_time_series

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE            = os.path.dirname(os.path.abspath(__file__))
NODES_CSV       = os.path.join(HERE, "nodes.csv")
PIPES_CSV       = os.path.join(HERE, "pipes.csv")
DEMAND_CSV      = os.path.join(HERE, "..", "..", "data", "demand_profile.csv")

# ---------------------------------------------------------------------------
# Read input data
# ---------------------------------------------------------------------------
node_data      = pd.read_csv(NODES_CSV)
pipe_data      = pd.read_csv(PIPES_CSV)
demand_profile = pd.read_csv(DEMAND_CSV)

print(f"Nodes  : {len(node_data)} rows")
print(f"Pipes  : {len(pipe_data)} rows")
print(f"Demand : {len(demand_profile)} timesteps  (dt=10 min, {len(demand_profile)//144} days)")

# ---------------------------------------------------------------------------
# Parameters — boundary conditions
# ---------------------------------------------------------------------------
t_initial_C    = 20      # initial junction temperature [degC]
p_initial_bar  = 10      # initial junction pressure [bar]
plift_bar      = 2.0     # pump pressure lift [bar]
deltat_nom_k   = 30.0    # nominal supply-return deltaT [K]
Q_PEAK_W       = 175_000 # peak heat demand per substation [W]
OFFSET_X       = 5       # return circuit x-offset for geodata [m]

# ---------------------------------------------------------------------------
# Create empty network
# ---------------------------------------------------------------------------
net = pp.create_empty_network(name="DHN_THV_3G_R_S_BASE")

# ---------------------------------------------------------------------------
# Fluid — water at 3GDH nominal supply temperature
# ---------------------------------------------------------------------------
fluid = create_constant_fluid(
    name="water_80",
    fluid_type="liquid",
    density=971.8,
    viscosity=0.000354,
    heat_capacity=4195.0,
    thermal_conductivity=0.67,
    temperature=80 + 273.15,
)
net.fluid = fluid

# ---------------------------------------------------------------------------
# Junctions — supply (_s) and return (_r) for every node
# ---------------------------------------------------------------------------
node_map = {}   # node_map[node_id] = {"supply": idx, "return": idx}

for _, row in node_data.iterrows():
    name      = row["node_id"]
    node_type = row["node_type"]
    x         = float(row["x_m"])
    y         = float(row["y_m"])

    j_s = pp.create_junction(
        net, pn_bar=p_initial_bar,
        tfluid_k=t_initial_C + 273.15,
        name=f"{name}_s", geodata=(x, y)
    )
    j_r = pp.create_junction(
        net, pn_bar=p_initial_bar,
        tfluid_k=t_initial_C + 273.15,
        name=f"{name}_r", geodata=(x + OFFSET_X, y)
    )
    node_map[name] = {"supply": j_s, "return": j_r}

    # Source — circulation pump (fixes p and T at supply outlet)
    if node_type == "source":
        pp.create_circ_pump_const_pressure(
            net,
            return_junction=j_r,
            flow_junction=j_s,
            p_flow_bar=float(row["p_pump_set_bar"]),
            plift_bar=plift_bar,
            t_flow_k=float(row["T_supply_set_degC"]) + 273.15,
            name="src"
        )

    # Substation — heat consumer (deltaT control)
    if node_type == "substation":
        pp.create_heat_consumer(
            net,
            from_junction=j_s,
            to_junction=j_r,
            deltat_k=float(row["delta_T_nom_K"]),
            qext_w=Q_PEAK_W,    # peak load
            name=name
        )

# ---------------------------------------------------------------------------
# Pipes — supply and return from pipes.csv
# ---------------------------------------------------------------------------
for _, row in pipe_data.iterrows():
    from_node = row["from_node"]
    to_node   = row["to_node"]
    pid       = row["pipe_id"]

    params = dict(
        length_km        = float(row["length_m"]) / 1e3,
        inner_diameter_mm= float(row["d_inner_m"]) * 1e3,
        outer_diameter_mm= float(row["d_outer_m"]) * 1e3,
        k_mm             = float(row["roughness_m"]) * 1e3,
        u_w_per_m2k      = float(row["U_Wm2K"]),
        text_k           = float(row["T_ground_degC"]) + 273.15,
    )

    # supply: from_node -> to_node
    pp.create_pipe_from_parameters(
        net,
        from_junction=node_map[from_node]["supply"],
        to_junction=node_map[to_node]["supply"],
        name=f"{pid}_s", **params
    )
    # return: to_node -> from_node (reversed)
    pp.create_pipe_from_parameters(
        net,
        from_junction=node_map[to_node]["return"],
        to_junction=node_map[from_node]["return"],
        name=f"{pid}_r", **params
    )

# ---------------------------------------------------------------------------
# Steady-state simulation — peak load
# ---------------------------------------------------------------------------
print("\nRunning steady-state simulation...")
pp.pipeflow(net, friction_model="colebrook", mode="bidirectional")
print("Converged.\n")

# ---------------------------------------------------------------------------
# Time-series setup
# ---------------------------------------------------------------------------
qext_w_ts   = demand_profile["Q_W"].values
NUM_STEPS   = len(qext_w_ts)
deltat_k_ts = np.full(NUM_STEPS, deltat_nom_k)

n_consumers    = len(net.heat_consumer)
consumer_names = net.heat_consumer["name"].values

# Replicate profile for all consumers
qext_profile = pd.DataFrame(
    data=np.tile(qext_w_ts.reshape(-1, 1), (1, n_consumers)),
    columns=consumer_names
)
deltat_profile = pd.DataFrame(
    data=np.tile(deltat_k_ts.reshape(-1, 1), (1, n_consumers)),
    columns=consumer_names
)

# Handle zero-demand timesteps (numerical stability)
qext_min = deltat_min = 1e-6
mask = qext_profile < qext_min
qext_profile[mask]   = qext_min
deltat_profile[mask] = deltat_min

# DFData wrappers
qext_data   = DFData(qext_profile)
deltat_data = DFData(deltat_profile)

# Controllers
for i, hc_idx in enumerate(net.heat_consumer.index):
    ConstControl(net, element="heat_consumer", variable="qext_w",
                 element_index=hc_idx,
                 profile_name=consumer_names[i], data_source=qext_data)
    ConstControl(net, element="heat_consumer", variable="deltat_k",
                 element_index=hc_idx,
                 profile_name=consumer_names[i], data_source=deltat_data)

# Output writer
log_variables = [
    ("res_junction",            "t_k"),
    ("res_junction",            "p_bar"),
    ("res_pipe",                "mdot_from_kg_per_s"),
    ("res_heat_consumer",       "t_from_k"),
    ("res_heat_consumer",       "t_to_k"),
    ("res_heat_consumer",       "mdot_from_kg_per_s"),
    ("res_circ_pump_pressure",  "mdot_from_kg_per_s"),
    ("res_circ_pump_pressure",  "qext_w"),
]
ow = OutputWriter(net, range(NUM_STEPS), output_path=None,
                  log_variables=log_variables)

# ---------------------------------------------------------------------------
# Time-series simulation
# ---------------------------------------------------------------------------
print(f"\nRunning time-series simulation ({NUM_STEPS} steps, dt=10 min)...")
t0 = time.perf_counter()
run_time_series.run_timeseries(net, range(NUM_STEPS),
                               mode="bidirectional", verbose=False)
sim_time = time.perf_counter() - t0
print(f"Completed in {sim_time:.1f} s  ({sim_time/NUM_STEPS*1000:.1f} ms/step)")

# ---------------------------------------------------------------------------
# Post-processing — results extraction
# ---------------------------------------------------------------------------
dt_min = 10
time_h = np.arange(NUM_STEPS) * dt_min / 60

results        = ow.output
T_junc_df      = results["res_junction.t_k"]       - 273.15   # degC
p_junc_df      = results["res_junction.p_bar"]
mdot_pipe_df   = results["res_pipe.mdot_from_kg_per_s"]
T_hc_from_df   = results["res_heat_consumer.t_from_k"]  - 273.15
T_hc_to_df     = results["res_heat_consumer.t_to_k"]    - 273.15
mdot_hc_df     = results["res_heat_consumer.mdot_from_kg_per_s"]
mdot_pump_df   = results["res_circ_pump_pressure.mdot_from_kg_per_s"]
qext_pump_df   = results["res_circ_pump_pressure.qext_w"]

# Junction name -> column position map
junc_names = net.junction["name"].values
junc_col   = {name: i for i, name in enumerate(junc_names)}

# Consumer name -> column position map
hc_names   = net.heat_consumer["name"].values
hc_col     = {name: i for i, name in enumerate(hc_names)}