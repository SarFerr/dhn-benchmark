"""
extract_results_DHN_THV_3G_R_S_BASE.py

Extracts simulation results from the OpenModelica .mat output file of
DHN_THV_3G_R_S_BASE and exports them as clean, unit-converted CSV files
ready for comparison against pandapipes.

Usage:
    python extract_results_DHN_THV_3G_R_S_BASE.py <path_to_mat_file>

Output (written next to the .mat file, in a subfolder "results_csv"):
    ets_results.csv        — per-substation: T_sup, T_ret [degC], Q [kW], m_flow [kg/s]
    pipe_results.csv       — per-pipe: Q_loss_sup/ret [kW], m_flow [kg/s], p_in/p_out [bar]
    plant_results.csv      — Q_flow [kW], m_flow [kg/s] from the central plant
"""

import sys
import os
import csv
from buildingspy.io.outputfile import Reader


# ---------------------------------------------------------------------------
# Configuration — substation and pipe names in the model
# ---------------------------------------------------------------------------
N_SUB = 10

PIPE_NAMES = [
    "pipe_src_a", "pipe_src_b", "pipe_a_c", "pipe_b_d",
    "pipe_a_sub1", "pipe_a_sub2",
    "pipe_b_sub3", "pipe_b_sub4",
    "pipe_c_sub5", "pipe_c_sub6", "pipe_c_sub7",
    "pipe_d_sub8", "pipe_d_sub9", "pipe_d_sub10",
]

T_K_TO_C = 273.15


def safe_values(reader, varName):
    """Return (time, values) for a variable, or (None, None) if not found."""
    try:
        t, v = reader.values(varName)
        return t, v
    except KeyError:
        print(f"  [WARN] Variable not found: {varName}")
        return None, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_results_DHN_THV_3G_R_S_BASE.py <path_to_mat_file>")
        sys.exit(1)

    mat_path = sys.argv[1]
    if not os.path.isfile(mat_path):
        print(f"File not found: {mat_path}")
        sys.exit(1)

    out_dir = os.path.join(os.path.dirname(mat_path), "results_csv")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Reading: {mat_path}")
    r = Reader(mat_path, "dymola")

    # Use simulation time vector from a variable guaranteed to exist
    time_ref, _ = safe_values(r, "src.Q_flow")
    if time_ref is None:
        print("Could not read reference time vector from src.Q_flow — aborting.")
        sys.exit(1)
    n_steps = len(time_ref)
    print(f"  Time vector: {n_steps} points, "
          f"{time_ref[0]:.0f}s to {time_ref[-1]:.0f}s")

    # -----------------------------------------------------------------
    # 1 — ETS results (10 substations)
    # -----------------------------------------------------------------
    print("\nExtracting ETS results...")
    ets_rows = []
    for i in range(1, N_SUB + 1):
        t, T_sup_K   = safe_values(r, f"ets[{i}].senT_disSup.T")
        _, T_ret_K   = safe_values(r, f"ets[{i}].senT_disRet.T")
        _, Q_flow_W  = safe_values(r, f"ets[{i}].QHea_flow")
        _, m_flow    = safe_values(r, f"ets[{i}].port_aSerHea.m_flow")

        if t is None:
            continue

        for k in range(len(t)):
            ets_rows.append({
                "time_s":     t[k],
                "substation": i,
                "T_sup_degC": T_sup_K[k] - T_K_TO_C if T_sup_K is not None else "",
                "T_ret_degC": T_ret_K[k] - T_K_TO_C if T_ret_K is not None else "",
                "Q_kW":       Q_flow_W[k] / 1000.0   if Q_flow_W is not None else "",
                "m_flow_kgs": abs(m_flow[k])         if m_flow   is not None else "",
            })

    ets_csv = os.path.join(out_dir, "ets_results.csv")
    with open(ets_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "time_s", "substation", "T_sup_degC", "T_ret_degC", "Q_kW", "m_flow_kgs"])
        w.writeheader()
        w.writerows(ets_rows)
    print(f"  → {ets_csv}  ({len(ets_rows)} rows)")

    # -----------------------------------------------------------------
    # 2 — Pipe results (14 pipes)
    # -----------------------------------------------------------------
    print("\nExtracting pipe results...")
    pipe_rows = []
    for name in PIPE_NAMES:
        t, Qloss_sup_W = safe_values(r, f"{name}.Q_loss_sup")
        _, Qloss_ret_W = safe_values(r, f"{name}.Q_loss_ret")
        _, m_flow      = safe_values(r, f"{name}.port_aDisSup.m_flow")
        _, p_in_Pa     = safe_values(r, f"{name}.port_aDisSup.p")
        _, p_out_Pa    = safe_values(r, f"{name}.port_bDisSup.p")

        if t is None:
            continue

        for k in range(len(t)):
            pipe_rows.append({
                "time_s":        t[k],
                "pipe_id":       name,
                "Q_loss_sup_kW": Qloss_sup_W[k] / 1000.0 if Qloss_sup_W is not None else "",
                "Q_loss_ret_kW": Qloss_ret_W[k] / 1000.0 if Qloss_ret_W is not None else "",
                "m_flow_kgs":    abs(m_flow[k])          if m_flow      is not None else "",
                "p_in_bar":      p_in_Pa[k] / 1e5         if p_in_Pa     is not None else "",
                "p_out_bar":     p_out_Pa[k] / 1e5        if p_out_Pa    is not None else "",
            })

    pipe_csv = os.path.join(out_dir, "pipe_results.csv")
    with open(pipe_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "time_s", "pipe_id", "Q_loss_sup_kW", "Q_loss_ret_kW",
            "m_flow_kgs", "p_in_bar", "p_out_bar"])
        w.writeheader()
        w.writerows(pipe_rows)
    print(f"  → {pipe_csv}  ({len(pipe_rows)} rows)")

    # -----------------------------------------------------------------
    # 3 — Plant results
    # -----------------------------------------------------------------
    print("\nExtracting plant results...")
    t, Q_flow_W = safe_values(r, "src.Q_flow")
    _, m_flow   = safe_values(r, "src.plaHea.m_flow")

    plant_rows = []
    for k in range(len(t)):
        plant_rows.append({
            "time_s":     t[k],
            "Q_kW":       Q_flow_W[k] / 1000.0 if Q_flow_W is not None else "",
            "m_flow_kgs": abs(m_flow[k])       if m_flow   is not None else "",
        })

    plant_csv = os.path.join(out_dir, "plant_results.csv")
    with open(plant_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["time_s", "Q_kW", "m_flow_kgs"])
        w.writeheader()
        w.writerows(plant_rows)
    print(f"  → {plant_csv}  ({len(plant_rows)} rows)")

    print(f"\nDone. All CSV files written to: {out_dir}")


if __name__ == "__main__":
    main()