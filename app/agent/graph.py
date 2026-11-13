"""LangGraph state machine for the customer-care conversation flow."""

import re
from copy import deepcopy
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agent.guardrails import check_prompt_injection
from app.agent.prompts import SYSTEM_PROMPT
from app.core.llm import get_llm
from app.db.queries import get_order
from app.tools.context import SessionContext, use_session_context
from app.tools.escalation import escalate_to_human_tool
from app.tools.orders import get_recent_orders_tool
from app.tools.policy import search_policy_tool
from app.tools.products import buy_with_credit_tool, recommend_products_tool
from app.tools.refunds import check_refund_eligibility_tool, initiate_refund_tool
from app.tools.returns import create_exchange_tool, get_return_methods_tool


class AgentState(TypedDict, total=False):
    """In-memory state for one customer session and one incoming turn."""

    session_id: str
    customer_id: int
    message: str
    step: str
    selected_order: dict[str, Any] | None
    reason: str | None
    chosen_option: str | None
    return_method: str | None
    slot: str | None
    replacement_product: int | None
    refund_method: str | None
    exchange_phase: str | None
    buy_phase: str | None
    credit_amount: float
    complaint_count: int
    orders: list[dict[str, Any]]
    products: list[dict[str, Any]]
    quick_replies: list[str]
    reply: str
    tools_used: list[str]
    summary_card: dict[str, Any] | None
    conversation_ended: bool


_SESSIONS: dict[str, AgentState] = {}
_CONTEXTS: dict[str, SessionContext] = {}


def _initial_state(session_id: str, customer_id: int) -> AgentState:
    return {
        "session_id": session_id,
        "customer_id": customer_id,
        "step": "greet",
        "selected_order": None,
        "reason": None,
        "chosen_option": None,
        "return_method": None,
        "slot": None,
        "replacement_product": None,
        "refund_method": None,
        "exchange_phase": None,
        "buy_phase": None,
        "credit_amount": 0.0,
        "complaint_count": 0,
        "orders": [],
        "products": [],
        "quick_replies": [],
        "reply": "",
        "tools_used": [],
        "summary_card": None,
        "conversation_ended": False,
    }


def reset_session(session_id: str) -> None:
    """Forget the in-memory state and transient approvals for one session."""

    _SESSIONS.pop(session_id, None)
    _CONTEXTS.pop(session_id, None)


def _context(state: AgentState) -> SessionContext:
    return _CONTEXTS.setdefault(state["session_id"], SessionContext(state["session_id"], state["customer_id"]))


def _tool(state: AgentState, tool: Any, payload: dict[str, Any]) -> Any:
    result = tool.invoke(payload)
    state.setdefault("tools_used", []).append(tool.name)
    return result


def _reply(state: AgentState, fallback: str, facts: Any, llm: Any = None) -> str:
    """Let the model phrase known facts, with a deterministic fallback."""

    if llm is None:
        return fallback
    try:
        response = llm.invoke([
            SystemMessage(content=f"{SYSTEM_PROMPT}\nUse only these facts and write one short friendly reply:\n{facts}"),
            HumanMessage(content=state["message"]),
        ])
        return str(response.content)
    except Exception:
        return fallback


def _llm_hint(state: AgentState, llm: Any, labels: str) -> str:
    """Ask ChatOllama to map ambiguous text to one allowed label."""

    if llm is None:
        return ""
    try:
        response = llm.invoke([
            SystemMessage(content=f"Map the customer message to exactly one of these labels: {labels}. Return only the label."),
            HumanMessage(content=state["message"]),
        ])
        return str(response.content).strip().lower()
    except Exception:
        return ""


def _numbered_orders(orders: list[dict[str, Any]]) -> str:
    return "\n".join(f"{index}. {order['item_name']} - ${order['price']:.2f} ({order['status']})" for index, order in enumerate(orders, start=1))


