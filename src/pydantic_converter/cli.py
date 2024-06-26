import importlib
import json
import shutil
import sys
import tempfile
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from subprocess import run
from typing import Any, Literal
from uuid import uuid4

from humps import camelize
from pydantic import BaseModel
from rich import print

from pydantic_converter.marker import has_schema, set_generate_context


def import_module(file: Path) -> Any:
    if file.suffix == ".py":
        name = uuid4().hex
        spec = spec_from_file_location(name, file, submodule_search_locations=[])
        assert spec is not None and spec.loader is not None
        module = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    else:
        return importlib.import_module(str(file))


def get_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()


def find_schema_marker_in_file(file: Path) -> Sequence[type[BaseModel]]:
    registered_models: list[type[BaseModel]] = []

    if file.suffix != ".py":
        return []

    module = import_module(file)
    global_vars = vars(module)
    for var in global_vars.values():
        if isinstance(var, type) and issubclass(var, BaseModel) and has_schema(var):
            registered_models.append(var)

    return registered_models


def convert_schema_to_ts(schema: dict[str, Any]) -> str:
    package, exec = ["json-schema-to-typescript", "json2ts"]

    if shutil.which(exec) is None:
        raise FileNotFoundError(f"{package} is not installed. " f"Please install it using `npm install -g {package}`.")

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(schema, f)
        f.flush()

        result = run(
            [
                exec,
                f.name,
                "--bannerComment",  # Hide the banner comment
                "--additionalProperties",
                "false",
                "--unknownAny",
                "true",
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        generated_ts = result.stdout

    return generated_ts


def clean_schemas(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Filter duplicate schemas
    schemas = list({json.dumps(schema): schema for schema in schemas}.values())

    print(f"Total schemas: {len(schemas)}")

    once_referenced = set[str]()

    # Remove name of all the properties to prevent name conflicts
    for schema in schemas:
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
            ref = prop.get("$ref")
            if ref is not None:
                if ref not in once_referenced:
                    once_referenced.add(ref)
                else:
                    prop.pop("$ref", None)
        for prop in schema.get("$defs", {}).values():
            proped = prop.get("properties", {}).values()
            for prop in proped:
                prop.pop("title", None)
                ref = prop.get("$ref")
                if ref is not None:
                    if ref not in once_referenced:
                        once_referenced.add(ref)
                    else:
                        prop.pop("$ref", None)

    return schemas


def refine_schema(
    schema: dict[str, Any],
    do_camelize: bool = False,
) -> dict[str, Any]:
    # Rename properties to camelCase
    if do_camelize:
        schema["properties"] = {
            camelize(prop): prop_schema for prop, prop_schema in schema.get("properties", {}).items()
        }
    return schema


def main(
    path: str | Path,
    output_file: str | Path,
    recursive: bool = False,
    camelize: bool = False,
    export_to: Literal["ts"] = "ts",
) -> None:
    set_generate_context()

    # TODO: Support multiple output formats
    del export_to

    path = Path(path)
    output_file = Path(output_file)

    files: list[Path]
    # Recursively find all files in the given path
    if path.is_dir():
        files = list(path.rglob("*.py") if recursive else path.glob("*.py"))
    else:
        files = [path]

    schemas: list[dict[str, Any]] = []

    for file in files:
        schemas.extend(get_json_schema(model) for model in find_schema_marker_in_file(file))

    if not schemas:
        print("No schemas found")
        return

    schemas = clean_schemas(schemas)
    schemas = [refine_schema(schema, do_camelize=camelize) for schema in schemas]

    generated_ts: list[str] = []
    for schema in schemas:
        generated_ts.append(convert_schema_to_ts(schema))

    banner = [
        "// This file is auto-generated by pydantic-converter",
        "// Do not modify this file manually",
    ]

    generated_content = "\n".join(banner + generated_ts)
    output_file.write_text(generated_content)
