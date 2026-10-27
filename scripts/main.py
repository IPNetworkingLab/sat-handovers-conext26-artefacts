from pathlib import Path
import json
import sys

from pandas import DataFrame, concat
import matplotlib.pyplot as plt
from matplotlib import gridspec
import matplotlib
import plot_utils as pu
import seaborn as sb
import numpy as np

from sim import load_handovers_data


FONTSIZE=11
matplotlib.rcParams.update({'font.size': FONTSIZE})
ORDER = {
    "meo_small": "MEOs",
    "meo_large": "MEOl",
    "hleo": "HLEO",
    "iris2": "IRIS2",
    "scn": "SCN-288",
    "leo": "LEO",
    "starlink": "Starlink",
}
sizes = {"leo": 432, 'scn': 288, 'hleo': 288, 'meo_large': 128, 'meo_small': 72, 'iris2': 264, 'starlink': 1584}
METHODS = {
    "S": "Sequential",
    "NF": "Nested",
}
PALETTE = sb.color_palette("Paired")

def put_shade(ax, xs, color=True):
    for i in range(len(xs) - 1):
        if color:
            ax.axhspan(xs[i], xs[i + 1], facecolor="gray", alpha=0.1)
        color = not color

def load_stat_data(stat_file: Path) -> dict:
    with open(stat_file, 'r') as fd:
        data = json.load(fd)

    nesting_ratio = []
    handover_reduction = []
    delays = []
    totals = []
    durations = []
    all_handovers = []
    all_connectivity = []

    for gw, gw_data in data.items():
        period = gw_data["period"]
        period_hour = period / 3600
        nested = gw_data["nesting"]["nested"]
        total = gw_data["nesting"]["total"]
        totals.append(total / period_hour)
        durations.extend(gw_data["durations"])
        # durations.extend([d / 3600 for d in  gw_data["durations"]])
        nesting_ratio.append( nested / total)
        delays.extend(gw_data["delays"])
        handovers = nested / 2 
        all_handovers.append(handovers / period_hour)
        simple = total - nested
        connectivity_events = (simple + handovers)
        all_connectivity.append(connectivity_events / period_hour)
        # handover_reduction.append(handover_eff / (period / 3600))

    return {
        "nesting_ratio": nesting_ratio,
        "delays": delays,
        "reduction": handover_reduction,
        "totals": totals,
        "durations": durations,
        "ce": connectivity_events,
        "all_handovers": all_handovers,
        "all_connectivity": all_connectivity,
        "orbital_period": period
    }

def plot_motivation(data, result_dir):
    # pu.latexify(nb_subplots_line=1, fig_width=5.5, fig_height=2.25)
    pu.latexify(nb_subplots_line=1, fig_width=4, fig_height=1.95)
    # pu.latexify(nb_subplots_line=1, fig_width=4.675, fig_height=1.912)
    plt.rc('font', weight='heavy')
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 2, wspace=.1)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
    ]

    topos = list(data.keys())
    order = [i for i in ORDER if i in topos]

    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis='both')
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.set_yticklabels([0, .25, .5, .75, 1], fontsize=FONTSIZE)

    # for (idx, (topo, topo_data)) in enumerate(data.items()):
    for (idx, (topo, topo_data)) in enumerate([(topo, data[topo]) for topo in order]):
        axes[0].ecdf(topo_data['totals'], label=topo, color=PALETTE[idx])
        axes[1].ecdf(topo_data['durations'], label=topo, color=PALETTE[idx])

    axes[0].set_ylabel("Ground Stations", fontsize=FONTSIZE)
    axes[0].set_xlabel("Connectivity Events/\nHour", fontsize=FONTSIZE)
    axes[0].set_xticks([0, 250, 500])
    axes[0].set_xticklabels([0, 250, 500], fontsize=FONTSIZE)
    axes[1].set_yticklabels([])
    axes[1].set_ylabel("ECDF", fontsize=FONTSIZE)
    axes[1].set_xlabel("Feeder Link\nDuration [min]", fontsize=FONTSIZE)
    axes[1].set_xscale('log')
    axes[1].set_xticks([60, 600, 1800], )
    axes[1].set_xticklabels([1, 10, 30], fontsize=FONTSIZE)

    for ax in axes:
        linestyles = ["-", "--", ":", "-."]
        for line, ls in zip(ax.lines, linestyles):
            line.set_linestyle(ls)
    
    legend = fig.legend([ORDER[topo] for topo in order], loc="outside upper center", bbox_to_anchor=(.5, 1.07), fontsize=FONTSIZE-3, ncols=len(topos))
    handles = getattr(legend, "legend_handles", None) or legend.legendHandles  # matplotlib >= 3.7 / < 3.7
    for h, ls in zip(handles, linestyles):
        h.set_linestyle(ls)
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_color('white')
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square', pad=0.1)
    gs.tight_layout(fig)
    pos = [ax.get_position() for ax in axes]
    axes[0].set_position([pos[0].x0, pos[0].y0, pos[0].width, pos[0].height])
    axes[1].set_position([pos[0].x1 + 0.1, pos[1].y0, pos[1].width, pos[0].height])
    plt.savefig(f"{result_dir}/events_duration.pdf", bbox_inches="tight")

