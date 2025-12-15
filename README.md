# NordVPN CLI for macOS

Unofficial CLI and TUI for NordVPN on macOS using WireGuard.

## Install

```bash
brew install wireguard-tools
uv sync
```

## Setup

```bash
nordvpn setup   # Install URL handler for seamless OAuth
```

This registers `nordvpn://` to intercept OAuth callbacks. On callback, choose:
- **CLI** — complete login in Terminal
- **Official** — hand off to NordVPN.app
- **Uninstall** — remove the handler

## Usage

### CLI

```bash
nordvpn login           # Browser OAuth login
nordvpn login -t TOKEN  # Manual token login
nordvpn connect         # Connect to best server
nordvpn connect US      # Connect to US server
nordvpn connect -i      # Interactive server selection
nordvpn disconnect
nordvpn status
nordvpn servers
nordvpn countries
```

### TUI

```bash
nordvpn-tui
```

Keyboard: `c`=connect, `d`=disconnect, `l`=login, `r`=refresh, `q`=quit

Note: Run `sudo -v` before using TUI (sudo prompts don't work in TUI).

## Requirements

- macOS
- WireGuard tools (`brew install wireguard-tools`)
- sudo access for `wg-quick`
