# plotting.py
#
# Standard plot of DHN benchmark network topologies (topology.png of every archetype).
# Same style as the network layouts saved by results/archetype_results.ipynb (LAYOUT_STYLE):
# black pipes, blue square source, light-blue substations, magenta prosumers, black junctions.
#
# Usage:
#   from archetypes_generation.plotting import plot_topology
#   plot_topology(NODES, EDGES, title)
#
# Coordinates: Methodology I files have y pointing down (flip_y=True, default);
# Methodology II files have y pointing up (flip_y=False).
# Fonts come from matplotlib rcParams (no fontsize is set here).

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# ---------------------------------------------------------------------------
# Visual parameters — identical to LAYOUT_STYLE in archetype_results.ipynb
# Marker sizes [pt²] and line widths [pt] refer to the width at which the layouts are shown in
# the paper (DISPLAY_W_IN) and are scaled with the figure width, so that topology.png and the
# results layouts look the same at any size.
# ---------------------------------------------------------------------------
LAYOUT_STYLE = {
    "pipe":       "black",
    "source":     dict(fc="blue",    ec="blue",  s=3.0,  z=6, marker="s"),
    "prosumer":   dict(fc="#FF00FF", ec="blue",  s=1.0,  z=4, marker="o"),
    "substation": dict(fc="#CCCCFF", ec="blue",  s=1.0,  z=4, marker="o"),
    "junction":   dict(fc="black",   ec="black", s=0.25, z=3, marker="."),
}
PIPE_LW, EDGE_LW = 0.15, 0.10            # pipe width, marker outline width
DISPLAY_W_IN     = 0.74                  # width of the layouts in the paper [in]
MARGIN           = 0.06                  # relative margin around the network
LABEL_OFFSET     = (3, 3, "left", "bottom")   # label offset of the other nodes (dx, dy [pt], ha, va)


def _away_offset(p, q, d=5):
    """Label offset of an end node p, pointing away from its neighbour q."""
    vx, vy = p[0] - q[0], p[1] - q[1]
    if abs(vx) >= abs(vy):
        return (d, 0, "left", "center") if vx >= 0 else (-d, 0, "right", "center")
    return (0, d, "center", "bottom") if vy >= 0 else (0, -d, "center", "top")


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------
def plot_topology(nodes, edges, title="DHN_Network",
                  label_offsets=None, ax=None, show=True,
                  show_labels=True, show_junctions=True, flip_y=True, figsize=(7.0, 5.6)):
    """
    Parameters
    ----------
    nodes          : list of (node_id, node_type, x, y); node types not in LAYOUT_STYLE are
                     drawn as substations
    edges          : list of (from_id, to_id)
    title          : str (None or "" = no title)
    label_offsets  : dict node_id -> (dx, dy, ha, va), offsets in points — optional; by default
                     end nodes (substations) are labelled on the far side of their pipe and the
                     other nodes above-right
    ax             : existing matplotlib Axes — optional
    show           : bool
    show_labels    : write the node ids
    show_junctions : draw the junction markers
    flip_y         : True for coordinates with y pointing down (Methodology I)
    figsize        : figure size [in] when ax is None (same 3 : 2.4 aspect as the results layouts)

    Returns
    -------
    fig, ax
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    k = fig.get_size_inches()[0] / DISPLAY_W_IN       # scale factor: displayed size -> this figure

    sign  = -1.0 if flip_y else 1.0
    pos   = {nid: (float(x), sign * float(y)) for nid, _, x, y in nodes}
    ntype = {nid: (t if t in LAYOUT_STYLE else "substation") for nid, t, _, _ in nodes}

    # --- pipes ---
    ax.add_collection(LineCollection([(pos[u], pos[v]) for u, v in edges],
                                     colors=LAYOUT_STYLE["pipe"], linewidths=PIPE_LW * k,
                                     capstyle="round", zorder=2))

    # --- nodes ---
    for kind in ("junction", "substation", "prosumer", "source"):
        if kind == "junction" and not show_junctions:
            continue
        ids = [n for n, t in ntype.items() if t == kind]
        if ids:
            st = LAYOUT_STYLE[kind]
            ax.scatter([pos[n][0] for n in ids], [pos[n][1] for n in ids], s=st["s"] * k**2,
                       marker=st["marker"], facecolor=st["fc"], edgecolor=st["ec"],
                       linewidths=EDGE_LW * k, zorder=st["z"])

    # --- labels ---
    if show_labels:
        nbrs = {n: [] for n in pos}
        for u, v in edges:
            nbrs[u].append(v); nbrs[v].append(u)
        for nid in pos:
            if label_offsets and nid in label_offsets:
                dx, dy, ha, va = label_offsets[nid]
            elif len(nbrs[nid]) == 1:                 # end node: label on the far side of its pipe
                dx, dy, ha, va = _away_offset(pos[nid], pos[nbrs[nid][0]])
            else:
                dx, dy, ha, va = LABEL_OFFSET
            ax.annotate(nid, pos[nid], xytext=(dx, dy), textcoords="offset points",
                        ha=ha, va=va, color="black", zorder=7)

    # --- formatting ---
    if title:
        ax.set_title(title)
    ax.set_aspect("equal")
    ax.autoscale()
    ax.margins(MARGIN)
    ax.axis("off")
    fig.tight_layout()

    if show:
        plt.show()

    return fig, ax
