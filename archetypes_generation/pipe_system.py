# pipe_system.py
#
#   3G, 4G : carbon steel carrier, rigid PUR insulation, HDPE casing (EN 253)
#   5G     : PE100 carrier, non-insulated, direct burial (ground = thermal buffer)
#

import math
import networkx as nx

from archetypes_generation.constants import (
    GEN_OPERATING, GEN_PIPE_SYSTEM, PIPE_CATALOGUE, PE100_OD_MM,
    LAMBDA_PUR, LAMBDA_HDPE, LAMBDA_SOIL, BURIAL_DEPTH, H_EXT, T_GROUND,
    RHO_PUR, CP_PUR, RHO_HDPE, CP_HDPE,
    DN_TABLE1_REFERENCE, REFERENCE_LOADS_W,
)


class PipeSizingError(ValueError):
    """Raised when no catalogue diameter keeps the velocity below v_max."""


# ---------------------------------------------------------------------------
# Catalogues  (entry = dict with DN, d_i, d_o, wall, d_casing, casing_wall)
# ---------------------------------------------------------------------------
def _steel_catalogue():
    out = []
    for dn, (di, do, s, dc, sc) in sorted(PIPE_CATALOGUE.items()):
        out.append(dict(DN=dn, d_i=di, d_o=do, wall=s, d_casing=dc, casing_wall=sc))
    return out


def _pe100_catalogue():
    """PE100 pipes, DN = outer diameter [mm]. SDR 11 up to OD 110, SDR 17 above
    (pressure class adequate for the 2-8 bar of 5GDHC). Wall = OD / SDR."""
    out = []
    for od in PE100_OD_MM:
        sdr = 11 if od <= 110 else 17
        wall = round(od / sdr, 1) / 1000.0
        do = od / 1000.0
        out.append(dict(DN=od, d_i=do - 2 * wall, d_o=do, wall=wall,
                        d_casing=do, casing_wall=0.0))      # no casing: casing = pipe
    return out


_CATALOGUES = {"steel_en253": _steel_catalogue(), "pe100_sdr11": _pe100_catalogue()}


def catalogue(gen):
    return _CATALOGUES[GEN_PIPE_SYSTEM[gen]["catalogue"]]


# ---------------------------------------------------------------------------
# Sizing: smallest DN with v <= v_lim (default v_max). NO silent fallback to the largest DN.
# ---------------------------------------------------------------------------
def select_dn(gen, Q_w, v_lim=None):
    """Smallest catalogue DN whose velocity at the design load Q_w does not exceed v_lim.

    v_lim : sizing velocity limit [m/s]; None = GEN_OPERATING[gen]["v_max"] (default).
            A lower value (e.g. a design velocity) gives larger diameters and lower
            specific pressure losses. It cannot exceed v_max.
    """
    gp = GEN_OPERATING[gen]
    v_lim = gp["v_max"] if v_lim is None else v_lim
    if v_lim > gp["v_max"]:
        raise ValueError(f"[{gen}] v_lim = {v_lim} m/s exceeds v_max = {gp['v_max']} m/s.")
    mdot = Q_w / (gp["cp"] * gp["delta_T_nom"])
    for e in catalogue(gen):
        v = mdot / (gp["rho"] * math.pi * e["d_i"] ** 2 / 4.0)
        if v <= v_lim:
            return dict(e, mdot=round(mdot, 4), velocity=round(v, 3))
    d_req = math.sqrt(4 * mdot / (math.pi * gp["rho"] * v_lim))
    raise PipeSizingError(
        f"[{gen}] Q = {Q_w/1e6:.2f} MW needs d_i >= {d_req*1000:.0f} mm "
        f"(v_lim = {v_lim} m/s); largest catalogue d_i = "
        f"{catalogue(gen)[-1]['d_i']*1000:.0f} mm. Extend the catalogue.")


# ---------------------------------------------------------------------------
# Heat loss
# ---------------------------------------------------------------------------
def u_linear(gen, e):
    """Linear heat-loss coefficient [W/(m K)] of a buried pipe."""
    sysd = GEN_PIPE_SYSTEM[gen]
    if sysd["insulation"] is None:                      # bare buried plastic pipe
        R_wall = math.log(e["d_o"] / e["d_i"]) / (2 * math.pi * sysd["carrier_lambda"])
        R_soil = math.log(2 * BURIAL_DEPTH / e["d_o"]) / (2 * math.pi * LAMBDA_SOIL)
        return round(1.0 / (R_wall + R_soil), 4)
    R_ins = math.log(e["d_casing"] / e["d_o"]) / (2 * math.pi * LAMBDA_PUR)
    R_soil = math.log(2 * BURIAL_DEPTH / e["d_casing"]) / (2 * math.pi * LAMBDA_SOIL)
    return round(1.0 / (R_ins + R_soil), 4)


