import requests
import json
import time
import logging

from osm_error import OsmError

# @when('action.config-vue-vdur')
# def do_config_vue_vdur():

logger = logging.getLogger(__name__)


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

            logger.debug('"get_token" Payload: {}'.format(json.dumps(payload)))

            r = requests.post('{}/admin/v1/tokens'.format(self.base_url), headers=headers, data=json.dumps(payload),
                              verify=False)
            self.token_payload = r.json()

        return self.token_payload.get('id')

    def get_headers(self):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.get_token())}
        return headers

    # [END] Request commons ###

    def schedule_ns_instantiation(self, nsd_name, nsi_name, vim_name, params):
        url = '{}/nslcm/v1/ns_instances'.format(self.base_url)
        nsd = self.get_nsds(nsd_name=nsd_name)

        if len(nsd) != 1:
            return OsmError(message='NSD not found')

        nsd_id = nsd[0].get('_id')
        vim_id = self.get_vim_id_by_name(vim_name)

        # additional_params_for_vnf = [{'member-vnf-index': '{}'.format(value.get('vnf-index')),
        #                               'additionalParams': {key: value.get('value')}} for key, value in params.items()]

        additional_params_for_vnf = []
        for key, value in params.items():
            if len(additional_params_for_vnf) == 0:
                additional_params_for_vnf = [{'member-vnf-index': '{}'.format(str(value.get('vnf-index'))),
                                              'additionalParams': {key: value.get('value')}}]
            else:
                already_exists = False
                for param in additional_params_for_vnf:
                    if param.get('member-vnf-index') == str(value.get('vnf-index')):
                        param['additionalParams'][key] = value.get('value')
                        already_exists = True
                if not already_exists:
                    additional_params_for_vnf.append({'member-vnf-index': '{}'.format(str(value.get('vnf-index'))),
                                                      'additionalParams': {key: value.get('value')}})

        payload = {
            "nsDescription": 'slimano-{}'.format(nsi_name),
            "nsName": 'slimano-{}'.format(nsi_name),
            "nsdId": nsd_id,
            "vimAccountId": vim_id,
            "vld": [
                {
                    "vim-network-name": "mgmt-net",
                    "name": "management"
                },
                {
                    "vim-network-name": "ext-net",
                    "name": "ext-net"
                }
            ],
            "additionalParamsForVnf": additional_params_for_vnf
        }

        logger.debug('"schedule_ns_instantiation" Payload: {}'.format(json.dumps(payload)))

        res = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), verify=False)
        logger.debug('NS instantiation scheduling response: {}'.format(res.json()))

        if not res and not res.json().get('id'):
            return OsmError(message='an error has occurred during NS scheduling')

        return res.json().get('id')

    def instantiate_ns(self, nsd_name, nsi_name, nsi_id, vim_name):
        url = '{}/nslcm/v1/ns_instances/{}/instantiate'.format(self.base_url, nsi_id)

        nsd = self.get_nsds(nsd_name=nsd_name)

        if len(nsd) != 1:
            return OsmError(message='NSD not found')

        nsd_id = nsd[0].get('_id')
        vim_id = self.get_vim_id_by_name(vim_name)

        payload = {
            "nsDescription": 'slimano-{}'.format(nsi_name),
            "nsName": 'slimano-{}'.format(nsi_name),
            "nsdId": nsd_id,
            "vimAccountId": vim_id,
            "vld": [
                {
                    "vim-network-name": "mgmt-net",
                    "name": "management"
                },
                {
                    "vim-network-name": "ext-net",
                    "name": "ext-net"
                }
            ],
            "additionalParamsForVnf": []
        }

        logger.debug('Payload: {}'.format(json.dumps(payload)))

        res = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), verify=False)

        if not res and not res.json().get('id'):
            return OsmError(message='an error has occurred during NS instantiation')

        return res.json().get('id')

    def delete_instance(self, nsr_id=None, nsr_name=None):
        if not nsr_id and not nsr_name:
            return OsmError(message='"nsr_id" or "nsr_name" not supplied')
        if not nsr_id:
            nsr_id = self.get_nsrs(nsr_name=nsr_name).get('_id')
        url = '{}/nslcm/v1/ns_instances_content/{}'.format(self.base_url, nsr_id)

        res = requests.delete(url, headers=self.get_headers(), verify=False)

        if res.ok:
            return None
        elif res.status_code == 404:
            return OsmError(message='NSR not found')
        else:
            return OsmError(message='an error has occurred during NS instantiation')

    def get_nsds(self, nsd_id=None, nsd_name=None):
        url = '{}/nsd/v1/ns_descriptors'.format(self.base_url)
        if nsd_id:
            url = url + '?id={}'.format(nsd_id)
        if nsd_name:
            url = url + '?name={}'.format(nsd_name)
        nsd = requests.get(url, headers=self.get_headers(), verify=False).json()
        return nsd

    def get_vnfrs_from_nsr(self, nsr_id=None, nsr_name=None):
        if nsr_name:
            nsr = self.get_nsrs(nsr_name=nsr_name)
            nsr_id = nsr.get('id') if len(nsr) > 0 and nsr[0].get('id') else None
        return self.get_vnfrs(nsr_id=nsr_id) if nsr_id else {}

    def get_nsrs(self, nsr_id=None, nsr_name=None):
        url = '{}/nslcm/v1/ns_instances'.format(self.base_url)
        if nsr_id:
            url = url + '?id={}'.format(nsr_id)
        if nsr_name:
            url = url + '?name={}'.format(nsr_name)
        nsr = requests.get(url, headers=self.get_headers(), verify=False).json()
        return nsr

    def get_nsr_in_dc(self, dc_name, nsr_id=None, nsr_name=None):
        dc_id = self.get_vim_id_by_name(dc_name)

        nsrs = self.get_nsrs(nsr_id, nsr_name)
        for nsr in nsrs:
            if nsr.get('datacenter') == dc_id:
                return nsr
        return None

    def get_vnfrs(self, nsr_id=None):
        url = '{}/nslcm/v1/vnfrs/'.format(self.base_url) if not nsr_id else \
            '{}/nslcm/v1/vnfrs{}'.format(self.base_url, '?nsr-id-ref={}'.format(nsr_id))
        return requests.get(url, headers=self.get_headers(), verify=False).json()

    def get_vnf_vdu(self, nsd_id=None, vnf_index=None, vnfd_ref=None, vdu_index=None, vdu_ref=None):
        vnfrs = self.get_vnfrs(nsd_id)

        for vnfr in vnfrs:
            if vnf_index and str(vnfr.get('member-vnf-index-ref')) == str(vnf_index) or \
                    vnfd_ref and vnfr.get('vnfd-ref'):
                vdurs = vnfr.get('vdur')
                for vdur in vdurs:
                    if str(vdur.get('count-index')) == str(vdu_index) or \
                            vdu_ref and vdur.get('vdu-id-ref'):
                        return vdur

    def get_vdu_mgmt_ip(self, mgmt_net, nsd_id=None, vnf_index=None, vnfd_ref=None, vdu_index=None, vdu_ref=None):
        vdu = self.get_vnf_vdu(nsd_id, vnf_index, vnfd_ref, vdu_index, vdu_ref)

        if not vdu:
            return None
        for interface in vdu.get('interfaces'):
            if interface.get('ns-vld-id') == mgmt_net:
                return interface.get('ip-address')

    def get_vim_id_by_name(self, vim_name):
        vims = requests.get('{}/admin/v1/vims'.format(self.base_url), headers=self.get_headers(), verify=False).json()
        for vim in vims:
            if vim.get('name') == vim_name:
                return vim.get('_id')
        return None

    def get_member_vnf_index_by_vnfd_name(self, nsr_id, vnfd_name):
        vnfrs = self.get_vnfrs(nsr_id)
        for vnfr in vnfrs:
            if vnfd_name == vnfr.get('vnfd-ref'):
                return vnfr.get('member-vnf-index-ref')
        return None

    def exec_action(self, nsr_id, member_vnf_index, primitive, primitive_params):
        payload = {'member_vnf_index': member_vnf_index, 'primitive': primitive,
                   'primitive_params': primitive_params}
        url = '{}/nslcm/v1/ns_instances/{}/action'.format(self.base_url, nsr_id)

        logger.debug('Payload: {}'.format(json.dumps(payload)))

        res = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), verify=False).json()
        if res.get('id'):
            return res.get('id')
        return None

    def get_action_status(self, action_id, location, nsr_id=None, nsr_name=None):
        if not nsr_id and not nsr_name:
            return None
        if not nsr_id:
            nsr_id = self.get_nsr_in_dc(location, nsr_name=nsr_name).get('_id')
        url = '{}/nslcm/v1/ns_lcm_op_occs/?nsInstanceId={}&id={}'.format(self.base_url, nsr_id, action_id)
        return requests.get(url, headers=self.get_headers(), verify=False).json()


if __name__ == '__main__':
    osmc = OsmClient('https://192.168.85.148:9999', 'manuelfernandes', '5gcontact@itneo', '5gcontact')
    print(osmc.schedule_ns_instantiation('isp', 'isp_instance', 'openstack-atnog-4', {
        'sdn_app_url': {'vnf-index': 1, 'value': 'http://10.0.1.2:8080/sdnController/stack_ready'},
        'docker_notifier_url': {'vnf-index': 3, 'value': 'empty'},
        'node_alerts_url': {'vnf-index': 3, 'value': 'empty'}}))
    # nsd_id = osmc.get_nsr_in_dc('openstack-atnog-4', nsr_name='isp').get('id')
    # print(osmc.get_vdu_mgmt_ip("osm-mgmt-net", nsd_id, vnfd_ref='swarmc', vdu_index=0))
