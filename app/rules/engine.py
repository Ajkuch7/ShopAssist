"""Pure Python return and refund decisions."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from app.db.models import Order, Refund
from app.db.session import session_scope
from app.rules.loader import get_rule


@dataclass(frozen=True)
class EligibilityResult:
	"""The deterministic outcome of a refund eligibility check."""

	decision: str
	rule_code: str
	message: str
	refundable_amount: float | None
	waive_pickup_fee: bool


def _deny(rule_code: str, message: str) -> EligibilityResult:
	return EligibilityResult("deny", rule_code, message, None, False)


def _escalate(rule_code: str, message: str) -> EligibilityResult:
	return EligibilityResult("escalate", rule_code, message, None, False)


def check_refund_eligibility(customer_id: int, order_id: int, reason: str) -> EligibilityResult:
	"""Check a customer's order against the configured return rules."""

	normalized_reason = reason.strip().lower()
	with session_scope() as session:
		order = session.scalar(select(Order).where(Order.order_id == order_id, Order.customer_id == customer_id))
		if order is None:
			return _deny("ORDER_NOT_FOUND", "I could not find that order for this customer.")
		if order.status.lower() != "delivered":
			return _deny("ORDER_NOT_DELIVERED", "This order is not eligible until it has been delivered.")

		non_returnable = {str(value).lower() for value in get_rule("non_returnable_categories")}
		if order.category.lower() in non_returnable:
			return _deny("CATEGORY_NOT_RETURNABLE", "This item category is not eligible for a return.")

		valid_reasons = {str(value).lower() for value in get_rule("valid_return_reasons")}
		if normalized_reason not in valid_reasons:
			return _deny("INVALID_REASON", "That return reason is not available for this request.")

		window_days = get_rule("return_window_days").get(order.category.lower())
		if window_days is None or order.delivered_at is None:
			return _deny("RETURN_WINDOW_UNAVAILABLE", "I could not confirm a return window for this item.")
		delivered_at = order.delivered_at.replace(tzinfo=timezone.utc) if order.delivered_at.tzinfo is None else order.delivered_at
		if datetime.now(timezone.utc) - delivered_at > timedelta(days=window_days):
			return _deny("RETURN_WINDOW_EXPIRED", "The return window for this item has ended.")

		already_refunded = order.refunded or session.scalar(select(Refund.id).where(Refund.order_id == order_id).limit(1)) is not None
		if already_refunded:
			return _deny("ALREADY_REFUNDED", "This order has already been refunded.")

		amount = float(order.amount)
		if amount > float(get_rule("auto_refund_max_usd")):
			return _escalate("AMOUNT_REQUIRES_REVIEW", "This refund needs a specialist review before it can proceed.")

		cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
		refund_count = session.scalar(
			select(func.count(Refund.id)).where(Refund.customer_id == customer_id, Refund.created_at >= cutoff)
		)
		if refund_count > int(get_rule("max_refunds_per_30_days")):
			return _escalate("REFUND_FREQUENCY_REVIEW", "This refund needs a specialist review before it can proceed.")

		waived_reasons = {str(value).lower() for value in get_rule("pickup_fee_waived_reasons")}
		return EligibilityResult("approve", "REFUND_ELIGIBLE", "This refund is eligible for approval.", amount, normalized_reason in waived_reasons)


def get_return_methods(reason: str) -> dict[str, Any]:
	"""Return free drop-off and courier pickup options for a return."""

	now = datetime.now(timezone.utc)
	slots = [(now + timedelta(days=offset)).strftime("%Y-%m-%d 09:00-12:00 UTC") for offset in range(1, 4)]
	waived = reason.strip().lower() in {str(value).lower() for value in get_rule("pickup_fee_waived_reasons")}
	return {
		"ups_dropoff": {"fee_usd": 0, "locations": ["UPS Store - Downtown", "UPS Store - Northside", "UPS Store - West End"]},
		"courier_pickup": {"fee_usd": 0 if waived else get_rule("pickup_fee_usd"), "fee_waived": waived, "time_slots": slots},
	}


__all__: tuple[str, ...] = ["EligibilityResult", "check_refund_eligibility", "get_return_methods"]
