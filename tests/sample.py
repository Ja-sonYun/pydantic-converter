from pydantic import BaseModel

from pydantic_converter.marker import schema


@schema
class Sample(BaseModel):
    name: str
    age: int


@schema
class AnotherSample(BaseModel):
    name: str
    age: int
    is_active: bool

    sample: Sample
