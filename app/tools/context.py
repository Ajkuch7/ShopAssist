"""Session-scoped values injected into tool execution."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator

from app.rules.engine import EligibilityResult


@dataclass
class SessionContext:
	"""Identity and transient approvals for one customer conversation."""

	session_id: str
	customer_id: int
	approved_eligibility: dict[int, tuple[EligibilityResult, str]] = field(default_factory=dict)


_current_context: ContextVar[SessionContext | None] = ContextVar("shopassist_session_context", default=None)


def get_session_context() -> SessionContext:
	"""Return the active context or fail closed when tools run without one."""

	context = _current_context.get()
	if context is None:
		raise RuntimeError("A SessionContext is required to run ShopAssist tools")
	return context


@contextmanager
def use_session_context(context: SessionContext) -> Iterator[SessionContext]:
	"""Inject a context for the duration of synchronous tool execution."""

	token = _current_context.set(context)
	try:
		yield context
	finally:
		_current_context.reset(token)