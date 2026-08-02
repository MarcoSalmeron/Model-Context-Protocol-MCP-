from __future__ import annotations

import unittest

from mcp_client.config.servers import OCI_MCP_SERVERS, build_server_connections
from mcp_client.config.settings import Settings


class ServerConfigurationTests(unittest.TestCase):
    def test_stdio_configures_all_requested_packages(self) -> None:
        settings = Settings(oci_config_profile="TEAM", openai_api_key="test-key")

        connections = build_server_connections(settings)

        self.assertEqual(len(connections), 12)
        for server in OCI_MCP_SERVERS:
            connection = connections[server.alias]
            self.assertEqual(connection["transport"], "stdio")
            self.assertEqual(connection["command"], "uvx")
            self.assertEqual(connection["args"], [f"{server.package}@latest"])
            self.assertEqual(connection["env"]["OCI_CONFIG_PROFILE"], "TEAM")

    def test_http_uses_per_server_url_and_keeps_api_on_stdio(self) -> None:
        settings = Settings(
            oci_config_profile="DEFAULT",
            openai_api_key="test-key",
            mcp_transport_mode="http",
            oracle_mcp_host="mcp.local",
            oracle_mcp_port=9000,
            oracle_mcp_urls={"compute": "https://compute.example/mcp"},
            oracle_mcp_bearer_token="secret-token",
        )

        connections = build_server_connections(settings)

        self.assertEqual(connections["compute"]["url"], "https://compute.example/mcp")
        self.assertEqual(connections["identity"]["url"], "http://mcp.local:9000/mcp")
        self.assertEqual(
            connections["identity"]["headers"], {"Authorization": "Bearer secret-token"}
        )
        self.assertEqual(connections["api"]["transport"], "stdio")


if __name__ == "__main__":
    unittest.main()
