from kubernetes import client, config, utils


class K8sClient:

    def __init__(self, host, token):
        a_config = client.Configuration()

        a_config.host = host
        a_config.verify_ssl = False

        a_config.api_key = {'authorization': 'Bearer {}'.format(token)}

        self.api_client = client.ApiClient(a_config)
        self.ext_v1 = client.ExtensionsV1beta1Api(self.api_client)

    def call_something(self):
        pass

    def create_deployment(self, name, deployment_template):
        utils.create_from_yaml(self.api_client,
                               deployment_template
                               )
        response = self.ext_v1.read_namespaced_deployment(
            name=name,
            namespace='default'
        )

    def update_deployment(self):
        pass


if __name__ == '__main__':
    k8s_client = K8sClient('192.168.85.xxx:443', 'xxxxxx')
