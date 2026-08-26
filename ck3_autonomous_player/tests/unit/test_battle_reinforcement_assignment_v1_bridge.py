from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import (
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
    normalize_battle_reinforcement_assignment_v1,
    parse_query_battle_reinforcement_assignment_v1_step,
    query_battle_reinforcement_assignment_v1_step,
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


SUBJECT = 83_886_341
SIBLING = 83_886_342
NATIVE_ARMY = 100_663_397
COORDINATOR = 117_440_519
NATIVE_REVISION = 5
PUBLIC_REVISION = 4
DATE_RAW = 53_178_264
TARGET = 2_579
STEP = f"query-battle-reinforcement-assignment-v1-{SUBJECT}"


def _frame(
    status: str = "available",
    reason: str = "subject_not_ai_managed",
) -> dict[str, object]:
    available = status == "available"
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_ai_reinforcement_assignment",
        "status": status,
        "unavailable_reason": None if available else reason,
        "battle_reinforcement_assignment_ready": available,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "selected_public_cunit_id": SUBJECT,
        "selected_native_carmy_id": NATIVE_ARMY if available else None,
        "coordinator_id": COORDINATOR if available else None,
        "unit_stack_stored_index": 2 if available else None,
        "subunit_stored_index": 0 if available else None,
        "signal": (
            {
                "asking_for_help": False,
                "assigned_to_help": True,
                "asking_changed_last_evaluation": True,
                "request_power_basis_raw": None,
                "cross_coordinator_request_valid_raw": 1,
                "cross_coordinator_request_power_raw": 2_300_000,
                "first_route_edge_remaining_duration_q100000": 150_000,
            }
            if available
            else None
        ),
        "assignment": (
            {
                "assignment_target_province_id": TARGET,
                "target_provenance": "native_help_override",
                "combat_binding_status": "unbound_until_contact",
                "active_combat_id": None,
            }
            if available
            else None
        ),
        "route": (
            {
                "current_province_id": 2_578,
                "move_target_province_id": TARGET,
                "route_province_ids": [TARGET, TARGET],
                "route_alignment": "aligned_to_assignment",
                "arrival_date_raws": [DATE_RAW + 24, DATE_RAW + 24],
                "assignment_eta_date_raw": DATE_RAW + 24,
            }
            if available
            else None
        ),
        "native_order": (
            {
                "support_search_province_ids_in_stored_order": [
                    TARGET,
                    TARGET,
                    2_580,
                ],
                "parent_subunits_in_stored_order": [
                    {
                        "public_cunit_ids_in_stored_order": [SUBJECT],
                        "asking_for_help": False,
                        "assigned_to_help": True,
                        "assignment_target_province_id": TARGET,
                    },
                    {
                        "public_cunit_ids_in_stored_order": [SIBLING],
                        "asking_for_help": True,
                        "assigned_to_help": False,
                        "assignment_target_province_id": None,
                    },
                ],
            }
            if available
            else None
        ),
        "contact_projection": (
            {
                "status": "available",
                "temporal_semantics": (
                    "present_time_only_not_future_binding"
                ),
                "current_target_compatible_combat_ids_in_stored_order": [
                    335_544_325,
                    335_544_326,
                ],
                "contact_if_now_selected_combat_id": 335_544_326,
            }
            if available
            else None
        ),
    }


def _native_result(status: str = "available") -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 61,
        "snapshot_revision": NATIVE_REVISION,
        "battle_reinforcement_assignment": _frame(status),
    }


def _driver_result(status: str = "available") -> dict[str, object]:
    frame = _frame(status)
    result = {
        **_native_result(status),
        "battle_reinforcement_assignment": frame,
        "backend_id": "battle-reinforcement-fixture",
    }
    for key in (
        "selected_public_cunit_id",
        "selected_native_carmy_id",
        "coordinator_id",
        "unit_stack_stored_index",
        "subunit_stored_index",
        "signal",
        "assignment",
        "route",
        "native_order",
        "contact_projection",
        "battle_reinforcement_assignment_ready",
        "unavailable_reason",
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
            "date": "1066.10.1",
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
                    "current_province_id": 2_578,
                    "move_target_province_id": TARGET,
                    "route_province_ids": [TARGET, TARGET],
                    "controllable": True,
                    "in_combat": False,
                    "retreating": False,
                },
                {
                    "army_id": SIBLING,
                    "owner_character_id": 29_829,
                    "soldiers": 2_000,
                    "current_province_id": 2_580,
                    "move_target_province_id": None,
                    "route_province_ids": [],
                    "controllable": False,
                    "in_combat": False,
                    "retreating": False,
                },
            ],
        },
    }


