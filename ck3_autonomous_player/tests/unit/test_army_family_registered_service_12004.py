"""One compiled whole Army-family consumer; the parent owns FIRST execution."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


_CONFIG: dict[str, Path] = {}
_SCENES = ("zero", "negative", "positive", "unavailable")
_EXPECTED_DAYS = (0, -1, 34, None)
_STEP = "query-army-strengths-v1"
_ARMY_ID = 16777217
_NATIVE_ARMY_ID = 33554433
_REGIMENT_IDS = [50331649, 50331649]
_NATIVE_BODY_KEYS = {"step", "accepted", "status", "query_sequence", "army_strengths"}
_DRIVER_BODY_KEYS = _NATIVE_BODY_KEYS | {
    "backend_id", "queried_snapshot_id", "queried_revision", "queried_native_revision",
}


class _WholeNativeEndpoint:
    """Only correlate the compiled outer response with a synthetic transport nonce."""

    pipe_name = r"\\.\pipe\xar-army-family-12004-fixture"

    def __init__(self, compiled_frame: dict[str, object]) -> None:
        self.compiled_frame = deepcopy(compiled_frame)
        self.requests: list[dict[str, object]] = []
        self.on_frame = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def send(self, request: dict[str, object]) -> None:
        if (request.get("type") != "execute_step" or request.get("step") != _STEP
                or request.get("expected_revision") != 7):
            raise AssertionError("unexpected fixture transport request")
        self.requests.append(deepcopy(request))
        frame = deepcopy(self.compiled_frame)
        frame["request_id"] = request["request_id"]
        if self.on_frame is None:
            raise AssertionError("fixture endpoint was not started")
        self.on_frame(frame)

    def close(self) -> None:
        pass


class ArmyFamilyRegisteredService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_mapperclosed_army_family_through_service_and_registered_mcp(self) -> None:
        if not _CONFIG:
            raise RuntimeError("use --source-root, --wire and --output-dir for this consumer")

        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import normalize_army_strengths

        wire_path = _CONFIG["wire"]
        output_dir = _CONFIG["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "army-family-12004-consumer.json"
        report = {
            "result": "RUNNING",
            "consumer": type(self).__name__,
            "compiled_whole_wire": str(wire_path),
            "scene_order": list(_SCENES),
            "synthetic_enclosing_frame": {
                "revision": 42, "native_revision": 7, "date_raw": 10000,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            },
            "native_body_changed": False,
            "live_queries": 0,
            "samples": [],
        }

        def persist() -> None:
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        persist()
        try:
            bundle = json.loads(wire_path.read_text(encoding="utf-8"))
            self.assertEqual(set(bundle), {"schema_version", "scene_order", "samples"})
            self.assertEqual(bundle["schema_version"], 1)
            self.assertEqual(bundle["scene_order"], list(_SCENES))
            self.assertEqual(set(bundle["samples"]), set(_SCENES))
            for index, (name, expected_days) in enumerate(zip(_SCENES, _EXPECTED_DAYS), 1):
                report["active_scene"] = name
                frame = bundle["samples"][name]
                self.assertEqual(
                    set(frame), {"type", "protocol_version", "request_id", "ok", "result"}
                )
                self.assertEqual(frame["type"], "command_result")
                self.assertEqual(frame["protocol_version"], 1)
                self.assertEqual(frame["request_id"], f"army-family-{name}")
                self.assertIs(frame["ok"], True)
                native_body = frame["result"]
                self.assertEqual(set(native_body), _NATIVE_BODY_KEYS)
                self.assertEqual(native_body["step"], _STEP)
                self.assertIs(native_body["accepted"], True)
                self.assertEqual(native_body["status"], "available")
                self.assertEqual(native_body["query_sequence"], index)
                self.assertEqual(len(native_body["army_strengths"]), 1)
                native_row = native_body["army_strengths"][0]
                self.assertEqual(native_row["army_id"], _ARMY_ID)
                self.assertEqual(native_row["native_carmy_id"], _NATIVE_ARMY_ID)
                self.assertEqual(native_row["scope_role"], "player")
                self.assertEqual(native_row["war_ids"], [])
                self.assertEqual(native_row["regiment_count"], 2)
                self.assertEqual(
                    [row["army_regiment_id"] for row in native_row["regiment_strengths"]],
                    _REGIMENT_IDS,
                )
                leaf = native_row["current_disembark_penalty_v1"]
                self.assertEqual(
                    set(leaf),
                    {"schema_version", "source", "status", "remaining_days", "unavailable_reason"},
                )
                self.assertEqual(leaf["schema_version"], 1)
                self.assertEqual(leaf["source"], "native_current_disembark_penalty_days_12003")
                self.assertEqual(leaf["remaining_days"], expected_days)
                self.assertEqual(
                    leaf["status"], "unavailable" if expected_days is None else "available"
                )
                self.assertEqual(
                    leaf["unavailable_reason"],
                    "disembark_getter_not_bound" if expected_days is None else None,
                )

                snapshot = {
                    "snapshot_id": f"synthetic-army-family-{name}",
                    "revision": 42,
                    "native_revision": 7,
                    "date_raw": 10000,
                    "paused": True,
                    "map_ready": True,
                    "backend_id": "native-headless",
                    "played_character": {"character_id": 29829},
                    "player_armies": [{"army_id": _ARMY_ID, "controllable": True}],
                    "active_wars": [],
                    "diagnostics": {
                        "connection_generation": 1,
                        "hello": {
                            "expected_ck3_version": CK3_12004.game_version,
                            "expected_ck3_sha256": CK3_12004.executable_sha256,
                            "game_version": CK3_12004.game_version,
                            "executable_sha256": CK3_12004.executable_sha256,
                        },
                    },
                }
                capabilities = {
                    "backend_id": "native-headless",
                    "snapshot": True,
                    "action_steps": [_STEP],
                    "bridge_capabilities": [
                        "game.state.snapshot", "game.command.query-army-strengths-v1",
                    ],
                    "diagnostics": deepcopy(snapshot["diagnostics"]),
                }
                expected_rows = normalize_army_strengths(
                    deepcopy(native_body["army_strengths"]),
                    expected_scope=[{
                        "army_id": _ARMY_ID, "scope_role": "player", "war_ids": [],
                    }],
                )
                route_receipts = []
                for route in ("ck3_execute_step", "ck3_query_army_strengths"):
                    endpoint = _WholeNativeEndpoint(frame)
                    driver = NativeHeadlessGameplayDriver(
                        endpoint=endpoint, episode_projection="native_campaign"
                    )
                    try:
                        with (
                            patch.object(driver, "take_snapshot", side_effect=lambda: deepcopy(snapshot)),
                            patch.object(driver, "capabilities", return_value=deepcopy(capabilities)),
                        ):
                            server = create_server(driver)
                            arguments = (
                                {"step": _STEP, "expected_revision": 42}
                                if route == "ck3_execute_step"
                                else {"army_ids": [_ARMY_ID], "expected_revision": 42}
                            )
                            result = await server.call_tool(route, arguments)
                        self.assertIs(result.is_error, False)
                        structured = result.structured_content
                        self.assertIsInstance(structured, dict)
                        self.assertEqual(len(endpoint.requests), 1)
                        self.assertEqual(endpoint.requests[0]["expected_revision"], 7)
                        self.assertEqual(structured["query_sequence"], index)
                        self.assertEqual(structured["status"], "available")
                        self.assertEqual(structured["backend_id"], "native-headless")
                        self.assertEqual(structured["queried_snapshot_id"], snapshot["snapshot_id"])
                        self.assertEqual(structured["queried_revision"], 42)
                        self.assertEqual(structured["queried_native_revision"], 7)
                        rows = structured["army_strengths"]
                        self.assertEqual(len(rows), 1)
                        if route == "ck3_execute_step":
                            self.assertEqual(set(structured), _DRIVER_BODY_KEYS)
                            self.assertEqual(rows, expected_rows)
                            self.assertNotIn("source", structured)
                            self.assertNotIn("army_ids", structured)
                        else:
                            for key, value in expected_rows[0].items():
                                self.assertEqual(rows[0][key], value, key)
                            self.assertEqual(structured["army_ids"], [_ARMY_ID])
                            self.assertEqual(structured["scope_army_ids"], [_ARMY_ID])
                            self.assertEqual(structured["source"]["game_version"], CK3_12004.game_version)
                            self.assertEqual(
                                structured["source"]["executable_sha256"], CK3_12004.executable_sha256
                            )
                            projection = structured["current_disembark_penalty_v1"][0]["projection"]
                            self.assertEqual(projection["remaining_days"], expected_days)
                            self.assertIs(
                                projection["current_disembark_days_ready"], expected_days is not None
                            )
                            self.assertIs(projection["future_route_landing_days_ready"], False)
                            self.assertEqual(
                                projection["observed_current_disembark_penalty"], leaf
                            )
                            self.assertEqual(
                                projection["source_provenance"]["game_version"], CK3_12004.game_version
                            )
                            self.assertEqual(
                                projection["source_provenance"]["native_revision"], 7
                            )
                        self.assertEqual(rows[0]["current_disembark_penalty_v1"], leaf)
                        self.assertEqual(
                            [row["army_regiment_id"] for row in rows[0]["regiment_strengths"]],
                            _REGIMENT_IDS,
                        )
                        self.assertEqual(driver._army_strength_query["army_strengths"], expected_rows)
                        self.assertEqual(driver._army_strength_query["query_sequence"], index)
                        self.assertEqual(driver._army_strength_query["cache_binding"]["native_revision"], 7)
                        self.assertEqual(len(result.content), 1)
                        summary = json.loads(result.content[0].text)
                        self.assertEqual(summary["army_ids"], [_ARMY_ID])
                        self.assertEqual(summary["source"], {"revision": 42, "native_revision": 7})
                        self.assertEqual(summary["result_location"], "structuredContent")
                        wire_roundtrip = json.loads(result.model_dump_json(by_alias=True))
                        self.assertEqual(wire_roundtrip["structuredContent"], structured)
                        self.assertEqual(
                            endpoint.compiled_frame["result"], native_body
                        )
                        route_receipts.append({
                            "registered_tool": route,
                            "transport_requests": len(endpoint.requests),
                            "backend_id_added_by_actual_primitive": structured["backend_id"],
                            "queried_revision": structured["queried_revision"],
                            "queried_native_revision": structured["queried_native_revision"],
                            "complete_structured_roundtrip": True,
                            "compact_text_bytes": len(result.content[0].text.encode("utf-8")),
                        })
                    finally:
                        endpoint.close()
                report["samples"].append({
                    "scene": name,
                    "query_sequence": index,
                    "army_id": _ARMY_ID,
                    "native_carmy_id": _NATIVE_ARMY_ID,
                    "regiment_ids": list(_REGIMENT_IDS),
                    "remaining_days": expected_days,
                    "native_leaf_status": leaf["status"],
                    "routes": route_receipts,
                })
                persist()
            report["result"] = "GREEN"
            persist()
        except BaseException as error:
            report["result"] = "RED"
            report["failure"] = f"{type(error).__name__}: {error}"
            persist()
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    _CONFIG.update({
        "source_root": arguments.source_root.resolve(),
        "wire": arguments.wire.resolve(),
        "output_dir": arguments.output_dir.resolve(),
    })
    sys.path.insert(0, str(_CONFIG["source_root"]))
    suite = unittest.TestLoader().loadTestsFromTestCase(ArmyFamilyRegisteredService12004Tests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "result": "GREEN" if outcome.wasSuccessful() else "RED",
        "tests_run": outcome.testsRun,
        "report": str(_CONFIG["output_dir"] / "army-family-12004-consumer.json"),
    }, separators=(",", ":")))
    return 0 if outcome.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
