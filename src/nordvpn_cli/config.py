"""Configuration and credential management via macOS Keychain."""

import contextlib

import keyring

SERVICE_NAME = "nordvpn-cli"
TOKEN_KEY = "access_token"
PRIVATE_KEY_KEY = "wireguard_private_key"
OAUTH_VERIFIER_KEY = "oauth_verifier"
OAUTH_ATTEMPT_KEY = "oauth_attempt"


def save_token(token: str) -> None:
    """Save access token to Keychain."""
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def get_token() -> str | None:
    """Get access token from Keychain."""
    return keyring.get_password(SERVICE_NAME, TOKEN_KEY)


def delete_token() -> None:
    """Delete access token from Keychain."""
    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, TOKEN_KEY)


def save_private_key(key: str) -> None:
    """Cache WireGuard private key in Keychain."""
    keyring.set_password(SERVICE_NAME, PRIVATE_KEY_KEY, key)


def get_private_key() -> str | None:
    """Get cached WireGuard private key from Keychain."""
    return keyring.get_password(SERVICE_NAME, PRIVATE_KEY_KEY)


def delete_private_key() -> None:
    """Delete cached private key from Keychain."""
    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, PRIVATE_KEY_KEY)


def save_oauth_session(verifier: str, attempt: str) -> None:
    """Save OAuth session for pending login."""
    keyring.set_password(SERVICE_NAME, OAUTH_VERIFIER_KEY, verifier)
    keyring.set_password(SERVICE_NAME, OAUTH_ATTEMPT_KEY, attempt)


def get_oauth_session() -> tuple[str | None, str | None]:
    """Get OAuth session (verifier, attempt) for pending login."""
    verifier = keyring.get_password(SERVICE_NAME, OAUTH_VERIFIER_KEY)
    attempt = keyring.get_password(SERVICE_NAME, OAUTH_ATTEMPT_KEY)
    return verifier, attempt


def delete_oauth_session() -> None:
    """Delete OAuth session after login completes."""
    for key in (OAUTH_VERIFIER_KEY, OAUTH_ATTEMPT_KEY):
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(SERVICE_NAME, key)
