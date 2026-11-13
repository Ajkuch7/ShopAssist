"""Input checks that run before model reasoning."""

import re

INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
	re.compile(r"ignore\s+(?:all\s+)?your\s+rules", re.IGNORECASE),
	re.compile(r"i\s+am\s+the\s+manager", re.IGNORECASE),
)


def check_prompt_injection(text: str) -> str | None:
	"""Return a reason when input attempts to override agent instructions."""

	for pattern in INJECTION_PATTERNS:
		if pattern.search(text):
			return "The request contains an instruction override attempt."
	return None


__all__: tuple[str, ...] = ["check_prompt_injection"]
