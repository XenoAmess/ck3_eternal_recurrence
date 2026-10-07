"""Root FIRST consumes new complete descendant wires through registered Service."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.current_first_heir_descendants_v1 import LEAF, SUMMARY
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    STEP, query_current_first_heir_relationship_private_v1,
)
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.current_betrothal_fulfillment_proposal import (
    SUBMIT_STEP, current_betrothal_fulfillment_m5_proposal,
)


class CurrentFirstHeirDescendantsRegisteredServiceTests(unittest.TestCase):
    def test_complete_descendants_reach_registered_query_and_service_as_readonly_evidence(self) -> None:
        """Six newly compiled wires and one absent-leaf copy; no game action.

        Native wire, strict transport, MCP registration and Service are the
        complete production observation path. Fixture snapshots/endpoint and
        unavailable ordinary candidate query supply only its source harness.
        No planner, kernel or process-identity lookup is replaced.
        """
        from mcp import Client

        wire_dir = os.environ.get("XAR_FIRST_HEIR_DESCENDANTS_NATIVE_WIRE_DIR")
        output_path = os.environ.get("XAR_FIRST_HEIR_DESCENDANTS_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native whole-wire directory required")
        scene_names = ("complete-roster", "known-empty", "data-missing",
                       "family-missing", "lineage-missing", "no-betrothal")
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scene_names}
        packets["old-absent"] = deepcopy(packets["complete-roster"])
        packets["old-absent"]["result"].pop(LEAF)
        actor, heir = 0x03000001, 0x03000002
        child5, child6, child7, child8 = (0x03000005, 0x03000006, 0x03000007, 0x03000008)
        raw_ids = [child5, child6, 0xFFFFFFFF, 0x07000005, child7] + [child5] * 12 + [child8]
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-descendants27",
            "episode_character_id": actor,
            "played_character": {"character_id": actor, "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }

        class FixtureDriver(CallbackGameplayDriver):
            allow_private_current_first_heir_relationship_query = True
            allow_private_current_first_heir_betrothal_fulfillment = True
            allow_private_family_marriage_formal_trial = True
            # Use Service's existing opening life-advance opportunity route.
            require_initial_lifestyle_focus_before_date_advance = True

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                def no_action(_step: str, _revision: int | None):
                    raise AssertionError("descendant observer cannot submit or advance")
                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []
                self.legality_reads = 0

            def send(self, request: dict[str, object]) -> None:
                if request.get("step") != STEP or request.get("expected_revision") != 7:
                    raise AssertionError("fixture accepts only the current-heir query")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id: str, timeout_seconds: float):
                if not self.requests or self.requests[-1]["request_id"] != request_id:
                    raise AssertionError("current-heir query correlation changed")
                return deepcopy(self.packet)

            def _execute_campaign_root_context_v1_query(self, *, expected_revision: int):
                if expected_revision != 7:
                    raise AssertionError("public-heir binding crossed the fixture frame")
                return {"status": "available", "query_sequence": 11,
                        "held_title_partition": [{"primary": True,
                                                  "first_heir_character_id": heir}]}

            def query_current_first_heir_relationship_private_v1(self, **kwargs):
                relation = query_current_first_heir_relationship_private_v1(self, **kwargs)
                self.relationships.append(deepcopy(relation))
                return relation

            def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision: int):
                if expected_native_revision != 7:
                    raise AssertionError("ordinary family query crossed the fixture frame")
                self.legality_reads += 1
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-descendants27-service-") as directory:
                for name, packet in packets.items():
                    with self.subTest(scene=name):
                        self.assertEqual(packet["type"], "command_result")
                        self.assertIs(packet["ok"], True)
                        wire = packet["result"]
                        self.assertEqual(wire["step"], STEP)
                        self.assertEqual(wire["native_revision"], 7)
                        self.assertEqual(wire["heir_character_id"], heir)
                        driver = FixtureDriver(packet, Path(directory) / name)
                        async with Client(create_server(driver)) as client:
                            tools = {tool.name for tool in (await client.list_tools()).tools}
                            self.assertIn("ck3_plan_turn", tools)
                            query_name = "ck3_query_current_first_heir_relationship_private_v1"
                            self.assertIn(query_name, tools)
                            queried = await client.call_tool(query_name, {"expected_native_revision": 7})
                            self.assertFalse(queried.is_error)
                            observed = queried.structured_content
                            planned = await client.call_tool("ck3_plan_turn", {})
                            self.assertFalse(planned.is_error)
                            service_result = planned.structured_content
                        self.assertIsInstance(observed, dict)
                        self.assertIsInstance(service_result, dict)
                        self.assertEqual(observed["exact_ck3_build"], CK3_12004.game_version)
                        self.assertEqual(observed["exe_sha256"], CK3_12004.executable_sha256)
                        self.assertGreaterEqual(len(driver.relationships), 2)
                        for relation in driver.relationships:
                            self.assertEqual(relation, observed)
                        for request in driver.requests:
                            self.assertNotIn("heir_character_id", request)
                            self.assertNotIn("candidate_character_id", request)
                        plan = service_result["plan"]
                        if name == "old-absent":
                            self.assertNotIn(LEAF, observed)
                            self.assertNotIn(SUMMARY, observed)
                        else:
                            leaf, summary = observed[LEAF], observed[SUMMARY]
                            self.assertEqual(leaf, wire[LEAF])
                            self.assertEqual(summary["source"], "derived_native_descendant_roster")
                            self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                                leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                            if name in {"complete-roster", "lineage-missing", "no-betrothal"}:
                                self.assertEqual(leaf["status"], "available")
                                self.assertIs(leaf["roster_complete"], True)
                                self.assertEqual(leaf["native_child_count_raw"], 18)
                                rows = leaf["rows"]
                                self.assertEqual([row["raw_character_id"] for row in rows], raw_ids)
                                self.assertEqual([row["occurrence_index"] for row in rows], list(range(18)))
                                self.assertEqual([row["generation_valid"] for row in rows],
                                                 [True, True, False, False, True] + [True] * 13)
                                self.assertIs(rows[1]["alive"], False)
                                self.assertIs(rows[1]["child_of_heir"], True)
                                self.assertIs(rows[4]["child_of_heir"], False)
                                self.assertIs(rows[17]["alive"], True)
                                self.assertIs(rows[17]["child_of_heir"], True)
                                self.assertEqual(summary["known_direct_child_occurrence_count"], 15)
                                self.assertEqual(summary["known_direct_child_character_ids"], [child5, child6, child8])
                                self.assertEqual(summary["known_living_direct_child_occurrence_count"], 14)
                                self.assertEqual(summary["known_living_direct_child_character_ids"], [child5, child8])
                                self.assertIs(summary["actual_direct_child_exists"], True)
                                self.assertIs(summary["living_actual_direct_child_exists"], True)
                                self.assertIs(summary["direct_child_count_complete"], False)
                                self.assertIs(summary["living_direct_child_count_complete"], False)
                                if name != "lineage-missing":
                                    self.assertEqual(leaf["heir_lineage"]["dynasty_id_raw"], 200)
                                    self.assertEqual(leaf["played_lineage"]["dynasty_id_raw"], 400)
                                    for key, dynasty, occurrences, ids in (
                                        ("current_heir_dynasty_matches", 200, 13, [child5]),
                                        ("played_dynasty_matches", 400, 1, [child8]),
                                    ):
                                        comparison = summary[key]
                                        self.assertEqual(comparison["status"], "partial")
                                        self.assertEqual(comparison["reference_dynasty_id_raw"], dynasty)
                                        self.assertEqual(comparison["known_living_direct_child_occurrence_count"], occurrences)
                                        self.assertEqual(comparison["known_living_direct_child_character_ids"], ids)
                                        self.assertIs(comparison["living_direct_child_exists"], True)
                                else:
                                    known_lineages = [leaf["played_lineage"], leaf["heir_lineage"]] + [
                                        row["lineage"] for row in rows if row["generation_valid"]]
                                    self.assertTrue(any(lineage["status"] == "unavailable" for lineage in known_lineages))
                                    self.assertNotIn("birth_count", summary)
                            elif name == "known-empty":
                                self.assertEqual(leaf["status"], "available")
                                self.assertIs(leaf["roster_complete"], True)
                                self.assertEqual(leaf["native_child_count_raw"], 0)
                                self.assertEqual(leaf["rows"], [])
                                self.assertEqual(summary["known_direct_child_character_ids"], [])
                                self.assertEqual(summary["known_living_direct_child_occurrence_count"], 0)
                                self.assertIs(summary["actual_direct_child_exists"], False)
                                self.assertIs(summary["living_actual_direct_child_exists"], False)
                                self.assertIs(summary["direct_child_count_complete"], True)
                                for key in ("current_heir_dynasty_matches", "played_dynasty_matches"):
                                    self.assertEqual(summary[key]["status"], "available")
                                    self.assertIs(summary[key]["living_direct_child_exists"], False)
                            else:
                                self.assertEqual(leaf["status"], "partial")
                                self.assertIs(leaf["roster_complete"], False)
                                self.assertEqual(leaf["rows"], [])
                                self.assertIsNone(summary["actual_direct_child_exists"])
                                self.assertIsNone(summary["living_actual_direct_child_exists"])
                                self.assertIs(summary["direct_child_count_complete"], False)
                                if name == "data-missing":
                                    self.assertIs(leaf["family_present"], True)
                                    self.assertEqual(leaf["native_child_count_raw"], 18)
                                    self.assertIs(leaf["data_pointer_present"], False)
                                else:
                                    self.assertIs(leaf["family_present"], False)
                                    self.assertIsNone(leaf["native_child_count_raw"])

                        if wire["betrothed_character_id"] is None:
                            self.assertNotIn("current_betrothal_choice", plan)
                            self.assertEqual(plan["selected_step"], "life-advance")
                            self.assertEqual(driver.legality_reads, 1)
                            if name == "no-betrothal":
                                self.assertEqual(observed["betrothal_actionability"]["status"], "not_applicable")
                                self.assertIs(observed[LEAF]["roster_complete"], True)
                                self.assertIs(observed[SUMMARY]["living_actual_direct_child_exists"], True)
                        else:
                            self.assertEqual(plan["selected_step"], SUBMIT_STEP)
                            self.assertEqual(driver.legality_reads, 0)
                            choice = plan["current_betrothal_choice"]
                            self.assertEqual(choice["status"], "selected")
                            self.assertEqual(choice["reasons"], [])
                            resource = choice["resource_proposal"]
                            for evidence in (choice, resource):
                                self.assertEqual(evidence[LEAF], observed.get(LEAF))
                                self.assertEqual(evidence[SUMMARY], observed.get(SUMMARY))
                            self.assertIn("child_dynasty_result", resource["unpriced"])
                            self.assertIs(resource["resource_reservation_performed"], False)
                            joint = current_betrothal_fulfillment_m5_proposal(
                                frame=resource["source_frame"], plan=plan)
                            self.assertEqual(joint["evidence"]["resource_proposal"][LEAF], observed.get(LEAF))
                            self.assertEqual(joint["evidence"]["resource_proposal"][SUMMARY], observed.get(SUMMARY))
                        records.append({"scene": name,
                            "source_kind": "compiled_native_source_fixture" if name != "old-absent"
                                else "new_native_wire_optional_leaf_removed",
                            "source_wire": str(Path(wire_dir) / (
                                (name if name != "old-absent" else "complete-roster") + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 7)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "new_birth_observed": False, "natural_birth_cause_observed": False,
                "natural_succession_observed": False, "native_action_submitted": False,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
