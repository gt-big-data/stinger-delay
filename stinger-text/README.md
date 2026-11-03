# StingerText — data and routing

Replay-first planner for Red (20), Green (17), and Gold (29). Clough is excluded. App time comes from `app.data.clock.now()`.

Startup is replay at Tuesday 12:00 America/New_York. Each route uses the recorded snapshot `clock.replay_frame` selects (same weekday when that minute is covered, otherwise another weekday, never more than 60 seconds stale).

Live polls `BUS_FEED_HOST` (default `bus.gatech.edu`) every 20 seconds on a background thread. `get_arrivals()` only reads that cache. Three failed polls in a row call `clock.set_demo` for the current weekday and minute.

## Tests

```bash
cd stinger-text
python3 -m unittest discover -s tests -v
```

Klaus → West Village at the default Tuesday noon replay returns a `TripPlan`. Origins within 250 m are walk-only. Origins more than 3 km from campus center still return a plan.
