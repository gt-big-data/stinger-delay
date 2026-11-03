"""Scrub a JSON or VCF file: python scrub_fixture.py <in> <out>."""
import json
import re
import sys
from pathlib import Path
from typing import Any

PHONE = "+15550001111"
EMAIL = "user@example.com"
LAT, LON = "33.77720", "-84.39560"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"\+\d{10,15}|(?<![\d.])\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?!\d)|(?<![\d.])\d{10}(?![\d.])")  # last: bare 10 digits, e.g. uncanonicalizedId
COORD_RE = re.compile(r"-?\d{1,3}\.\d{3,}(,|%2C|;|,\s)-?\d{1,3}\.\d{3,}", re.I)
NAME_KEYS = {"firstName": "Test", "lastName": "User", "displayName": "Test User"}
COORD_KEYS = {"latitude": float(LAT), "lat": float(LAT), "longitude": float(LON), "lng": float(LON), "lon": float(LON)}


def scrub_text(s: str) -> str:
    s = EMAIL_RE.sub(EMAIL, s)
    s = PHONE_RE.sub(PHONE, s)
    s = COORD_RE.sub(lambda m: f"{LAT}{m.group(1)}{LON}", s)
    s = re.sub(r"(?im)^(FN[^:\n]*):.*$", r"\1:Test User", s)
    s = re.sub(r"(?im)^(N[^:\n]*):.*$", r"\1:User;Test;;;", s)
    return s


def scrub_value(v: Any) -> Any:
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if k in NAME_KEYS and isinstance(x, str):
                out[k] = NAME_KEYS[k]
            elif k in COORD_KEYS and isinstance(x, (int, float)):
                out[k] = COORD_KEYS[k]
            else:
                out[scrub_text(k)] = scrub_value(x)
        return out
    if isinstance(v, list):
        return [scrub_value(x) for x in v]
    if isinstance(v, str):
        return scrub_text(v)
    return v


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    text = src.read_text()
    if src.suffix.lower() == ".json":
        out = json.dumps(scrub_value(json.loads(text)), indent=2)
    else:
        out = scrub_text(text)
    dst.write_text(out)


if __name__ == "__main__":
    main()
