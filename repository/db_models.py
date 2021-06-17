from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import case
from util.enum_types import DirectionType

# SQLAlchemy database models

Base = declarative_base()

class DataLoad(Base):
    __tablename__ = "data_loads"

    # country_pair_ids are of the form DE-NL
    # for any 2 distinct country-ids, the country_pair_id is sorted lexicographically(i.e. unique)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    country_pair_id = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)

class Flow(Base):
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    load_id = Column(Integer, ForeignKey(DataLoad.id), nullable=False)
    hour = Column(Integer, index=True, nullable=False)
    flow = Column(Float, nullable=False)
    direction = Column(Enum(DirectionType), nullable=False)

    data_loads = relationship(DataLoad, backref='flows')

    @hybrid_property
    def signed_flow(self):
        if self.direction == DirectionType.direct:
            return self.flow
        else:
            return self.flow * -1

    @signed_flow.expression
    def signed_flow(cls):
        return case([
            (cls.direction == DirectionType.direct, cls.flow),
        ], else_=cls.flow * -1)