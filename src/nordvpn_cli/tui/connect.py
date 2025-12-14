"""Connect screen for server selection."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView

from .. import api
from ..ui import load_color


class ConnectScreen(Screen[api.Server | None]):
    """Server selection screen with country filter."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "cancel", "Cancel")]

    def __init__(self) -> None:
        super().__init__()
        self._countries: list[dict] = []
        self._servers: list[api.Server] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="connect-layout"):
            with Vertical(id="country-panel"):
                yield Label("Country (type to filter):")
                yield Input(placeholder="Search country...", id="country-search")
                yield ListView(id="country-list")
            with Vertical(id="server-panel"):
                yield Label("Servers:")
                yield ListView(id="server-list")
        yield Footer()

    def on_mount(self) -> None:
        self._load_countries()

    def _load_countries(self) -> None:
        try:
            self._countries = api.get_countries()
            self._update_country_list("")
        except Exception as e:
            self.notify(f"Failed to load countries: {e}", severity="error")

    def _update_country_list(self, filter_text: str) -> None:
        listview = self.query_one("#country-list", ListView)
        listview.clear()
        ft = filter_text.lower()
        for c in self._countries:
            if ft in c["name"].lower() or ft in c["code"].lower():
                listview.append(ListItem(Label(f"{c['code']} - {c['name']}"), id=f"c-{c['code']}"))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "country-search":
            self._update_country_list(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "country-list" and event.item.id:
            code = event.item.id.replace("c-", "")
            self._load_servers(code)
        elif event.list_view.id == "server-list" and event.item.id:
            idx = int(event.item.id.replace("s-", ""))
            self.dismiss(self._servers[idx])

    def _load_servers(self, country_code: str) -> None:
        try:
            self._servers = api.get_servers(country_code=country_code, limit=10)
            listview = self.query_one("#server-list", ListView)
            listview.clear()
            for i, s in enumerate(self._servers):
                listview.append(
                    ListItem(Label(f"{s.hostname} [{load_color(s.load)}]{s.load}%[/]"), id=f"s-{i}")
                )
        except Exception as e:
            self.notify(f"Failed to load servers: {e}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(None)
