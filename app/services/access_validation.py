"""
Access validation service — G-07.

Defines the authentication contract for production access (MemberPress or
Stripe) and provides verifier functions for each provider. Both providers
are stubbed behind explicit checks until Joey confirms the real MemberPress
endpoint/credentials. Nothing here contacts a real provider yet — that
wiring is the last step once the endpoint is confirmed.
"""

import os
from dataclasses import dataclass
from enum import Enum


class AccessStatus(Enum):
    MEMBERPRESS_VALID = "memberpress_valid"
    STRIPE_VALID = "stripe_valid"
    MISSING = "missing"
    INVALID = "invalid"
    EXPIRED = "expired"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


@dataclass
class AccessResult:
    status: AccessStatus
    reason: str  # non-sensitive, log-safe reason string
    access_method: str | None = None  # "memberpress" | "stripe" | None

    @property
    def is_valid(self) -> bool:
        return self.status in (AccessStatus.MEMBERPRESS_VALID, AccessStatus.STRIPE_VALID)


def skip_auth_enabled() -> bool:
    """SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other
    value, including unset, is treated as false. Never active by accident."""
    return os.environ.get("SKIP_AUTH", "false").strip().lower() == "true"


def check_local_bypass() -> AccessResult | None:
    """Returns a valid local-dev result if SKIP_AUTH is on, else None."""
    if skip_auth_enabled():
        return AccessResult(
            status=AccessStatus.MEMBERPRESS_VALID,
            reason="SKIP_AUTH enabled — local development bypass",
            access_method="local_bypass",
        )
    return None


def verify_memberpress(request_context: dict) -> AccessResult:
    """
    Verify a MemberPress session by calling the WordPress Developer Tools
    REST endpoint. STUBBED until Joey confirms:
      - MEMBERPRESS_BASE_URL (WordPress site origin)
      - MEMBERPRESS_ENDPOINT (exact path)
      - the auth header/query param the API expects
      - which field on the response indicates an active vs
        expired/cancelled subscription

    Until those are confirmed, this always returns PROVIDER_UNAVAILABLE so
    the gate fails closed (denies access) rather than either granting
    access on guesswork or crashing on a missing config value.
    """
    base_url = os.environ.get("MEMBERPRESS_BASE_URL")
    endpoint = os.environ.get("MEMBERPRESS_ENDPOINT")
    api_key = os.environ.get("MEMBERPRESS_API_KEY")

    if not (base_url and endpoint and api_key):
        return AccessResult(
            status=AccessStatus.PROVIDER_UNAVAILABLE,
            reason="MemberPress endpoint/credentials not configured",
        )

    # TODO(G-07): once Joey confirms the endpoint contract, replace this
    # block with a real requests.get(...) call, a short timeout, and
    # response validation against the confirmed field names. Keep the
    # same AccessResult shape so the gate logic never needs to change.
    return AccessResult(
        status=AccessStatus.PROVIDER_UNAVAILABLE,
        reason="MemberPress verifier not yet implemented — awaiting endpoint confirmation",
    )


def verify_stripe(request_context: dict) -> AccessResult:
    """
    Verify a Stripe session token from an approved query param/cookie.
    STUBBED — Stripe checkout configuration (success product/price,
    redirect contract) isn't finalized yet. Returns PROVIDER_UNAVAILABLE
    so the gate fails closed rather than granting access.
    """
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        return AccessResult(
            status=AccessStatus.PROVIDER_UNAVAILABLE,
            reason="Stripe not configured",
        )

    # TODO(G-07): once the Stripe checkout/redirect contract is finalized,
    # implement real session validation here using Stripe's server SDK.
    return AccessResult(
        status=AccessStatus.PROVIDER_UNAVAILABLE,
        reason="Stripe verifier not yet implemented — checkout contract pending",
    )


def check_access(request_context: dict) -> AccessResult:
    """
    Single entry point the Flask gate calls. Tries, in order:
      1. Local SKIP_AUTH bypass (dev only)
      2. MemberPress session
      3. Stripe session
    Returns the first valid result, or the most informative failure.
    """
    bypass = check_local_bypass()
    if bypass:
        return bypass

    mp_result = verify_memberpress(request_context)
    if mp_result.is_valid:
        return mp_result

    stripe_result = verify_stripe(request_context)
    if stripe_result.is_valid:
        return stripe_result

    if mp_result.status != AccessStatus.PROVIDER_UNAVAILABLE:
        return mp_result
    if stripe_result.status != AccessStatus.PROVIDER_UNAVAILABLE:
        return stripe_result
    return AccessResult(status=AccessStatus.MISSING, reason="No valid access source found")
