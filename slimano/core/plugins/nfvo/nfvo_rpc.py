from nameko.standalone.rpc import ClusterRpcProxy
from sm_plugins.nfvo import Nfvo


class NfvoRpcClient(Nfvo):
        
    def __init__(self, config, nfvo_agent_name):
        self.config = config
        self.nfvo_agent_name = nfvo_agent_name

        self.cluster_rpc_c = ClusterRpcProxy(config)
        self.cluster_rpc = self.cluster_rpc_c.start()

    def deploy_instance(self, ctx, args):
        agent = getattr(self.cluster_rpc, self.nfvo_agent_name)
        return agent.deploy_instance.call_async(ctx, args)

    def exec_action(self, ctx, args):
        agent = getattr(self.cluster_rpc, self.nfvo_agent_name)
        return agent.exec_action.call_async(ctx, args)

    def exec_custom_action(self, ctx, args):
        agent = getattr(self.cluster_rpc, self.nfvo_agent_name)
        return agent.exec_custom_action.call_async(ctx, args)

    def delete_instance(self, ctx, args):
        agent = getattr(self.cluster_rpc, self.nfvo_agent_name)
        return agent.delete_instance.call_async(ctx, args)

    def stop(self):
        self.cluster_rpc_c.stop()
