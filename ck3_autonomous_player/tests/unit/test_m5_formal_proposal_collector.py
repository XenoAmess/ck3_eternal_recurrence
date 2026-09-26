from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest import mock
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.m5_formal_proposal_collector import (
    SOURCE_SCHEMA,
    collect_m5_formal_proposals,
)
from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher


_FRAME = {
    "played_character_id": 29829,
    "native_revision": 17,
    "date_raw": 53202168,
    "snapshot_id": "native:17",
    "revision": 23,
    "episode_run_id": "native-29829-m5-formal",
}


def _snapshot() -> dict[str, object]:
    return {
        **_FRAME,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29829},
        "played_character_gold": {"raw": 40_000_000, "scale": 100_000},
        "active_wars": [{
            "war_id": 16777231,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
        }],
        "player_armies": [{"army_id": 71, "controllable": True}],
        "history": [],
    }


def _commitments(**updates: object) -> dict[str, object]:
    result: dict[str, object] = {
        "frame": dict(_FRAME),
        "gold_raw": 0,
        "pending_war_slots": 0,
        "army_ids": [],
        "ally_character_ids": [],
        "character_ids": [],
        "commitment_keys": [],
    }
    result.update(updates)
    return result


def _war_source() -> dict[str, object]:
    return {
        "plan": {
            "policy": "one-life-turn-v1",
            "phase": "native_war_termination_query",
            "selected_step": "query-war-termination-options-16777231",
            "war_id": 16777231,
            "active_wars": [{
                "war_id": 16777231,
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }],
        },
        "observation": {
            "status": "available",
            "read_only": True,
            "source_frame": dict(_FRAME),
            "war_id": 16777231,
            "army_ids": [71],
            "ally_character_ids": [30098],
            "character_ids": [30097],
            "army_war_bindings": [{"army_id": 71, "war_id": 16777231}],
            "projected_supply_margin_raw": 250_000,
            "incremental_gold_cost_raw": 0,
            "minimum_gold_reserve_raw": 5_000_000,
        },
    }


def _building_source() -> dict[str, object]:
    return {"query": {
        "status": "selected",
        "source_frame": {
            **_FRAME,
            "actor_character_id": _FRAME["played_character_id"],
        },
        "candidate": {
            "barony_title_id": 501,
            "province_id": 601,
            "building_type_id": 701,
            "slot_index": 1,
            "stock_gold_cost_raw": 3_000_000,
            "gold_before_raw": 40_000_000,
        },
    }}


def _diplomacy_source() -> dict[str, object]:
    return {"candidate": {
        "status": "selected",
        "choice": {
            "snapshot_revision": _FRAME["native_revision"],
            "native_snapshot_revision": _FRAME["native_revision"],
            "date_raw": _FRAME["date_raw"],
            "player_character_id": _FRAME["played_character_id"],
            "source_faction_id": 801,
            "recipient_character_id": 41003,
            "gold_cost_raw": 2_000_000,
            "opinion_delta": 20,
            "minimum_gold_reserve_raw": 10_000_000,
        },
    }}


def _sources(
    *, domains: dict[str, object] | None = None,
    commitments: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": SOURCE_SCHEMA,
        "status": "available",
        "read_only": True,
        "advertised": False,
        "frame": dict(_FRAME),
        "existing_commitments": (
            _commitments() if commitments is None else commitments
        ),
        "gold_reserve_raw": 5_000_000,
        "max_active_wars": 1,
        "domains": ({
            "war": _war_source(),
            "building": _building_source(),
            "diplomacy": _diplomacy_source(),
        } if domains is None else domains),
    }


class _ServiceDriver:
    def __init__(
        self, *, enabled: bool, sources: dict[str, object] | None = None,
        snapshot: dict[str, object] | None = None,
    ) -> None:
        self.allow_private_m5_joint_collector = enabled
        self._sources = deepcopy(sources)
        self._snapshot = deepcopy(snapshot) if snapshot is not None else _snapshot()
        self.source_reads = 0

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self._snapshot)

    def capabilities(self) -> dict[str, object]:
        return {
            "action_steps": ["life-advance", "declare-war-31549-40--1"],
            "bridge_capabilities": [],
        }

    def query_m5_joint_proposal_sources_private_v1(
        self, **kwargs: object,
    ) -> dict[str, object]:
        self.source_reads += 1
        self.last_read = deepcopy(kwargs)
        if self._sources is None:
            raise AssertionError("private M5 reader must not be called")
        return deepcopy(self._sources)


