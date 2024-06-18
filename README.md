# pydantic-converter

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
pydantic-converter ./ ./output.ts
```

```typescript
export interface User {
  name: string;
  age: number;
}
```
