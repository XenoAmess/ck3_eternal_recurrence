from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (
    QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
    is_native_war_step,
    normalize_war_termination_terms,
    parse_query_war_termination_terms_step,
    query_war_termination_terms_step,
)
from xar_autoplayer.bridge.raiktor_surrender_public_aggregate import (
    project_raiktor_surrender_six_domain,
)


WAR_ID = 16_777_290


def _provenance() -> dict[str, str]:
    return {
        "game_version": "1.19.0.6",
        "executable_sha256": (
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
        ),
        "native_reader": "CWar+0x270/+0x290;0x28B1AA0",
        "present_claim_lifecycle": (
            "present_only_vtable_slot_0_delete_flags_0"
        ),
        "claim_script_sha256": (
            "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
        ),
    }


def _available_terms() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "war_id": WAR_ID,
        "casus_belli": {"database_index": 0, "canonical_key": "claim_cb"},
        "supported_slice": "claim_cb_claim_disposition",
        "claimant_character_id": 29_829,
        "target_title_ids": [2_388, 2_389],
        "claims": [
            {
                "title_id": 2_388,
                "present": True,
                "strong": True,
                "implicit": False,
                "state": "strong_explicit",
            },
            {"title_id": 2_389, "present": False, "state": "absent"},
        ],
        "outcomes": {
            "attacker_victory": {
                "declared_title_disposition": (
                    "transfer_to_claimant_via_conquest_claim"
                ),
                "claim_disposition": "resolve_with_add_claim_on_loss",
            },
            "white_peace": {
                "declared_title_disposition": "unchanged",
                "claim_disposition": "retain_and_strengthen_weak",
            },
            "attacker_defeat": {
                "declared_title_disposition": "unchanged",
                "claim_disposition": "remove_declared_target_claims",
            },
        },
        "readiness": {
            "identity_ready": True,
            "targets_ready": True,
            "claim_rows_ready": True,
            "claim_disposition_ready": True,
            "ready": True,
        },
        "provenance": _provenance(),
    }


def _raiktor_provenance() -> dict[str, str]:
    return {
        "game_version": "1.19.0.6",
        "executable_sha256": (
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
        ),
        "native_reader": "CWar+0x270/+0x290;0x28B1AA0",
        "present_claim_lifecycle": (
            "present_only_vtable_slot_0_delete_flags_0"
        ),
        "event_war_script_sha256": (
            "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707"
        ),
        "casus_belli_effects_script_sha256": (
            "9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C"
        ),
        "war_effects_script_sha256": (
            "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"
        ),
        "war_interactions_script_sha256": (
            "5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F"
        ),
        "bookmark_events_script_sha256": (
            "75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF"
        ),
        "truce_observer": (
            "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"
        ),
    }


