from app.data import clock, sources

ACK = "Checking buses..."
ERROR_TEXT = "Something went wrong on my end. Try again in a moment."
TIMEOUT_TEXT = "That is taking too long. Try again in a moment."
LAST_ERROR: str | None = None


def stamp() -> str:
    # TODO(SETUP): confirm clock.now() returns the demo time from B's real clock
    t = clock.now()
    return f"{t:%a} {t.day} {t:%b %H:%M}"


def footer() -> str:
    # TODO(SETUP): confirm sources.mode() casing/values from B's real sources
    if str(sources.mode()).upper() == "LIVE":
        return "[LIVE]"
    return f"[REPLAY {stamp()}]"


def with_footer(texts: list[str]) -> list[str]:
    if not texts:
        return texts
    return [*texts[:-1], texts[-1] + "\n" + footer()]


def record_error(step: str, exc: Exception) -> None:
    global LAST_ERROR
    LAST_ERROR = f"{step}: {type(exc).__name__}"
