# OCI MCP Client

Cliente Python independiente para consumir herramientas de Oracle Cloud Infrastructure (OCI)
publicadas mediante Model Context Protocol (MCP). Usa `langchain-mcp-adapters` para descubrir
las tools, `langchain-openai` para el modelo y el runtime de LangGraph que construye
`langchain.agents.create_agent`.

No es necesario clonar `oracle/mcp`: en modo `stdio`, `uvx` descarga y ejecuta cada paquete
publicado en un subproceso aislado.

## Requisitos

- `uv` y `uvx` instalados.
- Python 3.12 o posterior (administrado automáticamente por `uv`).
- Un perfil OCI local en `~/.oci/config`.
- Una API key de OpenAI.

La documentación vigente de Oracle recomienda autenticar una sesión local así:

```shell
oci session authenticate --region=<region> --tenancy-name=<tenancy_name>
```

Para renovar una sesión:

```shell
oci session authenticate --profile-name <profile_name> --region <region> --auth security_token
```

Aplica IAM de mínimo privilegio al perfil. Algunos servidores pueden requerir autenticación por
API key de OCI en lugar de una sesión con security token; consulta el README del servidor
correspondiente.

## Instalación

Desde este directorio:

```powershell
uv sync
Copy-Item .env.example .env
```

En macOS o Linux, copia el entorno con `cp .env.example .env`. Después completa al menos:

```dotenv
OCI_CONFIG_PROFILE=DEFAULT
OPENAI_API_KEY=sk-...
MCP_TRANSPORT_MODE=stdio
```

`uv sync` crea y mantiene `.venv`; no es necesario activar el entorno para ejecutar comandos con
`uv run`.

## Uso

```shell
uv run oci-mcp-client
```

También puede ejecutarse como módulo:

```shell
uv run python -m mcp_client.main
```

Al iniciar, cada servidor se conecta de manera independiente. Un fallo se reintenta y luego se
registra sin descartar las tools que sí pudieron cargarse desde los demás servidores.

## Servidores configurados

El catálogo declarativo vive únicamente en `src/mcp_client/config/servers.py`:

- `oracle.oci-compute-mcp-server`
- `oracle.oci-identity-mcp-server`
- `oracle.oci-networking-mcp-server`
- `oracle.oci-network-load-balancer-mcp-server`
- `oracle.oci-object-storage-mcp-server`
- `oracle.oci-monitoring-mcp-server`
- `oracle.oci-logging-mcp-server`
- `oracle.oci-registry-mcp-server`
- `oracle.oci-api-mcp-server`
- `oracle.oci-resource-search-mcp-server`
- `oracle.oci-migration-mcp-server`
- `oracle.oci-compute-instance-agent-mcp-server`

Para agregar o quitar un servidor, modifica solamente `OCI_MCP_SERVERS`. El cliente, cargador y
agente no contienen nombres de servicios.

## Transportes

### stdio (predeterminado)

Cada entrada se inicia con este patrón:

```text
uvx oracle.oci-<servicio>-mcp-server@latest
```

El subproceso recibe `OCI_CONFIG_PROFILE` y `FASTMCP_LOG_LEVEL=ERROR` sin copiar credenciales al
código o a los logs.

### HTTP

Configura `MCP_TRANSPORT_MODE=http`. Una sola URL base se deriva de
`ORACLE_MCP_HOST`/`ORACLE_MCP_PORT`. Para procesos que escuchan en puertos distintos, define un
mapa JSON por alias:

```dotenv
ORACLE_MCP_URLS={"compute":"http://127.0.0.1:8888/mcp","identity":"http://127.0.0.1:8889/mcp"}
```

Si ya cuentas con un access token IDCS válido, `ORACLE_MCP_BEARER_TOKEN` lo envía en el header
`Authorization`; su valor nunca se registra. En despliegues HTTP de Oracle también deben
configurarse en el proceso servidor `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`,
`IDCS_AUDIENCE`, `ORACLE_MCP_BASE_URL` y `OCI_REGION`, y registrar
`${ORACLE_MCP_BASE_URL}/auth/callback` en la aplicación confidencial de OCI IAM.

La documentación actual de Oracle marca `oracle.oci-api-mcp-server` como exclusivo de `stdio`.
Por ello, permanece en `stdio` aunque el modo global sea HTTP.

## Configuración

| Variable | Requerida | Valor predeterminado | Uso |
|---|---:|---|---|
| `OCI_CONFIG_PROFILE` | Sí | — | Perfil local para servidores `stdio` |
| `OPENAI_API_KEY` | Sí | — | Credencial del modelo |
| `OPENAI_MODEL` | No | `gpt-5.6-terra` | Modelo con tool calling |
| `MCP_TRANSPORT_MODE` | No | `stdio` | `stdio` o `http` |
| `ORACLE_MCP_HOST` | No | `127.0.0.1` | Host HTTP común |
| `ORACLE_MCP_PORT` | No | `8888` | Puerto HTTP común |
| `ORACLE_MCP_URLS` | No | `{}` | URLs HTTP por alias |
| `ORACLE_MCP_BEARER_TOKEN` | No | vacío | Bearer token HTTP |
| `LOG_LEVEL` | No | `INFO` | Nivel de logging |
| `LOG_FILE` | No | `logs/mcp_client.log` | Archivo rotativo |
| `MCP_LOAD_ATTEMPTS` | No | `2` | Intentos de carga por servidor |
| `MCP_RETRY_DELAY_SECONDS` | No | `0.5` | Base del backoff lineal |

## Arquitectura

```text
src/mcp_client/
├── config/              # Variables y catálogo declarativo
├── mcp/                 # Fábrica y carga resiliente de tools
├── agent/               # Agente LangGraph/LangChain
├── logging_config.py    # Consola, rotación, correlación e invocaciones
└── main.py              # Composición y CLI
```

El logger genera un `request_id` por pregunta y registra conexión, carga e invocación de tools,
duración y resultado. Los argumentos se truncan y los campos sensibles se redactan.

## Pruebas

Las pruebas son unitarias y no llaman a OCI, OpenAI ni a procesos `uvx`:

```shell
uv run python -m unittest discover -s tests -v
```

## Fuentes de diseño

- [Documentación navegable de oracle/mcp en DeepWiki](https://deepwiki.com/oracle/mcp)
- [Repositorio y autenticación de oracle/mcp](https://github.com/oracle/mcp)
- [Integración MCP de LangChain](https://docs.langchain.com/oss/python/langchain/mcp)
- [Modelos de OpenAI](https://developers.openai.com/api/docs/models)

Oracle describe estos servidores como implementaciones de referencia para exploración y
prototipado, no como una solución de producción lista para usar. Antes de producción añade
políticas de autorización, aprobación humana para cambios destructivos, observabilidad y pruebas
de integración en una tenancy aislada.

