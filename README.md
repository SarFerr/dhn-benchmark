# dhn-benchmark

**Synthetic benchmark networks for district heating systems: a reproducible archetype family for validating thermo-hydraulic simulation tools.**

This repository is the companion code and data of the paper

> *Synthetic Benchmark Networks for District Heating Systems: A Comprehensive Review and Standardisation Framework* (in preparation).

---

## About the work

Electric power systems have long relied on shared test cases (IEEE test feeders, CIGRE, ACTIVSg, SimBench) to validate and compare simulation tools on common ground. District heating research has no equivalent: most thermo-hydraulic studies use proprietary utility data, oversimplified networks or case-specific models that cannot be reproduced or compared.

The paper reviews the open-source tools for thermo-hydraulic simulation of district heating networks (DHNs). It then proposes a **standardisation framework and a family of synthetic benchmark networks (archetypes)**, designed by analogy with the power-system benchmarks. Archetypes are selected by the **validation challenge** they address, not by enumerating every combination of generation × topology × scale. They are grouped into three validation classes:

| Class | Purpose | Varied parameter |
|---|---|---|
| **THV**: Thermo-Hydraulic Validation | Solver convergence, accuracy of pressure, mass-flow and temperature fields, cross-tool comparison | Topology (radial → ring → meshed), with generation and scale fixed |
| **TG**: Technology Generation | Behaviour across DH generations (3GDH, 4GDH, 5GDHC), including multi-source operation and bidirectional prosumer flows | Generation, with topology and scale fixed |
| **CS**: Computational Scalability | Computational cost and practical size limits of each tool | Size (small → medium → large) |

