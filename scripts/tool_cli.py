"""Invoke ShopAssist tools from PowerShell with a customer identity."""

import json
import sys
from pathlib import Path

import typer

if __package__ in (None, ""):
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tools.context import SessionContext, use_session_context
from app.tools.escalation import escalate_to_human_tool
from app.tools.orders import get_recent_orders_tool
from app.tools.policy import search_policy_tool
from app.tools.products import buy_with_credit_tool, recommend_products_tool
from app.tools.refunds import check_refund_eligibility_tool, initiate_refund_tool
from app.tools.returns import create_exchange_tool, get_return_methods_tool


app = typer.Typer(no_args_is_help=True)


def _run(customer: int, tool, payload: dict) -> None:
	with use_session_context(SessionContext(session_id="tool-cli", customer_id=customer)):
		print(json.dumps(tool.invoke(payload), indent=2, default=str))


@app.command("recent-orders")
def recent_orders(customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, get_recent_orders_tool, {})


@app.command("check-refund")
def check_refund(
	order_id: int = typer.Option(..., "--order"),
	reason: str = typer.Option(..., "--reason"),
	customer: int = typer.Option(..., "--customer"),
) -> None:
	_run(customer, check_refund_eligibility_tool, {"order_id": order_id, "reason": reason})


@app.command("initiate-refund")
def initiate_refund(order_id: int, method: str, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, initiate_refund_tool, {"order_id": order_id, "method": method})


@app.command("return-methods")
def return_methods(order_id: int, reason: str, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, get_return_methods_tool, {"order_id": order_id, "reason": reason})


@app.command("create-exchange")
def create_exchange(order_id: int, replacement_product_id: int, return_method: str, slot: str, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, create_exchange_tool, {"order_id": order_id, "replacement_product_id": replacement_product_id, "return_method": return_method, "slot": slot})


@app.command("recommend")
def recommend(description: str, max_price: float | None = None, category: str | None = None, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, recommend_products_tool, {"description": description, "max_price": max_price, "category": category})


@app.command("buy-with-credit")
def buy_with_credit(product_id: int, credit_amount: float, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, buy_with_credit_tool, {"product_id": product_id, "credit_amount": credit_amount})


@app.command("search-policy")
def search_policy(question: str, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, search_policy_tool, {"question": question})


@app.command("escalate")
def escalate(summary: str, customer: int = typer.Option(..., "--customer")) -> None:
	_run(customer, escalate_to_human_tool, {"summary": summary})


if __name__ == "__main__":
	app()