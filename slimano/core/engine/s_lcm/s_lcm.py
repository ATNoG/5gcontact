import time
import logging

from threading import Thread

from persistence.helpers.nfvo_db_helper import NfvoDbHelper
from persistence.helpers.nsi_db_helper import NsiDbHelper

from sm_agents.responses.response import AgentResponse

from sm_utils.t_utils import TemplateUtils

from engine.s_lcm.tasks.nfvo.delete import NfvoDelete

logger = logging.getLogger(__name__)


class SliceLCM(Thread):

    def __init__(self, thread_id, db_engine, config, task, nst, nsi):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.b_time = round(time.time() * 1000)

        self.config = config
        self.task = task
        self.nsi = nsi
        self.nst = nst

        # database
        db_engine.dispose()
        self.db_engine = db_engine
        self.nfvo_db_helper = NfvoDbHelper(db_engine)
        self.nsi_db_helper = NsiDbHelper(db_engine)

        self.nfvo_tasks = []

    def run(self):

        if self.task == 'update':
            pass
        elif self.task == 'delete':

            # init tasks
            nfvo_agent_name = self.config.get('sm_agents') \
                .get('nfvo') \
                .get('osm')
            nfvo_delete = NfvoDelete(nfvo_agent_name,
                                   self.config)

            self.nsi['status'] = 'deleting'
            self.nsi_db_helper.update_nsi(self.nsi)

            instances = self.nsi.get('nss-instances')

            if instances:
                # nfvo_plugin = None
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
                            return

                        nfvo_info = self.nfvo_db_helper.get_nfvo(type_info.get('nfvo-name'))
                        
                        nfvo_delete.add_job(instance, nfvo_info)
                        
                        # self.nfvo_tasks.append(nfvo_task)
                        # nfvo_task.start()

                # for nfvo_task in self.nfvo_tasks:
                #     nfvo_task.join()
                
                nfvo_delete.run()

                # self.nsi['status'] = 'deleted'
                # self.nsi_db_helper.update_nsi(self.nsi)
            self.db_engine.dispose()
            self.nsi_db_helper.delete_nsi(id=self.nsi.get('id'))

            logger.debug('$$core|SliceLCM|run|delete|{}$$'.format(str(round(time.time() * 1000) - self.b_time)))

            # stop plugins
            # self.nfvo_plugin.stop()
