from entsoe import EntsoePandasClient
from entsoe.exceptions import *
from sqlalchemy.orm import Session
import pandas as pd
from repository import crud
from config import configs
from repository import db_models
from util.enum_types import DirectionType
from util import utils
from datetime import datetime, timedelta, time, timezone
import logging

logger = logging.getLogger(__name__)

class RepositoryLoader:
    def __init__(self, api_key: str, db: Session):
        self.client = EntsoePandasClient(api_key)
        self.db = db

    def load(self):
        timestamp_stop = pd.to_datetime(self.get_timestamp_current())
        country_pairs = self.get_country_pairs(configs.countries)

        for country_pair in country_pairs:
            timestamp_start = pd.to_datetime(self.get_timestamp_start(country_pair))
            country_codes = country_pair.split('-')
            direct_flows = self.get_response(country_codes[0], country_codes[1], timestamp_start, timestamp_stop)
            opposite_flows = self.get_response(country_codes[1], country_codes[0], timestamp_start, timestamp_stop)

            logger.info(f'Start database load for country pair {country_pair} from {timestamp_start} to {timestamp_stop}')

            if direct_flows is not None and opposite_flows is not None:
                direct_loads = self.get_db_flows(direct_flows, country_pair, DirectionType.direct)
                opposite_loads = self.get_db_flows(opposite_flows, country_pair, DirectionType.opposite)
                try:
                    crud.bulk_data_load(
                        db=self.db,
                        loads=direct_loads
                    )

                    crud.bulk_data_load(
                        db=self.db,
                        loads=opposite_loads
                    )

                    logger.info(f'Successful database load for country pair {country_pair} from {timestamp_start} to {timestamp_stop}')
                except:
                    logger.warning(f'Database Load for country pair {country_pair} from {timestamp_start} to {timestamp_stop} failed at database update')
            else:
                logger.info(f'No new data found for country pair {country_pair} from {timestamp_start} to {timestamp_stop}')

    def get_response(self,
                     country_code_from,
                     country_code_to,
                     timestamp_start,
                     timestamp_end):
        logger.info(f'Query entsoe-api for cross-border flows from {country_code_from} to {country_code_to.format()}, '
                     f'start {timestamp_start.strftime("%Y%m%dT%H:%M")} end {timestamp_end.strftime("%Y%m%dT%H:%M")}')
        try:
            return self.client.query_crossborder_flows(country_code_from,
                                                        country_code_to,
                                                        start=timestamp_start,
                                                        end=timestamp_end)
        except IndexError:
            logger.warning(f'Country pair not found: from {country_code_from} to {country_code_to}')
        except Exception as e:
            logger.warning(str(e))

    def get_timestamp_start(self, pair_id):
        # default: beginning of day
        latest_hour = 0
        latest_date = crud.get_latest_date(self.db, pair_id)
        if latest_date is None:
            # no data yet for this pair_id
            # start to backfill
            latest_date = datetime.now().date() - timedelta(configs.backfill_days)
        else:
            latest_hour = crud.get_latest_hour(self.db, pair_id, latest_date)
            # edge case
            if latest_hour is None:
                latest_hour = 0
        # we increment the latest upload timestamp by one hour
        return datetime.combine(latest_date, time(hour=latest_hour), timezone.utc) + timedelta(hours=1)

    def get_timestamp_current(self):
        dt = datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc, minute=0, second=0, microsecond=0)
        return utc_time

    def get_country_pairs(self, countries):
        duplicated = [utils.get_country_pair_id(item[0] , neighbour) for item in countries.items() for neighbour in item[1]]
        return sorted(list(dict.fromkeys(duplicated)))

    def get_db_flows(self, response_flows, country_pair, direction: DirectionType):
        dates = {}
        for row in response_flows.items():
            # the entsoe-py-api returns local timezone in the country_from timezone
            utc_dt = row[0].astimezone(timezone.utc)
            date_part = utc_dt.date()
            if date_part not in dates:
                dates[date_part] = db_models.DataLoad(date=date_part, country_pair_id=country_pair, flows=[])
            dates[date_part].flows.append(db_models.Flow(hour=utc_dt.hour, flow=row[1], direction=direction))
        return list(dates.values())

