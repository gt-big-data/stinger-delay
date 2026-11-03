"""Fake OpenAI-SDK client and fake Grok for tests (no network)."""
from __future__ import annotations

import json
import time
from types import SimpleNamespace
from typing import Callable, Optional

from app.core.grok import GrokError, Intent, Reply


def tool_response(dest: str, origin: str = "PIN", deadline: Optional[str] = None):
    call = SimpleNamespace(id="call_1", type="function", function=SimpleNamespace(
        name="plan_trip",
        arguments=json.dumps({"destination_place_id": dest, "origin_place_id": origin, "deadline_hhmm": deadline})))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[call]))])


def text_response(content: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=None))])


class FakeOpenAI:
    """Mimics client.chat.completions.create; `responder(kwargs)` returns a response or raises."""

    def __init__(self, responder: Callable[[dict], object]):
        self.calls: list[dict] = []
        self.responder = responder
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responder(kwargs)


class FakeGrok:
    """Stands in for GrokClient at the handler level."""

    def __init__(self, intent: Optional[Intent] = None, reply: Optional[Reply] = None,
                 round1_sleep: float = 0.0, round2_sleep: float = 0.0,
                 round1_error: bool = False, round2_error: bool = False):
        self.intent, self.reply = intent, reply
        self.round1_sleep, self.round2_sleep = round1_sleep, round2_sleep
        self.round1_error, self.round2_error = round1_error, round2_error
        self.round1_texts: list[str] = []
        self.round2_facts: list[dict] = []

    def round1(self, text, has_pin, now):
        self.round1_texts.append(text)
        if self.round1_sleep:
            time.sleep(self.round1_sleep)
        if self.round1_error:
            raise GrokError("blocked")
        return self.intent(text) if callable(self.intent) else self.intent

    def round2(self, intent, facts):
        self.round2_facts.append(facts)
        if self.round2_sleep:
            time.sleep(self.round2_sleep)
        if self.round2_error:
            raise GrokError("blocked")
        return self.reply(facts) if callable(self.reply) else self.reply
