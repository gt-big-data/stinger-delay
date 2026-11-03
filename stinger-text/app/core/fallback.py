"""Deterministic paths used when Grok is slow, down, or returns invalid output (owner: C).

- plan_facts(plan): the TripPlan digested into display-ready numbers. This is what
  Round 2 receives, so Grok only copies numbers and never does arithmetic.
- template_reply(plan): the reply in the PRD shape, filled from those facts.
- local_intent(text, now): a keyword parser standing in for Round 1.
- check_reply(reply, facts): rejects Grok replies that state times/minutes not in the facts.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timedelta
from typing import Optional

from app.core import prompts
from app.core.grok import Intent
from app.models import TripOption, TripPlan

VERDICT_WORDS = {"MAKE_IT": "YOU'LL MAKE IT", "TIGHT": "TIGHT", "WONT_MAKE_IT": "WON'T MAKE IT"}


def hhmm(dt: Optional[datetime]) -> Optional[str]:
    return None if dt is None else f"{dt:%H:%M}"


def minutes(seconds: float) -> int:
    return 0 if seconds <= 0 else max(1, math.ceil(seconds / 60 - 0.25))  # round, never show 0 for >0


def is_late_night(now: datetime) -> bool:
    return now.hour >= 21 or now.hour < 6


def _option_facts(o: TripOption) -> dict:
    if o.kind == "walk":
        return {"kind": "walk", "arrive": hhmm(o.arrive_at)}
    return {
        "kind": "bus",
        "route": o.route_name or f"route {o.route_id}",
        "board_stop": o.board_stop.name if o.board_stop else None,
        "alight_stop": o.alight_stop.name if o.alight_stop else None,
        "walk_to_stop_min": minutes(o.walk_to_stop_s),
        # B's wait_s is the residual wait after the walk. "Bus in" is the
        # boarding-stop ETA counted from now (walk + wait).
        "bus_in_min": minutes(o.walk_to_stop_s + o.wait_s),
        "ride_min": minutes(o.ride_s),
        "walk_from_stop_min": minutes(o.walk_from_stop_s),
        "arrive": hhmm(o.arrive_at),
        "rough_slip_estimate": o.slip_class,
    }


def plan_facts(plan: TripPlan) -> dict:
    walk_min = minutes((plan.walk.arrive_at - plan.now).total_seconds())
    return {
        "verdict": plan.verdict,
        "destination": plan.dest.name,
        "now": hhmm(plan.now),
        "deadline": hhmm(plan.deadline),
        "late_night": is_late_night(plan.now),
        "best": _option_facts(plan.best),
        "walk_only": {"minutes": walk_min, "arrive": hhmm(plan.walk.arrive_at)},
        "other_bus_options": [_option_facts(a) for a in plan.alternatives if a.kind == "bus"][:2],
    }


def template_reply(plan: TripPlan) -> str:
    f = plan_facts(plan)
    best, walk = f["best"], f["walk_only"]
    dest = plan.dest.name
    if best["kind"] == "bus":
        word = VERDICT_WORDS.get(plan.verdict, "TAKE THE BUS")
        stop = best["board_stop"] or "the stop"
        if not stop.lower().endswith("stop"):
            stop += " stop"
        text = (f"{word}. Walk {best['walk_to_stop_min']} min to {stop}, {best['route']} bus in "
                f"{best['bus_in_min']} min, arrive {dest} {best['arrive']}. Walking takes {walk['minutes']} min.")
        if best["rough_slip_estimate"] in ("slightly_late", "significantly_late"):
            extra = f" Rough slip estimate: {best['rough_slip_estimate'].replace('_', ' ')}."
            if len(text) + len(extra) <= prompts.MAX_REPLY_CHARS:
                text += extra
    else:
        word = VERDICT_WORDS.get(plan.verdict, "JUST WALK")
        text = f"{word}. Walking is fastest: {walk['minutes']} min, arrive {dest} {walk['arrive']}."
        buses = f["other_bus_options"]
        if buses:
            b = buses[0]
            text += f" Next {b['route']} bus option arrives {b['arrive']}."
        else:
            text += " No useful bus right now."
    return cap(text)


def cap(text: str, limit: int = prompts.MAX_REPLY_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


# -- reply validation ---------------------------------------------------------

_TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_MIN_RE = re.compile(r"\b(\d+)\s*(?:min|mins|minutes?)\b", re.I)
FOOTER_RE = re.compile(r"\s*\[(?:LIVE|REPLAY[^\]]*)\]\s*", re.I)


def _collect(obj, times: set[str], mins: set[int]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, int) and not isinstance(v, bool) and (k.endswith("_min") or k == "minutes"):
                mins.add(v)
            else:
                _collect(v, times, mins)
    elif isinstance(obj, list):
        for v in obj:
            _collect(v, times, mins)
    elif isinstance(obj, str) and re.fullmatch(r"\d{2}:\d{2}", obj):
        h, m = int(obj[:2]), int(obj[3:])
        times.add(f"{h}:{m:02d}")
        times.add(f"{(h % 12) or 12}:{m:02d}")


def check_reply(reply: str, facts: dict) -> Optional[str]:
    """Return a cleaned reply, or None if it is empty, too long, or states numbers not in facts."""
    reply = FOOTER_RE.sub(" ", reply).strip()
    if not reply or len(reply) > prompts.MAX_REPLY_CHARS:
        return None
    times: set[str] = set()
    mins: set[int] = set()
    _collect(facts, times, mins)
    for h, m in _TIME_RE.findall(reply):
        if f"{int(h)}:{m}" not in times:
            return None
    for n in _MIN_RE.findall(reply):
        if int(n) not in mins:
            return None
    return reply


# -- local Round 1 stand-in -----------------------------------------------------

_ORIGIN_CUE = re.compile(r"(?:i'?m|i am|im)\s+(?:at|near|in|by)\s+(?:the\s+)?$|(?:from|leaving)\s+(?:the\s+)?$", re.I)
_TRANSIT_CUE = re.compile(r"\b(bus|stinger|make it|make my|get to|go to|going to|how long|ride|walk|route|stop)\b", re.I)
_IN_MIN = re.compile(r"\bin\s+(\d{1,3})\s*(?:min|mins|minutes)\b", re.I)
_CLOCK = re.compile(r"\b(?:by|at|for|my|before|until|til)\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?(?![\d:])", re.I)


def _mentions(text: str) -> list[tuple[int, int, str]]:
    """(start, end, place_id) for every alias/name hit, longest alias wins at a position."""
    low = text.lower()
    hits = []
    for p in prompts.gazetteer():
        for alias in {p.id.replace("_", " "), p.name.lower(), *[a.lower() for a in p.aliases]}:
            for m in re.finditer(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low):
                hits.append((m.start(), m.end(), p.id))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, last_end = [], -1
    for h in hits:
        if h[0] >= last_end:
            out.append(h)
            last_end = h[1]
    return out


def _deadline(text: str, now: datetime) -> Optional[str]:
    m = _IN_MIN.search(text)
    if m:
        return hhmm(now + timedelta(minutes=int(m.group(1))))
    if re.search(r"\bnoon\b", text, re.I):
        return "12:00"
    if re.search(r"\bmidnight\b", text, re.I):
        return "00:00"
    m = _CLOCK.search(text)
    if not m:
        return None
    h, mm = int(m.group(1)), int(m.group(2) or 0)
    if h > 23 or mm > 59 or (m.group(2) is None and m.group(3) is None and h > 12):
        return None
    ampm = (m.group(3) or "").lower().replace(".", "")
    if ampm == "pm" and h < 12:
        h += 12
    elif ampm == "am" and h == 12:
        h = 0
    elif not ampm and h <= 12:
        # next occurrence after now among h and h+12
        cands = [h % 12, h % 12 + 12]
        now_min = now.hour * 60 + now.minute
        later = [c for c in cands if c * 60 + mm >= now_min]
        h = later[0] if later else cands[0]
    return f"{h:02d}:{mm:02d}"


def local_intent(text: str, now: datetime) -> Intent:
    hits = _mentions(text)
    origin, dest = "PIN", None
    for start, _end, pid in hits:
        if _ORIGIN_CUE.search(text[:start]):
            origin = pid
        else:
            dest = pid
    if dest is None:
        if not hits and not _TRANSIT_CUE.search(text):
            return Intent(tool_called=False)
        dest = "UNKNOWN"
    return Intent(tool_called=True, destination_place_id=dest, origin_place_id=origin,
                  deadline_hhmm=_deadline(text, now))
