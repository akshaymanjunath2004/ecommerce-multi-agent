import os
import secrets

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    raise ValueError("FATAL ERROR: INTERNAL_API_KEY is not set in the environment!")

def verify_api_key(provided_key: str) -> bool:
    """Verifies an API key using constant-time comparison."""
    if not provided_key:
        return False
        
    # compare_digest throws a TypeError if types don't match or are None, 
    # so we ensure both are strings before comparing.
    return secrets.compare_digest(str(provided_key), str(INTERNAL_API_KEY))