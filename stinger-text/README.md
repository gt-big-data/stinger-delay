# StingerText — data and routing

Replay-first planner for Red (20), Green (17), and Gold (29). Clough (28) is excluded. App time comes from `app.data.clock.now()`.

Startup is replay at Tuesday 12:00 America/New_York. Each route uses the recorded snapshot `clock.replay_frame` selects (same weekday when that minute is covered, otherwise another weekday, never more than 60 seconds stale).

## Tests

```bash
cd stinger-text
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m pytest -q
```

`unittest discover` runs the data and routing tests. `pytest` runs those plus the messaging tests. Without `XAI_API_KEY`, replies use the local parser and the template. `scripts/check_grok.py` and `scripts/eval_utterances.py` exit cleanly when that key is missing.

Run from `stinger-text/` so `app` imports. Klaus → West Village at the default Tuesday noon replay returns a `TripPlan`. The fixed pairs covered by the router tests are Klaus → West Village, West Village → Klaus, Kendeda → West Village, Klaus → North Ave, and CULC → Clough, plus Howey → Bobby Dodd, Skiles → Kendeda, and Student Center → MARTA.

Origins within 250 m are walk-only. If no bus can be caught, the plan says so on `notes`. Origins more than 3 km from campus center still return a plan and ask the caller to confirm the location.

## Verdicts

With a deadline, slack is `deadline - (arrival + slip_buffer_s)`. `MAKE_IT` means slack is at least 180 seconds. `TIGHT` means slack is inside ±180 seconds. Otherwise the verdict is `WONT_MAKE_IT`. No deadline yields `NO_DEADLINE`. Slip changes the verdict only. It does not change `arrive_at`.

## Ride time

Red ride time is the next-stop ETA plus median segment seconds from board to alight.

Green and Gold ride time is `ETA(alight) - ETA(board)` when both ETAs are on the same vehicle and the alight ETA is later. A vehicle with one ETA, equal ETAs, an earlier alight ETA, or only the other vehicle's ETA is not a ride, and segment medians do not fill that gap. The plan walks.

## Live feed

`BUS_FEED_HOST` defaults to `bus.gatech.edu` (same public map as `gatech.transloc.com`). The key and host live in `.env.example` (`BUS_FEED_KEY`). The poller calls `GetRouteStopArrivals` every 20 seconds on a background thread. `get_arrivals()` only reads that cache.

Three consecutive failures in one live session call `clock.set_demo` for the current weekday and minute. A successful poll starts a fresh streak. `set_live` and `set_demo` start a fresh streak too, so returning to live does not inherit the old count.

## Fixture

Probed Mon 2 Nov 2026. `GetMapStopPoints` timed out, so stop names and coordinates are in `stops.json`. One `GetRouteStopArrivals` body is saved at `fixtures/feed_arrivals.json`: 63 stop entries, Red 20 (18), Gold 29 (21), Blue 21 (13), and Clough 28 (11). Green 17 was not running. The parser keeps Red and Gold and drops Blue and Clough.

## Messaging

`POST /webhook/bluebubbles` accepts a new-message payload, runs admin commands, then `handler.handle()`. The handler appends the `[LIVE]` or `[REPLAY ...]` footer. It does not return the "Checking buses..." ack. Off-topic text that does not call `plan_trip` gets a fixed decline. Grok is optional: with no `XAI_API_KEY`, a keyword parser and a template fill the two rounds.

`/mode live` and `/mode replay` call `clock.set_live` and `clock.set_demo`. They do not override `sources.mode()` separately from the clock. `/status` reads `handler.last_error()`.

`TripOption.wait_s` on the real router is the residual wait after the walk to the stop. The spoken "bus in" minute count is `walk_to_stop_s + wait_s`, the boarding-stop ETA from now. Pins more than 3 km from campus center are refused before planning, using `FAR_FROM_CAMPUS_M` and `CAMPUS_CENTER_LAT` / `CAMPUS_CENTER_LNG`.

`app/data/sources.py`, `app/routing/router.py`, and `app/routing/params.py` are the real data and routing modules. The webhook and Grok client sit on top of them.