def plot_nesting(data, result_dir, nesting):
    # pu.latexify(nb_subplots_line=1, fig_width=4.9, fig_height=1.95)
    pu.latexify(nb_subplots_line=1, fig_width=8 if nesting else 4.9, fig_height=1.95)
    plt.rc('font', weight='heavy')
    # from matplotlib import gridspec
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 4 if nesting else 3, wspace=.1)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
    ]
    if nesting:
        axes.append(fig.add_subplot(gs[0, 3]))

    topos = list(data.keys())
    order = [i for i in ORDER if i in topos]
    
    FONTSIZE=12
    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis='both')
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.set_yticklabels([0, .25, .5, .75, 1], fontsize=FONTSIZE)
    # for (idx, (topo, topo_data)) in enumerate(data.items()):
    for (idx, (topo, topo_data)) in enumerate([(topo, data[topo]) for topo in order]):
        # axes[0].ecdf(topo_data['nesting_ratio'], label=topo, complementary=True, color=PALETTE[idx])
        axes[0].ecdf(topo_data['nesting_ratio'], label=topo, color=PALETTE[idx])
        axes[1].ecdf(topo_data['all_handovers'], label=topo,  color=PALETTE[idx])
        axes[2].ecdf(topo_data['all_connectivity'], label=topo,  color=PALETTE[idx])
        if nesting:
            axes[3].ecdf(topo_data['delays'], label=topo, color=PALETTE[idx])


    axes[0].set_xlabel("Nesting Ratio", fontsize=FONTSIZE)
    # axes[0].set_ylabel("Ground Stations", fontsize=FONTSIZE)
    axes[0].set_xticks([0, .25, .50, .75, 1])
    axes[0].set_xticklabels([0, 25, 50, 75, 100], fontsize=FONTSIZE)

    axes[1].set_xlabel("Handovers/Hour", fontsize=FONTSIZE)
    axes[1].set_yticklabels([])
    # axes[1].set_xscale('log')
    axes[1].set_xticks([0, 75, 150, 225, 300])
    axes[1].set_xticklabels([0, 75, 150, 225, 300], rotation=45, fontsize=FONTSIZE)
    # axes[1].set_xticks([0, 125, 250])
    # axes[1].set_xticklabels([0, 125, 250], fontsize=FONTSIZE)

    axes[2].set_xlabel("Conv./Hour", fontsize=FONTSIZE)
    axes[2].set_yticklabels([])
    # axes[1].set_xscale('log')
    # axes[2].set_xticks([0, 25, 50, 75, 100, 125, 150])
    # axes[2].set_xticklabels([0, 25, 50, 75, 100, 125, 150], rotation=45, fontsize=FONTSIZE)
    axes[2].set_xlim([0, 500])
    axes[2].set_xticks([0, 125, 250, 375, 500])
    axes[2].set_xticklabels([0, 125, 250, 375, 500], rotation=45, fontsize=FONTSIZE)
    # axes[2].set_xticklabels([0, 200, 400], fontsize=FONTSIZE)
    
    if nesting:
        axes[3].set_xlabel("Nesting Delay [s]", fontsize=FONTSIZE)
        axes[3].set_ylabel("Handovers", fontsize=FONTSIZE)
        axes[3].set_yticks([0, .25, .5, .75, 1])
        axes[3].set_yticklabels([])
        # axes[2].set_ylim([.25, 1])
        axes[3].set_xticks([0, 15, 30, 45, 60])
        axes[3].set_xticklabels([0, 15, 30, 45, 60], fontsize=FONTSIZE)

    for ax in axes:
        linestyles = ["-", "--", ":", "-."]
        for line, ls in zip(ax.lines, linestyles):
            line.set_linestyle(ls)
    
    legend = fig.legend([ORDER[topo] for topo in order], loc="outside upper center", bbox_to_anchor=(.45, 1.07), fontsize=FONTSIZE-3, ncols=len(topos))
    handles = getattr(legend, "legend_handles", None) or legend.legendHandles  # matplotlib >= 3.7 / < 3.7
    for h, ls in zip(handles, linestyles):
        h.set_linestyle(ls)
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_color('white')
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square', pad=0.1)
    gs.tight_layout(fig)
    # plt.tight_layout()
    # plt.subplots_adjust(wspace=0.4)
    pos = [ax.get_position() for ax in axes]
    axes[1].set_position([pos[0].x1 + 0.035, pos[1].y0, pos[1].width, pos[1].height])
    pos = [ax.get_position() for ax in axes]
    axes[2].set_position([pos[1].x1 + 0.035, pos[2].y0, pos[2].width, pos[2].height])
    pos = [ax.get_position() for ax in axes]
    if nesting:
        axes[3].set_position([pos[2].x1 + 0.05 , pos[3].y0, pos[3].width, pos[3].height])
    plt.savefig(f"{result_dir}/nesting.pdf", bbox_inches="tight")

