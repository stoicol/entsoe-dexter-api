from repository import pydantic_models


def get_country_pair_id(country_code1: str, country_code2: str):
    tuple = (country_code1, country_code2)
    return '-'.join(sorted(tuple))

def get_tuple_list_as_object_list(data):
    return [pydantic_models.Flow(hour=x[0], flow=x[1]) for x in data]