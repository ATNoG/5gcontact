import time
import logging

from sm_plugins.nfvo import Nfvo
from nameko.rpc import rpc
from nameko import config
from osm_client import OsmClient
from osm_error import OsmError
from osm_actions import OsmActions

from sm_agents.responses.response import AgentResponse

logger = logging.getLogger(__name__)


class OSMAgent(Nfvo):
    name = "osm_agent"

    def __init__(self):
        self.retries = config.get('nr_retries')
        self.retires_interval = config.get('retires_interval')

    @rpc
    def deploy_instance(self, ctx, args):
        logger.debug('"deploy_instance" ctx: {} | args: {}'.format(ctx, args))

        b_time = round(time.time() * 1000)

        osm_client = OsmClient(ctx.get('url'),
                               ctx.get('username'),
                               ctx.get('password'),
                               ctx['parameters'].get('project_id'))

        # schedule ns instantiation
        res = osm_client.schedule_ns_instantiation(args.get('descriptor_name'),
                                                   args.get('instance_name'),
                                                   args.get('location'),
                                                   args.get('instantiation_params'))

        logger.debug('Schedule instantiation OSM response: {}'.format(res))

        if isinstance(res, OsmError):
            msg = 'An error has occurred while instantiating NS.' \
                  ' OSM Client error: {}'.format(res.response.get('message'))
            logger.debug(msg)
            return AgentResponse(status='error',
                                 message=msg) \
                .response

        nsr_id = res

        # instantiate ns
        res = osm_client.instantiate_ns(args.get('descriptor_name'),
                                        args.get('instance_name'),
                                        nsr_id,
                                        args.get('location'))

        if isinstance(res, OsmError):
            msg = 'An error has occurred while instantiating NS.' \
                  ' OSM Client error: {}'.format(res.response.get('message'))
            logger.debug(msg)
            return AgentResponse(status='error',
                                 message=msg) \
                .response

        # wait for ns to be ready
        retries = self.retries
        while retries > 0:
            nsrs = osm_client.get_nsrs(nsr_id=nsr_id)
            if not nsrs:
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='An error has occurred while instantiating NS. Empty payload.') \
                    .response

            if len(nsrs) != 1:
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='Multiple NSRs found.').response

            nsr = nsrs[0]

            if not nsr.get('operational-status'):
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='An error has occurred while instantiating NS.'
                                             ' Cannot retrieve operational status.').response
            oper_state = nsr.get('operational-status')

            if not nsr.get('config-status'):
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='An error has occurred while instantiating NS.'
                                             ' Cannot retrieve configuration status.').response
            config_state = nsr.get('config-status')

            logger.debug('NSR "oper_state": {} | "config_state": {}'.format(oper_state, config_state))

            if oper_state == 'running' and config_state == 'configured':
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                ar = AgentResponse(status='ok', message='deployed')
                ar.set_outputs('ns_id', nsr_id)
                return ar.response
            if oper_state == 'failed' or config_state == 'failed':
                logger.debug(
                    '$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='An error has occurred while instantiating NS. Deploy failed') \
                    .response

            time.sleep(self.retires_interval)
            retries = retries - 1

        logger.debug('$$osm_agent|OSMAgent|deploy_instance||{}$$'.format(str(round(time.time() * 1000 - b_time))))

        return AgentResponse(status='error', message='An error has occurred while instantiating NS. Unknown error') \
            .response

    @rpc
    def exec_action(self, ctx, args):
        osm_client = OsmClient(ctx.get('url'),
                               ctx.get('username'),
                               ctx.get('password'),
                               ctx['parameters'].get('project_id'))
        osm_actions = OsmActions(osm_client, self.retries, self.retires_interval)

        if args.get('action') == 'cvnf_move':
            osm_actions.move_cvnf(args.get('cvnf_name'),
                                  args.get('cvnf_dc'),
                                  args.get('source_loc'),
                                  args.get('target_loc'),
                                  args.get('params'))
        else:
            return AgentResponse(status='error', message='Unknown OSM action') \
                .response

    @rpc
    def exec_custom_action(self, ctx, args):
        pass

    @rpc
    def delete_instance(self, ctx, args):
        logger.debug('"delete_instance" ctx: {} | args: {}'.format(ctx, args))

        b_time = round(time.time() * 1000)

        osm_client = OsmClient(ctx.get('url'),
                               ctx.get('username'),
                               ctx.get('password'),
                               ctx['parameters'].get('project_id'))

        res = osm_client.delete_instance(nsr_id=args.get('nsr_id'))

        if isinstance(res, OsmError):
            msg = 'An error has occurred while deleting NS.' \
                  ' OSM Client error: {}'.format(res.response.get('message'))
            logger.debug(msg)
            return AgentResponse(status='error',
                                 message=msg) \
                .response

        if res and res.get('code'):
            logger.debug('$$osm_agent|OSMAgent|delete_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
            return AgentResponse(status='error',
                                 message='An error has occurred while deleting NS. Error code: {}'
                                 .format(res.get('code'))).response

        retries = self.retries
        while retries > 0:
            nsrs = osm_client.get_nsrs(nsr_id=args.get('nsr_id'))

            if not nsrs:
                logger.debug(
                    '$$osm_agent|OSMAgent|delete_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='ok', message='deleted').response

            if len(nsrs) > 1:
                logger.debug(
                    '$$osm_agent|OSMAgent|delete_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='Multiple NSRs found.').response

            nsr = nsrs[0]

            if nsr.get('code') and nsr.get('code') == 'NOT_FOUND':
                logger.debug(
                    '$$osm_agent|OSMAgent|delete_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='ok', message='deleted').response
            if nsr.get('code') and nsr.get('code') != 'NOT_FOUND':
                logger.debug(
                    '$$osm_agent|OSMAgent|delete_instance||{}$$'.format(str(round(time.time() * 1000) - b_time)))
                return AgentResponse(status='error',
                                     message='An error has occurred while deleting NS. Delete failed') \
                    .response
            time.sleep(self.retires_interval)
            retries = retries - 1
