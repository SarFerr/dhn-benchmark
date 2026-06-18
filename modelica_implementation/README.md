# DHN-Benchmark

Synthetic benchmark networks for district heating systems (DHNs), implemented in
OpenModelica using the [Buildings](https://github.com/lbl-srg/modelica-buildings)
library (`Buildings.DHC` framework).

Companion repository to the paper:

> *Synthetic Benchmark Networks for District Heating Systems: A Comprehensive
> Review and Standardisation Framework* — S. Ferrero, D.S. Schiera,
> F.D. Minuto, A. Lanzini.

## Requirements

- [OpenModelica](https://openmodelica.org/) ≥ 1.26.3
- Modelica Standard Library **4.1.0**
- Buildings Library **13.0.0**

## Repository structure

```
DHN-Benchmark/
├── package.mo                # library root
├── Components/               # reusable custom blocks
│   ├── PlantStation.mo        # ideal central heat plant
│   ├── DHNPipe.mo              # two-pipe segment, plug-flow + ground losses
│   ├── DHNJunction.mo          # two-pipe T-junction (radial trees)
│   └── BuildingWithIndirectETS.mo  # substation, indirect ETS + time-series load
├── Archetypes/                # benchmark network instances
│   └── DHN_THV_3G_R_S_BASE.mo  # Thermo-Hydraulic Validation, 3GDH, Radial, Small
├── InputData/                 # heating load time series (.mos)
│   └── demand_profile_base.mos
├── Scripts/                   # Python post-processing tools
│   └── extract_results_DHN_THV_3G_R_S_BASE.py
└── Results/                   # simulation outputs (CSV, gitignored)
```

## Getting started

1. Clone this repository.
2. In OMEdit: `File → Open Model/Library File...` and select `package.mo` at the repository root.
3. Open `Archetypes.DHN_THV_3G_R_S_BASE`, update the `filNam` parameter to point to
   `InputData/demand_profile_base.mos` on your local path, and run the simulation
   (`experiment` settings: 7 days, 600 s resolution).
4. Export results to CSV with the provided Python script:

   ```bash
   pip install buildingspy
   python Scripts/extract_results_DHN_THV_3G_R_S_BASE.py <path_to_res.mat>
   ```

## Benchmark naming convention

Each archetype follows the six-field code:

```
DHN_{Objective}_{Generation}_{Topology}_{Scale}_{Variant}
```

| Field | Values |
|---|---|
| Objective | `THV` (thermo-hydraulic validation), `TG` (technology assessment), `CS` (scalability) |
| Generation | `3G`, `4G`, `5G` |
| Topology | `R` (radial), `L` (ring/loop), `M` (meshed) |
| Scale | `S` (small), `M` (medium), `L` (large) |
| Variant | `BASE` (currently the only implemented variant) |

## Status

| Archetype | Status |
|---|---|
| `DHN_THV_3G_R_S_BASE` | ✅ implemented and validated |
| `DHN_THV_3G_L_S_BASE` | planned |
| `DHN_THV_3G_M_S_BASE` | planned |
| `DHN_TG_*` | planned |
| `DHN_CS_*` | planned |

## License

TBD.
