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
                    if not d.get(row[0]):
                        d[row[0]] = {}
                    d[row[0]][os.path.basename(of.name)] = [float(x) for x in row[1:]]
    print(d)

    build_graph(d, '{}/graph_total.pdf'.format(sys.argv[1]))


def build_graph(md, graph_path):

    # print(md)

    for frmw, value in md.items():
        for run_nr, value2 in value.items():
            value2[1] = value2[0] - value2[1]
            del value2[-1]

    fig, ax = plt.subplots()
    # ax.set_xticks([0., 0.5, 1.])
    x_pos = np.arange(4)

    patterns = ('--', '\\\\', '///', '//')

    s = 0.3
    ss = 0.15
    bars = []
    l_comp = []
    xticks_labels = []
    s_keys = sorted(md)
    for index, frmw in enumerate(s_keys):
        value = md.get(frmw)
        means = []
        yerr = []
        xticks_labels = []
        ord_run_nr = sorted([int(x) for x in value.keys()])
        for run_nr in ord_run_nr:
            value2 = value.get(str(run_nr))
            means.append(round(value2[0] / 1000))
            yerr.append(round(value2[1] / 1000))
            xticks_labels.append(run_nr)
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
        l_comp.append(frmw.upper() if frmw != 'sm' else 'SliMANO')

    ax.set_xlabel('Number of OSM NSs')
    ax.set_ylabel('Seconds')

    ax.set_xticks(x_pos + s)
    ax.set_xticklabels(xticks_labels)
    leg = ax.legend(tuple(x[0] for x in bars),
                    tuple(l_comp),
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
