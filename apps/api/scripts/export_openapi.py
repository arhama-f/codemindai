"""Exports the FastAPI app's OpenAPI schema to packages/api-client/openapi.json
so the frontend's TypeScript client can be regenerated from it."""

import json
from pathlib import Path

from codemind_api.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "packages" / "api-client" / "openapi.json"


def main() -> None:
    app = create_app()
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote OpenAPI schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
