import os
import sys
import csv

from cycler import cycler

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

    monochrome = (cycler('color', ['k']) * cycler('linestyle', ['-', '--', ':', '=.']) * cycler('marker', ['^', ',', '.']))
    ax.set_prop_cycle(monochrome)

    l_comp = []
    s_keys = sorted(md)
    for index, frmw in enumerate(s_keys):
        value = md.get(frmw)
        means = []
        xerr = []
        xticks_labels = []
        ord_run_nr = sorted([int(x) for x in value.keys()])
        for run_nr in ord_run_nr:
            value2 = value.get(str(run_nr))
            means.append(round(value2[0] / 1000))
            xerr.append(round(value2[1] / 1000))
            xticks_labels.append(run_nr)
        print(means)
        print(xerr)

        ax.plot(ord_run_nr, means)
        ax.errorbar(ord_run_nr, means, xerr=xerr, fmt='o')

        l_comp.append(frmw.upper() if frmw != 'sm' else 'SliMANO')

    ax.set_xlabel('Number of OSM NSs')
    ax.set_ylabel('Seconds')

    leg = ax.legend(tuple(l_comp),
                    labelspacing=1.5,
                    handlelength=4,
                    borderpad=1)

    # Save the plot in pdf
    plt.tight_layout()
    plt.savefig(graph_path)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('USAGE: python create_total_graph.py <folder>')
        exit(2)

    run(sys.argv[1])
