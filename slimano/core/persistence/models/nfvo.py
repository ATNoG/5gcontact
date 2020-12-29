from persistence.models.models_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String


class Nfvo(Base):
    __tablename__ = 'nfvo'

    id = Column(String(40), primary_key=True)
    name = Column(String(16))
    type = Column(String(16))
    url = Column(String(100))

    #auth
    username = Column(String(16))
    password = Column(String(16))

    parameters = Column(String(255))

    nssi = relationship('Nssi', back_populates='nfvo', uselist=False, lazy='subquery')

