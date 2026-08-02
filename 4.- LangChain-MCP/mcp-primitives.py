"""
Core Primitives de LangChain MCP:

1.- Tools:
    Las herramientas MCP son objetos que se pueden invocar desde un cliente MCP.
    sin necesidad de desarrollar las tools localmente, se pueden reutilizar desde un servidor MCP,
    permiten que los servidores MCP expongan funciones ejecutables que los LLM pueden invocar para realizar acciones
    —como consultar bases de datos, llamar a API o interactuar con sistemas externos. 
    LangChain convierte las herramientas MCP en herramientas LangChain, 
    haciéndolas directamente utilizables en cualquier agente o flujo de trabajo de LangChain.

2.- Resourses:
    Los recursos permiten que los servidores MCP expongan datos —como archivos, registros de bases de datos o respuestas de API—
    que los clientes pueden leer. LangChain convierte recursos MCP en objetos Blob,
    que proporcionan una interfaz unificada para manejar contenido tanto de texto como binario.

3.- Prompt Templates:
    Permiten a los servidores MCP exponer plantillas de avisos / texto reutilizables que los clientes pueden recuperar y utilizar. 
    LangChain convierte las indicaciones de MCP en mensajes, lo que facilita su integración en flujos de trabajo basados en chat.
"""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio
import os 

load_dotenv(override=True)

print(f"API Key: {bool(os.getenv('OPENAI_API_KEY'))}")  

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, openai_api_key=os.getenv('OPENAI_API_KEY'), verbose=True, streaming=True)

async def main():

    # Cliente a servidor externo MCP
    client = MultiServerMCPClient({
            "mcp": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",
            }
        })
    
    # #####################
    # 1.- Obtener Tools MCP
    # #####################

    # Obtener lista de herramientas del servidor MCP
    tools = await client.get_tools()
    print(f'1.- Tools del servidor MCP: {len(tools)}')

    for tool in tools:
        print(f'Nombre: {tool.name}, Descripción: {tool.description[:60]}...\n')

    # #####################
    # 2.- Resources MCP
    # #####################

    # Cargar todos los recursos de un servidor MCP específico
    blobs = await client.get_resources("server_name")

    # Especificar recurso via URI
    blob = await client.get_resources("server_name", uris=["file:///path/to/file.txt"])
    print(f'2.- Resources del servidor MCP: {len(blobs)}')

    for resource in blobs:
        print(f"URI: {resource.metadata['uri']}, MIME type: {resource.mimetype}")
        print(f'Tipo: {resource.type}\n')
        print(resource.as_string())

    # Extraer documentos de los blobs para mas contexto 
    docs = [Document(page_content=blob.as_string(), metadata=blob.metadata) for blob in blobs]

    # Usar estos docs en base de conocimientos RAG
    # retriever = vectorstore.as_retriever()

    # #####################
    # 3.- Prompt Templates MCP
    # #####################

    # Cargar prompt por nombre
    messages = await client.get_prompt("server_name", "summarize")

    # Cargar prompt con argumentos
    messages = await client.get_prompt(
        "server_name",
        "code_review",
        arguments={"language": "python", "focus": "security"}
    )

    for message in messages:
        print(f"{message.type}: {message.content}")

    # Extraer prompt template de los messages
    prompt = ChatPromptTemplate.from_messages([(m.type, m.content) for m in messages])

    # #####################
    # Crear Agente enriquecido con herramientas, recursos, contexto MCP
    # #####################

    agent = create_agent(
        model=llm, 
        tools=tools,          # Tools MCP
        prompt=prompt,        # Prompt Templates MCP
        # retriever=retriever # Context MCP
    )

if __name__ == "__main__":
    asyncio.run(main())