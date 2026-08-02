"""Logging centralizado e instrumentación de invocaciones MCP."""

from __future__ import annotations

import json
import logging
import logging.config
import time
import uuid
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_SENSITIVE_MARKERS = ("authorization", "secret", "password", "token", "api_key")


class RequestIdFilter(logging.Filter):
    """Añade el identificador de correlación al registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


def set_request_id(value: str | None = None) -> Token[str]:
    """Establece un identificador de correlación y devuelve su token de contexto."""
    return _request_id.set(value or str(uuid.uuid4()))


def reset_request_id(token: Token[str]) -> None:
    """Restaura el contexto de correlación anterior."""
    _request_id.reset(token)


def configure_logging(level: str, log_file: Path) -> None:
    """Configura salida a consola y archivo rotativo."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = "%(asctime)s | %(name)s | %(levelname)s | request_id=%(request_id)s | %(message)s"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": RequestIdFilter}},
            "formatters": {"standard": {"format": formatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "standard",
                    "filters": ["request_id"],
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": level,
                    "formatter": "standard",
                    "filters": ["request_id"],
                    "filename": str(log_file),
                    "maxBytes": 5_000_000,
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
            },
            "root": {"level": level, "handlers": ["console", "file"]},
        }
    )


class ToolInvocationLoggingHandler(BaseCallbackHandler):
    """Registra argumentos resumidos, duración y resultado de cada tool."""

    def __init__(self, server_name: str) -> None:
        self.server_name = server_name
        self._started_at: dict[uuid.UUID, float] = {}
        self._logger = logging.getLogger("mcp_client.tools")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: uuid.UUID,
        **kwargs: Any,
    ) -> None:
        self._started_at[run_id] = time.perf_counter()
        tool_name = serialized.get("name", "unknown")
        arguments = kwargs.get("inputs", input_str)
        self._logger.info(
            "Invocando tool server=%s tool=%s args=%s",
            self.server_name,
            tool_name,
            _summarize(arguments),
        )

    def on_tool_end(self, output: Any, *, run_id: uuid.UUID, **kwargs: Any) -> None:
        self._logger.info(
            "Tool finalizada server=%s duration_ms=%.2f success=true",
            self.server_name,
            self._duration_ms(run_id),
        )

    def on_tool_error(self, error: BaseException, *, run_id: uuid.UUID, **kwargs: Any) -> None:
        message = str(error)
        if _looks_like_authentication_error(message):
            self._logger.error(
                "Fallo de autenticación OCI server=%s duration_ms=%.2f error=%s",
                self.server_name,
                self._duration_ms(run_id),
                message,
            )
            return
        self._logger.error(
            "Tool falló server=%s duration_ms=%.2f success=false error=%s",
            self.server_name,
            self._duration_ms(run_id),
            message,
        )

    def _duration_ms(self, run_id: uuid.UUID) -> float:
        started_at = self._started_at.pop(run_id, time.perf_counter())
        return (time.perf_counter() - started_at) * 1_000


def _summarize(value: Any, limit: int = 500) -> str:
    redacted = _redact(value)
    try:
        rendered = json.dumps(redacted, ensure_ascii=False, default=str)
    except TypeError:
        rendered = str(redacted)
    return rendered if len(rendered) <= limit else f"{rendered[:limit]}…"


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "***"
                if any(marker in key.lower() for marker in _SENSITIVE_MARKERS)
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _looks_like_authentication_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in ("401", "notauthenticated", "authentication"))
