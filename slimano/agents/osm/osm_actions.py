from osm_client import OsmClient


class OsmActions:

    def __init__(self, osm_client):
        self.osmc = osm_client

    def deploy_cvnf(self, cvnf_name, vnfd_name, d_compose_url, location, nsr_name=None, nsr_id=None):
        primitive_params = {'docker_compose': d_compose_url,
                            'stack_name': cvnf_name}
        if not nsr_id and not nsr_name:
            return None
        if nsr_name:
            nsr_id = self.osmc.get_nsr_in_dc(location, nsr_name=nsr_name)
        vnf_index = self.osmc.get_member_vnf_index_by_vnfd_name(nsr_id, vnfd_name)
        return self.osmc.exec_action(nsr_id, vnf_index, 'stack-deploy', primitive_params)

    def rm_cvnf(self, cvnf_name, vnfd_name, location, nsr_name=None, nsr_id=None):
        primitive_params = {'stack_name': cvnf_name}
        if not nsr_id and not nsr_name:
            return None
        if nsr_name:
            nsr_id = self.osmc.get_nsr_in_dc(location, nsr_name=nsr_name)
        vnf_index = self.osmc.get_member_vnf_index_by_vnfd_name(nsr_id, vnfd_name)
        return self.osmc.exec_action(nsr_id, vnf_index, 'stack-remove', primitive_params)
