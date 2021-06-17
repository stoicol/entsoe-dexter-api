from sqlalchemy import func
from sqlalchemy.orm import Session
from repository import db_models
from util.enum_types import DirectionType
import datetime
from typing import List, Dict

# reusable functions to interact with the data in the database

def get_base_daily_flows(db: Session, pair_id: str, ref_date: datetime.date):
    return db.query(
        db_models.Flow.hour,
        db_models.Flow.direction,
        func.max(db_models.Flow.signed_flow).label('signed_flow'),
        func.max(db_models.Flow.load_id).label('load_id')
    ).join(db_models.Flow.data_loads
    ).filter(db_models.DataLoad.country_pair_id == pair_id, db_models.DataLoad.date == ref_date
    ).group_by(db_models.Flow.hour, db_models.Flow.direction)

def get_net_flows(db: Session, pair_id: str, ref_date: datetime.date, multiplier: int = 1):
    base_query = get_base_daily_flows(db, pair_id, ref_date).subquery()
    return db.query(
        base_query.c.hour,
        func.sum(base_query.c.signed_flow).label('net_flow') * multiplier
    ).group_by(base_query.c.hour).all()

def get_directed_flows(db: Session, pair_id: str, ref_date: datetime.date, direction: DirectionType):
    base_query = get_base_daily_flows(db, pair_id, ref_date).subquery()
    return db.query(
        base_query.c.hour,
        base_query.c.signed_flow
    ).filter(base_query.c.direction == direction).all()

def get_latest_hour(db: Session, pair_id: str, ref_date: datetime.date):
    base_query = get_base_daily_flows(db, pair_id, ref_date).subquery()
    return db.query(
        func.max(base_query.c.hour)).first()[0]

def get_latest_date(db: Session, pair_id: str):
    return db.query(
        func.max(db_models.DataLoad.date)
    ).filter(db_models.DataLoad.country_pair_id == pair_id).first()[0]

def bulk_data_load(db: Session, loads: List[db_models.DataLoad]):
    db.add_all(loads)
    db.commit()




