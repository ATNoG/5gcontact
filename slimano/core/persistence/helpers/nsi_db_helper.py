import logging
import json
import uuid

from persistence.helpers.db_helper import DbHelper
from persistence.helpers.nssi_db_helper import NssiDbHelper
from persistence.helpers.nst_db_helper import NstDbHelper
from persistence.helpers.nfvo_db_helper import NfvoDbHelper
from persistence.models.nsi import Nsi
from persistence.models.nssi import Nssi

logger = logging.getLogger(__name__)


class NsiDbHelper(DbHelper):

    def __init__(self, db_engine):
        super().__init__(db_engine)
        self.db_engine = db_engine

    def insert_nsi(self, nsi_dict):

        nst = NstDbHelper(self.db_engine).get_nst(nsi_dict.get('nst-name'))
        logger.debug('"insert_nsi": nst_id: {}, nsi_dict: {}'.format(nst.id, nsi_dict))
        nsi_id = str(uuid.uuid4())
        nsi_db_obj = Nsi(
            id=nsi_id,
            name=nsi_dict.get('name'),
            nst_id=nst.id,
            nst_name=nsi_dict.get('nst-name'),
            status=json.dumps(nsi_dict.get('status'))
        )

        for nssi in nsi_dict.get('nss-instances', []):
            nssi_db_obj = Nssi(
                id=str(uuid.uuid4()),
                name=nssi.get('name'),
                template_name=nssi.get('template-name'),
                shared=True,
                location=nssi.get('location'),
                inputs=json.dumps(nssi['instantiation'].get('inputs', {})),
                outputs=json.dumps(nssi['instantiation'].get('outputs', {}))
            )

            for template in json.loads(nst.template).get('nss-templates', []):
                if template.get('template-name') == nssi.get('template-name'):
                    if template.get('type') == 'nfvo':
                        nfvo_db_helper = NfvoDbHelper(self.db_engine)
                        nssi_db_obj.nfvo = nfvo_db_helper.get_nfvo(template.get('nfvo-name'))
                    if template.get('type') == 'coe':
                        pass

            nsi_db_obj.nssis.append(nssi_db_obj)

        self.insert(nsi_db_obj)
        return nsi_id

    def update_nsi(self, nsi_dict):
        session = self.get_db_session()
        nsi = self.get_nsi(id=nsi_dict.get('id'), session=session)
        if not nsi:
            return False

        nsi.name = nsi_dict.get('name')
        nsi.status = nsi_dict.get('status')
        session.commit()
        session.close()

    def delete_nsi(self, name=None, id=None):
        if not name and not id:
            return False

        nsi = self.get_nsi(name, id)
        if not nsi:
            return False

        self.delete(nsi)
        return True

    def get_nsi(self, name=None, id=None, session=None):
        if name:
            res = self.query([Nsi], filters={'name': name}, session=session)
            return res[0] if len(res) > 0 else None
        elif id:
            res = self.query([Nsi], filters={'id': id}, session=session)
            return res[0] if len(res) > 0 else None
        else:
            res = self.query([Nsi], session=session)
            return res if len(res) > 0 else None

    def get_nsi_dict(self, name=None, id=None, session=None):
        nsis = self.get_nsi(name, id, session)

        if not nsis:
            return None

        if nsis is not list:
            return NsiDbHelper._nsi_dict(nsis)
        else:
            return [NsiDbHelper._nsi_dict(nsi) for nsi in nsis]

    @staticmethod
    def _nsi_dict(nsi):
        return {
            'slimano:nsi': {
                'id': nsi.id,
                'name': nsi.name,
                'nst-name': nsi.nst_name,
                'dependencies': [],
                'actions': [],
                'nss-instances': [NssiDbHelper.get_nssi_dict_from_object(nssi) for nssi in nsi.nssis],
                'sdn-apps': [],
                'connections': [],
                'status': nsi.status
            }
        }
