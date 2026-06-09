# constants.py

# Physical and engineering parameters for benchmark DHN networks.
#
# Reference standards:
# - EN 10220:2002 — Steel carrier pipe dimensions
# - EN 253:2019 — Pre-insulated pipes for underground district heating
# - EN 13941:2019 — Design and installation of pre-insulated pipes
#
# Symbols used in the code:
# d_i [m] Carrier pipe inner diameter
# d_o [m] Carrier pipe outer diameter
# s [m] Carrier pipe wall thickness
# d_casing [m] HDPE casing outer diameter



# ---------------------------------------------------------------------------
# 1. PROPERTIES OF WATER as a heat transfer fluid
# Values evaluated at nominal operating temperatures for generation
# ---------------------------------------------------------------------------

# 3GDH — water at ~80°C
RHO_WATER_3G = 971.8    # kg/m³   density
CP_WATER_3G  = 4195.0   # J/(kg·K) specific heat
MU_WATER_3G  = 3.54e-4  # Pa·s    dynamic viscosity

# 4GDH — water at ~60°C
RHO_WATER_4G = 983.2    # kg/m³
CP_WATER_4G  = 4181.0   # J/(kg·K)
MU_WATER_4G  = 4.67e-4  # Pa·s

# 5GDHC — water at ~15°C
RHO_WATER_5G = 999.1    # kg/m³
CP_WATER_5G  = 4186.0   # J/(kg·K)
MU_WATER_5G  = 1.14e-3  # Pa·s

# Generic alias
RHO_WATER = RHO_WATER_3G
CP_WATER  = CP_WATER_3G


# ---------------------------------------------------------------------------
# 2. SOIL AND INSTALLATION PARAMETERS (EN 13941, European standard conditions)
# ---------------------------------------------------------------------------

LAMBDA_SOIL  = 1.5    # W/(m·K)  soil thermal conductivity (medium moist soil)
T_GROUND     = 10.0   # °C       undisturbed soil temperature (Central Europe)
BURIAL_DEPTH = 0.8    # m        depth of pipe axis from ground level (EN 13941 §6)


# ---------------------------------------------------------------------------
# 3. STEEL SUPPORT TUBE MATERIALS
# P235GH steel according to EN 10217-2 / EN 10217-5 (EN 253 standard)
# ---------------------------------------------------------------------------

LAMBDA_STEEL    = 50.0      # W/(m·K)  thermal conductivity of carbon steel
ROUGHNESS_STEEL = 0.045e-3  # m        absolute roughness of commercial steel
E_STEEL         = 210e9     # Pa       Young's modulus
ALPHA_STEEL     = 1.2e-5    # 1/K      coefficient of linear thermal expansion


# ---------------------------------------------------------------------------
# 4. PLASTIC PIPE MATERIALS (carrier pipe for 4GDH and 5GDHC)
# PEX / PERT according to EN ISO 15875 and EN 13941
# ---------------------------------------------------------------------------

LAMBDA_PEX      = 0.38      # W/(m·K)
ROUGHNESS_PEX   = 0.007e-3  # m
LAMBDA_HDPE     = 0.42      # W/(m·K)  (HDPE PE100)


# ---------------------------------------------------------------------------
# 5. PUR FOAM INSULATION (EN 253:2019, series 1)
# λ₅₀ = conductivity at 50°C, aged design value
# ---------------------------------------------------------------------------

LAMBDA_PUR = 0.033  # W/(m K) (EN 253 §5.3: maximum permissible value = 0.033 W/(m K))
                    # Note: Real Logstor λ₅₀ ≈ 0.0241 W/(m K), but the conservative
                    # value of 0.033 is the standard design value.


# ---------------------------------------------------------------------------
# 6. PRE-INSULATED PIPES CATALOG - SERIES 1 (EN 253:2019)
#
# Structure: DN → (d_i [m], d_o [m], s [m], d_casing [m])
#
# Carrier pipe geometry source: EN 10220:2002 (steel diameters and thicknesses)
# d_o from ISO 4200 (OD column): 26.9, 33.7, 42.4, 48.3, 60.3, 76.1, 88.9,
#                                114.3, 139.7, 168.3, 219.1, 273.0, 323.9 mm
# s from EN 10220 minimum thickness standard series (PN16 DH service):
# DN20-DN32: 2.6mm; DN40-DN50: 2.9mm; DN65-DN80: 3.2mm;
# DN100: 3.6mm; DN125: 4.0mm; DN150: 4.5mm; DN200: 6.3mm;
# DN250: 6.3mm; DN300: 7.1mm
#
# Source d_casing: EN 253:2019 Table A.1, series 1 (insulation series 1)
# Values verified with Logstor catalog (2024) and ISOPLUS
#
# DN : (d_i [m], d_o [m], s [m], d_casing [m])
# ---------------------------------------------------------------------------

