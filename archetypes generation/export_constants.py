# export_constants.py
#
# Exports all physical and engineering parameters from constants.py
# to a single readable CSV file: data/parameters.csv
#
# Usage:  python export_constants.py
# Output: data/parameters.csv

import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dhn_benchmark.constants import (
    RHO_WATER_3G, CP_WATER_3G, MU_WATER_3G, LAMBDA_WATER_3G,
    RHO_WATER_4G, CP_WATER_4G, MU_WATER_4G, LAMBDA_WATER_4G,
    RHO_WATER_5G, CP_WATER_5G, MU_WATER_5G, LAMBDA_WATER_5G,
    RHO_SOIL, CP_SOIL, LAMBDA_SOIL, T_GROUND, BURIAL_DEPTH,
    RHO_STEEL, CP_STEEL, LAMBDA_STEEL, ROUGHNESS_STEEL, E_STEEL, ALPHA_STEEL,
    RHO_PUR, CP_PUR, LAMBDA_PUR,
    RHO_HDPE, CP_HDPE, LAMBDA_HDPE,
    LAMBDA_PEX, ROUGHNESS_PEX,
    PIPE_CATALOGUE, GEN_OPERATING, DN_BY_GEN_LEVEL,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "parameters.csv")
NCOLS = 8

def pad(row):
    r = list(row)
    while len(r) < NCOLS:
        r.append("")
    return r

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    rows = []

    def section(title):
        rows.append(pad([]))
        rows.append(pad(["###", title]))
        rows.append(pad([]))

    def hdr(*cols):
        rows.append(pad(list(cols)))

    # ------------------------------------------------------------------
    # 1. Water
    # ------------------------------------------------------------------
    section("1. WATER — heat transfer fluid")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("rho",    "3G", RHO_WATER_3G,    "kg/m3",    "Density at 80°C"),
        ("cp",     "3G", CP_WATER_3G,     "J/(kg·K)", "Specific heat at 80°C"),
        ("mu",     "3G", MU_WATER_3G,     "Pa·s",     "Dynamic viscosity at 80°C"),
        ("lambda", "3G", LAMBDA_WATER_3G, "W/(m·K)",  "Thermal conductivity at 80°C"),
        ("rho",    "4G", RHO_WATER_4G,    "kg/m3",    "Density at 60°C"),
        ("cp",     "4G", CP_WATER_4G,     "J/(kg·K)", "Specific heat at 60°C"),
        ("mu",     "4G", MU_WATER_4G,     "Pa·s",     "Dynamic viscosity at 60°C"),
        ("lambda", "4G", LAMBDA_WATER_4G, "W/(m·K)",  "Thermal conductivity at 60°C"),
        ("rho",    "5G", RHO_WATER_5G,    "kg/m3",    "Density at 15°C"),
        ("cp",     "5G", CP_WATER_5G,     "J/(kg·K)", "Specific heat at 15°C"),
        ("mu",     "5G", MU_WATER_5G,     "Pa·s",     "Dynamic viscosity at 15°C"),
        ("lambda", "5G", LAMBDA_WATER_5G, "W/(m·K)",  "Thermal conductivity at 15°C"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 2. Soil
    # ------------------------------------------------------------------
    section("2. SOIL — EN 13941, Central European standard conditions")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("rho",          "-", RHO_SOIL,     "kg/m3",   "Density"),
        ("cp",           "-", CP_SOIL,      "J/(kg·K)","Specific heat"),
        ("lambda",       "-", LAMBDA_SOIL,  "W/(m·K)", "Thermal conductivity"),
        ("T_ground",     "-", T_GROUND,     "°C",      "Undisturbed ground temperature"),
        ("burial_depth", "-", BURIAL_DEPTH, "m",       "Pipe axis depth from ground"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 3. Steel carrier pipe
    # ------------------------------------------------------------------
    section("3. STEEL carrier pipe — P235GH, EN 10217-2")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("rho",       "3G/4G", RHO_STEEL,       "kg/m3",   "Density"),
        ("cp",        "3G/4G", CP_STEEL,        "J/(kg·K)","Specific heat"),
        ("lambda",    "3G/4G", LAMBDA_STEEL,    "W/(m·K)", "Thermal conductivity"),
        ("roughness", "3G/4G", ROUGHNESS_STEEL, "m",       "Absolute roughness Darcy-Weisbach"),
        ("E",         "3G/4G", E_STEEL,         "Pa",      "Young's modulus"),
        ("alpha",     "3G/4G", ALPHA_STEEL,     "1/K",     "Linear thermal expansion coefficient"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 4. PUR insulation
    # ------------------------------------------------------------------
    section("4. PUR foam insulation — EN 253:2019 series 1")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("rho",    "-", RHO_PUR,    "kg/m3",   "Density (EN 253: 55–80 kg/m³)"),
        ("cp",     "-", CP_PUR,     "J/(kg·K)","Specific heat"),
        ("lambda", "-", LAMBDA_PUR, "W/(m·K)", "Thermal conductivity aged at 50°C (EN 253 max=0.033)"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 5. HDPE casing
    # ------------------------------------------------------------------
    section("5. HDPE casing — PE100, EN 253")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("rho",    "-", RHO_HDPE,    "kg/m3",   "Density"),
        ("cp",     "-", CP_HDPE,     "J/(kg·K)","Specific heat"),
        ("lambda", "-", LAMBDA_HDPE, "W/(m·K)", "Thermal conductivity"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 6. PEX/PERT plastic carrier pipe
    # ------------------------------------------------------------------
    section("6. PEX/PERT plastic carrier pipe — EN ISO 15875")
    hdr("parameter", "generation", "value", "unit", "description")
    for row in [
        ("lambda",    "4G/5G", LAMBDA_PEX,    "W/(m·K)", "Thermal conductivity"),
        ("roughness", "4G/5G", ROUGHNESS_PEX, "m",       "Absolute roughness"),
    ]:
        rows.append(pad(row))

    # ------------------------------------------------------------------
    # 7. Pipe catalogue
    # ------------------------------------------------------------------
    section("7. PIPE CATALOGUE — EN 253:2019 series 1 + EN 10220:2002")
    rows.append([
        "DN_mm", "d_inner_m", "d_outer_m", "wall_m",
        "d_casing_m", "d_inner_mm", "d_outer_mm", "d_casing_mm",
    ])
    for dn, (di, do, s, dc) in sorted(PIPE_CATALOGUE.items()):
        rows.append([
            dn, di, do, s, dc,
            round(di*1000, 2), round(do*1000, 2), round(dc*1000, 2),
        ])

    # ------------------------------------------------------------------
    # 8. Generation operating parameters
    # ------------------------------------------------------------------
    section("8. GENERATION OPERATING PARAMETERS — Table 1 paper_v2")
    hdr("parameter", "generation", "value", "unit", "description")
    param_meta = {
        "T_supply_nom" : ("°C",       "Nominal supply temperature"),
        "delta_T_nom"  : ("K",        "Design temperature differential"),
        "P_nom_bar"    : ("bar",      "Nominal operating pressure"),
        "control_mode" : ("-",        "Control strategy"),
        "v_design"     : ("m/s",      "Design flow velocity"),
        "v_max"        : ("m/s",      "Maximum allowable velocity EN 13941"),
        "carrier_mat"  : ("-",        "Carrier pipe material"),
        "rho"          : ("kg/m3",    "Water density at nominal T"),
        "cp"           : ("J/(kg·K)", "Water specific heat at nominal T"),
        "mu"           : ("Pa·s",     "Water dynamic viscosity at nominal T"),
        "lambda"       : ("W/(m·K)",  "Water thermal conductivity at nominal T"),
    }
    for gen, params in GEN_OPERATING.items():
        for key, val in params.items():
            unit, desc = param_meta.get(key, ("-", key))
            rows.append(pad([key, gen, val, unit, desc]))

    # ------------------------------------------------------------------
    # 9. DN by generation and grid level
    # ------------------------------------------------------------------
    section("9. ELIGIBLE DN BY GENERATION AND GRID LEVEL — Table 1 paper_v2")
    hdr("generation", "grid_level", "DN_list", "unit", "description")
    for gen, levels in DN_BY_GEN_LEVEL.items():
        for level, dn_list in levels.items():
            dn_str = str(dn_list[0]) if len(dn_list) == 1 \
                     else " | ".join(str(d) for d in dn_list)
            rows.append(pad([gen, level, dn_str, "mm",
                             f"Eligible DN for {gen} {level} pipes"]))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Exported: {OUTPUT_PATH}")
    print(f"  Rows: {len(rows)}  |  Columns: {NCOLS}")

if __name__ == "__main__":
    main()