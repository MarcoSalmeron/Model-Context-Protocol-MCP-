"""Agente ReAct construido por LangChain sobre el runtime de LangGraph."""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from mcp_client.config.settings import Settings

SYSTEM_PROMPT = """Eres un asistente de operaciones de Oracle Cloud Infrastructure.
Usa únicamente las tools MCP necesarias, confirma los datos antes de cualquier operación
destructiva y nunca reveles credenciales ni material sensible en tus respuestas.
"""


def build_agent(tools: list[BaseTool], settings: Settings) -> Any:
    """Crea un agente de LangChain cuyo grafo de ejecución usa LangGraph."""
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        use_responses_api=True,
    )
    return create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
