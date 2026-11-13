"""FastAPI routes for ShopAssist."""

from fastapi import APIRouter
from fastapi import HTTPException
import httpx

from app.agent.graph import chat_with_tools
from app.api.schemas import ChatRequest, ChatResponse, HealthResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
	"""Send a message through the session-aware agent."""

	try:
		result = chat_with_tools(request.message, request.session_id, request.customer_id)
	except httpx.HTTPError as error:
		logger.exception("Ollama request failed for session %s", request.session_id)
		raise HTTPException(
			status_code=503,
			detail="The local language model is unavailable. Start Ollama and try again.",
		) from error
	return ChatResponse(**result)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
	"""Report that the API process is available."""

	return HealthResponse(status="ok")
