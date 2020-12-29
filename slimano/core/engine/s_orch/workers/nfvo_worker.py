import time
import logging
import json

from plugins.nfvo.nfvo_rpc import NfvoRpcClient

logger = logging.getLogger(__name__)


class NfvoWorker:

    def __init__(self, nfvo_agent_name, config):
        self.nfvo_agent_name = nfvo_agent_name
        self.config = config

        self.jobs = []
        self.running_jobs = []

        self.nfvo_plugin = NfvoRpcClient(config, nfvo_agent_name)

    def add_job(self, instance, nfvo_info):
        self.jobs.append([instance, nfvo_info])

    def run(self, response):

        b_time = round(time.time() * 1000)

        for job in self.jobs:
            logger.debug('Prepare to deploy at NFVO name: {}'.format(job[1].name))

            nfvo_ctx = {
                'url': job[1].url,
                'username': job[1].username,
                'password': job[1].password,
                'parameters': json.loads(job[1].parameters)
            }

            args = {
                'descriptor_name': job[0].get('template-name'),
                'instance_name': job[0].get('name'),
                'location': job[0].get('location'),
                'instantiation_params': job[0]['instantiation'].get('inputs', {})
            }

            logger.debug('About to start deploy instance {} at NFVO {}'.format(job[0].get('name'),
                                                                               job[1].name))
            logger.debug('nfvo_ctx: {} | args: {}'.format(nfvo_ctx, args))

            # Call NFVO agent to deploy NS and save response to response builder
            res_call = self.nfvo_plugin.deploy_instance(nfvo_ctx, args)

            self.running_jobs.append([job[0], res_call])

        for r_job in self.running_jobs:
            res = r_job[1].result()

            logger.debug('A job has finished. Instance : {}'.format(r_job[0]))

            if res.get('outputs'):
                r_job[0]['instantiation']['outputs'] = res.pop('outputs')
            r_job[0]['status'] = res

            if r_job[0]['status'].get('status') == 'error':
                response.set_status('error')
                response.set_message('NSI deployment with errors')
            response.put_ns_instance(r_job[0])

        logger.debug('$$core|NfvoWorker|run||{}$$'
                     .format(str(round(time.time() * 1000) - b_time)))

        self.nfvo_plugin.stop()