PIPE_CATALOGUE = {
    #  DN  :  d_inner     d_outer     wall       d_casing
    20  : (0.02140,   0.02690,   0.00260,   0.0900),
    25  : (0.02820,   0.03370,   0.00260,   0.0900),
    32  : (0.03680,   0.04240,   0.00260,   0.1100),
    40  : (0.04250,   0.04830,   0.00290,   0.1100),
    50  : (0.05450,   0.06030,   0.00290,   0.1250),
    65  : (0.07170,   0.07610,   0.00320,   0.1400),  # d_o = 76.1 mm (EN 10220)
    80  : (0.08250,   0.08890,   0.00320,   0.1600),
    100 : (0.10710,   0.11430,   0.00360,   0.2000),
    125 : (0.13290,   0.13970,   0.00400,   0.2250),
    150 : (0.15930,   0.16830,   0.00450,   0.2500),
    200 : (0.20660,   0.21910,   0.00630,   0.3150),
    250 : (0.26060,   0.27300,   0.00630,   0.4000),  # d_casing da EN 253 Tab.A.1
    300 : (0.30970,   0.32390,   0.00710,   0.4500),
}


# ---------------------------------------------------------------------------
# 7. OPERATIONAL PARAMETERS BY GENERATION
# ---------------------------------------------------------------------------

GEN_OPERATING = {
    "3G": {
        "T_supply_nom"  : 80.0,   # °C
        "delta_T_nom"   : 30.0,   # K
        "P_nom_bar"     : 10.0,   # bar (range 6–16 bar)
        "control_mode"  : "CF-VT",# constant mass flow, variable temperature
        "v_design"      :  1.0,   # m/s
        "v_max"         :  2.5,   # m/s (EN 13941 limit for noise and erosion)
        "carrier_mat"   : "steel",
        "rho"           : RHO_WATER_3G,
        "cp"            : CP_WATER_3G,
        "mu"            : MU_WATER_3G,
    },
    "4G": {
        "T_supply_nom"  : 60.0,
        "delta_T_nom"   : 20.0,   # K
        "P_nom_bar"     : 8.0,
        "control_mode"  : "VF-VT",# variable mass flow, variable temperature
        "v_design"      :  0.8,   # m/s
        "v_max"         :  2.0,   # m/s
        "carrier_mat"   : "steel_or_pex",
        "rho"           : RHO_WATER_4G,
        "cp"            : CP_WATER_4G,
        "mu"            : MU_WATER_4G,
    },
    "5G": {
        "T_supply_nom"  : 20.0,   # °C
        "delta_T_nom"   :  5.0,   # K
        "P_nom_bar"     :  6.0,
        "control_mode"  : "prosumer",
        "v_design"      :  0.6,   # m/s
        "v_max"         :  1.5,   # m/s
        "carrier_mat"   : "hdpe",
        "rho"           : RHO_WATER_5G,
        "cp"            : CP_WATER_5G,
        "mu"            : MU_WATER_5G,
    },
}


# ---------------------------------------------------------------------------
# 8. ELIGIBLE DN BY GENERATION AND GRID LEVEL
#
# Three levels: 'building' (connection, ref 10 kW)
#               'distribution' (distribution network, ref 500 kW)
#               'transmission' (backbone, ref 5 MW)
# ---------------------------------------------------------------------------

DN_BY_GEN_LEVEL = {
    "3G": {
        "building"     : [20],
        "distribution" : [40, 50, 65, 80, 100],
        "transmission" : [100, 125, 150, 200, 250, 300],
    },
    "4G": {
        "building"     : [20],
        "distribution" : [50, 65, 80, 100, 125],
        "transmission" : [125, 150, 200, 250],
    },
    "5G": {
        "building"     : [35],
        "distribution" : [80, 100, 125, 150, 200],
        "transmission" : [200, 250, 300],
    },
}