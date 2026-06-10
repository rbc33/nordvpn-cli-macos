"""WireGuard configuration management."""

import shutil
import subprocess
import sys
from pathlib import Path

from . import allowlist as _allowlist

INTERFACE_NAME = "nordvpn"


def has_sudo_cached() -> bool:
    """Check if sudo credentials are cached (non-interactive)."""
    result = subprocess.run(
        ["sudo", "-n", "true"], capture_output=True, check=False
    )
    return result.returncode == 0


def _find_wg_quick() -> str:
    """Find wg-quick binary path."""
    # Check common Homebrew paths first (sudo doesn't inherit PATH)
    for path in ["/opt/homebrew/bin/wg-quick", "/usr/local/bin/wg-quick"]:
        if Path(path).exists():
            return path
    # Fallback to PATH lookup
    found = shutil.which("wg-quick")
    if found:
        return found
    raise FileNotFoundError(
        "wg-quick not found. Install with: brew install wireguard-tools"
    )


def _find_wg() -> str:
    """Find wg binary path."""
    for path in ["/opt/homebrew/bin/wg", "/usr/local/bin/wg"]:
        if Path(path).exists():
            return path
    found = shutil.which("wg")
    if found:
        return found
    raise FileNotFoundError(
        "wg not found. Install with: brew install wireguard-tools"
    )


_GW_TMP = "/tmp/nordvpn-allowlist-gw"


def _build_config(private_key: str, public_key: str, endpoint: str) -> str:
    data = _allowlist.get()
    ports = data["ports"]
    subnets = data["subnets"]

    allowed_ips = _allowlist.compute_allowed_ips(subnets) if subnets else "0.0.0.0/0, ::/0"

    lines = [
        "[Interface]",
        f"PrivateKey = {private_key}",
        "Address = 10.5.0.2/32",
        "DNS = 103.86.96.100, 103.86.99.100",
    ]

    if ports:
        port_list = ", ".join(str(p) for p in ports)
        pf_tcp = f"pass out route-to ($IF $GW) proto tcp from any to any port {{{port_list}}}"
        pf_udp = f"pass out route-to ($IF $GW) proto udp from any to any port {{{port_list}}}"
        postup = (
            f"if [ -s {_GW_TMP} ]; then "
            f"read -r GW IF < {_GW_TMP}; "
            f'{{ echo "{pf_tcp}"; echo "{pf_udp}"; }} | pfctl -a nordvpn -f - 2>/dev/null; '
            f"pfctl -e 2>/dev/null; true; fi"
        )
        lines += [
            f"PreUp = route -n get default 2>/dev/null | awk '/gateway:/ {{gw=$2}} /interface:/ {{iff=$2}} END {{print gw, iff}}' > {_GW_TMP}",
            f"PostUp = {postup}",
            f"PreDown = pfctl -a nordvpn -F all 2>/dev/null; rm -f {_GW_TMP}",
        ]

    lines += [
        "",
        "[Peer]",
        f"PublicKey = {public_key}",
        f"AllowedIPs = {allowed_ips}",
        f"Endpoint = {endpoint}:51820",
        "PersistentKeepalive = 25",
        "",
    ]
    return "\n".join(lines)


def get_config_dir() -> Path:
    """Get WireGuard config directory for macOS."""
    if sys.platform != "darwin":
        raise RuntimeError("This tool only supports macOS")

    # Apple Silicon vs Intel
    homebrew_arm = Path("/opt/homebrew/etc/wireguard")
    homebrew_intel = Path("/usr/local/etc/wireguard")

    if homebrew_arm.exists():
        return homebrew_arm
    if homebrew_intel.exists():
        return homebrew_intel

    # Try to create (prefer arm path on modern macs)
    config_dir = homebrew_arm if Path("/opt/homebrew").exists() else homebrew_intel
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get path to nordvpn WireGuard config file."""
    return get_config_dir() / f"{INTERFACE_NAME}.conf"


def write_config(private_key: str, public_key: str, endpoint: str) -> Path:
    """Write WireGuard configuration file."""
    config = _build_config(private_key, public_key, endpoint)
    config_path = get_config_path()
    config_path.write_text(config)
    config_path.chmod(0o600)
    return config_path


def connect() -> None:
    """Bring up WireGuard interface."""
    subprocess.run(["sudo", _find_wg_quick(), "up", INTERFACE_NAME], check=True)


def disconnect() -> None:
    """Bring down WireGuard interface."""
    subprocess.run(["sudo", _find_wg_quick(), "down", INTERFACE_NAME], check=True)


def is_connected() -> bool:
    """Check if WireGuard interface is up."""
    # wg show lists all active interfaces - check if any exist
    result = subprocess.run(
        ["sudo", _find_wg(), "show", "interfaces"],
        check=False, capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def get_status() -> dict | None:
    """Get WireGuard interface status."""
    if not is_connected():
        return None

    result = subprocess.run(
        ["sudo", _find_wg(), "show"],
        check=False, capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    status = {"raw": result.stdout}
    for line in result.stdout.splitlines():
        if "endpoint:" in line:
            status["endpoint"] = line.split("endpoint:")[1].strip()
        elif "latest handshake:" in line:
            status["handshake"] = line.split("latest handshake:")[1].strip()
        elif "transfer:" in line:
            status["transfer"] = line.split("transfer:")[1].strip()

    return status