def _parse_order(message: str, orders: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = message.lower()
    match = re.search(r"\b(\d+)\b", text)
    if match:
        number = int(match.group(1))
        for index, order in enumerate(orders, start=1):
            if number == index or number == order["order_id"]:
                return order
    for index, word in enumerate(("first", "second", "third", "fourth", "fifth")):
        if word in text and index < len(orders):
            return orders[index]
    for order in orders:
        if order["item_name"].lower() in text:
            return order
    return None


def _order_from_database(message: str, customer_id: int) -> dict[str, Any] | None:
    match = re.search(r"\border\s+(\d+)\b", message.lower())
    if not match:
        return None
    order = get_order(customer_id, int(match.group(1)))
    if order is None:
        return None
    return {"order_id": order.order_id, "item_name": order.item_name, "price": order.amount, "status": order.status, "date": order.order_date.isoformat()}


def _parse_reason(message: str) -> str | None:
    text = message.lower()
    aliases = {
        "damaged": ("damaged",),
        "defective": ("defective", "broken", "doesn't work"),
        "wrong_item": ("wrong item", "wrong product"),
        "not_as_described": ("not as described", "different than described"),
        "size_fit": ("size", "fit", "too small", "too large"),
        "changed_mind": ("changed my mind", "change my mind", "don't want", "dont want"),
    }
    for reason, phrases in aliases.items():
        if any(phrase in text for phrase in phrases):
            return reason
    if "other" in text:
        return "other"
    return None


def _parse_option(message: str) -> str | None:
    text = message.lower()
    if any(word in text for word in ("exchange", "swap", "different size", "different color")):
        return "exchange"
    if any(word in text for word in ("buy", "purchase", "different product", "shop")):
        return "buy_different"
    if any(word in text for word in ("refund", "money back", "moneyback")):
        return "refund"
    return None


def _parse_method(message: str) -> str | None:
    text = message.lower()
    if "store credit" in text or "credit" in text:
        return "store_credit"
    if "original" in text or "card" in text or "payment" in text:
        return "original_payment"
    return None


def _parse_return_method(message: str) -> str | None:
    text = message.lower()
    if "ups" in text or "drop" in text:
        return "ups_dropoff"
    if "courier" in text or "pickup" in text or "pick-up" in text:
        return "courier_pickup"
    return None


def _parse_product_number(message: str, products: list[dict[str, Any]]) -> int | None:
    match = re.search(r"\b([1-3])\b", message)
    if match and int(match.group(1)) <= len(products):
        return int(products[int(match.group(1)) - 1]["product_id"])
    return None


def _parse_credit(message: str) -> float:
    credit_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:dollars?\s+)?credit", message.lower())
    if credit_match:
        return float(credit_match.group(1))
    amounts = re.findall(r"\$?\s*(\d+(?:\.\d+)?)", message)
    return float(amounts[-1]) if amounts else 0.0


def _is_policy_question(message: str) -> bool:
    text = message.lower()
    return any(word in text for word in ("policy", "return window", "warranty", "shipping", "how long"))


def _handle_crosscutting(state: AgentState, llm: Any) -> bool:
    message = state["message"]
    injection = check_prompt_injection(message)
    if injection:
        state["reply"] = "I can help with your order, but I cannot follow instruction overrides."
        state["quick_replies"] = []
        return True
    if _is_policy_question(message) and state["step"] != "greet":
        results = _tool(state, search_policy_tool, {"question": message})
        facts = "\n".join(f"{item['content']} (Source: {item['source']})" for item in results)
        state["reply"] = _reply(state, "Here is what I found:\n" + facts, results, llm)
        state["quick_replies"] = ["Continue"]
        return True
    if "go back" in message.lower() or "start over" in message.lower():
        state["step"] = "ask_issue" if state.get("selected_order") else "select_order"
        state["reply"] = "Of course. What would you like to change?"
        state["quick_replies"] = ["Refund", "Exchange", "Buy something different"]
        return True
    option = _parse_option(message)
    change_request = any(phrase in message.lower() for phrase in ("actually", "instead", "change my mind", "i want"))
    if option and change_request and state["step"] not in {"offer_options", "greet"}:
        state["step"] = "offer_options"
        state["reply"] = "I can help with that. Would you like a refund, an exchange, or to buy something different?"
        state["quick_replies"] = ["Refund", "Exchange", "Buy something different"]
        return True
    if any(word in message.lower() for word in ("angry", "terrible", "ridiculous", "frustrated", "human", "agent", "manager")):
        state["complaint_count"] = state.get("complaint_count", 0) + 1
        if "human" in message.lower() or state["complaint_count"] >= 3:
            _tool(state, escalate_to_human_tool, {"summary": message})
            state["step"] = "anything_else"
            state["reply"] = "I am sorry this has been frustrating. A specialist will review this case. Is there anything else I can help you with?"
            state["quick_replies"] = ["No"]
            return True
        state["reply"] = "I am sorry this has been frustrating. I will help one step at a time."
        return True
    return False


