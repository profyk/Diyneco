"""Payment providers for hotels paying Diyneco's subscription invoices (DECISIONS D79).

A provider opens a checkout for an amount and later reports, on the server, what happened to
it. The browser's return from a checkout is never taken as proof: an attempt is settled only
from the provider's own status (fetched with Diyneco's credentials) or, for the sandbox, from
the sandbox page's explicit choice, which is test money and never counted as collected.

- SandboxProvider: no credentials, no money. Clearly labelled test checkouts for development,
  staging and the automated tests. Refused when APP_ENV is production.
- StitchProvider: Stitch Pay by Bank (https://docs.stitch.money): a client token
  (client_credentials), `clientPaymentInitiationRequestCreate` for the checkout and a `node`
  query for its state; webhooks are signed with Svix. Built from Stitch's public
  documentation; it must be exercised against a Stitch test client before live use, and no
  recurring or card-on-file charging is assumed (the payer approves each payment).

Card numbers never reach Diyneco: the payer pays on the provider's page.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal, Protocol
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.currencies import decimals
from app.core.errors import AppError

Status = Literal["pending", "succeeded", "failed", "cancelled", "expired"]


@dataclass(frozen=True)
class Checkout:
    provider_ref: str
    url: str


@dataclass(frozen=True)
class ProviderStatus:
    status: Status
    provider_payment_id: str | None = None
    amount_minor: int | None = None
    failure_reason: str | None = None


class PaymentProvider(Protocol):
    name: str
    test_mode: bool
    method: str

    async def create_checkout(
        self, *, attempt_id: str, amount_minor: int, currency: str, reference: str, return_url: str
    ) -> Checkout: ...

    async def fetch_status(self, provider_ref: str, currency: str) -> ProviderStatus: ...


def major(amount_minor: int, currency: str) -> str:
    """Minor units as the decimal string providers expect ("499.00")."""
    places = decimals(currency)
    return f"{Decimal(amount_minor).scaleb(-places):.{places}f}"


# --- Sandbox -------------------------------------------------------------------------------


@dataclass
class SandboxProvider:
    """Test checkouts only. Its status lives in Diyneco's own attempt row, set by the sandbox
    page; fetch_status therefore never reports a change by itself."""

    name: str = "sandbox"
    test_mode: bool = True
    method: str = "sandbox"

    async def create_checkout(
        self, *, attempt_id: str, amount_minor: int, currency: str, reference: str, return_url: str
    ) -> Checkout:
        sep = "&" if "?" in return_url else "?"
        return Checkout(provider_ref=f"sbx_{attempt_id}", url=f"{return_url}{sep}sandbox=1")

    async def fetch_status(self, provider_ref: str, currency: str) -> ProviderStatus:
        return ProviderStatus(status="pending")


# --- Stitch --------------------------------------------------------------------------------

_CREATE = """
mutation CreatePaymentRequest($amount: MoneyInput!, $payerReference: String!,
    $beneficiaryReference: String!, $externalReference: String) {
  clientPaymentInitiationRequestCreate(input: {amount: $amount, payerReference: $payerReference,
      beneficiaryReference: $beneficiaryReference, externalReference: $externalReference}) {
    paymentInitiationRequest { id url }
  }
}
"""

_STATUS = """
query GetPaymentRequestStatus($id: ID!) {
  node(id: $id) {
    ... on PaymentInitiationRequest {
      id
      amount
      state {
        __typename
        ... on PaymentInitiationRequestCompleted { date }
        ... on PaymentInitiationRequestCancelled { date reason }
        ... on PaymentInitiationRequestExpired { date }
      }
    }
  }
}
"""

_STATES: dict[str, Status] = {
    "PaymentInitiationRequestCompleted": "succeeded",
    "PaymentInitiationRequestCancelled": "cancelled",
    "PaymentInitiationRequestExpired": "expired",
    "PaymentInitiationRequestPending": "pending",
}

_token_cache: dict[str, tuple[str, float]] = {}


def _unavailable(problem: str) -> AppError:
    # The provider's own error text is never passed on to the client.
    return AppError(
        "SERVICE_UNAVAILABLE",
        "The payment provider could not be reached. Try again shortly.",
        details={"provider": "stitch", "problem": problem},
    )


@dataclass
class StitchProvider:
    client_id: str
    client_secret: str
    token_url: str
    api_url: str
    test_mode: bool
    http: httpx.AsyncClient | None = None
    name: str = "stitch"
    method: str = "pay_by_bank"

    async def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        if self.http is not None:
            return await self.http.post(url, timeout=15.0, **kwargs)
        async with httpx.AsyncClient(timeout=15.0) as client:
            return await client.post(url, **kwargs)

    async def _token(self) -> str:
        cached = _token_cache.get(self.client_id)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        try:
            r = await self._post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "client_paymentrequest",
                    "audience": self.token_url,
                },
            )
        except httpx.HTTPError as exc:
            raise _unavailable("token request failed") from exc
        if r.status_code != 200:
            raise _unavailable(f"token request answered {r.status_code}")
        body = r.json()
        token = str(body["access_token"])
        _token_cache[self.client_id] = (
            token,
            time.monotonic() + max(60, int(body.get("expires_in", 300)) - 60),
        )
        return token

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            r = await self._post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {await self._token()}"},
            )
        except httpx.HTTPError as exc:
            raise _unavailable("API request failed") from exc
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 200 or body.get("errors") or "data" not in body:
            raise _unavailable(f"API answered {r.status_code}")
        return dict(body["data"])

    async def create_checkout(
        self, *, attempt_id: str, amount_minor: int, currency: str, reference: str, return_url: str
    ) -> Checkout:
        data = await self._graphql(
            _CREATE,
            {
                "amount": {"quantity": major(amount_minor, currency), "currency": currency},
                # Stitch limits: payer reference 12 characters, beneficiary reference 20.
                "payerReference": "Diyneco"[:12],
                "beneficiaryReference": reference[:20],
                "externalReference": attempt_id,
            },
        )
        req = data["clientPaymentInitiationRequestCreate"]["paymentInitiationRequest"]
        return Checkout(
            provider_ref=str(req["id"]), url=f"{req['url']}?redirect_uri={quote(return_url, safe='')}"
        )

    async def fetch_status(self, provider_ref: str, currency: str) -> ProviderStatus:
        node = (await self._graphql(_STATUS, {"id": provider_ref})).get("node") or {}
        state = (node.get("state") or {}).get("__typename", "")
        status = _STATES.get(state)
        if status is None:
            raise _unavailable(f"unknown state {state!r}")
        amount = node.get("amount") or {}
        amount_minor = None
        if amount.get("quantity") is not None and amount.get("currency") == currency:
            amount_minor = int(Decimal(str(amount["quantity"])).scaleb(decimals(currency)))
        reason = (node.get("state") or {}).get("reason")
        return ProviderStatus(
            status=status,
            provider_payment_id=provider_ref if status == "succeeded" else None,
            amount_minor=amount_minor,
            failure_reason=str(reason)[:500] if reason else None,
        )


# --- Choosing a provider -------------------------------------------------------------------


def build(settings: Settings, card_provider: str, http: httpx.AsyncClient | None = None) -> PaymentProvider:
    """The provider the billing settings select, if it can run here."""
    if card_provider == "stitch":
        if not settings.stitch_configured:
            raise AppError(
                "INVALID_TRANSITION", "Online payment is not set up yet. Pay by bank transfer (EFT)."
            )
        assert settings.stitch_client_id and settings.stitch_client_secret  # noqa: S101 - checked above
        return StitchProvider(
            client_id=settings.stitch_client_id,
            client_secret=settings.stitch_client_secret,
            token_url=settings.stitch_token_url,
            api_url=settings.stitch_api_url,
            test_mode=settings.stitch_test_mode,
            http=http,
        )
    if card_provider == "sandbox":
        if settings.app_env == "production":
            raise AppError(
                "INVALID_TRANSITION", "Online payment is not set up yet. Pay by bank transfer (EFT)."
            )
        return SandboxProvider()
    raise AppError("INVALID_TRANSITION", "Online payment is turned off. Pay by bank transfer (EFT).")


def status_report(settings: Settings, card_provider: str) -> dict[str, Any]:
    """Connection status for the admin panel; never a secret, only whether each one is set."""
    return {
        "selected": card_provider,
        "environment": settings.app_env,
        "sandbox_allowed": settings.app_env != "production",
        "stitch": {
            "client_id_set": bool(settings.stitch_client_id),
            "client_secret_set": bool(settings.stitch_client_secret),
            "webhook_secret_set": bool(settings.stitch_webhook_secret),
            "test_mode": settings.stitch_test_mode,
            "ready": settings.stitch_configured,
        },
    }


# --- Webhook signatures (Svix, as Stitch uses) ---------------------------------------------

TOLERANCE_S = 300


def verify_svix(secret: str, headers: dict[str, str], body: bytes, now: float | None = None) -> str:
    """Checks a Svix signature and returns the message id. Raises UNAUTHENTICATED otherwise.

    Signed content is "{id}.{timestamp}.{body}" with HMAC-SHA256 under the base64 key after
    "whsec_"; the header holds space-separated "v1,<base64>" signatures. Timestamps more than
    five minutes away are refused, so an old delivery cannot be replayed."""
    msg_id = headers.get("svix-id") or headers.get("webhook-id") or ""
    stamp = headers.get("svix-timestamp") or headers.get("webhook-timestamp") or ""
    signatures = headers.get("svix-signature") or headers.get("webhook-signature") or ""
    bad = AppError("UNAUTHENTICATED", "The webhook signature is not valid.")
    if not msg_id or not stamp.isdigit() or not signatures:
        raise bad
    if abs((now if now is not None else time.time()) - int(stamp)) > TOLERANCE_S:
        raise bad
    try:
        key = base64.b64decode(secret.removeprefix("whsec_"))
    except ValueError as exc:
        raise bad from exc
    expected = base64.b64encode(
        hmac.new(key, f"{msg_id}.{stamp}.".encode() + body, hashlib.sha256).digest()
    ).decode()
    for part in signatures.split():
        version, _, sig = part.partition(",")
        if version == "v1" and hmac.compare_digest(sig, expected):
            return msg_id
    raise bad


def sign_svix(secret: str, msg_id: str, stamp: int, body: bytes) -> str:
    """The signature header value for a body (used by the tests and local tooling)."""
    key = base64.b64decode(secret.removeprefix("whsec_"))
    sig = base64.b64encode(hmac.new(key, f"{msg_id}.{stamp}.".encode() + body, hashlib.sha256).digest())
    return f"v1,{sig.decode()}"
