"""
Centralized logging configuration.

This module provides consistent logging setup across the application.
"""

import logging
import sys
from typing import Any, Dict

from clever.config import Settings


def configure_logging(config: Settings) -> None:
    """Configure logging based on environment settings."""

    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set log level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    # Create formatter based on format type
    if config.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    # Suppress overly verbose libraries
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("httpx").propagate = False
    logging.getLogger("sqlalchemy").propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the given module name."""
    return logging.getLogger(name)


class TextFormatter(logging.Formatter):
    """Text formatter for development environment."""

    def format(self, record: logging.LogRecord) -> str:
        # Color codes
        RESET = "\033[0m"
        LEVEL_COLORS = {
            logging.DEBUG: "\033[36m",  # Cyan
            logging.INFO: "\033[32m",  # Green
            logging.WARNING: "\033[33m",  # Yellow
            logging.ERROR: "\033[31m",  # Red
            logging.CRITICAL: "\033[35m",  # Magenta
        }

        level_color = LEVEL_COLORS.get(record.levelno, RESET)

        # Format: [LEVEL] YYYY-MM-DD HH:MM:SS module.function:line - message
        from datetime import datetime

        created_time = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return (
            f"{level_color}[{record.levelname}] {RESET}"
            f"\033[90m{created_time} {record.name}:{record.lineno} - {RESET}"
            f"{record.getMessage()}"
        )


class JSONFormatter(logging.Formatter):
    """JSON formatter for production environment."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "line": record.lineno,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        return json.dumps(log_record)
