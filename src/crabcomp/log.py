import json
import sys

from logging import getLogger, Formatter, INFO, Logger, StreamHandler
from typing import override


__all__ = ["configure_root_logger", "reset_root_logger", "JsonFormatter"]

__last_stream_handler: StreamHandler | None = None


class JsonFormatter(Formatter):
    """A formatter used to output all logs in JSON format."""

    @override
    def format(self, record):
        return json.dumps(
            {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
            }
        )


def configure_root_logger(level: int = INFO) -> Logger:
    """Adds JSON-formatted log streaming to stdout.

    Args:
        level: the minimum log level to output.
        logger: the logger instance to modify.

    Returns:
        The configured root logger for chaining.
    """
    global __last_stream_handler

    root_logger = getLogger()

    # Avoid unnecessary modifications.
    if not __last_stream_handler or __last_stream_handler not in root_logger.handlers:
        __last_stream_handler = StreamHandler(stream=sys.stdout)
        __last_stream_handler.setFormatter(fmt=JsonFormatter())
        __last_stream_handler.setLevel(level=level)

        root_logger.setLevel(level=level)
        root_logger.addHandler(__last_stream_handler)

    return root_logger


def reset_root_logger(level: int = INFO) -> Logger:
    """Removes modifications made during configuration.

    Args:
        level: the level to set for the root logger post reset. Defaults to INFO.

    Returns:
        The root logger with custom configurations removed for chaining.
    """

    global __last_stream_handler

    root_logger = getLogger()

    # Avoid unnecessary lock acquisition if root logger hasn't been configured.
    if __last_stream_handler and __last_stream_handler in root_logger.handlers:
        root_logger.removeHandler(__last_stream_handler)
        __last_stream_handler = None

    root_logger.setLevel(level)
    return root_logger
