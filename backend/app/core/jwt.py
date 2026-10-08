"""EdDSA (Ed25519) JWTs with `kid` for rotation.

JWT_SIGNING_KEYS_JSON holds a JWK set with the current and previous private keys; tokens are
signed with JWT_ACTIVE_KID and verified with whichever key their `kid` names. A `typ` claim
keeps token kinds apart, so a step-up or MFA token can never be used as an access token.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Literal

import jwt as pyjwt
from jwt import PyJWK

from app.core.errors import AppError

TokenType = Literal["access", "step_up", "mfa_pending"]
AUDIENCE = "diyneco-api"

ACCESS_TTL_S = 15 * 60
STEP_UP_TTL_S = 5 * 60
MFA_PENDING_TTL_S = 5 * 60


@dataclass(frozen=True)
class JwtKeys:
    active_kid: str
    keys: dict[str, PyJWK]
    issuer: str

    @classmethod
    def from_config(cls, keys_json: str, active_kid: str, issuer: str) -> JwtKeys:
        parsed: dict[str, PyJWK] = {}
        for jwk in json.loads(keys_json)["keys"]:
            if jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519":
                raise ValueError("JWT signing keys must be Ed25519 (kty OKP, crv Ed25519)")
            parsed[jwk["kid"]] = PyJWK.from_dict(jwk, algorithm="EdDSA")
        if active_kid not in parsed:
            raise ValueError("JWT_ACTIVE_KID not in key set")
        return cls(active_kid=active_kid, keys=parsed, issuer=issuer)

    def sign(self, typ: TokenType, claims: dict[str, Any], ttl_s: int) -> tuple[str, int]:
        now = int(time.time())
        exp = now + ttl_s
        payload = {**claims, "typ": typ, "iat": now, "exp": exp, "iss": self.issuer, "aud": AUDIENCE}
        token = pyjwt.encode(
            payload, self.keys[self.active_kid].key, algorithm="EdDSA", headers={"kid": self.active_kid}
        )
        return token, exp

    def verify(self, token: str, typ: TokenType, *, error_code: str = "UNAUTHENTICATED") -> dict[str, Any]:
        """Return the claims, or raise AppError(error_code). Fails closed on anything odd."""
        try:
            header = pyjwt.get_unverified_header(token)
            key = self.keys.get(str(header.get("kid")))
            if key is None or header.get("alg") != "EdDSA":
                raise AppError(error_code)
            claims: dict[str, Any] = pyjwt.decode(
                token,
                key.key,
                algorithms=["EdDSA"],
                audience=AUDIENCE,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "typ"]},
                leeway=0,
            )
        except pyjwt.PyJWTError as exc:
            raise AppError(error_code) from exc
        if claims.get("typ") != typ:
            raise AppError(error_code)
        return claims
