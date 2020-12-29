import time
import logging

from threading import Thread

from persistence.helpers.nfvo_db_helper import NfvoDbHelper
from persistence.helpers.nsi_db_helper import NsiDbHelper

from plugins.coe.coe_rpc import CoeRpcClient

from sm_agents.responses.response import AgentResponse

from engine.responses.s_orch_response import SOrchResponse
from sm_helpers.callback_helper import CallbackHelper
from engine.s_orch.workers.nfvo_worker import NfvoWorker

from sm_utils.t_utils import TemplateUtils

logger = logging.getLogger(__name__)


class SliceOrch(Thread):

    def __init__(self, thread_id, db_engine, nst, nsi, config):
        Thread.__init__(self)
        self.thread_id = thread_id

        self.b_time = round(time.time() * 1000)

        # database
        db_engine.dispose()
        self.db_engine = db_engine
        self.nfvo_db_helper = NfvoDbHelper(db_engine)
        self.nsi_db_helper = NsiDbHelper(db_engine)

        # data in
        self.nsi = nsi
        self.nst = nst

        self.config = config

        self.nfvo_workers = []

        # plugins
        nfvo_agent_name = config.get('sm_agents') \
            .get('nfvo') \
            .get('osm')

        self.nfvo_worker = NfvoWorker(nfvo_agent_name,
                                      self.config)

        logger.debug('$$core|SliceOrch|run|init|{}$$'.format(str(round(time.time() * 1000) - self.b_time)))
        # self.coe_plugin = CoeRpcClient('os-magnum-agent')

    def run(self):

        callback_helper = CallbackHelper(self.nsi.get('callback'), 3, 5)
        response = SOrchResponse(nsi_name=self.nsi.get('name'), nst_name=self.nsi.get('nst-name'))
        response.set_status('ok')
        response.set_message('NSI deployed successfully')
        instances = self.nsi.get('nss-instances')

        d_time = round(time.time() * 1000)

        if instances:

            for instance in instances:
                type_info = TemplateUtils.get_template_type(self.nst, instance.get('template-name'))

                ns_type = type_info.get('type')
                if ns_type == 'nfvo':
                    logger.debug('Prepare to deploy at NFVO name: {}'.format(type_info.get('nfvo-name')))

                    if not self.config.get('sm_agents') and \
                            not self.config.get('sm_agents').get('nfvo') and \
                            not self.config.get('sm_agents').get('nfvo').get('osm'):
                        error_message = 'A suitable agent to deploy {} not found'.format(instance.get('name'))
                        instance['status'] = AgentResponse(status='error',
                                                           message=error_message).response
                        response.set_status('error')
                        response.set_message(error_message)
                        return callback_helper.call_callback(str(response))

                    nfvo_info = self.nfvo_db_helper.get_nfvo(type_info.get('nfvo-name'))
                    
                    self.nfvo_worker.add_job(instance, nfvo_info)

                # coe -> container orchestration engine
                if ns_type == 'coe':
                    pass

            logger.debug('$$core|SliceOrch|run|worker_pre_start|{}$$'.format(str(round(time.time() * 1000) - d_time)))
            
            self.nfvo_worker.run(response)

        logger.debug('"s_orch" NSI: {}'.format(self.nsi))
        s_time = round(time.time() * 1000)

        self.nsi.pop('callback')
        # set NSI global status
        self._set_nsi_status()
        # save instantiation info on database
        self.db_engine.dispose()
        nsi_id = self.nsi_db_helper.insert_nsi(self.nsi)
        response.set_nsi_id(nsi_id)

        logger.debug('$$core|SliceOrch|run||{}$$'.format(str(round(time.time() * 1000) - self.b_time)))

        logger.debug('"SOrchResponse": {}'.format(str(response)))

        logger.debug('$$core|SliceOrch|run|persistence|{}$$'.format(str(round(time.time() * 1000) - s_time)))

        return callback_helper.call_callback(str(response))

    def _deploy_nfvo_net_services(self):
        # NFVO needs to be already deployed and running
        pass

    def _deploy_coe_net_services(self):
        # Deploy COE if needed
        pass

    def _deploy_coe(self):
        pass

    def _set_nsi_status(self):
        self.nsi['status'] = 'ok'
        for instance in self.nsi.get('nss-instances'):
            if instance['status'].get('status') == 'error':
                self.nsi['status'] = 'error'
