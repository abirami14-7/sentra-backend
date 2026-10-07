import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.ml.predictor import get_predictor
from app.models.route import RouteModel
from app.models.user import User
from app.schemas.route import (
    PlaceSuggestion,
    RouteOut,
    RouteSearchCandidate,
    RouteSearchRequest,
    RouteSearchResponse,
)
from app.services import geo

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=List[RouteOut])
def list_routes(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(RouteModel).order_by(RouteModel.route_id.asc()).all()


@router.get("/autocomplete", response_model=List[PlaceSuggestion])
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=120),
    limit: int = Query(6, ge=1, le=10),
    current: User = Depends(get_current_user),
):
    """Proxy to Nominatim to return up to `limit` place suggestions."""
    results = await geo.suggest(q, limit=limit)
    return results


def _risk_for_route(
    distance_km: float, duration_min: int, hour: int, seed: int
) -> dict:
    predictor = get_predictor()
    night = 1 if (hour >= 21 or hour <= 5) else 0
    if predictor is not None:
        try:
            ctx = {
                "hour": hour,
                "day_of_week": 3,
                "area_type": "isolated" if night else "commercial",
                "journey_type": "cab",
                "incident_density_7d": 5.0 + seed * 1.5,
                "incident_severity_avg": 2.6 + seed * 0.4,
                "lighting_score": 0.4 + (1 - seed) * 0.3,
                "transit_access": 0.5,
                "crowd_density": 0.4,
                "route_length_km": max(distance_km, 0.5),
                "user_baseline_deviation": 0.2 + seed * 0.15,
                "is_solo": True,
                "has_live_share": False,
            }
            r = predictor.predict(ctx)
            return {
                "risk_score": int(r["risk_score"]),
                "risk_level": str(r["risk_level"]),
                "confidence": int(r["confidence"]),
            }
        except Exception:
            pass

    base = 25 + seed * 20
    if night:
        base += 20
    score = int(min(95, max(5, base)))
    if score < 35:
        level = "LOW"
    elif score < 65:
        level = "MEDIUM"
    elif score < 85:
        level = "HIGH"
    else:
        level = "CRITICAL"
    return {"risk_score": score, "risk_level": level, "confidence": 70}


@router.post("/search", response_model=RouteSearchResponse)
async def search_routes(
    payload: RouteSearchRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    origin_name: str
    if payload.origin_lat is not None and payload.origin_lng is not None:
        o_lat, o_lng = payload.origin_lat, payload.origin_lng
        origin_name = payload.origin_text or "Current location"
    else:
        if not payload.origin_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide origin_lat/lng or origin_text.",
            )
        hit = await geo.geocode(payload.origin_text)
        if hit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find origin: {payload.origin_text}",
            )
        o_lat, o_lng, origin_name = hit

    hit = await geo.geocode(payload.destination_text)
    if hit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find destination: {payload.destination_text}",
        )
    d_lat, d_lng, dest_name = hit

    osm_routes = await geo.route_osrm((o_lat, o_lng), (d_lat, d_lng))
    if not osm_routes:
        dist = geo.haversine_km(o_lat, o_lng, d_lat, d_lng)
        osm_routes = [
            {
                "index": 0,
                "distance_km": round(dist, 2),
                "duration_min": int(round(dist * 3)),
                "points": [[o_lat, o_lng], [d_lat, d_lng]],
            }
        ]

    hour = __import__("datetime").datetime.now().hour
    candidates = []
    for r in osm_routes:
        risk = _risk_for_route(
            r["distance_km"], r["duration_min"], hour, r["index"]
        )
        candidates.append(
            RouteSearchCandidate(
                route_id=f"osrm-{r['index']}",
                name=(
                    "Fastest route"
                    if r["index"] == 0
                    else f"Alternative {r['index']}"
                ),
                distance_km=r["distance_km"],
                duration_min=r["duration_min"],
                risk_score=risk["risk_score"],
                risk_level=risk["risk_level"],
                confidence=risk["confidence"],
                is_safer=False,
                polyline=r["points"],
            )
        )

    best = min(candidates, key=lambda c: c.risk_score)
    for c in candidates:
        c.is_safer = c.route_id == best.route_id

    return RouteSearchResponse(
        origin_lat=o_lat,
        origin_lng=o_lng,
        origin_name=origin_name,
        destination_lat=d_lat,
        destination_lng=d_lng,
        destination_name=dest_name,
        routes=candidates,
    )
