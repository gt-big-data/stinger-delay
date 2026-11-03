"""Minimal stop contracts for StingerText.

Person C owns the full model module long-term. This file only carries the
types the stop catalog needs so inferred JSON can be loaded without waiting
on the rest of the messaging stack.
"""

from dataclasses import dataclass


@dataclass
class LatLng:
    lat: float
    lng: float


@dataclass
class Stop:
    route_stop_id: int
    route_id: int
    name: str
    loc: LatLng
    seq: int
