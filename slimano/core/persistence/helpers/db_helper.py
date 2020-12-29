from sqlalchemy.orm import sessionmaker
from persistence.models.models_base import Base


class DbHelper:

    def __init__(self, db_engine):
        self.db_engine = db_engine

    def init_db(self):
        # create database tables
        conn = self.db_engine.connect()
        metadata = Base.metadata
        metadata.create_all(conn)
        conn.close()
        self.db_engine.dispose()

    def insert(self, obj):
        session = self.get_db_session()
        try:
            obj = session.merge(obj)
            if obj is list:
                session.add_all(obj)
            else:
                session.add(obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, obj):
        session = self.get_db_session()
        try:
            if obj is list:
                for u_obj in obj:
                    session.delete(u_obj)
            else:
                session.delete(obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_db_session(self):
        Session = sessionmaker(bind=self.db_engine)
        return Session()

    def query(self, attributes, filters=None, order_by=None, session=None):
        if not session:
            session_in = self.get_db_session()
        else:
            session_in = session
        if order_by and not filters:
            res = session_in.query(*attributes).order_by(**order_by).all()
        elif order_by and filters:
            res = session_in.query(*attributes).filter_by(**filters).order_by(**order_by).all()
        elif not order_by and filters:
            res = session_in.query(*attributes).filter_by(**filters).all()
        else:
            res = session_in.query(*attributes).all()
        if not session:
            session_in.close()
        return res
