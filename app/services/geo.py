import math
from typing import Dict, List, Optional, Tuple

import httpx

NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
OSRM = "http://router.project-osrm.org/route/v1"

HEADERS = {
    "User-Agent": "SENTRA-MSc-Project/1.0 (student research)",
    "Accept-Language": "en",
}


async def geocode(query: str) -> Optional[Tuple[float, float, str]]:
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            NOMINATIM_SEARCH, params=params, headers=HEADERS
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        first = data[0]
        return (
            float(first["lat"]),
            float(first["lon"]),
            first.get("display_name", query),
        )


async def suggest(query: str, limit: int = 6) -> List[Dict]:
    """Return a list of place suggestions for autocomplete."""
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 0,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(
                NOMINATIM_SEARCH, params=params, headers=HEADERS
            )
        except Exception:
            return []
    if r.status_code != 200:
        return []
    data = r.json()
    out: List[Dict] = []
    for item in data:
        display = item.get("display_name", "")
        parts = [p.strip() for p in display.split(",")]
        short = parts[0] if parts else display
        out.append(
            {
                "display_name": display,
                "short_name": short,
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
            }
        )
    return out


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


async def route_osrm(
    start: Tuple[float, float], end: Tuple[float, float]
) -> Optional[List[Dict]]:
    lon1, lat1 = start[1], start[0]
    lon2, lat2 = end[1], end[0]
    url = f"{OSRM}/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "true",
        "steps": "false",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params, headers=HEADERS)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        out = []
        for idx, route in enumerate(data["routes"][:3]):
            coords = route["geometry"]["coordinates"]
            points = [[c[1], c[0]] for c in coords]
            out.append(
                {
                    "index": idx,
                    "distance_km": round(route["distance"] / 1000.0, 2),
                    "duration_min": int(round(route["duration"] / 60.0)),
                    "points": points,
                }
            )
        return out
