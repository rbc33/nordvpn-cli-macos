"""Login screens for NordVPN TUI."""

import re
import webbrowser
from typing import ClassVar
from urllib.parse import unquote

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label

from .. import api, config


class LoginScreen(Screen[bool]):
    """Login wizard screen."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="login-container"):
            yield Label("Login to NordVPN", id="login-title")
            yield Label("Enter access token or leave empty for browser OAuth:")
            yield Input(placeholder="Access token (optional)", id="token-input", password=True)
            with Horizontal(id="login-buttons"):
                yield Button("Login with Token", id="btn-token", variant="primary")
                yield Button("Browser OAuth", id="btn-oauth", variant="default")
        yield Footer()

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle login button presses."""
        if event.button.id == "btn-token":
            self._login_with_token()
        elif event.button.id == "btn-oauth":
            self._start_oauth()

    def _login_with_token(self) -> None:
        token = self.query_one("#token-input", Input).value.strip()
        if not token:
            self.notify("Enter a token or use OAuth", severity="warning")
            return
        try:
            private_key = api.get_private_key(token)
            config.save_token(token)
            config.save_private_key(private_key)
            self.notify("Logged in successfully!", severity="information")
            self.dismiss(True)
        except Exception as e:
            self.notify(f"Login failed: {e}", severity="error")

    def _start_oauth(self) -> None:
        try:
            session = api.start_oauth_login()
            config.save_oauth_session(session.verifier, session.attempt)
            webbrowser.open(session.login_url)
            self.notify("Browser opened. Complete login and return here.")
            self.app.push_screen(OAuthCallbackScreen())
        except Exception as e:
            self.notify(f"OAuth failed: {e}", severity="error")


class OAuthCallbackScreen(Screen[bool]):
    """Screen for entering OAuth callback URL."""

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="oauth-container"):
            yield Label("Paste the callback URL from browser:")
            yield Input(placeholder="nordvpn://...", id="callback-input")
            yield Button("Complete Login", id="btn-complete", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-complete":
            self._complete_oauth()

    def _complete_oauth(self) -> None:
        callback = self.query_one("#callback-input", Input).value.strip()
        match = re.search(r"exchange_token=([^&]+)", callback)
        if not match:
            self.notify("Invalid callback URL", severity="error")
            return

        exchange_token = unquote(match.group(1))
        verifier, attempt = config.get_oauth_session()
        if not verifier or not attempt:
            self.notify("No OAuth session found", severity="error")
            return

        try:
            token = api.complete_oauth_login(exchange_token, verifier, attempt)
            private_key = api.get_private_key(token)
            config.save_token(token)
            config.save_private_key(private_key)
            config.delete_oauth_session()
            self.notify("Logged in!", severity="information")
            self.app.pop_screen()
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Login failed: {e}", severity="error")
