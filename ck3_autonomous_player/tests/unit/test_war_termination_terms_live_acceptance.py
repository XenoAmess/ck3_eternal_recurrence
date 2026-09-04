"""Pure checks for the Raiktor terms live-acceptance harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_war_termination_terms_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_war_termination_terms_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def _payload(
    *, evaluated_days_observable: bool = True, expiry_date_raw: object = None
) -> dict[str, object]:
    terms = {
        "status": "available",
        "war_id": 50_331_699,
        "casus_belli": {"canonical_key": "raiktor_claim_cb", "database_index": 27},
        "supported_slice": "raiktor_claim_cb_attacker_defeat_disposition",
        "claimant_character_id": 16_826_697,
        "target_title_ids": [1207],
        "gold_reparations": {"actual_amount_observable": True},
        "attacker_fame": {"actual_delta_observable": True},
        "prisoner_release": {"actual_pairs_observable": True},
        "conditional_favor_hook": {
            "actual_applies_observable": True,
            "claimant_distinct_from_attacker": True,
            "original_visible_root_traversed": True,
            "will_apply": True,
        },
        "truce": {
            "direction": "primary_attacker_toward_primary_defender",
            "result": "defeat",
            "evaluated_days_observable": evaluated_days_observable,
            "evaluated_days": 1_825 if evaluated_days_observable else None,
            "actual_expiry_observable": False,
            "expiry_date_raw": expiry_date_raw,
        },
        "readiness": {
            "finance_ready": True,
            "gold_ready": True,
            "fame_factor_ready": True,
            "attacker_prestige_delta_ready": True,
            "prisoner_release_ready": True,
            "favor_hook_ready": True,
            "truce_ready": evaluated_days_observable,
            "war_bound_armies_ready": False,
            "same_frame_stable": True,
            "dynamic_deltas_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "ready": False,
        },
        "unobserved_dynamic_effects": list(
            HARNESS.EXPECTED_UNOBSERVED_AFTER_FOUR_DOMAINS
        ),
    }
    return {"war_termination_terms": terms}


class WarTerminationTermsLiveAcceptanceChecksTests(unittest.TestCase):
    def test_product_tree_sha256_comparison_is_case_insensitive(self) -> None:
        uppercase = "F4E63FFFA6CF9332BA41EB5985D1CB72F280F4BF375A15473F4638F43CF944BE"
        self.assertTrue(
            HARNESS._sha256_equal(
                uppercase.lower(),
                uppercase,
                "production-tree SHA-256",
            )
        )
        self.assertFalse(
            HARNESS._sha256_equal(
                "0" * 64,
                uppercase,
                "production-tree SHA-256",
            )
        )

    def test_exact_build_proof_distinguishes_template_and_concrete_step(self) -> None:
        capability = HARNESS.QUERY_WAR_TERMINATION_TERMS_CAPABILITY
        base = {
            "bridge_capabilities": [capability],
            "diagnostics": {
                "hello": {
                    "expected_ck3_version": HARNESS.EXPECTED_GAME_VERSION,
                    "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                    "game_adapter_status": "ready",
                    "ck3_build_match": True,
                    "expected_ck3_sha256": HARNESS.EXPECTED_EXECUTABLE_SHA256,
                    "capabilities": [capability],
                }
            },
        }
        template = dict(base, action_steps=["query-war-termination-terms-v1-N"])
        proof = HARNESS._exact_build_proof(
            template,
            managed_executable_sha256=HARNESS.EXPECTED_EXECUTABLE_SHA256,
            war_id=50_331_699,
        )
        self.assertFalse(proof["checks"]["action_step_family"])
        self.assertEqual(
            proof["observed_action_steps"], ["query-war-termination-terms-v1-N"]
        )

        concrete = dict(
            base,
            action_steps=["query-war-termination-terms-v1-50331699"],
        )
        proof = HARNESS._exact_build_proof(
            concrete,
            managed_executable_sha256=HARNESS.EXPECTED_EXECUTABLE_SHA256,
            war_id=50_331_699,
        )
        self.assertTrue(proof["checks"]["action_step_family"])
        self.assertEqual(
            proof["observed_action_steps"],
            ["query-war-termination-terms-v1-50331699"],
        )

    def test_duration_is_observed_while_expiry_stays_unobserved(self) -> None:
        checks = HARNESS._terms_checks(_payload(), war_id=50_331_699)
        self.assertTrue(checks["truce_duration_observed"])
        self.assertTrue(checks["truce_expiry_unobserved"])
        self.assertNotIn("truce_still_unobserved", checks)

    def test_missing_duration_or_invented_expiry_fails_distinct_checks(self) -> None:
        missing = HARNESS._terms_checks(
            _payload(evaluated_days_observable=False), war_id=50_331_699
        )
        self.assertFalse(missing["truce_duration_observed"])
        self.assertTrue(missing["truce_expiry_unobserved"])

        invented = HARNESS._terms_checks(
            _payload(expiry_date_raw=53_219_616), war_id=50_331_699
        )
        self.assertTrue(invented["truce_duration_observed"])
        self.assertFalse(invented["truce_expiry_unobserved"])


if __name__ == "__main__":
    unittest.main()
