from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (
    normalize_war_termination_options,
    offer_white_peace_step,
    parse_offer_white_peace_step,
    parse_query_war_termination_options_step,
    parse_surrender_war_step,
    query_war_termination_options_step,
    surrender_war_step,
)


def _option(
    outcome: str,
    *,
    constructed: bool = True,
    validator: bool | None = True,
) -> dict[str, object]:
    return {
        "outcome": outcome,
        "hostage_variant": "none",
        "context_constructed": constructed,
        "native_validator_passed": validator,
        "available": constructed and validator is True,
        "terms_observable": False,
        "terms": {
            "status": "unavailable",
            "reason": "cb_specific_terms_not_observable",
        },
        "ai_acceptance_observable": constructed,
        "ai_acceptance": (
            {"raw": -2_900_000, "scale": 100_000}
            if constructed
            else None
        ),
        "auto_accept_observable": constructed,
        "auto_accept": False if constructed else None,
    }


def _termination_options(
    *,
    war_id: int = 16_777_290,
    player_side: str = "attacker",
) -> dict[str, object]:
    attacker_score = 41
    defender_score = -41
    return {
        "war_id": war_id,
        "player_side": player_side,
        "player_is_primary_war_leader": True,
        "player_relative_war_score": (
            attacker_score if player_side == "attacker" else defender_score
        ),
        "war_duration_days": 203,
        "active_casus_belli_present": True,
        "active_casus_belli_identity": {
            "database_index": 17,
            "canonical_key": "county_conquest_cb",
        },
        "cb_allows_white_peace": True,
        "absolute_war_scores_observable": True,
        "attacker_war_score": attacker_score,
        "defender_war_score": defender_score,
        "war_score_breakdown": {
            "imprisonment": 0,
            "battles": -4,
            "occupation": 45,
            "ticking": 0,
        },
        "options": {
            "surrender": _option(
                "attacker_defeat"
                if player_side == "attacker"
                else "attacker_victory"
            ),
            "white_peace": _option("white_peace"),
            "victory": _option(
                "attacker_victory"
                if player_side == "attacker"
                else "attacker_defeat"
            ),
        },
    }


class WarTerminationContractTests(unittest.TestCase):
    def test_full_generation_war_steps_round_trip_canonically(self) -> None:
        war_id = 16_777_290
        self.assertEqual(
            query_war_termination_options_step(war_id),
            "query-war-termination-options-16777290",
        )
        self.assertEqual(surrender_war_step(war_id), "surrender-war-16777290")
        self.assertEqual(
            offer_white_peace_step(war_id),
            "offer-white-peace-16777290",
        )
        self.assertEqual(
            parse_query_war_termination_options_step(
                "query-war-termination-options-16777290"
            ),
            war_id,
        )
        self.assertEqual(
            parse_surrender_war_step("surrender-war-16777290"), war_id
        )
        self.assertEqual(
            parse_offer_white_peace_step("offer-white-peace-16777290"),
            war_id,
        )

    def test_war_step_parsers_reject_slots_placeholders_and_decorations(
        self,
    ) -> None:
        malformed = (
            "query-war-termination-options-N",
            "query-war-termination-options-0",
            "query-war-termination-options-016777290",
            "query-war-termination-options-2147483648",
            "query-war-termination-options-16777290-extra",
            "surrender-war-0",
            "surrender-war-016777290",
            "surrender-war-16777290/result",
            "offer-white-peace-0",
            "offer-white-peace-１６７７７２９０",
        )
        for step in malformed:
            with self.subTest(step=step):
                self.assertIsNone(
                    parse_query_war_termination_options_step(step)
                )
                self.assertIsNone(parse_surrender_war_step(step))
                self.assertIsNone(parse_offer_white_peace_step(step))

    def test_normalizer_preserves_unknown_validator_and_unavailable_domains(
        self,
    ) -> None:
        raw = _termination_options()
        raw["absolute_war_scores_observable"] = False
        raw["attacker_war_score"] = None
        raw["defender_war_score"] = None
        raw["war_score_breakdown"] = None
        raw["active_casus_belli_identity"] = None
        raw["options"]["white_peace"] = _option(
            "white_peace", constructed=True, validator=None
        )

        normalized = normalize_war_termination_options(raw)

        self.assertIsNone(
            normalized["options"]["white_peace"][
                "native_validator_passed"
            ]
        )
        self.assertFalse(normalized["options"]["white_peace"]["available"])
        self.assertIsNone(normalized["attacker_war_score"])
        self.assertIsNone(normalized["war_score_breakdown"])
        self.assertEqual(
            normalized["options"]["surrender"]["ai_acceptance"],
            {"raw": -2_900_000, "scale": 100_000},
        )

    def test_normalizer_rejects_side_outcome_or_partial_score_evidence(
        self,
    ) -> None:
        malformed_rows: list[dict[str, object]] = []
        wrong_outcome = _termination_options()
        wrong_outcome["options"]["surrender"]["outcome"] = (
            "attacker_victory"
        )
        malformed_rows.append(wrong_outcome)
        partial_absolute = _termination_options()
        partial_absolute["defender_war_score"] = None
        malformed_rows.append(partial_absolute)
        inconsistent_absolute = _termination_options()
        inconsistent_absolute["defender_war_score"] = -40
        malformed_rows.append(inconsistent_absolute)
        partial_breakdown = _termination_options()
        partial_breakdown["war_score_breakdown"].pop("ticking")
        malformed_rows.append(partial_breakdown)
        fake_terms = _termination_options()
        fake_terms["options"]["surrender"]["terms"] = None
        malformed_rows.append(fake_terms)
        missing_duration = _termination_options()
        missing_duration.pop("war_duration_days")
        malformed_rows.append(missing_duration)
        decorated_top_level = _termination_options()
        decorated_top_level["terms_observable"] = False
        malformed_rows.append(decorated_top_level)
        bad_acceptance_scale = _termination_options()
        bad_acceptance_scale["options"]["white_peace"]["ai_acceptance"][
            "scale"
        ] = 1_000
        malformed_rows.append(bad_acceptance_scale)

        for raw in malformed_rows:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    normalize_war_termination_options(raw)


if __name__ == "__main__":
    unittest.main()
