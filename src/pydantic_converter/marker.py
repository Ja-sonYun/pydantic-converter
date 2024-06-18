from typing import TypeVar

from pydantic import BaseModel

SCHEMA_KEY = "__REGISTERED_SCHEMA__"

_is_generation_context: bool = False


def set_generate_context() -> None:
    global _is_generation_context

    _is_generation_context = True


_MT = TypeVar("_MT", bound=BaseModel)


def schema(cls: type[_MT]) -> type[_MT]:
    global _is_generation_context

    if _is_generation_context is False:
        return cls

    setattr(cls, SCHEMA_KEY, True)

    return cls


def has_schema(cls: type[BaseModel]) -> bool:
    return getattr(cls, SCHEMA_KEY, False)
