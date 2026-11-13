"""Product recommendation and mock purchase tools."""

from langchain_core.tools import tool

from app.db.queries import create_mock_order, get_product
from app.rag.retriever import search_products_semantic
from app.tools.common import run_audited


@tool("recommend_products")
def recommend_products_tool(description: str, max_price: float | None = None, category: str | None = None) -> list[dict[str, object]]:
	"""Recommend up to three synthetic products using semantic search and filters."""

	def operation(context):
		results = search_products_semantic(description, max_price, category, k=3)
		return [
			{"product_id": result["metadata"].get("product_id"), "name": result["metadata"].get("name"), "price": result["metadata"].get("price"), "rating": result["metadata"].get("rating", 4.5), "key_features": result["metadata"].get("key_features", result["content"]), "reason": f"Matches your request for {description}."}
			for result in results
		]

	return run_audited("recommend_products", {"description": description, "max_price": max_price, "category": category}, operation)


@tool("buy_with_credit")
def buy_with_credit_tool(product_id: int, credit_amount: float) -> dict[str, object]:
	"""Create a synthetic order using available store credit."""

	def operation(context):
		product = get_product(product_id)
		if product is None:
			return {"decision": "deny", "message": "I could not find that product."}
		order = create_mock_order(context.customer_id, product)
		if credit_amount >= product.price:
			return {"decision": "approve", "order_id": order.order_id, "price": product.price, "pay_difference": 0, "credit_leftover": credit_amount - product.price}
		return {"decision": "approve", "order_id": order.order_id, "price": product.price, "pay_difference": product.price - credit_amount, "credit_leftover": 0}

	return run_audited("buy_with_credit", {"product_id": product_id, "credit_amount": credit_amount}, operation)