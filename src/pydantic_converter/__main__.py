from fire import Fire  # type: ignore

from pydantic_converter.cli import main


def run() -> None:
    Fire(main)
