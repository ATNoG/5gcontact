from persistence.models.models_base import Base
from sqlalchemy import Column, Integer, String


class Nst(Base):
    __tablename__ = 'nst'

    id = Column(String(40), primary_key=True)
    name = Column(String(16))
    template = Column(String(10000))

