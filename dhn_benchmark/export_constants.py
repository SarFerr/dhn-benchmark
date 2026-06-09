# export_constants.py
#
# Exports all physical and engineering parameters from constants.py
# to a single readable CSV file: data/parameters.csv
#
# The CSV is structured in labelled sections so it can be read by
# anyone: Python, Matlab, Excel, or manually in Modelica.
#
# Usage:
#   python export_constants.py
# Output:
#   data/parameters.csv

import csv
import os
import sys

# Make sure Python can find constants.py (same folder as this script)
sys.path.insert(0, os.path.dirname(__file__))
from dhn_benchmark.constants import (
    RHO_WATER_3G, CP_WATER_3G, MU_WATER_3G,
    RHO_WATER_4G, CP_WATER_4G, MU_WATER_4G,
    RHO_WATER_5G, CP_WATER_5G, MU_WATER_5G,
    LAMBDA_SOIL, T_GROUND, BURIAL_DEPTH,
    LAMBDA_STEEL, ROUGHNESS_STEEL, E_STEEL, ALPHA_STEEL,
    LAMBDA_PEX, ROUGHNESS_PEX, LAMBDA_HDPE,
    LAMBDA_PUR,
    PIPE_CATALOGUE,
    GEN_OPERATING,
    DN_BY_GEN_LEVEL,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "parameters.csv")


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    rows = []

    # ------------------------------------------------------------------
    # Helper: section separator
    # ------------------------------------------------------------------
    def section(title):
        rows.append([])
        rows.append(["# " + title, "", "", ""])

    # ------------------------------------------------------------------
    # 1. Fluid properties
    # ------------------------------------------------------------------
    section("FLUID PROPERTIES")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    fluid_params = [
        ("rho",  "3G", RHO_WATER_3G, "kg/m3",   "Water density at 80 deg C"),
        ("cp",   "3G", CP_WATER_3G,  "J/(kg·K)", "Water specific heat at 80 deg C"),
        ("mu",   "3G", MU_WATER_3G,  "Pa·s",     "Water dynamic viscosity at 80 deg C"),
        ("rho",  "4G", RHO_WATER_4G, "kg/m3",    "Water density at 60 deg C"),
        ("cp",   "4G", CP_WATER_4G,  "J/(kg·K)", "Water specific heat at 60 deg C"),
        ("mu",   "4G", MU_WATER_4G,  "Pa·s",     "Water dynamic viscosity at 60 deg C"),
        ("rho",  "5G", RHO_WATER_5G, "kg/m3",    "Water density at 15 deg C"),
        ("cp",   "5G", CP_WATER_5G,  "J/(kg·K)", "Water specific heat at 15 deg C"),
        ("mu",   "5G", MU_WATER_5G,  "Pa·s",     "Water dynamic viscosity at 15 deg C"),
    ]
    for p, gen, val, unit, desc in fluid_params:
        rows.append([p, gen, val, unit, desc])

    # ------------------------------------------------------------------
    # 2. Soil and installation
    # ------------------------------------------------------------------
    section("SOIL AND INSTALLATION (EN 13941)")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    rows.append(["lambda_soil",  "-", LAMBDA_SOIL,  "W/(m·K)", "Soil thermal conductivity"])
    rows.append(["T_ground",     "-", T_GROUND,     "deg C",   "Undisturbed soil temperature"])
    rows.append(["burial_depth", "-", BURIAL_DEPTH, "m",       "Pipe axis depth from ground level"])

    # ------------------------------------------------------------------
    # 3. Steel carrier pipe material
    # ------------------------------------------------------------------
    section("STEEL CARRIER PIPE MATERIAL (P235GH, EN 10217-2)")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    rows.append(["lambda_steel",    "3G/4G", LAMBDA_STEEL,    "W/(m·K)", "Thermal conductivity"])
    rows.append(["roughness_steel", "3G/4G", ROUGHNESS_STEEL, "m",       "Absolute roughness (Darcy-Weisbach)"])
    rows.append(["E_steel",         "3G/4G", E_STEEL,         "Pa",      "Young's modulus"])
    rows.append(["alpha_steel",     "3G/4G", ALPHA_STEEL,     "1/K",     "Linear thermal expansion coefficient"])

    # ------------------------------------------------------------------
    # 4. Plastic pipe material
    # ------------------------------------------------------------------
    section("PLASTIC CARRIER PIPE MATERIAL (PEX/PERT/HDPE, EN ISO 15875)")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    rows.append(["lambda_pex",    "4G/5G", LAMBDA_PEX,    "W/(m·K)", "PEX thermal conductivity"])
    rows.append(["roughness_pex", "4G/5G", ROUGHNESS_PEX, "m",       "PEX absolute roughness"])
    rows.append(["lambda_hdpe",   "5G",    LAMBDA_HDPE,   "W/(m·K)", "HDPE casing thermal conductivity"])

    # ------------------------------------------------------------------
    # 5. PUR insulation
    # ------------------------------------------------------------------
    section("PUR FOAM INSULATION (EN 253:2019, series 1)")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    rows.append(["lambda_pur", "-", LAMBDA_PUR, "W/(m·K)",
                 "Aged design value at 50 deg C (EN 253 max = 0.033)"])

    # ------------------------------------------------------------------
    # 6. Pipe catalogue
    # ------------------------------------------------------------------
    section("PIPE CATALOGUE - EN 253:2019 SERIES 1 + EN 10220:2002")
    rows.append(["DN", "d_inner_m", "d_outer_m", "wall_thickness_m",
                 "d_casing_m", "d_inner_mm", "d_outer_mm", "d_casing_mm",
                 "source"])

    for dn, (di, do, s, dc) in sorted(PIPE_CATALOGUE.items()):
        rows.append([
            dn,
            di, do, s, dc,
            round(di * 1000, 2),   # mm for readability
            round(do * 1000, 2),
            round(dc * 1000, 2),
            "EN10220+EN253:2019 Tab.A.1 series 1",
        ])

    # ------------------------------------------------------------------
    # 7. Generation operating parameters
    # ------------------------------------------------------------------
    section("GENERATION OPERATING PARAMETERS (Table 1, paper_v2)")
    rows.append(["parameter", "generation", "value", "unit", "description"])

    param_meta = {
        "T_supply_nom" : ("deg C",  "Nominal supply temperature"),
        "delta_T_nom"  : ("K",      "Design temperature differential supply-return"),
        "P_nom_bar"    : ("bar",    "Nominal operating pressure"),
        "control_mode" : ("-",      "Control strategy"),
        "v_design"     : ("m/s",    "Design flow velocity (distribution mains)"),
        "v_max"        : ("m/s",    "Maximum allowable velocity (EN 13941)"),
        "carrier_mat"  : ("-",      "Carrier pipe material"),
        "rho"          : ("kg/m3",  "Water density at nominal temperature"),
        "cp"           : ("J/(kg·K)","Water specific heat at nominal temperature"),
        "mu"           : ("Pa·s",   "Water dynamic viscosity at nominal temperature"),
    }

    for gen, params in GEN_OPERATING.items():
        for key, val in params.items():
            unit, desc = param_meta.get(key, ("-", key))
            rows.append([key, gen, val, unit, desc])

    # ------------------------------------------------------------------
    # 8. DN by generation and grid level
    # ------------------------------------------------------------------
    section("ELIGIBLE DN BY GENERATION AND GRID LEVEL (Table 1, paper_v2)")
    rows.append(["generation", "grid_level", "DN_list", "unit", "description"])

    for gen, levels in DN_BY_GEN_LEVEL.items():
        for level, dn_list in levels.items():
            rows.append([
                gen,
                level,
                str(dn_list),   # e.g. "[20, 25, 32]"
                "mm",
                f"Eligible nominal diameters for {gen} {level} pipes",
            ])

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Exported: {OUTPUT_PATH}")
    print(f"  Rows written: {len(rows)}")


if __name__ == "__main__":
    main()