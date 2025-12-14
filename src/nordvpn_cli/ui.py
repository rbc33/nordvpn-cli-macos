"""UI helpers for CLI output."""

from rich.console import Console
from rich.table import Table

from . import api

console = Console()

LOAD_LOW = 30
LOAD_MED = 60


def load_color(load: int) -> str:
    """Return color for server load."""
    if load < LOAD_LOW:
        return "green"
    return "yellow" if load < LOAD_MED else "red"


def print_error(msg: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {msg}")


def print_success(msg: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {msg}")


def print_warn(msg: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]![/yellow] {msg}")


def print_server_table(servers: list[api.Server], title: str = "Servers") -> None:
    """Print server table."""
    table = Table(title=title)
    table.add_column("Server")
    table.add_column("Location")
    table.add_column("Load")
    for s in servers:
        color = load_color(s.load)
        table.add_row(s.hostname, f"{s.city}, {s.country}", f"[{color}]{s.load}%[/]")
    console.print(table)


def print_country_table(countries: list[dict]) -> None:
    """Print country table."""
    table = Table(title="Available Countries")
    table.add_column("Code")
    table.add_column("Name")
    for c in countries:
        table.add_row(c["code"], c["name"])
    console.print(table)
