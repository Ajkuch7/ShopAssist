"""Human escalation tool."""

from langchain_core.tools import tool

from app.db.queries import add_escalation
from app.tools.common import run_audited


@tool("escalate_to_human")
def escalate_to_human_tool(summary: str) -> dict[str, object]:
	"""Save a concise customer-care escalation case."""

	def operation(context):
		case = add_escalation(context.customer_id, summary)
		return {"case_id": case.id, "status": "escalated", "summary": summary}

	return run_audited("escalate_to_human", {"summary": summary}, operation)