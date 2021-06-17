from enum import Enum

# By inheriting from str, the FastAPI docs will be able to know that the values must be of type string and will be able to render correctly
# https://fastapi.tiangolo.com/tutorial/path-params/#create-an-enum-class

class DirectionType(str, Enum):
    direct = "direct"
    opposite = "opposite"

class FlowType(str, Enum):
    net = 'net'
    directed = 'directed'

class CountryType(str, Enum):
    NL = 'NL'
    DE = 'DE'
    BE = 'BE'
    UK = 'UK'
    NO = 'NO'
    DK = 'DK'
    AT = 'AT'
    FR = 'FR'
    LU = 'LU'
    PL = 'PL'
    SE = 'SE'
    CH = 'CH'