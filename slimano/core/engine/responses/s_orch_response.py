from engine.responses.base import EngineResponse


class SOrchResponse(EngineResponse):

    def __init__(self, nsi_id=None, nsi_name=None, nst_name=None):
        super().__init__()
        self.response['modules_info']['slimano:slice-orch'] = {
            'ns-instance': {
                'nsi-id': nsi_id,
                'nsi-name': nsi_name,
            },
            'nst-name': nst_name,
            'actions': [],
            'nss-instances': [],
            'connections': []
        }

    def set_nsi_id(self, nsi_id):
        self.response['modules_info']['slimano:slice-orch']['ns-instance']['nsi-id'] = nsi_id

    def set_nsi_name(self, nsi_name):
        self.response['modules_info']['slimano:slice-orch']['ns-instance']['nsi-name'] = nsi_name

    def set_nst_name(self, nst_name):
        self.response['modules_info']['slimano:slice-orch']['nst-name'] = nst_name

    def put_action(self, action):
        self.response['modules_info']['slimano:slice-orch']['actions'].append(action)

    def put_ns_instance(self, ns_instance):
        self.response['modules_info']['slimano:slice-orch']['nss-instances'].append(ns_instance)

    def put_connections(self, connection):
        self.response['modules_info']['slimano:slice-orch']['connections'].append(connection)