class M5FormalProposalCollectorTests(unittest.TestCase):
    def test_ready_war_diplomacy_and_building_are_dispatched_once(self) -> None:
        original = M5FrameDispatcher.choose_observed

        def call_original(
            dispatcher: M5FrameDispatcher, **kwargs: object,
        ) -> dict[str, object]:
            return original(dispatcher, **kwargs)

        with mock.patch.object(
            M5FrameDispatcher,
            "choose_observed",
            autospec=True,
            side_effect=call_original,
        ) as dispatch:
            result = collect_m5_formal_proposals(
                snapshot=_snapshot(), sources=_sources(),
            )

        self.assertEqual(dispatch.call_count, 1)
        self.assertCountEqual(
            result["collected_domains"], ["war", "building", "diplomacy"]
        )
        self.assertEqual(
            result["dispatch"]["selected_candidate_id"],
            "diplomacy:faction-gift:801:41003",
        )
        evaluated = {
            row["domain"]: row
            for row in result["dispatch"]["analysis"]["evaluated"]
        }
        self.assertEqual(evaluated["war"]["reason"], "eligible")
        self.assertEqual(
            evaluated["war"]["projected_supply_margin_raw"], 250_000
        )
        self.assertIsNone(result["selected_step"])
        self.assertFalse(result["formal_action_ready"])

    def test_each_observed_resource_conflict_rejects_war_commitment(self) -> None:
        cases = (
            {"army_ids": [71]},
            {"ally_character_ids": [30098]},
            {"character_ids": [30097]},
            {"commitment_keys": ["active-war:16777231"]},
        )
        for claimed in cases:
            with self.subTest(claimed=claimed):
                result = collect_m5_formal_proposals(
                    snapshot=_snapshot(),
                    sources=_sources(
                        domains={
                            "war": _war_source(),
                            "diplomacy": _diplomacy_source(),
                        },
                        commitments=_commitments(**claimed),
                    ),
                )
                evaluated = {
                    row["domain"]: row
                    for row in result["dispatch"]["analysis"]["evaluated"]
                }
                self.assertEqual(
                    evaluated["war"]["reason"], "existing_commitment_conflict"
                )
                self.assertEqual(
                    result["dispatch"]["selected_candidate_id"],
                    "diplomacy:faction-gift:801:41003",
                )

    def test_one_ready_alternative_avoids_analytic_noop(self) -> None:
        result = collect_m5_formal_proposals(
            snapshot=_snapshot(),
            sources=_sources(domains={"building": _building_source()}),
        )
        self.assertEqual(result["status"], "reserved_analytic")
        self.assertEqual(
            result["dispatch"]["selected_candidate_id"],
            "building:501:701:1",
        )
        self.assertIsNotNone(result["dispatch"]["reservation"])

    def test_marriage_inventory_is_not_an_admitted_source_domain(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported domains: marriage"):
            collect_m5_formal_proposals(
                snapshot=_snapshot(),
                sources=_sources(domains={"marriage": {"candidate_count": 657}}),
            )

    def test_default_off_preserves_formal_plan_and_skips_reader(self) -> None:
        driver = _ServiceDriver(enabled=False)
        baseline = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_declaration",
            "selected_step": "declare-war-31549-40--1",
            "reason": "formal domain action remains unsubmitted",
        }
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"], baseline)
        self.assertEqual(driver.source_reads, 0)

    def test_opt_in_preserves_non_life_advance_formal_step(self) -> None:
        driver = _ServiceDriver(
            enabled=True,
            sources=_sources(domains={"diplomacy": _diplomacy_source()}),
        )
        baseline = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_declaration",
            "selected_step": "declare-war-31549-40--1",
            "reason": "formal domain action remains unsubmitted",
        }
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"], baseline)
        self.assertEqual(driver.source_reads, 0)

    def test_due_private_lifestyle_step_precedes_peace_only_joint_source(self) -> None:
        driver = _ServiceDriver(enabled=True, sources=_sources())
        driver.allow_private_lifestyle_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch.object(
            GameplayBridgeService, "_plan_private_lifestyle_trial_v1",
            side_effect=lambda planned, steps: {
                **planned, "plan": {**planned["plan"],
                                     "selected_step": "private-submit-player-lifestyle-perk-v1"},
            },
        ):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"]["selected_step"],
                         "private-submit-player-lifestyle-perk-v1")
        self.assertEqual(driver.source_reads, 0)

    def test_c8_active_war_skips_peace_only_m5_and_keeps_formal_turn(self) -> None:
        driver = _ServiceDriver(enabled=True)
        driver.allow_private_construction_formal_trial = True
        driver.allow_private_family_marriage_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "native_war_progress",
                    "selected_step": "life-advance"}
        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_construction_private",
            side_effect=lambda driver, planned, snapshot, history, steps, **kwargs:
                {**planned, "plan": {**planned["plan"],
                                     "construction_receipt_consumed": {"status": "applied"}}},
        ) as construction, mock.patch(
            "xar_autoplayer.bridge.service.plan_family_marriage_private",
            side_effect=lambda driver, planned, snapshot, **kwargs: planned,
        ) as family):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(planned["plan"]["m5_joint_status"], "ineligible_active_war")
        self.assertFalse(planned["plan"]["m5_joint_formal_action_ready"])
        self.assertEqual(planned["plan"]["construction_receipt_consumed"],
                         {"status": "applied"})
        self.assertEqual(driver.source_reads, 0)
        construction.assert_called_once()
        family.assert_called_once()

    def test_peace_m5_receipt_path_still_collects_family_diagnostic(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        driver.allow_private_family_marriage_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def family_no_positive(driver, planned, snapshot, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "family_marriage_status": "no_positive_observed_marriage_opportunity",
                "family_marriage_private_diagnostic": {"rows": []}}}

        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_m5_formal_query_only",
            side_effect=lambda driver, planned, **kwargs: planned,
        ) as joint, mock.patch(
            "xar_autoplayer.bridge.service.plan_family_marriage_private",
            side_effect=family_no_positive,
        ) as family):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(planned["plan"]["family_marriage_status"],
                         "no_positive_observed_marriage_opportunity")
        joint.assert_called_once()
        family.assert_called_once()

    def test_peace_m5_observation_red_remains_visible_after_family_diagnostic(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        driver.allow_private_family_marriage_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def joint_red(driver, planned, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "phase": "m5_joint_query_only_red", "selected_step": None,
                "reason": "M5 real observation missing"}}

        def family_no_positive(driver, planned, snapshot, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "family_marriage_status": "no_positive_observed_marriage_opportunity"}}

        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_m5_formal_query_only",
            side_effect=joint_red,
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_family_marriage_private",
            side_effect=family_no_positive,
        )):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertIsNone(planned["plan"]["selected_step"])
        self.assertEqual(planned["plan"]["phase"], "m5_joint_query_only_red")
        self.assertEqual(planned["plan"]["reason"], "M5 real observation missing")
        self.assertEqual(planned["plan"]["m5_joint_red_reason"],
                         "M5 real observation missing")
        self.assertEqual(planned["plan"]["family_marriage_status"],
                         "no_positive_observed_marriage_opportunity")

    def test_unknown_war_scene_does_not_claim_m5_ineligible(self) -> None:
        unknown = _snapshot()
        unknown.pop("active_wars")
        unknown.pop("player_armies")
        driver = _ServiceDriver(enabled=True, snapshot=unknown)
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}
        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_m5_formal_query_only",
            side_effect=lambda driver, planned, **kwargs: {
                **planned, "plan": {**planned["plan"],
                    "phase": "m5_joint_query_only_red", "selected_step": None,
                    "reason": "M5 scene observation is unavailable"}},
        ) as joint):
            planned = GameplayBridgeService(driver).plan_turn()
        joint.assert_called_once()
        self.assertIsNone(planned["plan"]["selected_step"])
        self.assertNotIn("m5_joint_status", planned["plan"])
        self.assertEqual(planned["plan"]["reason"],
                         "M5 scene observation is unavailable")

    def test_peace_m5_red_blocks_typed_family_after_diagnostic(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        driver.allow_private_family_marriage_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def joint_red(driver, planned, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "phase": "m5_joint_query_only_red", "selected_step": None,
                "reason": "M5 scene observation is unavailable"}}

        def family_typed(driver, planned, snapshot, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "phase": "first_heir_marriage_typed_submit",
                "selected_step": "private-submit-first-heir-marriage-v1",
                "family_marriage_private_diagnostic": {"valued": True}}}

        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_m5_formal_query_only",
            side_effect=joint_red,
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_family_marriage_private",
            side_effect=family_typed,
        ) as family):
            planned = GameplayBridgeService(driver).plan_turn()
        family.assert_called_once()
        self.assertIsNone(planned["plan"]["selected_step"])
        self.assertEqual(planned["plan"]["phase"], "m5_joint_query_only_red")
        self.assertEqual(planned["plan"]["reason"],
                         "M5 scene observation is unavailable")
        self.assertEqual(planned["plan"]["family_marriage_private_diagnostic"],
                         {"valued": True})


if __name__ == "__main__":
    unittest.main()
