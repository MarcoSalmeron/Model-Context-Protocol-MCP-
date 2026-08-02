import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import os 

load_dotenv(override=True)

print(f"API Key: {bool(os.getenv('OPENAI_API_KEY'))}")  

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, openai_api_key=os.getenv('OPENAI_API_KEY'), verbose=True, streaming=True)

async def main():

     # Cada invocación de herramienta crea un MCP nuevoClientSession, ejecuta la herramienta y luego limpia.
    client = MultiServerMCPClient({
            "mcp": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",  # Hosted server
                # "url": "http://localhost:8000/mcp",     # Local server
                
                # "headers": {
                #    "Authorization": "Bearer YOUR_TOKEN",
                #    "X-Custom-Header": "custom-value"
                # },
            }
        })

    # Obtener lista de herramientas del servidor MCP y usarlas en un agente
    # Ventaja: No es necesario crear herramientas localmente, implementacion desacoplada 
    tools = await client.get_tools()

    print(f'Tools del servidor MCP: {len(tools)}')
    for tool in tools:
        print(f'Nombre: {tool.name}, Descripción: {tool.description[:60]}...\n')
         
    agent = create_agent(model=llm, tools=tools)

    _run_agent("How do I connect LangChain to an MCP server over HTTP?", agent)

# Auxiliar 
def _run_agent(prompt: str, agent: any):

    print(f'Prompt: {prompt}\n')

    result = agent.ainvoke({
        "messages": [{"role": "user", "content": prompt}]
    })
    for msg in result["messages"]:
        if msg.type == "tool":
            print(f"🛠️ Tool result: {msg.content}")
        elif msg.type == "ai":
            print(f"🤖 Agent answer: {msg.content}")
        elif msg.type == "human":
            print(f"🧠 Agent thinks: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())