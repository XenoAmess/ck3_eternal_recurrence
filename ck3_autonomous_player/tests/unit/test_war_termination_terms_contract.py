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


class WarTerminationTermsContractTests(unittest.TestCase):
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
