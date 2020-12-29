import requests
import json
import time

# @when('action.config-vue-vdur')
# def do_config_vue_vdur():


def run(name):

    osmc = OsmClient('https://192.168.85.148:9999', 'manuelfernandes', '5gcontact@itneo', '5gcontact')

    nsi_id = osmc.schedule_nsi_instantiation('k8s_nst5', 'k8s_nsi5', 'openstack-atnog-4')

    osmc.instantiate_nsi('k8s_nst5', 'k8s_nsi5', nsi_id, 'openstack-atnog-4')

    init_time = round(time.time() * 1000)

    # wait for NSI to be deployed
    retries = 240
    retries_interval = 10
    while retries > 0:
        nsi = osmc.get_nsi(nsi_id)
        if nsi and nsi[0].get('detailed-status') == 'done' and nsi[0].get('operational-status') == 'running':
            break
        print('Waiting for NSI to be deployed... Retry: {}'.format(retries))
        retries = retries - 1
        time.sleep(retries_interval)

    if retries == 0:
        print('[ERROR] Number of retries exceeded')
        exit(2)

    end_time = round(time.time() * 1000) - init_time
    # core,Engine,create_nst,,13
    print('Saving deployment time on file...')
    with open('./osm/output/{}'.format(name), 'w') as f:
        f.write('TOTAL,,,deploy,{}\n'.format(end_time))

    init_time = round(time.time() * 1000)

    osmc.delete_nsi(nsi_id)

    # wait for NSI to be delete
    retries = 240
    retries_interval = 10
    while retries > 0:
        nsi = osmc.get_nsi(nsi_id)
        if nsi and nsi[0].get('operational-status') == 'terminated':
            osmc.delete_nsi(nsi_id)
            break
        print('Waiting for NSI to be deleted... Retry: {}'.format(retries))
        retries = retries - 1
        time.sleep(retries_interval)

    end_time = round(time.time() * 1000) - init_time
    print('Saving delete time on file...')
    with open('./osm/output/{}'.format(name), 'a') as f:
        f.write('TOTAL,,,delete,{}'.format(end_time))

    if retries == 0:
        print('[ERROR] Number of retries exceeded')
        exit(2)


class OsmClient:
    def __init__(self, url, user, password, project_id):
        self.base_url = '{}/osm'.format(url)

        # for use with "get_token"
        self.user = user
        self.password = password
        self.project_id = project_id

        self.token_payload = None

    # [START] request build-up commons ###
    def get_token(self):
        if not self.token_payload or self.token_payload.get('expires') < time.time():
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            payload = {'username': self.user, 'password': self.password, 'project_id': self.project_id}

            print('"get_token" Payload: {}'.format(json.dumps(payload)))

            r = requests.post('{}/admin/v1/tokens'.format(self.base_url), headers=headers, data=json.dumps(payload),
                              verify=False)
            self.token_payload = r.json()

        return self.token_payload.get('id')

    def get_headers(self):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.get_token())}
        return headers

    # [END] Request commons ###

    def schedule_nsi_instantiation(self, nst_name, nsi_name, vim_name):
        url = '{}/nsilcm/v1/netslice_instances'.format(self.base_url)
        nst = self.get_nst(name=nst_name)

        if len(nst) != 1:
            print('NST not found')
            return

        nst_id = nst[0].get('_id')
        vim_id = self.get_vim_id_by_name(vim_name)

        # additional_params_for_vnf = [{'member-vnf-index': '{}'.format(value.get('vnf-index')),
        #                               'additionalParams': {key: value.get('value')}} for key, value in params.items()]

        payload = {
            "nsiDescription": '{}'.format(nsi_name),
            "nsiName": '{}'.format(nsi_name),
            "nstId": nst_id,
            "vimAccountId": vim_id,
        }

        print('"schedule_nsi_instantiation" Payload: {}'.format(json.dumps(payload)))

        res = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), verify=False)
        print('NSI instantiation scheduling response: {}'.format(res.json()))

        if not res and not res.json().get('id'):
            print('an error has occurred during NSI scheduling')
            return

        return res.json().get('id')

    def instantiate_nsi(self, nst_name, nsi_name, nsi_id, vim_name):
        url = '{}/nsilcm/v1/netslice_instances/{}/instantiate'.format(self.base_url, nsi_id)

        nst = self.get_nst(name=nst_name)

        if len(nst) != 1:
            return print('NST not found')

        nst_id = nst[0].get('_id')
        vim_id = self.get_vim_id_by_name(vim_name)

        payload = {
            "nsiDescription": '{}'.format(nsi_name),
            "nsiName": '{}'.format(nsi_name),
            "nstId": nst_id,
            "vimAccountId": vim_id,
        }

        print('Payload: {}'.format(json.dumps(payload)))

        res = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), verify=False)

        if not res and not res.json().get('id'):
            print('an error has occurred during NSI instantiation')
            return

        return res.json().get('id')

    def get_nst(self, id=None, name=None):
        url = '{}/nst/v1/netslice_templates/'.format(self.base_url)
        if id:
            url = url + '?id={}'.format(id)
        if name:
            url = url + '?name={}'.format(name)
        nst = requests.get(url, headers=self.get_headers(), verify=False)

        if nst.status_code == 404:
            return None

        return nst.json()

    def get_nsi(self, id=None, name=None):
        url = '{}/nsilcm/v1/netslice_instances/'.format(self.base_url)
        if id:
            url = url + '?id={}'.format(id)
        if name:
            url = url + '?name={}'.format(name)
        nsi = requests.get(url, headers=self.get_headers(), verify=False)

        if nsi.status_code == 404:
            return None

        return nsi.json()

    def delete_nsi(self, nsi_id):
        url = '{}/nsilcm/v1/netslice_instances_content/{}'.format(self.base_url, nsi_id)

        return requests.delete(url, headers=self.get_headers(), verify=False)

    def get_vim_id_by_name(self, vim_name):
        vims = requests.get('{}/admin/v1/vims'.format(self.base_url), headers=self.get_headers(), verify=False).json()
        for vim in vims:
            if vim.get('name') == vim_name:
                return vim.get('_id')
        return None


if __name__ == '__main__':
    # osmc = OsmClient('https://192.168.85.148:9999', 'manuelfernandes', '5gcontact@itneo', '5gcontact')
    # print(osmc.delete_nsi('4875c435-bf2c-4d7e-b580-ba9b29f2667e').status_code)
    # run('test')

    runs = 50
    run_nr = 1
    while run_nr <= runs:
        run('test_osm_5ns_{}'.format(run_nr))
        run_nr = run_nr + 1
