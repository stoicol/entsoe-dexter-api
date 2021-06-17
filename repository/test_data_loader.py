from unittest import TestCase
from sqlalchemy.orm import Session
import pandas as pd
from os import environ
from datetime import datetime, timedelta, date, timezone, time
from config import configs
from . import db_models
from . import database
from . import data_loader
from util.enum_types import DirectionType

class TestDataLoader(TestCase):

    engine = database.get_engine(configs.SQLALCHEMY_DATABASE_URL_TESTING)

    def setUp(self):
        db_models.Base.metadata.create_all(bind=self.engine)

        self.source = data_loader.RepositoryLoader(environ.get('SOURCE_API_KEY'), Session(bind=self.engine))

    def tearDown(self):
        db_models.Base.metadata.drop_all(self.engine)

    def test_get_valid_response(self):
        # here we use pandas because the entsoe-api expects pandas timestamps
        start = pd.Timestamp(year=2020, month=6, day=5, hour=14, tz='UTC')
        end = pd.Timestamp(year=2020, month=6, day=5, hour=17, tz='UTC')

        country_code_from = 'NL'
        country_code_to = 'DE'
        response = self.source.get_response(country_code_from, country_code_to, start, end)
        self.assertEqual(response.to_list(), [1598.0, 1726.0, 972.0])

    def test_get_db_flows(self):
        start = pd.Timestamp(year=2020, month=6, day=5, hour=22, tz='UTC')
        end = pd.Timestamp(year=2020, month=6, day=6, hour=2, tz='UTC')

        country_code_from = 'NL'
        country_code_to = 'DE'
        response = self.source.get_response(country_code_from, country_code_to, start, end)
        db_ready = self.source.get_db_flows(response, 'DE-NL', DirectionType.direct)
        expected = [
            db_models.DataLoad(country_pair_id='DE-NL', date=date(year=2020, month=6,day=5), flows=[
                db_models.Flow(hour=22, flow=0.0, direction=DirectionType.direct),
                db_models.Flow(hour=23, flow=0.0, direction=DirectionType.direct)
            ]),
            db_models.DataLoad(country_pair_id='DE-NL', date=date(year=2020, month=6, day=6), flows=[
                db_models.Flow(hour=0, flow=0.0, direction=DirectionType.direct),
                db_models.Flow(hour=1, flow=0.0, direction=DirectionType.direct)
            ])
        ]
        # equality by reference, test must be improved
        # self.assertEqual(db_ready, expected)

    def test_get_response_no_data(self):
        # here we use pandas because the entsoe-api expects pandas timestamps
        start = pd.Timestamp(year=2020, month=6, day=5, hour=14, tz='UTC')
        end = pd.Timestamp(year=2020, month=6, day=5, hour=17, tz='UTC')

        country_code_from = 'NO'
        country_code_to = 'DE'

        response = self.source.get_response(country_code_from, country_code_to, start, end)
        self.assertEqual(response, None)

    def test_get_timestamp_start(self):
        latest_timestamp_no_data = self.source.get_timestamp_start('DE-NL')
        expected = datetime.combine(datetime.now().date() - timedelta(configs.backfill_days),
                                    time(hour=1),
                                    timezone.utc)
        self.assertEqual(latest_timestamp_no_data, expected)

        # add new data
        self.source.db.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=date(2021, 6, 6), flows=[
                db_models.Flow(hour=20, flow=5.5, direction=db_models.DirectionType.direct),
                db_models.Flow(hour=20, flow=4.5, direction=db_models.DirectionType.opposite)
            ])
        ])
        self.source.db.commit()

        latest_timestamp = self.source.get_timestamp_start('DE-NL')
        self.assertEqual(latest_timestamp, datetime(year=2021, month=6, day=6, hour=21, tzinfo=timezone.utc))

    def test_get_timestamp_current(self):
        current = self.source.get_timestamp_current()
        print('')

    def test_get_country_pairs(self):
        countries = {
            'NL': ['BE', 'DK'],
            'DE': ['NL', 'AT']
        }
        country_pairs = self.source.get_country_pairs(countries)
        expected = ['AT-DE', 'BE-NL', 'DE-NL', 'DK-NL']
        self.assertEqual(country_pairs, expected)


