# NordVPN CLI for macOS - Implementation Plan

## Research Summary

### Existing Solutions
- **divyam234/nordvpn-cli** - Linux-only, shell-based, uses WireGuard directly
- **niccolozanotti/nordvpn-python-interface** - macOS but uses OpenVPN (requires sudo, slower)
- **mrzool/nordvpn-server-find** - Bash server finder only, no connection management

### Key Findings
1. **NordVPN Public API** is available and working:
   - `https://api.nordvpn.com/v1/servers/recommendations` - server list with load/location
   - `https://api.nordvpn.com/v1/users/services/credentials` - WireGuard private key (requires access token)
   - Servers expose WireGuard public keys in metadata

2. **WireGuard on macOS** works via:
   - `brew install wireguard-tools` → `wg-quick up/down`
   - Config path: `/opt/homebrew/etc/wireguard/` (Apple Silicon) or `/usr/local/etc/wireguard/`

3. **Authentication**: User needs access token from NordVPN dashboard

---

## Recommended Strategy: Python CLI with WireGuard

**Why Python:**
- Cross-platform, easy to maintain
- Rich CLI library ecosystem (click/typer)
- Existing API interaction patterns from other projects
- Your stated preference for `uv`

**Why WireGuard over OpenVPN:**
- Faster (NordLynx protocol)
- Simpler config management
- Native macOS support via wireguard-tools
- No daemon required

---

## Architecture

```
nordvpn-cli/
├── pyproject.toml
├── src/
│   └── nordvpn_cli/
│       ├── __init__.py
│       ├── cli.py          # Click/Typer CLI entry point
│       ├── api.py          # NordVPN API client
│       ├── wireguard.py    # WireGuard config generation & management
│       └── config.py       # User config (token storage)
```

---

## Core Features (MVP)

### Commands

| Command | Description |
|---------|-------------|
| `nordvpn login` | Store access token (from NordAccount dashboard) in Keychain |
| `nordvpn connect [country]` | Connect to best server (optional: `--interactive` to choose) |
| `nordvpn disconnect` | Disconnect current VPN |
| `nordvpn status` | Show connection status + current server |
| `nordvpn servers [country]` | List recommended servers with load % |
| `nordvpn countries` | List available countries |
| `nordvpn logout` | Remove token from Keychain |

### Technical Flow: `connect`

1. Fetch private key from credentials API (cached locally)
2. Query recommendations API with optional country filter
3. Pick server with lowest load supporting `wireguard_udp`
4. Generate WireGuard config file
5. Run `wg-quick up nordvpn`

### Technical Flow: `disconnect`

1. Run `wg-quick down nordvpn`
2. Remove/rename config file

---

## Dependencies

- **typer** - CLI framework (includes rich for pretty output)
- **httpx** - Async-capable HTTP client
- **keyring** - macOS Keychain integration for secure token storage

System requirements:
- `brew install wireguard-tools`
- sudo access for wg-quick

---

## Decisions

1. **CLI Framework**: `typer` (modern, type-hint based)
2. **Token Storage**: macOS Keychain via `keyring` library
3. **Kill Switch**: Skip for MVP
4. **Server Selection**: Auto-pick by default, `--interactive` flag to prompt user with top servers

---

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| Port Linux CLI | Feature-complete | Heavy, requires daemon, Linux-specific syscalls |
| OpenVPN-based | Works with existing infra | Slower, requires sudo continuously |
| GUI wrapper | User-friendly | Out of scope |
| **WireGuard (chosen)** | Fast, simple, native | Requires wireguard-tools install |

---

## Sources

- [NordVPN Public API](https://sleeplessbeastie.eu/2019/02/18/how-to-use-public-nordvpn-api/)
- [WireGuard config extraction](https://gist.github.com/bluewalk/7b3db071c488c82c604baf76a42eaad3)
- [WireGuard on macOS CLI](https://blog.scottlowe.org/2021/06/28/using-wireguard-on-mac-via-cli/)
- [divyam234/nordvpn-cli](https://github.com/divyam234/nordvpn-cli)
- [niccolozanotti/nordvpn-python-interface](https://github.com/niccolozanotti/nordvpn-python-interface)
