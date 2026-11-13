"""Refund eligibility and initiation tools."""

from dataclasses import asdict

from langchain_core.tools import tool

from app.db.queries import create_refund
from app.rules.engine import check_refund_eligibility
from app.rules.loader import get_rule
from app.tools.common import run_audited


@tool("check_refund_eligibility")
def check_refund_eligibility_tool(order_id: int, reason: str) -> dict[str, object]:
	"""Check whether the customer's order can receive a refund."""

	def operation(context):
		result = check_refund_eligibility(context.customer_id, order_id, reason)
		if result.decision == "approve":
			context.approved_eligibility[order_id] = (result, reason.strip().lower())
		return asdict(result)

	return run_audited("check_refund_eligibility", {"order_id": order_id, "reason": reason}, operation)


@tool("initiate_refund")
def initiate_refund_tool(order_id: int, method: str) -> dict[str, object]:
	"""Create a refund only after this session approved the same order."""

	def operation(context):
		if method not in {"original_payment", "store_credit"}:
			return {"decision": "deny", "message": "Please choose original_payment or store_credit."}
		approval = context.approved_eligibility.get(order_id)
		if approval is None or approval[0].decision != "approve":
			return {"decision": "deny", "message": "Please check refund eligibility for this order first."}
		refund = create_refund(context.customer_id, order_id, method)
		timeline = "instant" if method == "store_credit" and get_rule("store_credit_instant") else get_rule("refund_days_original_payment")
		return {"decision": "approve", "refund_id": refund.id, "amount": refund.amount, "method": method, "timeline": timeline}

	return run_audited("initiate_refund", {"order_id": order_id, "method": method}, operation)