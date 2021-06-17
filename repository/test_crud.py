from unittest import TestCase
from sqlalchemy.orm import Session
from . import database
from . import db_models
from . import crud
from config import configs
from util.enum_types import DirectionType
import datetime

class TestModels(TestCase):

    engine = database.get_engine(configs.SQLALCHEMY_DATABASE_URL_TESTING)
    session = Session(bind=engine)

    def setUp(self):
        db_models.Base.metadata.create_all(bind=self.engine)
        self.session.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 4), flows=[
                db_models.Flow(hour=20, flow=5.5, direction=DirectionType.direct),
                db_models.Flow(hour=20, flow=4.5, direction=DirectionType.opposite)
            ]),
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 5))
        ])

        self.session.commit()

    def tearDown(self):
        db_models.Base.metadata.drop_all(self.engine)

    def test_netted_flows(self):
        query = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 4))
        self.assertEqual(query, [(20, 1.0)])

        query_inverse = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 4), multiplier=-1)
        self.assertEqual(query_inverse, [(20, -1.0)])

    def test_directed_flows(self):
        query = crud.get_directed_flows(self.session, 'DE-NL', datetime.date(2021, 6, 4), DirectionType.opposite)
        self.assertEqual(query, [(20, -4.5)])

    def test_empty_load(self):
        query_net = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 5))
        self.assertEqual(query_net, [])

        query_directed = crud.get_directed_flows(self.session, 'DE-NL', datetime.date(2021, 6, 5), DirectionType.opposite)
        self.assertEqual(query_directed, [])

    def test_unavailable_date(self):
        query = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 7))
        self.assertEqual(query, [])

    def test_ordered_by_hour(self):
        self.session.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 4), flows=[
                db_models.Flow(hour=19, flow=10.5, direction=DirectionType.direct),
                db_models.Flow(hour=19, flow=0, direction=DirectionType.opposite)
            ])
        ])

        self.session.commit()

        query = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 4))
        self.assertEqual(query, [(19, 10.5), (20, 1.0)])

    def test_latest_data_load(self):
        self.session.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 4), flows=[
                db_models.Flow(hour=18, flow=2.5, direction=DirectionType.direct),
                db_models.Flow(hour=18, flow=1, direction=DirectionType.opposite),
                db_models.Flow(hour=19, flow=10.5, direction=DirectionType.direct),
                db_models.Flow(hour=19, flow=0, direction=DirectionType.opposite),
                db_models.Flow(hour=21, flow=5.5, direction=DirectionType.direct),
                db_models.Flow(hour=21, flow=3.5, direction=DirectionType.opposite)
            ])
        ])

        self.session.commit()

        query_net = crud.get_net_flows(self.session, 'DE-NL', datetime.date(2021, 6, 4))
        self.assertEqual(query_net, [(18, 1.5), (19, 10.5), (20, 1.0), (21, 2.0)])

    def test_latest_hour(self):
        query_before = crud.get_latest_hour(self.session, 'DE-NL', datetime.date(2021, 6, 4))
        self.assertEqual(query_before, 20)

        self.session.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 4), flows=[
                db_models.Flow(hour=21, flow=2.5, direction=DirectionType.direct),
                db_models.Flow(hour=21, flow=1, direction=DirectionType.opposite)
            ])
        ])

        self.session.commit()

        query_after = crud.get_latest_hour(self.session, 'DE-NL', datetime.date(2021, 6, 4))
        self.assertEqual(query_after, 21)

    def test_latest_date(self):
        query_before = crud.get_latest_date(self.session, 'DE-NL')
        self.assertEqual(query_before, datetime.date(2021, 6, 5))

        self.session.add_all([
            db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 6))
        ])

        self.session.commit()

        query_after = crud.get_latest_date(self.session, 'DE-NL')
        self.assertEqual(query_after, datetime.date(2021, 6, 6))

    def test_write_data_load(self):
        crud.bulk_data_load(
            self.session,
            [db_models.DataLoad(country_pair_id='DE-NL', date=datetime.date(2021, 6, 6), flows=[
                db_models.Flow(hour=3, flow=18.0, direction=DirectionType.direct),
                db_models.Flow(hour=3, flow=13.7, direction=DirectionType.opposite)
            ])
        ])
        query = crud.get_latest_hour(self.session, 'DE-NL', datetime.date(2021, 6, 6))
        self.assertEqual(query, 3)





