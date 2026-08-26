from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.battle_transition_contract import (
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
    normalize_battle_transition_v1,
    parse_query_battle_transition_v1_step,
    query_battle_transition_v1_step,
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


COMBAT_ID = 335_544_325
SUBJECT = 83_886_341
NATIVE_REVISION = 5
PUBLIC_REVISION = 4
DATE_RAW = 53_178_624
STEP = f"query-battle-transition-v1-{COMBAT_ID}"


def _frame(status: str = "available") -> dict[str, object]:
    available = status == "available"
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_combat_lifecycle",
        "status": status,
        "battle_transition_ready": status in {
            "available",
            "combat_not_found",
        },
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "combat_id": COMBAT_ID,
        "province_id": 2586 if available else None,
        "phase": "done" if available else None,
        "phase_raw": 3 if available else None,
        "phase_day": 16 if available else None,
        "winner_side": "attacker" if available else None,
        "winner_raw": 0 if available else None,
        "forced_winner_side": "attacker" if available else None,
        "forced_winner_raw": 0 if available else None,
        "finalized": True if available else None,
        "battle_result_id": 553_648_135 if available else None,
        "attacker_public_cunit_ids_in_stored_order": (
            [SUBJECT] if available else []
        ),
        "defender_public_cunit_ids_in_stored_order": (
            [357, 33_554_657] if available else []
        ),
    }


def _native_result(status: str = "available") -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 51,
        "snapshot_revision": NATIVE_REVISION,
        "battle_transition_snapshot": _frame(status),
    }


def _driver_result(status: str = "available") -> dict[str, object]:
    result = {
        **_native_result(status),
        "backend_id": "battle-transition-fixture",
    }
    frame = result["battle_transition_snapshot"]
    assert isinstance(frame, dict)
    for key in (
        "combat_id",
        "province_id",
        "phase",
        "phase_raw",
        "phase_day",
        "winner_side",
        "winner_raw",
        "forced_winner_side",
        "forced_winner_raw",
        "finalized",
        "battle_result_id",
        "attacker_public_cunit_ids_in_stored_order",
        "defender_public_cunit_ids_in_stored_order",
        "battle_transition_ready",
    ):
        result[key] = copy.deepcopy(frame[key])
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
            "player_armies": [
                {
                    "army_id": SUBJECT,
                    "owner_character_id": 29_829,
                    "soldiers": 40_000,
                    "current_province_id": 2586,
                    "move_target_province_id": 2579,
                    "route_province_ids": [2579],
                    "controllable": True,
                    "in_combat": True,
                    "retreating": True,
                    "army_state": "retreating",
                    "army_state_code": 2,
                }
            ],
        },
    }


