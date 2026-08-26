from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    normalize_battle_terminal_transition_v1,
    parse_query_battle_terminal_transition_v1_step,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.battle_transition_contract import (
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


PRIOR_COMBAT_ID = 335_544_325
SUCCESSOR_COMBAT_ID = 335_544_326
SUBJECT_CUNIT_ID = 83_886_341
OTHER_CUNIT_ID = 357
NATIVE_REVISION = 7
PUBLIC_REVISION = 6
DATE_RAW = 53_178_624
CURSOR = 40
STEP = (
    "query-battle-terminal-transition-v1-"
    f"{PRIOR_COMBAT_ID}-{SUBJECT_CUNIT_ID}-{CURSOR}"
)


def _empty_warscore(status: str = "unavailable") -> dict[str, object]:
    return {
        "status": status,
        "war_id": None,
        "war_battle_row_index": None,
        "value_raw_q100000": None,
        "winner_is_war_attacker": None,
        "combat_side0_is_war_attacker": None,
        "attacker_relative_delta_raw_q100000": None,
    }


def _normal_frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_battle_terminal_transition",
        "status": "available",
        "unavailable_reason": None,
        "battle_terminal_transition_ready": True,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "prior_combat_id": PRIOR_COMBAT_ID,
        "subject_public_cunit_id": SUBJECT_CUNIT_ID,
        "terminal_journal": {
            "requested_after_sequence": CURSOR,
            "oldest_available_sequence": 35,
            "latest_sequence": 44,
            "event_sequence": 42,
            "event_status": "observed",
        },
        "prior": {
            "combat_id": PRIOR_COMBAT_ID,
            "terminal_kind": "normal_result",
            "suppress_normal_result_envelopes": False,
            "phase_raw": 3,
            "winner_raw": 0,
            "finalized_before": False,
            "daily_guard_raw": 0,
            "province_id": 2586,
            # Result absence is deliberately compatible with normal_result.
            "battle_result_id": None,
            "wipe_raw": None,
            "attacker_primary_participant_character_id": 29_829,
            "defender_primary_participant_character_id": 36_108,
            "attacker_public_cunit_ids_in_stored_order": [SUBJECT_CUNIT_ID],
            "defender_public_cunit_ids_in_stored_order": [
                OTHER_CUNIT_ID,
                33_554_657,
            ],
            "battle_warscore": {
                "status": "recorded",
                "war_id": 16_777_290,
                "war_battle_row_index": 3,
                # Native zero remains recorded rather than becoming absent.
                "value_raw_q100000": 0,
                "winner_is_war_attacker": True,
                "combat_side0_is_war_attacker": True,
                "attacker_relative_delta_raw_q100000": 0,
            },
        },
        "removal": {
            "prior_combat_strictly_resolves": False,
            "prior_province_strictly_resolves": True,
            "prior_province_contains_prior_combat_id": False,
            "result_strictly_resolves": False,
            "result_relevant_player_count": None,
        },
        "subject": {
            "exists": True,
            "current_province_id": 2586,
            "native_carmy_id": 83_886_341,
            "combat_backlink_id": SUCCESSOR_COMBAT_ID,
            "active_combat_id": SUCCESSOR_COMBAT_ID,
            "movement_or_retreat_state_raw": 0,
            "move_target_province_id": 2579,
            "route_province_ids_in_stored_order": [2579],
            "ai_membership_status": "observed",
            "coordinator_id": 16_777_217,
            "unit_stack_stored_index": 0,
            "subunit_stored_index": 1,
            "blocked_by_active_combat": True,
        },
        "successor": {
            "state": "residual_new_combat",
            "matching_combat_ids_in_native_order": [SUCCESSOR_COMBAT_ID],
            "selected_successor_combat_id": SUCCESSOR_COMBAT_ID,
            "participant_overlap_public_cunit_ids_in_prior_order": [
                SUBJECT_CUNIT_ID,
                OTHER_CUNIT_ID,
            ],
        },
    }


