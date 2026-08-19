"""
Authentication Dependencies

FastAPI dependencies for API key authentication via X-API-Key header.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from cv_matching.src.domain.services.authentication import AuthenticationService
from cv_matching.src.infrastructure.config.settings import get_cv_matching_settings

x_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_auth_service() -> AuthenticationService:
    """Build the AuthenticationService from current settings."""
    settings = get_cv_matching_settings()
    return AuthenticationService(settings=settings.authentication)


def verify_api_key(
    api_key: str = Depends(x_api_key_header),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> str:
    """
    FastAPI dependency that validates the X-API-Key header.

    Raises:
        HTTPException 401: If the API key is missing or invalid.

    Returns:
        str: The validated API key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide X-API-Key header.",
        )
    if not auth_service.authenticate(token=api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Invalid API Key.",
        )
    return api_key
