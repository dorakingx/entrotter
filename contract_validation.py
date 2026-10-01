"""Offline wire-shape validation; engine semantics and hashes are separate."""

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMAS = Path(__file__).resolve().parent / "schemas"
BASE = "https://entrotter.github.io/schemas/"
KINDS = ("scenario", "result", "agent-recording", "trace-plan", "trace-result")


def validator(kind: str, schema_dir: Path = SCHEMAS) -> Draft202012Validator:
    """Load all bundled schemas and bind relative references to a fixed base URI."""
    if kind not in KINDS:
        raise ValueError("Unknown contract kind")
    # An explicit empty Registry refuses unknown resources by default.
    # Never use jsonschema's implicit registry or add an HTTP/file retriever.
    registry: Registry[Any] = Registry()
    for name in KINDS:
        filename = f"{name}.v0.1.schema.json"
        schema = json.loads((schema_dir / filename).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(
            BASE + filename, Resource.from_contents(schema)
        )
    return Draft202012Validator(
        {"$ref": BASE + f"{kind}.v0.1.schema.json"}, registry=registry
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=KINDS, default="scenario")
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Local JSON files to validate"
    )
    args = parser.parse_args()
    check = validator(args.kind)
    for path in args.paths:
        check.validate(json.loads(path.read_text(encoding="utf-8")))
        print(f"Valid {args.kind} wire shape: {path}")


if __name__ == "__main__":
    main()
