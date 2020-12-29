from nameko.rpc import rpc
from nameko import config
from sqlalchemy import create_engine

# Init DB mappers
from persistence.models import nssi as nssi_model
from persistence.models import coe as coe_model
from persistence.models import nsi as nsi_model
from persistence.models import nst as nst_model
from persistence.models import nfvo as nfvo_model

from persistence.helpers.db_helper import DbHelper
from persistence.helpers.nst_db_helper import NstDbHelper
from persistence.helpers.nsi_db_helper import NsiDbHelper

from engine.responses.base import EngineResponse

from engine.validations import EngineValidations

# slice orchestrator worker
from engine.s_orch.s_orch import SliceOrch

# Slice LCM
from engine.s_lcm.s_lcm import SliceLCM

import time
import sys
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class Engine:
    name = "engine"

    def __init__(self):
        # setup logging
        logging.basicConfig(stream=sys.stdout,
                            # filename=config.get('DEFAULT', 'log_file'),
                            level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

        self.db_engine = create_engine(config.get('db_connection'), connect_args={'connect_timeout': 60})
        DbHelper(self.db_engine).init_db()
        
        self.lcms = []
        self.s_orchs = []

    @rpc
    def create_nst(self, payload):
        logger.debug('"create_nst" Payload: {}'.format(payload))

        b_time = round(time.time() * 1000)

        # Persist template in database
        template = payload['slimano:nst']
        new_nst = nst_model.Nst(
            id=str(uuid.uuid4()),
            name=template['name'],
            template=json.dumps(template)
        )
        db_helper = DbHelper(self.db_engine)
        db_helper.insert(new_nst)

        logger.debug('$$core|Engine|create_nst||{}$$'.format(str(round(time.time() * 1000) - b_time)))

        return EngineResponse(status='ok', message='NST created').response

    @rpc
    def update_nst(self):
        # Update template in database

        pass

    @rpc
    def delete_nst(self):
        # Check if template is currently stored in database

        # Check if the template has an instance of it deployed

        # Remove template if there are no instances deployed
        pass

    @rpc
    def create_nsi(self, payload):
        logger.debug('"create_nsi" Payload: {}'.format(payload))
        b_time = round(time.time() * 1000)

        nsi = payload['slimano:nsi']
        # Check if there are resources available to deploy the requested NSI

        # Check if there are NSSI that this new NSI depends and whether they are currently deployed or not. If they are
        # currently deployed and can be shared, associate this new NSI to them. Else deploy new NSIs (NSSI) to fulfill
        # the necessary template and SLA requirements.

        # validate if all parameters are in NSI payload in order to proceed with slice deploy
        nst = NstDbHelper(self.db_engine).get_nst(nsi.get('nst-name'))

        if not nst:
            return EngineResponse(status='error', message='NST corresponding to the NSI not found').response

        template = json.loads(nst.template)
        res = EngineValidations.check_nsi_with_nst(nsi, template)

        if res is not None:
            return res.response
        # Request NSI deploy by creating a new worker in slice orchestration
        so = SliceOrch(len(self.s_orchs), self.db_engine, template, nsi, config)
        self.s_orchs.append(so)
        so.start()

        # TODO: Create a LCM worker in order to keep track of the newly created slice
        logger.debug('$$core|Engine|create_nsi||{}$$'.format(str(round(time.time() * 1000) - b_time)))

        return EngineResponse(status='ok', message='NSI instantiation started').response

    @rpc
    def get_nsi(self, nsi_id):
        # get NSI from database
        nsi = NsiDbHelper(self.db_engine).get_nsi_dict(id=nsi_id)

        if not nsi:
            return EngineResponse(status='error', message='NSI not found').response

        return nsi

    @rpc
    def update_nsi(self):
        # Check if new requirements can be meet with the current resources available

        # Update slice by issuing the correspondent LCM worker
        pass

    @rpc
    def delete_nsi(self, nsi_id):
        b_time = round(time.time() * 1000)

        # get nsi from database
        nsi = NsiDbHelper(self.db_engine).get_nsi_dict(id=nsi_id)

        if not nsi:
            return EngineResponse(status='error', message='NSI not found').response

        nsi = nsi['slimano:nsi']

        nst = NstDbHelper(self.db_engine).get_nst(nsi.get('nst-name'))

        if not nst:
            return EngineResponse(status='error', message='NST corresponding to the NSI not found').response

        template = json.loads(nst.template)

        # Signal the correspondent LCM worker the intention of the NSI
        s_lcm = SliceLCM(len(self.lcms), self.db_engine, config, 'delete', template, nsi)
        self.lcms.append(s_lcm)
        s_lcm.start()

        logger.debug('$$core|Engine|delete_nsi||{}$$'.format(str(round(time.time() * 1000) - b_time)))

        return EngineResponse(status='ok', message='NSI delete started').response

    @rpc
    def create_nfvo(self, payload):
        logger.debug('"create_nfvo" Payload: {}'.format(payload))

        nfvo_payload = payload['slimano:nfvo']
        new_nfvo = nfvo_model.Nfvo(id=str(uuid.uuid4()),
                                   name=nfvo_payload['name'],
                                   type=nfvo_payload['type'],
                                   url=nfvo_payload['url'],
                                   username=nfvo_payload['auth']['username'],
                                   password=nfvo_payload['auth']['password'],
                                   parameters=json.dumps({'project_id': nfvo_payload['auth']['project_id']}))
        db_helper = DbHelper(self.db_engine)
        db_helper.insert(new_nfvo)
        return EngineResponse(status='ok', message='NFVO created').response