def plot_sims(data: DataFrame, result_dir, orbital_periods):
    FONTSIZE2=FONTSIZE+7

    pu.latexify(nb_subplots_line=1, fig_width=13, fig_height=3)
    plt.rc('font', weight='heavy')
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 5, wspace=.2)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[0, 3]),
        fig.add_subplot(gs[0, 4]),
    ]

    order = [i for i in ORDER if i in data["topo"].unique()]
    print(order)

    # plot1 = sb.violinplot(
    plot1 = sb.barplot(
        data,
        y="topo",
        x="cfut",
        hue="method", hue_order=METHODS.keys(),
        order=order,
        ax=axes[0],
        # cut=0,
        # density_norm="width",
        # palette=PALETTE[1:],
        # inner='quart'
        palette=PALETTE,
        estimator='median',
        errorbar='pi'
    )
    plot1.legend_.remove()
    # axes[0].set_ylabel("Topology", fontsize=FONTSIZE2)
    axes[0].set_ylabel("")
    axes[0].set_xlabel("Duration [ms]", fontsize=FONTSIZE2)
    #axes[0].set_xscale("log")
    #axes[0].set_xlim([100, 10000])
    axes[0].set_xticks([0, 250, 500, 750])
    axes[0].set_xticklabels([0, 250, 500, 750], fontsize=FONTSIZE2)
    # axes[0].set_xticklabels([100, 200, 300, 400, 500, 600, 700])
    # axes[0].set_xticks([100, 200, 300, 400, 500, 600, 700])
    # axes[0].set_xticklabels([100, 200, 300, 400, 500, 600, 700])
    axes[0].set_yticks([i for i, _ in enumerate(order)])
    axes[0].set_yticklabels([ORDER[i] for i in order])
    # for i, container in enumerate(axes[0].containers):
        # axes[0].bar_label(container, fmt='%.0f%%', label_type='center', fontsize=5, color='black')
        
    data['normalized_nfib'] = (data['n_fib'] / data['topo'].map(sizes) - 1)
    plot2 = sb.violinplot(data, y="topo", x="normalized_nfib", hue="method", hue_order=METHODS.keys(), order=order, ax=axes[1], cut=0, density_norm="width", inner="quart", palette=PALETTE)
    # plot2 = sb.barplot(data, y="topo", x="normalized_nfib", hue="method", hue_order=METHODS.keys(), order=order, ax=axes[1], palette=PALETTE, estimator='median', errorbar='pi')
    plot2.legend_.remove()

    data['normalized_messages'] = ((data['n_upd'] + data['confs']) / data['topo'].map(sizes))
    # plot3 = sb.violinplot(data, y="topo", x="normalized_messages", hue="method", order=order, ax=axes[2], cut=0,  density_norm="width", inner='quart',   native_scale=True )
    plot3 = sb.barplot(data, y="topo", x="normalized_messages", hue="method",  hue_order=METHODS.keys(), order=order, ax=axes[2], palette=PALETTE, estimator='median', errorbar='pi')
    plot3.legend_.remove()

    data['sync_overhead'] = data['confs'] / (data['n_upd'] + data['confs'])
    # plot4 = sb.violinplot(data, y="topo", x="sync_overhead", hue="method", order=order, ax=axes[3], cut=0,  density_norm="width", inner='quart',  )
    plot4 = sb.barplot(data, y="topo", x="sync_overhead", hue="method", hue_order=METHODS.keys(), order=order, ax=axes[3], palette=PALETTE, estimator='median', errorbar='pi')
    plot4.legend_.remove()

    data['orbital_period'] = data['topo'].map(orbital_periods) * 1000
    g = data.groupby(['topo', 'method', 'orbital_period']).agg(total_cfut=('cfut', 'sum'), orbital_period=('orbital_period', 'first'), topo=('topo', 'first'), method=("method", 'first')).assign(convergence_proportion=lambda x: x['total_cfut'] / x['orbital_period'])
    plot5 = sb.barplot(g, y="topo", x="convergence_proportion", hue="method", hue_order=METHODS.keys(), order=order, ax=axes[4], palette=PALETTE, estimator='median', errorbar='pi')
    plot5.legend_.remove()
    
    axes[1].set_xlabel('FIB Updates\nOverhead [\%]', fontsize=FONTSIZE2)
    axes[1].set_xlim([-.2, .05])
    overhead_range = [-.2, -.15, -.10, -.05, 0, .05]
    axes[1].set_xticks(overhead_range)
    axes[1].set_xticklabels([int(i*100) for i in overhead_range], fontsize=FONTSIZE2)
    # axes[1].set_xticklabels([0, 0.3])
    axes[2].set_xlabel('Message / Sat', fontsize=FONTSIZE2)
    axes[2].set_xticks([0, 1, 2, 3, 4])
    # for i, container in enumerate(axes[2].containers):
        # axes[2].bar_label(container, fmt='%.3f%%', label_type='center', fontsize=5, color='black')
    axes[3].set_xlabel('Sync. Overhead', fontsize=FONTSIZE2)
    axes[3].set_xticks([0, .1, .2, .3, .4])
    # for i, container in enumerate(axes[3].containers):
        # axes[3].bar_label(container, fmt='%.4f%%', label_type='edge', fontsize=5, color='black')
    axes[4].set_xlabel('Cumulated Conv.\nProportion', fontsize=FONTSIZE2)
    axes[4].set_xscale("log")
    axes[4].set_xlim([0.001, 1])
    # axes[4].set_xticks([0.01, 0.1, 1, 10])
    # axes[4].set_xticklabels([0.01, 0.1, 1, 10], fontsize=FONTSIZE2)
    axes[4].get_xaxis().set_major_locator(matplotlib.ticker.LogLocator(base=10, numticks=15))
    # for i, container in enumerate(axes[4].containers):
        # axes[4].bar_label(container, fmt='%.4f%%', label_type='center', fontsize=5, color='black')


    for (idx, ax) in enumerate(axes):
        put_shade(ax, xs = [0.5 + i for i in range(0, len(order))])
        ax.set_axisbelow(True)
        ax.grid(axis='x')
        if idx != 0:
            ax.set_yticklabels([])
            ax.set_ylabel("")

    h, l = axes[0].get_legend_handles_labels()
    legend = fig.legend(
        handles=h,
        labels=[METHODS[i] for i in l],
        bbox_to_anchor=(0.95, 1.15),
        ncols=len(data["method"]),
    )
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_color('white')
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square', pad=0.1)
    gs.tight_layout(fig)
        
    # pos = [ax.get_position() for ax in axes]
    # axes[0].set_position([pos[0].x0, pos[0].y0, pos[0].width + .035, pos[0].height])
    # axes[1].set_position([pos[0].x1 + 0.05, pos[1].y0, pos[1].width, pos[0].height])
    # axes[2].set_position([pos[1].x1 + .035 , pos[2].y0, pos[2].width - .035, pos[2].height])
    plt.savefig(f"{result_dir}/convergence.pdf", bbox_inches="tight")

