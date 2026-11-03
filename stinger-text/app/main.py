"""StingerText FastAPI app.

B's stop and plan routes stay registered. The BlueBubbles webhook sits
beside them. The live-feed poller starts with the process and stops on shutdown.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from app.api import router as data_router  # noqa: E402
from app.data import clock, sources  # noqa: E402
from app.messaging import webhook  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.getLogger("stingertext").info(
        "StingerText up: mode=%s clock=%s", sources.mode(), clock.now().isoformat()
    )
    sources.ensure_poller()
    yield
    sources.stop_poller()


app = FastAPI(title="StingerText", lifespan=lifespan)
app.include_router(data_router)
app.include_router(webhook.router)


@app.get("/")
def root():
    return {"service": "stinger-text", "mode": sources.mode(), "now": clock.now().isoformat()}
