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