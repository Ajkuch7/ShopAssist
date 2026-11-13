"""Tool registry consumed by the LangGraph agent."""

from app.tools.escalation import escalate_to_human_tool
from app.tools.orders import get_recent_orders_tool
from app.tools.policy import search_policy_tool
from app.tools.products import buy_with_credit_tool, recommend_products_tool
from app.tools.refunds import check_refund_eligibility_tool, initiate_refund_tool
from app.tools.returns import create_exchange_tool, get_return_methods_tool


TOOL_REGISTRY = [
	get_recent_orders_tool,
	check_refund_eligibility_tool,
	initiate_refund_tool,
	get_return_methods_tool,
	create_exchange_tool,
	recommend_products_tool,
	buy_with_credit_tool,
	search_policy_tool,
	escalate_to_human_tool,
]

__all__: tuple[str, ...] = ["TOOL_REGISTRY"]
