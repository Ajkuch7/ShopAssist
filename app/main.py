"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(title="ShopAssist API")
app.include_router(router)
