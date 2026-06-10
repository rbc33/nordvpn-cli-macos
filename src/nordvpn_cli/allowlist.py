"""Allowlist management - ports and subnets that bypass the VPN."""

import ipaddress
import json
from pathlib import Path

_IPV4 = 4


def _path() -> Path:
    d = Path.home() / ".config" / "nordvpn-cli"
    d.mkdir(parents=True, exist_ok=True)
    return d / "allowlist.json"


def get() -> dict:
    p = _path()
    if not p.exists():
        return {"ports": [], "subnets": []}
    return json.loads(p.read_text())


def _save(data: dict) -> None:
    _path().write_text(json.dumps(data, indent=2))


def add_port(port: int) -> bool:
    data = get()
    if port in data["ports"]:
        return False
    data["ports"] = sorted(set(data["ports"]) | {port})
    _save(data)
    return True


def remove_port(port: int) -> bool:
    data = get()
    if port not in data["ports"]:
        return False
    data["ports"].remove(port)
    _save(data)
    return True


def add_subnet(subnet: str) -> bool:
    normalized = str(ipaddress.ip_network(subnet, strict=False))
    data = get()
    if normalized in data["subnets"]:
        return False
    data["subnets"].append(normalized)
    _save(data)
    return True


def remove_all() -> None:
    _save({"ports": [], "subnets": []})


def remove_subnet(subnet: str) -> bool:
    normalized = str(ipaddress.ip_network(subnet, strict=False))
    data = get()
    if normalized not in data["subnets"]:
        return False
    data["subnets"].remove(normalized)
    _save(data)
    return True


def compute_allowed_ips(excluded_subnets: list[str]) -> str:
    """Compute AllowedIPs that covers all IPs except the excluded subnets."""
    ipv4 = [ipaddress.IPv4Network("0.0.0.0/0")]
    ipv6 = [ipaddress.IPv6Network("::/0")]

    for s in excluded_subnets:
        net = ipaddress.ip_network(s, strict=False)
        if net.version == _IPV4:
            result = []
            for a in ipv4:
                result.extend(a.address_exclude(net) if net.overlaps(a) else [a])
            ipv4 = list(ipaddress.collapse_addresses(result))
        else:
            result = []
            for a in ipv6:
                result.extend(a.address_exclude(net) if net.overlaps(a) else [a])
            ipv6 = list(ipaddress.collapse_addresses(result))

    return ", ".join(str(n) for n in ipv4 + ipv6)
