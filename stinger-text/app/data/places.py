"""Fuzzy campus place lookup over the verified OSM catalog."""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from app.models import LatLng, Place

_PLACES_PATH = Path(__file__).with_name("places.json")
_MIN_SCORE = 0.8


def _norm(text: str) -> str:
    lowered = text.lower().replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return " ".join(cleaned.split())


@lru_cache(maxsize=1)
def all_places() -> tuple[Place, ...]:
    raw = json.loads(_PLACES_PATH.read_text())
    places: list[Place] = []
    for item in raw:
        places.append(
            Place(
                id=item["id"],
                name=item["name"],
                loc=LatLng(lat=float(item["lat"]), lng=float(item["lng"])),
                aliases=list(item.get("aliases") or []),
            )
        )
    return tuple(places)


def _fields(place: Place) -> list[str]:
    return [
        _norm(place.id.replace("_", " ")),
        _norm(place.name),
        *(_norm(alias) for alias in place.aliases),
    ]


def _score(query: str, place: Place) -> float:
    if not query:
        return 0.0
    fields = [field for field in _fields(place) if field]
    if query in fields:
        return 1.0
    # Two-letter aliases ("vl", "wv", "sc") only hit on exact match.
    if len(query) < 3:
        return 0.0
    best = 0.0
    query_tokens = set(query.split())
    for field in fields:
        if query in field or field in query:
            best = max(best, 0.9)
        field_tokens = set(field.split())
        if query_tokens and query_tokens <= field_tokens:
            best = max(best, 0.93)
        best = max(best, SequenceMatcher(None, query, field).ratio())
    return best


def resolve(text: str) -> list[Place]:
    """Places matching ``text``, best match first. Empty when nothing is close."""
    query = _norm(text or "")
    if not query:
        return []
    ranked = [( _score(query, place), place) for place in all_places()]
    hits = [place for score, place in ranked if score >= _MIN_SCORE]
    hits.sort(key=lambda place: (-_score(query, place), place.id))
    return hits
