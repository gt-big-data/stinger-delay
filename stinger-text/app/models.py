"""Shared StingerText contracts.

LatLng and Stop match the stop catalog on main. Place is required by the
places resolver. The remaining types are the frozen dataclass contract so
other lanes can import them. Person C owns this module long-term.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


@dataclass
class LatLng:
    lat: float
    lng: float


@dataclass
class Place:
    id: str
    name: str
    loc: LatLng
    aliases: list[str] = field(default_factory=list)


@dataclass
class Stop:
    route_stop_id: int
    route_id: int
    name: str
    loc: LatLng
    seq: int


@dataclass
class StopArrival:
    route_id: int
    route_stop_id: int
    vehicle_id: int
    eta_s: float


@dataclass
class TripOption:
    kind: Literal["bus", "walk"]
    route_id: Optional[int]
    route_name: Optional[str]
    board_stop: Optional[Stop]
    alight_stop: Optional[Stop]
    walk_to_stop_s: float
    wait_s: float
    ride_s: float
    walk_from_stop_s: float
    arrive_at: datetime
    slip_class: Literal["on_time", "slightly_late", "significantly_late", "unknown"]
    slip_buffer_s: float


@dataclass
class TripPlan:
    origin: LatLng
    dest: Place
    now: datetime
    deadline: Optional[datetime]
    best: TripOption
    walk: TripOption
    alternatives: list[TripOption]
    verdict: Literal["MAKE_IT", "TIGHT", "WONT_MAKE_IT", "NO_DEADLINE"]
    mode: Literal["LIVE", "REPLAY"]
    notes: list[str] = field(default_factory=list)


@dataclass
class Inbound:
    user_id: str
    chat_guid: str
    text: Optional[str]
    location: Optional[LatLng]
    audio_path: Optional[str]
