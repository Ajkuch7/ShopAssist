"""Application logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "shopassist.log"


def configure_logging() -> None:
	"""Configure console and rotating file logs once at startup."""

	root_logger = logging.getLogger()
	if root_logger.handlers:
		return
	LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
	formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	file_handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
	file_handler.setFormatter(formatter)
	root_logger.setLevel(logging.INFO)
	root_logger.addHandler(console_handler)
	root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
	"""Return a named application logger."""

	return logging.getLogger(name)
