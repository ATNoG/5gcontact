from persistence.models.models_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Table


nsi_nssi_assoc_table = Table('nsi_nssi_assoc', Base.metadata,
                             Column('nsi_id', String(40), ForeignKey('nsi.id')),
                             Column('nssi_id', String(40), ForeignKey('nssi.id')))


class Nsi(Base):
    __tablename__ = 'nsi'

    id = Column(String(40), primary_key=True)
    name = Column(String(16))
    nst_name = Column(String(16))
    status = Column(String(500))

    nst_id = Column(String(40), ForeignKey('nst.id'))

    nssis = relationship('Nssi',
                         secondary=nsi_nssi_assoc_table,
                         backref='nsis',
                         lazy='subquery',
                         cascade='all, delete-orphan',
                         single_parent=True)

    # nfs = relationship('Nf',
    #                    back_populates='nsi')
