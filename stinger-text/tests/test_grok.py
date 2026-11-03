import json
import time
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.core import prompts
from app.core.grok import GrokClient, GrokError, GrokTimeout
from tests.fakes import FakeOpenAI, text_response, tool_response

NOW = datetime(2026, 3, 3, 12, 0, tzinfo=ZoneInfo("America/New_York"))


def test_tool_enums_built_from_places_json():
    params = prompts.plan_trip_tool()["function"]["parameters"]["properties"]
    dest_enum, origin_enum = params["destination_place_id"]["enum"], params["origin_place_id"]["enum"]
    for pid in ("klaus", "culc", "crc", "west_village", "north_ave_apts", "student_center"):
        assert pid in dest_enum and pid in origin_enum
    assert dest_enum[-1] == "UNKNOWN" and "PIN" not in dest_enum
    assert origin_enum[0] == "PIN" and origin_enum[-1] == "UNKNOWN"
    assert params["deadline_hhmm"]["type"] == ["string", "null"]


def test_round1_parses_valid_call_and_passes_context():
    fake = FakeOpenAI(lambda kw: tool_response("west_village", "PIN", "12:15"))
    g = GrokClient(client=fake, model="m", reasoning_effort="")
    intent = g.round1("WV by 12:15?", True, NOW)
    assert (intent.destination_place_id, intent.origin_place_id, intent.deadline_hhmm) == ("west_village", "PIN", "12:15")
    user = fake.calls[0]["messages"][1]["content"]
    assert "12:00" in user and "Stored location pin: yes" in user and "WV by 12:15?" in user


@pytest.mark.parametrize("args", [("hogwarts", "PIN", None), ("klaus", "PIN", "25:00"), ("klaus", "mars", None),
                                  ("klaus", "PIN", "9:30")])
def test_round1_rejects_invalid_args(args):
    g = GrokClient(client=FakeOpenAI(lambda kw: tool_response(*args)), model="m", reasoning_effort="")
    with pytest.raises(GrokError):
        g.round1("x", False, NOW)


def test_round1_off_topic_no_tool_call():
    g = GrokClient(client=FakeOpenAI(lambda kw: text_response("Sorry, I only do buses.")), model="m", reasoning_effort="")
    intent = g.round1("write me a poem", False, NOW)
    assert intent.tool_called is False


def test_round2_structured_reply_includes_tool_result():
    def responder(kw):
        if "response_format" in kw:
            return text_response(json.dumps({"reply": "TIGHT. Bus.", "ask_for_location": False}))
        return tool_response("crc")
    fake = FakeOpenAI(responder)
    g = GrokClient(client=fake, model="m", reasoning_effort="")
    intent = g.round1("crc?", True, NOW)
    reply = g.round2(intent, {"verdict": "TIGHT"})
    assert reply.reply == "TIGHT. Bus." and reply.ask_for_location is False
    tool_msg = fake.calls[1]["messages"][-1]
    assert tool_msg["role"] == "tool" and json.loads(tool_msg["content"]) == {"verdict": "TIGHT"}


def test_round2_bad_json_raises():
    def responder(kw):
        return text_response("not json") if "response_format" in kw else tool_response("crc")
    g = GrokClient(client=FakeOpenAI(responder), model="m", reasoning_effort="")
    with pytest.raises(GrokError):
        g.round2(g.round1("crc?", True, NOW), {})


def test_timeout_is_enforced():
    def slow(kw):
        time.sleep(1.0)
        return tool_response("crc")
    g = GrokClient(client=FakeOpenAI(slow), model="m", timeout_s=0.2, reasoning_effort="")
    t0 = time.monotonic()
    with pytest.raises(GrokTimeout):
        g.round1("crc?", True, NOW)
    assert time.monotonic() - t0 < 0.6


def test_reasoning_effort_sent_when_set():
    fake = FakeOpenAI(lambda kw: tool_response("crc"))
    GrokClient(client=fake, model="grok-4.3", reasoning_effort="none").round1("crc?", True, NOW)
    assert fake.calls[0]["reasoning_effort"] == "none" and fake.calls[0]["model"] == "grok-4.3"


def test_reasoning_effort_omitted_when_unset():
    fake = FakeOpenAI(lambda kw: tool_response("crc"))
    GrokClient(client=fake, model="m", reasoning_effort="").round1("crc?", True, NOW)
    assert "reasoning_effort" not in fake.calls[0]


def test_reasoning_effort_rejected_falls_back_without_it():
    class BadRequest(Exception):
        status_code = 400

    def responder(kw):
        if "reasoning_effort" in kw:
            raise BadRequest("Argument not supported: reasoning_effort")
        return tool_response("crc")
    fake = FakeOpenAI(responder)
    g = GrokClient(client=fake, model="m", reasoning_effort="none")
    assert g.round1("crc?", True, NOW).destination_place_id == "crc"
    assert len(fake.calls) == 2 and "reasoning_effort" not in fake.calls[1]
    g.round1("crc?", True, NOW)  # param stays dropped afterwards
    assert len(fake.calls) == 3 and "reasoning_effort" not in fake.calls[2]


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(GrokError):
        GrokClient()
