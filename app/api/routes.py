"""FastAPI routes for the ShopAssist state-machine agent."""

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select, text

from app.agent.graph import reset_session, run_turn
from app.api.schemas import ChatRequest, ChatResponse, ChatStartRequest, CustomerResponse, HealthResponse, ResetRequest
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Customer, Order
from app.db.queries import get_demo_customers
from app.db.session import session_scope


router = APIRouter()
logger = get_logger(__name__)


def _ollama_error() -> str | None:
	"""Return a friendly error when Ollama or the configured model is unavailable."""

	try:
		settings = get_settings()
		response = httpx.get(f"{settings.ollama.base_url.rstrip('/')}/api/tags", timeout=2)
		response.raise_for_status()
		models = response.json().get("models", [])
		configured_model = settings.models.chat
		if not any(model.get("name") == configured_model for model in models):
			return f"Support is unavailable because the model '{configured_model}' is not installed. Run: ollama pull {configured_model}"
		return None
	except (httpx.HTTPError, ValueError):
		return "Support is unavailable because Ollama is not running. Start Ollama and try again."


def _database_error() -> str | None:
	"""Return a friendly error when SQLite is unavailable or unseeded."""

	try:
		with session_scope() as session:
			customers = session.scalar(select(func.count(Customer.id)))
			orders = session.scalar(select(func.count(Order.order_id)))
	except Exception:
		return "Support is unavailable because the database cannot be reached."
	if not customers or not orders:
		return "Support is unavailable because the synthetic database is empty. Run: .\\.venv\\Scripts\\python.exe -m app.db.seed"
	return None


def _require_ollama() -> None:
	detail = _ollama_error()
	if detail:
		raise HTTPException(status_code=503, detail=detail)


def _require_database() -> None:
	detail = _database_error()
	if detail:
		raise HTTPException(status_code=503, detail=detail)


def _chat_response(result: dict[str, Any]) -> ChatResponse:
	return ChatResponse(**result)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
	"""Process one free-text customer turn."""

	logger.info("Chat request session=%s customer=%s", request.session_id, request.customer_id)
	_require_ollama()
	_require_database()
	try:
		return _chat_response(run_turn(request.message, request.session_id, request.customer_id, use_llm=True))
	except httpx.HTTPError as error:
		logger.exception("Ollama request failed for session %s", request.session_id)
		raise HTTPException(status_code=503, detail="The local language model is unavailable. Start Ollama and try again.") from error


@router.post("/chat/start", response_model=ChatResponse)
def start_chat(request: ChatStartRequest) -> ChatResponse:
	"""Start or restart a session with the greeting and recent orders."""

	logger.info("Chat start session=%s customer=%s", request.session_id, request.customer_id)
	_require_ollama()
	_require_database()
	reset_session(request.session_id)
	return _chat_response(run_turn("hello", request.session_id, request.customer_id))


@router.get("/customers", response_model=list[CustomerResponse])
def customers() -> list[CustomerResponse]:
	"""Return the synthetic demo customers."""

	_require_database()
	return [CustomerResponse(id=customer.id, name=customer.name) for customer in get_demo_customers()]


@router.post("/session/reset")
def reset(request: ResetRequest) -> dict[str, str]:
	"""Clear one in-memory conversation session."""

	logger.info("Reset session=%s", request.session_id)
	reset_session(request.session_id)
	return {"status": "reset", "session_id": request.session_id}


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
	"""Report API, Ollama, and SQLite reachability."""

	ollama_detail = _ollama_error()
	try:
		with session_scope() as session:
			session.execute(text("SELECT 1"))
			customers = session.scalar(select(func.count(Customer.id)))
			orders = session.scalar(select(func.count(Order.order_id)))
			database_status = "ok" if customers and orders else "empty"
	except Exception as error:
		logger.exception("Database health check failed")
		database_status = "error"
		detail = str(error)
	else:
		detail = None
	ollama_status = "ok" if ollama_detail is None else "error"
	status = "ok" if ollama_status == database_status == "ok" else "degraded"
	return HealthResponse(status=status, ollama=ollama_status, database=database_status, detail=ollama_detail or detail)
