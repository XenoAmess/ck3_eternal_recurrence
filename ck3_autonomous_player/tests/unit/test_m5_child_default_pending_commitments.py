from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_m5_peacetime_proposal_sources_v1 import (
    _Driver, _FRAME, _construction, _faction, _history,
)
from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import (
    query_m5_peacetime_proposal_sources_v1,
)


class M5ChildDefaultPendingCommitmentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temporary.name) / "state"
        self.state_dir.mkdir()
        self.ledger_path = self.state_dir / "player-child-default-formal-v1.json"
        self.ledger = {
            "schema": "xar.ck3.player-child-default-formal.v1",
            "pending": {
                "episode_run_id": _FRAME["episode_run_id"],
                "played_character_id": 29829,
                "heir_character_id": 38988,
                "candidate_character_id": 37909,
                "recipient_character_id": 34332,
                "claimed_character_ids": [29829, 38988, 37909, 34332],
                "selected_value_projection": {
                    "generic_costs": {"gold_raw": 0, "application_timing": "on_send"},
                    "possible_alliance_pairs": [{
                        "first_character_id": 29829,
                        "second_character_id": 37909,
                        "would_attempt_if_accepted": False,
                    }],
                },
            },
            "resolved": None,
        }
        self._write_ledger()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_ledger(self) -> None:
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")

    def _query(self) -> tuple[dict[str, object], _Driver]:
        faction = _faction()
        faction["choice"]["recipient_character_id"] = 34332
        driver = _Driver(self.state_dir, faction=faction)
        driver.allow_private_guy_default_formal_trial = False
        construction = _construction()
        construction["candidate"]["authored_monthly_income_hundredths"] = 35
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1.query_construction_private",
            return_value=construction,
        ):
            sources = query_m5_peacetime_proposal_sources_v1(
                driver, snapshot=driver.take_snapshot(), history=_history(),
                baseline_plan={"policy": "one-life-turn-v1", "selected_step": "life-advance"},
                expected_revision=_FRAME["revision"],
            )
        return sources, driver

    def test_pending_claims_survive_disabled_submit_and_leave_actor_available(self) -> None:
        sources, driver = self._query()
        claims = sources["existing_commitments"]
        self.assertFalse(driver.allow_private_guy_default_formal_trial)
        self.assertEqual(claims["character_ids"], [34332, 37909, 38988])
        self.assertNotIn(29829, claims["character_ids"])
        self.assertEqual(claims["gold_raw"], 0)
        self.assertEqual(claims["ally_character_ids"], [])
        self.assertEqual(claims["commitment_keys"], ["player-child-default-marriage:38988"])
        self.assertFalse(sources["producer"]["pending_formal_ledgers_empty"])
        self.assertEqual(json.loads(self.ledger_path.read_text(encoding="utf-8")), self.ledger)

    def test_existing_pending_blocks_shared_recipient_and_keeps_building_eligible(self) -> None:
        sources, driver = self._query()
        collection = collect_m5_formal_proposals(snapshot=driver.take_snapshot(), sources=sources)
        dispatch = collection["dispatch"]
        rows = {row["domain"]: row for row in dispatch["analysis"]["evaluated"]}
        self.assertEqual(rows["diplomacy"]["reason"], "existing_commitment_conflict")
        self.assertEqual(rows["building"]["reason"], "eligible")
        self.assertEqual(dispatch["selected_candidate_id"], "building:501:701:1")
        after = dispatch["reservation"]["commitments_after"]
        self.assertEqual(after["gold_raw"], 3_000_000)
        self.assertEqual(after["character_ids"], [34332, 37909, 38988])
        self.assertEqual(len(after["commitment_keys"]), len(set(after["commitment_keys"])))

    def test_cleared_pending_releases_temporary_relationship_claims(self) -> None:
        self.ledger["resolved"] = {"status": "betrothal", "source_pending": deepcopy(self.ledger["pending"])}
        self.ledger["pending"] = None
        self._write_ledger()
        sources, driver = self._query()
        claims = sources["existing_commitments"]
        self.assertEqual(claims["character_ids"], [])
        self.assertEqual(claims["ally_character_ids"], [])
        self.assertEqual(claims["commitment_keys"], [])
        collection = collect_m5_formal_proposals(snapshot=driver.take_snapshot(), sources=sources)
        gift = next(row for row in collection["dispatch"]["analysis"]["evaluated"] if row["domain"] == "diplomacy")
        self.assertEqual(gift["reason"], "eligible")


if __name__ == "__main__":
    unittest.main()
