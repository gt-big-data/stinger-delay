"""Send one text to an admin handle: send_test.py --to <handle> --text <text>. DRY_RUN=1 prints instead."""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.messaging import bluebubbles


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--to", required=True)
    p.add_argument("--text", required=True)
    a = p.parse_args()
    admins = [h.strip() for h in os.environ.get("ADMIN_HANDLES", "").split(",") if h.strip()]
    if a.to not in admins:
        print("REFUSED: --to is not in ADMIN_HANDLES")
        return 1
    if os.environ.get("DRY_RUN") == "1":
        print(f"DRY_RUN: would send to ...{a.to[-4:]}")
        return 0
    try:
        asyncio.run(bluebubbles.send_text(f"iMessage;-;{a.to}", a.text))
    except Exception as e:
        print(f"FAIL: {type(e).__name__}")
        return 1
    print("SENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
