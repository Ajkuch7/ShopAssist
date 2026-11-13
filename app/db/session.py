"""SQLite engine and transaction helpers."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.models import Base


def _engine():
	url = get_settings().database.url
	if url.startswith("sqlite:///"):
		Path(url.removeprefix("sqlite:///" )).parent.mkdir(parents=True, exist_ok=True)
	return create_engine(url, future=True)


def initialize_database() -> None:
	"""Create the small synthetic schema when it is not present."""

	engine = _engine()
	inspector = inspect(engine)
	required = {
		"orders": {"item_name", "order_date"},
		"refunds": {"method"},
		"products": {"rating", "key_features"},
	}
	if any(table in inspector.get_table_names() and missing - {column["name"] for column in inspector.get_columns(table)} for table, missing in required.items()):
		Base.metadata.drop_all(engine)
	Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
	"""Yield a committed session and roll back failed transactions."""

	session = sessionmaker(bind=_engine(), expire_on_commit=False)()
	try:
		yield session
		session.commit()
	except Exception:
		session.rollback()
		raise
	finally:
		session.close()