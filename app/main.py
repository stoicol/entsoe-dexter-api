import random
import string
import time
from os import path, environ
import logging.config
import datetime
from typing import Optional, List
from urllib.request import Request

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from repository import crud, db_models, pydantic_models, data_loader, database
from config import configs
from util import enum_types, utils

from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# setup loggers
log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)

logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

# setup database connection
engine = database.get_engine(configs.SQLALCHEMY_DATABASE_URL)
db_models.Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_key = environ.get('SOURCE_API_KEY')
if api_key is None:
    raise RuntimeError('The entsoe api-key must be provided, abort starting the service')

# setup data load scheduler
def schedule_data_loads():
    loader = data_loader.RepositoryLoader(api_key, Session(bind=engine))
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(loader.load, 'interval', hours=1, id='entsoe-upload', next_run_time=datetime.datetime.now())

@app.on_event('startup')
async def startup_event():
    schedule_data_loads()


@app.get("/flows/{flow_type}", response_model=List[pydantic_models.Flow])
async def get_flows(flow_type: enum_types.FlowType,
                    country_from: enum_types.CountryType,
                    country_to: enum_types.CountryType,
                    date: datetime.date,
                    db: Session = Depends(get_db)):
    data = []
    if country_from == country_to:
        raise HTTPException(status_code=400, detail="The country codes must be distinct")

    # the pair_id is lexicographically sorted
    # the multiplier reflects the direction requested by the user
    pair_id = utils.get_country_pair_id(country_from, country_to)
    multiplier = 1
    if pair_id != f'{country_from}-{country_to}':
        multiplier = -1

    if flow_type == enum_types.FlowType.net:
        data = crud.get_net_flows(pair_id=pair_id, ref_date=date, db=db, multiplier=multiplier)

    if flow_type == enum_types.FlowType.directed:
        direction = enum_types.DirectionType.direct
        if multiplier == -1:
            direction = enum_types.DirectionType.opposite
        data = crud.get_directed_flows(pair_id=pair_id, ref_date=date, direction=direction, db=db)

    return utils.get_tuple_list_as_object_list(data)
