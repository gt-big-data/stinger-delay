"""Pre-event smoke test: one tiny Round-1 tool call against the real xAI API.

Usage:  .venv/bin/python scripts/check_grok.py
Prints the model, latency, and whether a valid plan_trip call came back.
Exits 0 with a message if XAI_API_KEY is not set; exits 1 if the call fails or is invalid.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

TEXT = "Can I make it to West Village by 12:15?"
NOW = datetime(2026, 3, 3, 12, 0, tzinfo=ZoneInfo("America/New_York"))


def main() -> int:
    load_dotenv()
    if not os.getenv("XAI_API_KEY"):
        print("XAI_API_KEY is not set (env or .env). Nothing checked. Add the key and rerun.")
        return 0

    from app.core.grok import GrokClient, GrokError

    client = GrokClient()
    sent_effort = client.reasoning_effort
    print(f"model:            {client.model}")
    print(f"reasoning_effort: {sent_effort!r}")
    print(f"timeout:          {client.timeout_s}s")
    print(f"text:             {TEXT!r} (pin stored, now Tue 12:00)")
    t0 = time.monotonic()
    try:
        intent = client.round1(TEXT, True, NOW)
    except GrokError as e:
        print(f"latency:          {(time.monotonic() - t0) * 1000:.0f} ms")
        print(f"RESULT:           FAIL - {e}")
        return 1
    ms = (time.monotonic() - t0) * 1000
    if sent_effort and client.reasoning_effort is None:
        print("note:             API rejected reasoning_effort; client retried without it")
    print(f"latency:          {ms:.0f} ms")
    if not intent.tool_called:
        print(f"RESULT:           FAIL - no plan_trip call (model said: {intent.decline_text!r})")
        return 1
    print(f"plan_trip args:   dest={intent.destination_place_id} origin={intent.origin_place_id} "
          f"deadline={intent.deadline_hhmm}")
    expected = ("west_village", "PIN", "12:15")
    got = (intent.destination_place_id, intent.origin_place_id, intent.deadline_hhmm)
    print(f"RESULT:           {'PASS' if got == expected else 'VALID CALL, UNEXPECTED ARGS'}"
          f"{'' if ms <= 3000 else ' (slower than 3 s budget)'}")
    return 0 if got == expected else 1


if __name__ == "__main__":
    sys.exit(main())
