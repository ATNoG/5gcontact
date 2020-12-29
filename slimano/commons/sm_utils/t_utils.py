

class TemplateUtils:

    def __init__(self):
        pass

    @staticmethod
    def get_nst_nss_template(nst, template_name):
        templates = nst.get('nss-templates')
        if templates:
            descriptor = [d for d in templates if d.get('template-name') == template_name]
            if descriptor and len(descriptor) > 0:
                return descriptor[0]
        return None

    @staticmethod
    def get_template_type(nst, template_name):
        template = TemplateUtils.get_nst_nss_template(nst, template_name)
        if template:
            type_dict = {'type': template.get('type')}
            if template.get('type') == 'nfvo':
                type_dict['nfvo-type'] = template.get('nfvo-type')
                type_dict['nfvo-name'] = template.get('nfvo-name')
            return type_dict
        return None
