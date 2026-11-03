import os
import re

from app.messaging import admin, session


def allow(user_id: str, text: str | None, has_pin: bool) -> tuple[bool, str | None]:
    trigger = os.environ.get("TRIGGER_WORD", "").strip()
    if not trigger:
        return True, text
    if user_id in admin.admin_handles():
        return True, text
    m = re.match(rf"\s*{re.escape(trigger)}(?:[\s,:]+|$)", text or "", re.I)
    if m:
        session.open_window(user_id)
        return True, (text or "")[m.end():].strip()
    if session.in_window(user_id):
        session.open_window(user_id)  # restart the window
        return True, text
    return False, None
