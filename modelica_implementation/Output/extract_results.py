"""
extract_results.py — general post-processing for DHN benchmark archetypes.

How it works
------------
Each custom component exposes a variable name that is unique to its type.
The script scans the .mat file for these signatures and groups the matches
by instance name (the part of the variable name before the signature):

    DHNPipe                  -> "<name>.Q_loss_sup"     (any number of pipes,
                                  any naming scheme, anywhere in the model
                                  hierarchy, including inside arrays or
                                  sub-components)
    BuildingWithIndirectETS  -> "<name>.QHea_flow" AND "<name>.senT_disSup.T"
                                  together (QHea_flow alone is also produced
                                  by BuildingTimeSeries internally, so the
                                  combination disambiguates the ETS wrapper)
    PlantStation              -> "<name>.senT_ret.T"

Usage
-----
    python extract_results.py <path_to_mat_file> [--outdir <folder>]

Output (written to <outdir>, default: "results_csv/<archetype_name>/"):
    plant_results.csv   — one row per plant instance per timestep:
                           Q [kW], m_flow [kg/s], T_ret/T_sup [degC]
    pipe_results.csv    — one row per pipe instance per timestep:
                           Q_loss_sup/ret [kW], m_flow [kg/s], p_in/p_out [bar]
    ets_results.csv     — one row per substation instance per timestep:
                           T_sup, T_ret [degC], Q [kW], m_flow [kg/s]
"""

import sys
import os
import re
import csv
import argparse
from buildingspy.io.outputfile import Reader

T_K_TO_C = 273.15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_values(reader, varName):
    """Return (time, values) for a variable, or (None, None) if not found."""
    try:
        t, v = reader.values(varName)
        return t, v
    except KeyError:
        return None, None


def discover_instances(reader, signature_suffix):
    """
    Return a sorted list of instance names (the prefix before the given
    signature suffix) for every variable in the .mat file matching that
    suffix. Works for both scalar instances ("pipe_src_a.Q_loss_sup") and
    array instances ("ets[3].QHea_flow") since the regex simply strips the
    fixed suffix from the right.
    """
    pattern = re.escape(signature_suffix) + r"$"
    matches = reader.varNames(pattern)
    instances = sorted(set(n[: -len(signature_suffix)] for n in matches))
    return instances


def discover_pipes(reader):
    """DHNPipe instances, identified by the unique '.Q_loss_sup' output."""
    return discover_instances(reader, ".Q_loss_sup")


def discover_plants(reader):
    """PlantStation instances, identified by the unique '.senT_ret.T' sensor."""
    return discover_instances(reader, ".senT_ret.T")


def discover_ets(reader):
    """
    BuildingWithIndirectETS instances, identified by the combination of
    '.QHea_flow' and '.senT_disSup.T' (the district-side supply sensor we
    added specifically to this wrapper, disambiguating it from any other
    component that might also expose a QHea_flow-like signal).
    """
    qhea_instances = set(discover_instances(reader, ".QHea_flow"))
    tsup_instances = set(discover_instances(reader, ".senT_disSup.T"))
    return sorted(qhea_instances & tsup_instances)


# ---------------------------------------------------------------------------
# Extraction routines — one per component type
# ---------------------------------------------------------------------------
def extract_plants(reader, plant_names):
    rows = []
    for name in plant_names:
        t, Q_flow_W = safe_values(reader, f"{name}.Q_flow")
        _, m_flow   = safe_values(reader, f"{name}.plaHea.m_flow")
        _, T_ret_K  = safe_values(reader, f"{name}.senT_ret.T")
        _, T_sup_K  = safe_values(reader, f"{name}.senT_sup.T")

        if t is None:
            continue

        for k in range(len(t)):
            rows.append({
                "time_s":     t[k],
                "plant_id":   name,
                "Q_kW":       Q_flow_W[k] / 1000.0 if Q_flow_W is not None else "",
                "m_flow_kgs": abs(m_flow[k])       if m_flow   is not None else "",
                "T_ret_degC": T_ret_K[k] - T_K_TO_C if T_ret_K is not None else "",
                "T_sup_degC": T_sup_K[k] - T_K_TO_C if T_sup_K is not None else "",
            })
    return rows


