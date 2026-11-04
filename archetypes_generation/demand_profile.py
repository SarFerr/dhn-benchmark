# demand_profile.py
#
# Normalised heat demand profile for a single DHN substation.
# Resolution: 10 minutes.
#
# Profile structure.
#   - Morning peak:   amplitude 1.00 at 07:00
#   - Rise transient: switch-on (06:00) → peak (07:00), 60 min
#   - Decay transient: peak (07:00) → steady state, 60 min
#   - Steady state:   f = 0.35, from 08:00 to 22:00
#   - Overnight shutdown: f = 0.00, from 22:00 to 06:00
#
# Usage:
#   from archetypes_generation.demand_profile import DAILY_SHAPE, WEEKLY_SHAPE, DT_MIN, N_DAY, N_WEEK


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
    """

    shape = []
    for t in range(N_DAY):
        h_frac = t / N_HOUR

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
WEEKLY_DEMAND_W = [round(f * Q_PEAK_W, 1) for f in WEEKLY_SHAPE]

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
assert len(WEEKLY_DEMAND_W) == N_WEEK
assert max(WEEKLY_DEMAND_W) == Q_PEAK_W
assert max(DAILY_SHAPE)  == F_PEAK
assert DAILY_SHAPE[0]    == F_OFF   # midnight = shutdown
assert DAILY_SHAPE[42]   == F_PEAK  # t=42 → h=07:00 = peak

# ---------------------------------------------------------------------------
# CSV export — run once, shared across all archetypes
# ---------------------------------------------------------------------------
def export_csv(out_path="data/demand_profile.csv"):
    """
    Export the weekly demand profile to CSV.
    """
    import csv
    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    labels = timestep_labels()
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "timestep",
            "label",
            "f_normalised",
            "Q_W",
        ])
        for t in range(N_WEEK):
            w.writerow([
                t,
                labels[t],
                WEEKLY_SHAPE[t],
                WEEKLY_DEMAND_W[t],
            ])
    print(f"demand_profile.csv exported → {out_path}")
    print(f"  timesteps : {N_WEEK}  (Δt={DT_MIN} min, 7 days)")
    print(f"  Q_peak    : {Q_PEAK_W/1000:.0f} kW")


if __name__ == "__main__":
    export_csv()