"""xAI Grok client (owner: C, task C2).

Two rounds through the OpenAI SDK (base_url https://api.x.ai/v1):
    round1(text, has_pin, now) -> Intent    function calling: plan_trip args
    round2(intent, facts)      -> Reply     structured output: {"reply", "ask_for_location"}

Each round has a hard wall-clock timeout (GROK_TIMEOUT_S, default 3 s). On timeout,
API error, or invalid output it raises GrokError and the handler falls back to a
deterministic template. Grok never computes times; facts come from the TripPlan.

GROK_REASONING_EFFORT (e.g. "none" for grok-4.3) is sent as reasoning_effort only when
set; if the API rejects it, the request is retried once without it and the parameter is
dropped for the rest of the process.
"""
from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.core import prompts

log = logging.getLogger(__name__)

XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_TIMEOUT_S = 3.0
_HHMM = re.compile(prompts.HHMM_PATTERN)

# Shared pool: a timed-out call keeps running in its thread until the SDK's own
# timeout ends it, but the handler has already moved on.
_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="grok")


class GrokError(Exception):
    """Any Round 1/2 failure: timeout, API error, or invalid output."""


class GrokTimeout(GrokError):
    pass


@dataclass
class Intent:
    tool_called: bool
    destination_place_id: Optional[str] = None
    origin_place_id: Optional[str] = None
    deadline_hhmm: Optional[str] = None
    decline_text: Optional[str] = None
    # Round 1 conversation, carried into Round 2 (empty for fakes / local parse).
    messages: list[dict] = field(default_factory=list, repr=False)
    tool_call_id: Optional[str] = None


@dataclass
class Reply:
    reply: str
    ask_for_location: bool


def _timeout_from_env() -> float:
    try:
        return float(os.getenv("GROK_TIMEOUT_S", DEFAULT_TIMEOUT_S))
    except ValueError:
        return DEFAULT_TIMEOUT_S


class GrokClient:
    def __init__(self, client: Any = None, model: Optional[str] = None,
                 timeout_s: Optional[float] = None, reasoning_effort: Optional[str] = None):
        self.timeout_s = timeout_s if timeout_s is not None else _timeout_from_env()
        self.model = model or os.getenv("GROK_MODEL") or "grok-4.3"
        effort = reasoning_effort if reasoning_effort is not None else os.getenv("GROK_REASONING_EFFORT")
        self.reasoning_effort: Optional[str] = effort.strip() if effort and effort.strip() else None
        if client is None:
            from openai import OpenAI
            key = os.getenv("XAI_API_KEY")
            if not key:
                raise GrokError("XAI_API_KEY is not set")
            client = OpenAI(api_key=key, base_url=XAI_BASE_URL, timeout=self.timeout_s, max_retries=0)
        self.client = client

    # -- transport -------------------------------------------------------
    def _create(self, kwargs: dict) -> Any:
        if self.reasoning_effort:
            try:
                return self.client.chat.completions.create(**kwargs, reasoning_effort=self.reasoning_effort)
            except Exception as e:  # noqa: BLE001
                if not _rejects_reasoning_effort(e):
                    raise
                log.warning("API rejected reasoning_effort=%r (%s); retrying without it",
                            self.reasoning_effort, e)
                self.reasoning_effort = None
        return self.client.chat.completions.create(**kwargs)

    def _call(self, **kwargs: Any) -> Any:
        kwargs.setdefault("model", self.model)
        kwargs.setdefault("timeout", self.timeout_s)
        fut = _POOL.submit(self._create, kwargs)
        try:
            return fut.result(timeout=self.timeout_s)
        except FutureTimeout as e:
            fut.cancel()
            raise GrokTimeout(f"Grok call exceeded {self.timeout_s:.1f}s") from e
        except GrokError:
            raise
        except Exception as e:  # noqa: BLE001
            raise GrokError(f"Grok API error: {type(e).__name__}: {e}") from e

    # -- Round 1: function calling ----------------------------------------
    def round1(self, text: str, has_pin: bool, now: datetime) -> Intent:
        messages = [
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": prompts.round1_user_content(text, has_pin, now)},
        ]
        resp = self._call(messages=messages, tools=[prompts.plan_trip_tool()],
                          tool_choice="auto", temperature=0)
        try:
            msg = resp.choices[0].message
        except (AttributeError, IndexError) as e:
            raise GrokError("Round 1: empty response") from e
        calls = getattr(msg, "tool_calls", None) or []
        if not calls:
            return Intent(tool_called=False, decline_text=(msg.content or "").strip() or None)
        call = calls[0]
        if call.function.name != "plan_trip":
            raise GrokError(f"Round 1: unexpected tool {call.function.name!r}")
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError as e:
            raise GrokError("Round 1: tool arguments are not JSON") from e
        intent = validate_args(args)
        intent.messages = messages + [{
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [{"id": call.id, "type": "function",
                            "function": {"name": "plan_trip", "arguments": call.function.arguments}}],
        }]
        intent.tool_call_id = call.id
        return intent

    # -- Round 2: structured output ---------------------------------------
    def round2(self, intent: Intent, facts: dict) -> Reply:
        if not intent.messages or not intent.tool_call_id:
            raise GrokError("Round 2 needs the Round 1 conversation")
        messages = intent.messages + [
            {"role": "tool", "tool_call_id": intent.tool_call_id, "content": json.dumps(facts)},
        ]
        resp = self._call(messages=messages, tools=[prompts.plan_trip_tool()], tool_choice="none",
                          response_format=prompts.REPLY_SCHEMA, temperature=0.3)
        try:
            content = resp.choices[0].message.content
            data = json.loads(content)
        except (AttributeError, IndexError, TypeError, json.JSONDecodeError) as e:
            raise GrokError("Round 2: response is not the reply JSON") from e
        reply, ask = data.get("reply"), data.get("ask_for_location")
        if not isinstance(reply, str) or not reply.strip() or not isinstance(ask, bool):
            raise GrokError("Round 2: reply JSON has wrong shape")
        return Reply(reply=reply.strip(), ask_for_location=ask)


def validate_args(args: dict) -> Intent:
    ids = set(prompts.place_ids())
    dest = args.get("destination_place_id")
    origin = args.get("origin_place_id") or "PIN"
    deadline = args.get("deadline_hhmm")
    if dest not in ids | {"UNKNOWN"}:
        raise GrokError(f"Round 1: invalid destination {dest!r}")
    if origin not in ids | {"PIN", "UNKNOWN"}:
        raise GrokError(f"Round 1: invalid origin {origin!r}")
    # Grok fills the required field with "00:00" when the user gave no time; nobody
    # asks to arrive by midnight sharp, so that exact value means "no deadline".
    if deadline in ("", "null", "00:00"):
        deadline = None
    if deadline is not None:
        if not isinstance(deadline, str) or not _HHMM.match(deadline) or int(deadline[:2]) > 23:
            raise GrokError(f"Round 1: invalid deadline {deadline!r}")
    return Intent(tool_called=True, destination_place_id=dest, origin_place_id=origin, deadline_hhmm=deadline)


def _rejects_reasoning_effort(e: Exception) -> bool:
    if isinstance(e, TypeError):  # SDK-side unknown kwarg
        return "reasoning_effort" in str(e)
    status = getattr(e, "status_code", None)
    # Any 400/422 while the param was sent: retry once without it. If the param was not
    # the cause, the retry fails the same way and surfaces as a normal GrokError.
    return status in (400, 422)
