# Person C: pre-event checklist

Status key: **DONE** (done in the repo), **TODO** (anyone with the key can run it),
**HUMAN** (needs a person).

| # | Item | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Put the xAI API key into `.env` (`XAI_API_KEY`). Keep `GROK_MODEL=grok-4.3` and `GROK_REASONING_EFFORT=none` from `.env.example`. | Human | **HUMAN** | No key was available when the code was built, so live Grok is untested. |
| 2 | Run `.venv/bin/python scripts/check_grok.py` and record the model, latency, and PASS/FAIL below. | C | **TODO** (blocked on #1) | The script exists and exits cleanly without a key. If it prints "API rejected reasoning_effort", the client fell back on its own; note that here. |
| 3 | Run `.venv/bin/python scripts/eval_utterances.py` and record the **real** score below (target 18/20). | C | **TODO** (blocked on #1) | If it scores under 18, tune `SYSTEM_PROMPT` and the tool description in `app/core/prompts.py`, then rerun. |
| 4 | Set up Cursor with a Grok coding model on all three laptops, and take the screenshot for slide 2. | Human | **HUMAN** | |
| 5 | Confirm with the organizers that pre-built stubs and a prepared gazetteer are allowed. | Human | **HUMAN** | If not, B moves `places.json` into B7 at the event, and the C1 stubs are rewritten at T+0. |
| 6 | Rehearse the four scenes in `demo/script.md`. | C plus team | **TODO** | Needs A's BlueBubbles and B's router. Write the real replies into the "Actual" lines. |
| 7 | Plan the backup video: phone screen-record plus Mac terminal, all four scenes, recorded at the T+80 run-through. | C | **TODO** (plan below) / recording is **HUMAN** | |

Already done in the repo: C1 contracts and stubs, C2 Grok client, C3 handler, C4 eval
script, C5 demo script and slides outline, and `pytest` green with Grok mocked.

## Results (fill in from real runs only)

```
check_grok.py    date: ____  model: ____  latency: ____ ms  result: ____
eval_utterances  date: ____  model: ____  score: __/20
```

## Backup video plan

- **Device:** an iPhone with iOS screen recording (Control Center > Screen Recording, mic on for narration). At the same time, record the Mac's uvicorn log with QuickTime > New Screen Recording.
- **Content:** Scenes 1 to 4 in order, with the `/clock` admin texts visible between scenes, then one fallback beat: unset the key, rerun Scene 1, and show the template reply still arriving.
- **Length:** under 2 minutes. Trim the waits, but keep one full ack-to-answer delay uncut so the latency is honest.
- **When:** the T+80 run-through, with someone outside the team texting.
- **Where:** save it to the laptop desktop and to a phone, so it plays offline.
