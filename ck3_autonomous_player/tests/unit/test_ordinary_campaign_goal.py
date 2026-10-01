from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.declaration_contract import QUERY_DECLARABLE_WARS_STEP
from xar_autoplayer.bridge.marriage_contract import (
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
)
from xar_autoplayer.strategy import (
    new_ordinary_campaign_goal_v1,
    normalize_ordinary_campaign_goal_v1,
    ordinary_campaign_goal_plan_v1,
)
from test_native_bridge_driver import _write_driver_state_checkpoint_fixture
from test_succession_transition_contract import (
    _FakeEndpoint,
    _bundle,
    _hello,
    _native_snapshot,
    _ordinary_binding,
    _row,
)


_ROGUE_WAR_PRIORITIES = [
    {"priority": 100, "action": "reassess_first_low_cost_expansion"},
    {"priority": 80, "action": "seek_current_life_marriage_alliance"},
]
_OPENING_CAPABILITIES = {
    "action_steps": [
        QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
        QUERY_DECLARABLE_WARS_STEP,
        "life-advance",
    ],
    "bridge_capabilities": [],
}
_SUCCESSION_CAPABILITIES = {
    "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP],
    "bridge_capabilities": [],
}


def _write_rogue_war_plan(state_dir: Path) -> None:
    path = state_dir / "strategy" / "one-life-history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "mode": "one_life_roguelike",
                "continue_as_heir_after_death": False,
                "episodes": [{"run_id": "previous-rogue-run"}],
                "next_run_plan": {
                    "policy": "fixture-rogue-war-first",
                    "continue_as_heir_after_death": False,
                    "priorities": copy.deepcopy(_ROGUE_WAR_PRIORITIES),
                },
            }
        ),
        encoding="utf-8",
    )


def _checkpoint_receipt(driver: NativeHeadlessGameplayDriver) -> None:
    # Inject only an offline fixture receipt through the existing recorder.
    # The formal planner still consumes the actual driver's command history.
    driver._record_command(
        "save-checkpoint", ok=True, result={"step": "save-checkpoint"}
    )


def _succession_bundle(
    snapshot: dict[str, object], *, actor: int, heir: int
) -> dict[str, object]:
    return _bundle(
        character_id=actor,
        snapshot_id=str(snapshot["snapshot_id"]),
        revision=int(snapshot["revision"]),
        native_revision=int(snapshot["native_revision"]),
        date_raw=int(snapshot["date_raw"]),
        title_rows=[
            _row(10, heir, primary=True),
            _row(11, heir, primary=False),
        ],
        primary_heir=heir,
    )