def _available_raiktor_terms() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "war_id": WAR_ID,
        "casus_belli": {
            "database_index": 409,
            "canonical_key": "raiktor_claim_cb",
        },
        "supported_slice": (
            "raiktor_claim_cb_attacker_defeat_disposition"
        ),
        "claimant_character_id": 41_001,
        "target_title_ids": [1_800],
        "claims": [
            {
                "title_id": 1_800,
                "present": True,
                "strong": True,
                "implicit": False,
                "state": "strong_explicit",
            }
        ],
        "attacker_defeat": {
            "declared_title_disposition": "unchanged",
            "claim_disposition": "remove_declared_target_claims",
        },
        "gold_reparations": {
            "direction": "primary_attacker_to_primary_defender",
            "factor": 3,
            "positive_income_basis": "primary_attacker_yearly_income",
            "fallback_condition": (
                "landless_adventurer_or_nonpositive_monthly_income"
            ),
            "fallback_basis": "primary_attacker_medium_gold_value",
            "defender_culture_multiplier": (
                "2_if_primary_defender_has_more_gold_for_successful_defensive_wars_else_1"
            ),
            "actual_amount_observable": False,
            "attacker_current_gold": None,
            "defender_current_gold": None,
            "attacker_authoritative_monthly_gold_income": None,
            "defender_authoritative_monthly_gold_income": None,
            "actual_transfer": None,
        },
        "attacker_fame": {
            "resource": "prestige",
            "base": "cb_prestige_factor",
            "scale": -10,
            "limit_rule": "loss_capped_at_1000",
            "actual_delta_observable": False,
            "attacker_current_prestige": None,
            "cb_prestige_factor": None,
            "attacker_prestige_delta": None,
        },
        "truce": {
            "direction": "primary_attacker_toward_primary_defender",
            "result": "defeat",
            "evaluated_days_observable": False,
            "evaluated_days": None,
            "actual_expiry_observable": False,
            "expiry_date_raw": None,
        },
        "prisoner_release": {
            "rule": "war_result_primary_and_first_three_heirs",
            "actual_pairs_observable": False,
            "attacker_participant_ids": None,
            "defender_participant_ids": None,
            "attacker_release_candidate_ids": None,
            "defender_release_candidate_ids": None,
            "release_pairs": None,
            "full_participant_scan": None,
            "primary_and_first_three_successors_scanned": None,
        },
        "conditional_favor_hook": {
            "rule": (
                "attacker_on_claimant_if_distinct_and_can_add_favor_hook"
            ),
            "actual_applies_observable": False,
            "claimant_distinct_from_attacker": None,
            "original_visible_root_traversed": None,
            "will_apply": None,
        },
        "attacker_legitimacy_delta": {"raw": 0, "scale": 100_000},
        "attacker_influence_delta": {"raw": 0, "scale": 100_000},
        "hostages_allowed": False,
        "unobserved_dynamic_effects": [
            "actual_gold_transfer",
            "actual_prestige_delta",
            "actual_truce_expiry",
            "actual_prisoner_release_pairs",
            "conditional_favor_hook_application",
            "targeting_faction_discontent_delta",
            "glory_hound_vassal_opinion_rows",
            "antagonistic_clan_vassal_opinion_rows",
            "existing_house_feud_score_delta",
            "attacker_mandala_piety_experience_delta",
            "defender_mandala_serenity",
            "defender_accolade_glory",
            "laamp_actual_settlement_outside_cb_effect",
            "war_bound_army_losses",
        ],
        "readiness": {
            "identity_ready": True,
            "targets_ready": True,
            "claim_rows_ready": True,
            "attacker_defeat_rule_ready": True,
            "static_formula_ready": True,
            "finance_ready": False,
            "gold_ready": False,
            "fame_factor_ready": False,
            "attacker_prestige_delta_ready": False,
            "truce_ready": False,
            "prisoner_release_ready": False,
            "favor_hook_ready": False,
            "war_bound_armies_ready": False,
            "same_frame_stable": False,
            "dynamic_deltas_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "ready": False,
        },
        "provenance": _raiktor_provenance(),
    }


def _available_raiktor_observed_terms() -> dict[str, object]:
    terms = _available_raiktor_terms()
    terms["gold_reparations"].update(
        {
            "actual_amount_observable": True,
            "attacker_current_gold": {
                "character_id": 29_829,
                "value": {"raw": 35_000_000, "scale": 100_000},
            },
            "defender_current_gold": {
                "character_id": 41_002,
                "value": {"raw": 80_000_000, "scale": 100_000},
            },
            "attacker_authoritative_monthly_gold_income": {
                "character_id": 29_829,
                "value": {"raw": 500_001, "scale": 100_000},
            },
            "defender_authoritative_monthly_gold_income": {
                "character_id": 41_002,
                "value": {"raw": 800_000, "scale": 100_000},
            },
            "actual_transfer": {
                "from_character_id": 29_829,
                "to_character_id": 41_002,
                "value": {"raw": 15_000_000, "scale": 100_000},
            },
        }
    )
    terms["attacker_fame"].update(
        {
            "actual_delta_observable": True,
            "attacker_current_prestige": {
                "character_id": 29_829,
                "value": {"raw": 12_345_678, "scale": 100_000},
            },
            "cb_prestige_factor": {"raw": 700_000, "scale": 100_000},
            "attacker_prestige_delta": {
                "character_id": 29_829,
                "value": {"raw": -7_000_000, "scale": 100_000},
            },
        }
    )
    terms["prisoner_release"].update(
        {
            "actual_pairs_observable": True,
            "attacker_participant_ids": [29_829, 30_001],
            "defender_participant_ids": [41_002],
            "attacker_release_candidate_ids": [29_829, 30_003],
            "defender_release_candidate_ids": [41_002],
            "release_pairs": [
                {
                    "jailer_character_id": 41_002,
                    "prisoner_character_id": 30_003,
                    "reason": (
                        "opposite_primary_or_first_three_successors"
                    ),
                }
            ],
            "full_participant_scan": True,
            "primary_and_first_three_successors_scanned": True,
        }
    )
    terms["conditional_favor_hook"].update(
        {
            "actual_applies_observable": True,
            "claimant_distinct_from_attacker": True,
            "original_visible_root_traversed": True,
            "will_apply": True,
        }
    )
    for effect in (
        "actual_gold_transfer",
        "actual_prestige_delta",
        "actual_prisoner_release_pairs",
        "conditional_favor_hook_application",
    ):
        terms["unobserved_dynamic_effects"].remove(effect)
    terms["readiness"].update(
        {
            "finance_ready": True,
            "gold_ready": True,
            "fame_factor_ready": True,
            "attacker_prestige_delta_ready": True,
            "prisoner_release_ready": True,
            "favor_hook_ready": True,
            "same_frame_stable": True,
        }
    )
    return terms


