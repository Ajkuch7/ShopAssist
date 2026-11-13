"""Application logging configuration."""

import logging


def configure_logging() -> None:
	"""Configure concise, timestamped application logs once at startup."""

	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
	)


def get_logger(name: str) -> logging.Logger:
	"""Return a named application logger."""

	return logging.getLogger(name)
