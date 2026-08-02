from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, Mock

from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from mcp_client.mcp.tool_loader import load_all_tools


def _echo(value: str) -> str:
    return value


class ToolLoaderTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_server_does_not_discard_healthy_tools(self) -> None:
        calls = {"healthy": 0, "offline": 0}

        async def get_tools(*, server_name: str) -> list[StructuredTool]:
            calls[server_name] += 1
            if server_name == "offline":
                raise ConnectionError("server unavailable")
            return [StructuredTool.from_function(_echo, name="echo", description="Echo input")]

        client = Mock(spec=MultiServerMCPClient)
        client.connections = {"healthy": {}, "offline": {}}
        client.get_tools = AsyncMock(side_effect=get_tools)

        tools = await load_all_tools(client, max_attempts=2, retry_delay_seconds=0)

        self.assertEqual([tool.name for tool in tools], ["echo"])
        self.assertEqual(calls, {"healthy": 1, "offline": 2})
        self.assertEqual(tools[0].metadata["mcp_server"], "healthy")
        self.assertEqual(len(tools[0].callbacks), 1)


class AllServersFailTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_result_when_every_server_fails(self) -> None:
        client = Mock(spec=MultiServerMCPClient)
        client.connections = {"offline": {}}
        client.get_tools = AsyncMock(side_effect=ConnectionError("server unavailable"))

        tools = await load_all_tools(client, max_attempts=1, retry_delay_seconds=0)

        self.assertEqual(tools, [])
        client.get_tools.assert_awaited_once_with(server_name="offline")


if __name__ == "__main__":
    unittest.main()
