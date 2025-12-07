import json
import sys

from logging import Formatter, Logger, StreamHandler
from typing import override


class JsonFormatter(Formatter):
    """An formatter used to output all logs in JSON format."""

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


def configure(level: int, logger: Logger) -> Logger:
    """Configures the passed logger.

    Adds JSON-formatted log streaming to stdout.

    Args:
        level: the minimum loh level to output.
        logger: the logger instance to modify.

    Returns:
        The modified logger object for chaining.
    """

    stream_handler = StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(fmt=JsonFormatter())
    stream_handler.setLevel(level=level)

    logger.setLevel(level=level)
    logger.addHandler(stream_handler)

    return logger
