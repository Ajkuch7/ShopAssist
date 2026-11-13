"""Cached access to the YAML business rules."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


RULES_PATH = Path(__file__).with_name("rules.yaml")
_rules: dict[str, Any] | None = None


def _read_rules() -> dict[str, Any]:
	with RULES_PATH.open(encoding="utf-8") as rules_file:
		return dict(yaml.safe_load(rules_file) or {})


def get_rule(key: str) -> Any:
	"""Return one rule value, loading the YAML file only on first access."""

	global _rules
	if _rules is None:
		_rules = _read_rules()
	if key not in _rules:
		raise KeyError(f"Unknown rule: {key}")
	return deepcopy(_rules[key])


def reload() -> None:
	"""Clear the cache so the next lookup reads the current YAML file."""

	global _rules
	_rules = None


__all__: tuple[str, ...] = ["RULES_PATH", "get_rule", "reload"]