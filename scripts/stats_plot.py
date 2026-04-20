import json
import sys
from pathlib import Path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"python {sys.argv[0]} <result file>")
        exit(1)

    stat_dir = Path(sys.argv[1])

    if not stat_dir.exists():
        pass

    if not stat_dir.is_dir():
        print("Path is not a directory")
        exit(1)

    all_data = dict()
    
    for entry in stat_dir.iterdir():
        topo = entry.name
        stat_file = entry.joinpath(f"{topo}.stats")
        if stat_file.exists():
            with open(stat_file, 'r') as fd:
                data = json.load(fd)

                nesting_ratio = []
                handover_reduction = []
                delays = []
    
                for gw, gw_data in data.items():
                    period = gw_data["period"]
                    nested = gw_data["nesting"]["nested"]
                    total = gw_data["nesting"]["total"]
                    nesting_ratio.append( nested / total)
                    delays.extend(gw_data["delays"])
                    handover_eff = total - nested / 2
                    handover_reduction.append(handover_eff / (period / 3600))

                all_data[topo] = {"nesting_ratio": nesting_ratio, "delays": delays, "reduction": handover_reduction}


    # symbols = ["x-", ".-", "o-", "^-"]

    import matplotlib.pyplot as plt
    import plot_utils as pu

    pu.latexify(nb_subplots_line=1, fig_width=7.15, fig_height=2.15)
    plt.rc('font', weight='heavy')
    # fig, axes = plt.subplots(ncols=3, layout='constrained', constrained_layout=True)

    from matplotlib import gridspec
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 3, wspace=.3)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
    ]
    
    FONTSIZE=12
    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis='both')
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.set_yticklabels([0, .25, .5, .75, 1], fontsize=FONTSIZE)
    for (idx, (topo, topo_data)) in enumerate(all_data.items()):
        # axes[0].ecdf(topo_data['nesting_ratio'], label=topo, complementary=True, color=pu.COLORS[idx+1])
        axes[0].ecdf(topo_data['nesting_ratio'], label=topo, color=pu.COLORS[idx+1])
        axes[2].ecdf(topo_data['delays'], label=topo, color=pu.COLORS[idx+1])
        axes[1].ecdf(topo_data['reduction'], label=topo,  color=pu.COLORS[idx+1])


    axes[0].set_xlabel("Nesting Ratio", fontsize=FONTSIZE+1)
    axes[0].set_ylabel("Gateways", fontsize=FONTSIZE+1)
    axes[0].set_xticks([0, .25, .5, .75, 1])
    axes[0].set_xticklabels([0, 25, 50, 75, 100], fontsize=FONTSIZE)

    axes[1].set_xlabel("Handovers/Hour", fontsize=FONTSIZE+1)
    axes[1].set_yticklabels([])
    # axes[1].set_xscale('log')
    axes[1].set_xticks([0, 25, 50, 75, 100, 125])
    
    axes[2].set_xlabel("Nesting Delay [s]")
    axes[2].set_ylabel("Handovers")
    axes[2].set_yticks([0, .25, .5, .75, 1])
    axes[2].set_yticklabels([])
    # axes[2].set_ylim([.25, 1])
    axes[2].set_xticks([0, 15, 30, 45, 60])

    
    topos = list(all_data.keys())
    fig.legend(topos, loc="outside upper center", fontsize=11, ncols=len(topos))
    gs.tight_layout(fig)
    # plt.tight_layout()
    # plt.subplots_adjust(wspace=0.4)
    pos0 = axes[0].get_position()
    pos1 = axes[1].get_position()
    pos2 = axes[1].get_position()
    # axes[0].set_position([pos0.x0, pos1.y0, pos1.width + .05, pos1.height])
    # axes[1].set_position([pos0.x1 + 0.08, pos1.y0, pos1.width, pos1.height])
    axes[1].set_position([pos0.x1 + 0.03, pos1.y0, pos1.width + .025, pos1.height])
    # axes[2].set_position([pos1.x1 + 0.07, pos2.y0, pos2.width, pos2.height])
    axes[2].set_position([pos1.x1 + 0.025, pos2.y0, pos2.width, pos2.height])
    plt.savefig("all_stats.pdf", bbox_inches="tight")
