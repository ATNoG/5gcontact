import sys
import time
import json
import requests
import subprocess

from http_server import MyServer
from http.server import HTTPServer
from parser import LogParser

headers = {'Content-Type': 'application/json'}


def run(name, ip_callback):
    f_loc = './slimano/output/{}'.format(name)
    print('RUN: {} start\n'.format(name))
    # subprocess.check_call('docker-compose -f ../docker-compose.yaml --no-cache build', shell=True)
    subprocess.check_call('docker-compose -f ../docker-compose.yaml up -d', shell=True)

    print('waiting 40 seconds for containers to go up...')
    time.sleep(40)

    create_nfvo()
    create_nst_1_ns()

    print('Deploying NSI...')

    start_time = round(time.time() * 1000)

    deploy_nsi_1_ns(ip_callback)

    my_server = HTTPServer(('0.0.0.0', 8080), MyServer)
    print('waiting for the deployment callback...')
    my_server.serve_forever()

    with open(f_loc, 'a') as f:
        f.write('TOTAL,,,deploy,{}\n'.format(round(time.time() * 1000) - start_time))

    with open('./slimano/input/callback_payload', 'r') as c_file:
        r = json.loads(c_file.read())

    nsi_id = r['modules_info']['slimano:slice-orch']['ns-instance'].get('nsi-id')

    print('Deleting NSI...')
    start_time = round(time.time() * 1000)
    delete_nsi(nsi_id)

    retries = 50
    retries_interval = 5
    while retries > 0:
        print('Checking if NSI is still available... Try number: {}'.format(retries))
        res = get_nsi(nsi_id)
        if not res:
            return
        elif res.get('status') == 'error' and res.get('message') == 'NSI not found':
            break
        else:
            retries = retries - 1
            time.sleep(retries_interval)

    subprocess.check_call('docker-compose logs > ./slimano/input/d_logs', shell=True)

    LogParser.parse('./slimano/input/d_logs', f_loc)

    with open(f_loc, 'a') as f:
        f.write('TOTAL,,,delete,{}\n'.format(round(time.time() * 1000) - start_time))

    subprocess.check_call('docker-compose -f ../docker-compose.yaml stop', shell=True)
    subprocess.check_call('docker-compose -f ../docker-compose.yaml rm -f', shell=True)
    subprocess.check_call('docker system prune -f', shell=True)
    print('RUN: {} end\n'.format(name))


def create_nfvo():
    payload_nfvo = {
        "slimano:nfvo": {
            "name": "5gcontact-nfvo2",
            "type": "osm",
            "url": "https://192.168.85.148:9999",
            "auth": {
                "username": "manuelfernandes",
                "password": "5gcontact@itneo",
                "project_id": "5gcontact"
            }
        }
    }
    requests.post('http://localhost:5000/nfvo', headers=headers, data=json.dumps(payload_nfvo))


def create_nst_1_ns():
    payload_nst = {
        "slimano:nst": {
            "name": "k8s-nst",
            "dependencies": [],
            "actions": [
                {
                    "name": "cvnf_move",
                    "type": "custom-action",
                    "agent": "osm-agent",
                    "parameters": [
                        {"name": "name"},
                        {"name": "docker_compose"},
                        {"name": "nsri_name_source"},
                        {"name": "vnfd_name_source"},
                        {"name": "vim_source"},
                        {"name": "nsri_name_target"},
                        {"name": "vnfd_name_target"},
                        {"name": "vim_target"}

                    ]
                }
            ],
            "nss-templates": [
                {
                    "template-name": "k8s",
                    "type": "nfvo",
                    "nfvo-type": "osm",
                    "nfvo-name": "5gcontact-nfvo2",
                    "instantiation": {
                        "inputs": [],
                        "outputs": []
                    }
                }
            ],
            "sdn-apps": [],
            "connections": []
        }
    }
    requests.post('http://localhost:5000/nst', headers=headers, data=json.dumps(payload_nst))


def deploy_nsi_1_ns(ip_callback):
    payload_nsi = {
        "slimano:nsi": {
            "name": "k8s-instance",
            "nst-name": "k8s-nst",
            "dependencies": [],
            "actions": [],
            "nss-instances": [
                {
                    "name": "k8s-instance",
                    "template-name": "k8s",
                    "location": "openstack-atnog-4",
                    "instantiation": {
                        "inputs": {},
                        "outputs": {}
                    }
                }
            ],
            "sdn-apps": [],
            "connections": [],
            "callback": "http://{}:8080/callback".format(ip_callback)
        }
    }
    requests.post('http://localhost:5000/nsi', headers=headers, data=json.dumps(payload_nsi))


def delete_nsi(nsi_id):
    requests.delete('http://localhost:5000/nsi/{}'.format(nsi_id), headers=headers)


def get_nsi(nsi_id):
    res = requests.get('http://localhost:5000/nsi/{}'.format(nsi_id), headers=headers)
    if not res:
        return None
    return res.json()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('USAGE: python sm_test_1ns.py 192.168.85.237')
        exit(2)

    runs = 50
    run_nr = 1
    while run_nr <= runs:
        run('test_1ns_{}'.format(run_nr), sys.argv[1])
        run_nr = run_nr + 1
