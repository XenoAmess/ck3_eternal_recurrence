"""Formal MCP route-speed configuration through the real Native constructor."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import mcp_server, native_driver
from xar_autoplayer.bridge.service import GameplayBridgeService


class _NoNativeEndpoint:
    def __init__(self):
        self.starts = 0
        self.closes = 0

    def start(self, on_message, on_disconnect):
        self.starts += 1

    def send(self, *args, **kwargs):
        raise AssertionError("Configuration must not send a Native operation")

    def close(self):
        self.closes += 1


class McpRouteContactSpeedConfig(unittest.TestCase):
    def test_parser_defaults_and_bounded_explicit_values(self):
        args = mcp_server.parser().parse_args([])
        self.assertEqual(args.route_contact_speed, 3)
        self.assertIs(args.allow_route_contact_high_speed_ab, False)
        for speed in (4, 5):
            with self.subTest(speed=speed):
                args = mcp_server.parser().parse_args([
                    "--driver", "native-headless", "--route-contact-speed", str(speed),
                    "--allow-route-contact-high-speed-ab",
                ])
                self.assertEqual(args.route_contact_speed, speed)
                self.assertIs(args.allow_route_contact_high_speed_ab, True)
        for value in ("0", "6"):
            with self.subTest(invalid=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    mcp_server.parser().parse_args(["--route-contact-speed", value])
                self.assertEqual(error.exception.code, 2)

    def test_main_factory_constructor_and_service_keep_exact_options(self):
        from mcp.server import MCPServer

        scenes = (([], 3, False),
                  (["--route-contact-speed", "4", "--allow-route-contact-high-speed-ab"], 4, True),
                  (["--route-contact-speed", "5", "--allow-route-contact-high-speed-ab"], 5, True))
        for options, speed, ab in scenes:
            with self.subTest(speed=speed), tempfile.TemporaryDirectory() as temp:
                endpoint = _NoNativeEndpoint()
                services, runs = [], []

                def configure_service(driver):
                    self.assertIsInstance(driver, native_driver.NativeHeadlessGameplayDriver)
                    self.assertEqual(driver.state_dir, Path(temp))
                    self.assertEqual(driver.route_contact_timeline_speed, speed)
                    self.assertEqual(driver.route_contact_effective_timeline_speed, speed)
                    self.assertIs(driver.allow_route_contact_high_speed_ab, ab)
                    service = GameplayBridgeService(driver)
                    self.assertIs(service.driver, driver)
                    services.append(service)
                    return service

                def run_server(server, **kwargs):
                    self.assertIsInstance(server, MCPServer)
                    self.assertEqual(kwargs, {"transport": "stdio"})
                    runs.append(server)

                with patch.object(native_driver, "NativeNamedPipeServer", return_value=endpoint), \
                        patch.object(mcp_server, "GameplayBridgeService", side_effect=configure_service), \
                        patch.object(MCPServer, "run", new=run_server):
                    self.assertEqual(mcp_server.main([
                        "--driver", "native-headless", "--transport", "stdio",
                        "--state-dir", temp, *options,
                    ]), 0)
                self.assertEqual((len(services), len(runs)), (1, 1))
                self.assertEqual((endpoint.starts, endpoint.closes), (1, 1))

    def test_non_native_nondefault_options_reject_before_server(self):
        for options in (["--route-contact-speed", "4"],
                        ["--route-contact-speed", "1"],
                        ["--allow-route-contact-high-speed-ab"]):
            with self.subTest(options=options), \
                    patch.object(mcp_server, "DevelopmentReportDriver") as report, \
                    patch.object(native_driver, "NativeNamedPipeServer") as endpoint, \
                    patch.object(mcp_server, "create_server") as server:
                with self.assertRaisesRegex(ValueError, "native-headless"):
                    mcp_server.main(["--driver", "vision-report", *options])
                report.assert_not_called()
                endpoint.assert_not_called()
                server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
