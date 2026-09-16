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

from xar_autoplayer.bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
    SUCCESSION_EXPECTATION_V1_SCHEMA,
    SUCCESSION_RECONCILIATION_V1_SCHEMA,
    bind_succession_lifecycle_from_environment_v1,
    freeze_succession_expectation_v1,
    legacy_rogue_one_life_binding_v1,
    normalize_succession_expectation_v1,
    reconcile_succession_transition_v1,
    unknown_succession_lifecycle_binding_v1,
)
from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn


_ENVIRONMENT_SHA256 = "a" * 64


def _manifest(xar_enabled: str) -> dict[str, object]:
    return {
        "environment_sha256": _ENVIRONMENT_SHA256,
        "rules": {
            "profile": [
                {"rule": "xar_enabled", "setting": xar_enabled},
            ]
        },
    }


def _ordinary_binding() -> dict[str, object]:
    return bind_succession_lifecycle_from_environment_v1(
        _manifest("xar_off"),
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )


class _FakeEndpoint:
    def __init__(self, pipe_name: str = r"\\.\pipe\xar_succession_fixture") -> None:
        self.pipe_name = pipe_name
        self.on_frame = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        return None

    def close(self) -> None:
        return None

    def transport_error(self) -> None:
        return None


def _hello() -> dict[str, object]:
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 4242,
        "session_generation": 0,
        "capabilities": ["game.state.snapshot", "game.state.played-character"],
    }


