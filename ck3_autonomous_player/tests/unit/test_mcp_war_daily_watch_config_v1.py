"""Official MCP opt-in wiring, with no Game/pipe operations or speed changes."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge import mcp_server, native_driver
from xar_autoplayer.bridge.service import GameplayBridgeService

FLAG = "--private-war-daily-watch-speed2-trial"


class NoGameEndpoint:
    def __init__(self):
        self.starts = self.closes = 0

    def start(self, on_message, on_disconnect):
        self.starts += 1

    def send(self, *args, **kwargs):
        raise AssertionError("Configuration must send no Native operation")

    def close(self):
        self.closes += 1


class McpWarDailyWatchConfigTests(unittest.TestCase):
    def test_cli_boolean_defaults_off_and_explicit_opt_in(self):
        self.assertIs(mcp_server.parser().parse_args([]).private_war_daily_watch_speed2_trial, False)
        value = mcp_server.parser().parse_args(["--driver", "native-headless", FLAG])
        self.assertIs(value.private_war_daily_watch_speed2_trial, True)
        self.assertEqual(value.route_contact_speed, 3)
        self.assertIs(value.allow_route_contact_high_speed_ab, False)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            mcp_server.parser().parse_args([FLAG, "false"])
        self.assertEqual(error.exception.code, 2)

    def test_load_driver_forwards_exact_bool_and_preserves_all_original_constructor_kwargs(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                gate, lifecycle = object(), {"original": "lifecycle-binding"}
                args = dict(state_dir=Path("fixture-state"), pipe_name=r"\\.\pipe\war-watch-config",
                    route_contact_timeline_speed=3, allow_route_contact_high_speed_ab=False,
                    war31_one_shot_surrender_gate=gate, succession_lifecycle_binding=lifecycle,
                    allow_private_death_succession_modal_continue=True,
                    allow_private_faction_gift_formal_trial=True, private_faction_round_id="R123",
                    allow_private_lifestyle_formal_trial=True,
                    require_initial_lifestyle_focus_before_date_advance=True,
                    allow_war_daily_watch_v1=enabled)
                fake = SimpleNamespace()
                with patch.object(mcp_server, "NativeHeadlessGameplayDriver", return_value=fake) as constructor:
                    self.assertIs(mcp_server.load_driver("native-headless", **args), fake)
                positional, actual = constructor.call_args
                self.assertEqual(positional, (args["pipe_name"],))
                self.assertEqual(actual, {
                    "state_dir": Path("fixture-state"),
                    "save_dir": Path("fixture-state")/"profile"/"save games",
                    "route_contact_timeline_speed": 3, "allow_route_contact_high_speed_ab": False,
                    "allow_war_daily_watch_v1": enabled,
                    "war31_one_shot_surrender_gate": gate, "succession_lifecycle_binding": lifecycle,
                    "allow_private_faction_gift_formal_trial": True, "private_faction_round_id": "R123",
                    "allow_private_lifestyle_formal_trial": True,
                    "allow_private_current_timeline_blocker_query": True,
                    "allow_private_death_succession_modal_continue": True})
                self.assertTrue(fake.require_initial_lifestyle_focus_before_date_advance)
                self.assertEqual(fake.initial_lifestyle_focus_gate_stage, "await_submit")

    def test_load_driver_default_is_false_and_invalid_nonbooleans_reject_before_construction(self):
        with patch.object(mcp_server, "NativeHeadlessGameplayDriver") as constructor:
            mcp_server.load_driver("native-headless", state_dir="fixture-state")
            self.assertIs(constructor.call_args.kwargs["allow_war_daily_watch_v1"], False)
        for value in (None, 0, 1, "true", [], object()):
            with self.subTest(value=value), patch.object(mcp_server, "NativeHeadlessGameplayDriver") as constructor:
                with self.assertRaisesRegex(ValueError, "explicit boolean"):
                    mcp_server.load_driver("native-headless", allow_war_daily_watch_v1=value)
                constructor.assert_not_called()

    def test_non_native_opt_in_rejects_before_dispatch_or_import(self):
        for name in (None, "vision-report", "vision-session", "mod", "hybrid", "hybrid-fallback", "some_module:factory"):
            with self.subTest(factory=name), \
                    patch.object(mcp_server, "DevelopmentReportDriver") as report, \
                    patch.object(mcp_server, "NativeHeadlessGameplayDriver") as constructor, \
                    patch.object(mcp_server.importlib, "import_module") as importer:
                with self.assertRaisesRegex(ValueError, "native-headless"):
                    mcp_server.load_driver(name, allow_war_daily_watch_v1=True)
                report.assert_not_called()
                constructor.assert_not_called()
                importer.assert_not_called()

    def test_main_to_real_driver_preserves_private_flags_and_original_speed_policy(self):
        from mcp.server import MCPServer
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as temp:
                endpoint, configured, runs = NoGameEndpoint(), [], []
                def service(driver):
                    self.assertIs(type(driver), native_driver.NativeHeadlessGameplayDriver)
                    self.assertIs(driver._allow_war_daily_watch_v1, enabled)
                    self.assertEqual(driver.state_dir, Path(temp))
                    self.assertEqual(driver.route_contact_timeline_speed, 3)
                    self.assertEqual(driver.route_contact_effective_timeline_speed, 3)
                    self.assertIs(driver.allow_route_contact_high_speed_ab, False)
                    self.assertTrue(driver.allow_private_lifestyle_formal_trial)
                    self.assertTrue(driver.allow_private_semantic_snapshot_readonly)
                    self.assertTrue(driver.allow_private_prisoner_collection_query)
                    self.assertEqual(driver.initial_lifestyle_focus_gate_stage, "await_submit")
                    configured.append(driver)
                    return GameplayBridgeService(driver)
                def run(server, **kwargs):
                    self.assertEqual(kwargs, {"transport": "stdio"})
                    runs.append(server)
                options = [FLAG] if enabled else []
                with patch.object(native_driver, "NativeNamedPipeServer", return_value=endpoint), \
                        patch.object(mcp_server, "GameplayBridgeService", side_effect=service), \
                        patch.object(MCPServer, "run", new=run):
                    result = mcp_server.main(["--driver", "native-headless", "--transport", "stdio",
                        "--state-dir", temp, "--private-semantic-snapshot-readonly",
                        "--private-prisoner-collection-query", "--allow-private-lifestyle-formal-trial",
                        "--require-initial-lifestyle-focus-before-date-advance", *options])
                self.assertEqual(result, 0)
                self.assertEqual((len(configured), len(runs), endpoint.starts, endpoint.closes), (1, 1, 1, 1))

    def test_main_rejects_non_native_and_non_stdio_before_any_constructor(self):
        for driver, transport in (("vision-report", "stdio"), ("some_module:factory", "stdio"),
                                  ("native-headless", "streamable-http")):
            with self.subTest(driver=driver, transport=transport), \
                    patch.object(mcp_server, "load_driver") as loader, \
                    patch.object(mcp_server, "create_server") as server:
                with self.assertRaisesRegex(ValueError, "native-headless stdio"):
                    mcp_server.main(["--driver", driver, "--transport", transport, FLAG])
                loader.assert_not_called()
                server.assert_not_called()

    def test_trial_does_not_bypass_existing_lifecycle_initial_focus_or_route_speed_guards(self):
        for extra, message in ((["--succession-lifecycle", "ordinary_campaign_succession"],
                                "environment manifest and mode"),
                               (["--require-initial-lifestyle-focus-before-date-advance"],
                                "initial lifestyle focus requires"),
                               (["--route-contact-speed", "5"], "high_speed_ab")):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temp, \
                    patch.object(native_driver, "NativeNamedPipeServer") as endpoint, \
                    patch.object(mcp_server, "create_server") as server:
                with self.assertRaisesRegex(ValueError, message):
                    mcp_server.main(["--driver", "native-headless", "--transport", "stdio",
                                     "--state-dir", temp, FLAG, *extra])
                endpoint.assert_not_called()
                server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
