"""Loguru logging configuration."""

import sys

from loguru import logger


def configure_logging(
    level: str = "INFO",
    *,
    sink: object = sys.stderr,
) -> None:
    """
    Configure loguru with a consistent format and level.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        sink: Output sink (default: stderr).
    """
    logger.remove()

    format_ = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sink,
        format=format_,
        level=level,
        colorize=True,
    )
