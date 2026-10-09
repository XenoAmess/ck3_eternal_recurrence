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

from xar_autoplayer.bridge.current_first_heir_descendants_v1 import (
    CHILDHOOD_TRAIT_KEYS, CHILD_INPUTS, EDUCATION_POINT_TRAIT_KEYS, LEAF, SUMMARY,
    TYPED_WINDOWS,
)
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
            # Use ordinary family arbitration without the opening-focus opt-in,
            # which intentionally returns before the private relationship route.
            require_initial_lifestyle_focus_before_date_advance = False

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

    def test_current_first_heir_child_inputs_reach_registered_query_and_service(self) -> None:
        """Five compiled child-input wires and legacy absence on the actual query path."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHILD_INPUT_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHILD_INPUT_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native child-input wires required")
        scenes = ("empty-children", "living-child-no-traits", "childhood-affinity",
                  "child-values-unavailable", "child-traits-unavailable")
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scenes}
        packets["legacy-child-inputs-absent"] = deepcopy(packets["childhood-affinity"])
        packets["legacy-child-inputs-absent"]["result"][LEAF].pop(CHILD_INPUTS)
        actor, heir = 0x03000001, 0x03000002
        child5, child8 = 0x03000005, 0x03000008
        affinity_ids = [child5, 0x03000006, 0xFFFFFFFF, 0x07000005, 0x03000007]
        affinity_ids += [child5] * 12 + [child8]
        child5_indices = [0, *range(5, 17)]
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-child-inputs35",
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
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                def no_action(_step: str, _revision: int | None):
                    raise AssertionError("child-input observer cannot submit or advance")
                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []

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
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-child-inputs35-service-") as directory:
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
                        # Raw whole-wire identity has no SHA field. Keep the
                        # production private_native_provenance normalization.
                        self.assertIsNone(wire["betrothed_character_id"])
                        self.assertEqual(wire["primary_spouse_character_id"], 0x03000003)
                        self.assertEqual(wire["spouse_character_ids"], [0x03000003])
                        self.assertEqual(observed["exact_ck3_build"], CK3_12004.game_version)
                        self.assertEqual(observed["exe_sha256"], CK3_12004.executable_sha256)
                        self.assertGreaterEqual(len(driver.relationships), 2)
                        for relation in driver.relationships:
                            self.assertEqual(relation, observed)
                        for request in driver.requests:
                            for key in ("heir_character_id", "child_character_id", "candidate_character_id"):
                                self.assertNotIn(key, request)
                        leaf = observed[LEAF]
                        self.assertEqual(leaf, wire[LEAF])
                        self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                            leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                        self.assertEqual(observed[SUMMARY]["native_roster_status"], leaf["status"])
                        reproductive = "current_first_heir_reproductive_inputs_v1"
                        if reproductive in wire:
                            self.assertEqual(observed[reproductive], wire[reproductive])
                        if name == "legacy-child-inputs-absent":
                            self.assertNotIn(CHILD_INPUTS, leaf)
                            self.assertEqual([row["raw_character_id"] for row in leaf["rows"]], affinity_ids)
                        else:
                            inputs = leaf[CHILD_INPUTS]
                            self.assertEqual(inputs["source"], "native_current_heir_child_inputs")
                            for key in ("native_revision", "played_character_id", "heir_character_id", "date_raw"):
                                self.assertEqual(inputs[key], leaf[key])
                            rows = inputs["rows"]
                            if name == "empty-children":
                                self.assertEqual(leaf["native_child_count_raw"], 0)
                                self.assertEqual(leaf["rows"], [])
                                self.assertEqual(inputs["status"], "available")
                                self.assertEqual(rows, [])
                            else:
                                self.assertEqual(inputs["status"], "partial" if name in {
                                    "child-values-unavailable", "child-traits-unavailable"} else "available")
                                expected_ids = [child5, child8] if name == "childhood-affinity" else [child5]
                                self.assertEqual([row["character_id"] for row in rows], expected_ids)
                                for row in rows:
                                    self.assertEqual(row["values"]["source"], "native_character_age_and_sex")
                                    self.assertEqual(row["childhood_traits"]["source"], "native_character_has_trait")
                                    self.assertEqual(row["childhood_traits"]["queried_trait_keys"], list(CHILDHOOD_TRAIT_KEYS))
                                if name == "childhood-affinity":
                                    self.assertEqual(leaf["native_child_count_raw"], 18)
                                    self.assertEqual([row["raw_character_id"] for row in leaf["rows"]], affinity_ids)
                                    self.assertEqual([row["occurrence_indices"] for row in rows], [child5_indices, [17]])
                                    self.assertEqual([(row["values"]["age_measure_raw"],
                                        row["values"]["sex_selector_raw"]) for row in rows], [(7, 0), (9, 1)])
                                    self.assertEqual([row["childhood_traits"]["present_trait_keys"] for row in rows],
                                        [["curious", "pensive"], ["rowdy", "bossy", "charming"]])
                                else:
                                    self.assertEqual(leaf["native_child_count_raw"], 1)
                                    self.assertEqual(rows[0]["occurrence_indices"], [0])
                                    values, traits = rows[0]["values"], rows[0]["childhood_traits"]
                                    if name == "child-values-unavailable":
                                        self.assertEqual(values["status"], "unavailable")
                                        self.assertIsNone(values["age_measure_raw"])
                                        self.assertIsNone(values["sex_selector_raw"])
                                        self.assertEqual(traits["status"], "available")
                                        self.assertEqual(traits["present_trait_keys"], ["curious"])
                                    else:
                                        self.assertEqual(values["status"], "available")
                                        self.assertEqual((values["age_measure_raw"], values["sex_selector_raw"]), (0, 0))
                                        self.assertEqual(traits["status"], "unavailable" if name == "child-traits-unavailable" else "available")
                                        self.assertEqual(traits["present_trait_keys"], None if name == "child-traits-unavailable" else [])
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        self.assertEqual(plan["family_marriage_status"], "current_first_heir_already_partnered")
                        self.assertEqual(plan["family_marriage_current_relationship"], observed)
                        records.append({"scene": name,
                            "source_kind": "compiled_native_source_fixture" if name != "legacy-child-inputs-absent"
                                else "new_native_wire_optional_child_inputs_removed",
                            "source_wire": str(Path(wire_dir) / (("childhood-affinity"
                                if name == "legacy-child-inputs-absent" else name) + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 6)
        self.assertEqual(len({record["registered_service_result"]["plan"]["selected_step"]
                              for record in records}), 1)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "new_birth_observed": False, "natural_birth_cause_observed": False,
                "child_education_action_submitted": False, "native_action_submitted": False,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


    def test_current_first_heir_child_focus_wholes_reach_registered_query_and_service(self) -> None:
        """Six new native whole wires plus optional-focus legacy compatibility."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHILD_FOCUS_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHILD_FOCUS_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native child-focus wires required")
        scenes = (
            "empty-children-focus", "distinct-child-focus-keys",
            "child-focus-sentinel-absent", "child-focus-null-unavailable",
            "child-focus-key-unavailable", "child-focus-independent-of-values",
        )
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scenes}
        legacy = "legacy-native-focus-absent"
        packets[legacy] = deepcopy(packets["distinct-child-focus-keys"])
        for row in packets[legacy]["result"][LEAF][CHILD_INPUTS]["rows"]:
            row.pop("native_focus")
        actor, heir = 0x03000001, 0x03000002
        child5, child8 = 0x03000005, 0x03000008
        distinct_ids = [child5, 0x03000006, 0xFFFFFFFF, 0x07000005, 0x03000007]
        distinct_ids += [child5] * 12 + [child8]
        child5_indices = [0, *range(5, 17)]
        # Stock source34/stock/SOURCE-TREE.md:79 retains these actual IDs,
        # from00_education_focuses.txt:5 and379. They are fixture inputs only.
        focus_keys = ["education_diplomacy", "education_learning"]
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-child-focus37",
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
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                def no_action(_step: str, _revision: int | None):
                    raise AssertionError("child-focus observer cannot submit or advance")
                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []

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
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-child-focus37-service-") as directory:
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
                        # Normalization supplies build identity; the admitted
                        # raw whole wire contains no SHA field.
                        self.assertEqual(observed["exact_ck3_build"], CK3_12004.game_version)
                        self.assertEqual(observed["exe_sha256"], CK3_12004.executable_sha256)
                        self.assertIsNone(wire["betrothed_character_id"])
                        self.assertEqual(wire["primary_spouse_character_id"], 0x03000003)
                        self.assertEqual(wire["spouse_character_ids"], [0x03000003])
                        self.assertGreaterEqual(len(driver.relationships), 2)
                        for relation in driver.relationships:
                            self.assertEqual(relation, observed)
                        for request in driver.requests:
                            for key in ("heir_character_id", "child_character_id", "candidate_character_id"):
                                self.assertNotIn(key, request)
                        leaf = observed[LEAF]
                        self.assertEqual(leaf, wire[LEAF])
                        self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                            leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                        self.assertEqual(observed[SUMMARY]["native_roster_status"], leaf["status"])
                        reproductive = "current_first_heir_reproductive_inputs_v1"
                        if reproductive in wire:
                            self.assertEqual(observed[reproductive], wire[reproductive])
                        inputs = leaf[CHILD_INPUTS]
                        self.assertEqual(inputs["source"], "native_current_heir_child_inputs")
                        for key in ("native_revision", "played_character_id", "heir_character_id", "date_raw"):
                            self.assertEqual(inputs[key], leaf[key])
                        rows = inputs["rows"]
                        if name == "empty-children-focus":
                            self.assertEqual(leaf["native_child_count_raw"], 0)
                            self.assertEqual(leaf["rows"], [])
                            self.assertEqual(inputs["status"], "available")
                            self.assertEqual(rows, [])
                        else:
                            values_failed = name == "child-focus-independent-of-values"
                            self.assertEqual(inputs["status"], "partial" if values_failed else "available")
                            distinct = name in {"distinct-child-focus-keys", legacy}
                            expected_ids = [child5, child8] if distinct else [child5]
                            self.assertEqual([row["character_id"] for row in rows], expected_ids)
                            if distinct:
                                self.assertEqual(leaf["native_child_count_raw"], 18)
                                self.assertEqual([row["raw_character_id"] for row in leaf["rows"]], distinct_ids)
                                self.assertEqual([row["occurrence_indices"] for row in rows], [child5_indices, [17]])
                            else:
                                self.assertEqual(leaf["native_child_count_raw"], 1)
                                self.assertEqual(rows[0]["occurrence_indices"], [0])
                            for index, row in enumerate(rows):
                                values, traits = row["values"], row["childhood_traits"]
                                self.assertEqual(values["source"], "native_character_age_and_sex")
                                self.assertEqual(traits["source"], "native_character_has_trait")
                                self.assertEqual(traits["status"], "available")
                                self.assertEqual(traits["queried_trait_keys"], list(CHILDHOOD_TRAIT_KEYS))
                                self.assertEqual(values["status"], "unavailable" if values_failed else "available")
                                if values_failed:
                                    self.assertIsNone(values["age_measure_raw"])
                                    self.assertIsNone(values["sex_selector_raw"])
                                if name == legacy:
                                    self.assertNotIn("native_focus", row)
                                    continue
                                focus = row["native_focus"]
                                self.assertEqual(focus["source"], "native_character_current_focus")
                                if name in {"child-focus-null-unavailable", "child-focus-key-unavailable"}:
                                    self.assertEqual(focus["status"], "unavailable")
                                    self.assertIsInstance(focus["unavailable_reason"], str)
                                    self.assertTrue(focus["unavailable_reason"])
                                    self.assertIsNone(focus["presence"])
                                    self.assertIsNone(focus["key"])
                                elif name == "child-focus-sentinel-absent":
                                    self.assertEqual(focus["status"], "available")
                                    self.assertIsNone(focus["unavailable_reason"])
                                    self.assertEqual(focus["presence"], "absent")
                                    self.assertIsNone(focus["key"])
                                else:
                                    self.assertEqual(focus["status"], "available")
                                    self.assertIsNone(focus["unavailable_reason"])
                                    self.assertEqual(focus["presence"], "present")
                                    self.assertEqual(focus["key"], focus_keys[index])
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        self.assertEqual(plan["family_marriage_status"], "current_first_heir_already_partnered")
                        self.assertEqual(plan["family_marriage_current_relationship"], observed)
                        source_name = "distinct-child-focus-keys" if name == legacy else name
                        records.append({"scene": name,
                            "source_kind": "new_native_wire_optional_focus_removed" if name == legacy
                                else "compiled_native_source_fixture",
                            "source_wire": str(Path(wire_dir) / (source_name + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 7)
        self.assertEqual(len({record["registered_service_result"]["plan"]["selected_step"]
                              for record in records}), 1)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "new_birth_observed": False, "natural_birth_cause_observed": False,
                "child_education_action_submitted": False, "native_action_submitted": False,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


    def test_current_first_heir_education_point_traits_reach_registered_query_and_service(self) -> None:
        """Five native whole wires and one absent-optional-field legacy copy."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_FIRST_HEIR_EDUCATION_POINT_TRAIT_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_FIRST_HEIR_EDUCATION_POINT_TRAIT_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native education-point trait wires required")
        scenes = (
            "education-point-trait-subsets", "education-point-known-empty",
            "education-point-traits-unavailable", "education-point-values-unavailable",
            "education-point-traits-changed",
        )
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scenes}
        legacy = "legacy-education-point-traits-absent"
        packets[legacy] = deepcopy(packets["education-point-trait-subsets"])
        for row in packets[legacy]["result"][LEAF][CHILD_INPUTS]["rows"]:
            row.pop("education_point_traits")
        actor, heir = 0x03000001, 0x03000002
        child5, child8 = 0x03000005, 0x03000008
        distinct_ids = [child5, 0x03000006, 0xFFFFFFFF, 0x07000005, 0x03000007]
        distinct_ids += [child5] * 12 + [child8]
        child5_indices = [0, *range(5, 17)]
        present_subsets = [
            ["intellect_good_3", "shrewd"],
            ["intellect_bad_2", "dull", "inbred"],
        ]
        # Stock family40 INPUT-CONTRACT.json gives these child predicates;
        # this observer neither supplies an educator nor predicts inheritance.
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-education-point-traits40",
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
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                def no_action(_step: str, _revision: int | None):
                    raise AssertionError("education-point trait observer cannot submit or advance")
                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []

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
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-education-point40-service-") as directory:
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
                            query_name = "ck3_query_current_first_heir_relationship_private_v1"
                            self.assertIn(query_name, tools)
                            self.assertIn("ck3_plan_turn", tools)
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
                        self.assertIsNone(wire["betrothed_character_id"])
                        self.assertEqual(wire["primary_spouse_character_id"], 0x03000003)
                        self.assertEqual(wire["spouse_character_ids"], [0x03000003])
                        self.assertGreaterEqual(len(driver.relationships), 2)
                        for relation in driver.relationships:
                            self.assertEqual(relation, observed)
                        for request in driver.requests:
                            for key in ("heir_character_id", "child_character_id", "candidate_character_id"):
                                self.assertNotIn(key, request)
                        leaf = observed[LEAF]
                        self.assertEqual(leaf, wire[LEAF])
                        self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                            leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                        self.assertEqual(leaf["status"], "available")
                        self.assertIs(leaf["roster_complete"], True)
                        self.assertEqual(observed[SUMMARY]["native_roster_status"], leaf["status"])
                        reproductive = "current_first_heir_reproductive_inputs_v1"
                        if reproductive in wire:
                            self.assertEqual(observed[reproductive], wire[reproductive])
                        inputs = leaf[CHILD_INPUTS]
                        self.assertEqual(inputs["source"], "native_current_heir_child_inputs")
                        for key in ("native_revision", "played_character_id", "heir_character_id", "date_raw"):
                            self.assertEqual(inputs[key], leaf[key])
                        values_failed = name == "education-point-values-unavailable"
                        self.assertEqual(inputs["status"], "partial" if values_failed else "available")
                        rows = inputs["rows"]
                        distinct = name in {"education-point-trait-subsets", legacy}
                        expected_ids = [child5, child8] if distinct else [child5]
                        self.assertEqual([row["character_id"] for row in rows], expected_ids)
                        if distinct:
                            self.assertEqual(leaf["native_child_count_raw"], 18)
                            self.assertEqual([row["raw_character_id"] for row in leaf["rows"]], distinct_ids)
                            self.assertEqual([row["occurrence_indices"] for row in rows], [child5_indices, [17]])
                        else:
                            self.assertEqual(leaf["native_child_count_raw"], 1)
                            self.assertEqual(rows[0]["occurrence_indices"], [0])
                        for index, row in enumerate(rows):
                            values, childhood = row["values"], row["childhood_traits"]
                            self.assertEqual(values["source"], "native_character_age_and_sex")
                            self.assertEqual(values["status"], "unavailable" if values_failed else "available")
                            if values_failed:
                                self.assertIsNone(values["age_measure_raw"])
                                self.assertIsNone(values["sex_selector_raw"])
                            else:
                                age = 0 if name == "education-point-known-empty" else (7, 9)[index]
                                self.assertEqual(values["age_measure_raw"], age)
                            self.assertEqual(childhood["source"], "native_character_has_trait")
                            self.assertEqual(childhood["status"], "available")
                            self.assertEqual(childhood["queried_trait_keys"], list(CHILDHOOD_TRAIT_KEYS))
                            focus = row["native_focus"]
                            self.assertEqual(focus["source"], "native_character_current_focus")
                            self.assertEqual(focus["status"], "available")
                            if name == "education-point-known-empty":
                                self.assertEqual(focus["presence"], "absent")
                                self.assertIsNone(focus["key"])
                            if name == legacy:
                                self.assertNotIn("education_point_traits", row)
                                continue
                            traits = row["education_point_traits"]
                            self.assertEqual(traits["source"], "native_character_has_trait")
                            self.assertEqual(traits["queried_trait_keys"], list(EDUCATION_POINT_TRAIT_KEYS))
                            if name in {"education-point-traits-unavailable", "education-point-traits-changed"}:
                                self.assertEqual(traits["status"], "unavailable")
                                self.assertIsInstance(traits["unavailable_reason"], str)
                                self.assertTrue(traits["unavailable_reason"])
                                self.assertIsNone(traits["present_trait_keys"])
                            else:
                                self.assertEqual(traits["status"], "available")
                                self.assertIsNone(traits["unavailable_reason"])
                                self.assertEqual(traits["present_trait_keys"],
                                    [] if name == "education-point-known-empty" else present_subsets[index])
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        self.assertEqual(plan["family_marriage_status"], "current_first_heir_already_partnered")
                        self.assertEqual(plan["family_marriage_current_relationship"], observed)
                        source_name = "education-point-trait-subsets" if name == legacy else name
                        records.append({"scene": name,
                            "source_kind": "new_native_wire_optional_education_point_traits_removed"
                                if name == legacy else "compiled_native_source_fixture",
                            "source_wire": str(Path(wire_dir) / (source_name + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 6)
        self.assertEqual(len({record["registered_service_result"]["plan"]["selected_step"]
                              for record in records}), 1)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "new_birth_observed": False, "natural_birth_cause_observed": False,
                "child_education_action_submitted": False, "educator_observed": False,
                "native_action_submitted": False, "inheritance_probability_observed": False,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


    def test_current_first_heir_typed_windows_reach_registered_query_and_service(self) -> None:
        """Three new native whole packets and one optional-leaf legacy copy."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_FIRST_HEIR_TYPED_WINDOW_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_FIRST_HEIR_TYPED_WINDOW_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native typed-window wires required")
        scenes = ("typed-window-seven-mixed", "typed-window-independent-unavailable",
                  "typed-window-handler-unavailable")
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scenes}
        legacy = "legacy-typed-windows-absent"
        packets[legacy] = deepcopy(packets[scenes[0]])
        removed = packets[legacy]["result"][LEAF][CHILD_INPUTS].pop(TYPED_WINDOWS)
        restored = deepcopy(packets[legacy])
        restored["result"][LEAF][CHILD_INPUTS][TYPED_WINDOWS] = removed
        self.assertEqual(restored, packets[scenes[0]])
        originals = deepcopy(packets)
        actor, heir = 0x03000001, 0x03000002
        fixed = ((0, 152, 13092), (1, 160, 11010), (2, 168, 11399),
                 (3, 176, 14350), (4, 184, 14351), (5, 192, 15450),
                 (6, 200, 10602))
        names = [f"FixtureWindowType{index}" for index in range(6)]
        names.append("FixtureArmyWindowType6")
        rva_keys = ("object_vtable_rva", "object_col_rva", "object_type_descriptor_rva")
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-typed-windows51",
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
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                self.action_calls: list[str] = []
                self.advance_calls: list[str] = []
                self.submit_requests: list[dict[str, object]] = []
                self.action_acks: list[dict[str, object]] = []

                def no_action(step: str, _revision: int | None):
                    self.action_calls.append(step)
                    if step == "life-advance":
                        self.advance_calls.append(step)
                    raise AssertionError("typed-window observer cannot submit or advance")

                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []

            def send(self, request: dict[str, object]) -> None:
                self.requests.append(deepcopy(request))
                if request.get("step") != STEP:
                    self.submit_requests.append(deepcopy(request))
                    raise AssertionError("typed-window fixture accepts only the current-heir query")
                if request.get("expected_revision") != 7:
                    raise AssertionError("typed-window query crossed the native frame")

            def wait_for_command_result(self, request_id: str, timeout_seconds: float):
                if not self.requests or self.requests[-1]["request_id"] != request_id:
                    raise AssertionError("current-heir query correlation changed")
                response = deepcopy(self.packet)
                if response["result"].get("step") != STEP:
                    self.action_acks.append(deepcopy(response))
                    raise AssertionError("typed-window fixture cannot acknowledge an action")
                return response

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
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        def available_rtti(row, rvas, decorated_name):
            self.assertEqual(row["window_presence"], "present")
            self.assertEqual(row["object_type_status"], "available")
            self.assertEqual(tuple(row[key] for key in rva_keys), rvas)
            self.assertEqual(row["object_type_decorated_name"], decorated_name)
            self.assertIsNone(row["object_type_unavailable_reason"])

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-typed-window51-service-") as directory:
                for name, packet in packets.items():
                    with self.subTest(scene=name):
                        self.assertEqual(packet["type"], "command_result")
                        self.assertIs(packet["ok"], True)
                        wire = packet["result"]
                        self.assertEqual(wire["step"], STEP)
                        self.assertEqual(wire["native_revision"], 7)
                        self.assertEqual(wire["heir_character_id"], heir)
                        self.assertIsNone(wire["betrothed_character_id"])
                        self.assertEqual(wire["primary_spouse_character_id"], 0x03000003)
                        self.assertEqual(wire["spouse_character_ids"], [0x03000003])
                        driver = FixtureDriver(packet, Path(directory) / name)
                        async with Client(create_server(driver)) as client:
                            tools = {tool.name for tool in (await client.list_tools()).tools}
                            query_name = "ck3_query_current_first_heir_relationship_private_v1"
                            self.assertIn(query_name, tools)
                            self.assertIn("ck3_plan_turn", tools)
                            queried = await client.call_tool(
                                query_name, {"expected_native_revision": 7})
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
                            self.assertEqual(request["step"], STEP)
                            self.assertEqual(request["expected_revision"], 7)
                            for key in ("heir_character_id", "child_character_id",
                                        "candidate_character_id"):
                                self.assertNotIn(key, request)
                        self.assertEqual(driver.submit_requests, [])
                        self.assertEqual(driver.action_acks, [])
                        self.assertEqual(driver.action_calls, [])
                        self.assertEqual(driver.advance_calls, [])
                        leaf = observed[LEAF]
                        self.assertEqual(leaf, wire[LEAF])
                        self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                            leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                        child_unavailable = name == "typed-window-handler-unavailable"
                        self.assertEqual(leaf["native_child_count_raw"],
                                         1 if child_unavailable else 0)
                        self.assertIs(leaf["roster_complete"], not child_unavailable)
                        self.assertEqual(leaf["rows"], [])
                        self.assertEqual(observed[SUMMARY]["native_roster_status"], leaf["status"])
                        self.assertEqual(observed[SUMMARY]["known_living_direct_child_occurrence_count"], 0)
                        self.assertIs(observed[SUMMARY]["living_actual_direct_child_exists"],
                                      None if child_unavailable else False)
                        inputs = leaf[CHILD_INPUTS]
                        self.assertEqual(inputs["source"], "native_current_heir_child_inputs")
                        self.assertEqual(inputs["status"],
                                         "unavailable" if child_unavailable else "available")
                        self.assertEqual(inputs["rows"], [])
                        for key in ("native_revision", "played_character_id", "heir_character_id", "date_raw"):
                            self.assertEqual(inputs[key], leaf[key])
                        reproductive = "current_first_heir_reproductive_inputs_v1"
                        if reproductive in wire:
                            self.assertEqual(observed[reproductive], wire[reproductive])
                        if name == legacy:
                            self.assertNotIn(TYPED_WINDOWS, inputs)
                        else:
                            diagnostic = inputs[TYPED_WINDOWS]
                            self.assertEqual(diagnostic, wire[LEAF][CHILD_INPUTS][TYPED_WINDOWS])
                            self.assertEqual(diagnostic["source"], "native_fixed_window_type_diagnostic")
                            self.assertEqual(diagnostic["native_revision"], inputs["native_revision"])
                            handler_unavailable = name == "typed-window-handler-unavailable"
                            self.assertEqual(diagnostic["window_handler_status"],
                                             "unavailable" if handler_unavailable else "available")
                            if handler_unavailable:
                                self.assertIsInstance(diagnostic["window_handler_unavailable_reason"], str)
                                self.assertTrue(diagnostic["window_handler_unavailable_reason"])
                            else:
                                self.assertIsNone(diagnostic["window_handler_unavailable_reason"])
                            rows = diagnostic["rows"]
                            self.assertEqual(len(rows), 7)
                            self.assertEqual([(row["slot_index"], row["handler_member_offset"],
                                               row["type_identifier"]) for row in rows], list(fixed))
                            independent = name == "typed-window-independent-unavailable"
                            for index, row in enumerate(rows):
                                name_unavailable = independent and index in (1, 2)
                                self.assertEqual(row["registered_name_status"],
                                                 "unavailable" if name_unavailable else "available")
                                if name_unavailable:
                                    self.assertIsNone(row["registered_name"])
                                    self.assertIsInstance(row["registered_name_unavailable_reason"], str)
                                    self.assertTrue(row["registered_name_unavailable_reason"])
                                else:
                                    self.assertEqual(row["registered_name"], names[index])
                                    self.assertIsNone(row["registered_name_unavailable_reason"])
                                if handler_unavailable:
                                    self.assertEqual(row["window_presence"], "unavailable")
                                    self.assertEqual(row["object_type_status"], "unavailable")
                                    self.assertTrue(row["object_type_unavailable_reason"])
                                    self.assertTrue(all(row[key] is None for key in rva_keys))
                                    self.assertIsNone(row["object_type_decorated_name"])
                                elif index in range(1, 6):
                                    self.assertEqual(row["window_presence"], "absent")
                                    self.assertEqual(row["object_type_status"], "not_applicable")
                                    self.assertTrue(all(row[key] is None for key in rva_keys))
                                    self.assertIsNone(row["object_type_decorated_name"])
                                    self.assertIsNone(row["object_type_unavailable_reason"])
                            if not handler_unavailable:
                                available_rtti(rows[0], (0x108, 0x200, 0x300),
                                               ".?AVFixtureWindow0@@")
                                if independent:
                                    self.assertNotEqual(rows[1]["registered_name_unavailable_reason"],
                                                        rows[2]["registered_name_unavailable_reason"])
                                    self.assertEqual(rows[6]["window_presence"], "present")
                                    self.assertEqual(rows[6]["object_type_status"], "unavailable")
                                    self.assertTrue(rows[6]["object_type_unavailable_reason"])
                                else:
                                    available_rtti(rows[6], (0x408, 0x500, 0x600),
                                                   ".?AVFixtureArmyWindow@@")
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        self.assertEqual(plan["family_marriage_status"],
                                         "current_first_heir_already_partnered")
                        self.assertEqual(plan["family_marriage_current_relationship"], observed)
                        source_name = scenes[0] if name == legacy else name
                        records.append({
                            "scene": name,
                            "source_kind": "new_native_wire_optional_typed_windows_removed"
                                if name == legacy else "compiled_native_source_fixture",
                            "source_wire": str(Path(wire_dir) / (source_name + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests,
                            "submit_count": len(driver.submit_requests),
                            "action_ack_count": len(driver.action_acks),
                            "action_count": len(driver.action_calls),
                            "advance_count": len(driver.advance_calls),
                        })
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 4)
        self.assertEqual(packets, originals)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "typed_window_names_and_rtti_origin": "native_fixture_not_actual_game_facts",
                "guardian_relation_observed": False, "character_window_identity_inferred": False,
                "native_action_submitted": False, "action_acknowledged": False,
                "day_advanced": False, "live": False, "G2_credit": 0,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


    def test_current_first_heir_character_window_identity_reaches_registered_query_and_service(self) -> None:
        """Five original native whole packets and one optional-sibling legacy copy."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHARACTER_WINDOW_IDENTITY_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_FIRST_HEIR_CHARACTER_WINDOW_IDENTITY_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native CharacterWindow whole wires required")
        identity_key = "character_window_identity"
        scenes = ("character-window-receiver-unavailable", "character-window-type-mismatch",
                  "character-window-id-invalid", "character-window-generation-mismatch",
                  "character-window-id-resolved")
        reasons = {
            scenes[0]: ("character_window_receiver_absent", "character_window_receiver_unavailable"),
            scenes[1]: ("character_window_vtable_mismatch", "character_window_receiver_unavailable"),
            scenes[2]: ("", "character_window_character_id_invalid"),
            scenes[3]: ("", "character_window_character_unresolved"),
            scenes[4]: ("", ""),
        }
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in scenes}
        legacy = "legacy-character-window-identity-absent"
        packets[legacy] = deepcopy(packets[scenes[-1]])
        removed = packets[legacy]["result"][LEAF][CHILD_INPUTS].pop(identity_key)
        restored = deepcopy(packets[legacy])
        restored["result"][LEAF][CHILD_INPUTS][identity_key] = removed
        self.assertEqual(restored, packets[scenes[-1]])
        originals = deepcopy(packets)
        actor, heir, subject = 0x03000001, 0x03000002, 0x03000004
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-first-heir-character-window-identity",
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
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                self.action_calls: list[str] = []
                self.advance_calls: list[str] = []
                self.submit_requests: list[dict[str, object]] = []
                self.action_acks: list[dict[str, object]] = []

                def no_action(step: str, _revision: int | None):
                    self.action_calls.append(step)
                    if step == "life-advance":
                        self.advance_calls.append(step)
                    raise AssertionError("CharacterWindow identity observation cannot submit or advance")

                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=no_action, action_steps=("life-advance",))
                self.packet, self.state_dir = packet, state_dir
                self._session_bridge_pid = os.getpid()
                self.endpoint, self.state = self, self
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []

            def send(self, request: dict[str, object]) -> None:
                self.requests.append(deepcopy(request))
                if request.get("step") != STEP:
                    self.submit_requests.append(deepcopy(request))
                    raise AssertionError("CharacterWindow fixture accepts only the current-heir query")
                if request.get("expected_revision") != 7:
                    raise AssertionError("CharacterWindow query crossed the native frame")

            def wait_for_command_result(self, request_id: str, timeout_seconds: float):
                if not self.requests or self.requests[-1]["request_id"] != request_id:
                    raise AssertionError("current-heir query correlation changed")
                response = deepcopy(self.packet)
                if response["result"].get("step") != STEP:
                    self.action_acks.append(deepcopy(response))
                    raise AssertionError("CharacterWindow fixture cannot acknowledge an action")
                return response

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
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_heir_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-character-window-identity-service-") as directory:
                for name, packet in packets.items():
                    with self.subTest(scene=name):
                        self.assertEqual(packet["type"], "command_result")
                        self.assertIs(packet["ok"], True)
                        wire = packet["result"]
                        self.assertEqual(wire["step"], STEP)
                        self.assertEqual(wire["native_revision"], 7)
                        self.assertEqual(wire["heir_character_id"], heir)
                        self.assertIsNone(wire["betrothed_character_id"])
                        self.assertEqual(wire["primary_spouse_character_id"], 0x03000003)
                        self.assertEqual(wire["spouse_character_ids"], [0x03000003])
                        driver = FixtureDriver(packet, Path(directory) / name)
                        async with Client(create_server(driver)) as client:
                            tools = {tool.name for tool in (await client.list_tools()).tools}
                            query_name = "ck3_query_current_first_heir_relationship_private_v1"
                            self.assertIn(query_name, tools)
                            self.assertIn("ck3_plan_turn", tools)
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
                            self.assertEqual(request["step"], STEP)
                            self.assertEqual(request["expected_revision"], 7)
                            for key in ("heir_character_id", "child_character_id",
                                        "candidate_character_id"):
                                self.assertNotIn(key, request)
                        self.assertEqual(driver.submit_requests, [])
                        self.assertEqual(driver.action_acks, [])
                        self.assertEqual(driver.action_calls, [])
                        self.assertEqual(driver.advance_calls, [])
                        leaf = observed[LEAF]
                        self.assertEqual(leaf, wire[LEAF])
                        self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                            leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                        self.assertEqual(leaf["status"], "available")
                        self.assertEqual(leaf["native_child_count_raw"], 0)
                        self.assertIs(leaf["roster_complete"], True)
                        self.assertEqual(leaf["rows"], [])
                        self.assertEqual(observed[SUMMARY]["native_roster_status"], "available")
                        self.assertEqual(observed[SUMMARY]["known_living_direct_child_occurrence_count"], 0)
                        self.assertIs(observed[SUMMARY]["living_actual_direct_child_exists"], False)
                        inputs = leaf[CHILD_INPUTS]
                        self.assertEqual(inputs["source"], "native_current_heir_child_inputs")
                        self.assertEqual(inputs["status"], "available")
                        self.assertEqual(inputs["rows"], [])
                        for key in ("native_revision", "played_character_id", "heir_character_id", "date_raw"):
                            self.assertEqual(inputs[key], leaf[key])
                        reproductive = "current_first_heir_reproductive_inputs_v1"
                        if reproductive in wire:
                            self.assertEqual(observed[reproductive], wire[reproductive])
                        if name == legacy:
                            self.assertNotIn(identity_key, inputs)
                        else:
                            identity = inputs[identity_key]
                            self.assertEqual(identity, wire[LEAF][CHILD_INPUTS][identity_key])
                            receiver_available = name not in scenes[:2]
                            character_available = name == scenes[-1]
                            self.assertIs(identity["receiver_available"], receiver_available)
                            self.assertIs(identity["character_available"], character_available)
                            self.assertEqual((identity["receiver_unavailable_reason"],
                                              identity["character_unavailable_reason"]), reasons[name])
                            expected_raw = None if not receiver_available else (
                                -1 if name == scenes[2] else 0x07000004
                                if name == scenes[3] else subject)
                            self.assertEqual(identity["raw_character_id"], expected_raw)
                            self.assertEqual(identity["character_id"], subject if character_available else None)
                            if character_available:
                                self.assertNotIn(identity["character_id"], (actor, heir))
                                self.assertEqual(inputs["rows"], [])
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        self.assertEqual(plan["family_marriage_status"],
                                         "current_first_heir_already_partnered")
                        self.assertEqual(plan["family_marriage_current_relationship"], observed)
                        source_name = scenes[-1] if name == legacy else name
                        records.append({
                            "scene": name,
                            "source_kind": "new_native_wire_optional_character_window_identity_removed"
                                if name == legacy else "compiled_native_source_fixture",
                            "source_wire": str(Path(wire_dir) / (source_name + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests,
                            "submit_count": len(driver.submit_requests),
                            "action_ack_count": len(driver.action_acks),
                            "action_count": len(driver.action_calls),
                            "advance_count": len(driver.advance_calls),
                        })
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 6)
        self.assertEqual(packets, originals)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "character_window_identity_origin": "native_fixture_not_actual_game_observation",
                "window_receiver_source_closed": False, "guardian_relation_observed": False,
                "native_action_submitted": False, "action_acknowledged": False,
                "day_advanced": False, "live": False, "G2_credit": 0,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