def _native_snapshot(
    revision: int,
    *,
    character_id: int,
    date_raw: int,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": date_raw,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": character_id, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


def _component(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _bundle(
    *,
    character_id: int,
    snapshot_id: str,
    revision: int,
    native_revision: int,
    date_raw: int,
    title_rows: list[dict[str, object]],
    primary_heir: int | None,
) -> dict[str, object]:
    heir = (
        _component(primary_heir)
        if primary_heir is not None
        else {
            "status": "not_applicable",
            "value": None,
            "unavailable_reason": "no_observed_primary_title_successor",
        }
    )
    return {
        "schema": "xar.ck3.turn-bundle/v1",
        "status": "available",
        "binding": {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
        },
        "ruler_state": _component(
            {"character_id": character_id, "alive": True}
        ),
        "succession_state": _component(
            {
                "primary_title_heir_character_id": heir,
                "partition": _component(
                    {
                        "title_heirs": title_rows,
                        "risk_state": (
                            "no_primary_heir"
                            if primary_heir is None
                            else "split_successors"
                        ),
                    }
                ),
            }
        ),
    }


def _row(title_id: int, heir_id: int | None, *, primary: bool) -> dict[str, object]:
    return {
        "title": {"title_id": title_id, "tier_raw": 4 if primary else 2, "tier_key": "kingdom" if primary else "county"},
        "first_heir_character_id": heir_id,
        "primary": primary,
    }


class SuccessionTransitionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pre = _bundle(
            character_id=100,
            snapshot_id="native:20",
            revision=7,
            native_revision=20,
            date_raw=53_180_000,
            title_rows=[
                _row(10, 200, primary=True),
                _row(11, 200, primary=False),
                _row(12, 300, primary=False),
                _row(13, None, primary=False),
            ],
            primary_heir=200,
        )
        self.post = _bundle(
            character_id=200,
            snapshot_id="native:24",
            revision=8,
            native_revision=24,
            date_raw=53_180_720,
            title_rows=[
                _row(10, 400, primary=True),
                _row(11, 400, primary=False),
                _row(99, 400, primary=False),
            ],
            primary_heir=400,
        )
        self.snapshot = {
            "snapshot_id": "native:24",
            "revision": 8,
            "native_revision": 24,
            "date_raw": 53_180_720,
            "paused": True,
            "played_character": {"character_id": 200, "alive": True},
            "episode_character_id": 100,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
        }

    def test_freezes_exact_per_title_expectation(self) -> None:
        result = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        self.assertEqual(result["schema"], SUCCESSION_EXPECTATION_V1_SCHEMA)
        self.assertEqual(result["expectation_state"], "successor_expected")
        self.assertEqual(result["expected_successor_character_id"], 200)
        self.assertEqual(result["binding"]["native_revision"], 20)
        self.assertEqual(
            [row["title"]["title_id"] for row in result["title_expectations"]],
            [10, 11, 12, 13],
        )

    def test_reconciles_only_titles_owned_by_the_predecessor(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        result = reconcile_succession_transition_v1(
            expectation, self.snapshot, self.post
        )

        self.assertEqual(result["schema"], SUCCESSION_RECONCILIATION_V1_SCHEMA)
        self.assertEqual(result["verdict"], "matched")
        self.assertTrue(result["successor_match"])
        self.assertTrue(result["title_distribution_match"])
        self.assertEqual(result["matched_inherited_title_ids"], [10, 11])
        self.assertEqual(result["expected_other_heir_title_ids"], [12])
        self.assertEqual(result["expected_without_heir_title_ids"], [13])
        self.assertEqual(result["observed_additional_successor_title_ids"], [99])

    def test_reports_successor_and_title_mismatches_without_inventing_holders(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )
        wrong_successor = copy.deepcopy(self.snapshot)
        wrong_successor["played_character"]["character_id"] = 201
        wrong_post = copy.deepcopy(self.post)
        wrong_post["ruler_state"]["value"]["character_id"] = 201
        wrong_post["succession_state"]["value"]["partition"]["value"]["title_heirs"] = [
            _row(10, 400, primary=True),
            _row(12, 400, primary=False),
        ]

        result = reconcile_succession_transition_v1(
            expectation, wrong_successor, wrong_post
        )

        self.assertEqual(result["verdict"], "unexpected_successor")
        self.assertFalse(result["successor_match"])
        self.assertFalse(result["title_distribution_match"])
        self.assertEqual(result["missing_expected_inherited_title_ids"], [11])
        self.assertEqual(
            result["unexpected_retained_predecessor_title_ids"], [12]
        )

    def test_freezes_no_heir_as_observed_risk(self) -> None:
        no_heir = _bundle(
            character_id=100,
            snapshot_id="native:20",
            revision=7,
            native_revision=20,
            date_raw=53_180_000,
            title_rows=[_row(10, None, primary=True)],
            primary_heir=None,
        )

        result = freeze_succession_expectation_v1(
            no_heir,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )

        self.assertEqual(result["expectation_state"], "no_primary_heir")
        self.assertIsNone(result["expected_successor_character_id"])

    def test_rejects_cross_frame_and_non_transition_inputs(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )
        drifted = copy.deepcopy(self.post)
        drifted["binding"]["native_revision"] += 1
        active = copy.deepcopy(self.snapshot)
        active["one_life_terminal_reason"] = None

        with self.assertRaises(ValueError):
            reconcile_succession_transition_v1(
                expectation, self.snapshot, drifted
            )
        with self.assertRaises(ValueError):
            reconcile_succession_transition_v1(expectation, active, self.post)

    def test_mismatched_reconciliation_blocks_seed_replay_fallback(self) -> None:
        plan = choose_one_life_turn(
            [
                {
                    "command": "death-terminal",
                    "ok": True,
                    "result": {
                        "terminal": True,
                        "settlement_status": "complete",
                        "score": 123,
                    },
                }
            ],
            snapshot={
                "one_life_terminal_reason": "played_character_changed",
                "episode_character_id": 100,
                "succession_reconciliation": {
                    "status": "available",
                    "verdict": "unexpected_successor",
                    "successor_match": False,
                    "title_distribution_match": True,
                },
            },
            action_steps=["start-next-episode"],
        )

        self.assertEqual(
            plan["phase"], "terminal_succession_reconciliation_red"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertFalse(plan["continue_as_heir_after_death"])

    def test_support_profile_guard_requires_xar_off_and_fresh_no_pact(self) -> None:
        ordinary = _ordinary_binding()
        self.assertEqual(
            ordinary["lifecycle"], ORDINARY_CAMPAIGN_SUCCESSION
        )
        self.assertEqual(ordinary["xar_enabled"], "xar_off")
        with self.assertRaisesRegex(ValueError, "frozen xar_off"):
            bind_succession_lifecycle_from_environment_v1(
                _manifest("xar_on"),
                lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
                ordinary_campaign_no_pact=True,
            )
        with self.assertRaisesRegex(ValueError, "fresh no-pact"):
            bind_succession_lifecycle_from_environment_v1(
                _manifest("xar_off"),
                lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
            )
        rogue = bind_succession_lifecycle_from_environment_v1(
            _manifest("xar_on"), lifecycle=ROGUE_ONE_LIFE
        )
        self.assertEqual(rogue["pact_contract"], "terminal_settlement_required")

    def test_ordinary_matched_successor_does_not_require_death_terminal(self) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot={
                "one_life_terminal_reason": "played_character_changed",
                "episode_character_id": 100,
                "succession_lifecycle": _ordinary_binding(),
                "succession_reconciliation": {
                    "status": "available",
                    "verdict": "matched",
                    "successor_match": True,
                    "title_distribution_match": True,
                },
            },
            action_steps=[
                "death-terminal",
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            ],
        )

        self.assertEqual(
            plan["selected_step"], CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
        )
        self.assertFalse(plan["settlement_required"])

    def test_rogue_and_unknown_lifecycles_remain_fail_closed(self) -> None:
        snapshot = {
            "one_life_terminal_reason": "played_character_changed",
            "episode_character_id": 100,
            "succession_reconciliation": {
                "status": "available",
                "verdict": "matched",
                "successor_match": True,
                "title_distribution_match": True,
            },
        }
        rogue = choose_one_life_turn(
            [],
            snapshot={
                **snapshot,
                "succession_lifecycle": legacy_rogue_one_life_binding_v1(),
            },
            action_steps=[
                "death-terminal",
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            ],
        )
        self.assertEqual(rogue["selected_step"], "death-terminal")

        unknown = choose_one_life_turn(
            [],
            snapshot={
                **snapshot,
                "succession_lifecycle": (
                    unknown_succession_lifecycle_binding_v1()
                ),
            },
            action_steps=[
                "death-terminal",
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            ],
        )
        self.assertEqual(
            unknown["phase"], "terminal_succession_lifecycle_unbound"
        )
        self.assertIsNone(unknown["selected_step"])

    def test_persisted_expectation_normalizer_rejects_identity_drift(self) -> None:
        expectation = freeze_succession_expectation_v1(
            self.pre,
            episode_run_id="native-100-test",
            episode_character_id=100,
        )
        self.assertEqual(
            normalize_succession_expectation_v1(expectation), expectation
        )
        drifted = copy.deepcopy(expectation)
        drifted["binding"]["episode_character_id"] = 101
        with self.assertRaises(ValueError):
            normalize_succession_expectation_v1(drifted)

    def test_native_driver_retains_restores_and_reconciles_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = _FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            endpoint.publish(_hello())
            endpoint.publish(
                _native_snapshot(20, character_id=100, date_raw=53_180_000)
            )
            before = driver.take_snapshot()
            pre_bundle = _bundle(
                character_id=100,
                snapshot_id=str(before["snapshot_id"]),
                revision=int(before["revision"]),
                native_revision=int(before["native_revision"]),
                date_raw=int(before["date_raw"]),
                title_rows=[
                    _row(10, 200, primary=True),
                    _row(11, 200, primary=False),
                    _row(12, 300, primary=False),
                ],
                primary_heir=200,
            )
            service = GameplayBridgeService(driver)
            with mock.patch.object(
                service, "query_turn_bundle_v1", return_value=pre_bundle
            ) as query, mock.patch.object(
                service,
                "capabilities",
                return_value={
                    "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP],
                    "bridge_capabilities": [],
                },
            ):
                service.plan_turn()
                prepared = driver.take_internal_semantic_snapshot()
            query.assert_called_once_with(
                expected_revision=int(before["revision"])
            )
            retained = prepared["succession_expectation"]
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["succession_expectation"], retained)
            self.assertEqual(
                persisted["succession_lifecycle"], _ordinary_binding()
            )
            driver.close()

            restored_endpoint = _FakeEndpoint(endpoint.pipe_name)
            restored = NativeHeadlessGameplayDriver(
                restored_endpoint.pipe_name,
                endpoint=restored_endpoint,
                state_dir=state_dir,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            restored_endpoint.publish(_hello())
            restored_endpoint.publish(
                _native_snapshot(21, character_id=100, date_raw=53_180_000)
            )
            restored_before = restored.take_snapshot()
            self.assertEqual(
                restored_before["succession_expectation"], retained
            )

            restored_endpoint.publish(
                _native_snapshot(24, character_id=200, date_raw=53_180_720)
            )
            transition = restored.take_snapshot()
            self.assertEqual(
                transition["one_life_terminal_reason"],
                "played_character_changed",
            )
            post_bundle = _bundle(
                character_id=200,
                snapshot_id=str(transition["snapshot_id"]),
                revision=int(transition["revision"]),
                native_revision=int(transition["native_revision"]),
                date_raw=int(transition["date_raw"]),
                title_rows=[
                    _row(10, 400, primary=True),
                    _row(11, 400, primary=False),
                ],
                primary_heir=400,
            )
            restored_service = GameplayBridgeService(restored)
            with mock.patch.object(
                restored_service,
                "query_turn_bundle_v1",
                return_value=post_bundle,
            ) as query, mock.patch.object(
                restored_service,
                "capabilities",
                return_value={
                    "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP],
                    "bridge_capabilities": [],
                },
            ):
                restored_service.plan_turn()
                reconciled_snapshot = (
                    restored.take_internal_semantic_snapshot()
                )
            query.assert_called_once_with(
                expected_revision=int(transition["revision"])
            )
            reconciliation = reconciled_snapshot["succession_reconciliation"]
            self.assertEqual(reconciliation["verdict"], "matched")
            self.assertEqual(
                restored.succession_transition_state_v1()["reconciliation"],
                reconciliation,
            )

            predecessor_run_id = transition["episode_run_id"]
            self.assertIn(
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
                restored.capabilities()["action_steps"],
            )
            plan = restored_service.plan_turn()["plan"]
            self.assertEqual(
                plan["selected_step"],
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            )
            turn = restored_service.auto_turn()
            self.assertEqual(turn["status"], "executed")
            continuation = turn["result"]
            self.assertEqual(
                continuation["lifecycle_intent"], "natural_succession"
            )
            self.assertTrue(continuation["continue_as_heir_after_death"])
            self.assertFalse(continuation["ck3_command_submitted"])
            self.assertFalse(continuation["process_restarted"])
            self.assertEqual(continuation["predecessor_character_id"], 100)
            self.assertEqual(continuation["successor_character_id"], 200)
            self.assertNotEqual(
                continuation["episode_run_id"], predecessor_run_id
            )
            continued_snapshot = restored.take_snapshot()
            self.assertFalse(continued_snapshot["one_life_terminal"])
            self.assertEqual(continued_snapshot["episode_character_id"], 200)
            self.assertEqual(
                continued_snapshot["native_command_history"][0]["command"],
                CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            )
            restored.close()

    def test_legacy_rogue_driver_state_migrates_to_rogue_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = _FakeEndpoint()
            rogue = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(_hello())
            endpoint.publish(
                _native_snapshot(20, character_id=100, date_raw=53_180_000)
            )
            rogue.take_snapshot()
            rogue.close()

            state_path = state_dir / "native-session" / "driver-state.json"
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload.pop("succession_lifecycle")
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            restored_endpoint = _FakeEndpoint(endpoint.pipe_name)
            restored = NativeHeadlessGameplayDriver(
                restored_endpoint.pipe_name,
                endpoint=restored_endpoint,
                state_dir=state_dir,
            )
            restored_endpoint.publish(_hello())
            migrated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                migrated["succession_lifecycle"],
                legacy_rogue_one_life_binding_v1(),
            )
            restored.close()

    def test_legacy_unbound_driver_state_rejects_ordinary_profile_restore(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = _FakeEndpoint()
            rogue = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(_hello())
            endpoint.publish(
                _native_snapshot(20, character_id=100, date_raw=53_180_000)
            )
            rogue.take_snapshot()
            rogue.close()

            state_path = state_dir / "native-session" / "driver-state.json"
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload.pop("succession_lifecycle")
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            ordinary_endpoint = _FakeEndpoint(endpoint.pipe_name)
            ordinary = NativeHeadlessGameplayDriver(
                ordinary_endpoint.pipe_name,
                endpoint=ordinary_endpoint,
                state_dir=state_dir,
                succession_lifecycle_binding=_ordinary_binding(),
            )
            with self.assertRaisesRegex(
                BridgeUnavailableError, "legacy driver state"
            ):
                ordinary_endpoint.publish(_hello())
            ordinary.close()


if __name__ == "__main__":
    unittest.main()
