# NordVPN CLI for macOS

CLI and TUI for NordVPN on macOS using WireGuard.

## Install

```bash
brew install wireguard-tools
uv sync
```

## Usage

### CLI

```bash
nordvpn login           # Browser OAuth login
nordvpn login -t TOKEN  # Manual token login
nordvpn connect         # Connect to best server
nordvpn connect US      # Connect to US server
nordvpn disconnect
nordvpn status
nordvpn servers
nordvpn countries
```

### TUI

```bash
nordvpn-tui
```

Keyboard shortcuts: `c`=connect, `d`=disconnect, `l`=login, `r`=refresh, `q`=quit
