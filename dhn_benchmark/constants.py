# constants.py
# Physical and engineering parameters for benchmark DHN networks.

# ---------------------------------------------------------------------------
# water properties
# ---------------------------------------------------------------------------
RHO_WATER    = 971.8   # kg/m³  density at 80°C  (3GDH)
RHO_WATER_4G = 983.2   # kg/m³  density at 60°C  (4GDH)
CP_WATER     = 4195.0  # J/(kg·K)  specific heat

# ---------------------------------------------------------------------------
# ground (standard European conditions, underground installation)
# ---------------------------------------------------------------------------
LAMBDA_SOIL  = 1.5     # W/(m·K)  thermal conductivity of the soil
T_GROUND     = 10.0    # °C       undisturbed soil temperature
BURIAL_DEPTH = 0.8     # m       depth of pipe axis from ground level

# ---------------------------------------------------------------------------
# steel carrier pipe
# ---------------------------------------------------------------------------
LAMBDA_STEEL   = 50.0     # W/(m·K)
ROUGHNESS_STEEL = 0.045e-3  # m  absolute roughness (commercial steel)

# ---------------------------------------------------------------------------
# polyurethane foam insulation (PUR, EN 253 series 1)
# ---------------------------------------------------------------------------
LAMBDA_PUR = 0.033  # W/(m·K)  at 50°C, aged project value