"""AUTHORED_NOTRUN: one registered consumer of new native TurnTick full wires.

Root emits six new production-serializer query replies and one legacy reply
from the same readback. This selected method consumes all seven through the
existing registered law query. It does not construct or repair native rows,
replay old qualification cases, infer a calendar deadline or dispatch actions.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


TOOL = "ck3_query_realm_law_final_terms_private_v1"
STEP = "query-realm-law-final-terms-v1-private"
RAW_FIELD = "crown_authority_cooldown"
TURN_TICK_FIELD = "crown_authority_cooldown_turn_tick"
TURN_TICK_SOURCE = "native_variable_manager_turn_tick_context"
RECEIPT_SCHEMA = (
    "xar.ck3.crown-authority-cooldown-turn-tick-context-native-whole-fixture12004/v1"
)
FILES = (
    "late-exact-context-match.json",
    "complete-known-not-member.json",
    "legitimate-empty-manager.json",
    "member-zero-scalars.json",
    "member-untimed-tail.json",
    "bucket-read-unavailable.json",
    "legacy-leaf-absent.json",
)
EXPECTED_INPUTS = (
    (2, True, True, True),
    (0, False, True, False),
    (0, False, False, False),
    (1, True, False, False),
    (1, True, False, False),
    (None, None, None, None),
)
SELECTED_METHOD = "test_turn_tick_context_reaches_registered_realm_law_query"


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


class CrownCooldownTurnTickRegisteredQueryTest(unittest.IsolatedAsyncioTestCase):
    args: argparse.Namespace
    observations: list[dict[str, object]]
    evidence: dict[str, object]

    async def test_turn_tick_context_reaches_registered_realm_law_query(self) -> None:
        if not hasattr(self, "args"):
            self.skipTest("Use Root's standalone FIRST launcher with the new native full wires")
        sys.path.insert(0, str(self.args.source_root / "ck3_autonomous_player" / "src"))
        from xar_autoplayer.bridge.crown_authority_cooldown_clock_12004 import (
            interpret_crown_cooldown_native_clock_12004,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import (
            NativeHeadlessGameplayDriver, NativeProtocolState,
        )
        from xar_autoplayer.bridge.realm_law_paused_private_transport import (
            COOLDOWN_REMAINING_UNIT,
            normalize_crown_authority_cooldown_raw_v1,
            normalize_crown_authority_cooldown_turn_tick_v1,
            query_realm_law_final_terms_private_v1,
        )
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from mcp import Client

        receipt = load_object(self.args.native_wire_dir / "fixture-receipt.json")
        self.evidence["native_receipt"] = deepcopy(receipt)
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["cases"], 6)
        self.assertEqual(receipt["whole_wire_files"], list(FILES))
        self.assertIs(receipt["live"], False)
        self.assertEqual(receipt["old_cases_executed"], 0)
        self.assertEqual(receipt["law_action_calls"], 0)
        frame = receipt["frame"]
        for key in ("public_revision", "native_revision", "date_raw", "actor_character_id"):
            self.assertIs(type(frame[key]), int)
        self.assertGreater(frame["public_revision"], 0)
        self.assertGreater(frame["native_revision"], 0)
        self.assertEqual(frame["actor_character_id"], 29829)
        self.assertIs(frame["paused"], True)
        self.assertIs(frame["map_ready"], True)
        cases = receipt["case_frames"]
        self.assertEqual([case["file"] for case in cases], list(FILES))
        case_by_file = {case["file"]: case for case in cases}
        packets = {
            filename: load_object(self.args.native_wire_dir / filename)
            for filename in FILES
        }
        self.evidence["dispatch_path"] = (
            "real create_server/Service lifecycle -> registered law tool -> actual "
            "NativeHeadless Driver wrapper -> strict private transport -> real ingest/wait"
        )
        self.evidence["production_source_files"] = {
            "registration": inspect.getsourcefile(create_server),
            "service_lifecycle": inspect.getsourcefile(GameplayBridgeService),
            "driver_wrapper": inspect.getsourcefile(
                NativeHeadlessGameplayDriver.query_realm_law_final_terms_private_v1
            ),
            "private_transport": inspect.getsourcefile(query_realm_law_final_terms_private_v1),
            "turn_tick_normalizer": inspect.getsourcefile(
                normalize_crown_authority_cooldown_turn_tick_v1
            ),
            "protocol_state": inspect.getsourcefile(NativeProtocolState),
        }
        test_case = self

        class CompiledWholeLawDriver:
            allow_private_realm_law_paused_query = True
            allow_private_realm_law_action = False
            command_timeout_seconds = 1.0
            query_realm_law_final_terms_private_v1 = (
                NativeHeadlessGameplayDriver.query_realm_law_final_terms_private_v1
            )

            def __init__(self) -> None:
                self.endpoint = self

            def select(self, packet: dict[str, object]) -> None:
                self.packet = packet
                self.sent: list[dict[str, object]] = []
                self.ingested_types: list[str] = []
                self.state = NativeProtocolState("offline-fixture:m7-turn-tick-context-FIRST")
                native = packet["result"]["realm_law_final_terms"]
                # Fixture snapshot metadata binds the actual native full wire;
                # it is not a new native packet and is never sent to ingest.
                self.fixture_snapshot = {
                    "snapshot_id": f"native:{native['snapshot_revision']}",
                    "revision": frame["public_revision"],
                    "native_revision": native["snapshot_revision"],
                    "date_raw": native["date_raw"],
                    "played_character": {
                        "character_id": native["actor_character_id"], "alive": True,
                    },
                    "paused": frame["paused"], "map_ready": frame["map_ready"],
                    "diagnostics": {"hello": {
                        "expected_ck3_version": CK3_12004.game_version,
                        "expected_ck3_sha256": CK3_12004.executable_sha256,
                    }},
                }

            def take_snapshot(self) -> dict[str, object]:
                return deepcopy(self.fixture_snapshot)

            def send(self, request: dict[str, object]) -> None:
                test_case.assertEqual(set(request), {
                    "type", "protocol_version", "request_id", "step", "expected_revision",
                })
                test_case.assertEqual(request["type"], "execute_step")
                test_case.assertEqual(request["protocol_version"], 1)
                test_case.assertEqual(request["step"], STEP)
                test_case.assertEqual(request["request_id"], self.packet["request_id"])
                test_case.assertEqual(request["expected_revision"], frame["native_revision"])
                self.sent.append(deepcopy(request))
                # Ingest the entire emitted packet without repairing any value.
                self.ingested_types.append(self.state.ingest(deepcopy(self.packet)))

        driver = CompiledWholeLawDriver()
        driver.select(packets[FILES[0]])
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIn(TOOL, tools)
            self.assertIs(tools[TOOL].annotations.read_only_hint, True)
            self.assertNotIn("ck3_enact_realm_law_crown_private_v1", tools)
            for ordinal, filename in enumerate(FILES):
                packet = packets[filename]
                unchanged = deepcopy(packet)
                self.assertEqual(packet["type"], "command_result")
                self.assertEqual(packet["protocol_version"], 1)
                self.assertIs(packet["ok"], True)
                self.assertEqual(packet["request_id"], case_by_file[filename]["request_id"])
                envelope = packet["result"]
                self.assertEqual(envelope["step"], STEP)
                self.assertIs(envelope["accepted"], True)
                self.assertEqual(envelope["status"], "available")
                self.assertIs(envelope["read_only"], True)
                native = envelope["realm_law_final_terms"]
                self.assertEqual(native["snapshot_revision"], frame["native_revision"])
                self.assertEqual(native["date_raw"], frame["date_raw"])
                self.assertEqual(native["actor_character_id"], frame["actor_character_id"])
                raw = native[RAW_FIELD]
                self.assertEqual(
                    normalize_crown_authority_cooldown_raw_v1(raw, date_raw=native["date_raw"]),
                    raw,
                )
                self.assertEqual(raw["remaining_unit"], COOLDOWN_REMAINING_UNIT)
                interpreted = interpret_crown_cooldown_native_clock_12004(
                    raw, date_raw=native["date_raw"],
                )
                self.assertIs(interpreted.calendar_deadline_ready, False)
                if raw["present"] is True:
                    self.assertIsNone(raw["retry_date_raw"])
                if ordinal == 6:
                    self.assertNotIn(TURN_TICK_FIELD, native)
                else:
                    sidecar = native[TURN_TICK_FIELD]
                    count, contains, tail, eligible = EXPECTED_INPUTS[ordinal]
                    self.assertEqual(sidecar["source"], TURN_TICK_SOURCE)
                    self.assertIs(sidecar["read_available"], ordinal != 5)
                    self.assertEqual(sidecar["manager_match_count"], count)
                    self.assertIs(sidecar["manager_contains_context"], contains)
                    self.assertIs(sidecar["scalar_tail_allows_tick"], tail)
                    self.assertIs(sidecar["context_tick_eligible"], eligible)
                    if ordinal == 5:
                        self.assertIsInstance(sidecar["unavailable_reason"], str)
                        self.assertTrue(sidecar["unavailable_reason"])
                        self.assertIs(raw["read_available"], True)
                    else:
                        self.assertIsNone(sidecar["unavailable_reason"])
                driver.select(packet)
                before = driver.take_snapshot()
                record = {
                    "file": filename, "native_whole_packet": deepcopy(packet),
                    "source_snapshot": deepcopy(before),
                }
                self.observations.append(record)
                token = packet["request_id"].removeprefix("realm-law-read-")
                with patch(
                    "xar_autoplayer.bridge.realm_law_paused_private_transport.uuid.uuid4",
                    return_value=SimpleNamespace(hex=token),
                ):
                    received = await client.call_tool(TOOL, {
                        "expected_revision": before["revision"],
                    })
                self.assertIs(received.is_error, False, str(received.content))
                actual = received.structured_content
                self.assertIsInstance(actual, dict)
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual[RAW_FIELD], raw)
                self.assertEqual(actual["groups"], native["groups"])
                if ordinal == 6:
                    self.assertNotIn(TURN_TICK_FIELD, actual)
                else:
                    self.assertEqual(actual[TURN_TICK_FIELD], native[TURN_TICK_FIELD])
                self.assertEqual(actual["queried_revision"], frame["public_revision"])
                self.assertEqual(actual["queried_native_revision"], frame["native_revision"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(driver.state._command_results, {})
                self.assertEqual(len(driver.sent), 1)
                self.assertEqual(packet, unchanged)
                record["registered_mcp_output"] = deepcopy(actual)
                record["native_requests"] = deepcopy(driver.sent)
        self.assertEqual(len(self.observations), 7)
        self.evidence.update(
            cases=7, native_scenes=6, legacy_leaf_absent_cases=1,
            actual_registered_query=True, actual_production_transport=True,
            original_raw9_preserved=True, native_final_terms_preserved=True,
            match_count_two_preserved=True, unavailable_keeps_original_raw9=True,
            calendar_deadline_ready=False, game_actions=0,
        )


def main() -> int:
    if not __debug__:
        raise RuntimeError("FIRST consumer requires Python without -O")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-fA-F]{40}", args.source_sha) is None:
        parser.error("--source-sha must be Root's complete40-hex source qualification pin")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    observations: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    CrownCooldownTurnTickRegisteredQueryTest.args = args
    CrownCooldownTurnTickRegisteredQueryTest.observations = observations
    CrownCooldownTurnTickRegisteredQueryTest.evidence = evidence
    suite = unittest.TestSuite([CrownCooldownTurnTickRegisteredQueryTest(SELECTED_METHOD)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    successful = result.wasSuccessful() and result.testsRun == 1 and not result.skipped
    report = {
        "status": "GREEN" if successful else "RED",
        "scope": "M7 current TurnTick context offline registered native whole-query FIRST",
        "source_root": str(args.source_root), "source_sha": args.source_sha,
        "source_pin_owner": "Root source qualification; worker does not hash or run Git",
        "native_wire_dir": str(args.native_wire_dir), "whole_wire_files": list(FILES),
        "selected_method": SELECTED_METHOD, "tests_run": result.testsRun,
        "compound_methods": 1, "registered_query_cases_attempted": len(observations),
        "completed_outputs": sum("registered_mcp_output" in row for row in observations),
        "whole_native_packets_constructed": False, "whole_native_packets_repaired": False,
        "whole_native_request_ids_relabelled": False, "old_cases_replayed": 0,
        "pipe_operations": 0, "game_operations": 0, "game_actions": 0,
        "new_exe_bytes": 0, "live": False, "calendar_deadline_ready": False,
        "failures": [trace for _, trace in result.failures],
        "errors": [trace for _, trace in result.errors],
        **evidence,
    }
    for name, value in (("OBSERVED.json", observations), ("RESULT.json", report)):
        with (args.output_dir / name).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
