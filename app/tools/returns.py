"""Return-method and exchange tools."""

from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

from app.db.queries import create_return_request, get_order, get_product
from app.rules.engine import get_return_methods
from app.rules.loader import get_rule
from app.tools.common import run_audited


@tool("get_return_methods")
def get_return_methods_tool(order_id: int, reason: str) -> dict[str, object]:
	"""Show return methods for the customer's order."""

	def operation(context):
		if get_order(context.customer_id, order_id) is None:
			return {"decision": "deny", "message": "I could not find that order for this customer."}
		return {"order_id": order_id, **get_return_methods(reason)}

	return run_audited("get_return_methods", {"order_id": order_id, "reason": reason}, operation)


@tool("create_exchange")
def create_exchange_tool(order_id: int, replacement_product_id: int, return_method: str, slot: str) -> dict[str, object]:
	"""Create an exchange for the customer's order and replacement product."""

	def operation(context):
		if return_method not in {"ups_dropoff", "courier_pickup"}:
			return {"decision": "deny", "message": "Please choose ups_dropoff or courier_pickup."}
		if get_order(context.customer_id, order_id) is None:
			return {"decision": "deny", "message": "I could not find that order for this customer."}
		if get_product(replacement_product_id) is None:
			return {"decision": "deny", "message": "I could not find that replacement product."}
		approval = context.approved_eligibility.get(order_id)
		waive_fee = bool(approval and approval[0].waive_pickup_fee)
		fee = 0 if return_method == "ups_dropoff" or waive_fee else get_rule("pickup_fee_usd")
		request = create_return_request(context.customer_id, order_id, replacement_product_id, return_method, slot, fee, datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3))
		return {"return_id": request.id, "fee": fee, "replacement_ship_date": request.replacement_ship_date.isoformat()}

	return run_audited("create_exchange", {"order_id": order_id, "replacement_product_id": replacement_product_id, "return_method": return_method, "slot": slot}, operation)