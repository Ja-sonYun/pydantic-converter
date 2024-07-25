from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel

from pydantic_converter.marker import schema


class ModelImportedFromSomewhere(BaseModel):
    args: str


class Option(str, Enum):
    A = "A"
    B = "B"


@schema
class Sample(BaseModel):
    name: str
    age: int
    option: Option

    imported: Sequence[ModelImportedFromSomewhere]


@schema
class AnotherSample(BaseModel):
    name: str
    age: int
    is_active: bool

    sample: Sample | None
