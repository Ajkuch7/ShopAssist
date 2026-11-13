"""HTTP request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
	"""A customer chat message."""

	session_id: str = Field(min_length=1)
	customer_id: int = Field(gt=0)
	message: str = Field(min_length=1)


class ChatResponse(BaseModel):
	"""Complete customer-facing state-machine turn."""

	reply: str
	quick_replies: list[str]
	orders: list[dict[str, Any]]
	products: list[dict[str, Any]]
	summary_card: dict[str, Any] | None
	tools_used: list[str]
	conversation_ended: bool


class ChatStartRequest(BaseModel):
	"""Identity for starting a new in-memory chat session."""

	session_id: str = Field(min_length=1)
	customer_id: int = Field(gt=0)


class ResetRequest(BaseModel):
	"""Session identifier to clear."""

	session_id: str = Field(min_length=1)


class CustomerResponse(BaseModel):
	id: int
	name: str


class HealthResponse(BaseModel):
	"""API and dependency health status."""

	status: str
	ollama: str
	database: str
	detail: str | None = None