def plot_loops(data, result_dir):
    pu.latexify(nb_subplots_line=1, fig_width=2.5, fig_height=1.95)
    plt.rc('font', weight='heavy')

    gs = gridspec.GridSpec(1, 1)
    fig = plt.figure()
    ax = fig.add_subplot(gs[0, 0])
    ax.set_axisbelow(True)
    ax.grid(axis='both')
    order = [i for i in ORDER if i in data["topo"].unique()]
    plot = sb.ecdfplot(data, x="loops", hue="topo", hue_order=order, ax=ax, palette=PALETTE,)
    # h, l = ax.get_legend_handles_labels()
    h, l = ax.get_legend().legend_handles, [t.get_text() for t in ax.get_legend().get_texts()]
    plot.legend_.remove()
    # legend = fig.legend(handles=h, labels=[ORDER[i] for i in l], loc="outside upper center", bbox_to_anchor=(.5, 1.07), fontsize=FONTSIZE-3, ncols=len(order))
    ax.tick_params(axis="both", which="major", labelsize=FONTSIZE)
    ax.tick_params(axis="both", which="minor", labelsize=FONTSIZE)
    ax.set_xlabel('Loops', fontsize=FONTSIZE)
    # ax.set_xlim([0, 50])
    ax.set_ylabel('', fontsize=FONTSIZE)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_yticklabels([0, .25, .5, .75, 1], fontsize=FONTSIZE)
    ax.set_xscale("log")
    ax.set_xlim([0, 1000])
    # ax.set_xticks([0, 1, 10, 100, 1000])
    # ax.set_xticklabels([0, 1, 10, 100, 1000], fontsize=FONTSIZE)
    linestyles = ["-", "--", ":", "-."]
    for line, ls in zip(ax.lines[::-1], linestyles):
        line.set_linestyle(ls)
    legend = fig.legend(handles=h, labels=[ORDER[i] for i in l], loc="outside upper center", bbox_to_anchor=(.55, 1.15), fontsize=FONTSIZE-3, ncols=2)
    handles = getattr(legend, "legend_handles", None) or legend.legendHandles  # matplotlib >= 3.7 / < 3.7
    for h, ls in zip(handles, linestyles):
        h.set_linestyle(ls)
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_color('white')
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square', pad=0.1)
    gs.tight_layout(fig)
    plt.savefig(f"{result_dir}/loops.pdf", bbox_inches="tight")

