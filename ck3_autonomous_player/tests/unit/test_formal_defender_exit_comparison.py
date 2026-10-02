"""Synthetic contract tests; no H2743 material terms or live risk are implied."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.formal_defender_exit_comparison import (  # noqa: E402
    compare_defender_dejure_surrender_cost_to_continuation_risk,
    formal_surrender_action_preconditions,
)


SHA = "A" * 64
RESOURCES = (
    "gold", "prestige", "prestige_experience", "piety",
    "piety_experience", "legitimacy", "stress",
)


def _bundle() -> tuple[dict, dict, dict, dict]:
    frame = {
        "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
        "date_raw": 53217264, "episode_run_id": "synthetic-episode",
        "connection_generation": 1, "checkpoint_sha256": SHA,
        "war_id": 16777231, "primary_attacker_character_id": 30097,
        "primary_defender_character_id": 29829,
        "casus_belli_key": "individual_county_de_jure_cb",
        "casus_belli_database_index": 17, "target_title_ids": [2128],
    }
    option = {
        "schema": "xar.ck3.defender-dejure-exit-option.v1", "frame": copy.deepcopy(frame),
        "outcome": "surrender", "absolute_outcome": "attacker_victory",
        "source": "native", "native_legal_now": True,
        "recipient_accepts_now": True, "query_sequence": 1,
        "evidence_sha256": SHA,
    }
    deltas = [
        {"character_id": character_id, "resource": resource, "raw": 0, "scale": 100_000}
        for character_id in (29829, 30097) for resource in RESOURCES
    ]
    bounds = [
        {"character_id": character_id, "resource": resource,
         "lower_raw": -100, "upper_raw": 100, "scale": 100_000}
        for character_id in (29829, 30097) for resource in RESOURCES
    ]
    next(row for row in deltas if row["character_id"] == 29829 and row["resource"] == "gold")["raw"] = -300
    next(row for row in bounds if row["character_id"] == 29829 and row["resource"] == "gold").update(
        lower_raw=-600, upper_raw=-100
    )
    next(row for row in deltas if row["character_id"] == 29829 and row["resource"] == "prestige")["raw"] = -1_000
    next(row for row in bounds if row["character_id"] == 29829 and row["resource"] == "prestige").update(
        lower_raw=-500, upper_raw=-100
    )
    terms = {
        "schema": "xar.ck3.defender-dejure-exit-terms-complete.v1",
        "frame": copy.deepcopy(frame), "outcome": "surrender",
        "material_complete": True, "runtime_target_scope_title_id": 2128,
        "cb_prestige_factor": {"raw": 300_000, "scale": 100_000, "evidence_sha256": SHA},
        "title_vassal_delta": {
            "status": "complete", "evidence_sha256": SHA,
            "operations": [{"kind": "title_holder", "entity_id": 2128,
                            "before_id": 33435, "after_id": 30097}],
        },
        "signed_resource_delta": deltas,
        "directed_truce": {
            "owner_character_id": 30097, "toward_character_id": 29829,
            "days": 730, "expiry_date_raw": 53217264 + 730,
            "evidence_sha256": SHA,
        },
        "conditional_resource_effects": {
            "status": "complete", "effect_tree_sha256": SHA,
            "covered_effect_node_ids": ["synthetic-complete-effect-tree"],
            "unresolved_effect_node_ids": [], "evidence_sha256": SHA,
        },
        "evidence_sha256": SHA,
    }
    risk = {
        "schema": "xar.ck3.defender-dejure-continuation-risk.v1",
        "frame": copy.deepcopy(frame), "status": "bounded_complete",
        "horizon_days": 15, "resource_delta_bounds": bounds,
        "title_vassal_risk": {
            "status": "bounded_complete", "possible_operations": [],
            "evidence_sha256": SHA,
        },
        "war_score_bounds": {"lower": -35, "upper": -10},
        "contact_partition": {
            "status": "complete", "participant_army_ids": [83886367, 50331920],
            "evidence_sha256": SHA,
        },
        "evidence_sha256": SHA,
    }
    return frame, option, terms, risk


class FormalDefenderExitComparisonTests(unittest.TestCase):
    def test_complete_synthetic_bundle_is_only_componentwise_comparable(self) -> None:
        frame, option, terms, risk = _bundle()
        result = compare_defender_dejure_surrender_cost_to_continuation_risk(
            frame, option, terms, risk
        )
        self.assertEqual(result["status"], "componentwise_comparable_no_policy")
        self.assertEqual(len(result["comparison"]["resource_delta_interval_relations"]), 14)
        relations = {
            (row["character_id"], row["resource"]): row["relation"]
            for row in result["comparison"]["resource_delta_interval_relations"]
        }
        self.assertEqual(relations[29829, "gold"], "within_continuation_range")
        self.assertEqual(relations[29829, "prestige"], "below_continuation_range")
        self.assertIsNone(result["comparison"]["aggregate_preference"])
        self.assertIsNone(result["recommended_outcome"])
        self.assertIsNone(result["action_literal"])
        self.assertEqual(
            result["comparison_sha256"],
            compare_defender_dejure_surrender_cost_to_continuation_risk(
                frame, option, terms, risk
            )["comparison_sha256"],
        )
        terms["title_vassal_delta"]["operations"][0]["after_id"] = 1
        self.assertEqual(result["comparison"]["exit_title_vassal_operations"][0]["after_id"], 30097)

    def test_every_required_material_or_risk_domain_fails_closed(self) -> None:
        changes = (
            ("target", lambda option, terms, risk: terms["title_vassal_delta"].update(operations=[])),
            ("factor", lambda option, terms, risk: terms.update(cb_prestige_factor=None)),
            ("truce", lambda option, terms, risk: terms.update(directed_truce=None)),
            ("conditional", lambda option, terms, risk: terms["conditional_resource_effects"].update(unresolved_effect_node_ids=["unknown"])),
            ("resources", lambda option, terms, risk: terms.update(signed_resource_delta=[])),
            ("risk", lambda option, terms, risk: risk.update(resource_delta_bounds=[])),
            ("contact", lambda option, terms, risk: risk["contact_partition"].update(status="unavailable")),
            ("button", lambda option, terms, risk: option.update(native_legal_now=False)),
            ("recipient", lambda option, terms, risk: option.update(recipient_accepts_now=False)),
        )
        for name, change in changes:
            with self.subTest(domain=name):
                frame, option, terms, risk = _bundle()
                change(option, terms, risk)
                result = compare_defender_dejure_surrender_cost_to_continuation_risk(
                    frame, option, terms, risk
                )
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["comparison"])
                self.assertIsNone(result["action_literal"])

    def test_war_party_and_revision_drift_are_rejected(self) -> None:
        for domain, value in (
            ("war_id", 16777232),
            ("primary_attacker_character_id", 30098),
            ("primary_defender_character_id", 29830),
            ("native_revision", 4),
            ("date_raw", 53217265),
        ):
            with self.subTest(domain=domain):
                frame, option, terms, risk = _bundle()
                terms["frame"][domain] = value
                result = compare_defender_dejure_surrender_cost_to_continuation_risk(
                    frame, option, terms, risk
                )
                self.assertEqual(result["reason"], "terms_frame_mismatch")
        frame, option, terms, risk = _bundle()
        option["frame"]["war_id"] += 1
        self.assertEqual(
            compare_defender_dejure_surrender_cost_to_continuation_risk(
                frame, option, terms, risk
            )["reason"], "option_frame_mismatch",
        )
        frame, option, terms, risk = _bundle()
        risk["frame"]["native_revision"] += 1
        self.assertEqual(
            compare_defender_dejure_surrender_cost_to_continuation_risk(
                frame, option, terms, risk
            )["reason"], "continuation_frame_mismatch",
        )

    def test_malformed_nested_types_and_v1_baseline_never_launder(self) -> None:
        frame, option, terms, risk = _bundle()
        terms["title_vassal_delta"]["operations"][0]["kind"] = []
        self.assertEqual(
            compare_defender_dejure_surrender_cost_to_continuation_risk(
                frame, option, terms, risk
            )["status"], "unavailable",
        )
        frame, option, terms, risk = _bundle()
        terms["material_complete"] = False
        terms["signed_resource_delta"] = None
        self.assertEqual(
            compare_defender_dejure_surrender_cost_to_continuation_risk(
                frame, option, terms, risk
            )["status"], "unavailable",
        )

    def test_formal_action_contract_never_enables_submission(self) -> None:
        frame, option, terms, risk = _bundle()
        comparison = compare_defender_dejure_surrender_cost_to_continuation_risk(
            frame, option, terms, risk
        )
        self.assertEqual(
            formal_surrender_action_preconditions(comparison, None, None)["reason"],
            "documented_policy_selection_missing_or_unbound",
        )
        selection = {
            "schema": "xar.ck3.formal-exit-policy-selection.v1",
            "frame": copy.deepcopy(frame),
            "comparison_sha256": comparison["comparison_sha256"],
            "selected_outcome": "surrender", "policy_document_sha256": SHA,
            "risk_contract_sha256": SHA,
        }
        authority = {
            "schema": "xar.ck3.exact-checkpoint-exit-authority.v1",
            "frame": copy.deepcopy(frame),
            "comparison_sha256": comparison["comparison_sha256"],
            "checkpoint_sha256": frame["checkpoint_sha256"],
            "outcome": "surrender", "scope": "one_exact_checkpoint",
            "authority_id": "synthetic-only", "consumed": False,
        }
        result = formal_surrender_action_preconditions(
            comparison, selection, authority
        )
        self.assertEqual(result["status"], "structural_prerequisites_present_submission_disabled")
        self.assertTrue(result["structural_prerequisites_present"])
        self.assertFalse(result["submission_enabled"])
        self.assertFalse(result["external_authority_verified"])
        self.assertIsNone(result["action_literal"])
        altered = copy.deepcopy(comparison)
        altered["comparison"]["horizon_days"] += 1
        self.assertEqual(
            formal_surrender_action_preconditions(altered, selection, authority)["reason"],
            "comparison_binding_invalid",
        )
        authority["frame"]["war_id"] += 1
        self.assertEqual(
            formal_surrender_action_preconditions(comparison, selection, authority)["reason"],
            "exact_checkpoint_authority_missing_or_unbound",
        )


if __name__ == "__main__":
    unittest.main()
