from __future__ import annotations

import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
from unittest import mock
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import cli
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import EnvironmentSpec
from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher
from xar_autoplayer.m5_formal_proposal_collector import (
    collect_m5_formal_proposals,
)
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import (
    PRODUCER_POLICY,
    query_m5_peacetime_proposal_sources_v1,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig
import xar_autoplayer.native_auto_run as native_auto_run_module


_FRAME = {
    "played_character_id": 29829,
    "native_revision": 17,
    "date_raw": 53202168,
    "snapshot_id": "native:17",
    "revision": 23,
    "episode_run_id": "native-29829-m5-peace",
}


def _root(*, count: int = 1) -> dict[str, object]:
    return {
        "status": "available",
        "snapshot_revision": _FRAME["native_revision"],
        "date_raw": _FRAME["date_raw"],
        "player_character_id": _FRAME["played_character_id"],
        "player_character_alive": True,
        "government": {"key": "feudal_government"},
        "player_targeting_faction_count": count,
        "direct_landed_vassal_character_ids": [41003],
    }


def _history(*, count: int = 1) -> list[dict[str, object]]:
    return [{
        "command": "query-campaign-root-context-v1",
        "ok": True,
        "result": {
            "status": "available",
            "campaign_root_context": _root(count=count),
        },
    }]


def _snapshot(*, faction_count: int = 1) -> dict[str, object]:
    return {
        **_FRAME,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "played_character_gold": {"raw": 40_000_000, "scale": 100_000},
        "active_event": None,
        "pending_character_interaction": None,
        "one_life_terminal_reason": None,
        "active_wars": [],
        "player_armies": [],
        "history": [],
        "native_command_history": _history(count=faction_count),
    }


def _construction(*, status: str = "selected") -> dict[str, object]:
    result: dict[str, object] = {
        "status": status,
        "world": {"player_gold_raw": 40_000_000},
        "source_frame": {
            **_FRAME,
            "actor_character_id": _FRAME["played_character_id"],
        },
    }
    if status == "selected":
        result["candidate"] = {
            "barony_title_id": 501,
            "province_id": 601,
            "building_type_id": 701,
            "slot_index": 1,
            "stock_gold_cost_raw": 3_000_000,
            "gold_before_raw": 40_000_000,
        }
    return result


def _faction(*, status: str = "selected") -> dict[str, object]:
    observation = {
        "snapshot_revision": _FRAME["native_revision"],
        "native_snapshot_revision": _FRAME["native_revision"],
        "observed_date_raw": _FRAME["date_raw"],
        "player_character_id": _FRAME["played_character_id"],
        "player_gold_raw": 40_000_000,
    }
    result: dict[str, object] = {
        "status": status,
        "observation": observation,
        "public_capability_advertised": False,
        "gift_submission_enabled": False,
    }
    if status == "selected":
        result["choice"] = {
            "snapshot_revision": _FRAME["native_revision"],
            "native_snapshot_revision": _FRAME["native_revision"],
            "date_raw": _FRAME["date_raw"],
            "player_character_id": _FRAME["played_character_id"],
            "source_faction_id": 801,
            "recipient_character_id": 41003,
            "gold_cost_raw": 2_000_000,
            "opinion_delta": 20,
            "minimum_gold_reserve_raw": 10_000_000,
        }
    return result


class _Driver:
    def __init__(
        self,
        state_dir: Path,
        *,
        enabled: bool = True,
        snapshot: dict[str, object] | None = None,
        faction: dict[str, object] | None = None,
        drift_on_internal_read: int | None = None,
    ) -> None:
        self.state_dir = state_dir
        self.allow_private_m5_joint_collector = enabled
        self._snapshot = deepcopy(snapshot or _snapshot())
        self._faction = deepcopy(faction or _faction())
        self.drift_on_internal_read = drift_on_internal_read
        self.internal_reads = 0
        self.source_reads = 0
        self.faction_reads = 0

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self._snapshot)

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        self.internal_reads += 1
        result = deepcopy(self._snapshot)
        if self.internal_reads == self.drift_on_internal_read:
            result["native_revision"] = 18
            result["snapshot_id"] = "native:18"
        return result

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["life-advance"], "bridge_capabilities": []}

    def query_faction_gift_private_candidate_v1(
        self, **kwargs: object,
    ) -> dict[str, object]:
        self.faction_reads += 1
        self.faction_kwargs = deepcopy(kwargs)
        return deepcopy(self._faction)

    def query_m5_joint_proposal_sources_private_v1(
        self, **kwargs: object,
    ) -> dict[str, object]:
        self.source_reads += 1
        return query_m5_peacetime_proposal_sources_v1(self, **kwargs)


class M5PeacetimeProposalSourcesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._temporary.name) / "state"

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def _query(
        self, driver: _Driver, *, history: list[dict[str, object]] | None = None,
        construction: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "query_construction_private",
            return_value=deepcopy(construction or _construction()),
        ):
            return query_m5_peacetime_proposal_sources_v1(
                driver,
                snapshot=driver.take_snapshot(),
                history=deepcopy(_history() if history is None else history),
                baseline_plan={
                    "policy": "one-life-turn-v1",
                    "phase": "peace_growth",
                    "selected_step": "life-advance",
                },
                expected_revision=_FRAME["revision"],
            )

    def test_two_real_peacetime_sources_feed_existing_collector_once(
        self,
    ) -> None:
        driver = _Driver(self.state_dir)
        baseline = {
            "policy": "one-life-turn-v1",
            "phase": "peace_growth",
            "selected_step": "life-advance",
            "reason": "ordinary peacetime planning",
        }
        original = M5FrameDispatcher.choose_observed

        def call_original(
            dispatcher: M5FrameDispatcher, **kwargs: object,
        ) -> dict[str, object]:
            return original(dispatcher, **kwargs)

        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ), mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "query_construction_private",
            return_value=_construction(),
        ), mock.patch.object(
            M5FrameDispatcher,
            "choose_observed",
            autospec=True,
            side_effect=call_original,
        ) as dispatch:
            planned = GameplayBridgeService(driver).plan_turn()

        self.assertEqual(driver.source_reads, 1)
        self.assertEqual(driver.faction_reads, 1)
        self.assertEqual(dispatch.call_count, 1)
        collection = planned["plan"]["m5_joint_query_only"]
        self.assertCountEqual(
            collection["collected_domains"], ["building", "diplomacy"]
        )
        self.assertEqual(
            collection["dispatch"]["selected_candidate_id"],
            "diplomacy:faction-gift:801:41003",
        )
        evaluated = {
            row["domain"]: row
            for row in collection["dispatch"]["analysis"]["evaluated"]
        }
        self.assertEqual(evaluated["building"]["gold_cost_raw"], 3_000_000)
        self.assertEqual(
            evaluated["building"]["minimum_gold_reserve_raw"], 20_000_000
        )
        self.assertEqual(
            evaluated["building"]["commitment_keys"],
            ["building-slot:501:1"],
        )
        self.assertEqual(evaluated["diplomacy"]["gold_cost_raw"], 2_000_000)
        self.assertEqual(
            evaluated["diplomacy"]["minimum_gold_reserve_raw"], 10_000_000
        )
        self.assertEqual(
            evaluated["diplomacy"]["commitment_keys"],
            ["faction-gift:801:41003"],
        )
        reservation = collection["dispatch"]["reservation"]
        self.assertEqual(reservation["domain"], "diplomacy")
        self.assertEqual(
            reservation["commitments_after"]["gold_raw"], 2_000_000
        )
        self.assertEqual(
            reservation["commitments_after"]["pending_war_slots"], 0
        )
        self.assertEqual(
            reservation["commitments_after"]["commitment_keys"],
            ["faction-gift:801:41003"],
        )
        self.assertNotIn(
            "building-slot:501:1",
            reservation["commitments_after"]["commitment_keys"],
        )
        self.assertIsNone(planned["plan"]["selected_step"])
        self.assertFalse(planned["plan"]["m5_joint_formal_action_ready"])

    def test_one_ready_building_avoids_query_only_noop(self) -> None:
        driver = _Driver(
            self.state_dir, snapshot=_snapshot(faction_count=0)
        )
        result = self._query(driver, history=_history(count=0))
        self.assertEqual(driver.faction_reads, 0)
        self.assertEqual(list(result["domains"]), ["building"])
        self.assertEqual(result["producer"]["faction_status"], "known_empty")
        self.assertEqual(result["max_active_wars"], 0)
        self.assertEqual(result["gold_reserve_raw"], 0)
        self.assertEqual(result["existing_commitments"]["commitment_keys"], [])

    def test_drift_and_partial_data_are_red(self) -> None:
        drifted = _Driver(
            self.state_dir / "drift",
            drift_on_internal_read=3,
        )
        with self.assertRaisesRegex(
            BridgeUnavailableError, "crossed its paused frame"
        ):
            self._query(drifted)

        missing_root = _Driver(self.state_dir / "root")
        with self.assertRaisesRegex(
            BridgeUnavailableError, "same-frame feudal faction root"
        ):
            self._query(missing_root, history=[])

        incomplete = _Driver(
            self.state_dir / "partial",
            faction=_faction(status="unavailable"),
        )
        with self.assertRaisesRegex(
            BridgeUnavailableError, "faction source is incomplete"
        ):
            self._query(incomplete)

    def test_nonempty_pending_ledger_blocks_before_any_source_query(self) -> None:
        state_dir = self.state_dir
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "construction-formal-pending-v1.json").write_text(
            json.dumps({
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": {"episode_run_id": _FRAME["episode_run_id"]},
                "applied": None,
            }),
            encoding="utf-8",
        )
        driver = _Driver(state_dir)
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "query_construction_private"
        ) as construction:
            with self.assertRaisesRegex(
                BridgeUnavailableError, "unresolved construction"
            ):
                query_m5_peacetime_proposal_sources_v1(
                    driver,
                    snapshot=driver.take_snapshot(),
                    history=_history(),
                    baseline_plan={
                        "policy": "one-life-turn-v1",
                        "selected_step": "life-advance",
                    },
                    expected_revision=_FRAME["revision"],
                )
        construction.assert_not_called()
        self.assertEqual(driver.faction_reads, 0)

    def test_applied_building_omits_only_building_and_keeps_faction_choice(
        self,
    ) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "construction-formal-pending-v1.json").write_text(
            json.dumps({
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": None,
                "applied": {"episode_run_id": _FRAME["episode_run_id"]},
            }),
            encoding="utf-8",
        )
        driver = _Driver(self.state_dir)
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "query_construction_private"
        ) as construction:
            sources = query_m5_peacetime_proposal_sources_v1(
                driver,
                snapshot=driver.take_snapshot(),
                history=_history(),
                baseline_plan={
                    "policy": "one-life-turn-v1",
                    "selected_step": "life-advance",
                },
                expected_revision=_FRAME["revision"],
            )
        construction.assert_not_called()
        self.assertEqual(list(sources["domains"]), ["diplomacy"])
        self.assertEqual(
            sources["producer"]["construction_status"],
            "prior_receipt_not_released",
        )
        result = collect_m5_formal_proposals(
            snapshot=driver.take_snapshot(), sources=sources,
        )
        self.assertEqual(
            result["dispatch"]["selected_candidate_id"],
            "diplomacy:faction-gift:801:41003",
        )

    def test_later_day_verified_building_enters_joint_shortlist(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "construction-formal-pending-v1.json").write_text(
            json.dumps({
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": None,
                "applied": {
                    "status": "applied",
                    "postcondition_verified": True,
                    "episode_run_id": _FRAME["episode_run_id"],
                    "actor_character_id": _FRAME["played_character_id"],
                    "post_bridge_pid": 123,
                    "post_bridge_creation_date": "t1",
                    "post_native_revision": _FRAME["native_revision"] - 1,
                    "post_date_raw": _FRAME["date_raw"] - 24,
                },
            }),
            encoding="utf-8",
        )
        driver = _Driver(
            self.state_dir, snapshot=_snapshot(faction_count=0),
        )
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "construction_process_identity",
            return_value=(123, "t1"),
        ) as process, mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1."
            "query_construction_private",
            return_value=_construction(),
        ) as construction:
            sources = query_m5_peacetime_proposal_sources_v1(
                driver,
                snapshot=driver.take_snapshot(),
                history=_history(count=0),
                baseline_plan={
                    "policy": "one-life-turn-v1",
                    "selected_step": "life-advance",
                },
                expected_revision=_FRAME["revision"],
            )
        process.assert_called_once_with(driver)
        construction.assert_called_once_with(
            driver, expected_revision=_FRAME["revision"],
        )
        self.assertEqual(list(sources["domains"]), ["building"])
        self.assertEqual(sources["producer"]["construction_status"], "selected")
        result = collect_m5_formal_proposals(
            snapshot=driver.take_snapshot(), sources=sources,
        )
        self.assertEqual(
            result["dispatch"]["selected_candidate_id"],
            "building:501:701:1",
        )
        self.assertIsNone(result["selected_step"])
        self.assertFalse(result["formal_action_ready"])

    def test_active_war_or_player_army_is_out_of_scope(self) -> None:
        for field, row in (
            ("active_wars", {"war_id": 7}),
            ("player_armies", {"army_id": 9}),
        ):
            snapshot = _snapshot()
            snapshot[field] = [row]
            driver = _Driver(self.state_dir / field, snapshot=snapshot)
            with self.subTest(field=field), self.assertRaisesRegex(
                BridgeUnavailableError, "peaceful paused actor frame"
            ):
                self._query(driver)

    def test_default_off_preserves_plan_and_never_reads_sources(self) -> None:
        driver = _Driver(self.state_dir, enabled=False)
        baseline = {
            "policy": "one-life-turn-v1",
            "phase": "peace_growth",
            "selected_step": "life-advance",
            "reason": "unchanged default behavior",
        }
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=deepcopy(baseline),
        ):
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned["plan"], baseline)
        self.assertEqual(driver.source_reads, 0)
        self.assertEqual(driver.faction_reads, 0)

    def test_private_cli_flag_is_explicit_and_default_off(self) -> None:
        defaults = cli.parser().parse_args([
            "--bridge-mode", "native-headless",
            "native-auto-run", "--turns", "1",
        ])
        self.assertFalse(defaults.allow_private_m5_joint_collector)
        enabled = cli.parser().parse_args([
            "--bridge-mode", "native-headless",
            "native-auto-run", "--turns", "1",
            "--allow-private-m5-joint-collector",
        ])
        self.assertTrue(enabled.allow_private_m5_joint_collector)

    def test_private_cli_flag_reaches_native_runner_only_when_enabled(self) -> None:
        spec = EnvironmentSpec(self.state_dir, self.state_dir / "game")
        dll = Path(self._temporary.name) / "xar_ck3_bridge.dll"
        injector = Path(self._temporary.name) / "injector.exe"
        dll.write_bytes(b"fake dll")
        injector.write_bytes(b"fake injector")
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\m5-peace-source-test",
            dll_path=dll,
            injector_path=injector,
        )
        with mock.patch.object(
            cli, "make_spec", return_value=spec,
        ), mock.patch.object(
            cli,
            "configure_native_bridge_launch_environment",
            return_value=config,
        ), mock.patch.object(
            native_auto_run_module,
            "native_auto_run",
            return_value={"ok": False, "status": "blocked", "outcome": "failed"},
        ) as run, contextlib.redirect_stdout(io.StringIO()):
            code = cli.main([
                "--bridge-mode", "native-headless",
                "--bridge-dll", str(dll),
                "--bridge-injector", str(injector),
                "native-auto-run", "--turns", "1",
                "--allow-private-m5-joint-collector",
            ])
        self.assertEqual(code, 1)
        self.assertIs(
            run.call_args.kwargs["allow_private_m5_joint_collector"], True
        )

    def test_producer_metadata_stays_private_and_query_only(self) -> None:
        result = self._query(_Driver(self.state_dir))
        self.assertEqual(result["producer"]["policy"], PRODUCER_POLICY)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["advertised"])
        self.assertFalse(result["producer"]["formal_action_ready"])
        self.assertNotIn("war", result["domains"])
        self.assertNotIn("marriage", result["domains"])


if __name__ == "__main__":
    unittest.main()
