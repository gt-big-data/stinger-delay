"""Core handler (owner: C, task C3).

    handle(msg: Inbound) -> list[str]     reply texts in order, footer already appended

Contract points for A (messaging):
- The instant ack ("Checking buses...", ACK_TEXT) is sent by A's layer BEFORE calling
  handle(); handle() never returns it. handle() blocks on Grok for up to ~6 s, so it
  cannot deliver anything within 1 s. Suggested rule: ack every non-admin message that
  has text; skip the ack for a location-only message (its reply is instant).
- Every reply returned here already carries the mode footer ([LIVE] or
  [REPLAY Tue 3 Mar 12:00]). A must NOT append another one. The only exception is
  ERROR_TEXT, which has no footer.
- Admin commands are handled by A before handle() is called.
- session.set_pending(user_id, None) clears the pending question.
- last_error() feeds /status.

Grok never computes times: every time and minute in a reply comes from the TripPlan
(via fallback.plan_facts), and Grok replies that state other numbers are discarded in
favour of the deterministic template.
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, time as dtime, timedelta
from difflib import SequenceMatcher
from typing import Optional

from app.core import fallback, prompts
from app.core.grok import GrokClient, GrokError, Intent
from app.data import clock, places, sources
from app.messaging import session
from app.models import Inbound, LatLng, Place, TripPlan
from app.routing import params, router

log = logging.getLogger(__name__)

ACK_TEXT = "Checking buses..."
ERROR_TEXT = "Something went wrong on my end. Try again in a moment."
GOT_LOCATION_TEXT = "Got your location. Where to?"
ASK_PIN_TEXT = ("Drop your location pin (tap your name > Send My Current Location) "
                "or tell me where you are.")
DECLINE_TEXT = ("I can only help with Georgia Tech Stinger bus trips. "
                "Try: \"Can I make it to West Village by 12:15?\"")

_UNSET = object()
_grok: object = _UNSET
_grok_lock = threading.Lock()
_last_error: Optional[str] = None


# -- wiring --------------------------------------------------------------------

def get_grok():
    """The process-wide Grok client, or None when XAI_API_KEY is missing (template mode)."""
    global _grok
    with _grok_lock:
        if _grok is _UNSET:
            if os.getenv("XAI_API_KEY"):
                try:
                    _grok = GrokClient()
                except GrokError as e:
                    log.warning("Grok disabled: %s", e)
                    _grok = None
            else:
                log.warning("XAI_API_KEY not set: replies use the local parser and template")
                _grok = None
        return _grok


def set_grok(client) -> None:
    """Inject a client (tests) or None to force template mode."""
    global _grok
    with _grok_lock:
        _grok = client


def last_error() -> Optional[str]:
    return _last_error


def _record_error(exc: BaseException) -> None:
    global _last_error
    try:
        stamp = f"{clock.now():%a %d %b %H:%M:%S} "
    except Exception:  # noqa: BLE001
        stamp = ""
    _last_error = f"{stamp}{type(exc).__name__}: {exc}"


# -- footer --------------------------------------------------------------------

def footer(mode: str, ts: datetime) -> str:
    if mode == "LIVE":
        return "[LIVE]"
    return f"[REPLAY {ts:%a} {ts.day} {ts:%b %H:%M}]"


def _with_footer(text: str, plan: Optional[TripPlan] = None) -> str:
    text = fallback.cap(text)
    if plan is not None:
        return f"{text} {footer(plan.mode, plan.now)}"
    return f"{text} {footer(sources.mode(), clock.now())}"


# -- entry point -----------------------------------------------------------------

def handle(msg: Inbound) -> list[str]:
    try:
        return _handle(msg)
    except Exception as e:  # noqa: BLE001
        log.exception("handler failed for %s", msg.user_id)
        _record_error(e)
        return [ERROR_TEXT]


def _handle(msg: Inbound) -> list[str]:
    uid = msg.user_id
    if msg.location is not None:
        session.set_location(uid, msg.location)
    text = (msg.text or "").strip()

    if not text:
        if msg.location is None:
            return []
        pending = session.get_pending(uid)
        if pending:
            return _answer(uid, pending)
        return [_with_footer(GOT_LOCATION_TEXT)]

    pending = session.get_pending(uid)
    query = f"Earlier unanswered question: {pending}\nNew message: {text}" if pending else text
    return _answer(uid, query)


def _round1(query: str, has_pin: bool, now: datetime) -> Intent:
    grok = get_grok()
    if grok is not None:
        try:
            return grok.round1(query, has_pin, now)
        except GrokError as e:
            log.warning("Round 1 failed, using local parser: %s", e)
    return fallback.local_intent(query, now)


def _place(pid: str) -> Place:
    # Built from the same places.json the Round 1 enums come from, so every enum id resolves.
    for p in prompts.gazetteer():
        if p.id == pid:
            return p
    raise LookupError(f"place id {pid!r} not in gazetteer")


def _closest_names(query: str, exclude: tuple[str, ...] = ()) -> list[str]:
    # resolve() only returns confident hits, so top up with the nearest names by similarity.
    picked = [p for p in places.resolve(query) if p.id not in exclude]
    q = (query or "").lower()

    def similarity(p: Place) -> float:
        return max(SequenceMatcher(None, q, s.lower()).ratio() for s in (p.name, p.id, *p.aliases))

    rest = sorted((p for p in prompts.gazetteer() if p.id not in exclude and p not in picked),
                  key=similarity, reverse=True)
    return [p.name for p in (picked + rest)[:3]]


def _choice_list(names: list[str]) -> str:
    if len(names) >= 3:
        return f"{names[0]}, {names[1]}, or {names[2]}"
    return " or ".join(names)


def _answer(uid: str, query: str) -> list[str]:
    now = clock.now()
    pin = session.get_location(uid)
    intent = _round1(query, pin is not None, now)

    if not intent.tool_called:
        session.set_pending(uid, None)
        return [_with_footer(DECLINE_TEXT)]

    if intent.destination_place_id == "UNKNOWN":
        session.set_pending(uid, None)
        names = _closest_names(query)
        return [_with_footer(f"I don't know that place. Did you mean {_choice_list(names)}?")]

    dest = _place(intent.destination_place_id)

    if intent.origin_place_id == "UNKNOWN":
        session.set_pending(uid, query)
        names = _closest_names(query, exclude=(dest.id,))
        return [_with_footer(f"I couldn't place where you are. Are you near {_choice_list(names)}? "
                             "Or drop your location pin.")]

    if intent.origin_place_id == "PIN":
        if pin is None:
            session.set_pending(uid, query)
            return [_with_footer(ASK_PIN_TEXT)]
        origin: LatLng = pin
        far_m = router_distance(origin)
        if far_m > params.FAR_FROM_CAMPUS_M:
            session.set_pending(uid, query)
            return [_with_footer(f"Your pin is about {far_m / 1000:.1f} km from campus. Drop a new pin on "
                                 "campus or tell me which building you're at.")]
    else:
        origin = _place(intent.origin_place_id).loc

    session.set_pending(uid, None)
    deadline = _deadline_dt(intent.deadline_hhmm, now)
    plan = router.plan_trip(origin, dest, deadline)
    reply = _round2(intent, plan)
    return [_with_footer(reply, plan)]


def router_distance(loc: LatLng) -> float:
    """Meters from campus center, using the same haversine as the router."""
    center = LatLng(params.CAMPUS_CENTER_LAT, params.CAMPUS_CENTER_LNG)
    return router.haversine_m(loc, center)


def _deadline_dt(hhmm: Optional[str], now: datetime) -> Optional[datetime]:
    if not hhmm:
        return None
    h, m = int(hhmm[:2]), int(hhmm[3:])
    deadline = datetime.combine(now.date(), dtime(h, m), tzinfo=now.tzinfo)
    # A time long past (a "9:30" asked at 22:00) means tomorrow; one just missed stays today
    # so the verdict is WON'T MAKE IT instead of a free day of slack.
    if deadline < now - timedelta(hours=1):
        deadline += timedelta(days=1)
    return deadline


def _round2(intent: Intent, plan: TripPlan) -> str:
    facts = fallback.plan_facts(plan)
    grok = get_grok()
    if grok is not None:
        try:
            r = grok.round2(intent, facts)
            checked = fallback.check_reply(r.reply, facts)
            if checked is not None:
                return checked
            log.warning("Round 2 reply rejected (length or numbers not in plan): %r", r.reply)
        except GrokError as e:
            log.warning("Round 2 failed, using template: %s", e)
    return fallback.template_reply(plan)
