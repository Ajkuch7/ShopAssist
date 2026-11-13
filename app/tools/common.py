"""Shared tool auditing and context helpers."""

import json
from collections.abc import Callable
from typing import Any, TypeVar

from app.db.queries import add_audit_log
from app.tools.context import SessionContext, get_session_context


Result = TypeVar("Result")


def run_audited(tool_name: str, inputs: dict[str, Any], operation: Callable[[SessionContext], Result]) -> Result:
	"""Run a tool operation and persist its input/output audit record."""

	context = get_session_context()
	try:
		result = operation(context)
		output = json.dumps(result, default=str)
		rule_code = result.get("rule_code") if isinstance(result, dict) else None
		add_audit_log(context.session_id, context.customer_id, tool_name, json.dumps(inputs, default=str), output, rule_code)
		return result
	except Exception as error:
		output = json.dumps({"error": str(error)})
		add_audit_log(context.session_id, context.customer_id, tool_name, json.dumps(inputs, default=str), output)
		raise