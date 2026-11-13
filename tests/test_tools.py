"""Tests for context-bound customer tools."""

import pytest
from sqlalchemy import select

from app.db.models import AuditLog, Refund, ReturnRequest
from app.db.seed import seed_database
from app.db.session import session_scope
from app.tools.context import SessionContext, use_session_context
from app.tools.refunds import check_refund_eligibility_tool, initiate_refund_tool
from app.tools.returns import create_exchange_tool


@pytest.fixture(autouse=True)
def seeded_database() -> None:
	seed_database()


def test_refund_refuses_without_same_session_eligibility() -> None:
	context = SessionContext(session_id="tool-test-refuse", customer_id=1)
	with use_session_context(context):
		result = initiate_refund_tool.invoke({"order_id": 1001, "method": "original_payment"})

	assert result["decision"] == "deny"
	with session_scope() as session:
		assert session.scalar(select(Refund.id).where(Refund.order_id == 1001)) is None
		assert session.scalar(select(AuditLog.id).where(AuditLog.tool_name == "initiate_refund")) is not None


def test_customer_cannot_touch_another_customers_order() -> None:
	context = SessionContext(session_id="tool-test-identity", customer_id=1)
	with use_session_context(context):
		result = check_refund_eligibility_tool.invoke({"order_id": 1014, "reason": "defective"})

	assert result["rule_code"] == "ORDER_NOT_FOUND"


def test_exchange_fee_is_waived_for_damaged_reason() -> None:
	context = SessionContext(session_id="tool-test-damaged", customer_id=1)
	with use_session_context(context):
		eligibility = check_refund_eligibility_tool.invoke({"order_id": 1001, "reason": "damaged"})
		result = create_exchange_tool.invoke({"order_id": 1001, "replacement_product_id": 2, "return_method": "courier_pickup", "slot": "tomorrow 09:00-12:00"})

	assert eligibility["decision"] == "approve"
	assert result["fee"] == 0


def test_exchange_fee_is_ten_dollars_for_changed_mind() -> None:
	context = SessionContext(session_id="tool-test-changed-mind", customer_id=1)
	with use_session_context(context):
		check_refund_eligibility_tool.invoke({"order_id": 1006, "reason": "changed_mind"})
		result = create_exchange_tool.invoke({"order_id": 1006, "replacement_product_id": 3, "return_method": "courier_pickup", "slot": "tomorrow 09:00-12:00"})

	assert result["fee"] == 10
	with session_scope() as session:
		assert session.scalar(select(ReturnRequest.id).where(ReturnRequest.order_id == 1006)) is not None