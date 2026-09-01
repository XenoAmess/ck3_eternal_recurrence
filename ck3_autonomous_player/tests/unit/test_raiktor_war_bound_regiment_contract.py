from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    BACKEND_ID,
    STATUS,
    normalize_raiktor_war_bound_regiment,
)


ROOT = Path(__file__).resolve().parents[2]
WAR_ID = 50_331_699
ATTACKER_ID = 29_829
DEFENDER_ID = 17_116


def _row(
    ordinal: int,
    current_id: int | None = None,
    army_id: int | None = None,
    soldiers: int | None = None,
) -> dict[str, object]:
    return {
        "composition_ordinal": ordinal,
        "current_army_regiment_id": current_id,
        "raised_carmy_id": army_id,
        "current_soldiers": soldiers,
        "current_army_regiment_state": None,
        "raised_carmy_state": None,
        "frozen_carmy_roster_evidence": None,
    }


def _regiment(
    persistent_id: int, present: dict[int, tuple[int, int, int]]
) -> dict[str, object]:
    rows = [_row(ordinal) for ordinal in range(7)]
    for ordinal, (current_id, army_id, soldiers) in present.items():
        rows[ordinal] = _row(ordinal, current_id, army_id, soldiers)
    return {
        "persistent_regiment_id": persistent_id,
        "bound_war_id": WAR_ID,
        "war_keep_on_attacker_victory": False,
        "current_soldiers": sum(item[2] for item in present.values()),
        "postwar_persistent_state": None,
        "composition_rows": rows,
    }


def _active() -> dict[str, object]:
    return {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": STATUS,
        "failure": None,
        "active_frame": {
            "snapshot_revision": 91,
            "native_revision": 7,
            "date_raw": 53_175_816,
            "paused": True,
            "war_id": WAR_ID,
            "active_casus_belli_database_index": 411,
            "active_casus_belli_key": "raiktor_claim_cb",
            "primary_attacker_character_id": ATTACKER_ID,
            "primary_defender_character_id": DEFENDER_ID,
        },
        "postwar_frame": None,
        "owner_character_id": ATTACKER_ID,
        "war_id": WAR_ID,
        "source_attribution": {
            "mode": "authored_candidate_only",
            "authored_candidate_name": "norman_highwaymen",
            "authored_spawn_army_count": 6,
            "authored_soldiers_per_army": 500,
            "authored_total_soldiers": 3000,
        },
        "soldiers": {
            "current_soldiers_observable": True,
            "observed_current_soldiers": 180,
            "pre_soldiers_observable": False,
            "observed_pre_soldiers": None,
            "proven_soldier_loss_observable": False,
            "proven_soldiers_lost": None,
        },
        "cleanup": {"observable": False, "status": None},
        "regiments": [
            _regiment(
                0x01000010,
                {
                    0: (0x02000020, 0x03000030, 80),
                    3: (0x02000021, 0x03000030, 60),
                },
            ),
            _regiment(
                0x01000011,
                {6: (0x02000022, 0x03000031, 40)},
            ),
        ],
        "readiness": {
            "exact_raiktor_war_context_ready": True,
            "generic_war_bound_identity_ready": True,
            "current_soldiers_ready": True,
            "postwar_cleanup_ready": False,
            "source_specific_attribution_ready": False,
            "pre_soldiers_ready": False,
            "proven_soldier_loss_ready": False,
            "independently_visible_value_ready": True,
            "raiktor_source_specific_domain_ready": False,
        },
    }


