"""
Authentication Service

Domain service responsible for validating API keys.
"""

import hmac


class AuthenticationService:
    """Validates bearer / API-key tokens against the configured secret."""

    def __init__(self, settings) -> None:
        """
        Args:
            settings: An object (e.g. AuthenticationSettings) that exposes
                      an ``api_key`` attribute with the expected secret.
        """
        self._expected_key: str = settings.api_key

    def authenticate(self, token: str) -> bool:
        """
        Constant-time comparison of *token* against the stored API key.

        Returns:
            ``True`` when the token matches, ``False`` otherwise.
        """
        return hmac.compare_digest(token, self._expected_key)