def plot_handover_interval(data: DataFrame, stats: DataFrame, output_dir, orbital_periods):

    # Build spread dataframe
    spread = data.loc[data['method'] == 'NF', ['topo', 'cfut']].groupby('topo').agg(handover_mean=('cfut', 'mean'), handover_median=('cfut', 'median')).assign(orbital_period=orbital_periods)
    print(spread.to_string())

    feeder_mean = {}
    feeder_median = {}
    for topo, topodat in stats.items():
        feeder_mean[topo] = np.mean(topodat['durations'])
        feeder_median[topo] = np.median(topodat['durations'])
    spread['feeder_median'] = feeder_median
    spread['feeder_mean'] = feeder_mean
    spread['nconv_median'] = spread['feeder_median']*1000 / spread['handover_median']
    spread['nconv_mean'] = spread['feeder_mean']*1000 / spread['handover_mean']
    spread = spread.explode(list(spread.columns)).reset_index()

    print(spread.to_string())

    # print(spread['nconv_median'].explode().reset_index())
    
    def spread_window(data, spread):
        spread = spread[spread['topo'] == data.name].reset_index()
        print(spread)
        t = 0
        hspread = {}
        nconvm = int(spread['nconv_median'].loc[0])
        orbital_period = int(spread['orbital_period'].loc[0])
        feeder_median = spread['feeder_median'].loc[0]
        data = list(data)
        while t < orbital_period:
            start = t
            end = start + feeder_median
            nconv = len([i for i in data if start <= i < end])
            hspread[t] = nconv / nconvm
            t += 1

        return hspread

    def count_sim(diff):
        s = []
        z = 1
        for i in diff:
            if i == 0:
                z += 1
            elif z != 1:
                s.append(z)
                z = 1
        if z != 1:
            s.append(z)
        return s

    pu.latexify(nb_subplots_line=1, fig_width=2.5, fig_height=1.95)
    plt.rc('font', weight='heavy')
    gs = gridspec.GridSpec(1, 1)
    fig = plt.figure()
    ax = fig.add_subplot(gs[0, 0])
    ax.set_axisbelow(True)
    ax.grid(axis='both')
    order = [i for i in ORDER if i in data["topo"].unique()]

    d = data.loc[data['method'] == 'NF', ['topo', 'ts']]
    d = d.sort_values(['topo', 'ts']).reset_index(drop=True)
    a = data.groupby('topo')['ts'].apply(spread_window, spread).rename('spread').explode().reset_index()
    a = a.rename(columns={'level_1': 't'})
    print(a.columns)

    
    # all_ts = d.groupby('topo')['ts'].apply(list).to_dict()
    # import json
    # with open("ts.json", 'w') as fd:
    #     json.dump(all_ts, fd)
    d['dts'] = d.groupby('topo')['ts'].diff()

    c = d.groupby('topo')['dts'].apply(count_sim).explode().reset_index()

    # plot = sb.ecdfplot(c, x="dts", hue="topo", hue_order=order, ax=ax, palette=PALETTE,)
    # plot = sb.lineplot(a, x='t', y="spread", hue="topo", hue_order=order, ax=ax, palette=PALETTE,)
    plot = sb.ecdfplot(a, x="spread", hue="topo", hue_order=order, ax=ax, palette=PALETTE,)
    # h, l = ax.get_legend_handles_labels()
    h, l = ax.get_legend().legend_handles, [t.get_text() for t in ax.get_legend().get_texts()]
    plot.legend_.remove()
    # legend = fig.legend(handles=h, labels=[ORDER[i] for i in l], loc="outside upper center", bbox_to_anchor=(.5, 1.07), fontsize=FONTSIZE-3, ncols=len(order))
    # ax.set_xlabel('Ground Station Handover\nInterval [s]', fontsize=FONTSIZE)
    # ax.set_xlabel('Simultaneous Handovers', fontsize=FONTSIZE)
    # ax.set_xlabel('Time [s]', fontsize=FONTSIZE)
    # ax.set_xlim([0, 6500])
    # ax.set_ylim([0, 1])
    # ax.set_xlim([0, 1])
    # ax.set_ylabel('', fontsize=FONTSIZE)
    # ax.set_yticks([0, .25, .5, .75, 1])
    # ax.set_yticklabels([0, .25, .5, .75, 1], fontsize=FONTSIZE)
    ax.set_xscale("log")
    # ax.set_xlim([2, 7])
    # ax.set_xticks([2, 3, 4, 5, 6, 7])
    # ax.set_ylim([.5, 1])
    # ax.set_xticklabels([0, 1, 10, 100, 1000], fontsize=FONTSIZE)
    legend = fig.legend(handles=h, labels=[ORDER[i] for i in l], loc="outside upper center", bbox_to_anchor=(.55, 1.15), fontsize=FONTSIZE-3, ncols=2)
    frame = legend.get_frame()
    frame.set_alpha(1)
    frame.set_color('white')
    frame.set_edgecolor('black')
    frame.set_boxstyle('Square', pad=0.1)
    gs.tight_layout(fig)
    plt.savefig(f"{result_dir}/gwh_interval.pdf", bbox_inches="tight")
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"python {sys.argv[0]} <result directory>")
        exit(1)

    result_dir = Path(sys.argv[1])
    nesting = "no_delay" not in str(result_dir)
    print(nesting)

    if not result_dir.exists():
        print("Path does not exist.")

    if not result_dir.is_dir():
        print("Path is not a directory")
        exit(1)

    stats = dict()
    sims_frames = []
    orbital_periods = {}
    
    for entry in result_dir.iterdir():
        topo = entry.name
        # if topo == "meo_small":
        # if "meo" in topo or topo == "hleo":
            # continue
        # if topo == "walkers" or topo == "hleo":
        # if topo in ["walkers", "starlink9", "hleo"] or "meo" in topo:
        if topo not in ["scn", "iris2", "leo", "starlink"]:
        # if topo not in ["scn", "iris2", "leo"]:
        # if topo not in ["scn", "iris2"]:
        # if topo not in ["scn", "leo"]:
        # if topo != "scn":
        # if topo != "leo":
            continue

        # Load handovers schedule data for a single topo
        stat_file = entry.joinpath("stats.json")
        if stat_file.exists() and stat_file.is_file():
            print(f"Loading <{topo}> data")
            stats[topo] = load_stat_data(stat_file)
            orbital_periods[topo] = stats[topo]['orbital_period']

        # Load all handovers for a single topo
        if (handovers_dir := entry.joinpath("simulation")) is not None and handovers_dir.is_dir():
            (_, df)  = load_handovers_data(handovers_dir, topo)
            df['topo'] = topo
            sims_frames.append(df)

    print(orbital_periods)
    sims_frames = concat(sims_frames)
    plot_sims(sims_frames, result_dir, orbital_periods)
    plot_motivation(stats, result_dir)
    plot_nesting(stats, result_dir, nesting)
    plot_loops(sims_frames, result_dir)
    # plot_handover_interval(sims_frames, stats, result_dir, orbital_periods)
