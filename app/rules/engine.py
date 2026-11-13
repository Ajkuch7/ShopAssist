"""Load the synthetic return and refund rules from the single YAML source."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


RULES_PATH = Path(__file__).with_name("rules.yaml")


@lru_cache(maxsize=1)
def load_rules() -> dict[str, Any]:
	"""Return the cached business rules used by the support agent."""

	with RULES_PATH.open(encoding="utf-8") as rules_file:
		return dict(yaml.safe_load(rules_file) or {})


__all__: tuple[str, ...] = ["RULES_PATH", "load_rules"]