class BattleTransitionV1ContractTests(unittest.TestCase):
    def test_step_requires_one_canonical_positive_full_combat_id(self) -> None:
        self.assertEqual(query_battle_transition_v1_step(COMBAT_ID), STEP)
        self.assertEqual(
            parse_query_battle_transition_v1_step(STEP), COMBAT_ID
        )
        for malformed in (
            "query-battle-transition-v1-0",
            "query-battle-transition-v1-01",
            "query-battle-transition-v1--1",
            "query-battle-transition-v1-335544325x",
            "query-battle-transition-v1-N",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_battle_transition_v1_step(malformed)
                )
        for invalid in (True, 0, -1, 2**31):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    query_battle_transition_v1_step(invalid)

    def test_all_statuses_have_exact_readiness_and_nullability(self) -> None:
        for status in (
            "available",
            "combat_not_found",
            "state_changed",
            "unavailable",
        ):
            with self.subTest(status=status):
                normalized = normalize_battle_transition_v1(
                    _frame(status),
                    expected_combat_id=COMBAT_ID,
                    expected_observed_date_raw=DATE_RAW,
                    expected_snapshot_revision=NATIVE_REVISION,
                )
                self.assertEqual(normalized["status"], status)
                self.assertEqual(
                    normalized["battle_transition_ready"],
                    status in {"available", "combat_not_found"},
                )
                if status == "available":
                    self.assertEqual(normalized["phase"], "done")
                    self.assertEqual(normalized["winner_side"], "attacker")
                    self.assertEqual(
                        normalized[
                            "attacker_public_cunit_ids_in_stored_order"
                        ],
                        [SUBJECT],
                    )
                else:
                    self.assertIsNone(normalized["phase"])
                    self.assertEqual(
                        normalized[
                            "attacker_public_cunit_ids_in_stored_order"
                        ],
                        [],
                    )

    def test_binding_pairs_and_ordered_side_partition_are_strict(self) -> None:
        mutations = {
            "revision": lambda row: row.__setitem__(
                "snapshot_revision", NATIVE_REVISION + 1
            ),
            "date": lambda row: row.__setitem__(
                "observed_date_raw", DATE_RAW + 24
            ),
            "combat": lambda row: row.__setitem__(
                "combat_id", COMBAT_ID + 1
            ),
            "readiness": lambda row: row.__setitem__(
                "battle_transition_ready", False
            ),
            "phase_pair": lambda row: row.__setitem__("phase", "main"),
            "winner_pair": lambda row: row.__setitem__(
                "winner_side", "defender"
            ),
            "duplicate": lambda row: row.__setitem__(
                "defender_public_cunit_ids_in_stored_order", [357, 357]
            ),
            "overlap": lambda row: row.__setitem__(
                "defender_public_cunit_ids_in_stored_order", [SUBJECT]
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    normalize_battle_transition_v1(
                        frame,
                        expected_combat_id=COMBAT_ID,
                        expected_observed_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

        absent = _frame("combat_not_found")
        absent["winner_side"] = "attacker"
        with self.assertRaisesRegex(ValueError, "invented lifecycle"):
            normalize_battle_transition_v1(
                absent,
                expected_combat_id=COMBAT_ID,
                expected_observed_date_raw=DATE_RAW,
                expected_snapshot_revision=NATIVE_REVISION,
            )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_battle_transition_v1_fixture"
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
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _answer_with(
    endpoint: _FakeEndpoint,
    result_factory,
) -> None:
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


class BattleTransitionV1NativeDriverTests(unittest.TestCase):
    def test_query_works_for_a_retreating_in_combat_subject(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(capabilities["battle_transition_v1_query_supported"])
        self.assertNotIn(STEP, capabilities["action_steps"])
        self.assertNotIn(
            QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
            capabilities["action_steps"],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_BATTLE_TRANSITION_V1_CAPABILITY],
                player_armies=_semantic_snapshot()["state"]["player_armies"],
                paused=True,
            ),
            [],
        )
        _answer_with(endpoint, _native_result)
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertTrue(result["battle_transition_ready"])
        self.assertEqual(result["combat_id"], COMBAT_ID)
        self.assertEqual(result["phase"], "done")
        self.assertEqual(result["winner_side"], "attacker")
        self.assertEqual(
            result["attacker_public_cunit_ids_in_stored_order"], [SUBJECT]
        )

    def test_nonavailable_statuses_remain_typed_results(self) -> None:
        for status in (
            "combat_not_found",
            "state_changed",
            "unavailable",
        ):
            with self.subTest(status=status):
                driver, endpoint = _native_driver()
                _answer_with(
                    endpoint,
                    lambda selected=status: _native_result(selected),
                )
                result = driver.execute_step(
                    STEP,
                    expected_revision=int(driver.take_snapshot()["revision"]),
                )
                self.assertEqual(result["status"], status)
                self.assertIsNone(result["province_id"])
                self.assertEqual(
                    result["battle_transition_ready"],
                    status == "combat_not_found",
                )

    def test_malformed_frame_envelope_and_frame_drift_are_rejected(self) -> None:
        driver, endpoint = _native_driver()

        def wrong_envelope() -> dict[str, object]:
            result = _native_result()
            result["status"] = "state_changed"
            return result

        _answer_with(endpoint, wrong_envelope)
        with self.assertRaisesRegex(BridgeUnavailableError, "disagrees"):
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        driver, endpoint = _native_driver()

        def drift() -> dict[str, object]:
            result = _native_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return result

        _answer_with(endpoint, drift)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )


class _ServiceDriver:
    def __init__(
        self,
        status: str = "available",
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
    ) -> None:
        self.status = status
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "battle-transition-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_BATTLE_TRANSITION_V1_CAPABILITY]
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
            "snapshot_id": f"battle-transition-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "battle-transition-fixture",
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
            raise AssertionError("service changed the transition query binding")
        result = _driver_result(self.status)
        if self.mirror_drift:
            result["winner_side"] = "defender"
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("battle-transition observation must not advance")


class BattleTransitionV1ServiceTests(unittest.TestCase):
    def test_service_returns_all_four_typed_statuses(self) -> None:
        for status in (
            "available",
            "combat_not_found",
            "state_changed",
            "unavailable",
        ):
            with self.subTest(status=status):
                result = GameplayBridgeService(
                    _ServiceDriver(status)
                ).query_battle_transition_v1(
                    COMBAT_ID,
                    expected_revision=PUBLIC_REVISION,
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(result["scope"], "exact-combat-lifecycle")
                self.assertEqual(result["combat_id"], COMBAT_ID)
                self.assertEqual(
                    result["winner_side"],
                    result["battle_transition_snapshot"]["winner_side"],
                )
                self.assertEqual(
                    result[
                        "attacker_public_cunit_ids_in_stored_order"
                    ],
                    result["battle_transition_snapshot"][
                        "attacker_public_cunit_ids_in_stored_order"
                    ],
                )

    def test_service_requires_capability_revision_and_stable_mirrors(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=PUBLIC_REVISION - 1,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirror disagrees"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_battle_transition_v1(
                COMBAT_ID,
                expected_revision=PUBLIC_REVISION,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class BattleTransitionV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_transition_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_battle_transition_v1", names)
            result = await client.call_tool(
                "ck3_query_battle_transition_v1",
                {
                    "combat_id": COMBAT_ID,
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["combat_id"], COMBAT_ID)
        self.assertEqual(payload["phase"], "done")
        self.assertEqual(payload["winner_side"], "attacker")
        self.assertEqual(
            payload["defender_public_cunit_ids_in_stored_order"],
            [357, 33_554_657],
        )


if __name__ == "__main__":
    unittest.main()
