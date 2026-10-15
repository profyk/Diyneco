"""Settings from environment variables. The app refuses to start when a required value is
missing or still holds the CHANGE_ME placeholder from .env.example."""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import quote

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PLACEHOLDER = "CHANGE_ME"


def _link(base: str | None, path: str, token: str) -> str:
    if not base:
        return "Use"
    url = f"{base.rstrip('/')}{path}?token={quote(token)}"
    return f"Open this link:\n\n{url}\n\nOr use"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Runtime
    app_env: Literal["development", "staging", "production"]
    api_base_url: str
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    # Public address of the Merchant web app; account emails link to its pages when set.
    merchant_app_url: str | None = None
    # Public address of the Admin panel; platform staff invitations link to it (D71).
    admin_app_url: str | None = None
    # The public website (D83). Publishing asks it to refresh the changed pages at once when
    # both are set; otherwise pages refresh within its cache time (5 minutes).
    website_url: str | None = None
    website_revalidate_secret: str | None = None
    log_level: str = "info"

    # Database
    database_url: str
    worker_database_url: str | None = None
    migrations_database_url: str | None = None

    # Supabase (storage arrives in Phase 2; required outside development)
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    storage_bucket_assets: str = "hotel-assets"
    storage_bucket_invoices: str = "invoices"

    # Auth
    jwt_signing_keys_json: str
    jwt_active_kid: str
    pairing_code_pepper: str
    kms_master_key_id: str
    kms_provider: Literal["local", "aws"] = "local"
    kms_local_master_key: str | None = None
    # AWS KMS (production): KMS_MASTER_KEY_ID is the key's ARN; credentials are the standard
    # AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY of a principal limited to that key.
    aws_region: str | None = None

    # Realtime and jobs
    redis_url: str | None = None

    # Email
    email_provider: str = "console"
    email_provider_key: str | None = None
    email_from: str = "Diyneco <no-reply@diyneco.com>"
    # smtp: "smtp://user@host:587" (STARTTLS) or "smtps://user@host:465"; the password is
    # EMAIL_PROVIDER_KEY so the secret stays in one variable (DECISIONS D52).
    email_smtp_url: str | None = None

    # Stitch (subscription payments, DECISIONS D79). Secrets live only here, never in a web app.
    # Test and live clients are separate Stitch clients: each environment gets its own values.
    # STITCH_TEST_MODE stays true for a test client; payments through it are marked test.
    stitch_client_id: str | None = None
    stitch_client_secret: str | None = None
    stitch_webhook_secret: str | None = None  # Svix signing secret ("whsec_...")
    stitch_test_mode: bool = True
    stitch_token_url: str = "https://secure.stitch.money/connect/token"
    stitch_api_url: str = "https://api.stitch.money/graphql"

    # Monitoring
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0
    release: str | None = None  # set by the deployment (git sha)

    def merchant_link(self, path: str, token: str) -> str:
        """The start of an email sentence: a link that fills in `token` when the app URL is set,
        followed by "Or use" (the code still follows), else just "Use"."""
        return _link(self.merchant_app_url, path, token)

    @property
    def stitch_configured(self) -> bool:
        return bool(self.stitch_client_id and self.stitch_client_secret and self.stitch_webhook_secret)

    def admin_link(self, path: str, token: str) -> str:
        """As merchant_link, for a page of the Admin panel."""
        return _link(self.admin_app_url, path, token)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("*", mode="before")
    @classmethod
    def _empty_is_none(cls, v: object) -> object:
        return None if v == "" else v

    @model_validator(mode="after")
    def _fail_fast(self) -> Settings:
        missing: list[str] = []
        required: dict[str, str | None] = {
            "DATABASE_URL": self.database_url,
            "JWT_SIGNING_KEYS_JSON": self.jwt_signing_keys_json,
            "JWT_ACTIVE_KID": self.jwt_active_kid,
            "PAIRING_CODE_PEPPER": self.pairing_code_pepper,
            "KMS_MASTER_KEY_ID": self.kms_master_key_id,
        }
        if self.kms_provider == "local":
            required["KMS_LOCAL_MASTER_KEY"] = self.kms_local_master_key
        else:
            required["AWS_REGION"] = self.aws_region
        if self.app_env != "development":
            required.update(
                {
                    "REDIS_URL": self.redis_url,
                    "SUPABASE_URL": self.supabase_url,
                    "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
                }
            )
            if self.email_provider != "console":
                required["EMAIL_PROVIDER_KEY"] = self.email_provider_key
        if self.email_provider == "smtp":
            required["EMAIL_SMTP_URL"] = self.email_smtp_url
        if self.stitch_client_id or self.stitch_client_secret or self.stitch_webhook_secret:
            # Half a Stitch configuration is a mistake, not a choice.
            required.update(
                {
                    "STITCH_CLIENT_ID": self.stitch_client_id,
                    "STITCH_CLIENT_SECRET": self.stitch_client_secret,
                    "STITCH_WEBHOOK_SECRET": self.stitch_webhook_secret,
                }
            )
        for name, value in required.items():
            if not value or PLACEHOLDER in value:
                missing.append(name)
        if missing:
            raise ValueError(f"missing or placeholder configuration: {', '.join(sorted(missing))}")

        if self.app_env == "production" and self.kms_provider == "local":
            raise ValueError("KMS_PROVIDER=local is not allowed in production")
        if self.app_env == "production" and self.email_provider == "console":
            raise ValueError("EMAIL_PROVIDER=console is not allowed in production")
        if "*" in self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS may not contain a wildcard")
        if self.kms_provider == "local":
            try:
                key = base64.b64decode(self.kms_local_master_key or "", validate=True)
            except ValueError as exc:
                raise ValueError("KMS_LOCAL_MASTER_KEY must be base64") from exc
            if len(key) != 32:
                raise ValueError("KMS_LOCAL_MASTER_KEY must decode to 32 bytes")
        try:
            keys = json.loads(self.jwt_signing_keys_json)["keys"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError('JWT_SIGNING_KEYS_JSON must be a JWK set: {"keys": [...]}') from exc
        if not any(k.get("kid") == self.jwt_active_kid for k in keys):
            raise ValueError("JWT_ACTIVE_KID does not match any key in JWT_SIGNING_KEYS_JSON")
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
