"""Print fresh development secrets as .env lines: an Ed25519 JWK set, the pairing pepper and
a local KMS master key. For development and CI only; production secrets come from the
hosting provider's secret manager.

    uv run python scripts/gen_dev_keys.py >> .env
"""

from __future__ import annotations

import base64
import json
import secrets

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def ed25519_jwk(kid: str) -> dict[str, str]:
    key = Ed25519PrivateKey.generate()
    d = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    x = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return {"kty": "OKP", "crv": "Ed25519", "kid": kid, "alg": "EdDSA", "d": _b64url(d), "x": _b64url(x)}


def main() -> None:
    kid = f"dev-{secrets.token_hex(4)}"
    print(f"JWT_SIGNING_KEYS_JSON='{json.dumps({'keys': [ed25519_jwk(kid)]}, separators=(',', ':'))}'")
    print(f"JWT_ACTIVE_KID={kid}")
    print(f"PAIRING_CODE_PEPPER={secrets.token_urlsafe(32)}")
    print("KMS_MASTER_KEY_ID=local-dev")
    print("KMS_PROVIDER=local")
    print(f"KMS_LOCAL_MASTER_KEY={base64.b64encode(secrets.token_bytes(32)).decode()}")


if __name__ == "__main__":
    main()
