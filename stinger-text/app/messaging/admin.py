import os
import re

from app.data import clock, places, sources
from app.messaging import replies, session

HELP = "Commands: /clock, /mode, /where, /status"
CLOCK_USAGE = "Usage: /clock Tue 09:20 or /clock live"
MODE_USAGE = "Usage: /mode live or /mode replay"
WHERE_USAGE = "Usage: /where <landmark>"
DAYS = {"mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu", "fri": "Fri", "sat": "Sat", "sun": "Sun"}


def _norm(h: str) -> str:
    h = h.strip()
    return h.lower() if "@" in h else re.sub(r"[^\d+]", "", h)


def admin_handles() -> set[str]:
    return {_norm(h) for h in os.environ.get("ADMIN_HANDLES", "").split(",") if h.strip()}


def is_command(text: str | None) -> bool:
    return bool(text) and text.strip().startswith("/")


def _clock(arg: list[str]) -> str:
    if arg == ["live"]:
        clock.set_live()
        return "Clock is live. Mode: LIVE."
    if len(arg) == 2 and arg[0].lower() in DAYS and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", arg[1]):
        day = DAYS[arg[0].lower()]
        clock.set_demo(day, arg[1])
        return f"Clock set to {day} {arg[1]}. Mode: REPLAY."
    return CLOCK_USAGE


def _where(user_id: str, name: str) -> str:
    if not name:
        return WHERE_USAGE
    found = places.resolve(name)
    if not found:
        return f'No match for "{name}".'
    session.set_location(user_id, found[0].loc)
    return f"Location set to {found[0].name}."


def _status() -> str:
    from app.core import handler
    err = replies.LAST_ERROR or handler.last_error() or "none"
    return f"Mode: {sources.mode()}. Clock: {replies.stamp()}. Last error: {err}."


def _mode(want: str) -> str:
    # B's sources.mode() follows the demo clock: live = clock live; replay = freeze the clock at "now".
    if want == "live":
        clock.set_live()
    elif clock.mode() != "REPLAY":
        now = clock.now()
        clock.set_demo(DAYS[now.strftime("%a").lower()], now.strftime("%H:%M"))
    return f"Mode: {want.upper()}."


def run(user_id: str, text: str) -> list[str]:
    try:
        if user_id not in admin_handles():
            return []
        parts = text.strip().split()
        cmd, arg = (parts[0].lower() if parts else ""), parts[1:]
        if cmd == "/clock":
            return [_clock(arg)]
        if cmd == "/mode":
            if len(arg) == 1 and arg[0].lower() in ("live", "replay"):
                return [_mode(arg[0].lower())]
            return [MODE_USAGE]
        if cmd == "/where":
            return [_where(user_id, " ".join(arg))]
        if cmd == "/status":
            return [_status()]
        return [HELP]
    except Exception:
        return ["Command failed."]
