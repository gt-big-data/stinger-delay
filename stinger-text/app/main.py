"""FastAPI entry for the data and routing layer."""

from fastapi import FastAPI

from app.api import router as data_router
from app.data import clock
from app.data.sources import mode

app = FastAPI(title="StingerText")
app.include_router(data_router)


@app.get("/")
def root():
    return {"service": "stinger-text", "mode": mode(), "now": clock.now().isoformat()}
