from commons.plugins.sdn_ctrl import SdnCtrl
from nameko.rpc import RpcProxy


class SdnCtrlRpcClient(SdnCtrl):

    def __init__(self, agent_name):
        self.caller = RpcProxy(agent_name)

    def deploy_flow(self, args):
        self.caller.deploy_flow(args)

    def mod_flow(self, args):
        self.caller.mod_flow(args)

    def delete_flow(self, args):
        self.caller.delete_flow(args)
