"""Walk plus one direct bus per running route.

Red ride time is the next-stop ETA plus median segment run times.
Green and Gold use ETA(alight) - ETA(board) when both are on that vehicle.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from app.data import clock
from app.data.clock import ROUTE_RED
from app.data.sources import get_arrivals, mode, ride_seconds
from app.models import LatLng, Place, Stop, StopArrival, TripOption, TripPlan
from app.routing.params import (
    ALIGHT_RADIUS_M,
    BOARD_RADIUS_M,
    CAMPUS_CENTER_LAT,
    CAMPUS_CENTER_LNG,
    CATCH_MARGIN_S,
    DETOUR,
    FAR_FROM_CAMPUS_M,
    MAX_WAIT_S,
    ROUTE_NAMES,
    TIGHT_WINDOW_S,
    WALK_MPS,
    WALK_ONLY_M,
)

_DATA = Path(__file__).resolve().parents[1] / "data"
_BUS_MPS = 6.0
_SLIP_OK = {"on_time", "slightly_late", "significantly_late", "unknown"}

SHORT_TRIP_NOTE = "Walk only: origin and destination are under 250 m apart."
NO_BUS_NOTE = "Walk only: no bus serves this trip."
FAR_NOTE = "Origin is over 3 km from campus center; confirm the location."


def haversine_m(a: LatLng, b: LatLng) -> float:
    radius = 6_371_000.0
    lat1, lat2 = radians(a.lat), radians(b.lat)
    dlat = radians(b.lat - a.lat)
    dlng = radians(b.lng - a.lng)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * radius * asin(sqrt(h))


def walk_s(a: LatLng, b: LatLng) -> float:
    return haversine_m(a, b) * DETOUR / WALK_MPS


def far_from_campus(origin: LatLng) -> bool:
    return haversine_m(origin, LatLng(CAMPUS_CENTER_LAT, CAMPUS_CENTER_LNG)) > FAR_FROM_CAMPUS_M


@lru_cache(maxsize=1)
def stops_by_route() -> dict[int, tuple[Stop, ...]]:
    raw = json.loads((_DATA / "stops.json").read_text())
    grouped: dict[int, list[Stop]] = defaultdict(list)
    for item in raw:
        stop = Stop(
            route_stop_id=int(item["route_stop_id"]),
            route_id=int(item["route_id"]),
            name=item["name"],
            loc=LatLng(float(item["lat"]), float(item["lng"])),
            seq=int(item["seq"]),
        )
        grouped[stop.route_id].append(stop)
    return {route_id: tuple(sorted(stops, key=lambda stop: stop.seq)) for route_id, stops in grouped.items()}


@lru_cache(maxsize=1)
def _segments() -> dict[int, dict[tuple[int, int], float]]:
    raw = json.loads((_DATA / "segments.json").read_text())
    parsed: dict[int, dict[tuple[int, int], float]] = {}
    for route_id, edges in raw.items():
        bucket: dict[tuple[int, int], float] = {}
        for edge in edges:
            bucket[(int(edge["from_route_stop_id"]), int(edge["to_route_stop_id"]))] = float(edge["median_s"])
        parsed[int(route_id)] = bucket
    return parsed


@lru_cache(maxsize=1)
def _slip() -> dict:
    return json.loads((_DATA / "slip_stats.json").read_text())


def _edge_s(route_id: int, start: Stop, end: Stop) -> float:
    recorded = _segments().get(route_id, {}).get((start.route_stop_id, end.route_stop_id))
    if recorded and recorded > 0:
        return recorded
    return max(20.0, haversine_m(start.loc, end.loc) / _BUS_MPS)


def _forward_s(stops: tuple[Stop, ...], route_id: int, start_id: int, end_id: int) -> float:
    index = {stop.route_stop_id: i for i, stop in enumerate(stops)}
    if start_id not in index or end_id not in index or start_id == end_id:
        return 0.0
    cursor = index[start_id]
    target = index[end_id]
    total = 0.0
    count = len(stops)
    for _ in range(count):
        if cursor == target:
            break
        nxt = (cursor + 1) % count
        total += _edge_s(route_id, stops[cursor], stops[nxt])
        cursor = nxt
    return total


def _slip_for(route_id: int, when: datetime) -> tuple[str, float]:
    blob = _slip().get(str(route_id), {}).get(str(when.hour))
    if not blob:
        return "unknown", 0.0
    klass = blob.get("slip_class") or "unknown"
    if klass not in _SLIP_OK:
        klass = "unknown"
    return klass, max(0.0, float(blob.get("slip_buffer_s") or 0.0))


def _walk_option(origin: LatLng, dest: Place, now: datetime) -> TripOption:
    seconds = walk_s(origin, dest.loc)
    return TripOption(
        kind="walk",
        route_id=None,
        route_name=None,
        board_stop=None,
        alight_stop=None,
        walk_to_stop_s=seconds,
        wait_s=0.0,
        ride_s=0.0,
        walk_from_stop_s=0.0,
        arrive_at=now + timedelta(seconds=seconds),
        slip_class="on_time",
        slip_buffer_s=0.0,
    )


def _by_vehicle(arrivals: list[StopArrival], route_id: int) -> dict[int, dict[int, float]]:
    found: dict[int, dict[int, float]] = defaultdict(dict)
    for row in arrivals:
        if row.route_id != route_id:
            continue
        previous = found[row.vehicle_id].get(row.route_stop_id)
        if previous is None or row.eta_s < previous:
            found[row.vehicle_id][row.route_stop_id] = row.eta_s
    return found


def _bus_options(origin: LatLng, dest: Place, now: datetime, arrivals: list[StopArrival]) -> list[TripOption]:
    options: list[TripOption] = []
    present = {row.route_id for row in arrivals}
    for route_id, stops in stops_by_route().items():
        if route_id not in present or not stops:
            continue
        boards = [stop for stop in stops if haversine_m(origin, stop.loc) <= BOARD_RADIUS_M]
        alights = [stop for stop in stops if haversine_m(dest.loc, stop.loc) <= ALIGHT_RADIUS_M]
        vehicles = _by_vehicle(arrivals, route_id)
        if not boards or not alights or not vehicles:
            continue
        slip_class, slip_buffer = _slip_for(route_id, now)
        best: TripOption | None = None
        for board in boards:
            walk_to = walk_s(origin, board.loc)
            for alight in alights:
                if board.route_stop_id == alight.route_stop_id:
                    continue
                segment_ride = _forward_s(stops, route_id, board.route_stop_id, alight.route_stop_id)
                if segment_ride <= 0:
                    continue
                walk_from = walk_s(alight.loc, dest.loc)
                for etas in vehicles.values():
                    if route_id == ROUTE_RED:
                        positive = [(stop_id, eta) for stop_id, eta in etas.items() if eta >= 0]
                        if not positive:
                            continue
                        next_id, next_eta = min(positive, key=lambda item: item[1])
                        board_eta = next_eta + _forward_s(stops, route_id, next_id, board.route_stop_id)
                        ride = segment_ride
                    else:
                        # Green/Gold: only ETA(alight) - ETA(board). No segment fallback.
                        ride = ride_seconds(
                            route_id,
                            etas.get(board.route_stop_id),
                            etas.get(alight.route_stop_id),
                        )
                        if ride is None:
                            continue
                        board_eta = etas[board.route_stop_id]
                    if board_eta < walk_to + CATCH_MARGIN_S or board_eta > MAX_WAIT_S or ride <= 0:
                        continue
                    option = TripOption(
                        kind="bus",
                        route_id=route_id,
                        route_name=ROUTE_NAMES.get(route_id, str(route_id)),
                        board_stop=board,
                        alight_stop=alight,
                        walk_to_stop_s=walk_to,
                        wait_s=max(0.0, board_eta - walk_to),
                        ride_s=ride,
                        walk_from_stop_s=walk_from,
                        arrive_at=now + timedelta(seconds=board_eta + ride + walk_from),
                        slip_class=slip_class,  # type: ignore[arg-type]
                        slip_buffer_s=slip_buffer,
                    )
                    if best is None or option.arrive_at < best.arrive_at:
                        best = option
        if best is not None:
            options.append(best)
    options.sort(key=lambda option: option.arrive_at)
    return options


def _verdict(best: TripOption, deadline: datetime | None) -> str:
    if deadline is None:
        return "NO_DEADLINE"
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=best.arrive_at.tzinfo)
    buffered = best.arrive_at + timedelta(seconds=best.slip_buffer_s)
    slack = (deadline - buffered).total_seconds()
    if slack >= TIGHT_WINDOW_S:
        return "MAKE_IT"
    if slack >= -TIGHT_WINDOW_S:
        return "TIGHT"
    return "WONT_MAKE_IT"


def plan_trip(origin: LatLng, dest: Place, deadline: datetime | None = None) -> TripPlan:
    """Earliest of the direct buses and the walk. Far origins still get a plan."""
    now = clock.now()
    walking = _walk_option(origin, dest, now)
    short = haversine_m(origin, dest.loc) < WALK_ONLY_M
    buses: list[TripOption] = []
    if not short:
        buses = _bus_options(origin, dest, now, get_arrivals())
    notes: list[str] = []
    if short:
        notes.append(SHORT_TRIP_NOTE)
    elif not buses:
        notes.append(NO_BUS_NOTE)
    if far_from_campus(origin):
        notes.append(FAR_NOTE)
    ranked = sorted([walking, *buses], key=lambda option: option.arrive_at)
    best = ranked[0]
    alternatives = [option for option in ranked if option is not best and option is not walking][:2]
    return TripPlan(
        origin=origin,
        dest=dest,
        now=now,
        deadline=deadline,
        best=best,
        walk=walking,
        alternatives=alternatives,
        verdict=_verdict(best, deadline),  # type: ignore[arg-type]
        mode=mode(),  # type: ignore[arg-type]
        notes=notes,
    )
