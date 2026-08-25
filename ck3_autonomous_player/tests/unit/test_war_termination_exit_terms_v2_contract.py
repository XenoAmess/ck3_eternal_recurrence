from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_exit_terms_contract import (
    QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY,
    WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED,
    normalize_war_termination_exit_terms,
    parse_query_war_termination_exit_terms_step,
    query_war_termination_exit_terms_step,
)


FIXTURE = (
    ROOT / "tests" / "fixtures"
    / "war_termination_exit_terms_v2_synthetic.json"
)
LIVE_WAR_ID = 16_777_290
LIVE_TITLE_ID = 2_388


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class WarTerminationExitTermsV2ContractTests(unittest.TestCase):
    def test_capability_and_literal_are_versioned_and_canonical(self) -> None:
        self.assertFalse(WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED)
        self.assertEqual(
            QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY,
            "game.command.query-war-termination-exit-terms-v2-N",
        )
        step = query_war_termination_exit_terms_step(16_777_300)
        self.assertEqual(
            step, "query-war-termination-exit-terms-v2-16777300"
        )
        self.assertEqual(
            parse_query_war_termination_exit_terms_step(step), 16_777_300
        )
        for malformed in (
            "query-war-termination-exit-terms-v2-0",
            "query-war-termination-exit-terms-v2-016777300",
            "query-war-termination-exit-terms-v2-2147483648",
            "query-war-termination-exit-terms-v2-16777300-extra",
            "query-war-termination-exit-terms-v1-16777300",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_war_termination_exit_terms_step(malformed)
                )

    def test_synthetic_available_fixture_round_trips(self) -> None:
        raw = _fixture()
        normalized = normalize_war_termination_exit_terms(
            raw, expected_war_id=16_777_300
        )
        self.assertEqual(normalized, raw)
        self.assertTrue(normalized["readiness"]["exit_terms_ready"])
        self.assertEqual(
            len(
                normalized["outcomes"]["attacker_defeat"]
                ["primary_resource_deltas"]["values"]
            ),
            12,
        )
        self.assertEqual(
            len(normalized["primary_resource_balances"]["values"]), 14
        )
        self.assertEqual(
            len(normalized["primary_monthly_gold_income"]["values"]), 2
        )
        self.assertTrue(
            normalized["outcomes"]["white_peace"]
            ["recipient_response"]["would_accept_now"]
        )
        self.assertNotEqual(normalized["war_id"], LIVE_WAR_ID)
        self.assertNotIn(LIVE_TITLE_ID, normalized["target_title_ids"])

    def test_provenance_hashes_the_frozen_wire_descriptor(self) -> None:
        descriptor = (
            ROOT
            / "tests"
            / "fixtures"
            / "war_termination_exit_terms_v2_contract.txt"
        )
        digest = hashlib.sha256(descriptor.read_bytes()).hexdigest().upper()
        self.assertEqual(
            digest, _fixture()["provenance"]["native_contract_sha256"]
        )

    def test_white_peace_disposition_tracks_observed_claim_strength(self) -> None:
        raw = _fixture()
        raw["claims"][0]["strong"] = True
        raw["claims"][0]["state"] = "strong_explicit"
        raw["outcomes"]["white_peace"]["claim_disposition"] = {
            "declared_title_disposition": "unchanged",
            "claim_disposition": (
                "retain_no_strength_change_already_strong"
            ),
        }
        normalized = normalize_war_termination_exit_terms(raw)
        self.assertEqual(
            normalized["outcomes"]["white_peace"]["claim_disposition"]
            ["claim_disposition"],
            "retain_no_strength_change_already_strong",
        )

    def test_complete_union_rejects_partial_or_inconsistent_domains(
        self,
    ) -> None:
        cases: list[tuple[str, dict[str, object]]] = []

        partial = _fixture()
        partial["status"] = "partial"
        cases.append(("partial", partial))

        decorated = _fixture()
        decorated["unknown_fields"] = []
        cases.append(("decorated", decorated))

        readiness_false = _fixture()
        readiness_false["readiness"]["exit_terms_ready"] = False
        cases.append(("readiness_false", readiness_false))

        missing_resource = _fixture()
        missing_resource["outcomes"]["white_peace"][
            "primary_resource_deltas"
        ]["values"].pop()
        cases.append(("missing_resource", missing_resource))

        missing_balance = _fixture()
        missing_balance["primary_resource_balances"]["values"].pop()
        cases.append(("missing_balance", missing_balance))

        missing_income = _fixture()
        missing_income["primary_monthly_gold_income"]["values"].pop()
        cases.append(("missing_income", missing_income))

        wrong_income_order = _fixture()
        income_rows = wrong_income_order[
            "primary_monthly_gold_income"
        ]["values"]
        income_rows[0], income_rows[1] = income_rows[1], income_rows[0]
        cases.append(("wrong_income_order", wrong_income_order))

        reordered_resource = _fixture()
        rows = reordered_resource["outcomes"]["attacker_defeat"][
            "primary_resource_deltas"
        ]["values"]
        rows[0], rows[1] = rows[1], rows[0]
        cases.append(("reordered_resource", reordered_resource))

        wrong_scale = _fixture()
        wrong_scale["outcomes"]["white_peace"][
            "cb_prestige_factor"
        ]["scale"] = 1
        cases.append(("wrong_scale", wrong_scale))

        wrong_expiry = _fixture()
        wrong_expiry["outcomes"]["attacker_defeat"]["truce"][
            "expiry_date_raw"
        ] += 1
        cases.append(("wrong_expiry", wrong_expiry))

        wp_gold = _fixture()
        wp_gold["outcomes"]["white_peace"]["primary_gold_transfers"][
            "values"
        ] = copy.deepcopy(
            wp_gold["outcomes"]["attacker_defeat"]
            ["primary_gold_transfers"]["values"]
        )
        cases.append(("wp_gold", wp_gold))

        missing_defeat_gold = _fixture()
        missing_defeat_gold["outcomes"]["attacker_defeat"][
            "primary_gold_transfers"
        ]["values"] = []
        cases.append(("missing_defeat_gold", missing_defeat_gold))

        factor_drift = _fixture()
        factor_drift["outcomes"]["attacker_defeat"][
            "cb_prestige_factor"
        ]["raw"] += 1
        cases.append(("factor_drift", factor_drift))

        inconsistent_acceptance = _fixture()
        inconsistent_acceptance["outcomes"]["white_peace"][
            "recipient_response"
        ]["would_accept_now"] = False
        cases.append(("inconsistent_acceptance", inconsistent_acceptance))

        unavailable_decision = _fixture()
        unavailable_decision["outcomes"]["attacker_defeat"][
            "recipient_response"
        ]["decision_status_raw"] = 3
        cases.append(("unavailable_decision", unavailable_decision))

        bad_claim_disposition = _fixture()
        bad_claim_disposition["outcomes"]["white_peace"][
            "claim_disposition"
        ]["claim_disposition"] = (
            "retain_no_strength_change_already_strong"
        )
        cases.append(("bad_claim_disposition", bad_claim_disposition))

        bad_provenance = _fixture()
        bad_provenance["provenance"]["native_contract_sha256"] = "0" * 63
        cases.append(("bad_provenance", bad_provenance))

        null_domain = _fixture()
        null_domain["outcomes"]["white_peace"]["truce"] = None
        cases.append(("null_domain", null_domain))

        for name, raw in cases:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    normalize_war_termination_exit_terms(raw)


if __name__ == "__main__":
    unittest.main()
