"""
Security utilities for authentication and authorization.
"""
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import settings

# Security scheme for Bearer token
security_scheme = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token

    Example:
        ```python
        token = create_access_token({"sub": "user@example.com"})
        ```
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid

    Example:
        ```python
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
        except HTTPException:
            # Handle invalid token
            pass
        ```
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> bool:
    """
    Verify API key from Bearer token.

    This is a simple API key verification for Phase 1.
    Phase 5 will upgrade to OAuth2/JWT with full RBAC.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        bool: True if valid

    Raises:
        HTTPException: If API key is invalid

    Example:
        ```python
        @app.get("/agents", dependencies=[Depends(verify_api_key)])
        async def get_agents():
            # This endpoint requires valid API key
            pass
        ```
    """
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
