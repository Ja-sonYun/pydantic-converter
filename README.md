# pydantic-converter

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/pydantic-converter/0.1.4)](https://pypi.org/project/pydantic-converter/) [![PyPI version](https://badge.fury.io/py/pydantic-converter.svg)](https://badge.fury.io/py/pydantic-converter)

Convert pydantic models to other formats like typescript interfaces.

> [!WARNING]
> 
> If you're looking to convert FastAPI route definitions to TypeScript interfaces, try using [openapi-typescript](https://github.com/openapi-ts/openapi-typescript). You can easily achieve what you want by converting FastAPI's openapi.json to TypeScript interfaces.
> 

## Installation

```bash
pip install pydantic-converter
```

## Usage

You need to install [json-schema-to-typescript](https://github.com/bcherny/json-schema-to-typescript#readme) to use this tool.

```python
# tests/sample.py
from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel

from pydantic_converter.marker import schema


# Won't be exported since it doesn't have @schema decorator
class ModelImportedFromSomewhere(BaseModel):
    args: str


class Option(str, Enum):  # Enum as well
    A = "A"
    B = "B"


@schema  # Export from this schema
class Sample(BaseModel):
    name: str
    age: int
    option: Option

    imported: Sequence[ModelImportedFromSomewhere]
    # ModelImportedFromSomewhere doesn't have @schema decorator,
    # but since it is a member of Sample, it will be exported as well


@schema  # Export from this schema
class AnotherSample(BaseModel):
    name: str
    age: int
    is_active: bool  # Support camelCase conversion

    sample: Sample | None
```

```sh
$ pydantic-converter --help
NAME
    pydantic-converter

SYNOPSIS
    pydantic-converter PATH OUTPUT_FILE <flags>

POSITIONAL ARGUMENTS
    PATH
        Type: str | pathlib.Path
    OUTPUT_FILE
        Type: str | pathlib.Path

FLAGS
    -r, --recursive=RECURSIVE  # Search .py files recursively from the given path.
        Type: bool
        Default: False
    -c, --camelize=CAMELIZE  # Convert field names to camelCase.
        Type: bool
        Default: False
    -e, --export_to=EXPORT_TO
        Type: Literal
        Default: 'ts'

$ pydantic-converter ./tests ./tests/output.ts --camelize
```

```typescript
// tests/output.ts
export type __All = AnotherSample | Sample | ModelImportedFromSomewhere | Option;
export type Name = string;
export type Age = number;
export type IsActive = boolean;
export type Name1 = string;
export type Age1 = number;
export type Option = "A" | "B";  // Enum as well
export type Args = string;
export type Imported = ModelImportedFromSomewhere[];

export interface AnotherSample {
  name: Name;
  age: Age;
  isActive: IsActive; // Camelized
  sample: Sample | null;
}
export interface Sample {
  name: Name1;
  age: Age1;
  option: Option;
  imported: Imported;
}
export interface ModelImportedFromSomewhere {  // All valid schema will be exported by pydantic even without @schema decorator
  args: Args;
}
```

## TODO

- Support other language formats
- pytests