def _handle(state: AgentState, llm: Any) -> AgentState:
    if _handle_crosscutting(state, llm):
        return state
    step = state["step"]
    message = state["message"]
    if step == "greet":
        orders = _tool(state, get_recent_orders_tool, {})
        state["orders"] = orders
        state["step"] = "select_order"
        state["reply"] = "Hello! I am happy to help. Here are your recent orders:\n" + _numbered_orders(orders) + "\nWhich order do you need help with?"
        state["quick_replies"] = [f"Order {index}" for index in range(1, len(orders) + 1)]
    elif step == "select_order":
        order = _parse_order(message, state["orders"])
        if order is None:
            order = _order_from_database(message, state["customer_id"])
        if order is None:
            order = _parse_order(_llm_hint(state, llm, "first, second, third, fourth, fifth, or order id"), state["orders"])
        if order is None:
            state["reply"] = "I could not match that to one of the listed orders. Which order do you need help with?"
        else:
            state["selected_order"] = order
            state["step"] = "ask_issue"
            state["reply"] = "What went wrong with this order?"
            state["quick_replies"] = ["Damaged", "Defective", "Wrong item", "Not as described", "Size/fit", "Changed my mind", "Other"]
    elif step == "ask_issue":
        reason = _parse_reason(message)
        if reason is None:
            reason = _parse_reason(_llm_hint(state, llm, "damaged, defective, wrong_item, not_as_described, size_fit, changed_mind, or other"))
        if reason is None:
            state["reply"] = "Please tell me what went wrong: damaged, defective, wrong item, not as described, size/fit, changed my mind, or other."
        else:
            state["reason"] = reason
            result = _tool(state, check_refund_eligibility_tool, {"order_id": state["selected_order"]["order_id"], "reason": reason})
            if result["decision"] == "approve":
                state["step"] = "offer_options"
                state["reply"] = "This order is eligible. Would you like a refund, an exchange, or to buy something different?"
                state["quick_replies"] = ["Refund", "Exchange", "Buy something different"]
            elif result["decision"] == "escalate":
                _tool(state, escalate_to_human_tool, {"summary": result["message"]})
                state["step"] = "anything_else"
                state["reply"] = "A specialist will review this case. Is there anything else I can help you with?"
                state["quick_replies"] = ["Yes", "No"]
            else:
                state["step"] = "anything_else"
                state["reply"] = result["message"] + " Would you like help with another order or a specialist?"
                state["quick_replies"] = ["Another order", "Human", "No"]
    elif step == "offer_options":
        option = _parse_option(message)
        if option is None:
            option = _parse_option(_llm_hint(state, llm, "refund, exchange, or buy_different"))
        if option == "refund":
            state["chosen_option"] = "refund"
            state["step"] = "refund"
            state["reply"] = "Would you like the refund to your original payment method or as instant store credit?"
            state["quick_replies"] = ["Original payment", "Store credit"]
        elif option == "exchange":
            state["chosen_option"] = "exchange"
            state["step"] = "exchange"
            state["exchange_phase"] = "replacement"
            state["reply"] = "What would you like instead: the same item, another size or color, or a different product?"
            state["quick_replies"] = ["Same item", "Another size", "Another color", "Different product"]
        elif option == "buy_different":
            state["chosen_option"] = "buy_different"
            state["step"] = "buy_different"
            state["buy_phase"] = "requirements"
            state["reply"] = "What kind of product do you want, what is your budget, and which features matter most?"
            state["quick_replies"] = []
        else:
            state["reply"] = "Please choose a refund, exchange, or buying something different."
    elif step == "refund":
        method = _parse_method(message)
        if method is None:
            method = _parse_method(_llm_hint(state, llm, "original_payment or store_credit"))
        if method is None:
            state["reply"] = "Would you like original payment or store credit?"
        else:
            state["refund_method"] = method
            result = _tool(state, initiate_refund_tool, {"order_id": state["selected_order"]["order_id"], "method": method})
            state["step"] = "anything_else"
            state["summary_card"] = result
            state["reply"] = f"Your refund {result.get('refund_id', '')} is confirmed. The timeline is {result.get('timeline', 'as provided by the rules')}. Is there anything else I can help you with?"
            state["quick_replies"] = ["Yes", "No"]
    elif step == "exchange":
        phase = state.get("exchange_phase")
        if phase == "replacement":
            state["replacement_product"] = _parse_product_number(message, state.get("products", [])) or 2
            state["exchange_phase"] = "method"
            methods = _tool(state, get_return_methods_tool, {"order_id": state["selected_order"]["order_id"], "reason": state["reason"] or "changed_mind"})
            state["reply"] = f"Please pack the item in its original packaging. UPS drop-off is free at {', '.join(methods['ups_dropoff']['locations'])}. Courier pickup is ${methods['courier_pickup']['fee_usd']} with slots {', '.join(methods['courier_pickup']['time_slots'])}. Which return method would you like?"
            state["quick_replies"] = ["UPS drop-off", "Courier pickup"]
        elif phase == "method":
            method = _parse_return_method(message)
            if method is None:
                method = _parse_return_method(_llm_hint(state, llm, "ups_dropoff or courier_pickup"))
            if method is None:
                state["reply"] = "Would you prefer UPS drop-off or courier pickup?"
            else:
                state["return_method"] = method
                if method == "courier_pickup":
                    state["exchange_phase"] = "slot"
                    state["reply"] = "Which pickup time slot works for you?"
                    state["quick_replies"] = []
                else:
                    state["slot"] = "UPS drop-off"
                    result = _tool(state, create_exchange_tool, {"order_id": state["selected_order"]["order_id"], "replacement_product_id": state["replacement_product"] or 2, "return_method": method, "slot": state["slot"]})
                    state["step"] = "anything_else"
                    state["summary_card"] = result
                    state["reply"] = f"Your exchange return {result['return_id']} is confirmed. The replacement is expected to ship on {result['replacement_ship_date']}. Is there anything else I can help you with?"
                    state["quick_replies"] = ["Yes", "No"]
        else:
            state["slot"] = message
            result = _tool(state, create_exchange_tool, {"order_id": state["selected_order"]["order_id"], "replacement_product_id": state["replacement_product"] or 2, "return_method": "courier_pickup", "slot": message})
            state["step"] = "anything_else"
            state["summary_card"] = result
            state["reply"] = f"Your exchange return {result['return_id']} is confirmed. The replacement is expected to ship on {result['replacement_ship_date']}. Is there anything else I can help you with?"
            state["quick_replies"] = ["Yes", "No"]
    elif step == "buy_different":
        if state.get("buy_phase") == "requirements":
            state["credit_amount"] = _parse_credit(message)
            state["products"] = _tool(state, recommend_products_tool, {"description": message, "max_price": None, "category": None})
            state["buy_phase"] = "choose"
            state["reply"] = "Here are three options:\n" + "\n".join(f"{index}. {product['name']} - ${product['price']:.2f} - {product['reason']}" for index, product in enumerate(state["products"], start=1)) + "\nWhich one would you like?"
            state["quick_replies"] = ["1", "2", "3"]
        else:
            product_id = _parse_product_number(message, state["products"])
            if product_id is None:
                product_id = _parse_product_number(_llm_hint(state, llm, "1, 2, or 3"), state["products"])
            if product_id is None:
                state["reply"] = "Please choose option 1, 2, or 3."
            else:
                result = _tool(state, buy_with_credit_tool, {"product_id": product_id, "credit_amount": state.get("credit_amount", 0)})
                state["step"] = "anything_else"
                state["summary_card"] = result
                state["reply"] = f"Your order {result.get('order_id', '')} is created. The difference to pay is ${result.get('pay_difference', 0):.2f}; credit left over is ${result.get('credit_leftover', 0):.2f}. Is there anything else I can help you with?"
                state["quick_replies"] = ["Yes", "No"]
    elif step == "anything_else":
        if any(word in message.lower() for word in ("yes", "another", "more", "sure")):
            state["step"] = "greet"
            state["selected_order"] = None
            state["reply"] = "Of course. Which order do you need help with?"
            state["quick_replies"] = []
        else:
            state["conversation_ended"] = True
            state["reply"] = "Thanks for chatting with ShopAssist. Goodbye!"
            state["quick_replies"] = []
    return state


