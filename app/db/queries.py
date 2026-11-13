"""Customer-scoped database operations used by tools."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import AuditLog, Customer, EscalationCase, Order, Product, Refund, ReturnRequest
from app.db.session import session_scope


def get_recent_orders(customer_id: int, limit: int = 5) -> list[Order]:
	with session_scope() as session:
		return list(session.scalars(select(Order).where(Order.customer_id == customer_id).order_by(Order.order_date.desc()).limit(limit)).all())


def get_demo_customers() -> list[Customer]:
	with session_scope() as session:
		return list(session.scalars(select(Customer).order_by(Customer.id)).all())


def get_order(customer_id: int, order_id: int) -> Order | None:
	with session_scope() as session:
		return session.scalar(select(Order).where(Order.order_id == order_id, Order.customer_id == customer_id))


def create_refund(customer_id: int, order_id: int, method: str) -> Refund:
	with session_scope() as session:
		order = session.scalar(select(Order).where(Order.order_id == order_id, Order.customer_id == customer_id))
		if order is None:
			raise ValueError("Order not found")
		refund = Refund(order_id=order_id, customer_id=customer_id, amount=order.amount, method=method, created_at=datetime.now(timezone.utc).replace(tzinfo=None))
		order.refunded = True
		session.add(refund)
		session.flush()
		return refund


def create_return_request(customer_id: int, order_id: int, replacement_product_id: int, return_method: str, slot: str, fee: float, ship_date: datetime) -> ReturnRequest:
	with session_scope() as session:
		order = session.scalar(select(Order).where(Order.order_id == order_id, Order.customer_id == customer_id))
		if order is None:
			raise ValueError("Order not found")
		request = ReturnRequest(order_id=order_id, customer_id=customer_id, replacement_product_id=replacement_product_id, return_method=return_method, slot=slot, fee=fee, replacement_ship_date=ship_date)
		session.add(request)
		session.flush()
		return request


def get_product(product_id: int) -> Product | None:
	with session_scope() as session:
		return session.get(Product, product_id)


def create_mock_order(customer_id: int, product: Product) -> Order:
	with session_scope() as session:
		latest = session.scalar(select(func.max(Order.order_id))) or 1000
		now = datetime.now(timezone.utc).replace(tzinfo=None)
		order = Order(order_id=int(latest) + 1, customer_id=customer_id, category=product.category, amount=product.price, status="processing", item_name=product.name, order_date=now)
		session.add(order)
		session.flush()
		return order


def add_escalation(customer_id: int, summary: str) -> EscalationCase:
	with session_scope() as session:
		case = EscalationCase(customer_id=customer_id, summary=summary)
		session.add(case)
		session.flush()
		return case


def add_audit_log(session_id: str, customer_id: int, tool_name: str, input_text: str, output_text: str, rule_code: str | None = None) -> None:
	with session_scope() as session:
		session.add(AuditLog(session_id=session_id, customer_id=customer_id, tool_name=tool_name, input=input_text, output=output_text, rule_code=rule_code))