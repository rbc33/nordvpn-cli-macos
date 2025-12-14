"""NordVPN TUI application."""

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header

from .. import api, config, wireguard
from .connect import ConnectScreen
from .screens import LoginScreen
from .widgets import StatusWidget


class NordVPNApp(App[None]):
    """Main NordVPN TUI application."""

    CSS = """
    #status-widget { height: 5; padding: 1; border: solid green; }
    #login-container, #oauth-container { align: center middle; width: 60; height: auto; }
    #login-title { text-style: bold; }
    #login-buttons { height: 3; }
    #connect-layout { height: 100%; }
    #country-panel, #server-panel { width: 1fr; padding: 1; }
    #main-buttons { height: 3; padding: 1; }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit"),
        Binding("c", "connect", "Connect"),
        Binding("d", "disconnect", "Disconnect"),
        Binding("l", "login", "Login"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield StatusWidget(id="status-widget")
            with Horizontal(id="main-buttons"):
                yield Button("Connect", id="btn-connect", variant="primary")
                yield Button("Disconnect", id="btn-disconnect", variant="warning")
                yield Button("Login", id="btn-login", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.query_one("#status-widget", StatusWidget).refresh_status()

    def action_refresh(self) -> None:
        self._refresh_status()

    def action_login(self) -> None:
        self.push_screen(LoginScreen(), callback=self._on_login_complete)

    def _on_login_complete(self, success: bool) -> None:
        if success:
            self._refresh_status()

    def action_connect(self) -> None:
        if not config.get_private_key():
            self.notify("Not logged in. Press L to login.", severity="warning")
            return
        self.push_screen(ConnectScreen(), callback=self._on_server_selected)

    def _on_server_selected(self, server: api.Server | None) -> None:
        if not server:
            return
        private_key = config.get_private_key()
        if not private_key:
            return
        if wireguard.is_connected():
            wireguard.disconnect()
        wireguard.write_config(private_key, server.public_key, server.hostname)
        wireguard.connect()
        self.notify(f"Connected to {server.hostname}")
        self._refresh_status()

    def action_disconnect(self) -> None:
        if wireguard.is_connected():
            wireguard.disconnect()
            self.notify("Disconnected")
            self._refresh_status()
        else:
            self.notify("Not connected", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {"btn-connect": "connect", "btn-disconnect": "disconnect", "btn-login": "login"}
        if action := actions.get(event.button.id):
            getattr(self, f"action_{action}")()


def main() -> None:
    """Entry point for TUI."""
    NordVPNApp().run()


if __name__ == "__main__":
    main()