def _route(state: AgentState) -> str:
    return state.get("step", "greet")


def build_graph(model_name: str | None = None, use_llm: bool = False) -> Any:
    """Build the guided LangGraph state machine."""

    llm = get_llm(model_name) if use_llm else None
    builder = StateGraph(AgentState)
    steps = ("greet", "select_order", "ask_issue", "check_eligibility", "offer_options", "refund", "exchange", "buy_different", "anything_else")
    for step in steps:
        builder.add_node(step, lambda state, model=llm: _handle(state, model))
    builder.add_conditional_edges(START, _route, {step: step for step in steps})
    for step in steps:
        builder.add_edge(step, END)
    return builder.compile()


GRAPH = build_graph()


def run_turn(message: str, session_id: str, customer_id: int, model_name: str | None = None, use_llm: bool = False) -> dict[str, Any]:
    """Process one message and return the complete customer-facing turn."""

    state = deepcopy(_SESSIONS.get(session_id) or _initial_state(session_id, customer_id))
    state["message"] = message
    state["tools_used"] = []
    state["summary_card"] = None
    graph = GRAPH if not use_llm and model_name is None else build_graph(model_name, use_llm=use_llm)
    with use_session_context(_context(state)):
        try:
            result = graph.invoke(state, config={"configurable": {"thread_id": session_id}})
        except Exception:
            state["step"] = "anything_else"
            state["reply"] = "I am sorry, I could not complete that request. Would you like a human specialist to help?"
            state["quick_replies"] = ["Human", "No"]
            state["summary_card"] = None
            result = state
    _SESSIONS[session_id] = result
    return {key: result.get(key) for key in ("reply", "quick_replies", "orders", "products", "summary_card", "tools_used", "conversation_ended")}


def chat_with_tools(message: str, session_id: str, customer_id: int | None = None, model_name: str | None = None) -> dict[str, Any]:
    """Compatibility wrapper for one state-machine turn."""

    if customer_id is None:
        raise ValueError("customer_id is required for customer-scoped tools")
    result = run_turn(message, session_id, customer_id, model_name=model_name, use_llm=model_name is not None)
    return {"reply": result["reply"], "tools_called": result["tools_used"], **result}


def chat(message: str, session_id: str, customer_id: int = 1) -> str:
    return str(run_turn(message, session_id, customer_id)["reply"])


__all__: tuple[str, ...] = ["AgentState", "GRAPH", "build_graph", "chat", "chat_with_tools", "reset_session", "run_turn"]
