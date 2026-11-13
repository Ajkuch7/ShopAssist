"""HTTP request and response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
	"""A customer chat message."""

	session_id: str = Field(min_length=1)
	customer_id: int = Field(gt=0)
	message: str = Field(min_length=1)


class ChatResponse(BaseModel):
	"""The agent reply and tools used to produce it."""

	reply: str
	tools_called: list[str]


class HealthResponse(BaseModel):
	"""Service health response."""

	status: str
