from pydantic import BaseModel
from datetime import date
from util.enum_types import *
from typing import List

# pydantic models
# used to render the API responses

class Flow(BaseModel):
    hour: int
    flow: float

    class Config:
        orm_mode = True









