from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    BACKEND_ID,
    normalize_raiktor_surrender_six_domain,
)
from xar_autoplayer.bridge.raiktor_surrender_truce_contract import (
    BACKEND_ID as TRUCE_BACKEND_ID,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    BACKEND_ID as WAR_BOUND_BACKEND_ID,
    STATUS as WAR_BOUND_STATUS,
)


ROOT = Path(__file__).resolve().parents[2]
WAR_ID = 50_331_699
ATTACKER_ID = 29_829
DEFENDER_ID = 17_116
CLAIMANT_ID = 41_001
DOMAIN_ORDER = (
    "claims_base",
    "gold",
    "prestige",
    "prisoner_release",
    "favor_hook",
    "truce",
    "generic_war_bound_current",
)


def _frame() -> dict[str, object]:
    return {
        "snapshot_revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "paused": True,
        "war_id": WAR_ID,
        "active_casus_belli_database_index": 411,
        "active_casus_belli_key": "raiktor_claim_cb",
        "primary_attacker_character_id": ATTACKER_ID,
        "primary_defender_character_id": DEFENDER_ID,
        "claimant_character_id": CLAIMANT_ID,
    }


def _wrap(payload: dict[str, object]) -> dict[str, object]:
    return {"available": True, "frame": _frame(), "payload": payload}


def _claims() -> dict[str, object]:
    return {
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
        "target_order_stable": True,
        "claim_rows_stable": True,
    }


def _character_value(character_id: int, raw: int) -> dict[str, object]:
    return {
        "character_id": character_id,
        "value": {"raw": raw, "scale": 100_000},
    }


def _gold() -> dict[str, object]:
    return {
        "attacker_current_gold": _character_value(ATTACKER_ID, 35_000_000),
        "defender_current_gold": _character_value(DEFENDER_ID, 80_000_000),
        "attacker_authoritative_monthly_gold_income": _character_value(
            ATTACKER_ID, 500_001
        ),
        "defender_authoritative_monthly_gold_income": _character_value(
            DEFENDER_ID, 800_000
        ),
        "actual_transfer": {
            "from_character_id": ATTACKER_ID,
            "to_character_id": DEFENDER_ID,
            "value": {"raw": 15_000_000, "scale": 100_000},
        },
        "exact_primary_transfer_observed": True,
        "same_frame_stable": True,
    }


def _prestige() -> dict[str, object]:
    return {
        "attacker_current_prestige": _character_value(
            ATTACKER_ID, 12_345_678
        ),
        "cb_prestige_factor": {"raw": 700_000, "scale": 100_000},
        "attacker_prestige_delta": _character_value(
            ATTACKER_ID, -7_000_000
        ),
        "exact_factor_and_attacker_delta_observed": True,
        "same_frame_stable": True,
    }


def _prisoners() -> dict[str, object]:
    return {
        "attacker_participant_ids": [ATTACKER_ID, 30_001],
        "defender_participant_ids": [DEFENDER_ID],
        "attacker_release_candidate_ids": [ATTACKER_ID, 30_003],
        "defender_release_candidate_ids": [DEFENDER_ID],
        "release_pairs": [
            {
                "jailer_character_id": DEFENDER_ID,
                "prisoner_character_id": 30_003,
                "reason": "opposite_primary_or_first_three_successors",
            }
        ],
        "full_participant_scan": True,
        "primary_and_first_three_successors_scanned": True,
        "same_frame_stable": True,
    }


def _favor() -> dict[str, object]:
    return {
        "claimant_distinct_from_attacker": True,
        "original_visible_root_traversed": True,
        "will_apply": True,
        "same_frame_stable": True,
    }


def _truce() -> dict[str, object]:
    return {
        "schema_version": 1,
        "backend_id": TRUCE_BACKEND_ID,
        "status": "available",
        "failure": None,
        "snapshot_revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "paused": True,
        "war_id": WAR_ID,
        "active_casus_belli_database_index": 411,
        "active_casus_belli_key": "raiktor_claim_cb",
        "owner_character_id": ATTACKER_ID,
        "toward_character_id": DEFENDER_ID,
        "evaluated_days": 1_825,
        "pointer_shape_verified": True,
        "evaluator_double_read_stable": True,
        "same_frame_stable": True,
        "expiry_observable": False,
        "expiry_date_raw": None,
    }


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
        "current_soldiers": sum(row[2] for row in present.values()),
        "postwar_persistent_state": None,
        "composition_rows": rows,
    }


