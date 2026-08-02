from __future__ import annotations

import unittest
from pathlib import Path

from mcp_client.config.settings import MissingEnvVarError, Settings


class SettingsTests(unittest.TestCase):
    def test_missing_required_environment_variables_raise_clear_error(self) -> None:
        with self.assertRaises(MissingEnvVarError) as context:
            Settings.from_env(dotenv_path=Path("does-not-exist.env"), environ={})

        self.assertEqual(context.exception.names, ("OCI_CONFIG_PROFILE", "OPENAI_API_KEY"))

    def test_invalid_transport_is_rejected(self) -> None:
        environment = {
            "OCI_CONFIG_PROFILE": "DEFAULT",
            "OPENAI_API_KEY": "test-key",
            "MCP_TRANSPORT_MODE": "sse",
        }

        with self.assertRaisesRegex(ValueError, "stdio.*http"):
            Settings.from_env(dotenv_path=Path("does-not-exist.env"), environ=environment)


if __name__ == "__main__":
    unittest.main()
