"""Connected MCP LIFE configuration proof without replaying its lifecycle."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import mcp_server, native_driver
from xar_autoplayer.bridge.service import GameplayBridgeService


class _NoGameEndpoint:
    def __init__(self):
        self.starts = 0
        self.closes = 0

    def start(self, on_message, on_disconnect):
        self.starts += 1

    def send(self, *args, **kwargs):
        raise AssertionError("LIFE configuration must not send a game operation")

    def close(self):
        self.closes += 1


class McpLifestyleFormalConfig12004Test(unittest.TestCase):
    def test_public_argv_reaches_native_constructor_and_normal_service(self):
        from mcp.server import MCPServer

        scenes = (
            ("default", [], False, False),
            ("formal", ["--allow-private-lifestyle-formal-trial"], True, False),
            ("initial_focus", [
                "--allow-private-lifestyle-formal-trial",
                "--require-initial-lifestyle-focus-before-date-advance",
            ], True, True),
        )
        configured, runs = [], []
        for name, options, formal, initial_focus in scenes:
            with self.subTest(scene=name), tempfile.TemporaryDirectory() as tmp:
                endpoint = _NoGameEndpoint()

                def configure_service(driver):
                    # Preserve the real main -> factory -> constructor chain.
                    self.assertIsInstance(driver, native_driver.NativeHeadlessGameplayDriver)
                    self.assertIs(driver.allow_private_lifestyle_formal_trial, formal)
                    self.assertIs(getattr(
                        driver, "require_initial_lifestyle_focus_before_date_advance", False,
                    ), initial_focus)
                    if initial_focus:
                        self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_submit")
                    self.assertEqual(driver.state_dir, Path(tmp))
                    service = GameplayBridgeService(driver)
                    self.assertIs(service.driver, driver)
                    configured.append(service)
                    return service

                def capture_run(server, **kwargs):
                    self.assertIsInstance(server, MCPServer)
                    self.assertEqual(kwargs, {"transport": "stdio"})
                    runs.append(server)

                with patch.object(native_driver, "NativeNamedPipeServer", return_value=endpoint), \
                        patch.object(mcp_server, "GameplayBridgeService", side_effect=configure_service), \
                        patch.object(MCPServer, "run", new=capture_run):
                    self.assertEqual(mcp_server.main([
                        "--driver", "native-headless", "--transport", "stdio",
                        "--state-dir", tmp,
                        "--pipe-name", r"\\.\pipe\xar_ck3_m4_life_config_fixture",
                        *options,
                    ]), 0)
                self.assertEqual((endpoint.starts, endpoint.closes), (1, 1))
        self.assertEqual((len(configured), len(runs)), (3, 3))

        # The opening gate depends on LIFE and must reject before a pipe starts.
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(native_driver, "NativeNamedPipeServer") as endpoint_factory, \
                    patch.object(mcp_server, "create_server") as server_factory:
                with self.assertRaisesRegex(
                    ValueError, "initial lifestyle focus requires the private lifestyle formal trial",
                ):
                    mcp_server.main([
                        "--driver", "native-headless", "--transport", "stdio",
                        "--state-dir", tmp,
                        "--pipe-name", r"\\.\pipe\xar_ck3_m4_life_config_fixture",
                        "--require-initial-lifestyle-focus-before-date-advance",
                    ])
                endpoint_factory.assert_not_called()
                server_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