This repository contains everything needed to **regenerate** each archetype, the **network data** ready to load into any simulator, a **reference implementation in [pydhn](https://github.com/idiap/pydhn)** and the **simulation results** used in the paper.

---

## Archetype naming

Each archetype is identified by a code of the form

```
{Generation}_{Topology}_{Scale}_{Variant}
```

| Field | Values |
|---|---|
| Generation | `3G` (3GDH, 80 °C), `4G` (4GDH, 60 °C), `5G` (5GDHC, 20 °C ambient loop) |
| Topology | `R` radial · `L` ring (loop) · `M` meshed |
| Scale | `S` small · `M` medium · `L` large |
| Variant | `BASE`: the base operating scenario (the only one released so far; the field is reserved for future time-series/operating variants) |

A single archetype can serve more than one validation class. For example, `3G_M_M` is both the 3GDH case of the TG class and the medium case of the CS class.

## The archetypes

| Code | Class(es) | Substations | Nodes | Pipes | Length [km] | Construction | Operating point |
|---|---|---|---|---|---|---|---|
| `3G_R_S` | THV-R | 10 | 15 | 14 | 1.9 | Methodology I | 80 °C, ΔT 30 K, 10 bar |
| `3G_L_S` | THV-L | 10 | 19 | 19 | 2.7 | Methodology I | 80 °C, ΔT 30 K, 10 bar |
| `3G_M_S` | THV-M · CS-S | 10 | 19 | 26 | 3.7 | Methodology I | 80 °C, ΔT 30 K, 10 bar |
| `3G_M_M` | TG-3 · CS-M | 100 | 221 | 224 | 8.6 | Methodology II | 80 °C, ΔT 30 K, 10 bar |
| `4G_M_M` | TG-4 | 100 | 223 | 224 | 8.5 | Methodology II | 60 °C, ΔT 20 K, 8 bar, **2 sources** |
| `5G_M_M` | TG-5 | 90 + 10 prosumers | 221 | 224 | 8.6 | Methodology II | 20 °C, ΔT 5 K, 6 bar, **bidirectional** |
| `3G_M_L` | CS-L | 400 | 931 | 944 | 62.7 | Methodology II | 80 °C, ΔT 30 K, 10 bar |

**Methodology I: purpose-driven design** (THV archetypes). Networks are built by hand from prescribed rules, in the spirit of the IEEE test feeders. Each has exactly 10 substations, pipe lengths drawn from U[100, 200] m (seed 42), and a prescribed topology:
- radial: binary tree of depth 3, no loops;
- ring: one closed main loop;
- meshed: 8 independent loops, a deliberate stress test.

**Methodology II: algorithmic generation** (TG and CS archetypes). In the spirit of ACTIVSg and SimBench, these are built in three steps: a synthetic urban district, its street graph, and the DHN layout routed along the streets as a constrained Steiner tree (`networks/synthetic_district.py`).

**Common assumptions.**
- **Demand:** every substation follows the same normalised daily profile (175 kW peak), at 10-minute resolution over one week (1008 steps).
- **Pipes:** pipes are sized from EN 253 / EN 10220 catalogues. 3G and 4G use pre-insulated steel / PUR / HDPE pipes; 5G uses non-insulated PE100 pipes.
- **Soil and water:** soil properties follow EN 13941 (λ = 1.5 W/m·K, T = 10 °C, burial depth 0.8 m). Water properties are evaluated at each generation's operating temperature.

---

## Repository structure

```
dhn-benchmark/
├── requirements.txt               # pinned Python environment (pydhn pinned to a specific commit)
└── archetypes_generation/
    ├── constants.py               # all physical & engineering parameters, with standard references
    ├── export_constants.py        # exports constants.py → data/parameters.csv
    ├── pipe_system.py             # single source of truth for pipe materials, catalogues, sizing, U-values
    ├── demand_profile.py          # normalised substation demand profile
    ├── plotting.py                # topology plotting helper
    │
    ├── data/
    │   ├── parameters.csv         # human-readable table of every parameter used (fluid, soil, materials, catalogues)
    │   └── demand_profile.csv     # weekly demand time series shared by all archetypes
    │
    ├── networks/                  # GENERATORS: one script per archetype
    │   ├── synthetic_district.py  # district → street graph → Steiner-tree layout (Methodology II)
    │   ├── 3G_R_S_BASE.py
    │   ├── ...
    │   └── 5G_M_M_BASE.py
    │
    ├── archetypes/                # BENCHMARK DATA: one folder per archetype (output of networks/)
    │   └── <CODE>_BASE/
    │       ├── nodes.csv              # nodes and boundary conditions
    │       ├── pipes.csv              # pipes with every geometric, hydraulic and thermal parameter
    │       ├── incidence_matrix.csv   # node–pipe incidence matrix
    │       ├── topology.png           # layout plot
    │       ├── model_pydhn.ipynb      # reference implementation and simulation in pydhn
    │       └── (archetype-specific time series, see below)
    │
    └── results/
        ├── <CODE>_BASE_results.xlsx   # pydhn simulation results, one workbook per archetype
        ├── archetype_results.ipynb    # post-processing and figures for the paper
        └── figures/
```

If you only want to **use** the benchmark in your own tool, the `archetypes/` folder is all you need. `networks/` is there to **reproduce or extend** it.

---

## How to read the data

All files are plain CSV. Every column name ends with its **unit** (e.g. `length_m`, `d_inner_m`, `roughness_mm`, `T_supply_set_degC`, `U_linear_WmK`, `Q_W`).

### `nodes.csv`

One row per node. `node_type` is one of `source`, `junction`, `substation`, `prosumer` (5G only). Coordinates are `x_m`, `y_m`. The remaining columns are boundary conditions, filled only where they apply:

| Column | Applies to | Meaning |
|---|---|---|
| `T_supply_set_degC` | source (and 5G prosumer) | supply temperature set-point |
| `p_pump_set_bar` / `p_ref_bar` | source | reference (pump) pressure, relative |
| `delta_T_nom_K` | substation, prosumer | nominal supply–return temperature difference |
| `Q_peak_W` / `Q_peak_heat_W` | substation | demand time series; it references `data/demand_profile.csv` |
| `m_flow_set_kg_s` | 4G secondary source | references `src1_mdot_profile.csv` |
| `Q_prosumer_W`, `prosumer` | 5G | references `prosumer_production_profile.csv`, plus a prosumer flag |

Each node is a **single physical point**. Simulators that model supply and return lines separately (as pydhn does) duplicate every node into `<id>_s` and `<id>_r`.

### `pipes.csv`

One row per pipe, from `from_node` to `to_node`. Each row is **one line**: the supply and the return pipe are identical copies of it. The columns, in groups:

- **Geometry:** `length_m`, `DN_mm`, `d_inner_m`, `d_outer_m`, `wall_m`, `insulation_thickness_m`, `casing_thickness_m`, `d_casing_m`.
- **Hydraulics:** `roughness_mm`.
- **Fluid:** `fluid_rho_kgm3`, `fluid_cp_JkgK`, `fluid_mu_Pas`, `fluid_lambda_WmK`.
- **Layers:** carrier pipe (`carrier_material`, `carrier_rho_kgm3`, `carrier_cp_JkgK`, `carrier_lambda_WmK`), insulation (`insulation_material`, `PUR_*`) and casing (`casing_material`, `HDPE_*`). In 5G the insulation and casing are `none`, with zero thickness and zero properties.
- **Burial:** `burial_depth_m`, `soil_lambda_WmK`, `T_ground_degC`, `h_ext_Wm2K`.
- **Reference heat-loss coefficients:** `U_linear_WmK` (per metre of pipe) and `U_Wm2K`, computed analytically by `pipe_system.py`. Use them to cross-check the thermal model of any tool.

### `incidence_matrix.csv`

Rows are nodes, columns are pipes. An entry is `-1` where the pipe leaves the node, `+1` where it enters it, and `0` otherwise.

### Archetype-specific files

| File | Archetype | Content |
|---|---|---|
| `src1_mdot_profile.csv` | `4G_M_M` | mass-flow schedule of the secondary source (the primary source is the pressure reference and acts as slack) |
| `prosumer_production_profile.csv` | `5G_M_M` | heat-injection profile of the prosumers (the central plant acts as slack) |
| `pipe_design_flows.csv` | `5G_M_M` | design flow, velocity and selected DN of each pipe (sizing record) |

### Time series

Every time series has the columns `timestep, label, f_normalised, <value>`, with a 10-minute step and 1008 steps (Mon 00:00 → Sun 23:50). `f_normalised` is the profile scaled to [0, 1].

### Results (`results/<CODE>_BASE_results.xlsx`)

One sheet per variable. Each sheet has time in rows (after a 1-day warm-up) and elements in columns. Sheet names follow `<element>_<variable>_<unit>`:

| Prefix | Element |
|---|---|
| `sub_*` | substations |
| `pro_cons_*`, `pro_prod_*` | 5G prosumers, consumption side and production side |
| `src_*` / `source` | sources |
| `pipe_s_*`, `pipe_r_*` | supply and return pipes |
| `junction_T_degC` | junction temperatures |
| `energy_balance` | weekly network energy balance |

---

## Reproducing the results

```bash
# 1. Environment (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate            # Windows   |   source .venv/bin/activate  (Linux/macOS)
pip install -r requirements.txt   # installs pydhn from the pinned commit

# 2. (Optional) regenerate an archetype: rewrites archetypes/<CODE>_BASE/
python archetypes_generation/networks/3G_M_M_BASE.py

# 3. Simulate it: run the notebook from inside its own folder
jupyter lab archetypes_generation/archetypes/3G_M_M_BASE/model_pydhn.ipynb
#    → writes archetypes_generation/results/3G_M_M_BASE_results.xlsx

# 4. Post-process all archetypes and produce the paper figures
jupyter lab archetypes_generation/results/archetype_results_test.ipynb
```

All generators are deterministic, with fixed random seeds. The physical parameters live only in `constants.py` and `pipe_system.py`. To change an assumption, edit it there, then run `export_constants.py` and regenerate the archetypes.

## Using the benchmark with another tool

1. Load `nodes.csv` and `pipes.csv` from the archetype folder.
2. Duplicate the network into supply and return lines.
3. Apply the boundary conditions and time series as described above.
4. Simulate the same 7 days at a 10-minute step, discarding the first day as warm-up.
5. Compare your outputs with `results/<CODE>_BASE_results.xlsx`.

The pydhn notebooks are a complete, commented example of these steps.

---

## Citation

If you use these networks, please cite the paper (full reference available upon publication).

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
