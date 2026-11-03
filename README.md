# Synthetic Benchmark Networks for District Heating Systems: A Systematic Review and Standardisation Framework

**`dhn-benchmark`: a reproducible set of seven synthetic district heating network archetypes for validating and comparing thermo-hydraulic simulation tools.**

This repository is the companion code and data of the paper

> *Synthetic Benchmark Networks for District Heating Systems: A Systematic Review and Standardisation Framework* (in preparation).

Electric power systems have long relied on shared test cases (IEEE test feeders, CIGRE, ACTIVSg, SimBench, etc.) to validate and compare simulation tools on common ground. District heating research offers only limited first attempts at standardised, open benchmark networks for validating and comparing thermo-hydraulic models: most studies use proprietary utility data or case-specific models that cannot be reproduced or compared. The paper reviews the open-source tools for thermo-hydraulic simulation of district heating networks (DHNs) and proposes a benchmark framework, designed by analogy with the power-system benchmarks.

The repository contains everything needed to **regenerate** each archetype, the **network data** ready to load into any simulator, a **reference implementation in [pydhn](https://github.com/idiap/pydhn)** and the **simulation results** reported in the paper.

---

## Benchmark definition

The benchmark is organised around two complementary pillars.

- **Benchmark objectives** define the analytical purpose for which a network is used: the physical phenomenon, solver behaviour or technological characteristic that it is intended to exercise.
- **Network descriptors** define the physical and technological identity of the network: its district heating generation, topology and scale, in accordance with the taxonomy of the paper.

The archetypes are conceived with a challenge-driven approach: each network has been designed to meet a benchmarking objective and is defined by a combination of network descriptors.

### Benchmark objectives

For each objective, the network descriptors are either held constant or varied, to isolate the phenomenon under study.

| Objective | Purpose                                                                                                                                | Descriptor fixed | Descriptor varied                                       |
|---|----------------------------------------------------------------------------------------------------------------------------------------|---|---------------------------------------------------------|
| **THV**: Thermo-Hydraulic Validation | Validate the solver behaviour: algorithm convergence and accuracy of the hydraulic and thermal results                                 | Generation (3GDH), scale (small) | Topology (radial → ring → meshed)                       |
| **TA**: Technology Assessment | observe the behavior of the network against the characteristic  and operating mode of each district heating generation | Topology (meshed), scale (medium) | Generation (3GDH → 4GDH → 5GDHC)                        |
| **CS**: Computational Scalability | Quantify how solver performance scales with problem dimension                                                                          | Generation (3GDH) | Topology (small-scale series) and scale (meshed series) |

### Network descriptors and archetype naming

Each archetype is identified by a code of the form ```{Generation}_{Topology}_{Scale}_{Variant}```

| Field | Values                                    |
|---|-------------------------------------------|
| Generation | `3G` (3GDH) · `4G` (4GDH) · `5G` (5GDHC)  |
| Topology | `R` radial · `L` ring (loop) · `M` meshed |
| Scale | `S` small · `M` medium · `L` large        |
| Variant | `BASE`: reference operating scenario.     |


### Methodologies for generating archetypes

Two methods are used, each suited to different requirements, following the hybrid approach of power-system benchmarks.

**Methodology I: purpose-driven design** (`networks/methodology_I.py`). Similarity to IEEE test feeders, the structure of the network is prescribed, which gives topological control and analytic tractability. Node coordinates are prescribed, pipe lengths are the Euclidean distances between nodes, and the layout is fully deterministic. The topologies are obtained by nesting on a common radial base (radial → ring → meshed). Used for the THV archetypes.

**Methodology II: algorithmic generation** (`networks/methodology_II.py`). Analogously to ACTIVSg and SimBench, the structure is derived from a synthetic urban street graph, which gives physical plausibility and structural diversity. A network is generated in three steps: (1) a synthetic urban district (blocks, centreline streets, substations), (2) its street graph, (3) the DHN layout routed along the streets as a constrained Steiner tree grown from the heat source(s).

### Reference scenario (base problem variant)

All archetypes are released with a common reference scenario, which fixes the operating conditions of each generation and the thermal load of every substation.

| Generation | Supply temperature | Temperature drop | Reference pressure | Sources |
|---|---|---|---|---|
| 3GDH | 80 °C | 30 K | 10 bar | 1 centralised source (constant temperature, variable flow) |
| 4GDH | 60 °C | 20 K | 8 bar | 2 centralised sources: main (constant temperature, variable flow) + secondary (constant temperature, imposed mass flow) |
| 5GDHC | 20 °C | 5 K | 6 bar | 1 centralised source + 10 distributed prosumers (10 % of the buildings) |

- **Demand:** one synthetic winter week at 10-minute resolution (1008 time steps). Normalised daily profile with a morning peak of 1.00 at 07:00 (linear rise from 06:00, decay to 0.35 by 08:00, steady level until 22:00, zero overnight), repeated on all seven days. All substations share a peak load of 175 kW. The profile follows the structure of measured substation profiles of the Turin DHN.
- **Pipes:** sized from EN 253 / EN 10220 catalogues. 3G and 4G use pre-insulated steel / PUR / HDPE pipes; 5G uses non-insulated PE100 pipes. THV networks are sized with a 5 % heat-loss allowance and a velocity limit of 1.5 m/s; Methodology II networks are sized on the N-1 design flow.
- **Soil and water:** soil properties follow EN 13941 (λ = 1.5 W/m·K, T = 10 °C, burial depth 0.8 m). Water properties are evaluated at each generation's operating temperature.

---

## Benchmark archetype networks

The benchmark consists of seven archetypes. The tables report, for each of them, the archetype ID, the generation method, the benchmark objectives it serves and its network descriptors.

| Archetype ID | Generation method | Benchmark objectives | Generation | Topology | Scale |
|---|---|---|---|---|---|
| `3G_R_S` | Methodology I | THV · CS | 3GDH | Radial | Small |
| `3G_L_S` | Methodology I | THV · CS | 3GDH | Ring | Small |
| `3G_M_S` | Methodology I | THV · CS | 3GDH | Meshed | Small |
| `3G_M_M` | Methodology II | TA · CS | 3GDH | Meshed | Medium |
| `4G_M_M` | Methodology II | TA | 4GDH | Meshed | Medium |
| `5G_M_M` | Methodology II | TA | 5GDHC | Meshed | Medium |
| `3G_M_L` | Methodology II | CS | 3GDH | Meshed | Large |

CS uses two series: a **topology series** at small scale (`3G_R_S`, `3G_L_S`, `3G_M_S`) and a **size series** at meshed topology (`3G_M_S`, `3G_M_M`, `3G_M_L`).

Main characteristics of each archetype:

| Archetype ID | Substations | Nodes | Pipes | Loops | α | Pipe length [km] | Sources           |
|---|---|---|---|-------|---|---|-------------------|
| `3G_R_S` | 10 | 22 | 21 | 0     | 0 | 1.75 | 1 centralised     |
| `3G_L_S` | 10 | 22 | 22 | 1     | 0.026 | 2.20 | 1 centralised     |
| `3G_M_S` | 10 | 27 | 32 | 6     | 0.122 | 3.70 | 1 centralised     |
| `3G_M_M` | 100 | 221 | 224 | 4     | 0.009 | 8.61 | 1 centralised     | 
| `4G_M_M` | 100 | 223 | 224 | 2     | 0.005 | 8.52 | 2 centralised     |
| `5G_M_M` | 90 + 10 prosumers | 221 | 224 | 4     | 0.009 | 8.61 | 1 centralised + 10 prosumers |
| `3G_M_L` | 400 | 931 | 944 | 14    | 0.008 | 62.68 | 1 centralised |

**THV archetypes** share a common geometry: a 500 × 500 m footprint, the heat source at the north-west corner and 10 substations, each connected through a 20 m service pipe. The three networks differ only in the topological template: `3G_R_S` is the radial base (two feeders along the perimeter, with an analytical reference solution); `3G_L_S` closes the two feeders into a ring; `3G_M_S` adds three straight chords to the ring and is a diagnostic stress test rather than a representative topology.

**TA archetypes** share the same synthetic district (1200 × 800 m, 5 × 7 blocks, 100 substations, street width 15 m, block-size variation 0.25, substation displacement 7 m, β = 1.00, seed 42). They differ in the operating conditions and in the configuration of the heat sources, which slightly changes the routing graph produced by the Steiner algorithm.

**`3G_M_L`** is built on a larger district (4000 × 3000 m, 12 × 16 blocks, 400 substations, substation displacement 8 m); the other parameters are those of the TA set.

---

## Repository structure

```
dhn-benchmark/
├── README.md
├── LICENSE
├── requirements.txt               # Python environment (pydhn pinned to a specific commit)
└── archetypes_generation/
    ├── constants.py               # all physical & engineering parameters, with standard references
    ├── export_constants.py        # exports constants.py → data/parameters.csv
    ├── pipe_system.py             # pipe materials, catalogues, sizing (select_dn), U-values
    ├── demand_profile.py          # normalised substation demand profile
    ├── plotting.py                # topology plotting helper
    │
    ├── data/                      # INPUTS SHARED BY ALL ARCHETYPES
    │   ├── parameters.csv         # human-readable table of every parameter used (fluid, soil, materials, catalogues)
    │   └── demand_profile.csv     # weekly demand time series (1008 steps, 10 min)
    │
    ├── networks/                  # GENERATORS
    │   ├── methodology_I.py       # Methodology I: purpose-driven design (reusable module)
    │   ├── methodology_II.py      # Methodology II: district → street graph → Steiner tree (reusable module)
    │   ├── 3G_R_S_BASE.py         # one script per archetype, built on the two methodologies
    │   ├── 3G_L_S_BASE.py
    │   ├── 3G_M_S_BASE.py
    │   ├── 3G_M_M_BASE.py
    │   ├── 4G_M_M_BASE.py
    │   ├── 5G_M_M_BASE.py
    │   └── 3G_M_L_BASE.py
    │
    ├── archetypes/                # BENCHMARK DATA: one folder per archetype (output of networks/)
    │   └── <CODE>_BASE/
    │       ├── nodes.csv              # nodes and boundary conditions
    │       ├── pipes.csv              # pipes with every geometric, hydraulic and thermal parameter
    │       ├── incidence_matrix.csv   # node–pipe incidence matrix
    │       ├── topology.png           # layout plot
    │       ├── model_pydhn.ipynb      # reference implementation and simulation in pydhn
    │       └── (archetype-specific files, see below)
    │
    └── results/                   # REFERENCE RESULTS
        ├── <CODE>_BASE_results.xlsx   # pydhn simulation results, one workbook per archetype
        ├── archetype_results.ipynb    # post-processing: KPIs and figures of the paper
        └── output/
            ├── layouts/               # layout figure of each archetype
            └── results/               # result figures and benchmark_indicators.csv (KPI table)
```

If you only want to **use** the benchmark in your own tool, the `archetypes/` folder (plus `data/demand_profile.csv`) is all you need. `networks/` is there to **reproduce or extend** it: `methodology_I.py` and `methodology_II.py` can be imported to build new networks with the same methods (see the example at the top of each file), and the archetype scripts show how they are used for the benchmark.

---

## How to read the data

All files are plain CSV. Every column name ends with its **unit** (e.g. `length_m`, `d_inner_m`, `roughness_mm`, `T_supply_set_degC`, `U_linear_WmK`, `Q_W`).

### `nodes.csv`

One row per node. The boundary-condition columns are filled only for the node types they apply to; they are empty otherwise.

| Column | Group | Meaning |
|---|---|---|
| `node_id` | Identification | node identifier; referenced by `from_node` and `to_node` in `pipes.csv` |
| `node_type` | Identification | `source`, `junction`, `substation` or `prosumer` |
| `x_m`, `y_m` | Location | node coordinates [m] |
| `Q_peak_W` / `Q_peak_heat_W` | Demand | substation heat demand: references the time series `data/demand_profile.csv` |
| `delta_T_nom_K` | Demand | nominal supply–return temperature difference [K]  |
| `T_supply_set_degC` | Supply | supply temperature set-point [°C]  |
| `p_pump_set_bar` / `p_ref_bar` | Supply | reference (pump) pressure of the source [bar], relative |
| `m_flow_set_kg_s` | Supply | imposed mass flow of the secondary source `src1`: references `src1_mdot_profile.csv` |
| `Q_prosumer_W` | Prosumer | heat injected by the prosumer: references `prosumer_production_profile.csv` |
| `prosumer` | Prosumer | prosumer flag  |

Each node is a **single physical point**. Simulators that model supply and return lines separately (as pydhn) duplicate every node into `<id>_s` and `<id>_r`. In `4G_M_M` the two sources are `src0` (main, pressure reference) and `src1` (secondary).

### `pipes.csv`

One row per pipe, from `from_node` to `to_node`. Each row is **one line**: the supply and the return pipe are identical copies of it.

| Column | Parameter      | Meaning |
|---|----------------|---|
| `pipe_id` | Identification | pipe identifier, `<from_node>_<to_node>` |
| `from_node`, `to_node` | Identification | end nodes of the pipe (`node_id` in `nodes.csv`); the orientation defines the positive flow direction and the sign in `incidence_matrix.csv` |
| `length_m` | Geometry       | pipe length [m] |
| `DN_mm` | Geometry       | nominal diameter of the selected pipe [mm] |
| `d_inner_m` | Geometry       | inner diameter of the carrier pipe [m] |
| `d_outer_m` | Geometry       | outer diameter of the carrier pipe [m] |
| `d_casing_m` | Geometry       | outer diameter of the casing [m] |
| `wall_m` | Layers         | wall thickness of the carrier pipe [m] |
| `insulation_thickness_m` | Layers         | thickness of the insulation layer [m] |
| `casing_thickness_m` | Layers         | wall thickness of the outer casing [m] |
| `roughness_mm` | Hydraulics     | absolute roughness of the carrier pipe inner surface [mm] |
| `fluid_rho_kgm3` | Fluid          | water density at the generation's operating temperature [kg/m³] |
| `fluid_cp_JkgK` | Fluid          | water specific heat capacity [J/(kg·K)] |
| `fluid_mu_Pas` | Fluid          | water dynamic viscosity [Pa·s] |
| `fluid_lambda_WmK` | Fluid          | water thermal conductivity [W/(m·K)] |
| `carrier_material` | Material       | carrier pipe material |
| `carrier_rho_kgm3`, `carrier_cp_JkgK`, `carrier_lambda_WmK` | Material       | density [kg/m³], specific heat capacity [J/(kg·K)] and thermal conductivity [W/(m·K)] of the carrier pipe |
| `insulation_material` | Material       | insulation material  |
| `PUR_rho_kgm3`, `PUR_cp_JkgK`, `PUR_lambda_WmK` | Material       | density, specific heat capacity and thermal conductivity of the insulation |
| `casing_material` | Material       | casing material |
| `HDPE_rho_kgm3`, `HDPE_cp_JkgK`, `HDPE_lambda_WmK` | Material       | density, specific heat capacity and thermal conductivity of the casing |
| `burial_depth_m` | Burial         | burial depth of the pipe axis [m] |
| `soil_lambda_WmK` | Burial         | soil thermal conductivity [W/(m·K)] |
| `T_ground_degC` | Burial         | undisturbed ground temperature [°C] |
| `h_ext_Wm2K` | Burial         | external heat transfer coefficient of the soil [W/(m²·K)] |
| `U_linear_WmK` | Heat loss      | reference linear heat-loss coefficient of the buried pipe [W/(m·K)], computed analytically by `pipe_system.py`; use it to cross-check the thermal model of any tool |
| `U_Wm2K` | Heat loss      | `U_linear_WmK` referred to the outer surface of the carrier pipe, `U_linear / (π · d_outer)` [W/(m²·K)] |

### `incidence_matrix.csv`

Rows are nodes, columns are pipes. An entry is `-1` where the pipe leaves the node, `+1` where it enters it, and `0` otherwise.

### Archetype-specific files

| File | Archetype | Content                                  |
|---|---|------------------------------------------|
| `src1_mdot_profile.csv` | `4G_M_M` | mass-flow schedule of the secondary source |
| `prosumer_production_profile.csv` | `5G_M_M` | heat-injection profile of the prosumers |
| `pipe_design_flows.csv` | `5G_M_M` | design flow, velocity and selected DN of each pipe (sizing record) |

### Time series

Every time series (`data/demand_profile.csv` and the archetype-specific profiles) has the columns `timestep, label, f_normalised, <value>`, with a 10-minute step and 1008 steps (Mon 00:00 → Sun 23:50). `f_normalised` is the profile scaled to [0, 1]; `<value>` is `Q_W` for heat or `mdot_kg_s` for mass flow.

### Results (`results/<CODE>_BASE_results.xlsx`)

One sheet per variable, with time in rows (1008 steps; the 1-day pre-heating used to initialise the network is not included) and elements in columns. Sheet names follow `<element>_<variable>_<unit>`:

| Prefix / sheet | Content |
|---|---|
| `sub_*` | substations (supply and return temperature, ΔT, mass flow, heat) |
| `pro_cons_*`, `pro_prod_*` | prosumers, consumption side and production side |
| `source` | heat source(s) |
| `pipe_s_*`, `pipe_r_*` | supply and return pipes (pressure drop, mass flow, outlet temperature, heat losses) |
| `junction_T_degC` | junction temperatures |
| `energy_balance` | weekly network energy balance |
| `solver_iteration`, `convergence_traj` | solver iteration counts and convergence trajectories |

`results/output/results/benchmark_indicators.csv` collects the KPIs of all archetypes (heat produced, heat losses, supply temperatures, maximum velocity and pressure gradient, pumping energy, flow-direction indicators).

---

## Reproducing the results

```bash
# 1. Environment (Python 3.11; pydhn requires Python >= 3.9 and < 3.13)
python -m venv .venv
.venv\Scripts\activate            # Windows   |   source .venv/bin/activate  (Linux/macOS)
pip install -r requirements.txt   # installs pydhn from the pinned commit

# 2. (Optional) regenerate an archetype: rewrites archetypes/<CODE>_BASE/
python archetypes_generation/networks/3G_M_M_BASE.py

# 3. Simulate it: run the notebook from inside its own folder
jupyter lab archetypes_generation/archetypes/3G_M_M_BASE/model_pydhn.ipynb
#    → writes archetypes_generation/results/3G_M_M_BASE_results.xlsx

# 4. Post-process all archetypes and produce the paper figures and KPI table
jupyter lab archetypes_generation/results/archetype_results.ipynb
```

All generators are deterministic, with fixed random seeds. The physical parameters live only in `constants.py` and `pipe_system.py`. To change an assumption, edit it there, then run `export_constants.py` and regenerate the archetypes.

## Using the benchmark with another tool

1. Load `nodes.csv` and `pipes.csv` from the archetype folder.
2. Duplicate the network into supply and return lines.
3. Apply the boundary conditions and the time series as described above.
4. Simulate the 1008 steps (7 days at a 10-minute step). If necessary, initialise the network with a 1-day pre-heating at constant initial demand.
5. Compare your outputs with `results/<CODE>_BASE_results.xlsx`.

The pydhn notebooks are a complete, commented example of these steps. Acceptability thresholds for the KPIs are not defined: they require the comparison of several tools on the same archetypes, which is left to future work.

---

## Citation

If you use these networks, please cite the paper (full reference available upon publication).

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
