"""One synthetic production-carrier case, without a native parity claim."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.simulation.battle_phase_event_character_seam_12003 import (
    CharacterPhaseEventInputs12003,
    RootCharacterLocationScope12003,
    execute_selected_character_phase_event_12003,
    read_current_character_fields_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    compute_six_skill_cache_from_native_inputs_12003,
)


ROOT = 29829
DATE = 53178264
REVISION = 42


def _source():
    return {
        "combat_id": 335544325,
        "snapshot_revision": REVISION,
        "observed_date_raw": DATE,
        "provenance": "synthetic_source_conditioned_current_attribute_fixture_not_live",
    }


def _selected_context():
    return {
        "root_character_id": ROOT,
        "root_source_army_id": 83886341,
        "root_source_regiment_id": 901,
        "phase_roles": ["knight"],
        "combat_side_index": 0,
        "enemy_side_index": 1,
        "native_state_refs": {},
        "offline_state_refs": {
            "root.exists": True,
            "root.alive": True,
            "root.is_incapable": False,
            "root.traits.incapable": False,
            "root.skills.prowess_raw": 0,
            "root.traits.wounded.rank_raw": 0,
            "root.traits_and_culture_for_blademaster": {
                "lifestyle_blademaster": False,
                "lifestyle_blademaster_xp_raw": 0,
            },
            "combat_side.character_membership": [ROOT],
            "enemy_side.character_membership": [],
            "combat_side.ordered_enemy_knights": [],
            "combat_side.commander": None,
        },
        "candidate_rows": [],
    }


def _raw_inputs():
    return {
        "status": "available",
        "raw_numeric_inputs_ready": True,
        "character_id": ROOT,
        "context_source": "model_inline",
        "unavailable_reason": None,
        "base_points": [-3, 7, 4, 9, 8, 200],
        "caps": [-7, -5, 120, 120, 120, 120],
        "prowess_adjustment": -20,
        "scratch_present": True,
        "category_counts": [0, 0, 0, 0],
        "scratch_factor_numerator": 0,
        "scratch_factor_denominator": 1,
        "context": {
            "aggregate_properties": {"keys_u16": [], "values_q64": [], "count": 0},
            "weighted_rows": [],
            "weighted_count": 0,
        },
    }


def _frame(raw_inputs, *, current_prowess=0):
    return {
        "schema_version": 1,
        "contract_stage": BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
        "status": "available",
        "unavailable_reason": None,
        "battle_terminal_transition_ready": False,
        "snapshot_revision": REVISION,
        "observed_date_raw": DATE,
        "prior_combat_id": -1,
        "subject_public_cunit_id": -1,
        "terminal_journal": {
            "requested_after_sequence": None,
            "oldest_available_sequence": 0,
            "latest_sequence": 0,
            "event_sequence": None,
            "event_status": "not_observed",
        },
        "prior": None,
        "removal": None,
        "subject": None,
        "successor": None,
        "character_observations": [{
            "character_id": ROOT,
            "status": "none",
            "actual_jailer_character_id": -1,
            "alive": True,
            "current_person_state": {
                "scope": "current_character",
                "effective_prowess": {
                    "status": "available",
                    "points": current_prowess,
                    "unavailable_reason": None,
                },
                "injury_traits": {
                    "status": "available",
                    "flags": {
                        "wounded_1": False,
                        "wounded_2": False,
                        "wounded_3": False,
                        "maimed": False,
                        "one_legged": False,
                        "one_eyed": False,
                        "disfigured": False,
                        "incapable": False,
                    },
                    "wounded_rank": 0,
                    "unavailable_reason": None,
                    "wounded_rank_unavailable_reason": None,
                },
                "raw_numeric_inputs": raw_inputs,
            },
        }],
    }


def _normalize(frame):
    return normalize_battle_terminal_transition_v1(
        frame,
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=DATE,
        expected_snapshot_revision=REVISION,
        expected_character_ids=[ROOT],
    )


class BattleTraitNumericInputs12003ProductionFixtureTests(unittest.TestCase):
    captured_results = []

    def test_selected_request_uses_same_query_native_numeric_carrier(self):
        frame = _frame(_raw_inputs())
        original_frame = deepcopy(frame)
        normalized = _normalize(frame)
        context = _selected_context()
        original_context = deepcopy(context)
        source = _source()

        # Existing production request/reader, with explicit current observation.
        primary = execute_selected_character_phase_event_12003(
            context,
            script_outcomes=(),
            source_context=source,
            inputs=CharacterPhaseEventInputs12003(
                root_location_scope=RootCharacterLocationScope12003(
                    ROOT, 4100, "synthetic_current_root_location_not_combat_province"),
                current_person_observation=normalized,
                observation_source=source,
            ),
        )
        self.assertTrue(primary.event_execution_consumed)
        self.assertEqual(primary.character_primary_deltas[0]["character_id"], ROOT)
        self.assertEqual(primary.character_primary_deltas[0]["field"], "traits.incapable")
        self.assertIs(primary.character_primary_deltas[0]["before"], False)
        self.assertIs(primary.character_primary_deltas[0]["after"], True)
        self.assertEqual(primary.current_person_reader.effective_prowess_points, 0)
        self.assertFalse(primary.condition_feedback_ready)

        # One actual production-normalized leaf reaches the new numeric kernel.
        observed_row = normalized["character_observations"][0]
        native_inputs = observed_row["current_person_state"]["raw_numeric_inputs"]
        computed = compute_six_skill_cache_from_native_inputs_12003(native_inputs)
        self.assertTrue(computed.calculation_ready)
        self.assertEqual(computed.character_id, ROOT)
        self.assertEqual(observed_row["character_id"], ROOT)
        self.assertEqual(native_inputs["character_id"], ROOT)
        self.assertEqual(computed.raw_points, (-3, 7, 4, 9, 8, 200))
        self.assertEqual(computed.first_clipped_points, (0, -5, 4, 9, 8, 120))
        self.assertEqual(computed.final_cache_points, (0, -5, 4, 9, 8, 100))
        self.assertFalse(computed.missing_inputs)
        self.assertIn("input_source", computed.ledger)
        # raw-negative writes 0 even with cap -7; raw-positive/cap -5 stays -5.
        # Prowess first clips 200 to 120, then applies F0=-20 and clips to 100.
        self.assertNotEqual(computed.final_cache_points[5], 120)
        # A default cap100 would incorrectly return 80 for the same adjustment.
        self.assertNotEqual(computed.final_cache_points[5], 80)

        # Computation is neither a fresh current observation nor Entry refresh.
        self.assertEqual(primary.current_person_reader.effective_prowess_points, 0)
        self.assertEqual(primary.execution["after_state"]["root"]["prowess_raw"], 0)
        self.assertEqual(normalized["observed_date_raw"], DATE)
        self.assertEqual(normalized["snapshot_revision"], REVISION)
        self.assertFalse(normalized["battle_terminal_transition_ready"])
        gap_kinds = {gap.kind for gap in primary.typed_callback_gaps}
        self.assertIn("cached_stats_and_role_callbacks", gap_kinds)
        self.assertFalse(primary.full_script_feedback_ready)
        self.assertFalse(primary.complete_transition)

        # The same actor's current getter also permits signed negative values.
        negative_frame = _frame(_raw_inputs(), current_prowess=-3)
        negative_normalized = _normalize(negative_frame)
        negative_reader = read_current_character_fields_12003(
            negative_normalized, character_id=ROOT, source_context=source)
        self.assertEqual(negative_reader.effective_prowess_points, -3)
        self.assertEqual(negative_reader.character_id, ROOT)

        # A read failure keeps the affected operand null; known slots survive.
        failed_frame = deepcopy(frame)
        failed_state = failed_frame["character_observations"][0]["current_person_state"]
        failed_state["effective_prowess"] = {
            "status": "unavailable",
            "points": None,
            "unavailable_reason": "current_effective_prowess_read_failed",
        }
        failed_state["raw_numeric_inputs"]["base_points"][5] = None
        failed_state["raw_numeric_inputs"].update(
            status="partial", raw_numeric_inputs_ready=False,
            unavailable_reason="raw_skill5_read_failed")
        failed_normalized = _normalize(failed_frame)
        failed_leaf = failed_normalized["character_observations"][0]["current_person_state"]["raw_numeric_inputs"]
        partial = compute_six_skill_cache_from_native_inputs_12003(failed_leaf)
        failed_reader = read_current_character_fields_12003(
            failed_normalized, character_id=ROOT, source_context=source)
        self.assertIsNone(failed_leaf["base_points"][5])
        self.assertIsNone(failed_reader.effective_prowess_points)
        self.assertFalse(partial.calculation_ready)
        self.assertTrue(partial.missing_inputs)
        self.assertEqual(partial.character_id, ROOT)
        self.assertEqual(partial.raw_points, (-3, 7, 4, 9, 8, None))
        self.assertEqual(partial.final_cache_points, (0, -5, 4, 9, 8, None))
        self.assertEqual(failed_normalized["observed_date_raw"], DATE)
        self.assertEqual(failed_normalized["snapshot_revision"], REVISION)
        self.assertEqual(frame, original_frame)
        self.assertEqual(context, original_context)

        self.__class__.captured_results.append({
            "case": "selected_incapable_request_same_query_raw_inputs_two_stage_ec",
            "character_id": ROOT,
            "source_coordinate": {"snapshot_revision": REVISION, "observed_date_raw": DATE},
            "primary_trait": {"before": False, "after": True},
            "observed_current_ec_zero": primary.current_person_reader.effective_prowess_points,
            "observed_current_ec_negative": negative_reader.effective_prowess_points,
            "raw_points": list(computed.raw_points),
            "first_clipped_points": list(computed.first_clipped_points),
            "modeled_final_cache_points": list(computed.final_cache_points),
            "caps": native_inputs["caps"],
            "prowess_adjustment": native_inputs["prowess_adjustment"],
            "one_clamp_counterexample": 120,
            "default_100_cap_counterexample": 80,
            "input_source": deepcopy(computed.ledger["input_source"]),
            "read_failed_ec": failed_reader.effective_prowess_points,
            "partial_raw_points": list(partial.raw_points),
            "partial_final_cache_points": list(partial.final_cache_points),
            "partial_missing_inputs": list(partial.missing_inputs),
            "remaining_primary_callback_gaps": sorted(gap_kinds),
            "primary_feedback_ready": primary.condition_feedback_ready,
            "numeric_calculation_ready": computed.calculation_ready,
            "fresh_frame_created": False,
            "entry_cache_readiness_claimed": False,
            "synthetic_source_shaped_operands": True,
            "native_parity_claimed": False,
        })
