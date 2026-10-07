"""Source-shaped qualification of the bounded observed-comparison consumer.

Root owns FIRST execution. This compound does not replay a native wire or
qualify the previously delivered observers, a birth, or natural succession.
"""

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

from xar_autoplayer.bridge.domain_construction_private_transport_v1 import QUERY_NATIVE
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    STEP as RICH_STEP, query_first_heir_candidate_alliance_projection_private_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    SUBMIT_STEP, submit_observed_first_heir_marriage_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.family_marriage_formal_consumer import read_family_marriage_ledger
from xar_autoplayer.first_heir_native_reproductive_preference import BASIS
from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import (
    query_m5_peacetime_proposal_sources_v1,
)


class FirstHeirNativeReproductivePreferenceServiceTests(unittest.TestCase):
    def test_observed_comparison_preference_reaches_registered_service_m5_and_pending(self) -> None:
        """Eight new scenes use actual strict rich, preview loop and Service.

        Source fixtures supply snapshots, legal/current-relation/preview inputs
        and command replies. The production rich and action transports, real
        registered Service, continuity loop, M5 source/selector and pending
        projection are unchanged. No planner or arithmetic kernel is replaced.
        """
        from mcp import Client

        actor, heir = 0x03000001, 0x03000002
        candidates = [0x03000003, 0x03000005, 0x03000006, 0x03000007, 0x03000008]
        recipients = [0x03000020 + index for index in range(5)]
        acceptance = [500000, 400000, 300000, 200000, 100000]
        cost_keys = ("gold_raw", "prestige_raw", "piety_raw", "renown_raw",
                     "influence_raw", "herd_raw", "treasury_raw",
                     "treasury_or_gold_raw", "merit_raw", "barter_goods_raw")
        costs = {**dict.fromkeys(cost_keys, 0), "raw_scale": 100000,
                 "payer_role": "actor", "application_timing": "on_send"}
        goal = {
            "format_version": 1, "goal_key": "dynasty_continuity",
            "campaign_id": "source28-consumer-only", "origin_character_id": actor,
            "current_character_id": actor,
            "progress": {"reconciled_successions": 0, "last_succession": None},
        }
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-reproductive-preference28",
            "episode_character_id": actor,
            "played_character": {"character_id": actor, "alive": True},
            "played_character_gold": {"raw": 100000000, "scale": 100000},
            "campaign_goal": goal,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }

        def fertility(raw: int) -> dict[str, object]:
            return {"source": "native_marriage_fertility_input",
                    "extension_present": True, "native_gate_evaluated": True,
                    "native_gate_allows": True, "effective_raw": raw}

        base_rows = []
        for index, candidate in enumerate(candidates):
            base_rows.append({
                "actor_character_id": actor, "heir_character_id": heir,
                "candidate_character_id": candidate,
                "recipient_character_id": recipients[index],
                "status": "available", "failure": "none",
                "projection_failure": "none", "outcome_failure": "none",
                "predicted_outcome_if_accepted": "marriage",
                "matrilineal_option_selected": False,
                "effective_matrilineal_if_accepted": False,
                "heir_is_adult": True, "candidate_is_adult": True,
                "grand_wedding_option_selected": False,
                "heir_adult_measure_raw": 20, "candidate_adult_measure_raw": 20,
                "heir_adult_threshold_raw": 16, "candidate_adult_threshold_raw": 16,
                "played_house_id": 100, "played_dynasty_id": 200,
                "heir_house_id": 100, "heir_dynasty_id": 200,
                "candidate_house_id": 300 + index, "candidate_dynasty_id": 400 + index,
                "heir_sex_selector_raw": 0, "candidate_sex_selector_raw": 1,
                "heir_betrothed_character_id": None,
                "heir_primary_spouse_character_id": None, "heir_spouse_character_ids": [],
                "heir_native_fertility": fertility(15000),
                "candidate_native_fertility": fertility(10000 if index == 0 else 15000),
                "native_candidate_fertility_floor_raw": 10000,
                "heir_native_scorer_age_override_raw": -1,
                "candidate_native_scorer_age_override_raw": [None, 46, -1, -1, None][index],
                "native_candidate_scorer_age_upper_raw": 45,
                "recipient_ai_accept_raw": acceptance[index],
                "recipient_answer_status_raw": 0,
                "complete_can_send": True,
                "generic_costs": deepcopy(costs), "possible_alliance_pairs": [],
            })

        bypass_rows = deepcopy(base_rows)
        for row in bypass_rows:
            row.update({"heir_sex_selector_raw": 1, "candidate_sex_selector_raw": 0,
                        "matrilineal_option_selected": True,
                        "effective_matrilineal_if_accepted": True,
                        "heir_native_scorer_age_override_raw": None,
                        "candidate_native_scorer_age_override_raw": None,
                        "native_candidate_scorer_age_upper_raw": None})
        partial_rows = deepcopy(base_rows)
        for index, row in enumerate(partial_rows):
            row["candidate_native_scorer_age_override_raw"] = None
            row["native_candidate_fertility_floor_raw"] = None if index == 0 else 10000
            row["candidate_native_fertility"]["effective_raw"] = (
                10000 if index in (2, 4) else 15000)
        absent_rows = deepcopy(base_rows)
        optional_fields = ("native_candidate_fertility_floor_raw",
                           "heir_native_scorer_age_override_raw",
                           "candidate_native_scorer_age_override_raw",
                           "native_candidate_scorer_age_upper_raw")
        for row in absent_rows:
            for field in optional_fields:
                row.pop(field)
        all_fail_rows = deepcopy(base_rows)
        for index, row in enumerate(all_fail_rows):
            if index in (0, 2, 4):
                row["candidate_native_fertility"]["effective_raw"] = 10000
                row["candidate_native_scorer_age_override_raw"] = None
            else:
                row["candidate_native_scorer_age_override_raw"] = 46

        # Expected indices are original acceptance/ID order, never a fixture rank.
        scenes = (
            ("pass-before-fail", base_rows, 2, [2], 0),
            ("stable-all-positive-choices-retained", base_rows, 1, [2, 3, 4, 0, 1], 2),
            ("selector-zero-bypass", bypass_rows, 1, [1], 0),
            ("partial-stable", partial_rows, 3, [0, 1, 3], 1),
            ("old-absent-stable", absent_rows, 4, [0, 1, 2, 3, 4], 1),
            ("all-fail-fallback", all_fail_rows, 0, [0], 2),
            ("other-goal-original-order", base_rows, 0, [], None),
            ("existing-partner-dispatch", base_rows, None, [], None),
        )

        class FixtureDriver(CallbackGameplayDriver):
            allow_private_family_marriage_formal_trial = True
            allow_private_current_first_heir_relationship_query = True
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, name, rows, selected_index, state_dir):
                self.frame = deepcopy(frame)
                if name == "other-goal-original-order":
                    # The production ordinary campaign goal currently only
                    # admits continuity. Its absent-goal one-life route is
                    # the existing non-continuity path, not an invented goal.
                    self.frame.pop("campaign_goal")
                super().__init__(backend_id="native-headless",
                    snapshot=lambda: deepcopy(self.frame),
                    execute=self.unexpected_action, action_steps=("life-advance",))
                self.name, self.rows, self.selected_index = name, deepcopy(rows), selected_index
                self.state_dir = state_dir
                self._session_bridge_pid = os.getpid()
                self.command_timeout_seconds = 1.0
                self.endpoint, self.state = self, self
                self.requests, self.projections, self.relationships = [], [], []
                self.preview_queries, self.legality_reads, self.submissions = [], 0, []

            def unexpected_action(self, step, revision):
                raise AssertionError(f"fixture cannot execute a game step: {step}")

            def take_internal_semantic_snapshot(self):
                return self.take_snapshot()

            def query_current_first_heir_relationship_private_v1(self, *, expected_native_revision):
                if expected_native_revision != 7:
                    raise AssertionError("current relationship crossed the source frame")
                partnered = self.name == "existing-partner-dispatch"
                relation = {
                    "schema": "xar.ck3.current-first-heir-relationship.v1",
                    "status": "available", "native_revision": 7,
                    "read_only": True, "advertised": False, "bilateral_verified": True,
                    "heir_character_id": heir, "betrothed_character_id": None,
                    "primary_spouse_character_id": candidates[0] if partnered else None,
                    "spouse_character_ids": [candidates[0]] if partnered else [],
                }
                self.relationships.append(deepcopy(relation))
                return relation

            def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision):
                if expected_native_revision != 7:
                    raise AssertionError("final legality crossed the source frame")
                self.legality_reads += 1
                return {
                    "schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
                    "schema_version": 1, "status": "available", "read_only": True,
                    "advertised": False, "exact_ck3_build": CK3_12004.game_version,
                    "exe_sha256": CK3_12004.executable_sha256, "native_revision": 7,
                    "query_sequence": 12, "root_query_sequence": 11,
                    "observed_first_heir_character_id": heir,
                    "native_legal_candidates": [{
                        "played_character_id": actor, "subject_character_id": heir,
                        "candidate_character_id": candidate,
                        "recipient_matchmaker_character_id": recipients[index],
                        "intermediary_character_id": -1, "native_rank": None,
                        "complete_can_send": True, "recipient_answer_allows_send": True,
                        "recipient_answer_status_raw": 0, "recipient_ai_accept_raw": acceptance[index],
                        "played_dynasty_id": 200, "heir_dynasty_id": 200,
                        "candidate_dynasty_id": 400 + index,
                        "heir_adult_measure_raw": 20, "candidate_adult_measure_raw": 20,
                        "realm_backed_actor_recipient": True,
                    } for index, candidate in enumerate(candidates)],
                }

            def query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs):
                projection = query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs)
                self.projections.append(deepcopy(projection))
                return projection

            def query_family_obligations_private_v1(self, *, expected_revision,
                    subject_character_id, candidate_character_id, request_matrilineal_option):
                if (expected_revision != 7 or subject_character_id != heir
                        or candidate_character_id not in candidates):
                    raise AssertionError("native preview pair/frame changed")
                row = next(row for row in self.rows
                           if row["candidate_character_id"] == candidate_character_id)
                if request_matrilineal_option is not row["matrilineal_option_selected"]:
                    raise AssertionError("native selected option changed")
                self.preview_queries.append(candidate_character_id)
                positive = (self.name in {"pass-before-fail", "selector-zero-bypass",
                                         "all-fail-fallback"}
                            or candidate_character_id == candidates[self.selected_index])
                preview = {
                    "status": "available" if positive else "unavailable",
                    "reason": "" if positive else "source_fixture_preview_read_unavailable",
                    "subject_character_id": heir, "candidate_character_id": candidate_character_id,
                    "requested_matrilineal_option": request_matrilineal_option,
                }
                if positive:
                    preview.update({
                        "selected_matrilineal_option": row["matrilineal_option_selected"],
                        "effective_matrilineal_if_accepted": row["effective_matrilineal_if_accepted"],
                        "complete_can_send": True,
                        "native_selected_parent_character_id": heir,
                        "house_id": 100, "dynasty_id": 200,
                    })
                return {
                    "queried_native_revision": 7, "frame": {"date_raw": 53220000},
                    "native_child_house_preview": preview,
                }

            def submit_observed_first_heir_marriage_private_v1(self, **kwargs):
                return submit_observed_first_heir_marriage_private_v1(self, **kwargs)

            def send(self, request):
                if request.get("expected_revision") != 7 or request.get("step") not in {
                        RICH_STEP, SUBMIT_STEP, QUERY_NATIVE}:
                    raise AssertionError("fixture received an unplanned endpoint command")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id, timeout_seconds):
                request = self.requests[-1]
                if request["request_id"] != request_id:
                    raise AssertionError("endpoint correlation changed")
                step = request["step"]
                if step == RICH_STEP:
                    if (request["legality_query_sequence"] != 12
                            or [request[f"candidate_id_{index}"] for index in range(5)] != candidates):
                        raise AssertionError("fixed five source order changed")
                    result = {"step": step, "accepted": True, "private_build": True,
                              "read_only": True, "advertised": False, "native_revision": 7,
                              "legality_query_sequence": 12, "status": "available",
                              "rows": deepcopy(self.rows)}
                elif step == SUBMIT_STEP:
                    if request["query_sequence"] != 12:
                        raise AssertionError("submit lost final legality query")
                    self.submissions.append(request["candidate_character_id"])
                    result = {"step": step, "accepted": True, "private_build": True,
                              "advertised": False, "status": "receipt_pending",
                              "material_result": False, "pre_native_revision": 7,
                              "played_character_id": actor, "heir_character_id": heir,
                              "candidate_character_id": request["candidate_character_id"]}
                else:
                    world = {"status": "source_available", "snapshot_revision": 7,
                             "date_raw": 53220000, "player_character_id": actor,
                             "native_final_legality_evaluated": True,
                             "native_cost_evaluated": True, "player_gold_raw": 100000000,
                             "active_constructions": [], "completed_buildings_observed": True,
                             "completed_buildings": [], "legal_samples": [],
                             "positive_income_coverage_complete": True}
                    result = {"step": step, "accepted": True, "private_probe": {
                        "advertised": False, "snapshot_revision": 7, "date_raw": 53220000,
                        "proof_epoch": 1, "player_world_building_sources": world}}
                return {"type": "command_result", "protocol_version": 1,
                        "request_id": request_id, "ok": True, "result": result}

        async def consume():
            records = []
            with tempfile.TemporaryDirectory(prefix="xar-reproductive28-service-") as directory:
                for name, rows, selected_index, query_indices, preference_class in scenes:
                    with self.subTest(scene=name):
                        driver = FixtureDriver(name, rows, selected_index, Path(directory) / name)
                        source_rows = deepcopy(driver.rows)
                        async with Client(create_server(driver)) as client:
                            tools = {tool.name for tool in (await client.list_tools()).tools}
                            self.assertTrue({"ck3_plan_turn", "ck3_auto_turn"} <= tools)
                            planned = await client.call_tool("ck3_plan_turn", {})
                            self.assertFalse(planned.is_error)
                            plan = planned.structured_content["plan"]
                            self.assertGreaterEqual(len(driver.relationships), 1)
                            self.assertEqual(plan["family_marriage_current_relationship"],
                                             driver.relationships[-1])
                            record = {"scene": name, "service_plan": deepcopy(plan),
                                      "selected_candidate_character_id": None,
                                      "preview_query_order": deepcopy(driver.preview_queries)}
                            if selected_index is None:
                                self.assertEqual(plan["selected_step"], "life-advance")
                                self.assertEqual(plan["family_marriage_status"],
                                                 "current_first_heir_already_partnered")
                                self.assertEqual(driver.legality_reads, 0)
                                self.assertEqual(driver.projections, [])
                                self.assertEqual(driver.preview_queries, [])
                                self.assertEqual(driver.submissions, [])
                                self.assertNotIn("family_marriage_choice", plan)
                                self.assertIsNone(read_family_marriage_ledger(driver.state_dir)["pending"])
                            else:
                                selected = candidates[selected_index]
                                choice = plan["family_marriage_choice"]
                                self.assertEqual(plan["selected_step"], SUBMIT_STEP)
                                self.assertEqual(choice["candidate_character_id"], selected)
                                self.assertEqual(driver.preview_queries,
                                                 [candidates[index] for index in query_indices])
                                self.assertEqual(choice["recipient_ai_accept_raw"], acceptance[selected_index])
                                self.assertEqual(choice["immediate_generic_costs"], costs)
                                self.assertFalse(choice["realm_alliance_attempt_if_accepted"])
                                self.assertIn("child_dynasty_result", choice["unpriced"])
                                self.assertEqual(len(driver.projections), 1)
                                projection = driver.projections[0]
                                self.assertEqual(projection["exact_ck3_build"], CK3_12004.game_version)
                                self.assertEqual(projection["exe_sha256"], CK3_12004.executable_sha256)
                                self.assertEqual([row["candidate_character_id"] for row in projection["rows"]],
                                                 candidates)
                                self.assertEqual([row["rejection_reasons"] for row in
                                                  plan["family_marriage_private_diagnostic"]["rows"]], [[]] * 5)
                                observed_row = projection["rows"][selected_index]
                                if preference_class is None:
                                    self.assertNotIn(BASIS, choice)
                                else:
                                    basis = choice[BASIS]
                                    self.assertEqual(basis["source"],
                                        "derived_observed_native_reproductive_comparison_preference")
                                    self.assertEqual(basis["preference_class"], preference_class)
                                    self.assertEqual(basis["candidate_character_id"], selected)
                                    self.assertEqual(basis["floor_comparison"],
                                        observed_row["candidate_native_fertility_floor_comparison_v1"])
                                    floor_pass = basis["floor_comparison"]["passes"]
                                    self.assertIs(basis["age_considered"], floor_pass is True)
                                    self.assertEqual(basis["age_comparison"],
                                        observed_row["candidate_native_scorer_age_branch_v1"]
                                        if floor_pass is True else None)
                                    self.assertEqual(basis["comparison_status"],
                                        {0: "observed_pass", 1: "partial_or_absent", 2: "observed_fail"}[preference_class])
                                if name == "pass-before-fail":
                                    self.assertGreater(acceptance[0], choice["recipient_ai_accept_raw"])
                                    self.assertGreater(acceptance[1], choice["recipient_ai_accept_raw"])
                                    self.assertFalse(projection["rows"][0][
                                        "candidate_native_fertility_floor_comparison_v1"]["passes"])
                                    self.assertFalse(projection["rows"][1][
                                        "candidate_native_scorer_age_branch_v1"]["passes"])
                                if name == "selector-zero-bypass":
                                    age = choice[BASIS]["age_comparison"]
                                    self.assertIs(age["selector_zero_bypass"], True)
                                    self.assertIs(age["ready"], True)
                                    self.assertIs(age["passes"], True)
                                    self.assertFalse(age["first_comparison"]["ready"])
                                    self.assertFalse(age["second_comparison"]["ready"])
                                if name == "all-fail-fallback":
                                    self.assertIs(choice[BASIS]["floor_comparison"]["passes"], False)
                                    self.assertIsNone(choice[BASIS]["age_comparison"])
                                if name == "old-absent-stable":
                                    self.assertTrue(all(not row[
                                        "candidate_native_fertility_floor_comparison_v1"]["ready"]
                                        and not row["candidate_native_scorer_age_branch_v1"]["ready"]
                                        for row in projection["rows"]))

                                # M5's actual peaceful source copies the chosen
                                # plan and passes it to the original selector.
                                driver.preview_queries.clear()
                                snapshot = driver.take_snapshot()
                                m5_source = query_m5_peacetime_proposal_sources_v1(
                                    driver, snapshot=snapshot, history=[],
                                    baseline_plan={"policy": "one-life-turn-v1",
                                                   "selected_step": "life-advance"},
                                    expected_revision=7)
                                m5_plan = m5_source["domains"]["marriage"]["plan"]
                                self.assertEqual(m5_plan["family_marriage_choice"], choice)
                                copied_choices = m5_source["domains"]["marriage"]["plans"]
                                self.assertEqual(copied_choices[0]["family_marriage_choice"], choice)
                                if preference_class is not None:
                                    self.assertEqual(len(copied_choices), 1)
                                    self.assertEqual(copied_choices[0]["family_marriage_choice"][BASIS], choice[BASIS])
                                collection = collect_m5_formal_proposals(snapshot=snapshot, sources=m5_source)
                                self.assertEqual(collection["status"], "reserved_analytic")
                                self.assertEqual(collection["collected_domains"], ["marriage"])
                                expected_m5_id = f"marriage:first-heir:{heir}:{selected}:{recipients[selected_index]}"
                                self.assertIn(expected_m5_id, collection["collected_candidate_ids"])
                                self.assertEqual(collection["dispatch"]["selected_candidate_id"], expected_m5_id)

                                driver.preview_queries.clear()
                                submitted = await client.call_tool("ck3_auto_turn", {})
                                self.assertFalse(submitted.is_error)
                                outcome = submitted.structured_content
                                self.assertEqual(outcome["status"], "executed")
                                self.assertEqual(outcome["selected_step"], SUBMIT_STEP)
                                self.assertEqual(outcome["plan"]["family_marriage_choice"], choice)
                                self.assertEqual(driver.preview_queries,
                                                 [candidates[index] for index in query_indices])
                                self.assertEqual(driver.submissions, [selected])
                                pending = read_family_marriage_ledger(driver.state_dir)["pending"]
                                self.assertEqual(pending, outcome["result"])
                                self.assertEqual(pending["status"], "receipt_pending")
                                self.assertIs(pending["material_result"], False)
                                self.assertEqual(pending["candidate_character_id"], selected)
                                value = pending["selected_value_projection"]
                                self.assertEqual(value["candidate_character_id"], selected)
                                self.assertEqual(value["source_native_revision"], 7)
                                self.assertEqual(value["source_legality_query_sequence"], 12)
                                self.assertIn("future_child_identity_and_dynasty", value["unobserved_at_submission"])
                                if preference_class is None:
                                    self.assertNotIn(BASIS, value)
                                else:
                                    self.assertEqual(value[BASIS], choice[BASIS])
                                before_reads = (driver.legality_reads, len(driver.projections),
                                                len(driver.preview_queries), len(driver.relationships))
                                resumed = await client.call_tool("ck3_plan_turn", {})
                                self.assertFalse(resumed.is_error)
                                resumed_plan = resumed.structured_content["plan"]
                                self.assertEqual(resumed_plan["family_marriage_pending"], pending)
                                self.assertEqual(resumed_plan["family_marriage_status"], "await_later_paused_frame")
                                self.assertEqual(driver.submissions, [selected])
                                self.assertEqual(before_reads, (driver.legality_reads, len(driver.projections),
                                                len(driver.preview_queries), len(driver.relationships)))
                                self.assertEqual(read_family_marriage_ledger(driver.state_dir)["pending"], pending)
                                record.update({"selected_candidate_character_id": selected,
                                    "preference_basis": deepcopy(choice.get(BASIS)),
                                    "m5_source_choice": deepcopy(m5_plan["family_marriage_choice"]),
                                    "m5_collection": deepcopy(collection),
                                    "pending_value_basis": deepcopy(value.get(BASIS)),
                                    "pending": deepcopy(pending), "registered_submit": deepcopy(outcome),
                                    "pending_replan": deepcopy(resumed_plan)})
                        self.assertEqual(driver.rows, source_rows)
                        records.append(record)
            return records

        records = asyncio.run(consume())
        self.assertEqual(len(records), 8)
        output_path = os.environ.get("XAR_FIRST_HEIR_REPRODUCTIVE_PREFERENCE_SERVICE_OUTPUT")
        if output_path:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "schema": "xar.source28-reproductive-preference-service-evidence.v1",
                "input_boundary": "new_source_shaped_fixture_endpoints_through_production_consumer",
                "scene_count": 8, "unique_strict_opportunity_row_count": 35,
                "native_observer_requalification": False, "game_action": False,
                "birth": False, "natural_succession": False, "live": False,
                "scenes": records,
            }, indent=2) + "\n", encoding="utf-8")
