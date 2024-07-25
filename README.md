# pydantic-converter

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/pydantic-converter/0.1.6)](https://pypi.org/project/pydantic-converter/) [![PyPI version](https://badge.fury.io/py/pydantic-converter.svg)](https://badge.fury.io/py/pydantic-converter)

Convert pydantic models to other formats like typescript interfaces.

## Installation

```bash
pip install pydantic-converter
```

## Usage

You need to install [json-schema-to-typescript](https://github.com/bcherny/json-schema-to-typescript#readme) to use this tool.

```python
from pydantic_converter import schema
from pydantic import BaseModel


@schema
class User(BaseModel):
    name: str
    age: int
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

$ pydantic-converter ./ ./output.ts
```

```typescript
export Name = string;
export Age = number;
export interface User {
  name: Name;
  age: Age;
}
```

## TODO

- Support other language formats
