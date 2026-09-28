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
    plan_m5_formal_query_only,
    plan_m5_wartime_query_only,
)
from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher
from xar_autoplayer.native_auto_run import _compact_plan
from xar_autoplayer.m5_war_cash_resource_v1 import observe_active_war_cash_resource_v1
from xar_autoplayer.bridge.faction_gift_formal_route_v1 import (
    COLD_RECOVERY_STEP as FACTION_GIFT_COLD_RECOVERY_STEP,
    RECEIPT_STEP as FACTION_GIFT_RECEIPT_STEP,
    SUBMIT_STEP as FACTION_GIFT_SUBMIT_STEP,
)
from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    SUBMIT_STEP as FAMILY_SUBMIT_STEP,
)


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
            "priced_command": {
                "kind": "read_only_query", "war_id": 16777231,
                "query_name": "war_termination_options",
            },
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
            "war_cash_resource": _war_cash(),
            "immediate_action_quote": {
                "source_frame": dict(_FRAME), "war_id": 16777231,
                "selected_step": "query-war-termination-options-16777231",
                "priced_command": {
                    "kind": "read_only_query", "war_id": 16777231,
                    "query_name": "war_termination_options",
                },
                "quoted_cost_raw": 0, "scale": 100_000,
                "native_quote_id": "synthetic-read-only-query-fixture",
            },
        },
    }


