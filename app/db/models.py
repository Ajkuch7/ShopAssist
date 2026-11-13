"""Small SQLAlchemy schema for synthetic orders, refunds, and products."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
	return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
	"""Base class for application tables."""


class Customer(Base):
	__tablename__ = "customers"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	name: Mapped[str] = mapped_column(String(100))


class Order(Base):
	__tablename__ = "orders"

	order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
	customer_id: Mapped[int] = mapped_column(Integer, index=True)
	category: Mapped[str] = mapped_column(String(50))
	amount: Mapped[float] = mapped_column(Float)
	status: Mapped[str] = mapped_column(String(30))
	delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
	item_name: Mapped[str] = mapped_column(String(200), default="")
	order_date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
	refunded: Mapped[bool] = mapped_column(Boolean, default=False)


class Refund(Base):
	__tablename__ = "refunds"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	order_id: Mapped[int] = mapped_column(Integer, index=True)
	customer_id: Mapped[int] = mapped_column(Integer, index=True)
	amount: Mapped[float] = mapped_column(Float)
	created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
	method: Mapped[str] = mapped_column(String(30), default="original_payment")


class Product(Base):
	__tablename__ = "products"

	product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
	name: Mapped[str] = mapped_column(String(200))
	category: Mapped[str] = mapped_column(String(50), index=True)
	price: Mapped[float] = mapped_column(Float)
	description: Mapped[str] = mapped_column(String(500), default="")
	rating: Mapped[float] = mapped_column(Float, default=4.5)
	key_features: Mapped[str] = mapped_column(String(500), default="")


class ReturnRequest(Base):
	__tablename__ = "return_requests"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	order_id: Mapped[int] = mapped_column(Integer, index=True)
	customer_id: Mapped[int] = mapped_column(Integer, index=True)
	replacement_product_id: Mapped[int] = mapped_column(Integer)
	return_method: Mapped[str] = mapped_column(String(30))
	slot: Mapped[str] = mapped_column(String(100))
	fee: Mapped[float] = mapped_column(Float)
	replacement_ship_date: Mapped[datetime] = mapped_column(DateTime)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class EscalationCase(Base):
	__tablename__ = "escalation_cases"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	customer_id: Mapped[int] = mapped_column(Integer, index=True)
	summary: Mapped[str] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AuditLog(Base):
	__tablename__ = "audit_logs"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	session_id: Mapped[str] = mapped_column(String(100), index=True)
	customer_id: Mapped[int] = mapped_column(Integer, index=True)
	tool_name: Mapped[str] = mapped_column(String(100))
	input: Mapped[str] = mapped_column(Text)
	output: Mapped[str] = mapped_column(Text)
	rule_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)