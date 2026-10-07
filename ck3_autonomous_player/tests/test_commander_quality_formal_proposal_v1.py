"""One query-only proposal compound over four retained genuine native packets.

The R22 helper supplies only its real driver setup and implementation loader.
Its previous test method is never called. This test asks the registered MCP
query for a readonly proposal and never submits a commander assignment.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ARMY_ID = 83886367
NATIVE_ARMY_ID = 50331794
PLAYER_ID = 29829
CURRENT_ID = 30000
PUBLIC_REVISION = 4
NATIVE_REVISION = 11
DATE_RAW = 53288448
QUERY_SEQUENCE = 7
PACKETS = (
    ("quality-current-outside-pool.json", "keep_current", 37, -12),
    ("quality-current-zero.json", "assign_better_candidate", 0, 25),
    ("quality-current-unavailable.json", "current_quality_unavailable", None, None),
    ("quality-candidate-comparison.json", "keep_current", 37, -12),
)
HELPER_RELATIVE = (
    "ck3_autonomous_player/tests/"
    "test_current_commander_native_ai_base_quality_service_12004.py"
)
PROPOSAL_RELATIVE = (
    "ck3_autonomous_player/src/xar_autoplayer/commander_quality_formal_proposal_v1.py"
)
REPORT_NAME = "commander-quality-formal-proposal-service-result.json"
_CONFIG: dict[str, Path | None] | None = None


def _configuration() -> dict[str, Path | None]:
    if _CONFIG is not None:
        return _CONFIG
    native_dir = os.environ.get("XAR_COMMANDER_QUALITY_PROPOSAL_NATIVE_DIR")
    output_dir = os.environ.get("XAR_COMMANDER_QUALITY_PROPOSAL_OUTPUT_DIR")
    return {
        "source_root": Path(os.environ.get(
            "XAR_COMMANDER_QUALITY_PROPOSAL_SOURCE_ROOT",
            str(Path(__file__).resolve().parents[2]),
        )).resolve(),
        "native_dir": Path(native_dir).resolve() if native_dir else None,
        "output_dir": Path(output_dir).resolve() if output_dir else None,
    }


def _persist(output_dir: Path | None, report: dict[str, object]) -> None:
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / REPORT_NAME).write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8",
        )


def _load_fixture_helper(source_root: Path):
    helper_path = (source_root / HELPER_RELATIVE).resolve()
    spec = importlib.util.spec_from_file_location(
        "commander_quality_proposal_retained_fixture_helper", helper_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("retained native whole-packet helper cannot be loaded")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    if Path(helper.__file__).resolve() != helper_path:
        raise RuntimeError("retained helper loaded outside the owned source projection")
    return helper


class CurrentCommanderQualityFormalProposalTests(unittest.TestCase):
    def test_registered_mcp_whole_wire_formal_proposals(self):
        config = _configuration()
        source_root = config["source_root"]
        native_dir = config["native_dir"]
        output_dir = config["output_dir"]
        required = [source_root / HELPER_RELATIVE, source_root / PROPOSAL_RELATIVE]
        missing = [str(path) for path in required if not path.is_file()]
        if native_dir is None:
            missing.append("--native-dir")
        else:
            missing.extend(str(native_dir / filename) for filename, *_ in PACKETS
                           if not (native_dir / filename).is_file())
        if missing:
            _persist(output_dir, {
                "status": "NOTRUN", "missing_inputs": missing,
                "test_method_count": 1, "native_packets_consumed": 0,
                "native_producer_invocations": 0, "old_test_invocations": 0,
                "assignment_executed": False, "live_validation": False,
            })
            print("NOTRUN: owned proposal source/helper and four retained native packets are required")
            self.skipTest("NOTRUN: proposal whole-query inputs unavailable")

        report = {
            "schema": "commander-quality-formal-proposal-service-compound-v1",
            "status": "RED", "test_method_count": 1,
            "native_packet_count": 4, "derived_packet_count": 0,
            "native_producer_invocations": 0, "old_test_invocations": 0,
            "native_body_rows_replaced": False,
            "scope": "existing_mcp_queried_proposal",
            "automatic_consumption": False, "assignment_executed": False,
            "formal_planner_closed": False,
            "fake_boundary": "transport correlation and enclosing hello/paused scope only",
            "driver_methods_patched": False, "production_state_ingest": True,
            "game_touched": False, "live_validation": False, "occurrences": [],
        }
        try:
            helper = _load_fixture_helper(source_root)
            modules = helper._load_implementation(source_root)
            proposal_module = importlib.import_module(
                "xar_autoplayer.commander_quality_formal_proposal_v1",
            )
            expected_module_path = (source_root / PROPOSAL_RELATIVE).resolve()
            self.assertEqual(Path(proposal_module.__file__).resolve(), expected_module_path)
            # Loading proves projection binding; only Service calls the function.
            self.assertTrue(callable(proposal_module.propose_commander_quality_v1))
            self.assertIs(modules["service"].propose_commander_quality_v1,
                          proposal_module.propose_commander_quality_v1)
            report["fixture_helper_path"] = str(Path(helper.__file__).resolve())
            report["loaded_module_paths"] = {
                name: str(Path(module.__file__).resolve()) for name, module in modules.items()
            }
            report["loaded_module_paths"]["commander_quality_formal_proposal_v1"] = str(
                expected_module_path,
            )
            step = modules["army_commander_candidates"].query_army_commander_candidates_v1_step(
                ARMY_ID,
            )

            async def consume():
                for filename, expected_status, current_quality, gain in PACKETS:
                    packet = json.loads((native_dir / filename).read_text(encoding="utf-8-sig"))
                    original = deepcopy(packet)
                    self.assertEqual(packet["type"], "command_result")
                    self.assertEqual(packet["protocol_version"], 1)
                    self.assertIs(packet["ok"], True)
                    envelope = packet["result"]
                    self.assertEqual(envelope["step"], step)
                    self.assertIs(envelope["accepted"], True)
                    self.assertIs(envelope["read_only"], True)
                    self.assertEqual(envelope["snapshot_revision"], NATIVE_REVISION)
                    self.assertEqual(envelope["date_raw"], DATE_RAW)
                    self.assertEqual(envelope["query_sequence"], QUERY_SEQUENCE)
                    self.assertNotIn("commander_quality_proposal", envelope)
                    native_candidates = envelope["army_commander_candidates"]

                    with tempfile.TemporaryDirectory(prefix="quality-proposal-scope-") as temporary:
                        driver = helper._driver_for_packet(modules, packet, Path(temporary))
                        try:
                            scope = driver.take_snapshot()
                            self.assertEqual(scope["revision"], PUBLIC_REVISION)
                            self.assertEqual(scope["native_revision"], NATIVE_REVISION)
                            self.assertEqual(scope["date_raw"], DATE_RAW)
                            self.assertEqual(driver._command_history, [])
                            self.assertTrue(driver.state._raw_state_snapshot_accepted)
                            self.assertTrue(driver.capabilities()["snapshot"])
                            server = modules["mcp_server"].create_server(driver)
                            registered = await server.list_tools()
                            tool = next(row for row in registered
                                        if row.name == "ck3_query_army_commander_candidates_v1")
                            self.assertEqual(set(tool.input_schema["properties"]), {
                                "army_id", "expected_revision", "target_province_id",
                            })
                            self.assertEqual(tool.input_schema["required"], ["army_id"])
                            self.assertTrue(getattr(tool.annotations, "read_only_hint",
                                                   getattr(tool.annotations, "readOnlyHint", False)))
                            response = await server.call_tool(
                                "ck3_query_army_commander_candidates_v1",
                                {"army_id": ARMY_ID, "expected_revision": PUBLIC_REVISION},
                            )
                            self.assertFalse(getattr(response, "is_error",
                                                     getattr(response, "isError", False)))
                            observed = response.structured_content
                            self.assertIsInstance(observed, dict)
                            self.assertEqual(observed["army_commander_candidates"], native_candidates)
                            self.assertEqual(observed["queried_snapshot_id"], scope["snapshot_id"])
                            self.assertEqual(observed["queried_revision"], PUBLIC_REVISION)
                            self.assertEqual(observed["queried_native_revision"], NATIVE_REVISION)
                            self.assertEqual(observed["date_raw"], DATE_RAW)
                            self.assertEqual(observed["query_sequence"], QUERY_SEQUENCE)
                            self.assertEqual(observed["backend_id"], "native-headless")

                            assign = expected_status == "assign_better_candidate"
                            unavailable = expected_status == "current_quality_unavailable"
                            expected_proposal = {
                                "schema": "xar.ck3.commander-quality-proposal.v1",
                                "policy": "native_base_quality_current_baseline_v1",
                                "status": expected_status,
                                "read_only": True,
                                "scope": "existing_mcp_queried_proposal",
                                "automatic_consumption": False,
                                "assignment_executed": False,
                                "source": "native_ai_base_quality",
                                "army_id": ARMY_ID,
                                "native_carmy_id": NATIVE_ARMY_ID,
                                "owner_character_id": PLAYER_ID,
                                "frame": {
                                    "snapshot_id": scope["snapshot_id"],
                                    "revision": PUBLIC_REVISION,
                                    "native_revision": NATIVE_REVISION,
                                    "date_raw": DATE_RAW,
                                    "query_sequence": QUERY_SEQUENCE,
                                },
                                "current_commander_character_id": CURRENT_ID,
                                "current_native_ai_base_quality": current_quality,
                                "best_eligible_candidate_character_id": 30001,
                                "best_eligible_candidate_native_ai_base_quality": 25,
                                "quality_gain": gain,
                                "proposed_commander_character_id": 30001 if assign else None,
                                "selected_step": (
                                    "assign-army-commander-v1-army-83886367-to-character-30001"
                                    if assign else None
                                ),
                                "unavailable_reason": (
                                    "current_native_ai_base_quality_unavailable"
                                    if unavailable else None
                                ),
                            }
                            proposal = observed["commander_quality_proposal"]
                            self.assertEqual(proposal, expected_proposal)
                            self.assertIs(proposal["read_only"], True)
                            self.assertIs(proposal["automatic_consumption"], False)
                            self.assertIs(proposal["assignment_executed"], False)

                            role = native_candidates["current_commander"]
                            quality = role["current_native_ai_base_quality"]
                            pool = native_candidates["candidates"]
                            self.assertEqual(native_candidates["army_id"], ARMY_ID)
                            self.assertEqual(native_candidates["native_carmy_id"], NATIVE_ARMY_ID)
                            self.assertEqual(native_candidates["owner_character_id"], PLAYER_ID)
                            self.assertEqual(role["character_id"], CURRENT_ID)
                            self.assertEqual(quality["source_character_id"], CURRENT_ID)
                            self.assertEqual(quality["value"], current_quality)
                            best = next(row for row in pool if row["character_id"] == 30001)
                            self.assertIs(best["available"], True)
                            self.assertIs(best["can_assign"], True)
                            self.assertIs(best["final_eligibility_observable"], True)
                            self.assertIs(best["quality_observable"], True)
                            self.assertEqual(best["native_ai_base_quality"], 25)
                            if filename == "quality-current-outside-pool.json":
                                self.assertNotIn(CURRENT_ID, [row["character_id"] for row in pool])
                                self.assertEqual(quality["status"], "available")
                                self.assertGreater(current_quality, best["native_ai_base_quality"])
                            elif filename == "quality-current-zero.json":
                                self.assertIs(type(current_quality), int)
                                self.assertEqual(quality["status"], "available")
                                self.assertEqual(proposal["quality_gain"], 25)
                            elif unavailable:
                                self.assertEqual(quality["status"], "unavailable")
                                self.assertEqual(quality["unavailable_reason"],
                                                 "current_commander_identity_unavailable")
                                self.assertIsNone(proposal["current_native_ai_base_quality"])
                                self.assertIsNone(proposal["quality_gain"])
                                self.assertIsNone(proposal["selected_step"])
                            else:
                                self.assertEqual([row["character_id"] for row in pool], [30000, 30001])
                                self.assertIs(pool[0]["can_assign"], False)
                                self.assertEqual(pool[0]["native_ai_base_quality"], 37)
                                self.assertEqual(role["current_total_martial"]["value"], 17)
                                self.assertEqual(pool[0]["generic_advantage_points"], 9)
                                self.assertNotEqual(quality["value"], role["current_total_martial"]["value"])
                                self.assertNotEqual(quality["value"], pool[0]["generic_advantage_points"])
                                self.assertEqual(proposal["status"], "keep_current")

                            # The sole submitted command is the readonly native query.
                            # A returned assignment string is data, not execution.
                            self.assertEqual(len(driver.endpoint.requests), 1)
                            self.assertEqual(driver.endpoint.requests[0]["step"], step)
                            self.assertEqual(driver.endpoint.requests[0]["expected_revision"], NATIVE_REVISION)
                            self.assertEqual(driver.endpoint.responses[0]["result"], original["result"])
                            self.assertEqual(packet, original)
                            self.assertEqual(len(driver._command_history), 1)
                            self.assertEqual(driver._command_history[0]["command"], step)
                            self.assertIs(driver._command_history[0]["ok"], True)
                            report["occurrences"].append({
                                "wire": str(native_dir / filename), "status": "GREEN",
                                "provenance": "retained original genuine native whole command_result",
                                "proposal": proposal,
                                "native_query_commands": 1, "assignment_commands": 0,
                            })
                        finally:
                            driver.endpoint.close()

            asyncio.run(consume())
            self.assertEqual(len(report["occurrences"]), 4)
            report["status"] = "GREEN"
            report["readiness"] = "static-ready; query-only whole fixture consumption"
        except Exception as error:
            report["failure"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            _persist(output_dir, report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    global _CONFIG
    _CONFIG = {
        "source_root": arguments.source_root.resolve(),
        "native_dir": arguments.native_dir.resolve(),
        "output_dir": arguments.output_dir.resolve(),
    }
    suite = unittest.TestSuite([CurrentCommanderQualityFormalProposalTests(
        "test_registered_mcp_whole_wire_formal_proposals",
    )])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
