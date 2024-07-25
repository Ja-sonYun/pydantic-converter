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


def ref_replacer(namespace: str, obj: Any) -> Any:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref":
                ref = value.split("/")[-1]
                obj[key] = f"#/definitions/{ref}"
            else:
                obj[key] = ref_replacer(namespace, value)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            obj[i] = ref_replacer(namespace, value)
    return obj


def refine_schemas(schemas: list[dict[str, Any]], do_camelize: bool = False) -> dict[str, Any]:
    # Filter duplicate schemas
    schemas = list({json.dumps(schema): schema for schema in schemas}.values())
    definitions: dict[str, Any] = {}

    parent_defs: set[str] = {schema["title"] for schema in schemas if "title" in schema}

    # First put parent schemas in the new schema
    for schema in schemas:
        if "title" in schema:
            definitions[schema["title"]] = schema

    # Find property defs and move them to parent schema
    child_defs: set[str] = set()
    for schema in schemas:
        if "$defs" in schema:
            for key, value in schema["$defs"].items():
                if key not in parent_defs:
                    child_defs.add(key)
                    definitions[key] = value

            del schema["$defs"]

    all_defs = parent_defs.union(child_defs)

    # Then rewrite the $deps path to definitions if it is parent schema
    for schema in definitions.values():
        if "properties" in schema:
            for prop in schema["properties"].values():
                ref = prop.get("$ref")
                if ref is not None and ref in all_defs:
                    prop["$ref"] = f"#/definitions/{ref}"

            ref_replacer(schema["title"], schema)

    if do_camelize:
        for schema in definitions.values():
            # Camelize properties
            if "properties" in schema:
                schema["properties"] = {
                    camelize(prop): prop_schema for prop, prop_schema in schema.get("properties", {}).items()
                }
            if "required" in schema:
                schema["required"] = [camelize(prop) for prop in schema["required"]]

    return {
        "definitions": definitions,
        "title": "__All",
        "description": "This is dummy value to make the root schema valid.",
        "oneOf": [{"$ref": f"#/definitions/{def_name}"} for def_name in all_defs],
    }


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

    schema = refine_schemas(schemas, camelize)
    generated_ts = convert_schema_to_ts(schema)

    banner = """\
// This file is auto-generated by pydantic-converter
// Do not modify this file manually
"""

    generated_content = banner + generated_ts
    output_file.write_text(generated_content)
