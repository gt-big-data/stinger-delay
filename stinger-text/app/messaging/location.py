import re

from app.models import LatLng

_N = r"(-?\d{1,3}(?:\.\d+)?)"
_SEP = r"(?:\\?,|%2C)"
_PATTERNS = [
    re.compile(r"maps\.apple\.com[^\s]*?[?&]ll=" + _N + _SEP + _N, re.I),
    re.compile(r"maps\.apple\.com[^\s]*?[?&]coordinate=" + _N + _SEP + _N, re.I),  # real share link (A1 capture)
    re.compile(r"maps\.apple\.com[^\s]*?[?&]q=" + _N + _SEP + _N + r"(?![\d.])", re.I),
    re.compile(r"google\.[a-z.]+/maps[^\s]*?@" + _N + _SEP + _N, re.I),
    re.compile(r"google\.[a-z.]+/maps[^\s]*?[?&]q=" + _N + _SEP + _N + r"(?![\d.])", re.I),
    re.compile(r"geo:" + _N + _SEP + _N, re.I),
    re.compile(r"GEO:" + _N + r";" + _N, re.I),
]


def parse_map_text(text: str) -> LatLng | None:
    for p in _PATTERNS:
        m = p.search(text or "")
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180 and (lat, lng) != (0, 0):
                return LatLng(lat, lng)
    return None


def parse_vcf(text: str) -> LatLng | None:
    return parse_map_text(text)


def _is_loc(a: dict) -> bool:
    name = (a.get("transferName") or "").lower()
    return name.endswith(".loc.vcf") or (a.get("mimeType") or "").lower() in ("text/vcard", "text/x-vlocation")


async def extract(text: str | None, attachments: list[dict], client) -> LatLng | None:
    for a in attachments or []:
        if not _is_loc(a):
            continue
        try:
            data = await client.download_attachment(a.get("guid"))
            loc = parse_vcf(data.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if loc:
            return loc
    return parse_map_text(text) if text else None
