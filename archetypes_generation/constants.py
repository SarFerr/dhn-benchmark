# constants.py
#
# Physical and engineering parameters for benchmark DHN networks.
#
# Reference standards:
# - EN 10220:2002 — Steel carrier pipe dimensions
# - EN 253:2019 — Pre-insulated pipes for underground district heating
# - EN 13941:2019 — Design and installation of pre-insulated pipes
#
# ---------------------------------------------------------------------------
# 1. WATER — heat transfer fluid
# ---------------------------------------------------------------------------
RHO_WATER_3G    = 971.8     # kg/m³   density at 80°C
CP_WATER_3G     = 4195.0    # J/(kg·K)
MU_WATER_3G     = 3.54e-4   # Pa·s
LAMBDA_WATER_3G = 0.670     # W/(m·K) thermal conductivity at 80°C

RHO_WATER_4G    = 983.2     # kg/m³   density at 60°C
CP_WATER_4G     = 4181.0    # J/(kg·K)
MU_WATER_4G     = 4.67e-4   # Pa·s
LAMBDA_WATER_4G = 0.654     # W/(m·K) at 60°C

RHO_WATER_5G    = 999.1     # kg/m³   density at 15°C
CP_WATER_5G     = 4186.0    # J/(kg·K)
MU_WATER_5G     = 1.14e-3   # Pa·s
LAMBDA_WATER_5G = 0.589     # W/(m·K) at 15°C

RHO_WATER = RHO_WATER_3G
CP_WATER  = CP_WATER_3G

# ---------------------------------------------------------------------------
# 2. SOIL — EN 13941, Central European standard conditions
# ---------------------------------------------------------------------------
RHO_SOIL     = 1800.0   # kg/m³
CP_SOIL      = 1500.0   # J/(kg·K)
LAMBDA_SOIL  = 1.5      # W/(m·K)
T_GROUND     = 10.0     # °C
BURIAL_DEPTH = 0.8      # m

# External heat transfer coefficient for buried pipes [W/(m²·K)]
# Approximated as lambda_soil / burial_depth (EN 13941 simplified)
H_EXT = LAMBDA_SOIL / BURIAL_DEPTH   # = 1.875 W/(m²·K)

# ---------------------------------------------------------------------------
# 3. STEEL carrier pipe — P235GH, EN 10217-2
# ---------------------------------------------------------------------------
RHO_STEEL       = 7850.0    # kg/m³
CP_STEEL        = 490.0     # J/(kg·K)
LAMBDA_STEEL    = 50.0      # W/(m·K)
ROUGHNESS_STEEL = 0.045     # mm
E_STEEL         = 210e9     # Pa
ALPHA_STEEL     = 1.2e-5    # 1/K

# ---------------------------------------------------------------------------
# 4. PUR foam insulation — EN 253:2019 series 1
# ---------------------------------------------------------------------------
RHO_PUR    = 60.0    # kg/m³  (EN 253: 55–80 kg/m³)
CP_PUR     = 1400.0  # J/(kg·K)
LAMBDA_PUR = 0.033   # W/(m·K) aged design value at 50°C (EN 253 §5.3 max)

# ---------------------------------------------------------------------------
# 5. HDPE casing — PE100, EN 253
# ---------------------------------------------------------------------------
RHO_HDPE    = 955.0   # kg/m³
CP_HDPE     = 2300.0  # J/(kg·K)
LAMBDA_HDPE = 0.42    # W/(m·K)

# ---------------------------------------------------------------------------
# 6. PEX/PERT plastic carrier pipe — EN ISO 15875, EN 13941
# ---------------------------------------------------------------------------
LAMBDA_PEX    = 0.38      # W/(m·K)
ROUGHNESS_PEX = 0.007e-3  # m