def _war_cash(
    pending_cash_raw: int = 0,
    pending_source: str = "test-empty-pending-ledger",
) -> dict[str, object]:
    def amount(raw: int, source: str) -> dict[str, object]:
        return {"raw": raw, "scale": 100_000, "source": source,
                "source_frame": dict(_FRAME), "war_id": 16777231}

    return observe_active_war_cash_resource_v1(
        snapshot=_snapshot(), war_id=16777231,
        inputs={
            "source_frame": dict(_FRAME), "war_id": 16777231,
            "pending_war_cash_raw": amount(pending_cash_raw, pending_source),
            "immediate_war_action_cost_raw": amount(0, "test-read-only-query"),
            "future_war_cost_upper_raw": amount(1_000_000, "test-bound"),
            "future_risk_budget_raw": amount(1_000_000, "test-risk"),
            "policy_minimum_gold_reserve_raw": amount(3_000_000, "test-policy"),
            "horizon_days": 1,
            "future_bound_assumptions": ["synthetic bounded test only"],
        },
    )


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
        "war_cash_resource": _war_cash(),
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
    def test_selected_gift_reaches_existing_formal_consumer(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        candidate = _diplomacy_source()["candidate"]
        driver = _ServiceDriver(
            enabled=True,
            sources=_sources(domains={"diplomacy": {"candidate": candidate}}),
            snapshot=peace,
        )
        driver.allow_private_faction_gift_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def gift_consumer(driver, planned, snapshot, history, available_steps):
            return {**planned, "plan": {
                **planned["plan"],
                "phase": "faction_gift_typed_submit",
                "selected_step": FACTION_GIFT_SUBMIT_STEP,
                "faction_gift_action": deepcopy(candidate),
                "faction_gift_private_candidate_v1": deepcopy(candidate),
            }}

        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.plan_faction_gift_private_v1",
            side_effect=gift_consumer,
        ) as gift):
            planned = GameplayBridgeService(driver).plan_turn()
        gift.assert_called_once()
        self.assertEqual(planned["plan"]["selected_step"], FACTION_GIFT_SUBMIT_STEP)
        self.assertTrue(planned["plan"]["m5_joint_formal_action_ready"])
        self.assertEqual(driver.source_reads, 1)

    def test_gift_without_formal_opt_in_does_not_block_normal_advance(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(
            enabled=True,
            sources=_sources(domains={"diplomacy": _diplomacy_source()}),
            snapshot=peace,
        )
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(planned["plan"]["m5_joint_query_only"]["collected_domains"],
                         ["diplomacy"])
        self.assertEqual(planned["plan"]["m5_joint_status"],
                         "selected_gift_formal_consumer_disabled")
        self.assertEqual(driver.source_reads, 1)

    def test_pending_gift_uses_existing_cold_recovery_before_m5_source(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        driver.state_dir = Path("Z:/jt54-tmp")
        driver.allow_private_faction_gift_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def gift_recovery(driver, planned, snapshot, history, available_steps):
            return {**planned, "plan": {
                **planned["plan"], "phase": "faction_gift_pending_verification",
                "selected_step": FACTION_GIFT_COLD_RECOVERY_STEP,
            }}

        with (mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.read_construction_ledger",
            return_value={"pending": None, "applied": None},
        ), mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.read_faction_gift_ledger_v1",
            return_value={"pending": {"request_id": "gift-already-sent"}},
        ), mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.plan_faction_gift_private_v1",
            side_effect=gift_recovery,
        ) as gift):
            planned = plan_m5_formal_query_only(
                driver, {"revision": _FRAME["revision"], "plan": baseline},
                snapshot=peace, history=[], available_steps=set(),
            )
        gift.assert_called_once()
        self.assertEqual(planned["plan"]["selected_step"],
                         FACTION_GIFT_COLD_RECOVERY_STEP)
        self.assertEqual(driver.source_reads, 0)

    def test_pending_gift_same_date_refresh_reaches_service_replan(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        driver.state_dir = Path("Z:/fa98-tmp")
        driver.allow_private_faction_gift_formal_trial = True
        driver._session_bridge_pid = 12345
        pending = {
            "request_id": "gift-pending-same-date",
            "source_bridge_pid": 12345,
            "source_bridge_creation_date": "old-process",
            "episode_run_id": peace["episode_run_id"],
            "pre_snapshot_revision": peace["native_revision"],
            "pre_date_raw": peace["date_raw"],
        }
        fresh = {**peace, "revision": peace["revision"] + 1,
                 "native_revision": peace["native_revision"] + 1,
                 "snapshot_id": "native:18"}
        waits: list[float] = []

        def native_wait(start, predicate, *, timeout_seconds):
            self.assertEqual(start["snapshot_id"], peace["snapshot_id"])
            self.assertTrue(predicate(fresh))
            waits.append(timeout_seconds)
            return fresh

        driver._wait_for_snapshot = native_wait
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}
        service = GameplayBridgeService(driver)
        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.read_construction_ledger",
            return_value={"pending": None, "applied": None},
        ), mock.patch(
            "xar_autoplayer.m5_formal_proposal_collector.read_faction_gift_ledger_v1",
            return_value={"pending": pending},
        ), mock.patch(
            "xar_autoplayer.bridge.faction_gift_formal_route_v1.read_faction_gift_ledger_v1",
            return_value={"pending": pending},
        ), mock.patch(
            "xar_autoplayer.bridge.faction_gift_formal_route_v1._process_identity",
            return_value={"creation_date": "old-process"},
        )):
            with self.assertRaises(PreSubmissionRevisionMismatchError):
                service.plan_turn()
            driver._snapshot = fresh
            receipt = service.plan_turn()
        self.assertEqual(waits, [5.0])
        self.assertEqual(receipt["plan"]["selected_step"], FACTION_GIFT_RECEIPT_STEP)
        self.assertEqual(driver.source_reads, 0)

    def test_live_empty_peace_source_keeps_family_and_normal_advance(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        driver = _ServiceDriver(
            enabled=True, sources=_sources(domains={}), snapshot=peace,
        )
        driver.allow_private_family_marriage_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        def family_no_positive(driver, planned, snapshot, **kwargs):
            return {**planned, "plan": {**planned["plan"],
                "family_marriage_status": "no_new_proposal"}}

        with (mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.bridge.service.plan_family_marriage_private",
            side_effect=family_no_positive,
        ) as family):
            planned = GameplayBridgeService(driver).plan_turn()

        family.assert_called_once()
        self.assertEqual(driver.source_reads, 1)
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(planned["plan"]["phase"], "m5_joint_empty_proposals")
        self.assertEqual(planned["plan"]["family_marriage_status"],
                         "no_new_proposal")
        collection = planned["plan"]["m5_joint_query_only"]
        self.assertEqual(collection["status"], "no_complete_feasible_proposal")
        self.assertEqual(collection["collected_domains"], [])
        self.assertFalse(planned["plan"]["m5_joint_formal_action_ready"])

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

    def test_wartime_building_cannot_spend_without_complete_war_cash(self) -> None:
        sources = _sources(domains={"building": _building_source()})
        sources.pop("war_cash_resource")
        with self.assertRaisesRegex(ValueError, "complete same-frame"):
            collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)

        sources = _sources(domains={"building": _building_source()})
        sources["gold_reserve_raw"] = 4_999_999
        with self.assertRaisesRegex(ValueError, "omits active-war cash"):
            collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)

        sources = _sources(domains={"building": _building_source()})
        sources["war_cash_resource"]["observed_treasury_raw"] += 1
        with self.assertRaisesRegex(ValueError, "treasury differs"):
            collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)

    def test_war_quote_cannot_be_reused_for_another_step_at_same_price(self) -> None:
        sources = _sources()
        quote = sources["domains"]["war"]["observation"]["immediate_action_quote"]
        quote["selected_step"] = "query-different-war-step"
        with self.assertRaisesRegex(ValueError, "quote changed frame, WarID or selected command"):
            collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)

    def test_pending_war_cash_must_enter_existing_commitments_once(self) -> None:
        sources = _sources(domains={"building": _building_source()})
        cash = _war_cash(2_000_000, "test-observed-pending-ledger")
        sources["war_cash_resource"] = cash
        with self.assertRaisesRegex(ValueError, "omits active-war cash"):
            collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)
        sources["existing_commitments"]["gold_raw"] = 2_000_000
        result = collect_m5_formal_proposals(snapshot=_snapshot(), sources=sources)
        self.assertEqual(result["status"], "reserved_analytic")
        self.assertEqual(
            result["dispatch"]["reservation"]["commitments_after"]["gold_raw"],
            5_000_000,
        )

    def test_marriage_inventory_is_not_an_admitted_source_domain(self) -> None:
        with self.assertRaisesRegex(ValueError, "marriage.plan is unavailable"):
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
        for key, value in baseline.items():
            self.assertEqual(planned["plan"][key], value)
        wartime = planned["plan"]["m5_joint_wartime_observation"]
        self.assertTrue(wartime["read_only"])
        self.assertFalse(wartime["formal_action_ready"])
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

    def test_unavailable_joint_root_keeps_independent_family_action(self) -> None:
        peace = _snapshot()
        peace["active_wars"] = []
        peace["player_armies"] = []
        peace["played_character"]["alive"] = True
        driver = _ServiceDriver(enabled=True, snapshot=peace)
        # All ledger reads below are mocked; this portable sentinel must stay
        # absent so the test cannot silently create campaign state.
        driver.state_dir = Path("c146-inert-state-dir")
        self.assertFalse(driver.state_dir.exists())
        driver.allow_private_family_marriage_formal_trial = True
        driver.allow_private_faction_gift_formal_trial = True
        baseline = {"policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": "life-advance"}

        for family_step in (FAMILY_SUBMIT_STEP, "life-advance"):
            with (self.subTest(family_step=family_step), mock.patch(
                "xar_autoplayer.bridge.service.choose_one_life_turn",
                return_value=deepcopy(baseline),
            ), mock.patch(
                "xar_autoplayer.m5_formal_proposal_collector.read_construction_ledger",
                return_value={"pending": None, "applied": None},
            ), mock.patch(
                "xar_autoplayer.m5_formal_proposal_collector.read_faction_gift_ledger_v1",
                return_value={"pending": None},
            ), mock.patch(
                "xar_autoplayer.m5_formal_proposal_collector.read_family_marriage_ledger",
                return_value={"pending": None, "resolved": None},
            ), mock.patch(
                "xar_autoplayer.bridge.service.plan_family_marriage_private",
                side_effect=lambda driver, planned, snapshot, **kwargs: {
                    **planned, "plan": {**planned["plan"],
                        "selected_step": family_step,
                        "family_marriage_status": (
                            "native_final_legal_selected"
                            if family_step == FAMILY_SUBMIT_STEP else "no_new_proposal"
                        ),
                    },
                },
            ) as family):
                planned = GameplayBridgeService(driver).plan_turn()
            family.assert_called_once()
            self.assertEqual(family.call_args.args[1]["plan"]["selected_step"],
                             "life-advance")
            self.assertEqual(family.call_args.args[2]["snapshot_id"],
                             peace["snapshot_id"])
            self.assertEqual(driver.source_reads, 0)
            self.assertEqual(planned["plan"]["m5_joint_status"],
                             "same_frame_faction_root_unavailable")
            self.assertIn("same-frame faction root",
                          planned["plan"]["m5_joint_red_reason"])
            self.assertEqual(planned["plan"]["selected_step"],
                             FAMILY_SUBMIT_STEP if family_step == FAMILY_SUBMIT_STEP
                             else None)
            self.assertFalse(planned["plan"]["m5_joint_formal_action_ready"])
            self.assertFalse(driver.state_dir.exists())

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


