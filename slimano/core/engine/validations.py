from engine.responses.base import EngineResponse


class EngineValidations:

    @staticmethod
    def check_nsi_with_nst(nsi, nst):

        if len(nst.get('dependencies')) > 0:
            pass
        if len(nst.get('actions')) > 0:
            pass
        if len(nst.get('nss-templates')) > 0:
            templates = nst.get('nss-templates')
            instances = nsi.get('nss-instances')
            for template in templates:
                i_found = False
                for instance in instances:
                    if instance.get('template-name') == template.get('template-name'):
                        i_found = True
                        t_instantiation_params = template['instantiation'].get('inputs', {})
                        i_instantiation_params = instance['instantiation'].get('inputs', {})
                        for t_inst in t_instantiation_params:
                            if t_inst.get('name') not in list(i_instantiation_params.keys()):
                                return EngineResponse(status='error',
                                                      message='Validation error: instantiation parameter is missing')
                if not i_found:
                    return EngineResponse(status='error', message='Validation error: instances missing')
            return None

        if len(nst.get('sdn-apps')) > 0:
            pass
        if len(nst.get('connections')) > 0:
            pass
