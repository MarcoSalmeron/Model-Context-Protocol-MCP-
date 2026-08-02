"""Fábrica del cliente MCP multiserver."""

from __future__ import annotations

import logging

from langchain_mcp_adapters.client import MultiServerMCPClient

from mcp_client.config.servers import build_server_connections
from mcp_client.config.settings import Settings

logger = logging.getLogger(__name__)

def create_mcp_client(settings: Settings) -> MultiServerMCPClient:
    """Construye el cliente; la conexión efectiva y sus reintentos son diferidos."""
    connections = build_server_connections(settings)
    logger.info(
        "Construyendo cliente MCP transport=%s servers=%d",
        settings.mcp_transport_mode,
        len(connections),
    )
    return MultiServerMCPClient(connections)
