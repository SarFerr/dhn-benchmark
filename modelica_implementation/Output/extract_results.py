"""
extract_results.py
==================
Post-processing script for DHN benchmark archetypes.

Reads the OpenModelica simulation result file (.mat) and exports
a single Excel file with one sheet per variable:

    plant_Q_W          : thermal power from each plant [W]
    plant_m_flow_kgs   : mass flow rate from each plant [kg/s]
    plant_T_ret_degC   : return temperature at each plant [degC]
    plant_T_sup_degC   : supply temperature at each plant [degC]

    pipe_Q_loss_sup_W  : heat loss in supply pipe [W]
    pipe_Q_loss_ret_W  : heat loss in return pipe [W]
    pipe_m_flow_kgs    : mass flow rate in each pipe [kg/s]
    pipe_p_in_bar      : pressure at pipe inlet [bar]
    pipe_p_out_bar     : pressure at pipe outlet [bar]

    ets_T_sup_degC     : district supply temperature at each ETS [degC]
    ets_T_ret_degC     : district return temperature at each ETS [degC]
    ets_Q_W            : heating load at each ETS [W]
    ets_m_flow_kgs     : mass flow rate at each ETS [kg/s]

Works for ANY archetype — auto-detects any number of plants, pipes and ETS.
"""

import sys
import os
import re
import argparse
import openpyxl
from buildingspy.io.outputfile import Reader

# ===========================================================================
# DEFAULT PATHS
# ===========================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_ARCHETYPE = "DHN_THV_3G_R_S_BASE_res.mat"

DEFAULT_MAT_PATH = os.path.join(BASE_DIR, "Results", "DHN_THV_3G_R_S_BASE", FILE_ARCHETYPE)
DEFAULT_OUT_DIR  = os.path.join(BASE_DIR, "Results", "DHN_THV_3G_R_S_BASE")

# ===========================================================================
# UNIT CONVERSION
# ===========================================================================
T_K_TO_C  = 273.15
PA_TO_BAR = 1e5

# ===========================================================================
# SAFE VARIABLE READER
# ===========================================================================
def safe_values(reader, varName):
    """Return (time, values) or (None, None) if variable not found."""
    try:
        t, v = reader.values(varName)
        return t, v
    except KeyError:
        return None, None

# ===========================================================================
# AUTO-DISCOVERY
# ===========================================================================
def discover_instances(reader, signature_suffix):
    """Find all component instances by a unique variable signature."""
    pattern = re.escape(signature_suffix) + r"$"
    matches = reader.varNames(pattern)
    return sorted(set(n[: -len(signature_suffix)] for n in matches))

def discover_plants(reader):
    return discover_instances(reader, ".senT_ret.T")

def discover_pipes(reader):
    return discover_instances(reader, ".Q_loss_sup")

def discover_ets(reader):
    qhea = set(discover_instances(reader, ".QHea_flow"))
    tsup = set(discover_instances(reader, ".senT_disSup.T"))
    return sorted(qhea & tsup)

# ===========================================================================
# EXTRACTION — returns wide-format data
# variable_name -> {instance_name -> [values]}
# ===========================================================================
def extract_plants(reader, plant_names):
    time_vec = None
    data = {}
    for name in plant_names:
        t, Q_W     = safe_values(reader, f"{name}.Q_flow")
        _, m_flow  = safe_values(reader, f"{name}.plaHea.m_flow")
        _, T_ret_K = safe_values(reader, f"{name}.senT_ret.T")
        _, T_sup_K = safe_values(reader, f"{name}.senT_sup.T")
        if t is None:
            print(f"  [WARN] Plant '{name}': Q_flow not found, skipping.")
            continue
        if time_vec is None:
            time_vec = t
        data.setdefault("Q_W",        {})[name] = Q_W
        data.setdefault("m_flow_kgs", {})[name] = [abs(v) for v in m_flow]            if m_flow  is not None else None
        data.setdefault("T_ret_degC", {})[name] = [v - T_K_TO_C for v in T_ret_K]    if T_ret_K is not None else None
        data.setdefault("T_sup_degC", {})[name] = [v - T_K_TO_C for v in T_sup_K]    if T_sup_K is not None else None
    return time_vec, data

def extract_pipes(reader, pipe_names):
    time_vec = None
    data = {}
    for name in pipe_names:
        t, Qloss_sup = safe_values(reader, f"{name}.Q_loss_sup")
        _, Qloss_ret = safe_values(reader, f"{name}.Q_loss_ret")
        _, m_flow    = safe_values(reader, f"{name}.port_aDisSup.m_flow")
        _, p_in_Pa   = safe_values(reader, f"{name}.port_aDisSup.p")
        _, p_out_Pa  = safe_values(reader, f"{name}.port_bDisSup.p")
        if t is None:
            print(f"  [WARN] Pipe '{name}': Q_loss_sup not found, skipping.")
            continue
        if time_vec is None:
            time_vec = t
        data.setdefault("Q_loss_sup_W", {})[name] = Qloss_sup
        data.setdefault("Q_loss_ret_W", {})[name] = Qloss_ret
        data.setdefault("m_flow_kgs",   {})[name] = [abs(v) for v in m_flow]           if m_flow   is not None else None
        data.setdefault("p_in_bar",     {})[name] = [v / PA_TO_BAR for v in p_in_Pa]   if p_in_Pa  is not None else None
        data.setdefault("p_out_bar",    {})[name] = [v / PA_TO_BAR for v in p_out_Pa]  if p_out_Pa is not None else None
    return time_vec, data

