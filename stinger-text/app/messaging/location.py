"""Location pin parsing (owner: A, task A4). STUB from C1.

extract_latlng(text) pulls coordinates out of a CL.loc.vcf body or a pasted
maps.apple.com / maps.google.com link. Not a frozen contract; A may rename.
"""
from __future__ import annotations

import re
from typing import Optional

from app.models import LatLng

_APPLE_LL = re.compile(r"ll=(-?\d+\.\d+)\\?,(-?\d+\.\d+)")
_GOOGLE_AT = re.compile(r"[@?&](?:q=|query=)?(-?\d+\.\d+),\s*(-?\d+\.\d+)")


def extract_latlng(text: str) -> Optional[LatLng]:
    if not text:
        return None
    m = _APPLE_LL.search(text)
    if m is None and ("google." in text or "goo.gl" in text):
        m = _GOOGLE_AT.search(text)
    if m is None:
        return None
    return LatLng(float(m.group(1)), float(m.group(2)))
