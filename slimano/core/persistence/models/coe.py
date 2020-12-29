from persistence.models.models_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String


class Coe(Base):
    __tablename__ = 'coe'

    id = Column(String(40), primary_key=True)
    name = Column(String(16))
    type = Column(String(16))

    nssi = relationship('Nssi', back_populates='coe', uselist=False)

