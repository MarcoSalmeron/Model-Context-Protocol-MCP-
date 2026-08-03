"""Entrypoint asíncrono y CLI interactiva."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.messages import BaseMessage

from mcp_client.agent.graph import build_agent
from mcp_client.config.settings import Settings
from mcp_client.logging_config import configure_logging, reset_request_id, set_request_id
from mcp_client.mcp.client_factory import create_mcp_client
from mcp_client.mcp.tool_loader import load_all_tools

logger = logging.getLogger(__name__)


async def ask(agent: Any, question: str) -> str:
    """Ejecuta una consulta correlacionada y devuelve el texto final del agente."""
    token = set_request_id()
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": question}]})
        messages: list[BaseMessage] = result["messages"]
        return _message_text(messages[-1])
    finally:
        reset_request_id(token)


async def main() -> None:
    """Inicializa configuración, MCP, agente y el loop interactivo."""
    settings = Settings.from_env()
    configure_logging(settings.log_level, settings.log_file)
    logger.info("Iniciando cliente OCI MCP")

    client = create_mcp_client(settings)
    tools = await load_all_tools(
        client,
        max_attempts=settings.mcp_load_attempts,
        retry_delay_seconds=settings.mcp_retry_delay_seconds,
    )
    if not tools:
        raise RuntimeError(
            "Ningún servidor MCP entregó tools; revisa uvx, credenciales OCI y los logs"
        )

    agent = build_agent(tools, settings)
    print(f"Cliente listo con {len(tools)} tools. Escribe 'salir' para terminar.")
    while True:
        question = (await asyncio.to_thread(input, "\nOCI> ")).strip()
        if question.lower() in {"salir", "exit", "quit"}:
            break
        if question:
            print(await ask(agent, question))


def run() -> None:
    """Ejecuta el entrypoint asíncrono desde consola"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSesión finalizada.")
    except Exception:
        logging.getLogger(__name__).exception("El cliente no pudo iniciar")
        raise


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"}
        ]
        return "\n".join(part for part in parts if part)
    return str(content)


if __name__ == "__main__":
    run()
