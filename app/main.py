from fastapi import FastAPI

from app.api import reviews, webhooks
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title="CodeGuardian AI", version="0.1.0")

app.include_router(webhooks.router)
app.include_router(reviews.router)


@app.get("/health")
def health():
    return {"status": "ok"}
