import os
import sys
import csv
import numpy as np

# matplotlib
import matplotlib.pyplot as plt;

plt.rcdefaults()
import matplotlib.pyplot as plt


def run(path):
    d = {}
    for f in os.listdir(path):
        c_path = os.path.join(path, f)
        if '.pdf' not in c_path:
            with open(c_path, 'r') as of:
                # d[os.path.basename(of.name)] = {}
                csv_reader = csv.reader(of, delimiter=',')
                for row in csv_reader:
                    if row[0] != 'total':
                        if not d.get(row[0]):
                            d[row[0]] = {}
                        # d[os.path.basename(of.name)][row[0]] = [float(x) for x in row[1:]]
                        d[row[0]][os.path.basename(of.name)] = [float(x) for x in row[1:]]
    print(d)

    build_graph(d, './graph.pdf'.format(sys.argv[1]))


def build_graph(md, graph_path):

    # print(md)

    for run_nr, value in md.items():
        for comp, value2 in value.items():
            value2[1] = value2[0] - value2[1]
            del value2[-1]

    fig, ax = plt.subplots()
    ax.set_xticks([0., 0.5, 1.])
    x_pos = np.arange(4)

    patterns = ('--', '\\\\', '///', '//')

    xticks_labels = []
    s = 0.35
    ss = 0.15
    bars = []
    l_comp = []
    for index, comp in enumerate(md):
        value = md.get(comp)
        means = []
        l_comp = []
        yerr = []
        comps = sorted([int(x) for x in value.keys()])
        for run_nr_n in comps:
            run_nr_v = value.get(str(run_nr_n))
            means.append(run_nr_v[0])
            yerr.append(run_nr_v[1])
            l_comp.append(int(''.join([n for n in str(run_nr_n) if n.isdigit()])))
        print(means)
        print(yerr)
        bars.append(ax.bar(x_pos + ss,
                           means,
                           yerr=yerr,
                           align='center',
                           alpha=1.,
                           edgecolor='black',
                           ecolor='black',
                           capsize=10,
                           hatch=patterns[index],
                           color='white',
                           width=s)
                    )
        ss = ss + s
        xticks_labels.append(comp if comp != 'nbi' else comp.upper())

    ax.set_xlabel('Number of OSM NSs')
    ax.set_ylabel('Milliseconds - ms')

    ax.set_xticks(x_pos + s)
    ax.set_xticklabels(l_comp)
    leg = ax.legend(tuple(x[0] for x in bars),
                    tuple(xticks_labels),
                    labelspacing=1.5,
                    handlelength=4,
                    borderpad=1)
    leg.get_frame().set_linewidth(0.0)

    for patch in leg.get_patches():
        patch.set_height(22)
        patch.set_y(-6)

    ax.yaxis.grid(False)

    # Save the plot in pdf
    plt.tight_layout()
    plt.savefig(graph_path)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('USAGE: python create_total_graph.py <folder>')
        exit(2)

    run(sys.argv[1])
