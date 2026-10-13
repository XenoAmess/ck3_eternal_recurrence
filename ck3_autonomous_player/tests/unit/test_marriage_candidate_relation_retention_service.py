"""Retain existing candidate relationships without changing marriage policy."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_family_marriage_formal_consumer import family_reads, scene
from xar_autoplayer.bridge.domain_construction_private_transport_v1 import QUERY_NATIVE
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    STEP as RICH_STEP, query_first_heir_candidate_alliance_projection_private_v1,
)
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    SUBMIT_STEP, submit_observed_first_heir_marriage_private_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.family_marriage_formal_consumer import read_family_marriage_ledger
from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import query_m5_peacetime_proposal_sources_v1


RELATION_FIELDS = (
    "candidate_betrothed_character_id", "candidate_primary_spouse_character_id",
    "candidate_spouse_character_ids",
)


class CandidateRelationFixtureDriver(CallbackGameplayDriver):
    allow_private_family_marriage_formal_trial = True
    require_initial_lifestyle_focus_before_date_advance = False

    def __init__(self, state_dir: Path, selected_relation: dict[str, object]) -> None:
        self.frame = {**scene(), "snapshot_id": "native:7", "revision": 7,
                      "episode_character_id": 101, "history": [], "player_armies": [],
                      "played_character": {"character_id": 101, "alive": True},
                      "played_character_gold": {"raw": 100000000, "scale": 100000},
                      "diagnostics": {"hello": {
                          "expected_ck3_version": CK3_12004.game_version,
                          "expected_ck3_sha256": CK3_12004.executable_sha256,
                      }}}
        super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(self.frame),
                         execute=self.unexpected_action, action_steps=("life-advance",))
        self.state_dir = state_dir
        self._session_bridge_pid = os.getpid()
        self.command_timeout_seconds = 1.0
        self.endpoint = self.state = self
        self.requests: list[dict[str, object]] = []
        self.submissions: list[int] = []
        self.rich_projections: list[dict[str, object]] = []
        self.legality, self.projection = family_reads()
        self.legality.update(exact_ck3_build=CK3_12004.game_version,
                             exe_sha256=CK3_12004.executable_sha256,
                             read_only=True, advertised=False, root_query_sequence=1)
        for row in self.legality["native_legal_candidates"]:
            row.update(intermediary_character_id=-1, native_rank=None)
        relations = [selected_relation,
                     dict(zip(RELATION_FIELDS, (701, None, []))),
                     dict(zip(RELATION_FIELDS, (None, None, []))),
                     {}, dict(zip(RELATION_FIELDS, (None, 801, [801, 802])))]
        fertility = {"source": "native_marriage_fertility_input", "extension_present": True,
                     "native_gate_evaluated": True, "native_gate_allows": True,
                     "effective_raw": 50000}
        for row, relation in zip(self.projection["rows"], relations):
            row.update(failure="none", projection_failure="none", outcome_failure="none",
                       heir_native_fertility=deepcopy(fertility),
                       candidate_native_fertility=deepcopy(fertility), **deepcopy(relation))

    def unexpected_action(self, step, revision):
        raise AssertionError(f"source fixture cannot execute game step {step}")

    def take_internal_semantic_snapshot(self):
        return self.take_snapshot()

    def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision):
        if expected_native_revision != 7:
            raise AssertionError("final legality crossed the fixture frame")
        return deepcopy(self.legality)

    def query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs):
        result = query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs)
        self.rich_projections.append(result)
        return result

    def submit_observed_first_heir_marriage_private_v1(self, **kwargs):
        return submit_observed_first_heir_marriage_private_v1(self, **kwargs)

    def send(self, request):
        if request.get("expected_revision") != 7 or request.get("step") not in {
                RICH_STEP, SUBMIT_STEP, QUERY_NATIVE}:
            raise AssertionError("unexpected fixture endpoint request")
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout_seconds):
        request = self.requests[-1]
        if request["request_id"] != request_id:
            raise AssertionError("fixture correlation changed")
        step = request["step"]
        if step == RICH_STEP:
            if [request[f"candidate_id_{i}"] for i in range(5)] != list(range(300, 305)):
                raise AssertionError("existing bounded candidate order changed")
            result = {"step": step, "accepted": True, "private_build": True,
                      "read_only": True, "advertised": False, "native_revision": 7,
                      "legality_query_sequence": 2, "status": "available",
                      "rows": deepcopy(self.projection["rows"])}
        elif step == SUBMIT_STEP:
            self.submissions.append(request["candidate_character_id"])
            result = {"step": step, "accepted": True, "private_build": True,
                      "advertised": False, "status": "receipt_pending",
                      "material_result": False, "pre_native_revision": 7,
                      "played_character_id": 101, "heir_character_id": 202,
                      "candidate_character_id": request["candidate_character_id"]}
        else:
            world = {"status": "source_available", "snapshot_revision": 7,
                     "date_raw": self.frame["date_raw"], "player_character_id": 101,
                     "native_final_legality_evaluated": True, "native_cost_evaluated": True,
                     "player_gold_raw": 100000000, "active_constructions": [],
                     "completed_buildings_observed": True, "completed_buildings": [],
                     "legal_samples": [], "positive_income_coverage_complete": True}
            result = {"step": step, "accepted": True, "private_probe": {
                "advertised": False, "snapshot_revision": 7,
                "date_raw": self.frame["date_raw"], "proof_epoch": 1,
                "player_world_building_sources": world}}
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": result}


class MarriageCandidateRelationRetentionServiceTests(unittest.TestCase):
    def test_candidate_relation_retained_through_service_m5_and_pending(self) -> None:
        cases = {"existing": dict(zip(RELATION_FIELDS, (None, 601, [601, 602]))),
                 "betrothed": dict(zip(RELATION_FIELDS, (603, None, []))),
                 "empty": dict(zip(RELATION_FIELDS, (None, None, []))), "legacy": {}}
        with tempfile.TemporaryDirectory(prefix="xar-marriage-retention-") as temporary:
            for name, relation in cases.items():
                with self.subTest(candidate_relation=name):
                    driver = CandidateRelationFixtureDriver(Path(temporary) / name, relation)
                    service = GameplayBridgeService(driver)
                    planned = service.plan_turn()
                    plan = planned["plan"]
                    self.assertEqual(plan["selected_step"], SUBMIT_STEP)
                    self.assertEqual(plan["family_marriage_choice"]["candidate_character_id"], 300)
                    expected = {field: deepcopy(relation.get(field)) for field in RELATION_FIELDS}
                    diagnostic = plan["family_marriage_private_diagnostic"]["rows"]
                    for source, observed in zip(driver.projection["rows"], diagnostic):
                        self.assertEqual({field: observed[field] for field in RELATION_FIELDS},
                                         {field: source.get(field) for field in RELATION_FIELDS})
                    sources = query_m5_peacetime_proposal_sources_v1(
                        driver, snapshot=driver.take_snapshot(), history=[],
                        baseline_plan={"policy": "one-life-turn-v1", "selected_step": "life-advance"},
                        expected_revision=7)
                    copied = sources["domains"]["marriage"]["plan"]
                    self.assertEqual({field: copied["family_marriage_private_diagnostic"]["rows"][0][field]
                                      for field in RELATION_FIELDS}, expected)
                    collection = collect_m5_formal_proposals(snapshot=driver.take_snapshot(), sources=sources)
                    self.assertEqual(collection["dispatch"]["selected_candidate_id"],
                                     "marriage:first-heir:202:300:400")
                    reservation = collection["dispatch"]["reservation"]["commitments_after"]
                    self.assertEqual(reservation["ally_character_ids"], [])
                    self.assertEqual(reservation["character_ids"], [202, 300, 400])
                    self.assertEqual(reservation["commitment_keys"], ["first-heir-marriage:202"])
                    # Candidate relation IDs never become additional occupied roles.
                    outcome = service.auto_turn()
                    self.assertEqual(outcome["status"], "executed")
                    self.assertEqual(driver.submissions, [300])
                    value = outcome["result"]["selected_value_projection"]
                    self.assertEqual({field: value[field] for field in RELATION_FIELDS}, expected)
                    self.assertEqual({field: read_family_marriage_ledger(driver.state_dir)["pending"]
                                      ["selected_value_projection"][field] for field in RELATION_FIELDS}, expected)
                    if name == "existing":
                        # Mutating diagnostic evidence cannot rewrite the returned pending record.
                        outcome["plan"]["family_marriage_private_diagnostic"]["rows"][0][
                            "candidate_spouse_character_ids"].append(999)
                        self.assertEqual(value["candidate_spouse_character_ids"], [601, 602])
                        # The native input and initial diagnostic also own separate lists.
                        driver.rich_projections[0]["rows"][0]["candidate_spouse_character_ids"].append(998)
                        self.assertEqual(diagnostic[0]["candidate_spouse_character_ids"], [601, 602])
                    else:
                        self.assertEqual(value["candidate_betrothed_character_id"],
                                         603 if name == "betrothed" else None)
                        self.assertIsNone(value["candidate_primary_spouse_character_id"])
                        self.assertEqual(value["candidate_spouse_character_ids"],
                                         None if name == "legacy" else [])


if __name__ == "__main__":
    unittest.main()