class WarTerminationTermsContractTests(unittest.TestCase):
    def test_public_raiktor_terms_project_four_domains_without_overclaim(
        self,
    ) -> None:
        terms = normalize_war_termination_terms(
            _available_raiktor_observed_terms(), expected_war_id=WAR_ID
        )
        snapshot = {
            "snapshot_id": "native:91",
            "revision": 91,
            "native_revision": 7,
            "date_raw": 53_175_816,
            "paused": True,
            "episode_character_id": 29_829,
            "played_character": {"character_id": 29_829, "alive": True},
            "active_wars": [
                {
                    "war_id": WAR_ID,
                    "player_side": "attacker",
                    "player_is_primary_war_leader": True,
                    "primary_opponent_character_id": 41_002,
                }
            ],
        }

        aggregate = project_raiktor_surrender_six_domain(snapshot, terms)

        self.assertIsInstance(aggregate, dict)
        assert isinstance(aggregate, dict)
        self.assertEqual(aggregate["status"], "incomplete")
        self.assertEqual(
            aggregate["missing_domains"],
            ["truce", "generic_war_bound_current"],
        )
        self.assertTrue(aggregate["readiness"]["gold_ready"])
        self.assertTrue(aggregate["readiness"]["prestige_ready"])
        self.assertTrue(aggregate["readiness"]["prisoner_release_ready"])
        self.assertTrue(aggregate["readiness"]["favor_hook_ready"])
        self.assertFalse(aggregate["readiness"]["truce_ready"])
        self.assertFalse(aggregate["readiness"]["action_terms_ready"])
        self.assertFalse(
            aggregate["readiness"]["automatic_surrender_ready"]
        )

    def test_public_raiktor_projection_does_not_invent_missing_owner(self) -> None:
        terms = normalize_war_termination_terms(
            _available_raiktor_observed_terms(), expected_war_id=WAR_ID
        )
        snapshot = {
            "revision": 91,
            "native_revision": 7,
            "date_raw": 53_175_816,
            "paused": True,
            "episode_character_id": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "active_wars": [],
        }

        self.assertIsNone(
            project_raiktor_surrender_six_domain(snapshot, terms)
        )

    def test_capability_and_literal_are_versioned_and_canonical(self) -> None:
        self.assertEqual(
            QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
            "game.command.query-war-termination-terms-v1-N",
        )
        step = query_war_termination_terms_step(WAR_ID)
        self.assertEqual(step, "query-war-termination-terms-v1-16777290")
        self.assertEqual(parse_query_war_termination_terms_step(step), WAR_ID)
        self.assertTrue(is_native_war_step(step))
        for malformed in (
            "query-war-termination-terms-v1-0",
            "query-war-termination-terms-v1-016777290",
            "query-war-termination-terms-v1-2147483648",
            "query-war-termination-terms-v1-16777290-extra",
            "query-war-termination-terms-v2-16777290",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_war_termination_terms_step(malformed)
                )

    def test_available_claim_slice_normalizes_without_broad_placeholders(
        self,
    ) -> None:
        normalized = normalize_war_termination_terms(
            _available_terms(), expected_war_id=WAR_ID
        )
        self.assertEqual(normalized["status"], "available")
        self.assertTrue(normalized["readiness"]["ready"])
        self.assertEqual(
            normalized["claims"][0]["state"], "strong_explicit"
        )
        self.assertEqual(
            normalized["claims"][1],
            {"title_id": 2_389, "present": False, "state": "absent"},
        )
        for broad_domain in (
            "gold",
            "prestige",
            "truce",
            "prisoners",
            "piety",
            "legitimacy",
        ):
            self.assertNotIn(broad_domain, normalized)

    def test_non_claim_cb_is_a_typed_narrow_unsupported_union(self) -> None:
        raw = {
            "schema_version": 1,
            "status": "unsupported",
            "war_id": WAR_ID,
            "casus_belli": {
                "database_index": 4,
                "canonical_key": "county_conquest_cb",
            },
            "supported_slice": "claim_cb_claim_disposition",
            "reason": "casus_belli_not_claim_cb",
            "readiness": {"ready": False},
            "provenance": _provenance(),
        }
        self.assertEqual(normalize_war_termination_terms(raw), raw)
        self.assertNotIn("claimant_character_id", raw)
        self.assertNotIn("target_title_ids", raw)

    def test_raiktor_surrender_slice_keeps_dynamic_deltas_explicit(self) -> None:
        raw = _available_raiktor_terms()

        normalized = normalize_war_termination_terms(
            raw, expected_war_id=WAR_ID
        )

        self.assertEqual(normalized, raw)
        self.assertFalse(normalized["readiness"]["ready"])
        self.assertFalse(normalized["readiness"]["decision_ready"])
        self.assertFalse(
            normalized["readiness"]["automatic_surrender_ready"]
        )
        self.assertFalse(
            normalized["gold_reparations"]["actual_amount_observable"]
        )
        self.assertEqual(normalized["attacker_fame"]["scale"], -10)
        self.assertFalse(normalized["hostages_allowed"])

    def test_raiktor_surrender_slice_publishes_four_observed_domains_only(
        self,
    ) -> None:
        raw = _available_raiktor_observed_terms()

        normalized = normalize_war_termination_terms(
            raw, expected_war_id=WAR_ID
        )

        self.assertEqual(normalized, raw)
        self.assertTrue(normalized["readiness"]["gold_ready"])
        self.assertTrue(normalized["readiness"]["fame_factor_ready"])
        self.assertTrue(normalized["readiness"]["prisoner_release_ready"])
        self.assertTrue(normalized["readiness"]["favor_hook_ready"])
        self.assertFalse(normalized["readiness"]["truce_ready"])
        self.assertFalse(normalized["readiness"]["war_bound_armies_ready"])
        self.assertFalse(normalized["readiness"]["decision_ready"])
        self.assertFalse(
            normalized["readiness"]["automatic_surrender_ready"]
        )
        self.assertEqual(
            normalized["unobserved_dynamic_effects"][:2],
            [
                "actual_truce_expiry",
                "targeting_faction_discontent_delta",
            ],
        )

    def test_raiktor_surrender_slice_accepts_evaluated_truce_duration_only(
        self,
    ) -> None:
        raw = _available_raiktor_observed_terms()
        raw["truce"].update(
            {
                "evaluated_days_observable": True,
                "evaluated_days": 1_825,
            }
        )
        raw["readiness"]["truce_ready"] = True

        normalized = normalize_war_termination_terms(
            raw, expected_war_id=WAR_ID
        )

        self.assertEqual(normalized, raw)
        self.assertTrue(normalized["readiness"]["truce_ready"])
        self.assertEqual(normalized["truce"]["evaluated_days"], 1_825)
        self.assertFalse(normalized["truce"]["actual_expiry_observable"])
        self.assertIsNone(normalized["truce"]["expiry_date_raw"])
        self.assertIn(
            "actual_truce_expiry", normalized["unobserved_dynamic_effects"]
        )

    def test_raiktor_surrender_slice_rejects_truce_expiry_or_duration_drift(
        self,
    ) -> None:
        expiry = _available_raiktor_terms()
        expiry["truce"]["expiry_date_raw"] = 53_177_641
        duration_gate = _available_raiktor_terms()
        duration_gate["truce"]["evaluated_days_observable"] = True
        for raw in (expiry, duration_gate):
            with self.subTest(raw=copy.deepcopy(raw)):
                with self.assertRaises(ValueError):
                    normalize_war_termination_terms(raw)

    def test_raiktor_surrender_slice_rejects_observed_domain_drift(
        self,
    ) -> None:
        cases: list[dict[str, object]] = []
        missing_gold_value = _available_raiktor_observed_terms()
        missing_gold_value["gold_reparations"]["actual_transfer"] = None
        cases.append(missing_gold_value)
        reversed_transfer = _available_raiktor_observed_terms()
        reversed_transfer["gold_reparations"]["actual_transfer"][
            "from_character_id"
        ] = 41_002
        cases.append(reversed_transfer)
        wrong_prestige_formula = _available_raiktor_observed_terms()
        wrong_prestige_formula["attacker_fame"]["attacker_prestige_delta"][
            "value"
        ]["raw"] = -6_999_999
        cases.append(wrong_prestige_formula)
        wrong_prisoner_side = _available_raiktor_observed_terms()
        wrong_prisoner_side["prisoner_release"]["release_pairs"][0][
            "jailer_character_id"
        ] = 29_829
        cases.append(wrong_prisoner_side)
        overlapping_successor = _available_raiktor_observed_terms()
        overlapping_successor["prisoner_release"][
            "defender_release_candidate_ids"
        ].append(30_003)
        cases.append(overlapping_successor)
        wrong_favor_gate = _available_raiktor_observed_terms()
        wrong_favor_gate["conditional_favor_hook"][
            "claimant_distinct_from_attacker"
        ] = False
        cases.append(wrong_favor_gate)
        fabricated_full_readiness = _available_raiktor_observed_terms()
        fabricated_full_readiness["readiness"]["decision_ready"] = True
        cases.append(fabricated_full_readiness)
        for raw in cases:
            with self.subTest(raw=copy.deepcopy(raw)):
                with self.assertRaises(ValueError):
                    normalize_war_termination_terms(raw)

    def test_raiktor_surrender_slice_rejects_formula_or_readiness_drift(
        self,
    ) -> None:
        cases: list[dict[str, object]] = []
        wrong_cb = _available_raiktor_terms()
        wrong_cb["casus_belli"]["canonical_key"] = "claim_cb"
        cases.append(wrong_cb)
        fabricated_amount = _available_raiktor_terms()
        fabricated_amount["gold_reparations"][
            "actual_amount_observable"
        ] = True
        cases.append(fabricated_amount)
        auto_ready = _available_raiktor_terms()
        auto_ready["readiness"]["automatic_surrender_ready"] = True
        cases.append(auto_ready)
        hostages = _available_raiktor_terms()
        hostages["hostages_allowed"] = True
        cases.append(hostages)
        missing_unknown = _available_raiktor_terms()
        missing_unknown["unobserved_dynamic_effects"].pop()
        cases.append(missing_unknown)
        wrong_source = _available_raiktor_terms()
        wrong_source["provenance"]["event_war_script_sha256"] = "0" * 64
        cases.append(wrong_source)
        for raw in cases:
            with self.subTest(raw=copy.deepcopy(raw)):
                with self.assertRaises(ValueError):
                    normalize_war_termination_terms(raw)

    def test_strict_union_rejects_inconsistent_or_decorated_claims(self) -> None:
        cases: list[dict[str, object]] = []
        decorated = _available_terms()
        decorated["gold"] = None
        cases.append(decorated)
        duplicate = _available_terms()
        duplicate["target_title_ids"] = [2_388, 2_388]
        cases.append(duplicate)
        reordered = _available_terms()
        reordered["claims"] = list(reversed(reordered["claims"]))
        cases.append(reordered)
        bad_state = _available_terms()
        bad_state["claims"][0]["state"] = "weak_explicit"
        cases.append(bad_state)
        absent_with_uninitialized_fields = _available_terms()
        absent_with_uninitialized_fields["claims"][1]["strong"] = False
        cases.append(absent_with_uninitialized_fields)
        drifted_outcome = _available_terms()
        drifted_outcome["outcomes"]["white_peace"][
            "claim_disposition"
        ] = "retain"
        cases.append(drifted_outcome)
        drifted_lifecycle = _available_terms()
        drifted_lifecycle["provenance"]["present_claim_lifecycle"] = (
            "not_destroyed"
        )
        cases.append(drifted_lifecycle)
        wrong_war = _available_terms()
        wrong_war["war_id"] = WAR_ID + 1
        cases.append(wrong_war)
        for raw in cases:
            with self.subTest(raw=copy.deepcopy(raw)):
                with self.assertRaises(ValueError):
                    normalize_war_termination_terms(
                        raw, expected_war_id=WAR_ID
                    )


if __name__ == "__main__":
    unittest.main()