# ---------------------------------------------------------------------------
# 7. PRE-INSULATED PIPE CATALOGUE — EN 253:2019 series 1 + EN 10220:2002
# DN : (d_inner [m], d_outer [m], wall [m], d_casing [m], casing_wall [m])
PIPE_CATALOGUE = {
    20  : (0.02140, 0.02690, 0.00260, 0.0900, 0.0030),
    25  : (0.02820, 0.03370, 0.00260, 0.0900, 0.0030),
    32  : (0.03680, 0.04240, 0.00260, 0.1100, 0.0030),
    40  : (0.04250, 0.04830, 0.00290, 0.1100, 0.0030),
    50  : (0.05450, 0.06030, 0.00290, 0.1250, 0.0030),
    65  : (0.07170, 0.07610, 0.00320, 0.1400, 0.0030),
    80  : (0.08250, 0.08890, 0.00320, 0.1600, 0.0035),
    100 : (0.10710, 0.11430, 0.00360, 0.2000, 0.0035),
    125 : (0.13290, 0.13970, 0.00400, 0.2250, 0.0035),
    150 : (0.15930, 0.16830, 0.00450, 0.2500, 0.0035),
    200 : (0.20660, 0.21910, 0.00630, 0.3150, 0.0040),
    250 : (0.26060, 0.27300, 0.00630, 0.4000, 0.0040),
    300 : (0.30970, 0.32390, 0.00710, 0.4500, 0.0040),
    # --- extension for large mains (TO VERIFY against EN 10220 / EN 253 tables) ---
    350 : (0.33960, 0.35560, 0.00800, 0.5000, 0.0045),
    400 : (0.38880, 0.40640, 0.00880, 0.5600, 0.0045),
    450 : (0.43960, 0.45720, 0.00880, 0.6300, 0.0050),
    500 : (0.49120, 0.50800, 0.00880, 0.7100, 0.0050),
    600 : (0.59000, 0.61000, 0.01000, 0.8000, 0.0055),
    700 : (0.69100, 0.71100, 0.01000, 0.9000, 0.0060),
    800 : (0.78700, 0.81300, 0.01300, 1.0000, 0.0060),
}
# ---------------------------------------------------------------------------
# 8. OPERATIONAL PARAMETERS BY GENERATION
# ---------------------------------------------------------------------------
GEN_OPERATING = {
    "3G": {
        "T_supply_nom" : 80.0,
        "delta_T_nom"  : 30.0,
        "P_nom_bar"    : 10.0,
        "control_mode" : "VF-CT",
        "v_design"     : 1.0,
        "v_max"        : 2.5,
        "carrier_mat"  : "steel",
        "rho"          : RHO_WATER_3G,
        "cp"           : CP_WATER_3G,
        "mu"           : MU_WATER_3G,
        "lambda"       : LAMBDA_WATER_3G,
    },
    "4G": {
        "T_supply_nom" : 60.0,
        "delta_T_nom"  : 20.0,
        "P_nom_bar"    : 8.0,
        "control_mode" : "VF-CT",
        "v_design"     : 0.8,
        "v_max"        : 2.0,
        "carrier_mat"  : "steel",
        "rho"          : RHO_WATER_4G,
        "cp"           : CP_WATER_4G,
        "mu"           : MU_WATER_4G,
        "lambda"       : LAMBDA_WATER_4G,
    },
    "5G": {
        "T_supply_nom" : 20.0,
        "delta_T_nom"  : 5.0,
        "P_nom_bar"    : 6.0,
        "control_mode" : "prosumer",
        "v_design"     : 0.6,
        "v_max"        : 1.5,
        "carrier_mat"  : "PE100",
        "rho"          : RHO_WATER_5G,
        "cp"           : CP_WATER_5G,
        "mu"           : MU_WATER_5G,
        "lambda"       : LAMBDA_WATER_5G,
    },
}

# ---------------------------------------------------------------------------
# 9. PIPE SYSTEM BY GENERATION
#   3G : carbon steel, pre-insulated rigid PUR, HDPE jacket
#   4G : carbon steel (pre-insulated)  [PEX/PERT admissible, not used in TG-4]
#   5G : PE100 SDR11 carrier, non-insulated, direct burial (ground = thermal buffer)
# ---------------------------------------------------------------------------
RHO_PEX, CP_PEX = 940.0, 2300.0      # typical PE-X (TO VERIFY with manufacturer data)
SDR_PE100 = 11
PE100_OD_MM = [25, 32, 40, 50, 63, 75, 90, 110, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]

GEN_PIPE_SYSTEM = {
    "3G": {"carrier": "steel", "catalogue": "steel_en253", "roughness_mm": ROUGHNESS_STEEL,
           "carrier_rho": RHO_STEEL, "carrier_cp": CP_STEEL, "carrier_lambda": LAMBDA_STEEL,
           "insulation": "PUR", "casing": "HDPE"},
    "4G": {"carrier": "steel", "catalogue": "steel_en253", "roughness_mm": ROUGHNESS_STEEL,
           "carrier_rho": RHO_STEEL, "carrier_cp": CP_STEEL, "carrier_lambda": LAMBDA_STEEL,
           "insulation": "PUR", "casing": "HDPE"},
    "5G": {"carrier": "PE100", "catalogue": "pe100_sdr11", "roughness_mm": ROUGHNESS_PEX,
           "carrier_rho": RHO_HDPE, "carrier_cp": CP_HDPE, "carrier_lambda": LAMBDA_HDPE,
           "insulation": None, "casing": None},
}

# they refer to reference loads of 10 kW, 500 kW and 5 MW)
DN_TABLE1_REFERENCE = {
    "3G": {"building": (20, 20),  "distribution": (50, 65),   "transmission": (125, 150)},
    "4G": {"building": (20, 20),  "distribution": (65, 80),   "transmission": (150, 200)},
    "5G": {"building": (25, 40),  "distribution": (100, 200), "transmission": (250, 500)},
}
REFERENCE_LOADS_W = {"building": 10e3, "distribution": 500e3, "transmission": 5e6}
