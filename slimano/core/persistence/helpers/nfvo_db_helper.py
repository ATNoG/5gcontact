from persistence.helpers.db_helper import DbHelper
from persistence.models.nfvo import Nfvo


class NfvoDbHelper(DbHelper):

    def __init__(self, db_engine):
        super().__init__(db_engine)

    def get_nfvo(self, name):
        res = self.query([Nfvo], filters={'name': name})
        return res[0] if len(res) > 0 else None