def _active_frame() -> dict[str, object]:
    frame = _normal_frame()
    frame["terminal_journal"] = {
        "requested_after_sequence": CURSOR,
        "oldest_available_sequence": 35,
        "latest_sequence": 44,
        "event_sequence": None,
        "event_status": "not_observed",
    }
    frame["prior"] = {
        "combat_id": PRIOR_COMBAT_ID,
        "terminal_kind": "active_not_terminal",
        "suppress_normal_result_envelopes": None,
        "phase_raw": 1,
        "winner_raw": -1,
        "finalized_before": False,
        "daily_guard_raw": 0,
        "province_id": 2586,
        "battle_result_id": None,
        "wipe_raw": None,
        "attacker_primary_participant_character_id": 29_829,
        "defender_primary_participant_character_id": 36_108,
        "attacker_public_cunit_ids_in_stored_order": [SUBJECT_CUNIT_ID],
        "defender_public_cunit_ids_in_stored_order": [
            OTHER_CUNIT_ID,
            33_554_657,
        ],
        "battle_warscore": _empty_warscore(),
    }
    frame["removal"] = {
        "prior_combat_strictly_resolves": True,
        "prior_province_strictly_resolves": True,
        "prior_province_contains_prior_combat_id": True,
        "result_strictly_resolves": None,
        "result_relevant_player_count": None,
    }
    subject = frame["subject"]
    assert isinstance(subject, dict)
    subject["combat_backlink_id"] = PRIOR_COMBAT_ID
    subject["active_combat_id"] = PRIOR_COMBAT_ID
    frame["successor"] = {
        "state": "unavailable",
        "matching_combat_ids_in_native_order": [],
        "selected_successor_combat_id": None,
        "participant_overlap_public_cunit_ids_in_prior_order": [],
    }
    return frame


def _membership_unavailable_frame() -> dict[str, object]:
    frame = _normal_frame()
    subject = frame["subject"]
    assert isinstance(subject, dict)
    subject.update(
        {
            "combat_backlink_id": None,
            "active_combat_id": None,
            "movement_or_retreat_state_raw": 0,
            "ai_membership_status": "unavailable",
            "coordinator_id": None,
            "unit_stack_stored_index": None,
            "subunit_stored_index": None,
            "blocked_by_active_combat": False,
        }
    )
    frame["successor"] = {
        "state": "unavailable",
        "matching_combat_ids_in_native_order": [],
        "selected_successor_combat_id": None,
        "participant_overlap_public_cunit_ids_in_prior_order": [],
    }
    return frame


def _unavailable_frame(reason: str = "journal_gap") -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_battle_terminal_transition",
        "status": "unavailable",
        "unavailable_reason": reason,
        "battle_terminal_transition_ready": False,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "prior_combat_id": PRIOR_COMBAT_ID,
        "subject_public_cunit_id": SUBJECT_CUNIT_ID,
        "terminal_journal": {
            "requested_after_sequence": CURSOR,
            "oldest_available_sequence": 43,
            "latest_sequence": 50,
            "event_sequence": None,
            "event_status": "not_observed",
        },
        "prior": None,
        "removal": None,
        "subject": None,
        "successor": None,
    }


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_battle_terminal_transition_v1(
        frame,
        expected_prior_combat_id=PRIOR_COMBAT_ID,
        expected_subject_public_cunit_id=SUBJECT_CUNIT_ID,
        expected_after_terminal_sequence=CURSOR,
        expected_observed_date_raw=DATE_RAW,
        expected_snapshot_revision=NATIVE_REVISION,
    )


def _native_result(frame: dict[str, object] | None = None) -> dict[str, object]:
    selected = copy.deepcopy(frame if frame is not None else _normal_frame())
    return {
        "step": STEP,
        "accepted": True,
        "status": selected["status"],
        "query_sequence": 51,
        "snapshot_revision": NATIVE_REVISION,
        "battle_terminal_transition": selected,
    }


def _driver_result(frame: dict[str, object] | None = None) -> dict[str, object]:
    result = {**_native_result(frame), "backend_id": "terminal-fixture"}
    selected = result["battle_terminal_transition"]
    assert isinstance(selected, dict)
    for key in (
        "prior_combat_id",
        "subject_public_cunit_id",
        "terminal_journal",
        "prior",
        "removal",
        "subject",
        "successor",
        "battle_terminal_transition_ready",
        "unavailable_reason",
    ):
        result[key] = copy.deepcopy(selected[key])
    return result


