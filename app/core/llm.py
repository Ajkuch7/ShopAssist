"""Factories for the configured local Ollama chat and embedding models."""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import get_settings


def get_llm(model_name: str | None = None) -> BaseChatModel:
    """Create the configured Ollama chat model."""

    settings = get_settings()
    return ChatOllama(
        model=model_name or settings.models.chat,
        base_url=settings.ollama.base_url,
        temperature=settings.models.temperature,
    )


def get_embeddings() -> Embeddings:
    """Create the configured Ollama embedding model."""

    settings = get_settings()
    return OllamaEmbeddings(
        model=settings.models.embedding,
        base_url=settings.ollama.base_url,
    )


__all__: tuple[str, ...] = ["get_embeddings", "get_llm"]
