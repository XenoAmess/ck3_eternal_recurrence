"""Root FIRST of seven new household wires through the registered existing query."""

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

from xar_autoplayer.bridge.current_first_heir_reproductive_inputs_v1 import LEAF
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    STEP, query_current_first_heir_relationship_private_v1,
)
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004


class CurrentFirstHeirReproductiveInputsRegisteredServiceTests(unittest.TestCase):
    def test_current_married_household_inputs_reach_registered_query_and_service(self) -> None:
        """Real compiled native envelopes, strict transport, registry and ordinary plan."""
        from mcp import Client

        wire_dir = os.environ.get("XAR_CURRENT_HEIR_REPRODUCTIVE_NATIVE_WIRE_DIR")
        self.assertIsNotNone(wire_dir, "new compiled household whole-wire directory required")
        names = ("married-pair", "gate-zero", "extension-zero", "signed-negative",
                 "missing-gate", "partner-value-unavailable", "unpartnered")
        packets = {name: json.loads((Path(wire_dir) / (name + ".json")).read_text(
            encoding="utf-8")) for name in names}
        packets["legacy-absent"] = deepcopy(packets["married-pair"])
        packets["legacy-absent"]["result"].pop(LEAF)
        actor, heir, partner = 0x03000001, 0x03000002, 0x03000003
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-current-heir-reproductive32",
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
                    raise AssertionError("household observation cannot submit or advance")
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
                    raise AssertionError("source fixture accepts only the current-heir query")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id: str, timeout_seconds: float):
                if not self.requests or self.requests[-1]["request_id"] != request_id:
                    raise AssertionError("current-heir query correlation changed")
                return deepcopy(self.packet)

            def _execute_campaign_root_context_v1_query(self, *, expected_revision: int):
                if expected_revision != 7:
                    raise AssertionError("public heir crossed the fixture frame")
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
                return {"status": "unavailable", "unavailable_reason": "source_fixture_current_household_only"}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-household32-service-") as directory:
                for name, packet in packets.items():
                    with self.subTest(scene=name):
                        self.assertIs(packet["ok"], True)
                        wire = packet["result"]
                        driver = FixtureDriver(packet, Path(directory) / name)
                        async with Client(create_server(driver)) as client:
                            queried = await client.call_tool(
                                "ck3_query_current_first_heir_relationship_private_v1",
                                {"expected_native_revision": 7})
                            self.assertFalse(queried.is_error)
                            observed = queried.structured_content
                            planned = await client.call_tool("ck3_plan_turn", {})
                            self.assertFalse(planned.is_error)
                            service_result = planned.structured_content
                        self.assertEqual(observed["status"], "available")
                        self.assertEqual(observed["exact_ck3_build"], CK3_12004.game_version)
                        self.assertEqual(observed["exe_sha256"], CK3_12004.executable_sha256)
                        self.assertEqual(observed["current_first_heir_descendants_v1"]["native_child_count_raw"], 0)
                        self.assertIs(observed["current_first_heir_descendants_summary_v1"]["actual_direct_child_exists"], False)
                        self.assertEqual(observed["betrothal_actionability"]["status"], "not_applicable")
                        for relation in driver.relationships:
                            self.assertEqual(relation, observed)
                        for request in driver.requests:
                            self.assertNotIn("heir_character_id", request)
                            self.assertNotIn("candidate_character_id", request)
                        plan = service_result["plan"]
                        self.assertEqual(plan["selected_step"], "life-advance")
                        if name == "legacy-absent":
                            self.assertNotIn(LEAF, observed)
                        else:
                            leaf = observed[LEAF]
                            self.assertEqual(leaf, wire[LEAF])
                            self.assertEqual((leaf["played_character_id"], leaf["heir_character_id"],
                                leaf["native_revision"], leaf["date_raw"]), (actor, heir, 7, 53220000))
                            self.assertEqual(leaf["fertility_raw_scale"], 100000)
                            rows = leaf["rows"]
                            self.assertEqual([row["character_id"] for row in rows],
                                             [heir] if name == "unpartnered" else [heir, partner])
                            self.assertEqual(rows[0]["roles"], ["heir"])
                            if name != "unpartnered":
                                self.assertEqual(rows[1]["roles"], ["primary_spouse", "spouse"])
                            if name == "missing-gate":
                                self.assertEqual(leaf["status"], "partial")
                                for row in rows:
                                    self.assertEqual(row["status"], "unavailable")
                                    self.assertIsNone(row["native_fertility"])
                                    self.assertIsNone(row["age_measure_raw"])
                            else:
                                self.assertEqual(rows[0]["age_measure_raw"], 32)
                                self.assertEqual(rows[0]["sex_selector_raw"], 0)
                                self.assertEqual(rows[0]["native_fertility"]["effective_raw"],
                                                 0 if name == "gate-zero" else 80000)
                                if name == "partner-value-unavailable":
                                    self.assertEqual(leaf["status"], "partial")
                                    self.assertEqual(rows[1]["status"], "unavailable")
                                    self.assertIsNone(rows[1]["native_fertility"])
                                else:
                                    self.assertEqual(leaf["status"], "available")
                                    if name != "unpartnered":
                                        fertility = rows[1]["native_fertility"]
                                        self.assertEqual(rows[1]["age_measure_raw"], 29)
                                        self.assertEqual(fertility["effective_raw"],
                                            -2500 if name == "signed-negative" else
                                            0 if name in {"gate-zero", "extension-zero"} else 60000)
                                        if name == "extension-zero":
                                            self.assertIs(fertility["extension_present"], False)
                                            self.assertIs(fertility["native_gate_evaluated"], False)
                                            self.assertIsNone(fertility["native_gate_allows"])
                                        elif name == "gate-zero":
                                            self.assertIs(fertility["native_gate_evaluated"], True)
                                            self.assertIs(fertility["native_gate_allows"], False)
                            self.assertNotIn("pregnant", leaf)
                            self.assertNotIn("birth_probability", leaf)
                        if name != "unpartnered":
                            self.assertEqual(plan["family_marriage_status"], "current_first_heir_already_partnered")
                            self.assertEqual(plan["family_marriage_current_relationship"], observed)
                            self.assertEqual(driver.legality_reads, 0)
                        else:
                            self.assertEqual(driver.legality_reads, 1)
                        records.append({"scene": name,
                            "source_wire": str(Path(wire_dir) / (
                                ("married-pair" if name == "legacy-absent" else name) + ".json")),
                            "registered_query_result": observed,
                            "registered_service_result": service_result,
                            "query_requests": driver.requests})
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 8)
        output_path = os.environ.get("XAR_CURRENT_HEIR_REPRODUCTIVE_SERVICE_OUTPUT")
        if output_path:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({
                "qualification": "compiled_source_fixture_registered_service_only",
                "new_birth_observed": False, "pregnancy_observed": False,
                "natural_succession_observed": False, "native_action_submitted": False,
                "cases": records,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
