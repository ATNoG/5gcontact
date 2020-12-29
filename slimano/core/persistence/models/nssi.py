from persistence.models.models_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Nssi(Base):
    __tablename__ = 'nssi'

    id = Column(String(40), primary_key=True)
    name = Column(String(16))
    template_name = Column(String(16))
    shared = Column(Boolean)
    location = Column(String(50))
    inputs = Column(String(10000))
    outputs = Column(String(10000))

    nfvo_id = Column(String(40), ForeignKey('nfvo.id'))
    nfvo = relationship("Nfvo", back_populates='nssi', lazy='subquery')

    coe_id = Column(String(40), ForeignKey('coe.id'))
    coe = relationship("Coe", back_populates='nssi', lazy='subquery')

    # nsi_id = Column(Integer, ForeignKey('nsi.id'))
    # nsi = relationship('Nsi', uselist=False, back_populates='nsis')

