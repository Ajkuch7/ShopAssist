"""Deterministic tests for rules loading and refund eligibility."""

import pytest

from app.db.seed import seed_database
from app.rules.engine import check_refund_eligibility, get_return_methods
from app.rules.loader import get_rule, reload


@pytest.fixture(autouse=True)
def seeded_database() -> None:
	seed_database()


def test_valid_refund() -> None:
	result = check_refund_eligibility(1, 1001, "defective")
	assert (result.decision, result.rule_code, result.refundable_amount) == ("approve", "REFUND_ELIGIBLE", 120.0)


def test_late_return() -> None:
	assert check_refund_eligibility(1, 1002, "changed_mind").rule_code == "RETURN_WINDOW_EXPIRED"


def test_non_returnable_category() -> None:
	assert check_refund_eligibility(1, 1003, "changed_mind").rule_code == "CATEGORY_NOT_RETURNABLE"


def test_already_refunded() -> None:
	assert check_refund_eligibility(1, 1013, "defective").rule_code == "ALREADY_REFUNDED"


def test_in_transit_order() -> None:
	assert check_refund_eligibility(1, 1005, "changed_mind").rule_code == "ORDER_NOT_DELIVERED"


def test_wrong_customer_cannot_access_order() -> None:
	assert check_refund_eligibility(1, 1014, "defective").rule_code == "ORDER_NOT_FOUND"


def test_bad_reason() -> None:
	assert check_refund_eligibility(1, 1001, "price_match").rule_code == "INVALID_REASON"


def test_amount_above_auto_refund_limit_escalates() -> None:
	result = check_refund_eligibility(1, 1008, "defective")
	assert (result.decision, result.rule_code) == ("escalate", "AMOUNT_REQUIRES_REVIEW")


def test_four_recent_refunds_escalate() -> None:
	result = check_refund_eligibility(4, 2001, "defective")
	assert (result.decision, result.rule_code) == ("escalate", "REFUND_FREQUENCY_REVIEW")


def test_damaged_pickup_fee_is_waived() -> None:
	methods = get_return_methods("damaged")
	assert methods["courier_pickup"]["fee_usd"] == 0
	assert methods["courier_pickup"]["fee_waived"] is True


def test_changed_mind_pickup_fee_is_ten_dollars() -> None:
	methods = get_return_methods("changed_mind")
	assert methods["courier_pickup"]["fee_usd"] == 10
	assert methods["courier_pickup"]["fee_waived"] is False


def test_dropoff_has_three_locations() -> None:
	assert len(get_return_methods("defective")["ups_dropoff"]["locations"]) == 3


def test_pickup_has_three_time_slots() -> None:
	assert len(get_return_methods("defective")["courier_pickup"]["time_slots"]) == 3


def test_valid_reason_is_case_insensitive() -> None:
	assert check_refund_eligibility(1, 1001, "DAMAGED").decision == "approve"


def test_reason_whitespace_is_ignored() -> None:
	assert check_refund_eligibility(1, 1001, " defective ").decision == "approve"


def test_return_window_rules_are_loaded() -> None:
	windows = get_rule("return_window_days")
	assert windows["electronics"] == 7
	assert windows["clothing"] == 30


def test_original_payment_refund_timing_rule() -> None:
	assert get_rule("refund_days_original_payment") == "3-5 business days"


def test_store_credit_is_instant_rule() -> None:
	assert get_rule("store_credit_instant") is True


def test_max_refund_rule() -> None:
	assert get_rule("auto_refund_max_usd") == 500


def test_non_returnable_rule() -> None:
	assert set(get_rule("non_returnable_categories")) == {"innerwear", "grocery"}


def test_loader_reload_reads_changes(tmp_path, monkeypatch) -> None:
	from app.rules import loader

	path = tmp_path / "rules.yaml"
	path.write_text("temporary: 1\n", encoding="utf-8")
	monkeypatch.setattr(loader, "RULES_PATH", path)
	reload()
	assert get_rule("temporary") == 1
	path.write_text("temporary: 2\n", encoding="utf-8")
	reload()
	assert get_rule("temporary") == 2
	reload()


def test_missing_order_is_neutral() -> None:
	result = check_refund_eligibility(1, 9999, "defective")
	assert result.decision == "deny"
	assert "fraud" not in result.message.lower()


def test_denial_messages_do_not_expose_internal_checks() -> None:
	result = check_refund_eligibility(1, 1002, "changed_mind")
	assert all(word not in result.message.lower() for word in ("fraud", "risk", "abuse"))