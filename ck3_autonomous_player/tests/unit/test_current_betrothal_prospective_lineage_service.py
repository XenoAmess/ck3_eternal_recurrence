"""Root FIRST consumes new native current-pair wires through registered Service."""

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

from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    STEP, query_current_first_heir_relationship_private_v1,
)
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.current_betrothal_fulfillment_proposal import (
    SUBMIT_STEP, current_betrothal_fulfillment_m5_proposal,
)


class CurrentBetrothalProspectiveLineageServiceTests(unittest.TestCase):
    def test_same_context_preview_reaches_registered_service_without_changing_fulfillment(self) -> None:
        """Five newly compiled wires and one absent-field copy; no native action.

        The fixture endpoint supplies only whole current-pair source packets.
        MCP registration, Service planning, strict transport, fixed-pair value
        and resource adaptation are production code. This qualifies the source
        fixture path, not a paused game, actual child or fulfilled marriage.
        """
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_BETROTHAL_LINEAGE_NATIVE_WIRE_DIR")
        output_path = os.environ.get("XAR_CURRENT_BETROTHAL_LINEAGE_SERVICE_OUTPUT")
        self.assertIsNotNone(wire_dir, "new compiled native whole-wire directory required")
        actor, heir, partner = 0x03000001, 0x03000002, 0x03000003
        scene_names = (
            "selected-false", "selected-true", "same-selector",
            "preview-binding-missing", "no-betrothal",
        )
        packets = {
            name: json.loads((Path(wire_dir) / (name + ".json")).read_text(encoding="utf-8"))
            for name in scene_names
        }
        packets["old-absent"] = deepcopy(packets["selected-false"])
        old_value = packets["old-absent"]["result"]["betrothal_actionability"]
        old_value.pop("matrilineal_option_selected")
        old_value.pop("native_child_house_preview")
        expected = {
            "selected-false": (False, False, heir, 100, 200),
            "selected-true": (True, True, partner, 300, 400),
            "same-selector": (True, False, partner, 300, 400),
        }
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-current-betrothal-lineage26",
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
            # This current-family scenario has no opening-focus prerequisite.
            # Its opt-in would return before ordinary family arbitration.
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, packet: dict[str, object], state_dir: Path) -> None:
                def no_action(_step: str, _revision: int | None) -> dict[str, object]:
                    raise AssertionError("observer compound cannot submit or advance")

                super().__init__(backend_id="native-headless",
                    snapshot=lambda: deepcopy(frame), execute=no_action,
                    action_steps=("life-advance",))
                self.packet = packet
                self.state_dir = state_dir
                self._session_bridge_pid = os.getpid()
                self.requests: list[dict[str, object]] = []
                self.relationships: list[dict[str, object]] = []
                self.legality_reads = 0
                self.endpoint = self
                self.state = self

            def send(self, request: dict[str, object]) -> None:
                if request.get("step") != STEP or request.get("expected_revision") != 7:
                    raise AssertionError("fixture accepts only the current-pair query")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id: str, timeout_seconds: float):
                if not self.requests or self.requests[-1]["request_id"] != request_id:
                    raise AssertionError("current-pair query correlation changed")
                return deepcopy(self.packet)

            def _execute_campaign_root_context_v1_query(self, *, expected_revision: int):
                if expected_revision != 7:
                    raise AssertionError("current-pair root crossed the fixture frame")
                return {"status": "available", "query_sequence": 11,
                        "held_title_partition": [{"primary": True,
                                                  "first_heir_character_id": heir}]}

            def query_current_first_heir_relationship_private_v1(self, **kwargs):
                relation = query_current_first_heir_relationship_private_v1(self, **kwargs)
                self.relationships.append(deepcopy(relation))
                return relation

            def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision: int):
                if expected_native_revision != 7:
                    raise AssertionError("ordinary family route crossed the fixture frame")
                self.legality_reads += 1
                # The no-betrothal case reaches the unchanged ordinary route.
                # This current-pair fixture supplies no candidate observations.
                return {"status": "unavailable",
                        "unavailable_reason": "source_fixture_current_pair_only"}

        async def consume() -> list[dict[str, object]]:
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-lineage26-service-") as directory:
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
                            self.assertIn("ck3_query_current_first_heir_relationship_private_v1", tools)
                            result = await client.call_tool("ck3_plan_turn", {})
                            self.assertFalse(result.is_error)
                            planned = result.structured_content
                        self.assertIsInstance(planned, dict)
                        plan = planned["plan"]
                        self.assertGreaterEqual(len(driver.relationships), 1)
                        relation = driver.relationships[-1]
                        value = relation["betrothal_actionability"]
                        self.assertEqual(value, wire["betrothal_actionability"])
                        self.assertEqual(relation["exact_ck3_build"], CK3_12004.game_version)
                        self.assertEqual(relation["exe_sha256"], CK3_12004.executable_sha256)
                        for request in driver.requests:
                            self.assertNotIn("heir_character_id", request)
                            self.assertNotIn("candidate_character_id", request)
                        preview = value.get("native_child_house_preview")
                        if name == "no-betrothal":
                            self.assertIsNone(relation["betrothed_character_id"])
                            self.assertEqual(value["status"], "not_applicable")
                            self.assertIsNone(value["matrilineal_option_selected"])
                            self.assertEqual(preview["status"], "not_applicable")
                            self.assertTrue(all(preview.get(key) is None for key in (
                                "selected_matrilineal_option", "effective_matrilineal_if_accepted",
                                "complete_can_send", "native_selected_parent_character_id",
                                "house_id", "dynasty_id")))
                            self.assertNotIn("current_betrothal_choice", plan)
                            self.assertEqual(plan["selected_step"], "life-advance")
                            self.assertEqual(driver.legality_reads, 1)
                        else:
                            self.assertEqual(value["status"], "available")
                            self.assertIs(value["ready_to_marry_betrothed"], True)
                            self.assertIs(value["complete_can_send"], True)
                            self.assertEqual(plan["selected_step"], SUBMIT_STEP)
                            self.assertEqual(driver.legality_reads, 0)
                            choice = plan["current_betrothal_choice"]
                            resource = choice["resource_proposal"]
                            self.assertEqual(choice["status"], "selected")
                            self.assertEqual(choice["reasons"], [])
                            for observed in (choice, resource):
                                self.assertIs(observed["matrilineal_option_selected"],
                                              value.get("matrilineal_option_selected"))
                                self.assertEqual(observed["native_child_house_preview"], preview)
                                self.assertIs(observed["effective_matrilineal_if_accepted"],
                                              value["effective_matrilineal_if_accepted"])
                            self.assertIn("child_dynasty_result", resource["unpriced"])
                            self.assertIs(resource["resource_reservation_performed"], False)
                            joint = current_betrothal_fulfillment_m5_proposal(
                                frame=resource["source_frame"], plan=plan)
                            self.assertEqual(joint["evidence"]["resource_proposal"][
                                "native_child_house_preview"], preview)
                            if name in expected:
                                selected, effective, parent_id, house, dynasty = expected[name]
                                self.assertIs(value["matrilineal_option_selected"], selected)
                                self.assertEqual(preview["status"], "available")
                                self.assertEqual(preview["reason"], "")
                                self.assertEqual(preview["subject_character_id"], heir)
                                self.assertEqual(preview["candidate_character_id"], partner)
                                self.assertIs(preview["requested_matrilineal_option"], False)
                                self.assertIs(preview["selected_matrilineal_option"], selected)
                                self.assertIs(preview["effective_matrilineal_if_accepted"], effective)
                                self.assertIs(preview["complete_can_send"], True)
                                self.assertEqual(preview["native_selected_parent_character_id"], parent_id)
                                self.assertEqual((preview["house_id"], preview["dynasty_id"]), (house, dynasty))
                            elif name == "preview-binding-missing":
                                self.assertIs(value["matrilineal_option_selected"], False)
                                self.assertEqual(preview["status"], "unavailable")
                                self.assertTrue(preview["reason"])
                            else:
                                self.assertNotIn("matrilineal_option_selected", value)
                                self.assertNotIn("native_child_house_preview", value)
                                self.assertIsNone(choice["matrilineal_option_selected"])
                                self.assertIsNone(choice["native_child_house_preview"])
                        records.append({"scene": name, "source_kind": "compiled_native_source_fixture"
                            if name != "old-absent" else "new_native_wire_optional_fields_removed",
                            "source_wire": str(Path(wire_dir) / (
                                (name if name != "old-absent" else "selected-false") + ".json")),
                            "relationship": relation, "service_result": planned,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 6)
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "actual_child_result_observed": False,
                "native_action_submitted": False, "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