def _cleanup(*, still_alive: bool) -> dict[str, object]:
    value = _active()
    value["postwar_frame"] = {
        "snapshot_revision": 96,
        "native_revision": 8,
        "date_raw": 53_175_816,
        "paused": True,
        "frozen_war_id": WAR_ID,
        "frozen_war_absent_from_active_wars": True,
    }
    value["cleanup"] = {
        "observable": True,
        "status": "still_alive" if still_alive else "destroyed",
    }
    value["readiness"]["postwar_cleanup_ready"] = True
    for regiment in value["regiments"]:
        regiment["postwar_persistent_state"] = "destroyed"
        for row in regiment["composition_rows"]:
            if row["current_army_regiment_id"] is None:
                row["current_army_regiment_state"] = "not_present"
                row["raised_carmy_state"] = "not_present"
                row["frozen_carmy_roster_evidence"] = "not_present"
            else:
                row["current_army_regiment_state"] = "destroyed"
                row["raised_carmy_state"] = "destroyed"
                row["frozen_carmy_roster_evidence"] = "frozen_army_destroyed"
    if still_alive:
        row = value["regiments"][0]["composition_rows"][0]
        row["current_army_regiment_state"] = "still_alive"
        row["raised_carmy_state"] = "still_alive"
        row["frozen_carmy_roster_evidence"] = "still_attached"
    return value


def _normalize(value: object) -> dict[str, object]:
    return normalize_raiktor_war_bound_regiment(
        value,
        expected_war_id=WAR_ID,
        expected_attacker_character_id=ATTACKER_ID,
        expected_defender_character_id=DEFENDER_ID,
        expected_snapshot_revision=91,
        expected_native_revision=7,
        expected_date_raw=53_175_816,
    )


class RaiktorWarBoundRegimentContractTests(unittest.TestCase):
    def test_accepts_current_soldiers_as_independent_visible_value(self) -> None:
        value = _active()
        self.assertEqual(_normalize(value), value)
        self.assertFalse(
            value["readiness"]["source_specific_attribution_ready"]
        )
        self.assertFalse(value["readiness"]["proven_soldier_loss_ready"])

    def test_accepts_destroyed_and_still_alive_cleanup(self) -> None:
        for still_alive in (False, True):
            with self.subTest(still_alive=still_alive):
                value = _cleanup(still_alive=still_alive)
                self.assertEqual(_normalize(value), value)

    def test_rejects_source_pre_or_loss_overclaim(self) -> None:
        value = _active()
        value["readiness"]["source_specific_attribution_ready"] = True
        value["readiness"]["raiktor_source_specific_domain_ready"] = True
        with self.assertRaises(ValueError):
            _normalize(value)
        value = _active()
        value["soldiers"]["pre_soldiers_observable"] = True
        value["soldiers"]["observed_pre_soldiers"] = 3000
        value["soldiers"]["proven_soldier_loss_observable"] = True
        value["soldiers"]["proven_soldiers_lost"] = 2820
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_rejects_generation_or_soldier_aggregate_drift(self) -> None:
        value = _active()
        value["regiments"][1]["persistent_regiment_id"] = value[
            "regiments"
        ][0]["persistent_regiment_id"]
        with self.assertRaises(ValueError):
            _normalize(value)
        value = _active()
        value["soldiers"]["observed_current_soldiers"] = 3000
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_rejects_cleanup_state_or_aggregate_drift(self) -> None:
        value = _cleanup(still_alive=False)
        value["regiments"][0]["composition_rows"][0][
            "frozen_carmy_roster_evidence"
        ] = "still_attached"
        with self.assertRaises(ValueError):
            _normalize(value)
        value = _cleanup(still_alive=True)
        value["cleanup"]["status"] = "destroyed"
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_source_contract_records_the_unclosed_origin_gap(self) -> None:
        fixture = json.loads(
            (
                ROOT
                / "native_bridge"
                / "research"
                / "fixtures"
                / "raiktor_war_bound_regiment_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(
            fixture["source_attribution_boundary"][
                "source_specific_attribution_ready"
            ]
        )
        self.assertFalse(
            fixture["soldier_boundary"]["pre_soldiers_observable"]
        )
        self.assertFalse(
            fixture["soldier_boundary"]["proven_soldier_loss_observable"]
        )
        source = (
            ROOT
            / "native_bridge"
            / "src"
            / "raiktor_war_bound_regiment_v1.cpp"
        ).read_text(encoding="utf-8")
        self.assertNotIn("norman_highwaymen", source)
        self.assertNotIn("kRaiktorAuthoredTotalSoldiers -", source)


if __name__ == "__main__":
    unittest.main()
