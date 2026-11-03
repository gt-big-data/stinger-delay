import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from scrub_fixture import scrub_text, scrub_value  # noqa: E402


def test_json_payload_is_scrubbed() -> None:
    payload = {
        "type": "new-message",
        "data": {
            "text": "mail me at jane.doe@gmail.com or (404) 555-1234",
            "handle": {"address": "+14045551234", "firstName": "Jane", "lastName": "Doe", "displayName": "Jane Doe"},
            "chats": [{"guid": "iMessage;-;+14045551234"}],
            "latitude": 33.9, "longitude": -84.1,
            "url": "https://maps.apple.com/?ll=33.90123,-84.12345&q=x",
        },
    }
    out = json.dumps(scrub_value(payload))
    assert "4045551234" not in out and "gmail" not in out and "Jane" not in out
    assert "33.90123" not in out and "-84.12345" not in out
    d = json.loads(out)["data"]
    assert d["handle"]["address"] == "+15550001111"
    assert d["chats"][0]["guid"] == "iMessage;-;+15550001111"
    assert d["handle"]["displayName"] == "Test User"
    assert (d["latitude"], d["longitude"]) == (33.7772, -84.3956)
    assert "ll=33.77720,-84.39560" in d["url"]


def test_vcf_is_scrubbed() -> None:
    vcf = "BEGIN:VCARD\nFN:Jane Doe\nN:Doe;Jane;;;\nTEL;type=CELL:+1 404-555-1234\nEMAIL:j@x.org\nURL:https://maps.apple.com/?ll=33.9%2C-84.1\nEND:VCARD\n"
    out = scrub_text(vcf)
    assert "Jane" not in out and "404" not in out and "j@x.org" not in out
    assert "FN:Test User" in out
    assert scrub_text("+15550001111") == "+15550001111"


def test_bare_ten_digit_number_is_scrubbed() -> None:
    out = json.dumps(scrub_value({"handle": {"uncanonicalizedId": "4045551234"}, "dateCreated": 1793669849160}))
    assert "4045551234" not in out and "1793669849160" in out
