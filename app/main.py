"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from time import perf_counter

from app.api.routes import router
from app.core.logging import configure_logging
from app.core.config import get_settings
from app.core.logging import get_logger

configure_logging()
logger = get_logger(__name__)
app = FastAPI(title="ShopAssist API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=get_settings().cors.origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
	start = perf_counter()
	response = await call_next(request)
	logger.info("%s %s -> %s in %.3fs", request.method, request.url.path, response.status_code, perf_counter() - start)
	return response


app.include_router(router)
