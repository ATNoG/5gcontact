import time
import json
import logging

from plugins.nfvo.nfvo_rpc import NfvoRpcClient

logger = logging.getLogger(__name__)


class NfvoDelete:

    def __init__(self, nfvo_agent_name, config):
        self.config = config
        self.nfvo_agent_name = nfvo_agent_name

        self.jobs = []
        self.running_jobs = []

        self.nfvo_plugin = NfvoRpcClient(config, nfvo_agent_name)

    def add_job(self, instance, nfvo_info):
        self.jobs.append([instance, nfvo_info])

    def run(self, response=None):

        b_time = round(time.time() * 1000)

        for job in self.jobs:
            logger.debug('Prepare to delete NSSI at NFVO name: {}'.format(job[1].name))

            nfvo_ctx = {
                'url': job[1].url,
                'username': job[1].username,
                'password': job[1].password,
                'parameters': json.loads(job[1].parameters)
            }

            args = {
                'nsr_id': job[0]['instantiation']['outputs'].get('ns_id')
            }

            logger.debug('About to start to delete NSSI {} at NFVO {}'.format(job[0].get('name'),
                                                                              job[1].name))
            logger.debug('nfvo_ctx: {} | args: {}'.format(nfvo_ctx, args))

            # Call NFVO agent to deploy NS and save response to response builder
            res_call = self.nfvo_plugin.delete_instance(nfvo_ctx, args)

            self.running_jobs.append([job[0], res_call])

        for r_job in self.running_jobs:
            res = r_job[1].result()

            logger.debug('A job has finished. Instance : {}'.format(r_job[0]))

            if res.get('outputs'):
                r_job[0]['instantiation']['outputs'] = res.pop('outputs')
            r_job[0]['status'] = res

        logger.debug('$$core|NfvoDelete|run||{}$$'
                     .format(str(round(time.time() * 1000) - b_time)))

        self.nfvo_plugin.stop()

