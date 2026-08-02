"""Carga y validación centralizada de variables de entorno."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from dotenv import load_dotenv

TransportMode = Literal["stdio", "http"]


class MissingEnvVarError(ValueError):
    """Indica que faltan variables de entorno necesarias para arrancar."""

    def __init__(self, names: list[str]) -> None:
        joined = ", ".join(sorted(names))
        super().__init__(f"Faltan variables de entorno requeridas: {joined}")
        self.names = tuple(sorted(names))


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuración inmutable de la aplicación."""

    oci_config_profile: str
    openai_api_key: str
    openai_model: str = "gpt-5.6-terra"
    mcp_transport_mode: TransportMode = "stdio"
    oracle_mcp_host: str = "127.0.0.1"
    oracle_mcp_port: int = 8888
    oracle_mcp_urls: Mapping[str, str] | None = None
    oracle_mcp_bearer_token: str | None = None
    log_level: str = "INFO"
    log_file: Path = Path("logs/mcp_client.log")
    mcp_load_attempts: int = 2
    mcp_retry_delay_seconds: float = 0.5

    @classmethod
    def from_env(
        cls,
        dotenv_path: str | Path = ".env",
        environ: Mapping[str, str] | None = None,
    ) -> Self:
        """Carga ``.env`` y construye una configuración validada."""
        load_dotenv(dotenv_path=dotenv_path, override=False)
        env = os.environ if environ is None else environ

        required = ("OCI_CONFIG_PROFILE", "OPENAI_API_KEY")
        missing = [name for name in required if not env.get(name, "").strip()]
        if missing:
            raise MissingEnvVarError(missing)

        transport = env.get("MCP_TRANSPORT_MODE", "stdio").strip().lower()
        if transport not in {"stdio", "http"}:
            raise ValueError("MCP_TRANSPORT_MODE debe ser 'stdio' o 'http'")

        urls = _parse_http_urls(env.get("ORACLE_MCP_URLS", ""))
        port = _positive_int(env.get("ORACLE_MCP_PORT", "8888"), "ORACLE_MCP_PORT")
        attempts = _positive_int(env.get("MCP_LOAD_ATTEMPTS", "2"), "MCP_LOAD_ATTEMPTS")
        delay = _non_negative_float(
            env.get("MCP_RETRY_DELAY_SECONDS", "0.5"), "MCP_RETRY_DELAY_SECONDS"
        )

        return cls(
            oci_config_profile=env["OCI_CONFIG_PROFILE"].strip(),
            openai_api_key=env["OPENAI_API_KEY"].strip(),
            openai_model=env.get("OPENAI_MODEL", "gpt-5.6-terra").strip(),
            mcp_transport_mode=transport,
            oracle_mcp_host=env.get("ORACLE_MCP_HOST", "127.0.0.1").strip(),
            oracle_mcp_port=port,
            oracle_mcp_urls=urls,
            oracle_mcp_bearer_token=env.get("ORACLE_MCP_BEARER_TOKEN", "").strip() or None,
            log_level=env.get("LOG_LEVEL", "INFO").strip().upper(),
            log_file=Path(env.get("LOG_FILE", "logs/mcp_client.log")),
            mcp_load_attempts=attempts,
            mcp_retry_delay_seconds=delay,
        )


def _parse_http_urls(raw_value: str) -> Mapping[str, str]:
    if not raw_value.strip():
        return {}
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("ORACLE_MCP_URLS debe ser un objeto JSON válido") from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(url, str) for key, url in value.items()
    ):
        raise ValueError("ORACLE_MCP_URLS debe mapear alias de servidor a URLs")
    return value


def _positive_int(raw_value: str, name: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un entero") from exc
    if value < 1:
        raise ValueError(f"{name} debe ser mayor que cero")
    return value


def _non_negative_float(raw_value: str, name: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    if value < 0:
        raise ValueError(f"{name} no puede ser negativo")
    return value