class BattleReinforcementAssignmentV1ContractTests(unittest.TestCase):
    def normalize(self, frame: object) -> dict[str, object]:
        return normalize_battle_reinforcement_assignment_v1(
            frame,
            expected_selected_public_cunit_id=SUBJECT,
            expected_observed_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

    def test_step_is_one_canonical_positive_full_cunit_id(self) -> None:
        self.assertEqual(
            query_battle_reinforcement_assignment_v1_step(SUBJECT), STEP
        )
        self.assertEqual(
            parse_query_battle_reinforcement_assignment_v1_step(STEP),
            SUBJECT,
        )
        for malformed in (
            "query-battle-reinforcement-assignment-v1-0",
            "query-battle-reinforcement-assignment-v1-01",
            "query-battle-reinforcement-assignment-v1--1",
            "query-battle-reinforcement-assignment-v1-N",
            "query-battle-reinforcement-assignment-v1-2147483648",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_battle_reinforcement_assignment_v1_step(
                        malformed
                    )
                )

    def test_available_preserves_native_order_duplicates_and_final_contact(self) -> None:
        result = self.normalize(_frame())
        self.assertEqual(result["route"]["route_province_ids"], [TARGET, TARGET])
        self.assertEqual(
            result["native_order"][
                "support_search_province_ids_in_stored_order"
            ],
            [TARGET, TARGET, 2_580],
        )
        self.assertIsNone(result["signal"]["request_power_basis_raw"])
        self.assertEqual(
            result["contact_projection"][
                "contact_if_now_selected_combat_id"
            ],
            335_544_326,
        )
        self.assertEqual(
            result["assignment"]["combat_binding_status"],
            "unbound_until_contact",
        )

    def test_active_combat_native_move_slot_may_differ_from_route_final(self) -> None:
        frame = _frame()
        frame["signal"]["assigned_to_help"] = False
        frame["assignment"] = {
            "assignment_target_province_id": None,
            "target_provenance": "none",
            "combat_binding_status": "already_in_active_combat",
            "active_combat_id": 335_544_325,
        }
        frame["route"] = {
            "current_province_id": 2_586,
            # Direct CUnit+0x30 slot; this is not ArmySnapshot's route-final
            # semantic move target.
            "move_target_province_id": 2_579,
            "route_province_ids": [2_581],
            "route_alignment": "no_assignment",
            "arrival_date_raws": [DATE_RAW + 312],
            "assignment_eta_date_raw": None,
        }
        frame["native_order"]["parent_subunits_in_stored_order"][0][
            "assigned_to_help"
        ] = False
        frame["native_order"]["parent_subunits_in_stored_order"][0][
            "assignment_target_province_id"
        ] = None
        frame["contact_projection"] = {
            "status": "not_applicable",
            "temporal_semantics": "present_time_only_not_future_binding",
            "current_target_compatible_combat_ids_in_stored_order": [],
            "contact_if_now_selected_combat_id": None,
        }

        result = self.normalize(frame)

        self.assertEqual(result["route"]["move_target_province_id"], 2_579)
        self.assertEqual(result["route"]["route_province_ids"], [2_581])
        self.assertEqual(
            result["assignment"]["combat_binding_status"],
            "already_in_active_combat",
        )

    def test_unavailable_reasons_null_all_native_groups(self) -> None:
        for reason in (
            "unsupported_build",
            "requires_paused",
            "subject_cunit_not_found",
            "subject_not_ai_managed",
            "coordinator_generation_mismatch",
            "subunit_backlink_mismatch",
            "parent_membership_mismatch",
            "route_timeline_unavailable",
            "state_changed",
        ):
            with self.subTest(reason=reason):
                result = self.normalize(_frame("unavailable", reason))
                self.assertFalse(
                    result["battle_reinforcement_assignment_ready"]
                )
                self.assertEqual(result["unavailable_reason"], reason)
                self.assertIsNone(result["route"])

    def test_stale_fields_membership_route_and_contact_are_rejected(self) -> None:
        mutations = {
            "revision": lambda row: row.__setitem__(
                "snapshot_revision", NATIVE_REVISION + 1
            ),
            "stale_request": lambda row: row["signal"].__setitem__(
                "request_power_basis_raw", 5
            ),
            "stale_cross": lambda row: (
                row["signal"].__setitem__(
                    "cross_coordinator_request_valid_raw", 0
                )
            ),
            "target_flag": lambda row: row["signal"].__setitem__(
                "assigned_to_help", False
            ),
            "route_final": lambda row: row["route"][
                "route_province_ids"
            ].__setitem__(-1, 2_580),
            "eta": lambda row: row["route"].__setitem__(
                "assignment_eta_date_raw", DATE_RAW + 48
            ),
            "selected_membership": lambda row: row["native_order"][
                "parent_subunits_in_stored_order"
            ][0].__setitem__("public_cunit_ids_in_stored_order", [SIBLING]),
            "contact_final": lambda row: row["contact_projection"].__setitem__(
                "contact_if_now_selected_combat_id", 335_544_325
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    self.normalize(frame)

        stale_cross = _frame()
        stale_cross["signal"]["cross_coordinator_request_valid_raw"] = 0
        with self.assertRaisesRegex(ValueError, "stale cross"):
            self.normalize(stale_cross)

    def test_route_alignment_variants_are_exact(self) -> None:
        not_aligned = _frame()
        not_aligned["route"]["move_target_province_id"] = 2_580
        not_aligned["route"]["route_alignment"] = "not_aligned"
        not_aligned["route"]["assignment_eta_date_raw"] = None
        self.assertEqual(
            self.normalize(not_aligned)["route"]["route_alignment"],
            "not_aligned",
        )

        no_assignment = _frame()
        no_assignment["signal"]["assigned_to_help"] = False
        no_assignment["assignment"]["assignment_target_province_id"] = None
        no_assignment["assignment"]["target_provenance"] = "none"
        no_assignment["route"]["route_alignment"] = "no_assignment"
        no_assignment["route"]["assignment_eta_date_raw"] = None
        no_assignment["native_order"]["parent_subunits_in_stored_order"][0][
            "assigned_to_help"
        ] = False
        no_assignment["native_order"]["parent_subunits_in_stored_order"][0][
            "assignment_target_province_id"
        ] = None
        no_assignment["contact_projection"] = {
            "status": "not_applicable",
            "temporal_semantics": "present_time_only_not_future_binding",
            "current_target_compatible_combat_ids_in_stored_order": [],
            "contact_if_now_selected_combat_id": None,
        }
        self.assertEqual(
            self.normalize(no_assignment)["route"]["route_alignment"],
            "no_assignment",
        )

    def test_action_literals_expand_only_on_paused_concrete_armies(self) -> None:
        armies = _semantic_snapshot()["state"]["player_armies"]
        self.assertEqual(
            _action_steps(
                [QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY],
                player_armies=armies,
                paused=True,
            ),
            [STEP, f"query-battle-reinforcement-assignment-v1-{SIBLING}"],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY],
                player_armies=armies,
                paused=False,
            ),
            [],
        )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_battle_reinforcement_v1_fixture"
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
                QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") == "execute_step":
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


class BattleReinforcementAssignmentV1NativeDriverTests(unittest.TestCase):
    def test_available_and_unavailable_are_typed_same_frame_results(self) -> None:
        for status in ("available", "unavailable"):
            with self.subTest(status=status):
                driver, endpoint = _native_driver()
                self.assertTrue(
                    driver.capabilities()[
                        "battle_reinforcement_assignment_v1_query_supported"
                    ]
                )
                self.assertIn(STEP, driver.capabilities()["action_steps"])
                _answer_with(
                    endpoint,
                    lambda selected=status: _native_result(selected),
                )
                result = driver.execute_step(
                    STEP,
                    expected_revision=int(driver.take_snapshot()["revision"]),
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(result["selected_public_cunit_id"], SUBJECT)
                self.assertEqual(
                    result["battle_reinforcement_assignment_ready"],
                    status == "available",
                )

    def test_malformed_frame_and_same_frame_drift_are_rejected(self) -> None:
        driver, endpoint = _native_driver()

        def malformed() -> dict[str, object]:
            result = _native_result()
            result["battle_reinforcement_assignment"]["route"][
                "assignment_eta_date_raw"
            ] += 24
            return result

        _answer_with(endpoint, malformed)
        with self.assertRaisesRegex(BridgeUnavailableError, "malformed frame"):
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
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
        status: str = "available",
    ) -> None:
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.status = status
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "battle-reinforcement-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP] if self.advertise else [],
            "bridge_capabilities": (
                [QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY]
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
            "snapshot_id": f"battle-reinforcement-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "battle-reinforcement-fixture",
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
            raise AssertionError("service changed reinforcement query binding")
        result = _driver_result(self.status)
        if self.mirror_drift:
            result["coordinator_id"] = COORDINATOR + 1
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("reinforcement observation must not advance")


class BattleReinforcementAssignmentV1ServiceTests(unittest.TestCase):
    def test_service_returns_canonical_frame_and_exact_mirrors(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver()
        ).query_battle_reinforcement_assignment_v1(
            SUBJECT,
            expected_revision=PUBLIC_REVISION,
        )
        self.assertEqual(
            result["scope"], "native-ai-reinforcement-assignment"
        )
        self.assertTrue(result["battle_reinforcement_assignment_ready"])
        self.assertEqual(
            result["route"],
            result["battle_reinforcement_assignment"]["route"],
        )
        self.assertEqual(
            result["native_order"],
            result["battle_reinforcement_assignment"]["native_order"],
        )

    def test_service_rejects_missing_capability_drift_and_mirror_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_battle_reinforcement_assignment_v1(
                SUBJECT, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_battle_reinforcement_assignment_v1(
                SUBJECT, expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirror disagrees"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_battle_reinforcement_assignment_v1(
                SUBJECT, expected_revision=PUBLIC_REVISION
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class BattleReinforcementAssignmentV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_tool_lists_and_calls_typed_facade(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_query_battle_reinforcement_assignment_v1",
                {tool.name for tool in listed.tools},
            )
            result = await client.call_tool(
                "ck3_query_battle_reinforcement_assignment_v1",
                {
                    "selected_public_cunit_id": SUBJECT,
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["selected_public_cunit_id"], SUBJECT)
        self.assertEqual(
            payload["contact_projection"],
            payload["battle_reinforcement_assignment"][
                "contact_projection"
            ],
        )


if __name__ == "__main__":
    unittest.main()
