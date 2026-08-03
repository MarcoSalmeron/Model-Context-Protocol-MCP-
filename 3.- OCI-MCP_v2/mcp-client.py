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

    # Conexion a un servidor MCP de OCI
    client = MultiServerMCPClient({
            "oci_usage": {
                "command": "uvx",
                "args": ["oracle.oci-usage-mcp-server"],
                "transport": "stdio",
                "env": {
                    **os.environ,
                    "OCI_CONFIG_PROFILE": "DEFAULT",
                    "OCI_CLI_AUTH": "api_key",
                    "FASTMCP_LOG_LEVEL": "ERROR",
                },
            },
        })

    # Obtener lista de herramientas del servidor MCP 
    tools = await client.get_tools()
    print(f"{'#'*50}\n -- Tools disponibles: ({len(tools)}) \n{'#'*50}\n")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    # Crear agente con herramientas del servidor MCP de OCI
    agent = create_agent(
        model=11m,
        tools=tools,
        system_prompt=(
            "You are an Oracle Cloud Infrastructure (OCI) cost-and-usage "
            "assistant.\n\n"
            f"The user's tenancy OCID is: {tenancy_ocid}\n"
            f"Today's date in UTC is: {today_utc}\n\n"
            "Use the get_summarized_usage tool to answer questions. "
            "Required arguments:\n"
            " - tenant_id: the tenancy OCID above\n"
            " - start_time: ISO 8601, MUST be midnight UTC "
            "(e.g. 2024-01-01T00:00:00Z)\n"
            " - end_time: ISO 8601, midnight UTC, exclusive\n"
            " - group_by: array of dimensions. Use [\"service\"] for "
            "service breakdowns, [\"compartmentName\"] for per-compartment, "
            "[\"skuName\"] for sku-level, or [] for a single total.\n"
            " - compartment_depth: integer, use 1 unless the user "
            "specifically asks for child-compartment detail.\n"
            "Optional: granularity (DAILY/MONTHLY/HOURLY/TOTAL), "
            "query_type (COST or USAGE; default to COST if spend "
            "questions, USAGE for consumption).\n\n"
            "OUTPUT RULES:\n"
            "Do NOT produce a numerical table or list of per-service or "
            "per-day numbers in your reply. The application renders an "
            "exact table from the raw tool result on its own. Your job "
            "is to give a brief natural-language insight (2-4 sentences) "
            "about what stands out: which service or day dominates, any "
            "obvious trend, anything worth a closer look. If the result "
            "is empty or the call fails, say so plainly - do not invent."
        ),
    )

    # Ejecutar agente
    question = (
        "Show me my OCI cost for the last 30 days as a daily breakdown by "
        "service. I want to compare it to the OCI Cost Analysis console "
        "with Granularity=Daily, Show=Cost, Group by=Service. After the "
        "table, give me one or two sentences pointing out anything notable."
    )

    print(f"User: {question}\n")

    response = await agent.ainvoke({"messages": [("user", question)]})
    messages = response["messages"]

    # Debug
    for msg in messages:
        if msg.type == "tool":
            print(f"🛠️ Tool result: {msg.content}")
        elif msg.type == "ai":
            print(f"🤖 Agent answer: {msg.content}")
        elif msg.type == "human":
            print(f"🧠 Agent thinks: {msg.content}")
        else:
            print(f"🤔 Agent message: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())