# ---------------------------------------------------------------------------
# One record of pipes.csv (identical columns for every archetype)
# ---------------------------------------------------------------------------
def pipe_record(gen, e, from_node, to_node, length_m):
    gp, sysd = GEN_OPERATING[gen], GEN_PIPE_SYSTEM[gen]
    insulated = sysd["insulation"] is not None
    ins_t = round((e["d_casing"] - e["d_o"]) / 2 - e["casing_wall"], 5) if insulated else 0.0
    UL = u_linear(gen, e)
    return {
        "from_node": from_node, "to_node": to_node,
        "length_m": round(length_m, 2), "DN_mm": e["DN"],
        "d_inner_m": e["d_i"], "d_outer_m": e["d_o"], "wall_m": e["wall"],
        "insulation_thickness_m": ins_t,
        "casing_thickness_m": e["casing_wall"] if insulated else 0.0,
        "d_casing_m": e["d_casing"],
        "roughness_mm": sysd["roughness_mm"],
        "fluid_rho_kgm3": gp["rho"], "fluid_cp_JkgK": gp["cp"],
        "fluid_mu_Pas": gp["mu"], "fluid_lambda_WmK": gp["lambda"],
        "carrier_material": sysd["carrier"],
        "carrier_rho_kgm3": sysd["carrier_rho"], "carrier_cp_JkgK": sysd["carrier_cp"],
        "carrier_lambda_WmK": sysd["carrier_lambda"],
        "insulation_material": sysd["insulation"] or "none",
        "PUR_rho_kgm3": RHO_PUR if insulated else 0.0,
        "PUR_cp_JkgK": CP_PUR if insulated else 0.0,
        "PUR_lambda_WmK": LAMBDA_PUR if insulated else 0.0,
        "casing_material": sysd["casing"] or "none",
        "HDPE_rho_kgm3": RHO_HDPE if insulated else 0.0,
        "HDPE_cp_JkgK": CP_HDPE if insulated else 0.0,
        "HDPE_lambda_WmK": LAMBDA_HDPE if insulated else 0.0,
        "burial_depth_m": BURIAL_DEPTH, "soil_lambda_WmK": LAMBDA_SOIL,
        "T_ground_degC": T_GROUND, "h_ext_Wm2K": H_EXT,
        "U_linear_WmK": UL, "U_Wm2K": round(UL / (math.pi * e["d_o"]), 4),
    }


def write_pipes_csv(path, records):
    """records: dict pipe_id -> record dict. One writer for every script."""
    import csv
    first = next(iter(records.values()))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pipe_id"] + list(first.keys()))
        w.writeheader()
        for pid, d in records.items():
            w.writerow({"pipe_id": pid, **d})


# ---------------------------------------------------------------------------
# Orientation for downstream-load sizing (works for 1 or several sources)
# ---------------------------------------------------------------------------
def orient_from_sources(dhn, source_nodes):
    """Directed BFS forest rooted at the sources: every consumer is assigned to
    the source reached first, so loads are not all attributed to source 0."""
    G = nx.Graph(dhn)
    root = "__ROOT__"
    for g in source_nodes:
        G.add_edge(root, g)
    T = nx.bfs_tree(G, root)
    T.remove_node(root)
    return T


# ---------------------------------------------------------------------------
# Consistency test against Table 1 (reference loads 10 kW / 500 kW / 5 MW)
# ---------------------------------------------------------------------------
def check_table1_consistency(verbose=True):
    ok = True
    for gen in ("3G", "4G", "5G"):
        for level, Q in REFERENCE_LOADS_W.items():
            lo, hi = DN_TABLE1_REFERENCE[gen][level]
            try:
                dn = select_dn(gen, Q)["DN"]
                inside = lo <= dn <= hi
            except PipeSizingError:
                dn, inside = None, False
            ok &= inside
            if verbose:
                print(f"  {gen} {level:<13s} Q={Q/1e3:>6.0f} kW -> DN {dn}  "
                      f"(Table 1: {lo}-{hi})  {'OK' if inside else 'OUTSIDE'}")
    return ok
