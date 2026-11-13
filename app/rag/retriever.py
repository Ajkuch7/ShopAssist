"""Semantic search over the persistent policy and product collections."""

from typing import Any

from app.rag.ingest import POLICY_COLLECTION, PRODUCT_COLLECTION, _store


def _result(document: Any, score: float) -> dict[str, Any]:
	return {"content": document.page_content, "source": document.metadata.get("source", ""), "metadata": document.metadata, "score": score}


def search_policy(question: str, k: int = 3) -> list[dict[str, Any]]:
	"""Return the closest policy chunks with their source paths."""

	return [_result(document, score) for document, score in _store(POLICY_COLLECTION).similarity_search_with_score(question, k=k)]


def search_products_semantic(
	description: str,
	max_price: float | None = None,
	category: str | None = None,
	k: int = 5,
) -> list[dict[str, Any]]:
	"""Return semantic product matches constrained by price and category."""

	filters: list[dict[str, Any]] = []
	if max_price is not None:
		filters.append({"price": {"$lte": max_price}})
	if category:
		filters.append({"category": category.lower()})
	where: dict[str, Any] | None = None
	if len(filters) == 1:
		where = filters[0]
	elif filters:
		where = {"$and": filters}
	store = _store(PRODUCT_COLLECTION)
	results = store.similarity_search_with_score(description, k=k, filter=where)
	return [_result(document, score) for document, score in results]