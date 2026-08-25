from __future__ import annotations

import copy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.phase_event_evaluator import (
    PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
    PHASE_EVENT_AST_EVALUATOR_SHA256,
    PHASE_EVENT_AST_EVALUATOR_VERSION,
    PhaseEventEvaluationError,
    _DrawTape,
    _native_tail_swap_filter,
    _native_candidate_int_weight,
    audit_stock_phase_event_evaluator,
    evaluate_phase_event_contexts,
    execute_phase_event_effect,
)
from xar_autoplayer.simulation.candidate_source_proof import (
    CANDIDATE_SOURCE_PROOF_POLICY,
    candidate_source_sequence_sha256,
)
from xar_autoplayer.simulation.phase_event_manifest import (
    load_stock_phase_event_manifest,
)


GOLDEN_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat_phase_events"
    / "v3_ast_evaluator_family_golden.json"
)
NATIVE_SOURCE_CONTRACT_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "combat_phase_event_trace_v1_source_contract.json"
)
NATIVE_ABI_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "combat_phase_event_trace_v1_abi.json"
)


def _production_fixture_builder():
    path = Path(__file__).with_name(
        "test_combat_phase_inputs_v3_production_contract.py"
    )
    spec = importlib.util.spec_from_file_location("_xar_phase_v3_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PhaseEventAstEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder = _production_fixture_builder()
        payload, scope = builder._production_payload()
        normalized = builder._normalize(payload, scope)
        phase = normalized["phase_event_inputs"]
        cls.contexts = phase["evaluation_contexts"]
        cls.advantage = phase["advantage_model"]
        cls.commander_context = next(
            context
            for context in cls.contexts
            if context["phase_roles"] == ["commander"]
        )
        cls.knight_context = next(
            context
            for context in cls.contexts
            if context["phase_roles"] == ["knight"]
        )
        cls.golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    def test_canonical_audit_covers_every_node_and_transition(self) -> None:
        audit = audit_stock_phase_event_evaluator()
        self.assertEqual(
            PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
            self.golden["schema_version"],
        )
        self.assertEqual(
            PHASE_EVENT_AST_EVALUATOR_VERSION,
            self.golden["evaluator_version"],
        )
        self.assertEqual(
            PHASE_EVENT_AST_EVALUATOR_SHA256,
            self.golden["evaluator_sha256"],
        )
        self.assertEqual(audit["proof_sha256"], self.golden["evaluator_proof_sha256"])
        self.assertEqual(
            audit["coverage"],
            {
                "event_row_count": 13,
                "commander_row_count": 4,
                "knight_row_count": 9,
                "ast_node_count": 688,
                "trigger_ast_rows_covered": 13,
                "chance_ast_rows_covered": 13,
                "effect_ast_rows_covered": 13,
                "direct_transition_count": 12,
                "internal_transition_count": 3,
                "unsupported_nodes": [],
                "unsupported_effects": [],
                "structural_ready": True,
                "ready": False,
            },
        )
        self.assertEqual(
            audit["status"], "structurally_covered_fidelity_blocked"
        )
        self.assertFalse(audit["ast_evaluator_ready"])
        self.assertEqual(
            audit["scope_semantics"]["owner"],
            {"status": "absent", "value": None},
        )
        self.assertFalse(audit["original_trace_ready"])

    def test_all_13_family_ast_hashes_and_node_counts_match_golden(self) -> None:
        rows = audit_stock_phase_event_evaluator()["rows"]
        expected = self.golden["families"]
        self.assertEqual([row["key"] for row in rows], [row["key"] for row in expected])
        for row, golden in zip(rows, expected, strict=True):
            with self.subTest(event=row["key"]):
                self.assertEqual(row["global_load_index"], golden["global_load_index"])
                self.assertEqual(row["type"], golden["type"])
                self.assertEqual(
                    [
                        row["validity_ast_sha256"],
                        row["chance_ast_sha256"],
                        row["effect_ast_sha256"],
                    ],
                    golden["ast_sha256"],
                )
                self.assertEqual(
                    [
                        row["validity_node_count"],
                        row["chance_node_count"],
                        row["effect_node_count"],
                    ],
                    golden["node_counts"],
                )
                self.assertTrue(row["validity_covered"])
                self.assertTrue(row["chance_covered"])
                self.assertTrue(row["effect_covered"])

    def test_current_132_ref_contexts_evaluate_all_rows_but_remain_blocked(self) -> None:
        projection = evaluate_phase_event_contexts(self.contexts)
        self.assertEqual(
            projection["status"], "structurally_covered_fidelity_blocked"
        )
        self.assertEqual(projection["context_count"], len(self.contexts))
        self.assertEqual(
            projection["event_row_coverage"]["event_row_count"], 13
        )
        self.assertEqual(
            projection["event_row_coverage"]["unsupported_nodes"], []
        )
        self.assertEqual(
            projection["event_row_coverage"]["unsupported_effects"], []
        )
        self.assertTrue(projection["event_row_coverage"]["structural_ready"])
        self.assertFalse(projection["event_row_coverage"]["ready"])
        self.assertTrue(
            projection["candidate_materialization_and_order"][
                "materialization_input_ready"
            ]
        )
        self.assertTrue(
            projection["candidate_materialization_and_order"]["ready"]
        )
        self.assertFalse(projection["ast_evaluator_ready"])
        self.assertFalse(projection["original_trace_ready"])
        for context in projection["contexts"]:
            self.assertEqual(
                [row["global_load_index"] for row in context["rows"]],
                list(range(13)),
            )
            self.assertEqual(
                context["owner_scope"], {"status": "absent", "value": None}
            )

    def test_all_13_family_effects_write_back_to_trial_state(self) -> None:
        for family in self.golden["families"]:
            key = family["key"]
            with self.subTest(event=key):
                context = self._valid_context(key, family["type"])
                result = execute_phase_event_effect(
                    context,
                    event_key=key,
                    draws=[0] * family["draw_count"],
                    advantage_model=self.advantage,
                )
                self.assertEqual(
                    result["status"],
                    "offline_projection_applied_fidelity_blocked",
                )
                self.assertEqual(result["event"]["key"], key)
                self.assertTrue(result["event"]["trigger_valid"])
                self.assertEqual(
                    result["draw_tape"]["consumed_count"], family["draw_count"]
                )
                self.assertFalse(result["original_trace_ready"])
                self.assertFalse(result["ast_evaluator_ready"])
                self.assertTrue(
                    result["candidate_materialization_and_order_ready"]
                )
                self.assertFalse(result["battle_horizon_feedback_ready"])
                self.assertFalse(result["planner_usable"])
                self.assertFalse(result["active_attack_allowed"])
                self._assert_family_effect(family, result)

    def test_candidate_order_and_each_feedback_effect_are_hard_blockers(self) -> None:
        audit = audit_stock_phase_event_evaluator()
        candidate = audit["candidate_materialization_and_order"]
        self.assertEqual(
            candidate["policy"],
            "ccombat_side_knight_source_then_tail_swap_remove_v1",
        )
        self.assertEqual(candidate["occurrence_count"], 9)
        self.assertTrue(candidate["algorithm_ready"])
        self.assertFalse(candidate["materialization_input_ready"])
        self.assertFalse(candidate["ready"])
        self.assertEqual(
            candidate["candidate_source_proof_policy"],
            CANDIDATE_SOURCE_PROOF_POLICY,
        )
        golden_candidate = self.golden["fidelity_blockers"][
            "native_random_side_knight_candidate_payload_requirement"
        ]
        self.assertFalse(
            golden_candidate["static_audit_materialization_input_ready"]
        )
        self.assertTrue(
            golden_candidate["production_fixture_materialization_input_ready"]
        )
        self.assertTrue(golden_candidate["production_fixture_ready"])

        feedback = audit["battle_horizon_feedback"]
        expected = self.golden["fidelity_blockers"][
            "battle_horizon_effect_feedback_closure"
        ]["unmodeled_effects_source_order"]
        self.assertEqual(
            [row["effect"] for row in feedback["effects"]], expected
        )
        self.assertEqual(feedback["effect_count"], 15)
        self.assertFalse(feedback["ready"])
        for row in feedback["effects"]:
            with self.subTest(effect=row["effect"]):
                self.assertTrue(row["event_keys_source_order"])
                self.assertEqual(
                    row["model_status"], "record_only_not_state_complete"
                )
                self.assertIsInstance(row["direct_132_ref_intersection"], list)
                self.assertTrue(row["required_closure_evidence"])
                self.assertFalse(row["battle_horizon_exclusion_proved"])
                self.assertFalse(row["feedback_ready"])
        delays = {
            row["effect"]: row.get("minimum_delay_days")
            for row in feedback["effects"]
            if "minimum_delay_days" in row
        }
        self.assertEqual(
            delays,
            {
                "delayed_epilepsy_risk": 30,
                "delayed_infection_or_treatment": 2,
                "hold_court_delayed_event": 1,
            },
        )
        by_effect = {row["effect"]: row for row in feedback["effects"]}
        self.assertIn(
            "effective knight contribution/advantage",
            by_effect["glory"]["direct_132_ref_intersection"],
        )
        self.assertEqual(
            by_effect["prestige"]["direct_132_ref_intersection"], []
        )
        self.assertFalse(by_effect["prestige"]["feedback_ready"])

    def test_native_candidate_contract_is_locked_to_source_and_abi_fixtures(self) -> None:
        source = json.loads(NATIVE_SOURCE_CONTRACT_PATH.read_text(encoding="utf-8"))[
            "random_side_knight_order"
        ]
        abi = json.loads(NATIVE_ABI_PATH.read_text(encoding="utf-8"))["abi"][
            "random_side_knight_candidate_order"
        ]
        contract = audit_stock_phase_event_evaluator()[
            "candidate_materialization_and_order"
        ]
        self.assertEqual(source["policy"], contract["policy"])
        self.assertEqual(abi["policy"], contract["policy"])
        self.assertEqual(source["class_vtable_rva"], "0x41DE5C0")
        self.assertEqual(abi["materializer"].split(";")[0], "0x19DD670")
        self.assertIn("shared R8 first then source RDX", abi["predicate_receiver_order"])
        self.assertIn("tail_swap_remove", abi["limit_compaction"])
        self.assertIn("signed Q100000", abi["weight"])
        self.assertIn("draw31 % candidate_count", abi["rng"])
        self.assertFalse(source["combat_inputs_v3_source_vector_equivalence_ready"])
        self.assertTrue(contract["algorithm_ready"])
        self.assertFalse(contract["materialization_input_ready"])
        projection = evaluate_phase_event_contexts(self.contexts)
        production = projection["candidate_materialization_and_order"]
        self.assertTrue(production["materialization_input_ready"])
        self.assertTrue(production["ready"])
        self.assertEqual(
            production["candidate_source_proof_policy"],
            CANDIDATE_SOURCE_PROOF_POLICY,
        )

    def test_candidate_tail_swap_order_and_exact_weighted_draw(self) -> None:
        context = self._valid_context("commander_wounded", "commander")
        template = context["candidate_rows"][0]
        source_contract = json.loads(
            NATIVE_SOURCE_CONTRACT_PATH.read_text(encoding="utf-8")
        )["random_side_knight_order"]
        native_vector = next(
            row
            for row in source_contract["deterministic_vectors"]
            if row["case"] == "tail_swap_remove_nonstable"
        )
        character_ids = native_vector["source"]
        rows = []
        for index, character_id in enumerate(character_ids):
            row = copy.deepcopy(template)
            row["character_id"] = character_id
            # Only source row 102 fails. Stable filter would yield 101,103,104;
            # the native tail swap must yield fixture order 101,104,103.
            prowess = (
                0
                if character_id in native_vector["source_reject"]
                else 10_000_000
            )
            row["candidate_refs"]["candidate.skills.prowess_raw"] = prowess
            row["selected_enemy_knight_refs"][
                "selected_enemy_knight.skills.prowess_raw"
            ] = prowess
            rows.append(row)
        context["candidate_rows"] = rows
        refs = {**context["native_state_refs"], **context["offline_state_refs"]}
        enemy_membership_owner = (
            context["native_state_refs"]
            if "enemy_side.character_membership" in context["native_state_refs"]
            else context["offline_state_refs"]
        )
        ordered_owner = (
            context["native_state_refs"]
            if "combat_side.ordered_enemy_knights" in context["native_state_refs"]
            else context["offline_state_refs"]
        )
        self.assertIn("enemy_side.character_membership", refs)
        self.assertIn("combat_side.ordered_enemy_knights", refs)
        enemy_membership_owner["enemy_side.character_membership"] = character_ids
        ordered_owner["combat_side.ordered_enemy_knights"] = character_ids
        proof = context["candidate_source_proof"]
        commander_sources = [
            copy.deepcopy(row)
            for row in proof["ordered_sources"]
            if row["role"] == "commander"
        ]
        source_army_id = next(
            int(row["source_army_id"])
            for row in proof["ordered_sources"]
            if row["role"] == "knight"
        )
        proof["ordered_sources"] = commander_sources + [
            {
                "role": "knight",
                "source_army_id": source_army_id,
                "source_regiment_id": 10_000 + index,
                "character_id": character_id,
            }
            for index, character_id in enumerate(character_ids)
        ]
        proof["sequence_sha256"] = candidate_source_sequence_sha256(
            context["enemy_side_index"], proof["ordered_sources"]
        )

        result = execute_phase_event_effect(
            context,
            event_key="commander_wounded",
            draws=[0, 0],
        )
        selection = result["transition_log"][0]
        self.assertEqual(
            selection["eligible_character_ids_compacted_order"],
            native_vector["expected_post_compaction"],
        )
        self.assertEqual(selection["selected_character_id"], 101)
        materialization = selection["materialization"]
        self.assertEqual(
            materialization["post_compaction_character_ids"],
            native_vector["expected_post_compaction"],
        )
        self.assertEqual(
            materialization["predicate_log"],
            native_vector["expected_predicate_log"],
        )
        draw = result["draw_tape"]["records"][0]
        self.assertEqual(draw["weights_int32_compacted_order"], [1, 1, 1])
        self.assertEqual(draw["selection_mode"], "positive_total_weighted")
        self.assertTrue(result["candidate_materialization_input_ready"])
        self.assertTrue(result["candidate_materialization_and_order_ready"])
        self.assertFalse(result["ast_evaluator_ready"])

    def test_candidate_signed_int32_weights_and_uniform_fallback_consume_draw(self) -> None:
        self.assertEqual(
            [
                _native_candidate_int_weight(value)
                for value in [1, -1, 100_000, 100_001, -100_001]
            ],
            [1, 0, 1, 2, -1],
        )
        self.assertEqual(
            _native_candidate_int_weight((1 << 31) * 100_000),
            -(1 << 31),
        )
        vectors = json.loads(
            NATIVE_SOURCE_CONTRACT_PATH.read_text(encoding="utf-8")
        )["random_side_knight_order"]["deterministic_vectors"]
        signed = next(
            row for row in vectors if row["case"] == "signed_negative_weight_not_clamped"
        )
        tape = _DrawTape.from_value([signed["draw31"]])
        selected = tape.take_native_side_knight(
            "test:signed", signed["chance_raw"]
        )
        self.assertEqual(selected, signed["expected_selected_index"])
        self.assertEqual(
            tape.records[0]["weights_int32_compacted_order"],
            signed["expected_int32_weights"],
        )
        uniform = next(
            row for row in vectors if row["case"] == "total_nonpositive_uniform_draw"
        )
        tape = _DrawTape.from_value([uniform["draw31"]])
        selected = tape.take_native_side_knight(
            "test:nonpositive",
            [weight * 100_000 for weight in uniform["int32_weights"]],
        )
        self.assertEqual(selected, uniform["expected_selected_index"])
        self.assertEqual(tape.position, 1)
        self.assertEqual(tape.records[0]["total_int32"], uniform["signed_total"])
        self.assertEqual(
            tape.records[0]["selection_mode"], "nonpositive_total_uniform"
        )

    def test_evaluator_revalidates_candidate_proof_digest_and_knight_subsequence(self) -> None:
        digest_tamper = copy.deepcopy(self.commander_context)
        digest_tamper["candidate_source_proof"]["sequence_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            PhaseEventEvaluationError, "candidate-source proof rejected"
        ):
            evaluate_phase_event_contexts([digest_tamper])

        sequence_tamper = copy.deepcopy(self.commander_context)
        proof = sequence_tamper["candidate_source_proof"]
        knight = next(
            row for row in proof["ordered_sources"] if row["role"] == "knight"
        )
        knight["character_id"] = int(knight["character_id"]) + 1
        proof["sequence_sha256"] = candidate_source_sequence_sha256(
            sequence_tamper["enemy_side_index"], proof["ordered_sources"]
        )
        with self.assertRaisesRegex(
            PhaseEventEvaluationError, "knight subsequence differs"
        ):
            evaluate_phase_event_contexts([sequence_tamper])

    def test_candidate_shared_predicate_short_circuits_source_fixture(self) -> None:
        vector = next(
            row
            for row in json.loads(
                NATIVE_SOURCE_CONTRACT_PATH.read_text(encoding="utf-8")
            )["random_side_knight_order"]["deterministic_vectors"]
            if row["case"] == "shared_short_circuits_source"
        )
        rows = [{"character_id": item} for item in vector["source"]]
        compacted, _evaluations, predicate_log = _native_tail_swap_filter(
            rows,
            shared_predicate=lambda row: row["character_id"]
            not in vector["shared_reject"],
            source_predicate=lambda row: row["character_id"]
            not in vector["source_reject"],
        )
        self.assertEqual(
            [row["character_id"] for row in compacted],
            vector["expected_post_compaction"],
        )
        self.assertEqual(predicate_log, vector["expected_predicate_log"])

    def test_prowess_branch_writes_selected_knight_and_requests_recompute(self) -> None:
        context = self._valid_context("commander_wounded", "commander")
        candidate_id = context["candidate_rows"][0]["character_id"]
        before = context["candidate_rows"][0]["selected_enemy_knight_refs"][
            "selected_enemy_knight.skills.prowess_raw"
        ]
        result = execute_phase_event_effect(
            context,
            event_key="commander_wounded",
            draws=[0, 1_342_177_280],
        )
        candidate = next(
            row
            for row in result["after_state"]["enemy_candidates"]
            if row["character_id"] == candidate_id
        )
        self.assertEqual(candidate["prowess_raw"], before + 100_000)
        self.assertIn(
            candidate_id,
            result["after_state"]["recompute"]["character_stat_ids"],
        )

    def test_wound_rank_three_kills_and_detaches_root(self) -> None:
        context = self._valid_context("commander_wounded", "commander")
        context["native_state_refs"]["root.traits.wounded.rank_raw"] = 300_000
        result = execute_phase_event_effect(
            context,
            event_key="commander_wounded",
            draws=[0, 0],
        )
        self.assertFalse(result["after_state"]["root"]["alive"])
        self.assertNotIn(
            context["root_character_id"],
            result["after_state"]["sides"]["combat_membership"],
        )
        self.assertIn(
            context["root_character_id"],
            result["after_state"]["recompute"]["participant_detach_ids"],
        )

    def test_commander_death_removes_advantage_contribution_then_recomputes(self) -> None:
        context = self._valid_context("commander_killed", "commander")
        root_id = context["root_character_id"]
        model = {
            "status": "available",
            "base_static_accumulator_raw": 100_000,
            "resolved_dynamic": {
                "sides": [
                    {
                        "side": "attacker",
                        "battle_commander_character_id": root_id,
                        "commander_dynamic_raw": 500_000,
                        "side_total_raw": 800_000,
                    },
                    {
                        "side": "defender",
                        "battle_commander_character_id": None,
                        "commander_dynamic_raw": 0,
                        "side_total_raw": 200_000,
                    },
                ],
                "resolved_advantage_at_zero_roll_raw": 700_000,
            },
        }
        result = execute_phase_event_effect(
            context,
            event_key="commander_killed",
            draws=[0, 0],
            advantage_model=model,
        )
        advantage = result["after_state"]["recompute"]["advantage"]
        self.assertTrue(advantage["recompute_required"])
        self.assertEqual(
            advantage["removed_commander_contributions"],
            [{"character_id": root_id, "side_index": 0, "removed_raw": 500_000}],
        )
        self.assertIsNone(advantage["side_rows"][0]["battle_commander_character_id"])
        self.assertEqual(advantage["side_rows"][0]["side_total_raw"], 300_000)
        self.assertEqual(advantage["resolved_advantage_raw"], 200_000)
        self.assertFalse(advantage["original_trace_ready"])

    def test_uncovered_node_effect_and_malformed_schema_fail_closed(self) -> None:
        manifest = load_stock_phase_event_manifest()
        first = manifest.event_rows[0]
        bad_node = replace(first, validity_ast={"op": "caller_defined"})
        with self.assertRaisesRegex(PhaseEventEvaluationError, "unsupported value op"):
            audit_stock_phase_event_evaluator(
                replace(manifest, event_rows=(bad_node, *manifest.event_rows[1:]))
            )

        bad_effect = replace(
            first,
            effect_ast={
                "op": "call_transition",
                "key": "caller_defined_effect",
                "args": {},
                "dependencies": [],
            },
        )
        with self.assertRaisesRegex(
            PhaseEventEvaluationError, "unsupported direct transition"
        ):
            audit_stock_phase_event_evaluator(
                replace(manifest, event_rows=(bad_effect, *manifest.event_rows[1:]))
            )

        malformed = replace(
            first,
            validity_ast={"op": "const_bool", "value": True, "extra": False},
        )
        with self.assertRaisesRegex(PhaseEventEvaluationError, "schema is malformed"):
            audit_stock_phase_event_evaluator(
                replace(manifest, event_rows=(malformed, *manifest.event_rows[1:]))
            )

    def test_missing_draw_and_wrong_scope_role_fail_closed(self) -> None:
        context = self._valid_context("commander_wounded", "commander")
        with self.assertRaisesRegex(PhaseEventEvaluationError, "draw tape exhausted"):
            execute_phase_event_effect(
                context, event_key="commander_wounded", draws=[]
            )
        with self.assertRaisesRegex(PhaseEventEvaluationError, "has no knight role"):
            execute_phase_event_effect(
                context, event_key="knight_none", draws=[]
            )

    def _valid_context(self, key: str, event_type: str) -> dict[str, object]:
        context = copy.deepcopy(
            self.commander_context if event_type == "commander" else self.knight_context
        )
        native = context["native_state_refs"]
        offline = context["offline_state_refs"]
        candidate = context["candidate_rows"][0]
        candidate_refs = candidate["candidate_refs"]
        selected_refs = candidate["selected_enemy_knight_refs"]

        # Attribution rows require an enemy at or above 80% root prowess.
        root_prowess = native["root.skills.prowess_raw"]
        candidate_refs["candidate.skills.prowess_raw"] = root_prowess
        selected_refs["selected_enemy_knight.skills.prowess_raw"] = root_prowess
        candidate_refs[
            "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter"
        ] = True

        if key == "commander_killed":
            native["root.traits.wounded.rank_raw"] = 100_000
        elif key == "knight_berserker_attack":
            native["root.traits.berserker"] = True
            self._make_candidate_below(candidate, offline)
        elif key == "knight_become_berserker":
            native["root.faith.tenets.warmonger"] = True
            native["root.culture.heritage_north_germanic"] = True
            native["root.traits.craven"] = False
            native["root.traits.berserker"] = False
            native["root.traits.calm"] = False
            self._make_candidate_below(candidate, offline, require_alive=False)
        elif key == "knight_shieldmaiden_attack":
            native["root.traits.shieldmaiden"] = True
            self._make_candidate_below(candidate, offline)
        elif key == "knight_qualify_for_accolade":
            native["root.liege.accolade_progress_raw"] = 100_000
        return context

    @staticmethod
    def _make_candidate_below(
        candidate: dict[str, object],
        offline: dict[str, object],
        *,
        require_alive: bool = True,
    ) -> None:
        candidate_refs = candidate["candidate_refs"]
        selected_refs = candidate["selected_enemy_knight_refs"]
        candidate_refs["candidate.alive"] = True
        selected_refs["selected_enemy_knight.alive"] = True
        candidate_refs["candidate.skills.prowess_raw"] = 0
        selected_refs["selected_enemy_knight.skills.prowess_raw"] = 0
        candidate_refs[
            "derived.candidate_prowess_at_or_below_root_opponent_threshold"
        ] = True
        candidate_refs[
            "derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter"
        ] = True
        offline[
            "derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists"
        ] = require_alive
        offline["derived.qualifying_enemy_knight_exists"] = True

    def _assert_family_effect(
        self, family: dict[str, object], result: dict[str, object]
    ) -> None:
        expected = family["expected"]
        state = result["after_state"]
        if "root_alive" in expected:
            self.assertEqual(state["root"]["alive"], expected["root_alive"])
        if "wounded_rank_raw" in expected:
            self.assertEqual(
                state["root"]["wounded_rank_raw"], expected["wounded_rank_raw"]
            )
        if "trait" in expected:
            self.assertTrue(state["root"]["traits"][expected["trait"]])
        if "enemy_alive" in expected:
            self.assertEqual(
                state["enemy_candidates"][0]["alive"], expected["enemy_alive"]
            )
        if expected.get("commander_detached"):
            self.assertIsNone(state["sides"]["combat_commander_character_id"])
        if expected.get("participant_detached"):
            self.assertNotIn(
                state["scope"]["root_character_id"],
                state["sides"]["combat_membership"],
            )
        if "transition" in expected:
            self.assertEqual(
                result["transition_log"][0]["transition"], expected["transition"]
            )
        if "liege_accolade_progress_raw" in expected:
            self.assertEqual(
                state["root"]["liege_variable_updates"]["accolade_progress"],
                expected["liege_accolade_progress_raw"],
            )
        if "root_variable" in expected:
            self.assertTrue(
                state["root"]["variable_updates"][expected["root_variable"]]
            )


if __name__ == "__main__":
    unittest.main()
