import json
import logging
import sys
import os
from datetime import datetime, timezone
from logging.config import dictConfig


class EcsJsonFormatter(logging.Formatter):
    """Formats each record as one line of JSON using Elastic Common Schema field names."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "@timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "log.level": record.levelname,
            "log.logger": record.name,
            "message": record.getMessage(),
            "process.thread.name": record.threadName,
        }
        if record.exc_info:
            error_type, error, _ = record.exc_info
            entry["error.type"] = error_type.__qualname__ if error_type else None
            entry["error.message"] = str(error)
            entry["error.stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging():
    """Configures root, app and uvicorn logging; LOG_FORMAT=json switches every handler to ECS JSON."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "access_console": {
                "class": "logging.StreamHandler",
                "formatter": "access",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access_console"], "level": "INFO", "propagate": False},
            "src": {"handlers": ["console"], "level": log_level, "propagate": False},
        },
        "root": {"handlers": ["console"], "level": log_level},
    }

    if os.getenv("LOG_FORMAT", "").lower() == "json":
        LOGGING_CONFIG["formatters"] = {
            "default": {"()": EcsJsonFormatter},
            "access": {"()": EcsJsonFormatter},
        }

    dictConfig(LOGGING_CONFIG)

def get_logger(name: str):
    return logging.getLogger(f"src.{name}")
