"""TUI widgets for NordVPN."""

from textual.app import ComposeResult
from textual.widgets import Label, Static

from .. import api, wireguard


class StatusWidget(Static):
    """Displays current VPN connection status."""

    def compose(self) -> ComposeResult:
        yield Label("Loading...", id="status-text")

    def refresh_status(self) -> None:
        """Update status display."""
        label = self.query_one("#status-text", Label)
        if not wireguard.has_sudo_cached():
            label.update("[dim]Run 'sudo -v' to check status[/]")
            return
        if wireguard.is_connected():
            ip_info = api.get_external_ip()
            ip_text = f"{ip_info['ip']} ({ip_info.get('city', '?')})" if ip_info else "Unknown"
            label.update(f"[green]● Connected[/]\nIP: {ip_text}")
        else:
            label.update("[yellow]○ Disconnected[/]")
