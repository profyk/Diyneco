"""Write the API's OpenAPI document to packages/shared-types/openapi.json without a database.

uv run python scripts/export_openapi.py [output path]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Building the schema needs settings but no connection; placeholders are fine here.
_PLACEHOLDERS = {
    "APP_ENV": "development",
    "API_BASE_URL": "http://localhost:8000",
    "DATABASE_URL": "postgresql+asyncpg://openapi:openapi@localhost:5432/openapi",
    "PAIRING_CODE_PEPPER": "openapi-export",
    "KMS_MASTER_KEY_ID": "openapi-export",
    "KMS_PROVIDER": "local",
    "KMS_LOCAL_MASTER_KEY": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
}


def main() -> int:
    if not os.environ.get("JWT_SIGNING_KEYS_JSON") and not (ROOT / ".env").exists():
        from scripts.gen_dev_keys import ed25519_jwk

        os.environ["JWT_SIGNING_KEYS_JSON"] = json.dumps({"keys": [ed25519_jwk("openapi")]})
        os.environ["JWT_ACTIVE_KID"] = "openapi"
        for k, v in _PLACEHOLDERS.items():
            os.environ.setdefault(k, v)
    from app.main import create_app

    out = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "packages" / "shared-types" / "openapi.json"
    )
    out.write_text(json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
