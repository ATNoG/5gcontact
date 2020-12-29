from commons.plugins.sd_ran import SdnRan
from nameko.rpc import RpcProxy


class SdRanRpcClient(SdnRan):

    def __init__(self, agent_name):
        self.caller = RpcProxy(agent_name)

    def deploy_slice(self, args):
        self.caller.deploy_slice(args)

    def mod_slice(self, args):
        self.caller.mod_slice(args)

    def delete_slice(self, args):
        self.caller.delete_slice(args)
