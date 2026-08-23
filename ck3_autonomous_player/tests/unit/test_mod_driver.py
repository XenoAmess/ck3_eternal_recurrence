from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import HybridGameplayDriver, UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import load_driver
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver


class DataModGameplayDriverTests(unittest.TestCase):
    def test_writes_typed_request_and_parses_incremental_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            userdir = Path(temporary)
            log_path = userdir / "logs" / "debug.log"
            log_path.parent.mkdir(parents=True)
            log_path.write_text("existing log content\n", encoding="utf-8")
            fixture = (
                ROOT / "mod_bridge" / "tests" / "fixtures" / "debug_snapshot.log"
            ).read_text(encoding="utf-8")
            observed_requests: list[str] = []

            def publish_fixture(_seconds: float) -> None:
                inbox = userdir / "run" / "xar_mcp_inbox.txt"
                request = inbox.read_text(encoding="utf-8-sig")
                if "xar_mcp_take_snapshot" not in request or observed_requests:
                    return
                observed_requests.append(request)
                with log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(fixture)

            driver = DataModGameplayDriver(
                userdir,
                request_timeout_seconds=0.5,
                poll_interval_seconds=0.001,
                request_id_factory=lambda: "xar_req_000001",
                sleep=publish_fixture,
            )
            snapshot = driver.take_snapshot()

            self.assertIn(
                "xar_mcp_take_snapshot = { REQUEST_ID = xar_req_000001 }",
                observed_requests[0],
            )
            self.assertEqual(snapshot["backend_id"], "data-mod")
            self.assertEqual(snapshot["player_id"], 4_294_967_297)
            self.assertEqual(snapshot["date"], "15 September, 1067")
            self.assertEqual(snapshot["total_days"], 389_742)
            self.assertEqual(snapshot["revision"], 1)
            inbox_bytes = (userdir / "run" / "xar_mcp_inbox.txt").read_bytes()
            self.assertTrue(inbox_bytes.startswith(b"\xef\xbb\xbf"))
            inbox = inbox_bytes.decode("utf-8-sig")
            self.assertNotIn("xar_mcp_take_snapshot", inbox)
            self.assertEqual([], list((userdir / "run").glob("*.tmp")))

            capabilities = driver.capabilities()
            self.assertTrue(capabilities["snapshot"])
            self.assertTrue(capabilities["wait_for_change"])
            self.assertEqual(capabilities["action_steps"], [])
            with self.assertRaises(UnsupportedStepError):
                driver.execute_step("life-advance")

    def test_ignores_matching_frame_before_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            userdir = Path(temporary)
            log_path = userdir / "logs" / "debug.log"
            log_path.parent.mkdir(parents=True)
            fixture = (
                ROOT / "mod_bridge" / "tests" / "fixtures" / "debug_snapshot.log"
            ).read_text(encoding="utf-8")
            log_path.write_text(fixture, encoding="utf-8")
            driver = DataModGameplayDriver(
                userdir,
                request_timeout_seconds=0.02,
                poll_interval_seconds=0.001,
                request_id_factory=lambda: "xar_req_000001",
            )

            with self.assertRaisesRegex(RuntimeError, "timed out"):
                driver.take_snapshot()
            inbox = (userdir / "run" / "xar_mcp_inbox.txt").read_text(
                encoding="utf-8-sig"
            )
            self.assertNotIn("xar_mcp_take_snapshot", inbox)

    def test_wait_ignores_duplicate_poll_and_returns_changed_game_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            userdir = Path(temporary)
            log_path = userdir / "logs" / "debug.log"
            log_path.parent.mkdir(parents=True)
            log_path.write_text("", encoding="utf-8")
            request_ids = iter(
                ("xar_req_first", "xar_req_duplicate", "xar_req_changed")
            )
            published: set[str] = set()

            def publish_snapshot(_seconds: float) -> None:
                request = (userdir / "run" / "xar_mcp_inbox.txt").read_text(
                    encoding="utf-8-sig"
                )
                if "REQUEST_ID = " not in request:
                    return
                request_id = request.split("REQUEST_ID = ", 1)[1].split()[0]
                if request_id in published:
                    return
                published.add(request_id)
                changed = request_id == "xar_req_changed"
                with log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(
                        "XAR_MCP:BEGIN|schema=1|kind=snapshot|"
                        f"request_id={request_id}\n"
                        "XAR_MCP:STATE|player_id=17|date="
                        f"{'2 January, 1067' if changed else '1 January, 1067'}|"
                        f"total_days={389486 if changed else 389485}\n"
                        "XAR_MCP:ACK|schema=1|"
                        f"request_id={request_id}|command=take_snapshot|status=ok\n"
                        "XAR_MCP:END|schema=1|"
                        f"request_id={request_id}\n"
                    )

            driver = DataModGameplayDriver(
                userdir,
                request_timeout_seconds=0.5,
                poll_interval_seconds=0.001,
                request_id_factory=lambda: next(request_ids),
                sleep=publish_snapshot,
            )
            first = driver.take_snapshot()
            second = driver.wait_for_change(
                int(first["revision"]), timeout_seconds=0.5
            )

            self.assertEqual(first["total_days"], 389_485)
            self.assertEqual(second["total_days"], 389_486)
            self.assertEqual(second["revision"], int(first["revision"]) + 1)
            self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])

    def test_factory_supports_mod_cli_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            explicit = load_driver("mod", userdir=temporary)
            self.assertIsInstance(explicit, DataModGameplayDriver)
            self.assertEqual(explicit.userdir, Path(temporary))

            with patch.dict("os.environ", {"XAR_CK3_USERDIR": temporary}):
                configured = load_driver("mod")
            self.assertIsInstance(configured, DataModGameplayDriver)
            self.assertEqual(configured.userdir, Path(temporary))

    def test_factory_builds_mod_snapshot_plus_vision_action_hybrid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            driver = load_driver(
                "hybrid",
                userdir=root / "ck3-userdir",
                state_dir=root / "agent-state",
            )
            self.assertIsInstance(driver, HybridGameplayDriver)
            self.assertIsInstance(driver.fast, DataModGameplayDriver)
            self.assertEqual(driver.fast.userdir, root / "ck3-userdir")
            self.assertEqual(driver.baseline.state_dir, root / "agent-state")


if __name__ == "__main__":
    unittest.main()