def extract_ets(reader, ets_names):
    time_vec = None
    data = {}
    for name in ets_names:
        t, T_sup_K = safe_values(reader, f"{name}.senT_disSup.T")
        _, T_ret_K = safe_values(reader, f"{name}.senT_disRet.T")
        _, Q_W     = safe_values(reader, f"{name}.QHea_flow")
        _, m_flow  = safe_values(reader, f"{name}.port_aSerHea.m_flow")
        if t is None:
            print(f"  [WARN] ETS '{name}': senT_disSup.T not found, skipping.")
            continue
        if time_vec is None:
            time_vec = t
        data.setdefault("T_sup_degC", {})[name] = [v - T_K_TO_C for v in T_sup_K] if T_sup_K is not None else None
        data.setdefault("T_ret_degC", {})[name] = [v - T_K_TO_C for v in T_ret_K] if T_ret_K is not None else None
        data.setdefault("Q_W",        {})[name] = Q_W
        data.setdefault("m_flow_kgs", {})[name] = [abs(v) for v in m_flow]         if m_flow  is not None else None
    return time_vec, data

# ===========================================================================
# EXCEL EXPORT
# ===========================================================================
def write_excel(plant_time, plant_data, plant_names,
                pipe_time,  pipe_data,  pipe_names,
                ets_time,   ets_data,   ets_names,
                out_path):

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default empty sheet

    def add_sheet(sheet_name, time_vec, instance_dict, instance_names):
        ws = wb.create_sheet(title=sheet_name[:31])  # Excel max 31 chars
        ws.append(["time_s"] + instance_names)
        for k in range(len(time_vec)):
            row = [float(time_vec[k])]
            for name in instance_names:
                arr = instance_dict.get(name)
                row.append(float(arr[k]) if arr is not None else "")
            ws.append(row)

    for var, d in plant_data.items():
        add_sheet(f"plant_{var}", plant_time, d, plant_names)

    for var, d in pipe_data.items():
        add_sheet(f"pipe_{var}", pipe_time, d, pipe_names)

    for var, d in ets_data.items():
        add_sheet(f"ets_{var}", ets_time, d, ets_names)

    wb.save(out_path)
    print(f"\n  Excel saved: {out_path}")
    print(f"  Sheets ({len(wb.sheetnames)}): {wb.sheetnames}")

# ===========================================================================
# MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Post-processing for DHN benchmark archetypes.")
    parser.add_argument("mat_path", nargs="?", default=None,
                        help="Path to the .mat result file.")
    parser.add_argument("--outdir", default=None,
                        help="Output folder.")
    args = parser.parse_args()

    mat_path = args.mat_path or DEFAULT_MAT_PATH
    out_dir  = args.outdir   or DEFAULT_OUT_DIR

    if not os.path.isfile(mat_path):
        print(f"[ERROR] File not found: {mat_path}")
        print("  Check DEFAULT_MAT_PATH at the top of the script.")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    print(f"Reading: {mat_path}")
    r = Reader(mat_path, "dymola")

    plant_names = discover_plants(r)
    pipe_names  = discover_pipes(r)
    ets_names   = discover_ets(r)

    print(f"  Detected {len(plant_names)} PlantStation(s) : {plant_names}")
    print(f"  Detected {len(pipe_names)}  DHNPipe(s)      : {pipe_names}")
    print(f"  Detected {len(ets_names)}   ETS(s)          : {ets_names}")

    if not (plant_names or pipe_names or ets_names):
        print("  [WARN] No DHN_Benchmark components found.")
        sys.exit(0)

    plant_time, plant_data = extract_plants(r, plant_names) if plant_names else (None, {})
    pipe_time,  pipe_data  = extract_pipes(r,  pipe_names)  if pipe_names  else (None, {})
    ets_time,   ets_data   = extract_ets(r,    ets_names)   if ets_names   else (None, {})

    archetype_name = os.path.splitext(os.path.basename(mat_path))[0].replace("_res", "")
    excel_path = os.path.join(out_dir, f"{archetype_name}_results.xlsx")

    write_excel(
        plant_time, plant_data, plant_names,
        pipe_time,  pipe_data,  pipe_names,
        ets_time,   ets_data,   ets_names,
        excel_path
    )

    print(f"\nDone.")

if __name__ == "__main__":
    main()