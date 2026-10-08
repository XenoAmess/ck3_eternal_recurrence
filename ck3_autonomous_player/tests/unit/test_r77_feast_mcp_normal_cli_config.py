"""Root-only parser → real MCP Service configuration compound, authored not run.

No native Feast lifecycle case is repeated. Only the game I/O driver factory
and server.run lifetime are substituted; no game or native operation is sent.
"""

from pathlib import Path
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


class McpFeastNormalCliConfigTest(unittest.TestCase):
    def test_real_parser_main_configures_real_service_without_io(self):
        from mcp.server import MCPServer

        flags = (
            "allow_private_activity_planner_diag_query",
            "allow_private_activity_feast_stage5_start_query",
            "allow_private_activity_feast_lifecycle_observation",
            "allow_private_activity_feast_stage5_start_action",
        )
        scenes = (
            ("default", [], (False, False, False, False)),
            ("queries", ["--private-activity-feast-queries"], (True, True, True, False)),
            ("normal", ["--allow-private-activity-feast-normal"], (True, True, True, True)),
            ("combined", ["--private-activity-feast-queries",
                          "--allow-private-activity-feast-normal"], (True, True, True, True)),
        )
        loaded, configured, runs = [], [], []

        def unexpected_io(*args, **kwargs):
            raise AssertionError("parser/config compound must not query or operate the game")

        for name, options, expected in scenes:
            with self.subTest(scene=name):
                state_dir = Path("source-only-fixture") / name

                def load_fixture(factory, **kwargs):
                    self.assertEqual(factory, "native-headless")
                    self.assertEqual(kwargs["state_dir"], state_dir)
                    driver = CallbackGameplayDriver(backend_id="native-headless",
                        snapshot=unexpected_io, execute=unexpected_io,
                        action_steps=("life-advance",))
                    driver.state_dir = state_dir
                    for flag in flags:
                        setattr(driver, flag, False)
                    loaded.append(driver)
                    return driver

                def configure_service(driver):
                    self.assertIs(driver, loaded[-1])
                    self.assertEqual(tuple(getattr(driver, flag) for flag in flags), expected)
                    service = GameplayBridgeService(driver)
                    self.assertIs(service.driver, driver)
                    configured.append(service)
                    return service

                def capture_run(server, **kwargs):
                    self.assertEqual(kwargs, {"transport": "stdio"})
                    self.assertIsInstance(server, MCPServer)
                    runs.append(server)

                with patch.object(mcp_server, "load_driver", side_effect=load_fixture), \
                        patch.object(mcp_server, "GameplayBridgeService", side_effect=configure_service), \
                        patch.object(MCPServer, "run", new=capture_run):
                    self.assertEqual(mcp_server.main([
                        "--driver", "native-headless", "--transport", "stdio",
                        "--state-dir", str(state_dir), *options]), 0)
        self.assertEqual((len(loaded), len(configured), len(runs)), (4, 4, 4))
