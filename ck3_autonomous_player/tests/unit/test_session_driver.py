from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.session_driver import DevelopmentSessionDriver  # noqa: E402
from xar_autoplayer.bridge.mcp_server import load_driver  # noqa: E402


def make_session_fixture(root: Path) -> tuple[Path, Path, Path]:
    run = root / "runs" / "20260823T000000Z-dev-session-fixture"
    inbox = run / "bridge" / "inbox"
    outbox = run / "bridge" / "outbox"
    inbox.mkdir(parents=True)
    outbox.mkdir(parents=True)
    report_path = run / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": run.name,
                "process": {"pid": 123},
                "finalized": False,
                "commands": [
                    {
                        "index": 1,
                        "command": "save-checkpoint",
                        "ok": True,
                        "result": {"final_screen": "map_hud"},
                    }
                ],
                "bridge": {
                    "protocol_version": 1,
                    "bridge_dir": str(run / "bridge"),
                    "inbox_dir": str(inbox),
                    "outbox_dir": str(outbox),
                    "supported_commands": [
                        "auto-turn",
                        "life-advance",
                        "status",
                        "stop",
                    ],
                    "action_steps": ["auto-turn", "life-advance"],
                },
            }
        ),
        encoding="utf-8",
    )
    return report_path, inbox, outbox


class DevelopmentSessionDriverTests(unittest.TestCase):
    def test_mcp_loader_exposes_vision_session_driver(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(
                "os.environ", {"XAR_AUTOPLAYER_STATE_DIR": temporary}
            ):
                driver = load_driver("vision-session")
            self.assertIsInstance(driver, DevelopmentSessionDriver)
            self.assertEqual(driver.state_dir, Path(temporary))

    def test_dispatches_step_and_reads_main_thread_response(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            report_path, inbox, outbox = make_session_fixture(state)
            observed: list[dict[str, object]] = []

            def publish_response(_seconds: float) -> None:
                requests = list(inbox.glob("*.json"))
                if not requests or observed:
                    return
                request = json.loads(requests[0].read_text(encoding="utf-8"))
                observed.append(request)
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report["commands"].append(
                    {
                        "index": 2,
                        "command": request["step"],
                        "source": "bridge",
                        "request_id": request["request_id"],
                        "ok": True,
                        "result": {"final_screen": "map_running", "days_advanced": 7},
                    }
                )
                report_path.write_text(json.dumps(report), encoding="utf-8")
                (outbox / requests[0].name).write_text(
                    json.dumps(
                        {
                            "protocol_version": 1,
                            "request_id": request["request_id"],
                            "ok": True,
                            "result": {
                                "final_screen": "map_running",
                                "days_advanced": 7,
                            },
                            "error": None,
                        }
                    ),
                    encoding="utf-8",
                )

            driver = DevelopmentSessionDriver(
                state,
                request_timeout_seconds=0.5,
                poll_interval_seconds=0.001,
                request_id_factory=lambda: "mcp-fixture-0001",
                sleep=publish_response,
            )

            capabilities = driver.capabilities()
            self.assertEqual(capabilities["backend_id"], "vision-session")
            self.assertEqual(
                capabilities["action_steps"], ["auto-turn", "life-advance"]
            )
            result = driver.execute_step("life-advance", expected_revision=1)

            self.assertEqual(
                observed,
                [
                    {
                        "protocol_version": 1,
                        "request_id": "mcp-fixture-0001",
                        "command": "step",
                        "step": "life-advance",
                        "expected_revision": 1,
                    }
                ],
            )
            self.assertEqual(result["backend_id"], "vision-session")
            self.assertEqual(result["days_advanced"], 7)
            snapshot = driver.take_snapshot()
            self.assertEqual(snapshot["revision"], 2)
            self.assertEqual(snapshot["phase"], "map_running")
            self.assertEqual(snapshot["backend_id"], "vision-session")

    def test_expected_revision_mismatch_does_not_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            _report, inbox, _outbox = make_session_fixture(state)
            driver = DevelopmentSessionDriver(
                state,
                request_timeout_seconds=0.02,
                poll_interval_seconds=0.001,
            )

            with self.assertRaisesRegex(
                BridgeUnavailableError, "expected 99, current 1"
            ):
                driver.execute_step("auto-turn", expected_revision=99)
            self.assertEqual(list(inbox.glob("*.json")), [])

    def test_rejects_step_absent_from_persisted_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            _report, inbox, _outbox = make_session_fixture(state)
            driver = DevelopmentSessionDriver(state)

            with self.assertRaisesRegex(UnsupportedStepError, "war-status"):
                driver.execute_step("war-status", expected_revision=1)
            self.assertEqual(list(inbox.glob("*.json")), [])

    def test_surfaces_session_command_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            _report, inbox, outbox = make_session_fixture(state)

            def publish_error(_seconds: float) -> None:
                requests = list(inbox.glob("*.json"))
                if not requests or (outbox / requests[0].name).exists():
                    return
                request = json.loads(requests[0].read_text(encoding="utf-8"))
                (outbox / requests[0].name).write_text(
                    json.dumps(
                        {
                            "request_id": request["request_id"],
                            "ok": False,
                            "result": None,
                            "error": "visible UI timeout",
                        }
                    ),
                    encoding="utf-8",
                )

            driver = DevelopmentSessionDriver(
                state,
                request_timeout_seconds=0.5,
                poll_interval_seconds=0.001,
                request_id_factory=lambda: "mcp-fixture-error",
                sleep=publish_error,
            )

            with self.assertRaisesRegex(
                BridgeUnavailableError, "visible UI timeout"
            ):
                driver.execute_step("auto-turn", expected_revision=1)


if __name__ == "__main__":
    unittest.main()
