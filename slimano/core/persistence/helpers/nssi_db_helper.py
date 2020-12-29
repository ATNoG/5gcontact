import json

from persistence.helpers.db_helper import DbHelper
from persistence.models.nssi import Nssi


class NssiDbHelper(DbHelper):

    def __init__(self, db_engine):
        super().__init__(db_engine)

    def insert_nssi(self, nssi_dict):
        new_nssi = Nssi(
            name=nssi_dict.get('name'),
            template_name=nssi_dict.get('template-name'),
            location=nssi_dict.get('location'),
            inputs=nssi_dict['instantiation'].get('inputs', {}),
            outputs=nssi_dict['instantiation'].get('outputs', {})
        )
        self.insert(new_nssi)

    def get_nssi(self, name):
        res = self.query([Nssi], filters={'name': name})
        return res[0] if len(res) > 0 else None

    def get_nssi_dict(self, name):
        nssi = self.get_nssi(name)

        if not nssi:
            return None

        return self.get_nssi_dict_from_object(nssi)

    @staticmethod
    def get_nssi_dict_from_object(nssi):
        return {
            'name': nssi.name,
            'template-name': nssi.template_name,
            'location': nssi.location,
            'instantiation': {
                'inputs': json.loads(nssi.inputs),
                'outputs': json.loads(nssi.outputs)
            },
            'dependencies': []
        }
