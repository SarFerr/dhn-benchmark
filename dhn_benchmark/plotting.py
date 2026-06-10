# plotting.py
#
# Standard plot function for DHN benchmark network topologies.
#
# Usage:
#   from dhn_benchmark.plotting import plot_topology
#   plot_topology(NODES, EDGES, title="DHN_THV_3G_R_S_BASE")

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Visual parameters
# ---------------------------------------------------------------------------
RADIUS = {
    "source"     : 10,
    "junction"   : 10,
    "substation" : 10,
}

EDGE_COLOR = "black"
EDGE_LW    = 1.0

NODE_STYLE = {
    # type       : (facecolor,  edgecolor, lw,  alpha)
    "source"     : ("blue",     "blue",    1.2,  1.0),
    "junction"   : ("black",    "black",   1.2,  1.0),
    "substation" : ("#CCCCFF",   "blue",   1.2,  1.0),
}


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------
def plot_topology(nodes, edges, title="DHN_Network",
                  label_offsets=None, ax=None, show=True):
    """
    Parameters
    ----------
    nodes         : list of (node_id, node_type, x, y)
    edges         : list of (from_id, to_id)
    title         : str
    label_offsets : dict  node_id -> (dx, dy, ha, va)  — optional
    ax            : existing matplotlib Axes             — optional
    show          : bool

    Returns
    -------
    fig, ax
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 7))
    else:
        fig = ax.get_figure()

    pos = {nid: (x, y) for nid, _, x, y in nodes}

    # --- edges ---
    for u, v in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [-y1, -y2],
                color=EDGE_COLOR, lw=EDGE_LW, zorder=2)

    # --- nodes ---
    for nid, ntype, x, y in nodes:
        r  = RADIUS[ntype]
        fc, ec, lw, alpha_face = NODE_STYLE[ntype]

        ax.add_patch(plt.Circle(
            (x, -y), radius=r,
            facecolor=fc, edgecolor=ec,
            linewidth=lw, zorder=3,
        ))

    # --- labels ---
    for nid, ntype, x, y in nodes:
        r = RADIUS[ntype]
        if label_offsets and nid in label_offsets:
            dx, dy, ha, va = label_offsets[nid]
        else:
            dx, dy, ha, va = r + 2, 5, "left", "center"
        ax.text(
            x + dx, -y + dy, nid,
            ha=ha, va=va,
            fontsize=10, color="black", zorder=5,
        )

    # --- formatting ---
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.set_aspect("equal")
    ax.autoscale()
    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax