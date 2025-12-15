"""Authentication commands for CLI."""

import re
import webbrowser
from urllib.parse import unquote

import typer
from rich.prompt import Prompt

from . import api, config, url_handler
from .ui import console, print_error, print_success


def fail(msg: str) -> None:
    """Print error and exit."""
    print_error(msg)
    raise typer.Exit(1) from None


def do_token_login(token: str) -> None:
    """Login using manual access token."""
    try:
        private_key = api.get_private_key(token)
    except Exception as e:
        fail(f"Login failed: {e}")
    config.save_token(token)
    config.save_private_key(private_key)
    print_success("Logged in successfully")


def do_callback_login(url: str, verifier: str | None = None, attempt: str | None = None) -> None:
    """Complete login using OAuth callback URL."""
    match = re.search(r"exchange_token=([^&]+)", url)
    if not match:
        fail("Invalid callback URL - no exchange_token found")
    exchange_token = unquote(match.group(1))
    if not verifier or not attempt:
        verifier, attempt = config.get_oauth_session()
    if not verifier or not attempt:
        fail("No OAuth session found. Run 'nordvpn login' first.")
    _complete_oauth(exchange_token, verifier, attempt)


def _complete_oauth(exchange_token: str, verifier: str, attempt: str) -> None:
    try:
        token = api.complete_oauth_login(exchange_token, verifier, attempt)
        private_key = api.get_private_key(token)
    except Exception as e:
        fail(f"Login failed: {e}")
    config.save_token(token)
    config.save_private_key(private_key)
    config.delete_oauth_session()
    print_success("Logged in successfully")


def do_oauth_flow() -> None:
    """Start browser OAuth flow."""
    try:
        session = api.start_oauth_login()
    except Exception as e:
        fail(f"Failed to start login: {e}")
    config.save_oauth_session(session.verifier, session.attempt)
    console.print("Opening browser for login...")
    webbrowser.open(session.login_url)
    if url_handler.APP_PATH.exists():
        console.print("\nClick 'Continue' in browser - login will complete automatically.")
    else:
        console.print("\nAfter login, copy the callback URL and paste below.")
        console.print("[dim]Tip: run 'nordvpn setup' for automatic callback handling[/dim]")
        cb = Prompt.ask("\nCallback URL (or Enter to cancel)")
        if cb:
            do_callback_login(cb, session.verifier, session.attempt)
