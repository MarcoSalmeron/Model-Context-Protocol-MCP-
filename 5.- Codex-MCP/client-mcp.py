"""
Instalar CLI de Codex con NPM:

& "C:\Program Files\nodejs\npm.ps1" install -g @openai/codex
"""
import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


NODE_EXE = r"C:\Program Files\nodejs\node.exe"

CODEX_JS = (
    r"C:\Users\Marco\AppData\Roaming\npm"
    r"\node_modules\@openai\codex\bin\codex.js"
)

PROJECT_DIR = str(Path(__file__).resolve().parent)


async def main():
    # Servidor MCP de Codex local
    transport = StdioTransport(
        command=NODE_EXE,
        args=[
            CODEX_JS,
            "mcp-server",
        ],
        cwd=PROJECT_DIR,
    )

    client = Client(transport)

    async with client:
        print("Conectado al servidor MCP de Codex.")

        tools = await client.list_tools()

        print(f"\n{'#'*50}\n -- Tools disponibles: \n{'#'*50}\n")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        result = await client.call_tool(
            "codex",
            {
                "prompt": (
                    "Crea una función de Python que ordene una lista de números. "
                    "Incluye type hints, docstring y pruebas unitarias. "
                    "Devuelve solamente la propuesta; no modifiques archivos."
                ),
                "cwd": PROJECT_DIR,
                "sandbox": "read-only",
                "approval-policy": "never",
            },
        )

        print("\nResultado completo:")
        print(result)

        if getattr(result, "content", None):
            print("\nRespuesta textual:")

            for block in result.content:
                block_text = getattr(block, "text", None)

                if block_text:
                    print(block_text)

        structured = getattr(result, "structured_content", None)

        if structured:
            thread_id = structured.get("threadId")
            print(f"\nThread ID: {thread_id}")

            if thread_id:
                continuation = await client.call_tool(
                    "codex-reply",
                    {
                        "threadId": thread_id,
                        "prompt": "Ahora agrega un ejemplo de uso.",
                    },
                )

                print("\nContinuación:")
                print(continuation)


if __name__ == "__main__":
    asyncio.run(main())