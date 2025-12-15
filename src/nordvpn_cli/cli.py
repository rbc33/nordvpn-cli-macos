"""CLI interface for NordVPN on macOS."""

import typer
from rich.prompt import Prompt
from rich.table import Table

from . import api, config, url_handler, wireguard
from .auth import do_callback_login, do_oauth_flow, do_token_login, fail
from .ui import console, load_color, print_success, print_warn

app = typer.Typer(help="NordVPN CLI for macOS using WireGuard")


@app.command()
def setup() -> None:
    """Install nordvpn:// URL handler for seamless OAuth login."""
    path = url_handler.install_handler()
    print_success(f"URL handler installed: {path}")


@app.command()
def login(
    token: str = typer.Option(None, "--token", "-t", help="Access token"),
    callback: str = typer.Option(None, "--callback", "-c", help="OAuth callback URL"),
) -> None:
    """Log in to NordVPN (browser OAuth or --token for manual)."""
    if token:
        do_token_login(token)
    elif callback:
        do_callback_login(callback)
    else:
        do_oauth_flow()


@app.command()
def logout() -> None:
    """Remove credentials from Keychain."""
    config.delete_token(), config.delete_private_key(), config.delete_oauth_session()
    print_success("Logged out")


@app.command()
def connect(
    country: str = typer.Argument(None, help="Country code (e.g., US, NL, DE)"),
    interactive: bool = typer.Option(False, "-i", help="Choose server interactively"),
) -> None:
    """Connect to NordVPN server."""
    private_key = config.get_private_key()
    if not private_key:
        fail("Not logged in. Run 'nordvpn login' first.")
    _do_connect(private_key, country, interactive)


def _do_connect(private_key: str, country: str | None, interactive: bool) -> None:
    if wireguard.is_connected():
        print_warn("Already connected. Disconnecting first...")
        wireguard.disconnect()
    try:
        servers = api.get_servers(country_code=country, limit=10 if interactive else 1)
    except Exception as e:
        fail(f"Failed to fetch servers: {e}")
    if not servers:
        fail("No servers found")
    server = _select_server(servers) if interactive and len(servers) > 1 else servers[0]
    console.print(f"Connecting to [cyan]{server.hostname}[/cyan]...")
    wireguard.write_config(private_key, server.public_key, server.hostname)
    console.print("[dim]sudo required for wg-quick[/dim]")
    wireguard.connect()
    print_success(f"Connected to {server.hostname}")


def _select_server(servers: list[api.Server]) -> api.Server:
    table = Table(title="Available Servers")
    for col in [("#", "dim"), ("Server", None), ("Location", None), ("Load", None)]:
        table.add_column(col[0], style=col[1])
    for i, s in enumerate(servers, 1):
        ld = f"[{load_color(s.load)}]{s.load}%[/]"
        table.add_row(str(i), s.hostname, f"{s.city}, {s.country}", ld)
    console.print(table)
    return servers[max(0, min(int(Prompt.ask("Select", default="1")) - 1, len(servers) - 1))]


@app.command()
def disconnect() -> None:
    """Disconnect from NordVPN."""
    if not wireguard.is_connected():
        print_warn("Not connected")
        return
    wireguard.disconnect()
    print_success("Disconnected")


@app.command()
def status() -> None:
    """Show connection status and external IP."""
    wg_status = wireguard.get_status()
    ip_info = api.get_external_ip()
    if not wg_status:
        console.print("[yellow]Disconnected[/yellow]")
        if ip_info:
            ip, city, country = ip_info.get("ip"), ip_info.get("city"), ip_info.get("country")
            console.print(f"  IP: {ip} ({city}, {country})")
        return
    _print_connected_status(ip_info, wg_status)


def _print_connected_status(ip_info: dict | None, wg_status: dict) -> None:
    console.print("[green]Connected[/green]")
    if ip_info:
        loc = f"{ip_info.get('city')}, {ip_info.get('country')}"
        console.print(f"  IP: [cyan]{ip_info['ip']}[/cyan] ({loc})")
        if org := ip_info.get("org"):
            console.print(f"  Org: {org}")
    for k, lbl in [("endpoint", "Server"), ("handshake", "Handshake"), ("transfer", "Transfer")]:
        if v := wg_status.get(k):
            console.print(f"  {lbl}: {v}")


@app.command()
def servers(
    country: str = typer.Argument(None, help="Filter by country code"),
    limit: int = typer.Option(10, "-n", help="Number of servers"),
) -> None:
    """List recommended servers."""
    try:
        server_list = api.get_servers(country_code=country, limit=limit)
    except Exception as e:
        fail(f"Failed to fetch servers: {e}")
    table = Table(title="Recommended Servers")
    table.add_column("Server")
    table.add_column("Location")
    table.add_column("Load")
    for s in server_list:
        table.add_row(s.hostname, f"{s.city}, {s.country}", f"[{load_color(s.load)}]{s.load}%[/]")
    console.print(table)


@app.command()
def countries() -> None:
    """List available countries."""
    try:
        country_list = api.get_countries()
    except Exception as e:
        fail(f"Failed to fetch countries: {e}")
    table = Table(title="Available Countries")
    table.add_column("Code")
    table.add_column("Name")
    for c in country_list:
        table.add_row(c["code"], c["name"])
    console.print(table)
