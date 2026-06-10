# demand_profile.py
#
# Normalised heat demand profile for a single DHN substation.
# Resolution: 10 minutes (6 points per hour).
# Same profile applied uniformly to all substations in all archetypes.
#
# Profile structure.
#   - Morning peak:   amplitude 1.00 at 07:00
#   - Rise transient: switch-on (06:00) → peak (07:00), ~60 min
#   - Decay transient: peak (07:00) → steady state, ~60 min
#   - Steady state:   f = 0.35, from ~08:00 to 22:00
#   - Overnight shutdown: f = 0.00, from 22:00 to 06:00
#   - Same profile applied uniformly all 7 days
#
# Usage:
#   from dhn_benchmark.demand_profile import DAILY_SHAPE, WEEKLY_SHAPE, DT_MIN, N_DAY, N_WEEK


# ---------------------------------------------------------------------------
# Substation peak load
# ---------------------------------------------------------------------------
Q_PEAK_W = 175_000   # W  — nominal peak load per substation

# ---------------------------------------------------------------------------
# Time resolution
# ---------------------------------------------------------------------------
DT_MIN  = 10             # minutes per timestep
N_HOUR  = 60 // DT_MIN   # timesteps per hour = 6
N_DAY   = 24 * N_HOUR    # timesteps per day  = 144
N_WEEK  = 7  * N_DAY     # timesteps per week = 1008

# ---------------------------------------------------------------------------
# Profile shape parameters
# ---------------------------------------------------------------------------
F_PEAK   = 1.00
F_STEADY = 0.35
F_OFF    = 0.00

# ---------------------------------------------------------------------------
# Daily normalised profile — 144 values, f(t) ∈ [0, 1]
# ---------------------------------------------------------------------------
def _build_daily_shape():
    """
    Builds the 144-point daily normalised load profile.

    Time windows (in timestep indices, 1 step = 10 min):
      t   0– 35  →  h 00:00–05:50  : shutdown   f = 0.00
      t  36– 41  →  h 06:00–06:50  : rise ramp  f = 0.00 → 1.00 (linear, 6 steps)
      t  42– 47  →  h 07:00–07:50  : decay ramp f = 1.00 → 0.35 (linear, 6 steps)
      t  48–131  →  h 08:00–21:50  : steady     f = 0.35
      t 132–143  →  h 22:00–23:50  : shutdown   f = 0.00
    """

    shape = []
    for t in range(N_DAY):
        h_frac = t / N_HOUR   # fractional hour (0.0 .. 23.833)

        if h_frac < 6.0:
            # overnight shutdown
            f = F_OFF

        elif 6.0 <= h_frac < 7.0:
            # rise transient: linear ramp 0.00 → 1.00 over 60 min
            f = F_OFF + (F_PEAK - F_OFF) * (h_frac - 6.0) / 1.0

        elif 7.0 <= h_frac < 8.0:
            # decay transient: linear ramp 1.00 → 0.35 over 60 min
            f = F_PEAK + (F_STEADY - F_PEAK) * (h_frac - 7.0) / 1.0

        elif 8.0 <= h_frac < 22.0:
            # steady state
            f = F_STEADY

        else:
            # h >= 22: shutdown
            f = F_OFF

        shape.append(round(f, 4))

    return shape


DAILY_SHAPE = _build_daily_shape()

# ---------------------------------------------------------------------------
# Weekly profile — 1008 values (7 × daily, uniform)
# ---------------------------------------------------------------------------
WEEKLY_SHAPE = DAILY_SHAPE * 7

# ---------------------------------------------------------------------------
# Timestep metadata helpers
# ---------------------------------------------------------------------------
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def timestep_labels():
    """
    Returns a list of 1008 label strings: 'Mon 06:30', 'Mon 06:40', ...
    Useful for CSV export and plotting.
    """
    labels = []
    for d, day in enumerate(DAYS):
        for t in range(N_DAY):
            total_min = t * DT_MIN
            hh = total_min // 60
            mm = total_min % 60
            labels.append(f"{day} {hh:02d}:{mm:02d}")
    return labels

# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
assert len(DAILY_SHAPE)  == N_DAY,  f"Expected {N_DAY}, got {len(DAILY_SHAPE)}"
assert len(WEEKLY_SHAPE) == N_WEEK, f"Expected {N_WEEK}, got {len(WEEKLY_SHAPE)}"
assert max(DAILY_SHAPE)  == F_PEAK
assert DAILY_SHAPE[0]    == F_OFF   # midnight = shutdown
assert DAILY_SHAPE[42]   == F_PEAK  # t=42 → h=07:00 = peak