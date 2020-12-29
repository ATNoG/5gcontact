from persistence.helpers.db_helper import DbHelper
from persistence.models.nst import Nst


class NstDbHelper(DbHelper):

    def __init__(self, db_engine):
        super().__init__(db_engine)

    def get_nst(self, name):
        res = self.query([Nst], filters={'name': name})
        return res[0] if len(res) > 0 else None

    def get_nst_id(self, name):
        return self.get_nst(name).id