def extract_pipes(reader, pipe_names):
    rows = []
    for name in pipe_names:
        t, Qloss_sup_W = safe_values(reader, f"{name}.Q_loss_sup")
        _, Qloss_ret_W = safe_values(reader, f"{name}.Q_loss_ret")
        _, m_flow      = safe_values(reader, f"{name}.port_aDisSup.m_flow")
        _, p_in_Pa     = safe_values(reader, f"{name}.port_aDisSup.p")
        _, p_out_Pa    = safe_values(reader, f"{name}.port_bDisSup.p")

        if t is None:
            continue

        for k in range(len(t)):
            rows.append({
                "time_s":        t[k],
                "pipe_id":       name,
                "Q_loss_sup_kW": Qloss_sup_W[k] / 1000.0 if Qloss_sup_W is not None else "",
                "Q_loss_ret_kW": Qloss_ret_W[k] / 1000.0 if Qloss_ret_W is not None else "",
                "m_flow_kgs":    abs(m_flow[k])          if m_flow      is not None else "",
                "p_in_bar":      p_in_Pa[k] / 1e5        if p_in_Pa     is not None else "",
                "p_out_bar":     p_out_Pa[k] / 1e5       if p_out_Pa    is not None else "",
            })
    return rows


def extract_ets(reader, ets_names):
    rows = []
    for name in ets_names:
        t, T_sup_K  = safe_values(reader, f"{name}.senT_disSup.T")
        _, T_ret_K  = safe_values(reader, f"{name}.senT_disRet.T")
        _, Q_flow_W = safe_values(reader, f"{name}.QHea_flow")
        _, m_flow   = safe_values(reader, f"{name}.port_aSerHea.m_flow")

        if t is None:
            continue

        for k in range(len(t)):
            rows.append({
                "time_s":        t[k],
                "substation_id": name,
                "T_sup_degC":    T_sup_K[k] - T_K_TO_C if T_sup_K  is not None else "",
                "T_ret_degC":    T_ret_K[k] - T_K_TO_C if T_ret_K  is not None else "",
                "Q_kW":          Q_flow_W[k] / 1000.0  if Q_flow_W is not None else "",
                "m_flow_kgs":    abs(m_flow[k])        if m_flow   is not None else "",
            })
    return rows


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------
def write_csv(rows, fieldnames, out_path):
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Universal post-processing for DHN benchmark archetypes. "
                     "Auto-detects an arbitrary number of plants, pipes and "
                     "substations directly from the .mat file contents.")
    parser.add_argument("mat_path", help="Path to the OpenModelica .mat result file")
    parser.add_argument("--outdir", default=None,
                         help="Output folder for CSV files "
                              "(default: results_csv/<archetype_name>/ next to the .mat file)")
    args = parser.parse_args()

    if not os.path.isfile(args.mat_path):
        print(f"File not found: {args.mat_path}")
        sys.exit(1)

    archetype_name = os.path.splitext(os.path.basename(args.mat_path))[0]
    archetype_name = re.sub(r"_res$", "", archetype_name)

    out_dir = args.outdir or os.path.join(
        os.path.dirname(args.mat_path), "results_csv", archetype_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Reading: {args.mat_path}")
    r = Reader(args.mat_path, "dymola")

    # -----------------------------------------------------------------
    # Auto-discovery — no assumption on instance count for any component
    # -----------------------------------------------------------------
    plant_names = discover_plants(r)
    pipe_names  = discover_pipes(r)
    ets_names   = discover_ets(r)

    print(f"  Detected {len(plant_names)} PlantStation instance(s): {plant_names}")
    print(f"  Detected {len(pipe_names)} DHNPipe instance(s): {pipe_names}")
    print(f"  Detected {len(ets_names)} ETS substation instance(s): {ets_names}")

    if not (plant_names or pipe_names or ets_names):
        print("  [WARN] No recognisable DHN_Benchmark components found in this .mat file.")

    # -----------------------------------------------------------------
    # Extraction + export
    # -----------------------------------------------------------------
    if plant_names:
        rows = extract_plants(r, plant_names)
        out_path = os.path.join(out_dir, "plant_results.csv")
        write_csv(rows, ["time_s", "plant_id", "Q_kW", "m_flow_kgs",
                          "T_ret_degC", "T_sup_degC"], out_path)
        print(f"  -> {out_path}  ({len(rows)} rows)")

    if pipe_names:
        rows = extract_pipes(r, pipe_names)
        out_path = os.path.join(out_dir, "pipe_results.csv")
        write_csv(rows, ["time_s", "pipe_id", "Q_loss_sup_kW", "Q_loss_ret_kW",
                          "m_flow_kgs", "p_in_bar", "p_out_bar"], out_path)
        print(f"  -> {out_path}  ({len(rows)} rows)")

    if ets_names:
        rows = extract_ets(r, ets_names)
        out_path = os.path.join(out_dir, "ets_results.csv")
        write_csv(rows, ["time_s", "substation_id", "T_sup_degC", "T_ret_degC",
                          "Q_kW", "m_flow_kgs"], out_path)
        print(f"  -> {out_path}  ({len(rows)} rows)")

    print(f"\nDone. All CSV files written to: {out_dir}")


if __name__ == "__main__":
    main()