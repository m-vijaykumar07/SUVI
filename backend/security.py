import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings

api_key_header = APIKeyHeader(name="X-SUVI-API-KEY", auto_error=False)
security_bearer = HTTPBearer(auto_error=False)

def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> bool:
    """Validate incoming request API key or Bearer token."""
    # Allow local development if API key matches or bearer matches
    token = None
    if header_key:
        token = header_key
    elif credentials:
        token = credentials.credentials
    
    # In default local mode, accept default configured token
    if not token or (token != settings.API_TOKEN and token != settings.SECRET_KEY):
        # We don't block standard browser HUD access on localhost for ease of use,
        # but protected API endpoints verify PIN or Token
        return False
    return True

def verify_action_pin(provided_pin: Optional[str]) -> bool:
    """Verify Master Security PIN for sensitive actions (calls, messages, shutdown)."""
    if not provided_pin:
        return False
    return hmac.compare_digest(str(provided_pin).strip(), str(settings.MASTER_PIN).strip())

def require_pin_auth(provided_pin: Optional[str]):
    """Enforce PIN verification, raising 403 HTTP exception if invalid."""
    if not verify_action_pin(provided_pin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Verification Failed: Valid Master Security PIN required for this action."
        )

def sanitize_phone_number(number: str) -> str:
    """Sanitize and format phone numbers."""
    cleaned = "".join(ch for ch in number if ch.isdigit() or ch == '+')
    return cleaned
