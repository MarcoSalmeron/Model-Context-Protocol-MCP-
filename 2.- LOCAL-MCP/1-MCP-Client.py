### Crear agente de IA conectado a servidor MCP en lugar de tools locales

from dotenv import load_dotenv
import os
import asyncio

load_dotenv(override=True)

print(f"API Key: {bool(os.getenv('OPENAI_API_KEY'))}")

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

### Conectar al MCP Server Local
async def main():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_server = os.path.join(directorio_actual, "2-MCP-Server.py")

    # 1.- Crear cliente MCP
    client = MultiServerMCPClient({
            "math": {
                "command": "python",
                "args": [directorio_server], # Ruta servidor local MCP
                "transport": "stdio",        # transport="http" para usar en un servidor externo MCP
            },
        })
    
    # 2.- Obtener lista de tools del servidor MCP
    tools = await client.get_tools()
    print('#'*30)
    print(f'Tools del servidor MCP: {len(tools)}')
    print('#'*30)

    for tool in tools:
        print(f'Nombre: {tool.name}')
        print(f'Descripción: {tool.description[:60]}...') 
        print()

    # 3.- Crear agente con tools del servidor MCP
    agent = create_agent(
        model=llm,
        tools=tools,
    )

    # 4.- Ejecutar agente con tools del servidor MCP
    async def run_agent(prompt: str):
        print(f'Prompt: {prompt}\n') 

        result = await agent.ainvoke({
            "messages": [("user", prompt)]
        })

        for msg in result["messages"]:

            if msg.type == "human":
                continue

            elif msg.type == "ai":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"🧠 Agent thinks → calling: {tc['name']}({tc['args']})")
                elif msg.content:
                    print(f"🤖 Agent answer: {msg.content}")

            elif msg.type == "tool":
                # Extract clean result from MCP tool response
                content = msg.content
                # MCP returns structured content as a list of dicts
                # e.g. [{'type': 'text', 'text': '120.0', ...}]
                # Extract just the text value for clean display
                if isinstance(content, list):
                    texts = [item["text"] for item in content if isinstance(item, dict) and "text" in item]
                    content = ", ".join(texts) if texts else str(content)
                print(f"🛠️ Tool result: {content}")

        print("=" * 55,'\n')

    ### Casos de uso
    await run_agent("¿Cuanto es 2 + 2 y luego dividio por 2?")
    await run_agent("¿Cuanto es 5 x 15?") 
    await run_agent("Cuanto es 100 dividido por 0?")

    print('\nDEMO MCP COMPLETADO!!\n')
    
if __name__ == "__main__":
    asyncio.run(main())