from fastapi import FastAPI

from app.messaging import webhook

app = FastAPI()
app.include_router(webhook.router)
