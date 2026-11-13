"""Customer order tools."""

from langchain_core.tools import tool

from app.db.queries import get_recent_orders
from app.tools.common import run_audited


@tool("get_recent_orders")
def get_recent_orders_tool() -> list[dict[str, object]]:
	"""List the customer's five most recent orders."""

	def operation(context):
		return [
			{"order_id": order.order_id, "item_name": order.item_name, "price": order.amount, "status": order.status, "date": order.order_date.isoformat()}
			for order in get_recent_orders(context.customer_id)
		]

	return run_audited("get_recent_orders", {}, operation)