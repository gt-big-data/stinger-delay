from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.core import fallback

TZ = ZoneInfo("America/New_York")
NOON = datetime(2026, 3, 3, 12, 0, tzinfo=TZ)


@pytest.mark.parametrize("text,now,dest,origin,deadline", [
    ("Can I make it to West Village by 12:15?", NOON, "west_village", "PIN", "12:15"),
    ("WV in 10 min?", NOON, "west_village", "PIN", "12:10"),
    ("culc by noon", datetime(2026, 3, 3, 11, 30, tzinfo=TZ), "culc", "PIN", "12:00"),
    ("I'm at North Ave Apts, can I make my 9:30 in Klaus?", datetime(2026, 3, 3, 9, 20, tzinfo=TZ),
     "klaus", "north_ave_apts", "09:30"),
    ("from klaus to the crc by 1", NOON, "crc", "klaus", "13:00"),
    ("how long till a bus to west village", NOON, "west_village", "PIN", None),
    ("can I get to hogwarts by 3pm", NOON, "UNKNOWN", "PIN", "15:00"),
])
def test_local_intent(text, now, dest, origin, deadline):
    i = fallback.local_intent(text, now)
    assert (i.tool_called, i.destination_place_id, i.origin_place_id, i.deadline_hhmm) == (True, dest, origin, deadline)


def test_local_intent_off_topic():
    assert fallback.local_intent("write me a haiku about cats", NOON).tool_called is False


def test_check_reply_allows_12h_and_rejects_unknown_numbers():
    facts = {"best": {"arrive": "13:05", "bus_in_min": 4}, "walk_only": {"minutes": 19, "arrive": "13:20"}}
    assert fallback.check_reply("Bus in 4 min, arrive 1:05. Walking takes 19 min.", facts)
    assert fallback.check_reply("Bus in 5 min, arrive 1:05.", facts) is None
    assert fallback.check_reply("Arrive 13:06.", facts) is None
    assert fallback.check_reply("ok [LIVE]", facts) == "ok"
