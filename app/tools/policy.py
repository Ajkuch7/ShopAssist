"""Policy search tool."""

from langchain_core.tools import tool

from app.rag.retriever import search_policy
from app.tools.common import run_audited


@tool("search_policy")
def search_policy_tool(question: str) -> list[dict[str, object]]:
	"""Search synthetic policy documents and return cited sources."""

	return run_audited("search_policy", {"question": question}, lambda context: search_policy(question))