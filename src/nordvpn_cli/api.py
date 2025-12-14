"""NordVPN API client."""

import hashlib
import uuid
from dataclasses import dataclass

import httpx

API_BASE = "https://api.nordvpn.com/v1"


@dataclass
class OAuthSession:
    login_url: str
    verifier: str
    attempt: str


@dataclass
class Server:
    hostname: str
    ip: str
    country: str
    city: str
    load: int
    public_key: str


def get_countries() -> list[dict]:
    """Fetch available countries."""
    resp = httpx.get(f"{API_BASE}/servers/countries", timeout=10)
    resp.raise_for_status()
    return sorted(resp.json(), key=lambda c: c["name"])


def get_servers(country_code: str | None = None, limit: int = 10) -> list[Server]:
    """Fetch recommended WireGuard servers."""
    params = {
        "filters[servers_technologies][identifier]": "wireguard_udp",
        "limit": limit,
    }
    if country_code:
        countries = get_countries()
        country_id = next(
            (c["id"] for c in countries if c["code"].lower() == country_code.lower()),
            None,
        )
        if country_id:
            params["filters[country_id]"] = country_id

    resp = httpx.get(f"{API_BASE}/servers/recommendations", params=params, timeout=10)
    resp.raise_for_status()

    servers = []
    for s in resp.json():
        wg_tech = next(
            (t for t in s.get("technologies", []) if t["identifier"] == "wireguard_udp"),
            None,
        )
        if not wg_tech:
            continue
        public_key = next(
            (m["value"] for m in wg_tech.get("metadata", []) if m["name"] == "public_key"),
            None,
        )
        if not public_key:
            continue

        location = s.get("locations", [{}])[0]
        country_info = location.get("country", {})
        city_info = country_info.get("city", {})

        servers.append(Server(
            hostname=s["hostname"],
            ip=s["station"],
            country=country_info.get("name", "Unknown"),
            city=city_info.get("name", "Unknown"),
            load=s.get("load", 0),
            public_key=public_key,
        ))

    return servers


def get_external_ip() -> dict | None:
    """Get external IP info from ipinfo.io."""
    try:
        resp = httpx.get("https://ipinfo.io/json", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def get_private_key(token: str) -> str:
    """Fetch WireGuard private key using access token."""
    resp = httpx.get(
        f"{API_BASE}/users/services/credentials",
        auth=("token", token),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    key = data.get("nordlynx_private_key")
    if not key:
        raise ValueError("No WireGuard private key in response")
    return key


def start_oauth_login() -> OAuthSession:
    """Start OAuth login flow, returns URL to open in browser."""
    verifier = str(uuid.uuid4())
    challenge = hashlib.sha256(verifier.encode()).hexdigest()

    resp = httpx.post(
        f"{API_BASE}/users/oauth/login",
        json={"preferred_flow": "login", "challenge": challenge},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return OAuthSession(
        login_url=data["redirect_uri"],
        verifier=verifier,
        attempt=data["attempt"],
    )


def complete_oauth_login(exchange_token: str, verifier: str, attempt: str) -> str:
    """Exchange OAuth token for access token."""
    resp = httpx.get(
        f"{API_BASE}/users/oauth/token",
        params={"attempt": attempt, "exchange_token": exchange_token, "verifier": verifier},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]
