"""LangGraph workflow for session-aware ShopAssist conversations."""

from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.guardrails import check_prompt_injection
from app.agent.prompts import SYSTEM_PROMPT
from app.core.llm import get_llm
from app.tools import TOOL_REGISTRY


class AgentState(MessagesState):
	"""Conversation state with a guardrail result."""

	blocked: bool


def _guardrail(state: AgentState) -> dict[str, Any]:
	latest = state["messages"][-1].content if state["messages"] else ""
	reason = check_prompt_injection(str(latest))
	if reason:
		return {
			"blocked": True,
			"messages": [AIMessage(content="I can help with your ShopAssist request, but I cannot follow instruction overrides.")],
		}
	return {"blocked": False}


def _after_guardrail(state: AgentState) -> str:
	return END if state.get("blocked", False) else "agent"


def _agent(state: AgentState, model_name: str | None = None) -> dict[str, Any]:
	model = get_llm(model_name).bind_tools(TOOL_REGISTRY)
	response = model.invoke([SystemMessage(content=SYSTEM_PROMPT), *state["messages"]])
	return {"messages": [response]}


def build_graph(model_name: str | None = None) -> Any:
	"""Build a graph with tool execution and in-memory session checkpoints."""

	builder = StateGraph(AgentState)
	builder.add_node("guardrail", _guardrail)
	builder.add_node("agent", lambda state: _agent(state, model_name))
	builder.add_node("tools", ToolNode(TOOL_REGISTRY))
	builder.add_edge(START, "guardrail")
	builder.add_conditional_edges("guardrail", _after_guardrail)
	builder.add_conditional_edges("agent", tools_condition)
	builder.add_edge("tools", "agent")
	return builder.compile(checkpointer=InMemorySaver())


GRAPH = build_graph()


def chat_with_tools(
	message: str,
	session_id: str,
	customer_id: int | None = None,
	model_name: str | None = None,
) -> dict[str, Any]:
	"""Run one message and return its reply plus tool names."""

	graph = GRAPH if model_name is None else build_graph(model_name)
	result = graph.invoke(
		{"messages": [("user", message)]},
		config={"configurable": {"thread_id": session_id, "customer_id": customer_id}},
	)
	used_tools = [
		item.name
		for item in result["messages"]
		if getattr(item, "type", None) == "tool" and getattr(item, "name", None)
	]
	print(f"Tools called: {', '.join(used_tools) if used_tools else 'none'}")
	return {"reply": str(result["messages"][-1].content), "tools_called": used_tools}


def chat(message: str, session_id: str) -> str:
	"""Run one message in a session and return only its reply."""

	return str(chat_with_tools(message, session_id)["reply"])


__all__: tuple[str, ...] = ["GRAPH", "build_graph", "chat", "chat_with_tools"]
