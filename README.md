# README.md


## Commands

```bash
uv tool install .         # install nordvpn + nordvpn-tui globally
uv sync                   # install dependencies (dev)
uv run nordvpn --help     # run CLI
uv run nordvpn-tui        # run TUI
uv run ruff check src/    # lint
uv run ruff format src/   # format
```

No test suite exists yet.

## Commit hook

`.githooks/commit-msg` rejects AI attribution patterns ("Co-Authored-By: Claude", "Generated with Claude", etc.). Activate with:

```bash
git config core.hooksPath .githooks
```

Do **not** include AI co-author lines in commit messages.

## CLI Usage

```bash
# Allowlist — ports and subnets that bypass the VPN
nordvpn allowlist add port 22
nordvpn allowlist add port 80
nordvpn allowlist add subnet 192.168.0.0/24
nordvpn allowlist add local
nordvpn allowlist remove port 22
nordvpn allowlist remove subnet 192.168.0.0/24
nordvpn allowlist remove local
nordvpn allowlist remove all
nordvpn allowlist list
```

Changes take effect on next `nordvpn connect`. Subnet exclusions rewrite `AllowedIPs`; port exclusions use macOS `pf` rules.

## Architecture

Two entry points: `nordvpn` (CLI via Typer) and `nordvpn-tui` (TUI via Textual).

### Module responsibilities

| Module | Role |
|---|---|
| `api.py` | NordVPN REST API (httpx). Fetches servers, countries, handles OAuth token exchange, fetches WireGuard private key. |
| `auth.py` | Three login paths: token, OAuth callback URL, browser OAuth flow. Orchestrates `api` + `config`. |
| `config.py` | macOS Keychain (via `keyring`). Stores access token, WireGuard private key, and in-flight OAuth session (verifier + attempt). |
| `wireguard.py` | Generates `nordvpn.conf`, calls `wg-quick up/down` and `wg show` via sudo subprocess. Config path: `/opt/homebrew/etc/wireguard/nordvpn.conf` (Apple Silicon) or `/usr/local/etc/wireguard/nordvpn.conf` (Intel). |
| `allowlist.py` | Persists port/subnet allowlist at `~/.config/nordvpn-cli/allowlist.json`. Subnet exclusions modify `AllowedIPs` via CIDR subtraction (`ipaddress.address_exclude`). Port exclusions inject pf anchor rules via wg-quick `PreUp`/`PostUp`/`PreDown` hooks. |
| `cli.py` | Typer app. All user-facing commands live here. |
| `url_handler.py` | Compiles an AppleScript `.app` bundle into `~/Applications/` and registers it as the `nordvpn://` URL scheme handler via `lsregister` + Swift `LSSetDefaultHandlerForURLScheme`. |
| `tui/` | Textual app (`NordVPNApp`). Screens: `LoginScreen`, `ConnectScreen`. `StatusWidget` shows live connection state. |
| `ui.py` | Rich console helpers (`print_success`, `print_warn`, `print_error`, `load_color`). |

### Key flows

**Login (browser OAuth)**
1. `api.start_oauth_login()` → gets redirect URL + verifier + attempt
2. Verifier/attempt saved to Keychain; browser opened to NordVPN login page
3. NordVPN redirects to `nordvpn://...?exchange_token=...`
4. URL handler app intercepts, user picks "CLI" → opens Terminal running `nordvpn login --callback <url>`
5. `auth.do_callback_login()` exchanges token → fetches WireGuard private key → saves both to Keychain

**Connect**
1. `config.get_private_key()` — no API call, key is cached from login
2. `api.get_servers()` — fetches from `/v1/servers/recommendations` filtered to `wireguard_udp`
3. `wireguard.write_config()` — builds config using allowlist state (AllowedIPs + optional pf hooks)
4. `sudo wg-quick up nordvpn`

**Allowlist (port bypass)**
- `PreUp` saves default gateway + interface to `/tmp/nordvpn-allowlist-gw` *before* wg-quick changes routes
- `PostUp` loads a `pf` anchor named `nordvpn` with `route-to` rules that send matched port traffic to the original gateway
- `PreDown` flushes the pf anchor

### Ruff constraints (pyproject.toml)

- Max function args: 3 (`PLR0913`)
- Max statements per function: 20
- Max branches: 8
- Max cyclomatic complexity: 8
- Line length: 100

### TUI sudo note

`wg-quick` requires sudo. The TUI has no TTY for password prompts — user must run `sudo -v` in a terminal before launching the TUI.
