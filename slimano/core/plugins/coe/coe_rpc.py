from sm_plugins.coe import Coe
from nameko.rpc import RpcProxy


class CoeRpcClient(Coe):

    def __init__(self, agent_name):
        self.caller = RpcProxy(agent_name)

    def deploy_coe(self, args):
        return self.caller.deploy_coe(args)

    def deploy_instance(self, args):
        return self.caller.deploy_instance(args)

    def exec_action(self, args):
        return self.caller.exec_action(args)

    def exec_custom_action(self, args):
        return self.caller.exec_custom_action(args)

    def delete_coe(self, args):
        return self.caller.delete_coe(args)

    def delete_instance(self, args):
        return self.caller.delete_instance(args)
