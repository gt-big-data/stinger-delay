# StingerText pitch: 3 slides

Each slide maps to the judging criteria: (1) creative, extensive Grok use, (2) social good,
(3) working demo, (4) integration.

---

## Slide 1: The problem, and who it's for (social good)

- **Hook:** "Can I make it to Klaus right now?" GT's bus map shows raw ETAs, not that answer.
- **Who it's for:** riders waiting alone at night, who need to know whether the bus is 3 or 18 minutes away, and riders with limited mobility, for whom a missed bus or a long walk is costly.
- **How it works:** text a question and drop a pin. Within about 8 s you get back a verdict (MAKE IT / TIGHT / WON'T MAKE IT / JUST WALK), the plan in one line, and the walk-only time.
- **Privacy:** locations are kept in memory only and expire after 15 min. Nothing is written to disk, and there are no push alerts.
- Visual: a phone screenshot of the Scene 1 exchange.

## Slide 2: How Grok is used (Grok use)

- **Function calling:** one `plan_trip` tool whose place enums are generated from our gazetteer, so Grok maps "WV", "the CULC", and "my 9:30 in Klaus" onto real IDs and can't invent a place.
- **Natural-language time parsing:** "in 10 min" and "by noon" become HH:MM using the demo clock.
- **Structured output:** `{reply, ask_for_location}` JSON, at most 320 characters.
- **Guardrails:** Grok never does arithmetic. Python computes every time, and a reply that states a number not in the plan is replaced by a deterministic template. Each round has a 3 s timeout, so the demo never hangs. Prompt-injection attempts get a one-line decline.
- **Eval:** 20 phrasings (slang, typos, relative times, injection), with a score of __/20. Fill this in from the real `eval_utterances.py` run; don't estimate it.
- **Built with:** Cursor using a Grok coding model. Add the screenshot here (human task).

## Slide 3: Real data, live demo (integration + working demo)

- Built on BDBI's Stinger Delay project: its recorded March 2026 Red, Green, and Gold bus data, replayed on a shifted demo clock. No hand-made mock data.
- Stops inferred from vehicle positions. Rough slip estimates use Stinger Delay's own 3-class delay scheme (on time, slightly late, significantly late).
- Live GT feed when it responds; replay takes over automatically when it doesn't.
- Architecture: iPhone, then iMessage and BlueBubbles, then FastAPI on one Mac. Grok (2 calls) handles language and Python handles routing.
- **Call to action:** "Text it now from your own phone." Show the bot's handle or a QR code.

---

Human tasks: Cursor screenshot, phone screenshots, final eval score, and the backup video.
