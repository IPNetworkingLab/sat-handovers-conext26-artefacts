import json
import sys
from pathlib import Path
from pandas import DataFrame, concat


METHODS = {
    "NestedForward": 'NF',
    "AggregatedSequential": 'AS',
    "FastAggregatedSequential": 'FAS',
    "Sequential": 'S'
}
sizes = {"leo": 432, 'scn': 288, 'hleo': 288, 'meo_large': 128, 'meo_small': 72, 'iris2': 264, 'starlink': 1584}

def parse_handover(filepath: Path, topo: str) -> (dict, DataFrame):

    with open(filepath , 'r') as fd:
        data = json.load(fd)
    stats = dict()

    # Measure number of loops
    total_loops = 0
    stats["loops"] = dict()
    # print("Loops analyis:")
    for loop_type, loops in data['Loops'][0]['Loops'].items():
        n_loops = len(loops)
        # print(f" {loop_type}: {n_loops}")
        stats['loops'][loop_type] = n_loops
        total_loops += n_loops
    # print(f" total loops: {total_loops}\n")
    stats["loops"]["total"] = total_loops

    frames = []

    stats["methods"] = dict()
    for method, data in data.items():
        if method not in METHODS:
            continue

        # Measure number of FIB update
        n_fib = 0
        # Measure number of update application
        apps = set()

        # Measure instability duration
        instab_start = -1
        instab_end = -1
        previous = False

        # Measure amount of explicit synchronization
        n_confirmations = 0

        # Measure number of updates
        n_upd = 0

        first_fib = -1
        last_fib = -1

        nodes = set()

        for entry in data:
            if (upd := entry.get('FibUpdate')) is not None:
                if first_fib == -1:
                    first_fib = upd['ts']
                last_fib = upd['ts']
                nodes.add(upd['node'])
                n_fib += 1
                current = upd["seamless"]
                if current is not None:
                    if not current:
                        print(filepath, method, upd)
                    if not current and instab_start == -1:
                        instab_start = upd['ts']
                    if not previous and current:
                        instab_end = upd['ts']
                    previous = current
            elif (_conf := entry.get('Confirmation')) is not None:
                n_confirmations += 1
            elif (_upd := entry.get('UpdateTx')) is not None:
                n_upd += 1
            elif (app := entry.get('Update')) is not None and (rid := app.get('rid')) is not None:
                apps.add(rid)

        # Compute C_FUT
        c_fut = (last_fib - first_fib) / 1000

        instab = (0 if instab_start == -1 or instab_end == -1 else instab_end - instab_start) / 1000
    
        # print(f"{method}:\n C_FUT: {c_fut}\n Instab: {instab}\n Confirmations: {n_confirmations}\n# Fib: {n_fib}\n# Upd: {n_upd}")
        stats["methods"][method] = {"cfut": c_fut, "instab": instab, "confs": n_confirmations, "n_fib": n_fib, "n_upd": n_upd}
        frames.append(DataFrame([{'method': METHODS[method], "cfut": c_fut, "instab": instab, "confs": n_confirmations, "n_fib": n_fib, "n_upd": n_upd, "handover": filepath.name, 'loops': stats['loops']['total']}]))

        if len(apps) < sizes[topo]:
            missing = set([i for i in range(0, sizes[topo])]).difference(apps)
            print(f"{method} Nodes have not applied the update {filepath} {len(apps)}/{sizes[topo]}: {missing}")

        if len(nodes) < sizes[topo]:
            missing = set([i for i in range(0, sizes[topo])]).difference(nodes)
            print(f"{method} No FIB update {filepath}: {missing}")

    return (stats, concat(frames))


def load_handovers_data(xp_dirs: Path, topo: str) -> (dict, DataFrame):
    loops = dict()
    frames = []
    
    for entry in xp_dirs.iterdir():
        if entry.suffix != ".json":
            continue
        handover = entry.name.split('.')[0]
        (stats, df) = parse_handover(entry, topo)
        frames.append(df)
                    
        for loop_type in stats["loops"].keys():
            if loop_type == "total":
                continue
            try:
                loops[loop_type][handover] = stats["loops"][loop_type]
            except KeyError:
                loops[loop_type] = {handover: stats["loops"][loop_type]}

    return ({'loops': loops}, concat(frames))



    # pu.latexify(nb_subplots_line=2, fig_width=3, fig_height=4)
    # fig, axes = plt.subplots(nrows=2, layout='constrained')
    # plt.rc('font', weight='heavy')
    # for ax in axes:
    #     ax.set_axisbelow(True)
    #     ax.grid(axis='y')
    # import numpy as np
    # bottom = np.zeros(len(order))
    # axes[0].set_ylabel('Loops')
    # axes[1].set_ylabel('Addition Delay [ms]')

    # for (idx, (loop_type, y)) in enumerate(loops.items()):
    #     y = [y[x] for x in order]
    #     axes[0].bar(x, y, label=loop_type, bottom=bottom, color=pu.COLORS[idx+1])
    #     bottom += y
    # axes[0].legend(["Type 1", "Type 2", "Type 3"], fontsize=11)
    # axes[0].set_xticklabels([])
    # axes[1].plot(x, [int(handover.split("_")[-2]) for handover in order], "x-")

    # plt.xlabel('Handover')
    # plt.tight_layout()
    # plt.savefig(f"{topo}_loops.pdf")
