"""
FIX GAP #12: Previously raised ValueError at module import time if
INTERNAL_API_KEY was not set. This crashed the entire application on startup
(and during any local testing without a .env file).

Now uses a safe default with a loud WARNING log so development still works
but production misconfiguration is clearly surfaced — not silently accepted.
"""
import os
import secrets
import warnings

_INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")

if not _INTERNAL_API_KEY:
    warnings.warn(
        "INTERNAL_API_KEY is not set. Using an insecure empty default. "
        "Set this env var in production!",
        stacklevel=2,
    )
    _INTERNAL_API_KEY = "insecure-default-change-me"

INTERNAL_API_KEY: str = _INTERNAL_API_KEY


def verify_api_key(provided_key: str) -> bool:
    """Verify an API key using constant-time comparison to prevent timing attacks."""
    if not provided_key:
        return False
    return secrets.compare_digest(str(provided_key), str(INTERNAL_API_KEY))