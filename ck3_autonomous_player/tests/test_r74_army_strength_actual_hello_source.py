"""AUTHORED_NOTRUN: R74 expected-only hello through the registered Army query.

The retained snapshot supplies actual R74 identity metadata. Army strength DTOs
are synthetic and deliberately minimal. The installed MCP SDK, Service, row
normalizer, disembark projection and exact-build checker are production code.
This regression neither loads CK3 nor qualifies a native producer or live action.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
import traceback
import unittest

METHOD = "test_registered_query_preserves_actual_expected_only_hello_source"
CONFIG: argparse.Namespace | None = None
ARMY_ID = 218104048
STEP = "query-army-strengths-v1"


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _snapshot_from_response(document: object) -> dict[str, object]:
    """Unwrap saved MCP envelopes without walking the snapshot history."""
    pending = [document]
    wrappers = ("result", "response", "payload", "snapshot", "structuredContent",
                "structured_content", "native_source_snapshot", "source_snapshot")
    while pending:
        value = pending.pop(0)
        if not isinstance(value, dict):
            continue
        if ("diagnostics" in value and "revision" in value
                and "player_armies" in value):
            return deepcopy(value)
        for key in wrappers:
            if isinstance(value.get(key), dict):
                pending.append(value[key])
        content = value.get("content")
        if isinstance(content, list):
            for block in content:
                if (isinstance(block, dict) and block.get("type") == "text"
                        and isinstance(block.get("text"), str)):
                    try:
                        pending.append(json.loads(block["text"]))
                    except json.JSONDecodeError:
                        pass
    raise ValueError("saved response does not contain the R74 source snapshot")


class _SyntheticReadOnlyArmyDriver:
    """Supply only an offline DTO; no Service or production function overrides."""

    def __init__(self, snapshot: dict[str, object],
                 rows: list[dict[str, object]]) -> None:
        self.snapshot_value = deepcopy(snapshot)
        self.rows = deepcopy(rows)
        self.calls: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot_value)

    def capabilities(self) -> dict[str, object]:
        return {"backend_id": "native-headless", "action_steps": [STEP],
                "bridge_capabilities": ["game.command.query-army-strengths-v1"]}

    def execute_step(self, step: str, *,
                     expected_revision: int | None = None) -> dict[str, object]:
        if step != STEP or expected_revision != self.snapshot_value["revision"]:
            raise AssertionError("fixture supplies one paused R74 read-only Army query")
        self.calls.append({"step": step, "expected_revision": expected_revision})
        return {"step": step, "accepted": True, "status": "available",
                "query_sequence": 1, "army_strengths": deepcopy(self.rows),
                "backend_id": "native-headless"}


class R74ArmyStrengthActualHelloSourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_query_preserves_actual_expected_only_hello_source(self) -> None:
        self.assertIsNotNone(CONFIG, "use the sole-method CLI")
        output = Path(CONFIG.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        report = {
            "schema": "xar.r74-army-strength-actual-hello-source-regression.v1",
            "status": "RED", "sole_method": self._testMethodName,
            "snapshot_response": str(Path(CONFIG.snapshot_response)),
            "actual_mcp_route": "ck3_query_army_strengths",
            "fixture_boundary": "retained actual R74 source metadata; synthetic minimal Army DTO Driver",
            "mocked_service_projection_or_checker": False,
            "native_driver_used": False, "live": False,
            "native_producer_or_live_qualification": False,
            "old_tests_executed": 0,
        }
        started = time.perf_counter()
        try:
            self.assertEqual(sys.flags.optimize, 0, "run without -O")
            source_root = Path(CONFIG.source_root).resolve()
            project = source_root / "ck3_autonomous_player"
            sys.path.insert(0, str(source_root / "tools"))
            sys.path.insert(0, str(project / "src"))
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.army_current_disembark_penalty_contract import (
                project_current_disembark_penalty_v1,
            )
            from xar_autoplayer.bridge.version_identity import CK3_12004, require_exact_native_build
            from xar_autoplayer.bridge.war_contract import army_strength_scope

            for label, entry in (
                ("mcp", create_server), ("service", GameplayBridgeService),
                ("projection", project_current_disembark_penalty_v1),
                ("identity_checker", require_exact_native_build),
            ):
                path = Path(sys.modules[entry.__module__].__file__).resolve()
                self.assertTrue(path.is_relative_to((project / "src").resolve()))
                report[label + "_source"] = str(path)

            document = json.loads(Path(CONFIG.snapshot_response).read_text(encoding="utf-8-sig"))
            snapshot = _snapshot_from_response(document)
            hello = snapshot["diagnostics"]["hello"]
            self.assertNotIn("game_version", hello)
            self.assertNotIn("executable_sha256", hello)
            self.assertEqual(hello["expected_ck3_version"], CK3_12004.game_version)
            self.assertEqual(hello["expected_ck3_sha256"].upper(), CK3_12004.executable_sha256)
            self.assertEqual(snapshot["snapshot_id"], "native:2")
            self.assertEqual(snapshot["revision"], 3)
            self.assertEqual(snapshot["native_revision"], 2)
            self.assertEqual(snapshot["date_raw"], 53288448)
            self.assertIs(snapshot["paused"], True)
            report["retained_frame"] = {
                key: snapshot[key] for key in
                ("snapshot_id", "revision", "native_revision", "date_raw", "paused")
            }
            report["retained_hello"] = deepcopy(hello)
            scope = army_strength_scope(snapshot)
            self.assertIn(ARMY_ID, [row["army_id"] for row in scope])
            raw_leaf = {"schema_version": 1,
                        "source": "native_current_disembark_penalty_days_12003",
                        "status": "available", "remaining_days": 0,
                        "unavailable_reason": None}
            rows = []
            for index, item in enumerate(scope):
                row = {
                    "status": "available", "army_id": item["army_id"],
                    "native_carmy_id": 1000 + index,
                    "scope_role": item["scope_role"], "war_ids": list(item["war_ids"]),
                    "regiment_count": 0, "current_soldiers": 0,
                    "maximum_soldiers": 0, "ai_base_power_raw": 0,
                    "ai_base_power_scale": 100000, "unavailable_reason": None,
                }
                if item["army_id"] == ARMY_ID:
                    row["current_disembark_penalty_v1"] = deepcopy(raw_leaf)
                rows.append(row)
            driver = _SyntheticReadOnlyArmyDriver(snapshot, rows)
            server = create_server(driver, profile_dir=None)
            arguments = {"army_ids": [ARMY_ID], "expected_revision": snapshot["revision"]}
            report["arguments"] = arguments
            response = await server.call_tool("ck3_query_army_strengths", arguments)
            self.assertFalse(response.is_error)
            result = response.structured_content
            self.assertIsInstance(result, dict)
            report["actual_service_result"] = result
            self.assertEqual(driver.calls, [{"step": STEP, "expected_revision": 3}])
            self.assertEqual(result["source"]["game_version"], CK3_12004.game_version)
            self.assertEqual(result["source"]["executable_sha256"], CK3_12004.executable_sha256)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
                self.assertEqual(result["source"][key], snapshot[key])
            self.assertEqual(result["army_ids"], [ARMY_ID])
            self.assertEqual(result["army_strengths"][0]["current_disembark_penalty_v1"], raw_leaf)
            projection = result["current_disembark_penalty_v1"][0]["projection"]
            self.assertEqual(projection["status"], "available")
            self.assertIs(projection["current_disembark_days_ready"], True)
            self.assertEqual(projection["remaining_days"], 0)
            self.assertEqual(projection["observed_current_disembark_penalty"], raw_leaf)
            self.assertEqual(projection["source_provenance"]["game_version"], CK3_12004.game_version)
            self.assertEqual(projection["source_provenance"]["executable_sha256"], CK3_12004.executable_sha256)
            self.assertEqual(driver.snapshot_value, snapshot)
            self.assertEqual(driver.rows, rows)
            self.assertNotIn("game_version", driver.snapshot_value["diagnostics"]["hello"])
            report["driver_calls"] = driver.calls
            report["source_and_projection_exact_pair"] = {
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            }
            report["status"] = "GREEN"
        except BaseException as error:
            report["exception"] = {"type": type(error).__name__, "text": str(error),
                                   "traceback": traceback.format_exc()}
            raise
        finally:
            report["elapsed_seconds"] = time.perf_counter() - started
            _write(output / "r74-army-strength-actual-hello-source-result.json", report)


def main() -> int:
    global CONFIG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--snapshot-response", required=True)
    parser.add_argument("--output-dir", required=True)
    CONFIG = parser.parse_args()
    suite = unittest.TestSuite([R74ArmyStrengthActualHelloSourceTests(METHOD)])
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if outcome.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
