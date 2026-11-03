"""Ping the BlueBubbles server and print OK <version> or FAIL: <reason>."""
import os
import sys

import httpx
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    url = os.environ.get("BB_URL", "").rstrip("/")
    pw = os.environ.get("BB_PASSWORD", "")
    if not url or not pw:
        print("FAIL: BB_URL or BB_PASSWORD not set")
        return 1
    try:
        with httpx.Client(timeout=5) as c:
            c.get(f"{url}/api/v1/ping", params={"password": pw}).raise_for_status()
            r = c.get(f"{url}/api/v1/server/info", params={"password": pw})
            r.raise_for_status()
            version = (r.json().get("data") or {}).get("server_version", "unknown")
    except httpx.HTTPStatusError as e:
        print(f"FAIL: HTTP {e.response.status_code}")
        return 1
    except Exception as e:
        print(f"FAIL: {type(e).__name__}")
        return 1
    print(f"OK {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