class M5WartimeObservationTests(unittest.TestCase):
    def _plan(self, observation: object) -> dict[str, object]:
        return {
            "revision": _FRAME["revision"],
            "plan": {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_forecast_inputs_query",
                "selected_step": "query-combat-simulation-inputs-v3-2629",
                "construction_wartime_observation": observation,
            },
        }

    def _construction(self) -> dict[str, object]:
        return {
            "status": "observed",
            "native_source_status": "selected",
            "native_budgeted_positive_income_candidate": True,
            "candidate": {
                "barony_title_id": 2103,
                "province_id": 2635,
                "slot_index": 1,
                "building_key": "farm_estates_01",
                "stock_gold_cost_raw": 18_000_000,
                "authored_monthly_income_hundredths": 70,
            },
            "observed_player_gold_raw": 40_000_000,
            "observed_active_war_count": 1,
            "source_frame": {
                "snapshot_id": _FRAME["snapshot_id"],
                "revision": _FRAME["revision"],
                "native_revision": _FRAME["native_revision"],
                "date_raw": _FRAME["date_raw"],
                "episode_run_id": _FRAME["episode_run_id"],
                "actor_character_id": _FRAME["played_character_id"],
            },
        }

    def test_h3075_type_building_remains_read_only_with_war_cash_missing(self):
        original = self._plan(self._construction())
        result = plan_m5_wartime_query_only(
            object(), original, snapshot=_snapshot(), history=[],
            available_steps=set(),
        )
        plan = result["plan"]
        self.assertEqual(plan["selected_step"], original["plan"]["selected_step"])
        self.assertEqual(plan["phase"], original["plan"]["phase"])
        observed = plan["m5_joint_wartime_observation"]
        self.assertEqual(observed["status"], "incomplete_war_cash")
        self.assertEqual(observed["war_ids"], [16777231])
        self.assertIn("future_war_cost_upper_raw", observed["missing"])
        self.assertIn("pending_war_cash_raw", observed["missing"])
        self.assertIsNone(observed["immediate_war_action_cost_observation"])
        self.assertFalse(observed["formal_action_ready"])
        self.assertEqual(observed["candidate"]["stock_gold_cost_raw"], 18_000_000)
        self.assertNotIn("m5_joint_wartime_observation", original["plan"])

    def test_explicit_same_frame_no_war_step_produces_only_immediate_zero(self):
        planned = self._plan(self._construction())
        planned["snapshot_id"] = _FRAME["snapshot_id"]
        planned["plan"]["selected_step"] = None
        result = plan_m5_wartime_query_only(
            object(), planned, snapshot=_snapshot(), history=[],
            available_steps=set(),
        )
        observed = result["plan"]["m5_joint_wartime_observation"]
        self.assertEqual(observed["status"], "incomplete_war_cash")
        self.assertNotIn("immediate_war_action_cost_raw", observed["missing"])
        self.assertIn("pending_war_cash_raw", observed["missing"])
        self.assertIn("future_war_cost_upper_raw", observed["missing"])
        fee = observed["immediate_war_action_cost_observation"]
        self.assertEqual(fee["immediate_war_action_cost_raw"]["raw"], 0)
        self.assertEqual(fee["immediate_war_action_cost_raw"]["source_frame"], _FRAME)
        self.assertFalse(fee["formal_cash_receipt_eligible"])
        compact = _compact_plan(result["plan"])["m5_joint_wartime_observation"]
        self.assertEqual(compact["immediate_war_action_cost_observation"]
                         ["immediate_war_action_cost_raw"]["raw"], 0)
        self.assertEqual(compact["missing_count"], 6)

        forged = {**result["plan"], "selected_step": "move-army-71-to-22"}
        self.assertNotIn(
            "immediate_war_action_cost_observation",
            _compact_plan(forged)["m5_joint_wartime_observation"],
        )
        self.assertIn(
            "immediate_war_action_cost_raw",
            _compact_plan(forged)["m5_joint_wartime_observation"]["missing"],
        )

    def test_stale_no_step_plan_does_not_publish_immediate_zero(self):
        planned = self._plan(self._construction())
        planned["snapshot_id"] = "native:older"
        planned["plan"]["selected_step"] = None
        result = plan_m5_wartime_query_only(
            object(), planned, snapshot=_snapshot(), history=[],
            available_steps=set(),
        )
        observed = result["plan"]["m5_joint_wartime_observation"]
        self.assertIn("immediate_war_action_cost_raw", observed["missing"])
        self.assertIsNone(observed["immediate_war_action_cost_observation"])
        self.assertIn("crossed", observed["cash_input_missing_reasons"]
                      ["immediate_war_action_cost_raw"])

    def test_wartime_comparison_survives_bounded_formal_turn_report(self):
        result = plan_m5_wartime_query_only(
            object(), self._plan(self._construction()),
            snapshot=_snapshot(), history=[], available_steps=set(),
        )
        result["plan"]["m5_joint_wartime_observation"]["candidate"][
            "private_unbounded_detail"
        ] = {"discard": True}
        compact = _compact_plan(result["plan"])
        self.assertEqual(compact["selected_step"],
                         "query-combat-simulation-inputs-v3-2629")
        observed = compact["m5_joint_wartime_observation"]
        self.assertEqual(observed["status"], "incomplete_war_cash")
        self.assertEqual(observed["frame"]["date_raw"], _FRAME["date_raw"])
        self.assertEqual(observed["war_ids"], [16777231])
        self.assertEqual(observed["candidate"]["stock_gold_cost_raw"],
                         18_000_000)
        self.assertEqual(observed["candidate"][
            "authored_monthly_income_hundredths"], 70)
        self.assertNotIn("private_unbounded_detail", observed["candidate"])
        self.assertIn("future_war_cost_upper_raw", observed["missing"])
        self.assertFalse(observed["formal_action_ready"])
        self.assertNotIn("m5_joint_wartime_observation", _compact_plan({
            "selected_step": "query-combat-simulation-inputs-v3-2629",
        }))

    def test_stale_construction_frame_does_not_become_a_joint_candidate(self):
        construction = self._construction()
        construction["source_frame"]["date_raw"] += 24
        result = plan_m5_wartime_query_only(
            object(), self._plan(construction), snapshot=_snapshot(),
            history=[], available_steps=set(),
        )
        observed = result["plan"]["m5_joint_wartime_observation"]
        self.assertEqual(observed["status"], "construction_observation_frame_mismatch")
        self.assertIsNone(observed["candidate"])
        self.assertIn("same_frame_native_budgeted_building", observed["missing"])
        self.assertFalse(observed["formal_action_ready"])

    def test_complete_empty_building_source_is_no_opportunity(self):
        construction = self._construction()
        construction["native_source_status"] = "no_legal_budgeted_building"
        construction["native_budgeted_positive_income_candidate"] = False
        construction["candidate"] = None
        construction["positive_income_coverage_complete"] = True
        result = plan_m5_wartime_query_only(
            object(), self._plan(construction), snapshot=_snapshot(),
            history=[], available_steps=set(),
        )
        observed = result["plan"]["m5_joint_wartime_observation"]
        self.assertEqual(observed["status"], "no_budgeted_building_observed")
        self.assertEqual(observed["missing"], [])
        self.assertIsNone(observed["candidate"])
        self.assertFalse(observed["formal_action_ready"])


if __name__ == "__main__":
    unittest.main()
