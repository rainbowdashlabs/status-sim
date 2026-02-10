import logging
import sys
import os
from logging.config import dictConfig

def setup_logging():
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

    dictConfig(LOGGING_CONFIG)

def get_logger(name: str):
    return logging.getLogger(f"src.{name}")
