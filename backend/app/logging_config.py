"""Logging configuration for the FastAPI application.

This module configures logging to output to stdout/stderr so that
Docker can capture logs via `docker logs`.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application.

    Logs are sent to stdout/stderr so Docker can capture them.
    Format includes timestamp, level, module, and message.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=(
            "%(asctime)s [%(levelname)s] "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Docker captures stdout
            logging.StreamHandler(sys.stderr),    # Errors to stderr
        ],
        force=True,  # Override any existing configuration
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Get application logger
    logger = logging.getLogger("backend.app")
    logger.info(f"Logging configured at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

