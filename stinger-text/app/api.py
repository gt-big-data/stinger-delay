"""HTTP surface shaped like the Stinger Delay Stop and DelayPrediction types."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.data import clock
from app.data.places import all_places, resolve
from app.data.sources import mode
from app.models import LatLng
from app.routing.router import plan_trip, stops_by_route

router = APIRouter()


class OriginIn(BaseModel):
    lat: float
    lng: float


class PlanIn(BaseModel):
    origin: OriginIn
    destination: str = Field(description="Place id or alias")
    deadline: datetime | None = None


def _stop_json(stop) -> dict:
    return {
        "id": str(stop.route_stop_id),
        "name": stop.name,
        "latitude": stop.loc.lat,
        "longitude": stop.loc.lng,
        "sequence": stop.seq,
        "routeId": str(stop.route_id),
    }


def _option_json(option) -> dict:
    return {
        "kind": option.kind,
        "routeId": None if option.route_id is None else str(option.route_id),
        "routeName": option.route_name,
        "walkToStopSeconds": option.walk_to_stop_s,
        "waitSeconds": option.wait_s,
        "rideSeconds": option.ride_s,
        "walkFromStopSeconds": option.walk_from_stop_s,
        "arriveAt": option.arrive_at.isoformat(),
        "slipClass": option.slip_class,
        "slipBufferSeconds": option.slip_buffer_s,
        "boardStop": None if option.board_stop is None else _stop_json(option.board_stop),
        "alightStop": None if option.alight_stop is None else _stop_json(option.alight_stop),
    }


def _delays(option) -> list[dict]:
    if option.kind != "bus" or option.board_stop is None:
        return []
    minutes = round(option.slip_buffer_s / 60.0, 2)
    confidence = 0.5 if option.slip_class == "unknown" else 0.8
    rows = []
    for stop in (option.board_stop, option.alight_stop):
        if stop is None:
            continue
        rows.append({
            "routeId": str(option.route_id),
            "stopId": str(stop.route_stop_id),
            "predictedDelayMinutes": minutes,
            "eta": option.arrive_at.isoformat(),
            "confidence": confidence,
        })
    return rows


@router.get("/stops")
def stops(routeId: str | None = None):
    rows = []
    for route_stops in stops_by_route().values():
        for stop in route_stops:
            if routeId is not None and str(stop.route_id) != str(routeId):
                continue
            rows.append(_stop_json(stop))
    return rows


@router.post("/plan-trip")
def plan(body: PlanIn):
    dest = next((place for place in all_places() if place.id == body.destination), None)
    if dest is None:
        found = resolve(body.destination)
        dest = found[0] if found else None
    if dest is None:
        raise HTTPException(status_code=404, detail="unknown destination")
    trip = plan_trip(LatLng(body.origin.lat, body.origin.lng), dest, body.deadline)
    return {
        "origin": {"lat": trip.origin.lat, "lng": trip.origin.lng},
        "destination": {"id": trip.dest.id, "name": trip.dest.name},
        "now": trip.now.isoformat(),
        "deadline": None if trip.deadline is None else trip.deadline.isoformat(),
        "verdict": trip.verdict,
        "mode": trip.mode,
        "best": _option_json(trip.best),
        "walk": _option_json(trip.walk),
        "alternatives": [_option_json(item) for item in trip.alternatives],
        "delayPredictions": _delays(trip.best),
    }


@router.get("/health")
def health():
    return {"mode": mode(), "now": clock.now().isoformat()}
