"""Optional private-deployment authentication.

The public demo remains open by default. A private deployment can set
``RLE_PRIVATE_AUTH_TOKEN`` and every non-public API route then requires either
``Authorization: Bearer <token>`` or ``X-RLE-Auth: <token>``.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Mapping

from .api import is_api_path, is_public_api_path

AUTH_TOKEN_ENV = "RLE_PRIVATE_AUTH_TOKEN"
REQUIRE_AUTH_ENV = "RLE_REQUIRE_AUTH"


class AuthError(RuntimeError):
    """Raised when a request is missing valid private-deployment credentials."""


class AuthConfigurationError(RuntimeError):
    """Raised when auth is required but no token has been configured."""


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def configured_token() -> str:
    return os.environ.get(AUTH_TOKEN_ENV, "").strip()


def auth_required() -> bool:
    return bool(configured_token()) or _truthy(os.environ.get(REQUIRE_AUTH_ENV))


def auth_status() -> dict[str, object]:
    return {
        "required": auth_required(),
        "configured": bool(configured_token()),
        "token_env": AUTH_TOKEN_ENV,
    }


def require_api_auth(path: str, headers: Mapping[str, str]) -> None:
    if not is_api_path(path) or is_public_api_path(path) or not auth_required():
        return

    token = configured_token()
    if not token:
        raise AuthConfigurationError(f"{REQUIRE_AUTH_ENV} is enabled, but {AUTH_TOKEN_ENV} is not configured.")

    authorization = headers.get("Authorization") or headers.get("authorization") or ""
    supplied = ""
    if authorization.lower().startswith("bearer "):
        supplied = authorization.split(" ", 1)[1].strip()
    supplied = supplied or headers.get("X-RLE-Auth") or headers.get("x-rle-auth") or ""

    if not hmac.compare_digest(supplied, token):
        raise AuthError("Authentication required for this private API route.")
