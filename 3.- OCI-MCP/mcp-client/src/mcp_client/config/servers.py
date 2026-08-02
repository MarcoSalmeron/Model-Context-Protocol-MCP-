"""Catálogo declarativo de servidores MCP de OCI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp_client.config.settings import Settings


@dataclass(frozen=True, slots=True)
class MCPServerConfig:
    """Describe un servidor sin acoplarlo al cliente o al agente."""

    alias: str
    package: str
    supports_http: bool = True


OCI_MCP_SERVERS: tuple[MCPServerConfig, ...] = (
    MCPServerConfig("compute", "oracle.oci-compute-mcp-server"),
    MCPServerConfig("identity", "oracle.oci-identity-mcp-server"),
    MCPServerConfig("networking", "oracle.oci-networking-mcp-server"),
    MCPServerConfig("network-load-balancer", "oracle.oci-network-load-balancer-mcp-server"),
    MCPServerConfig("object-storage", "oracle.oci-object-storage-mcp-server"),
    MCPServerConfig("monitoring", "oracle.oci-monitoring-mcp-server"),
    MCPServerConfig("logging", "oracle.oci-logging-mcp-server"),
    MCPServerConfig("registry", "oracle.oci-registry-mcp-server"),
    MCPServerConfig("api", "oracle.oci-api-mcp-server", supports_http=False),
    MCPServerConfig("resource-search", "oracle.oci-resource-search-mcp-server"),
    MCPServerConfig("migration", "oracle.oci-migration-mcp-server"),
    MCPServerConfig("compute-instance-agent", "oracle.oci-compute-instance-agent-mcp-server"),
)


def build_server_connections(settings: Settings) -> dict[str, dict[str, Any]]:
    """Genera la configuración que consume ``MultiServerMCPClient``."""
    return {server.alias: _connection_for(server, settings) for server in OCI_MCP_SERVERS}


def _connection_for(server: MCPServerConfig, settings: Settings) -> dict[str, Any]:
    if settings.mcp_transport_mode == "http" and server.supports_http:
        default_url = f"http://{settings.oracle_mcp_host}:{settings.oracle_mcp_port}/mcp"
        connection: dict[str, Any] = {
            "transport": "http",
            "url": (settings.oracle_mcp_urls or {}).get(server.alias, default_url),
        }
        if settings.oracle_mcp_bearer_token:
            connection["headers"] = {"Authorization": f"Bearer {settings.oracle_mcp_bearer_token}"}
        return connection

    return {
        "transport": "stdio",
        "command": "uvx",
        "args": [f"{server.package}@latest"],
        "env": {
            "OCI_CONFIG_PROFILE": settings.oci_config_profile,
            "FASTMCP_LOG_LEVEL": "ERROR",
        },
    }
