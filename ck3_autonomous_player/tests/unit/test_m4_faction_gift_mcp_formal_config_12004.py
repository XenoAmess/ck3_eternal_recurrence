"""One new public-MCP configuration proof; no gift lifecycle replay or game I/O."""

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
        raise AssertionError("MCP configuration must not send any game operation")

    def close(self):
        self.closes += 1


class McpFactionGiftFormalConfig12004Test(unittest.TestCase):
    def test_public_argv_reaches_native_constructor_and_normal_service(self):
        from mcp.server import MCPServer

        scenes = (
            ("default", [], False, None, False, False),
            ("query", ["--private-faction-gift-query"], False, None, True, False),
            ("action", ["--private-faction-gift-action"], False, None, True, True),
            ("formal", ["--allow-private-faction-gift-formal-trial",
                        "--private-faction-round-id", "R94"], True, "R94", False, False),
            ("combined", ["--allow-private-faction-gift-formal-trial",
                          "--private-faction-round-id", "R94",
                          "--private-faction-gift-action"], True, "R94", True, True),
            ("unused_round", ["--private-faction-round-id", "R94"],
             False, None, False, False),
        )
        configured, runs = [], []
        for name, options, formal, round_id, query, action in scenes:
            with self.subTest(scene=name), tempfile.TemporaryDirectory() as tmp:
                endpoint = _NoGameEndpoint()

                def configure_service(driver):
                    # main -> real load_driver -> real native constructor must
                    # establish the formal flag and its constructor-validated round.
                    self.assertIsInstance(driver, native_driver.NativeHeadlessGameplayDriver)
                    self.assertEqual(driver.allow_private_faction_gift_formal_trial, formal)
                    self.assertEqual(driver.private_faction_round_id, round_id)
                    self.assertEqual(getattr(driver, "allow_private_faction_gift_query", False), query)
                    self.assertEqual(getattr(driver, "allow_private_faction_gift_action", False), action)
                    self.assertIs(driver.nonwar_only, False)
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
                        "--pipe-name", r"\\.\pipe\xar_ck3_m4_gift_config_fixture",
                        *options,
                    ]), 0)
                self.assertEqual((endpoint.starts, endpoint.closes), (1, 1))
        self.assertEqual((len(configured), len(runs)), (6, 6))

        # Reuse the production constructor's existing round validation, rather
        # than introducing another parser policy or a cached configured driver.
        for options in (
            ["--allow-private-faction-gift-formal-trial"],
            ["--allow-private-faction-gift-formal-trial",
             "--private-faction-round-id", "94"],
        ):
            with self.subTest(rejected_options=options), tempfile.TemporaryDirectory() as tmp:
                with patch.object(native_driver, "NativeNamedPipeServer") as endpoint_factory, \
                        patch.object(mcp_server, "create_server") as server_factory:
                    with self.assertRaisesRegex(ValueError, r"monotonic R<number> round ID"):
                        mcp_server.main([
                            "--driver", "native-headless", "--transport", "stdio",
                            "--state-dir", tmp,
                            "--pipe-name", r"\\.\pipe\xar_ck3_m4_gift_config_fixture",
                            *options,
                        ])
                    endpoint_factory.assert_not_called()
                    server_factory.assert_not_called()
