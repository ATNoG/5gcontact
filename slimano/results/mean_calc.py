import sys
import os
import csv
import numpy as np

from scipy import stats


nbi_dp = []
core_dp = []
agent_dp = []
total_dp = []

nbi_del = []
core_del = []
agent_del = []
total_del = []


def run(path):
    for f in os.listdir(path):
        if f.startswith('test_'):
            nbi = []
            core = []
            osm_agent = []
            total = []
            c_path = os.path.join(path, f)
            with open(c_path, 'r') as of:
                csv_reader = csv.reader(of, delimiter=',')
                for row in csv_reader:
                    if row[0] == 'nbi':
                        nbi.append(row[1:])
                    if row[0] == 'core':
                        core.append(row[1:])
                    if row[0] == 'osm_agent':
                        osm_agent.append(row[1:])
                    if row[0] == 'TOTAL':
                        total.append(row)
            update_mean_dp(nbi, core, osm_agent, total)
            update_mean_del(nbi, core, osm_agent, total)


def update_mean_dp(nbi_l, core_l, agent_l, total_l):
    nbi_c = 0
    for nbi in nbi_l:
        if nbi[0] == 'Flask' and \
                nbi[1] == 'nsi_instantiate':
            nbi_c = int(nbi[-1])
    nbi_dp.append(nbi_c)

    so_core = 0
    nfvo_w = []
    engine_cn = []
    for core in core_l:
        if core[0] == 'SliceOrch' and core[1] == 'run' and core[2] == '':
            so_core = int(core[-1])
        if core[0].startswith('NfvoWorker') and core[1] == 'run':
            nfvo_w.append(int(core[-1]))
        if core[0] == 'Engine' and core[1] == 'create_nsi':
            engine_cn.append(int(core[-1]))

    nfvo_w_m = max(nfvo_w, default=0)
    engine_cn_m = max(engine_cn, default=0)
    # core_dp.append((so_core - nfvo_w_m) + engine_cn_m)

    agent_c = []
    for agent in agent_l:
        if agent[0] == 'OSMAgent' and \
                agent[1] == 'deploy_instance':
            agent_c.append(int(agent[-1]))

    agent_c_m = max(agent_c, default=0)

    # NFVO Worker execution time
    s_orch_et = so_core - agent_c_m
    core_dp.append(s_orch_et)

    # agent_dp.append(nfvo_w_et)

    total_c = 0
    for total in total_l:
        if total[0] == 'TOTAL' and total[-2] == 'deploy':
            total_c = int(total[-1])
    total_dp.append(total_c)


def update_mean_del(nbi_l, core_l, agent_l, total_l):
    nbi_c = 0
    for nbi in nbi_l:
        if nbi[0] == 'Flask' and \
                nbi[1] == 'nsi_delete':
            nbi_c = nbi_c + int(nbi[-1])
    nbi_del.append(nbi_c)

    so_core = 0
    nfvo_d = 0
    engine_cn = []
    for core in core_l:
        if core[0] == 'SliceLCM' and core[1] == 'run' and core[2] == 'delete':
            so_core = int(core[-1])
        if core[0].startswith('NfvoDelete') and core[1] == 'run':
            nfvo_d = int(core[-1])
        if core[0] == 'Engine' and core[1] == 'delete_nsi':
            engine_cn.append(int(core[-1]))

    engine_cn_m = max(engine_cn, default=0)
    core_del.append((so_core - nfvo_d) + engine_cn_m)

    agent_c = 0
    for agent in agent_l:
        if agent[0] == 'OSMAgent' and \
                agent[1] == 'delete_instance':
            agent_c = int(agent[-1])

    agent_del.append(nfvo_d - agent_c)

    total_c = 0
    for total in total_l:
        if total[0] == 'TOTAL' and total[-2] == 'delete':
            total_c = int(total[-1])
    total_del.append(total_c)


def get_stats(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t._ppf((1 + confidence) / 2., n - 1)
    return m, max(m - h, 0.0), m + h


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('USAGE: python mean_calc.py <folder>')
        exit(2)

    folder = sys.argv[1]
    run(folder)

    nbi_ms = get_stats(nbi_dp)
    core_ms = get_stats(core_dp)
    # agent_ms = get_stats(agent_dp)
    total_ms = get_stats(total_dp)

    with open('{}/mean_deploy'.format(folder), 'w') as f:
        csv_w = csv.writer(f, delimiter=',')

        csv_w.writerow(['nbi'] + list(nbi_ms))
        csv_w.writerow(['core'] + list(core_ms))
        # csv_w.writerow(['agent'] + list(agent_ms))
        csv_w.writerow(['total'] + list(total_ms))

    print('Deploy mean:\n')
    print(nbi_ms)
    print(core_ms)
    # print(agent_ms)
    print(total_ms)

    nbi_ms = get_stats(nbi_del)
    core_ms = get_stats(core_del)
    # agent_ms = get_stats(agent_del)
    total_ms = get_stats(total_del)

    with open('{}/mean_delete'.format(folder), 'w') as f:
        csv_w = csv.writer(f, delimiter=',')

        csv_w.writerow(['nbi'] + list(nbi_ms))
        csv_w.writerow(['core'] + list(core_ms))
        # csv_w.writerow(['agent'] + list(agent_ms))
        csv_w.writerow(['total'] + list(total_ms))

    print('Delete mean:\n')
    print(nbi_ms)
    print(core_ms)
    # print(agent_ms)
    print(total_ms)
