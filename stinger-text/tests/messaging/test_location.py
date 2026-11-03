import asyncio
from pathlib import Path

import pytest

from app.messaging.location import extract, parse_map_text, parse_vcf
from app.models import LatLng

KLAUS = LatLng(33.7772, -84.3956)


def test_fixture_parses_to_klaus():
    # TODO(SETUP): switch to the scrubbed real CL.loc.vcf once captured.
    p = Path(__file__).parents[2] / "fixtures" / "CL.PLACEHOLDER.loc.vcf"
    assert parse_vcf(p.read_text()) == KLAUS


@pytest.mark.parametrize("s", [
    "http://maps.apple.com/?ll=33.7772,-84.3956&q=My%20Location",
    r"http://maps.apple.com/?ll=33.7772\,-84.3956&q=x",
    "http://maps.apple.com/?ll=33.7772%2C-84.3956",
    "https://maps.apple.com/place?coordinate=33.7772,-84.3956&name=Klaus&map=explore",
    "https://maps.apple.com/?q=33.7772,-84.3956",
    "https://www.google.com/maps/@33.7772,-84.3956,17z",
    "https://www.google.com/maps?q=33.7772,-84.3956",
    "geo:33.7772,-84.3956",
    "GEO:33.7772;-84.3956",
])
def test_patterns(s):
    assert parse_map_text(s) == KLAUS


@pytest.mark.parametrize("s", [
    "https://maps.apple.com/p/abc123xyz",
    "http://maps.apple.com/?ll=200,300",
    "http://maps.apple.com/?ll=0,0",
    "can I make it to Klaus",
])
def test_none(s):
    assert parse_map_text(s) is None


class Fake:
    def __init__(self, data=b"GEO:33.7772;-84.3956"):
        self.data, self.calls = data, []

    async def download_attachment(self, guid):
        self.calls.append(guid)
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


def test_only_location_file_downloaded():
    c = Fake()
    atts = [{"guid": "img", "mimeType": "image/jpeg", "transferName": "a.jpg"},
            {"guid": "loc", "mimeType": "text/x-vlocation", "transferName": "CL.loc.vcf"}]
    assert asyncio.run(extract(None, atts, c)) == KLAUS
    assert c.calls == ["loc"]


@pytest.mark.parametrize("data", [OSError("boom"), b"\xff\xfe garbage"])
def test_bad_attachment_returns_none(data):
    atts = [{"guid": "loc", "transferName": "x.loc.vcf"}]
    assert asyncio.run(extract(None, atts, Fake(data))) is None


def test_real_maplink_fixture():
    import json
    d = json.loads((Path(__file__).parents[2] / "fixtures" / "bb_maplink.json").read_text())
    assert parse_map_text(d["data"]["text"]) == LatLng(33.77720, -84.39560)
