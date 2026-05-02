import logging
import os
import json
from typing import Any

# Default logger for all log messages in this module, configured to emit JSON-formatted logs to stdout.
logger = logging.getLogger(__name__)
# Set the log level from the environment variable (set by Terraform) or default to INFO.
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON object."""

    # Standard Python logging record fields to exclude from output
    _EXCLUDE_FIELDS = {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "module",
        "msecs",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include only extra fields (exclude standard logging record attributes)
        for key, value in record.__dict__.items():
            if key not in self._EXCLUDE_FIELDS:
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


_handler = logging.StreamHandler()
_handler.setFormatter(_JSONFormatter())
logger.handlers = [_handler]
logger.propagate = False
