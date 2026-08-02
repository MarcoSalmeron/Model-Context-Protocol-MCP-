"""Carga aislada y resiliente de herramientas desde todos los servidores."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from mcp_client.logging_config import ToolInvocationLoggingHandler

logger = logging.getLogger(__name__)


async def load_all_tools(
    client: MultiServerMCPClient,
    *,
    max_attempts: int = 2,
    retry_delay_seconds: float = 0.5,
) -> list[BaseTool]:
    """Carga tools por servidor sin propagar el fallo de uno a los demás."""
    server_names = tuple(client.connections)
    tasks = [
        _load_server_tools(client, name, max_attempts, retry_delay_seconds) for name in server_names
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    loaded: list[BaseTool] = []
    for server_name, result in zip(server_names, results, strict=True):
        if isinstance(result, BaseException):
            _log_load_failure(server_name, result)
            continue
        loaded.extend(_instrument_tools(result, server_name))
        logger.info("Tools cargadas server=%s count=%d", server_name, len(result))

    logger.info("Carga MCP finalizada tools=%d servers=%d", len(loaded), len(server_names))
    return loaded


async def _load_server_tools(
    client: MultiServerMCPClient,
    server_name: str,
    max_attempts: int,
    retry_delay_seconds: float,
) -> list[BaseTool]:
    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Conectando a servidor MCP server=%s attempt=%d/%d",
            server_name,
            attempt,
            max_attempts,
        )
        try:
            return await client.get_tools(server_name=server_name)
        except Exception:
            if attempt == max_attempts:
                raise
            logger.warning("Conexión MCP falló; reintentando server=%s", server_name)
            await asyncio.sleep(retry_delay_seconds * attempt)
    return []


def _instrument_tools(tools: Sequence[BaseTool], server_name: str) -> list[BaseTool]:
    handler = ToolInvocationLoggingHandler(server_name)
    for tool in tools:
        callbacks: list[Any] = list(tool.callbacks or [])
        tool.callbacks = [*callbacks, handler]
        tool.metadata = {**(tool.metadata or {}), "mcp_server": server_name}
    return list(tools)


def _log_load_failure(server_name: str, error: BaseException) -> None:
    message = str(error)
    if any(marker in message.lower() for marker in ("401", "notauthenticated", "authentication")):
        logger.error("Fallo de autenticación OCI server=%s error=%s", server_name, message)
        return
    logger.error("No fue posible cargar tools server=%s error=%s", server_name, message)