def _semantic_snapshot(revision: int = NATIVE_REVISION) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.12",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class BattleTerminalTransitionV1ContractTests(unittest.TestCase):
    def test_step_wire_is_canonical_and_zero_means_no_cursor(self) -> None:
        self.assertEqual(
            query_battle_terminal_transition_v1_step(
                PRIOR_COMBAT_ID, SUBJECT_CUNIT_ID, CURSOR
            ),
            STEP,
        )
        self.assertEqual(
            query_battle_terminal_transition_v1_step(
                PRIOR_COMBAT_ID, SUBJECT_CUNIT_ID
            ),
            "query-battle-terminal-transition-v1-"
            f"{PRIOR_COMBAT_ID}-{SUBJECT_CUNIT_ID}-0",
        )
        self.assertEqual(
            parse_query_battle_terminal_transition_v1_step(STEP),
            (PRIOR_COMBAT_ID, SUBJECT_CUNIT_ID, CURSOR),
        )
        self.assertEqual(
            parse_query_battle_terminal_transition_v1_step(
                "query-battle-terminal-transition-v1-"
                f"{PRIOR_COMBAT_ID}-{SUBJECT_CUNIT_ID}-0"
            ),
            (PRIOR_COMBAT_ID, SUBJECT_CUNIT_ID, None),
        )
        for malformed in (
            "query-battle-terminal-transition-v1-0-1-0",
            "query-battle-terminal-transition-v1-1-0-0",
            "query-battle-terminal-transition-v1-01-1-0",
            "query-battle-terminal-transition-v1-1-1-00",
            "query-battle-terminal-transition-v1-1-1",
            "query-battle-terminal-transition-v1-1-1-0-extra",
            "query-battle-transition-v1-335544325",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_battle_terminal_transition_v1_step(malformed)
                )

    def test_normal_result_does_not_depend_on_result_id_and_zero_is_recorded(self) -> None:
        frame = _normalize(_normal_frame())
        self.assertEqual(frame["prior"]["terminal_kind"], "normal_result")
        self.assertIsNone(frame["prior"]["battle_result_id"])
        self.assertEqual(
            frame["prior"]["battle_warscore"]["status"], "recorded"
        )
        self.assertEqual(
            frame["prior"]["battle_warscore"]["value_raw_q100000"], 0
        )
        with_result = _normal_frame()
        with_result["prior"]["battle_result_id"] = 553_648_135
        self.assertEqual(
            _normalize(with_result)["prior"]["terminal_kind"],
            "normal_result",
        )

    def test_active_and_gap_are_distinct_typed_states(self) -> None:
        active = _normalize(_active_frame())
        self.assertEqual(active["prior"]["terminal_kind"], "active_not_terminal")
        self.assertEqual(active["prior"]["phase_raw"], 1)
        self.assertEqual(
            active["prior"]["attacker_public_cunit_ids_in_stored_order"],
            [SUBJECT_CUNIT_ID],
        )
        self.assertIsNone(
            active["prior"]["suppress_normal_result_envelopes"]
        )
        self.assertTrue(active["removal"]["prior_combat_strictly_resolves"])

        gap = _normalize(_unavailable_frame())
        self.assertEqual(gap["status"], "unavailable")
        self.assertEqual(gap["unavailable_reason"], "journal_gap")
        self.assertEqual(gap["terminal_journal"]["oldest_available_sequence"], 43)
        self.assertIsNone(gap["prior"])

    def test_subject_ai_membership_tristate_is_exact(self) -> None:
        observed = _normalize(_normal_frame())
        self.assertEqual(
            observed["subject"]["ai_membership_status"], "observed"
        )

        unavailable = _normalize(_membership_unavailable_frame())
        self.assertEqual(unavailable["status"], "available")
        self.assertEqual(
            unavailable["subject"]["ai_membership_status"], "unavailable"
        )
        self.assertEqual(unavailable["successor"]["state"], "unavailable")

        residual_without_membership = _normal_frame()
        residual_subject = residual_without_membership["subject"]
        residual_subject["ai_membership_status"] = "unavailable"
        residual_subject["coordinator_id"] = None
        residual_subject["unit_stack_stored_index"] = None
        residual_subject["subunit_stored_index"] = None
        self.assertEqual(
            _normalize(residual_without_membership)["successor"]["state"],
            "residual_new_combat",
        )

        none = _membership_unavailable_frame()
        none["subject"]["ai_membership_status"] = "none"
        none["successor"]["state"] = "no_successor"
        self.assertEqual(
            _normalize(none)["subject"]["ai_membership_status"], "none"
        )

        missing = _membership_unavailable_frame()
        missing["subject"] = {
            "exists": False,
            "current_province_id": None,
            "native_carmy_id": None,
            "combat_backlink_id": None,
            "active_combat_id": None,
            "movement_or_retreat_state_raw": None,
            "move_target_province_id": None,
            "route_province_ids_in_stored_order": None,
            "ai_membership_status": "none",
            "coordinator_id": None,
            "unit_stack_stored_index": None,
            "subunit_stored_index": None,
            "blocked_by_active_combat": None,
        }
        missing["successor"]["state"] = "subject_missing"
        self.assertFalse(_normalize(missing)["subject"]["exists"])

        invalid_frames: dict[str, dict[str, object]] = {}
        invalid_frames["missing_discriminant"] = _normal_frame()
        del invalid_frames["missing_discriminant"]["subject"][
            "ai_membership_status"
        ]
        invalid_frames["observed_incomplete"] = _normal_frame()
        invalid_frames["observed_incomplete"]["subject"]["coordinator_id"] = None
        invalid_frames["none_invented_identity"] = _normal_frame()
        invalid_frames["none_invented_identity"]["subject"][
            "ai_membership_status"
        ] = "none"
        invalid_frames["unavailable_invented_identity"] = _normal_frame()
        invalid_frames["unavailable_invented_identity"]["subject"][
            "ai_membership_status"
        ] = "unavailable"
        invalid_frames["assignment_without_observed_membership"] = (
            _membership_unavailable_frame()
        )
        invalid_frames["assignment_without_observed_membership"]["successor"][
            "state"
        ] = "subject_assignment_reopened"
        invalid_frames["no_successor_without_observed_none"] = (
            _membership_unavailable_frame()
        )
        invalid_frames["no_successor_without_observed_none"]["successor"][
            "state"
        ] = "no_successor"
        missing_unavailable = copy.deepcopy(missing)
        missing_unavailable["subject"]["ai_membership_status"] = "unavailable"
        invalid_frames["missing_subject_unavailable_membership"] = (
            missing_unavailable
        )

        for label, frame in invalid_frames.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    _normalize(frame)

    def test_suppress_cursor_warscore_and_overlap_invariants_are_strict(self) -> None:
        mutations = {
            "suppress_mapping": lambda row: row["prior"].__setitem__(
                "suppress_normal_result_envelopes", True
            ),
            "cursor_binding": lambda row: row["terminal_journal"].__setitem__(
                "requested_after_sequence", CURSOR + 1
            ),
            "event_order": lambda row: row["terminal_journal"].__setitem__(
                "event_sequence", CURSOR
            ),
            "warscore_sign": lambda row: row["prior"]["battle_warscore"].__setitem__(
                "attacker_relative_delta_raw_q100000", -1
            ),
            "selected_successor": lambda row: row["successor"].__setitem__(
                "selected_successor_combat_id", SUCCESSOR_COMBAT_ID + 1
            ),
            "overlap_order": lambda row: row["successor"].__setitem__(
                "participant_overlap_public_cunit_ids_in_prior_order",
                [OTHER_CUNIT_ID, SUBJECT_CUNIT_ID],
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _normal_frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    _normalize(frame)

        gap = _unavailable_frame()
        gap["prior"] = _normal_frame()["prior"]
        with self.assertRaisesRegex(ValueError, "invented native state"):
            _normalize(gap)


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_terminal_transition_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver() -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 4545,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": "a" * 64,
            "capabilities": [
                "game.state.snapshot",
                QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result_factory(),
            }
        )

    endpoint.send_hook = answer


class BattleTerminalTransitionV1NativeDriverTests(unittest.TestCase):
    def test_new_query_is_read_only_and_old_query_stays_advertised(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["battle_terminal_transition_v1_query_supported"]
        )
        self.assertTrue(capabilities["battle_transition_v1_query_supported"])
        self.assertNotIn(STEP, capabilities["action_steps"])
        self.assertEqual(
            _action_steps(
                [
                    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
                    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
                ],
                paused=True,
            ),
            [],
        )
        _answer_with(endpoint, _native_result)

        result = driver.execute_step(
            STEP, expected_revision=int(driver.take_snapshot()["revision"])
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["prior"]["terminal_kind"], "normal_result"
        )
        self.assertEqual(
            result["successor"]["selected_successor_combat_id"],
            SUCCESSOR_COMBAT_ID,
        )

    def test_membership_unavailable_keeps_core_query_available(self) -> None:
        driver, endpoint = _native_driver()
        _answer_with(
            endpoint,
            lambda: _native_result(_membership_unavailable_frame()),
        )

        result = driver.execute_step(
            STEP, expected_revision=int(driver.take_snapshot()["revision"])
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["subject"]["ai_membership_status"], "unavailable"
        )
        self.assertEqual(result["successor"]["state"], "unavailable")

    def test_journal_gap_is_a_typed_result_with_cursor_diagnostics(self) -> None:
        driver, endpoint = _native_driver()
        _answer_with(endpoint, lambda: _native_result(_unavailable_frame()))

        result = driver.execute_step(
            STEP, expected_revision=int(driver.take_snapshot()["revision"])
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "journal_gap")
        self.assertEqual(result["terminal_journal"]["latest_sequence"], 50)
        self.assertIsNone(result["prior"])

    def test_envelope_and_snapshot_drift_are_rejected(self) -> None:
        driver, endpoint = _native_driver()

        def wrong_status() -> dict[str, object]:
            result = _native_result()
            result["status"] = "unavailable"
            return result

        _answer_with(endpoint, wrong_status)
        with self.assertRaisesRegex(BridgeUnavailableError, "disagrees"):
            driver.execute_step(
                STEP,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def drift() -> dict[str, object]:
            result = _native_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return result

        _answer_with(endpoint, drift)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.execute_step(
                STEP,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(
        self,
        frame: dict[str, object] | None = None,
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
    ) -> None:
        self.frame = copy.deepcopy(frame if frame is not None else _normal_frame())
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "terminal-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.calls += 1
        revision = (
            PUBLIC_REVISION + 1
            if self.drift and self.calls > 1
            else PUBLIC_REVISION
        )
        return {
            "format_version": 1,
            "snapshot_id": f"terminal-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "terminal-fixture",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-29829-fixture",
            "diagnostics": {
                "hello": {
                    "game_version": "1.19.0.6",
                    "executable_sha256": "a" * 64,
                }
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed terminal query binding")
        result = _driver_result(self.frame)
        if self.mirror_drift:
            result["prior_combat_id"] = PRIOR_COMBAT_ID + 1
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("terminal observation must not advance")


class BattleTerminalTransitionV1ServiceTests(unittest.TestCase):
    def test_service_returns_available_and_gap_without_mutation(self) -> None:
        for frame in (
            _normal_frame(),
            _membership_unavailable_frame(),
            _unavailable_frame(),
        ):
            with self.subTest(
                status=frame["status"],
                successor=(frame.get("successor") or {}).get("state"),
            ):
                result = GameplayBridgeService(
                    _ServiceDriver(frame)
                ).query_battle_terminal_transition_v1(
                    PRIOR_COMBAT_ID,
                    SUBJECT_CUNIT_ID,
                    expected_revision=PUBLIC_REVISION,
                    after_terminal_sequence=CURSOR,
                )
                self.assertEqual(result["status"], frame["status"])
                self.assertEqual(
                    result["scope"],
                    "journal-backed-battle-terminal-transition",
                )
                self.assertEqual(result["terminal_journal"], frame["terminal_journal"])

    def test_service_requires_capability_revision_and_stable_mirrors(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_battle_terminal_transition_v1(
                PRIOR_COMBAT_ID,
                SUBJECT_CUNIT_ID,
                expected_revision=PUBLIC_REVISION,
                after_terminal_sequence=CURSOR,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_battle_terminal_transition_v1(
                PRIOR_COMBAT_ID,
                SUBJECT_CUNIT_ID,
                expected_revision=PUBLIC_REVISION - 1,
                after_terminal_sequence=CURSOR,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_battle_terminal_transition_v1(
                PRIOR_COMBAT_ID,
                SUBJECT_CUNIT_ID,
                expected_revision=PUBLIC_REVISION,
                after_terminal_sequence=CURSOR,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirror disagrees"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_battle_terminal_transition_v1(
                PRIOR_COMBAT_ID,
                SUBJECT_CUNIT_ID,
                expected_revision=PUBLIC_REVISION,
                after_terminal_sequence=CURSOR,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class BattleTerminalTransitionV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_terminal_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_battle_terminal_transition_v1", names)
            result = await client.call_tool(
                "ck3_query_battle_terminal_transition_v1",
                {
                    "prior_combat_id": PRIOR_COMBAT_ID,
                    "subject_public_cunit_id": SUBJECT_CUNIT_ID,
                    "expected_revision": PUBLIC_REVISION,
                    "after_terminal_sequence": CURSOR,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["prior_combat_id"], PRIOR_COMBAT_ID)
        self.assertEqual(payload["prior"]["terminal_kind"], "normal_result")
        self.assertEqual(
            payload["successor"]["selected_successor_combat_id"],
            SUCCESSOR_COMBAT_ID,
        )

    async def test_mcp_preserves_membership_unavailable_subdomain(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver(_membership_unavailable_frame()))
        async with Client(server) as client:
            result = await client.call_tool(
                "ck3_query_battle_terminal_transition_v1",
                {
                    "prior_combat_id": PRIOR_COMBAT_ID,
                    "subject_public_cunit_id": SUBJECT_CUNIT_ID,
                    "expected_revision": PUBLIC_REVISION,
                    "after_terminal_sequence": CURSOR,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(
            payload["subject"]["ai_membership_status"], "unavailable"
        )
        self.assertEqual(payload["successor"]["state"], "unavailable")


if __name__ == "__main__":
    unittest.main()
