"""Seed deterministic synthetic orders, refunds, and products for local use."""

from datetime import datetime, timedelta, timezone

from app.db.models import Customer, Order, Product, Refund
from app.db.session import initialize_database, session_scope


def seed_database() -> None:
	"""Reset and populate the local synthetic database."""

	initialize_database()
	now = datetime.now(timezone.utc).replace(tzinfo=None)
	orders = [
		Order(order_id=1001, customer_id=1, category="electronics", amount=120, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1002, customer_id=1, category="clothing", amount=80, status="delivered", delivered_at=now - timedelta(days=40)),
		Order(order_id=1003, customer_id=1, category="grocery", amount=25, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1004, customer_id=1, category="electronics", amount=150, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1005, customer_id=1, category="footwear", amount=90, status="shipped"),
		Order(order_id=1006, customer_id=1, category="headphones", amount=75, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1007, customer_id=1, category="home", amount=25, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1008, customer_id=1, category="electronics", amount=1200, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1010, customer_id=1, category="beauty", amount=35, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1011, customer_id=1, category="clothing", amount=60, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=1013, customer_id=1, category="electronics", amount=70, status="delivered", delivered_at=now - timedelta(days=2), refunded=True),
		Order(order_id=1014, customer_id=2, category="electronics", amount=100, status="delivered", delivered_at=now - timedelta(days=2)),
		Order(order_id=2001, customer_id=4, category="electronics", amount=100, status="delivered", delivered_at=now - timedelta(days=2)),
	]
	products = [
		Product(product_id=1, name="Everyday Laptop", category="electronics", price=499, description="Lightweight laptop for work and study.", rating=4.6, key_features="Lightweight; long battery life"),
		Product(product_id=2, name="Quiet Headphones", category="headphones", price=79, description="Wireless noise-reducing headphones.", rating=4.4, key_features="Wireless; noise reducing"),
		Product(product_id=3, name="Trail Shoes", category="footwear", price=95, description="Comfortable shoes for everyday trails.", rating=4.5, key_features="Cushioned; water resistant"),
	]
	customers = [Customer(id=1, name="Alex Morgan"), Customer(id=2, name="Jordan Lee"), Customer(id=4, name="Sam Rivera")]
	for order in orders:
		order.item_name = f"{order.category.title()} item"
		order.order_date = order.delivered_at or now
	with session_scope() as session:
		session.query(Refund).delete()
		session.query(Order).delete()
		session.query(Product).delete()
		session.query(Customer).delete()
		session.add_all(orders + products + customers)
		session.add(Refund(order_id=1013, customer_id=1, amount=70, created_at=now - timedelta(days=2)))
		for index in range(4):
			session.add(Refund(order_id=2010 + index, customer_id=4, amount=20, created_at=now - timedelta(days=index + 1)))


if __name__ == "__main__":
	seed_database()