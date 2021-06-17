from unittest import TestCase
from . import utils
from repository import pydantic_models

class TestUtils(TestCase):

    def test_country_pair_id(self):
        pair_id = utils.get_country_pair_id('RO', 'NL')
        self.assertEqual(pair_id, 'NL-RO')

    def test_get_tuple_list_as_object_list(self):
        data = [(1,10.0), (2, -2.0)]
        object_list = utils.get_tuple_list_as_object_list(data)
        self.assertEqual(object_list, [pydantic_models.Flow(hour=1, flow=10.0), pydantic_models.Flow(hour=2, flow=-2.0)])