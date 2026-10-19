"""Deterministic schema export, with strict comparison mode for CI."""
import argparse
import json
from pathlib import Path
from stellar_catalog.app import app as catalog
from stellar_journey.app import app as journey
from schema_models import Release, PhaseReport

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    documents = {"catalog.openapi.json": catalog.openapi(), "journey.openapi.json": journey.openapi(),
                 "release.schema.json": Release.model_json_schema(), "phase-report.schema.json": PhaseReport.model_json_schema()}
    for name in ("catalog.openapi.json", "journey.openapi.json"):
        document = documents[name]
        document["x-max-body-bytes"] = 4096
        document["x-timestamp-format"] = "UTC RFC3339"
        for operations in document["paths"].values():
            for operation in operations.values():
                operation.setdefault("parameters", []).append({"in": "header", "name": "X-Request-ID", "required": False,
                    "description": "Propagated internal ID. Invalid or overlong values replaced; gateway generates public IDs.",
                    "schema": {"type": "string", "maxLength": 64, "pattern": "^[A-Za-z0-9._-]+$"}, "example": "contract-example-1"})
                for response in operation["responses"].values():
                    response.setdefault("headers", {})["X-Request-ID"] = {"schema": {"type": "string", "maxLength": 64}}
    mismatches = []
    for name, document in documents.items():
        if name.endswith(".schema.json"):
            document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        text = json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n"
        target = ROOT / "contracts" / name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                mismatches.append(name)
        else:
            target.write_text(text, encoding="utf-8", newline="\n")
    if mismatches:
        raise SystemExit("Contract drift: " + ", ".join(mismatches))


if __name__ == "__main__":
    main()