class OrdinaryCampaignGoalTests(unittest.TestCase):
    def test_goal_round_trip_keeps_campaign_intent_and_marriage_priority(self) -> None:
        goal = new_ordinary_campaign_goal_v1("ordinary-campaign-fixture", 100)
        before = copy.deepcopy(goal)

        restored = normalize_ordinary_campaign_goal_v1(
            json.loads(json.dumps(goal))
        )
        plan = ordinary_campaign_goal_plan_v1(restored)

        self.assertEqual(restored, before)
        self.assertEqual(goal["goal_key"], "dynasty_continuity")
        self.assertEqual(goal["campaign_id"], "ordinary-campaign-fixture")
        self.assertEqual(goal["origin_character_id"], 100)
        self.assertEqual(goal["current_character_id"], 100)
        self.assertEqual(goal["progress"]["reconciled_successions"], 0)
        self.assertIsNone(goal["progress"]["last_succession"])
        self.assertEqual(plan["policy"], "ordinary-campaign-goal-v1")
        self.assertEqual(plan["focus"], "marriage")
        self.assertEqual(
            plan["priorities"][0]["action"],
            "seek_current_ruler_marriage_and_family_continuity",
        )
        self.assertEqual(goal, before)

    def test_retained_goal_drives_successor_plan_after_real_continuation(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".ordinary-goal-", dir=PROJECT_ROOT.parent
        ) as temporary:
            state_dir = Path(temporary)
            _write_rogue_war_plan(state_dir)
            endpoint = _FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            self.addCleanup(driver.close)
            endpoint.publish(_hello())
            endpoint.publish(
                _native_snapshot(20, character_id=100, date_raw=53_180_000)
            )
            before = driver.take_snapshot()
            goal = copy.deepcopy(before["campaign_goal"])
            self.assertEqual(goal["current_character_id"], 100)
            service = GameplayBridgeService(driver)
            with mock.patch.object(
                service,
                "query_turn_bundle_v1",
                return_value=_succession_bundle(before, actor=100, heir=200),
            ), mock.patch.object(
                service, "capabilities", return_value=_SUCCESSION_CAPABILITIES
            ):
                service.plan_turn()

            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["campaign_goal"], goal)
            retained_expectation = persisted["succession_expectation"]
            driver.close()

            restored_endpoint = _FakeEndpoint(endpoint.pipe_name)
            restored = NativeHeadlessGameplayDriver(
                restored_endpoint.pipe_name,
                endpoint=restored_endpoint,
                state_dir=state_dir,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            self.addCleanup(restored.close)
            restored_endpoint.publish(_hello())
            restored_endpoint.publish(
                _native_snapshot(21, character_id=100, date_raw=53_180_000)
            )
            resumed = restored.take_snapshot()
            self.assertEqual(resumed["campaign_goal"], goal)
            self.assertEqual(resumed["succession_expectation"], retained_expectation)
            self.assertEqual(
                restored.capabilities()["native_session_control"][
                    "driver_state_restore_kind"
                ],
                "same_pid_hot",
            )

            restored_endpoint.publish(
                _native_snapshot(24, character_id=200, date_raw=53_180_720)
            )
            transition = restored.take_snapshot()
            restored_service = GameplayBridgeService(restored)
            with mock.patch.object(
                restored_service,
                "query_turn_bundle_v1",
                return_value=_succession_bundle(transition, actor=200, heir=400),
            ), mock.patch.object(
                restored_service,
                "capabilities",
                return_value=_SUCCESSION_CAPABILITIES,
            ):
                restored_service.plan_turn()

            reconciled = restored.take_snapshot()
            self.assertEqual(reconciled["succession_reconciliation"]["verdict"], "matched")
            turn = restored_service.auto_turn()
            self.assertEqual(turn["status"], "executed")
            self.assertEqual(
                turn["plan"]["selected_step"],
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            )
            self.assertEqual(turn["result"]["successor_character_id"], 200)
            self.assertFalse(turn["result"]["ck3_command_submitted"])

            continued = restored.take_snapshot()
            successor_goal = continued["campaign_goal"]
            self.assertEqual(successor_goal["campaign_id"], goal["campaign_id"])
            self.assertEqual(successor_goal["goal_key"], goal["goal_key"])
            self.assertEqual(successor_goal["origin_character_id"], 100)
            self.assertEqual(successor_goal["current_character_id"], 200)
            self.assertEqual(successor_goal["progress"]["reconciled_successions"], 1)
            self.assertIsInstance(successor_goal["progress"]["last_succession"], dict)
            self.assertEqual(continued["episode_character_id"], 200)
            self.assertFalse(continued["one_life_terminal"])

            _checkpoint_receipt(restored)
            with mock.patch.object(
                restored_service,
                "capabilities",
                return_value=_OPENING_CAPABILITIES,
            ):
                plan = restored_service.plan_turn()["plan"]

            self.assertEqual(
                plan["selected_step"], QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
            )
            self.assertEqual(
                plan["campaign_goal_plan_used"],
                ordinary_campaign_goal_plan_v1(successor_goal),
            )
            self.assertEqual(plan["campaign_goal_plan_used"]["focus"], "marriage")
            self.assertIsNone(plan.get("cross_run_plan_used"))
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["campaign_goal"], successor_goal)
            restored.close()

    def test_cold_checkpoint_restore_retains_the_ordinary_campaign_goal(self) -> None:
        # The checkpoint contains fixture bytes, not a game-created save or live proof.
        with tempfile.TemporaryDirectory(
            prefix=".ordinary-goal-cold-", dir=PROJECT_ROOT.parent
        ) as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_ordinary_goal_cold_fixture"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=4242,
                character_id=100,
                run_id="native-100-ordinary-cold",
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            goal = new_ordinary_campaign_goal_v1("ordinary-campaign-cold-fixture", 100)
            persisted["succession_lifecycle"] = _ordinary_binding()
            persisted["campaign_goal"] = goal
            state_path.write_text(json.dumps(persisted), encoding="utf-8")

            endpoint = _FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            self.addCleanup(driver.close)
            endpoint.publish({**_hello(), "pid": 5252})
            endpoint.publish(
                _native_snapshot(
                    1,
                    character_id=100,
                    date_raw=int(checkpoint["date_raw"]),
                )
            )

            resumed = driver.take_snapshot()
            self.assertEqual(resumed["campaign_goal"], goal)
            self.assertEqual(resumed["episode_run_id"], "native-100-ordinary-cold")
            self.assertEqual(
                driver.capabilities()["native_session_control"][
                    "driver_state_restore_kind"
                ],
                "cold_checkpoint",
            )
            self.assertEqual(
                resumed["native_command_history"][-1]["command"],
                "restore-checkpoint",
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["campaign_goal"],
                goal,
            )
            driver.close()

    def test_rogue_driver_preserves_the_existing_cross_run_war_priority(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".rogue-goal-regression-", dir=PROJECT_ROOT.parent
        ) as temporary:
            state_dir = Path(temporary)
            _write_rogue_war_plan(state_dir)
            endpoint = _FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir
            )
            self.addCleanup(driver.close)
            endpoint.publish(_hello())
            endpoint.publish(
                _native_snapshot(20, character_id=100, date_raw=53_180_000)
            )
            snapshot = driver.take_snapshot()
            self.assertIsNone(snapshot["campaign_goal"])
            _checkpoint_receipt(driver)
            service = GameplayBridgeService(driver)
            with mock.patch.object(
                service, "capabilities", return_value=_OPENING_CAPABILITIES
            ):
                plan = service.plan_turn()["plan"]

            self.assertEqual(plan["selected_step"], QUERY_DECLARABLE_WARS_STEP)
            self.assertEqual(
                plan["cross_run_plan_used"]["priorities"], _ROGUE_WAR_PRIORITIES
            )
            self.assertIsNone(plan.get("campaign_goal_plan_used"))
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIsNone(persisted["campaign_goal"])
            driver.close()


if __name__ == "__main__":
    unittest.main()