def _war_bound(*, cleanup: bool = False) -> dict[str, object]:
    value = {
        "schema_version": 1,
        "backend_id": WAR_BOUND_BACKEND_ID,
        "status": WAR_BOUND_STATUS,
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
            _regiment(0x01000011, {6: (0x02000022, 0x03000031, 40)}),
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
    if not cleanup:
        return value
    value["postwar_frame"] = {
        "snapshot_revision": 96,
        "native_revision": 8,
        "date_raw": 53_175_816,
        "paused": True,
        "frozen_war_id": WAR_ID,
        "frozen_war_absent_from_active_wars": True,
    }
    value["cleanup"] = {"observable": True, "status": "destroyed"}
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
                row["frozen_carmy_roster_evidence"] = (
                    "frozen_army_destroyed"
                )
    return value


def _aggregate(
    *, missing: tuple[str, ...] = (), cleanup: bool = False
) -> dict[str, object]:
    wrappers = {
        "claims_base": _wrap(_claims()),
        "gold": _wrap(_gold()),
        "prestige": _wrap(_prestige()),
        "prisoner_release": _wrap(_prisoners()),
        "favor_hook": _wrap(_favor()),
        "truce": _wrap(_truce()),
        "generic_war_bound_current": _wrap(_war_bound(cleanup=cleanup)),
    }
    for name in missing:
        wrappers[name] = {"available": False}
    available = {name: name not in missing for name in DOMAIN_ORDER}
    six_ready = all(available[name] for name in DOMAIN_ORDER[1:])
    action_ready = available["claims_base"] and six_ready
    return {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": "complete" if action_ready else "incomplete",
        "failure": None,
        "frame": _frame(),
        "claims_base": wrappers["claims_base"],
        "domains": {
            name: wrappers[name] for name in DOMAIN_ORDER[1:]
        },
        "missing_domains": [
            name for name in DOMAIN_ORDER if not available[name]
        ],
        "readiness": {
            "claims_base_ready": available["claims_base"],
            "gold_ready": available["gold"],
            "prestige_ready": available["prestige"],
            "prisoner_release_ready": available["prisoner_release"],
            "favor_hook_ready": available["favor_hook"],
            "truce_ready": available["truce"],
            "generic_war_bound_current_ready": available[
                "generic_war_bound_current"
            ],
            "postwar_cleanup_ready": (
                cleanup and available["generic_war_bound_current"]
            ),
            "source_specific_war_bound_ready": False,
            "pre_soldiers_ready": False,
            "proven_soldier_loss_ready": False,
            "six_dynamic_domains_ready": six_ready,
            "same_frame_stable": action_ready,
            "action_terms_ready": action_ready,
            "automatic_surrender_ready": False,
        },
    }


def _normalize(value: object) -> dict[str, object]:
    return normalize_raiktor_surrender_six_domain(
        value,
        expected_war_id=WAR_ID,
        expected_snapshot_revision=91,
        expected_native_revision=7,
        expected_date_raw=53_175_816,
        expected_attacker_character_id=ATTACKER_ID,
        expected_defender_character_id=DEFENDER_ID,
        expected_claimant_character_id=CLAIMANT_ID,
    )


class RaiktorSurrenderSixDomainContractTests(unittest.TestCase):
    def test_accepts_complete_same_frame_terms_without_automatic_action(self) -> None:
        value = _aggregate()
        self.assertEqual(_normalize(value), value)
        self.assertTrue(value["readiness"]["action_terms_ready"])
        self.assertFalse(value["readiness"]["automatic_surrender_ready"])
        self.assertFalse(
            value["readiness"]["source_specific_war_bound_ready"]
        )

    def test_every_missing_child_is_explicit_and_fail_closed(self) -> None:
        for name in DOMAIN_ORDER:
            with self.subTest(name=name):
                value = _aggregate(missing=(name,))
                self.assertEqual(_normalize(value), value)
                self.assertEqual(value["status"], "incomplete")
                self.assertFalse(value["readiness"]["action_terms_ready"])
                self.assertEqual(value["missing_domains"], [name])

    def test_rejects_cross_frame_domain_stamps(self) -> None:
        for name in DOMAIN_ORDER:
            with self.subTest(name=name):
                value = _aggregate()
                wrapper = (
                    value["claims_base"]
                    if name == "claims_base"
                    else value["domains"][name]
                )
                wrapper["frame"]["snapshot_revision"] += 1
                with self.assertRaises(ValueError):
                    _normalize(value)

    def test_rejects_dynamic_identity_formula_or_scope_drift(self) -> None:
        mutations = (
            lambda value: value["domains"]["gold"]["payload"][
                "actual_transfer"
            ].update({"to_character_id": ATTACKER_ID}),
            lambda value: value["domains"]["prestige"]["payload"][
                "attacker_prestige_delta"
            ]["value"].update({"raw": -6_999_999}),
            lambda value: value["domains"]["prisoner_release"]["payload"][
                "release_pairs"
            ][0].update({"jailer_character_id": ATTACKER_ID}),
            lambda value: value["domains"]["favor_hook"]["payload"].update(
                {"claimant_distinct_from_attacker": False}
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = _aggregate()
                mutation(value)
                with self.assertRaises(ValueError):
                    _normalize(value)

    def test_rejects_invented_truce_expiry(self) -> None:
        value = _aggregate()
        truce = value["domains"]["truce"]["payload"]
        truce["expiry_observable"] = True
        truce["expiry_date_raw"] = 53_219_616
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_rejects_event_source_pre_soldiers_or_loss_overclaim(self) -> None:
        value = _aggregate()
        war_bound = value["domains"]["generic_war_bound_current"]["payload"]
        war_bound["readiness"]["source_specific_attribution_ready"] = True
        war_bound["readiness"]["raiktor_source_specific_domain_ready"] = True
        war_bound["soldiers"]["pre_soldiers_observable"] = True
        war_bound["soldiers"]["observed_pre_soldiers"] = 3000
        war_bound["soldiers"]["proven_soldier_loss_observable"] = True
        war_bound["soldiers"]["proven_soldiers_lost"] = 2820
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_accepts_separate_postwar_cleanup_attachment(self) -> None:
        value = _aggregate(cleanup=True)
        self.assertEqual(_normalize(value), value)
        self.assertTrue(value["readiness"]["postwar_cleanup_ready"])
        self.assertFalse(value["readiness"]["proven_soldier_loss_ready"])

    def test_source_contract_freezes_static_only_boundary(self) -> None:
        contract = json.loads(
            (
                ROOT
                / "native_bridge"
                / "research"
                / "fixtures"
                / "raiktor_surrender_six_domain_v1_source_contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            contract["domain_counting"]["six_dynamic_domains"],
            [
                "gold",
                "prestige",
                "prisoner_release",
                "favor_hook",
                "truce",
                "generic_war_bound_current",
            ],
        )
        self.assertFalse(
            contract["war_bound_boundary"][
                "source_specific_attribution_ready"
            ]
        )
        self.assertFalse(
            contract["war_bound_boundary"]["proven_soldier_loss_ready"]
        )
        self.assertFalse(contract["readiness"]["production_live"])
        for frozen in contract["frozen_component_contracts"]:
            component = ROOT / frozen["path"]
            self.assertEqual(
                hashlib.sha256(component.read_bytes()).hexdigest().upper(),
                frozen["sha256"],
            )
        source = (
            ROOT
            / "native_bridge"
            / "src"
            / "raiktor_surrender_six_domain_v1.cpp"
        ).read_text(encoding="utf-8")
        self.assertNotIn("norman_highwaymen", source)
        self.assertNotIn("expiry_date_raw", source)


if __name__ == "__main__":
    unittest.main()
