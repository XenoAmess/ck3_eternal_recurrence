from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.active_combat_retreat_contract import (
    normalize_active_combat_retreat_v1_order_ack,
    normalize_active_combat_retreat_v1_preview,
    order_active_combat_retreat_v1_step,
    parse_order_active_combat_retreat_v1_step,
    parse_preview_active_combat_retreat_v1_step,
    preview_active_combat_retreat_v1_step,
)
from xar_autoplayer.bridge.battle_control_contract import (
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_order_active_combat_retreat_v1,
    _ck3_preview_active_combat_retreat_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import (
    ARMY_ROUTES_CAPABILITY,
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
)


SELECTED = 101
SECOND_SELECTED_OWNER = 102
SAME_SIDE_ALLY = 103
DEFENDER = 201
PLAYER = 29_829
ALLY_OWNER = 40_001
ENEMY_OWNER = 36_108
COMBAT_ID = 335_544_325
COMBAT_PROVINCE = 2586
TARGET_PROVINCE = 2700
MID_PROVINCE = 2630
DATE_RAW = 53_178_264
NATIVE_REVISION = 5


def _army_identity(
    public_id: int,
    native_id: int,
    owner_id: int,
) -> dict[str, int]:
    return {
        "native_carmy_id": native_id,
        "public_cunit_id": public_id,
        "owner_character_id": owner_id,
        "combat_backlink_id": COMBAT_ID,
    }


def _side(
    side_index: int,
    role: str,
    armies: list[dict[str, int]],
    primary: int,
) -> dict[str, object]:
    return {
        "side_index": side_index,
        "role": role,
        "primary_participant_character_id": primary,
        "selected_commander_character_id": None,
        "current_roll_points": 0,
        "ordered_armies": armies,
        "levy_entries": [],
        "men_at_arms_entries": [],
        "stored_current_fighting_raw": 0,
        "stored_levy_current_fighting_raw": 0,
        "stored_current_matches_derived": True,
        "stored_levy_current_matches_derived": True,
        "derived_current_fighting_raw": 0,
        "derived_soft_casualties_raw": 0,
        "derived_main_fighting_entry_hard_casualties_raw": 0,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [],
        "participant_hard_total_raw": 0,
        "side_strength_raw": 0,
        "side_strength_scale": 100_000,
    }


def _battle_frame(
    *,
    scope: str = "full_side",
    legal_now: bool = True,
) -> dict[str, object]:
    if scope == "full_side":
        attacker_armies = [
            _army_identity(SELECTED, 301, PLAYER),
            _army_identity(SECOND_SELECTED_OWNER, 302, PLAYER),
        ]
        affected = [SELECTED, SECOND_SELECTED_OWNER]
        unaffected: list[int] = []
    else:
        attacker_armies = [
            _army_identity(SELECTED, 301, PLAYER),
            _army_identity(SAME_SIDE_ALLY, 303, ALLY_OWNER),
            _army_identity(SECOND_SELECTED_OWNER, 302, PLAYER),
        ]
        affected = [SELECTED, SECOND_SELECTED_OWNER]
        unaffected = [SAME_SIDE_ALLY]
    allow_early = legal_now
    reason_codes = [] if legal_now else ["too_early"]
    reason_keys = [] if legal_now else ["COMBAT_NO_RETREAT_TOO_EARLY"]
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_ongoing_combat",
        "status": "available",
        "battle_control_ready": True,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "subject_public_cunit_id": SELECTED,
        "subject_native_carmy_id": 301,
        "combat_id": COMBAT_ID,
        "province_id": COMBAT_PROVINCE,
        "selected_public_cunit_id": SELECTED,
        "selected_native_carmy_id": 301,
        "selected_owner_character_id": PLAYER,
        "combat_province_id": COMBAT_PROVINCE,
        "side_index": 0,
        "side_scope": scope,
        "affected_public_cunit_ids_in_stored_order": affected,
        "unaffected_same_side_public_cunit_ids_in_stored_order": unaffected,
        "side_flags": {
            "disallow_retreat": False,
            "allow_early_retreat": allow_early,
            "skip_pursuit": False,
        },
        "legality": {
            "status": "available",
            "native_boolean": legal_now,
            "phase_raw": 1,
            "phase": "main",
            "retreat_elapsed_baseline_date_raw": DATE_RAW,
            "elapsed_whole_days": 0,
            "minimum_elapsed_whole_days_exclusive": 14,
            "landless_gate_allows_retreat": True,
            "legal_now": legal_now,
            "reason_codes_in_native_order": reason_codes,
            "native_reason_keys_in_native_order": reason_keys,
            "earliest_day_gate_date_raw": DATE_RAW + 15 * 24,
        },
        "phase": "main",
        "phase_raw": 1,
        "phase_day": 4,
        "winner_side": "none",
        "winner_raw": -1,
        "forced_winner_side": "none",
        "forced_winner_raw": -1,
        "finalized": False,
        "battle_result_id": None,
        "base_combat_width": 6200,
        "final_combat_width": 5800,
        "roll_cadence_counter": 2,
        "base_advantage_raw": 0,
        "resolved_advantage_raw": 0,
        "attacker": _side(0, "attacker", attacker_armies, PLAYER),
        "defender": _side(
            1,
            "defender",
            [_army_identity(DEFENDER, 401, ENEMY_OWNER)],
            ENEMY_OWNER,
        ),
    }


def _semantic_army(
    army_id: int,
    *,
    retreating: bool = False,
    target_province_id: int | None = None,
) -> dict[str, object]:
    return {
        "army_id": army_id,
        "owner_character_id": PLAYER,
        "soldiers": 1_000,
        "current_province_id": COMBAT_PROVINCE,
        "move_target_province_id": target_province_id,
        "route_province_ids": (
            [target_province_id] if target_province_id is not None else []
        ),
        "controllable": True,
        "in_combat": not retreating,
        "retreating": retreating,
        "army_state": "retreating" if retreating else "combat",
        "army_state_code": 6 if retreating else 2,
    }


def _semantic_snapshot(
    native_revision: int = NATIVE_REVISION,
    *,
    retreating: bool = False,
) -> dict[str, object]:
    player_armies = [
        _semantic_army(
            SELECTED,
            retreating=retreating,
            target_province_id=(TARGET_PROVINCE if retreating else None),
        ),
        _semantic_army(
            SECOND_SELECTED_OWNER,
            retreating=retreating,
            target_province_id=(TARGET_PROVINCE if retreating else None),
        ),
    ]
    enemy_army = {
        "army_id": DEFENDER,
        "owner_character_id": ENEMY_OWNER,
        "soldiers": 800,
        "current_province_id": TARGET_PROVINCE,
        "move_target_province_id": None,
        "route_province_ids": [],
        "controllable": False,
        "in_combat": not retreating,
        "retreating": False,
        "army_state": "combat" if not retreating else "regular",
        "army_state_code": 2 if not retreating else 1,
    }
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{native_revision}",
        "revision": native_revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.27",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": PLAYER, "alive": True},
            "one_life_settlement": None,
            "active_wars": [
                {
                    "war_id": 88,
                    "player_side": "attacker",
                    "primary_opponent_character_id": ENEMY_OWNER,
                    "player_is_primary_war_leader": True,
                    "player_relative_war_score": 0,
                    "allied_armies": copy.deepcopy(player_armies),
                    "enemy_armies": [enemy_army],
                    "war_objective_province_ids": [],
                    "objective_province_states": [],
                    "targeted_title_ids": [],
                }
            ],
            "player_armies": player_armies,
        },
    }


class _FakeEndpoint:
    def __init__(
        self,
        *,
        battle_frames: list[dict[str, object]],
        routes: list[list[int]] | None = None,
        publish_post_move: bool = False,
    ) -> None:
        self.pipe_name = r"\\.\pipe\xar_active_retreat_v1_fixture"
        self.battle_frames = [copy.deepcopy(row) for row in battle_frames]
        self.routes = [list(route) for route in (routes or [[TARGET_PROVINCE]])]
        self.publish_post_move = publish_post_move
        self.on_frame = None
        self.on_disconnect = None
        self.sent_steps: list[str] = []
        self.battle_query_count = 0
        self.route_preview_count = 0
        self.move_count = 0

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        step = str(frame["step"])
        self.sent_steps.append(step)
        if step.startswith("query-battle-control-snapshot-v1-"):
            index = min(self.battle_query_count, len(self.battle_frames) - 1)
            battle = copy.deepcopy(self.battle_frames[index])
            self.battle_query_count += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "available",
                "query_sequence": self.battle_query_count,
                "snapshot_revision": battle["snapshot_revision"],
                "battle_control_snapshot": battle,
            }
        elif step.startswith("preview-move-army-"):
            index = min(self.route_preview_count, len(self.routes) - 1)
            route = list(self.routes[index])
            self.route_preview_count += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "available",
                "route_preview": {
                    "status": "available",
                    "army_id": SELECTED,
                    "origin_province_id": COMBAT_PROVINCE,
                    "target_province_id": TARGET_PROVINCE,
                    "route_province_ids": route,
                },
            }
        elif step.startswith("move-army-"):
            self.move_count += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "submitted",
            }
        else:
            raise AssertionError(f"unexpected native step {step}")
        self.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result,
            }
        )
        if step.startswith("move-army-") and self.publish_post_move:
            self.publish(
                _semantic_snapshot(
                    NATIVE_REVISION + 1,
                    retreating=True,
                )
            )

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _driver(
    *,
    frame: dict[str, object] | None = None,
    battle_frames: list[dict[str, object]] | None = None,
    routes: list[list[int]] | None = None,
    publish_post_move: bool = False,
    capabilities: list[str] | None = None,
) -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    selected_frames = battle_frames or [frame or _battle_frame()]
    endpoint = _FakeEndpoint(
        battle_frames=selected_frames,
        routes=routes,
        publish_post_move=publish_post_move,
    )
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.05,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 7001,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": "a" * 64,
            "capabilities": capabilities
            or [
                    "game.state.snapshot",
                    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
                    PREVIEW_MOVE_ARMY_CAPABILITY,
                    MOVE_ARMY_CAPABILITY,
                    ARMY_ROUTES_CAPABILITY,
                ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _preview(
    driver: NativeHeadlessGameplayDriver,
    target: int = TARGET_PROVINCE,
) -> tuple[GameplayBridgeService, dict[str, object]]:
    service = GameplayBridgeService(driver)
    revision = int(service.snapshot()["revision"])
    result = service.preview_active_combat_retreat_v1(
        SELECTED,
        target,
        expected_revision=revision,
    )
    return service, result


def _order_arguments(preview: dict[str, object]) -> dict[str, object]:
    target_preview = preview["target_preview"]
    assert isinstance(target_preview, dict)
    return {
        "selected_public_cunit_id": SELECTED,
        "expected_revision": preview["source_binding"]["revision"],
        "expected_combat_id": preview["combat_id"],
        "expected_side_index": preview["side_index"],
        "expected_scope": preview["side_scope"],
        "target_province_id": preview["target_province_id"],
        "candidate_token": target_preview["candidate_token"],
    }


class ActiveCombatRetreatV1ContractTests(unittest.TestCase):
    def test_builders_parse_only_canonical_complete_literals(self) -> None:
        preview = preview_active_combat_retreat_v1_step(
            SELECTED, TARGET_PROVINCE
        )
        self.assertEqual(
            parse_preview_active_combat_retreat_v1_step(preview),
            (SELECTED, TARGET_PROVINCE),
        )
        token = "A" * 32
        order = order_active_combat_retreat_v1_step(
            SELECTED,
            expected_snapshot_revision=7,
            expected_combat_id=COMBAT_ID,
            expected_side_index=0,
            expected_scope="full_side",
            target_province_id=TARGET_PROVINCE,
            candidate_token=token,
        )
        self.assertEqual(
            parse_order_active_combat_retreat_v1_step(order),
            {
                "selected_public_cunit_id": SELECTED,
                "expected_snapshot_revision": 7,
                "expected_combat_id": COMBAT_ID,
                "expected_side_index": 0,
                "expected_scope": "full_side",
                "target_province_id": TARGET_PROVINCE,
                "candidate_token": token,
            },
        )
        for malformed in (
            preview.replace(f"-{SELECTED}-", f"-0{SELECTED}-"),
            order.replace("-side-0-", "-side-2-"),
            order.replace(token, "short"),
            f"{order}!suffix",
        ):
            self.assertIsNone(
                parse_order_active_combat_retreat_v1_step(malformed)
                if malformed.startswith("order-")
                else parse_preview_active_combat_retreat_v1_step(malformed)
            )

    def test_strict_normalizers_reject_completion_or_binding_forgery(self) -> None:
        driver, _endpoint = _driver()
        _service, preview = _preview(driver)
        normalized = normalize_active_combat_retreat_v1_preview(
            preview,
            expected_selected_public_cunit_id=SELECTED,
            expected_target_province_id=TARGET_PROVINCE,
            expected_snapshot_revision=preview["source_binding"]["revision"],
        )
        forged = copy.deepcopy(normalized)
        forged["target_preview"]["route_province_ids"] = [MID_PROVINCE]
        with self.assertRaisesRegex(ValueError, "available target preview"):
            normalize_active_combat_retreat_v1_preview(
                forged,
                expected_selected_public_cunit_id=SELECTED,
                expected_target_province_id=TARGET_PROVINCE,
                expected_snapshot_revision=preview["source_binding"][
                    "revision"
                ],
            )


class ActiveCombatRetreatV1DriverTests(unittest.TestCase):
    def test_capability_exposes_preview_then_exactly_one_fresh_order(self) -> None:
        driver, _endpoint = _driver()
        preview_step = preview_active_combat_retreat_v1_step(
            SELECTED, TARGET_PROVINCE
        )
        before = driver.capabilities()
        self.assertTrue(
            before["active_combat_retreat_v1_composition_supported"]
        )
        self.assertIn(preview_step, before["action_steps"])
        self.assertFalse(before["active_combat_retreat_v1_token_ready"])

        _service, preview = _preview(driver)
        order_step = preview["target_preview"]["order_step"]
        after = driver.capabilities()
        orders = [
            step
            for step in after["action_steps"]
            if step.startswith("order-active-combat-retreat-v1-")
        ]
        self.assertEqual(orders, [order_step])
        self.assertTrue(after["active_combat_retreat_v1_token_ready"])

    def test_capability_requires_all_three_underlying_native_primitives(self) -> None:
        driver, _endpoint = _driver(
            capabilities=[
                "game.state.snapshot",
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
                PREVIEW_MOVE_ARMY_CAPABILITY,
                ARMY_ROUTES_CAPABILITY,
            ]
        )
        capabilities = driver.capabilities()
        self.assertFalse(
            capabilities["active_combat_retreat_v1_composition_supported"]
        )
        self.assertNotIn(
            preview_active_combat_retreat_v1_step(
                SELECTED, TARGET_PROVINCE
            ),
            capabilities["action_steps"],
        )

    def test_too_early_and_same_origin_never_call_route_preview(self) -> None:
        driver, endpoint = _driver(frame=_battle_frame(legal_now=False))
        _service, result = _preview(driver)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "retreat_not_legal:too_early")
        self.assertFalse(result["action_ready"])
        self.assertEqual(endpoint.route_preview_count, 0)
        self.assertFalse(driver.capabilities()["active_combat_retreat_v1_token_ready"])

        driver, endpoint = _driver()
        _service, result = _preview(driver, COMBAT_PROVINCE)
        self.assertEqual(
            result["unavailable_reason"],
            "target_does_not_leave_combat_province",
        )
        self.assertEqual(endpoint.route_preview_count, 0)

    def test_wrong_token_and_scope_are_consumed_without_movement(self) -> None:
        driver, endpoint = _driver()
        _service, preview = _preview(driver)
        args = _order_arguments(preview)
        wrong_token_step = order_active_combat_retreat_v1_step(
            SELECTED,
            expected_snapshot_revision=int(args["expected_revision"]),
            expected_combat_id=COMBAT_ID,
            expected_side_index=0,
            expected_scope="full_side",
            target_province_id=TARGET_PROVINCE,
            candidate_token="Z" * 32,
        )
        rejected = driver.execute_step(
            wrong_token_step,
            expected_revision=int(args["expected_revision"]),
        )
        self.assertEqual(rejected["rejection_reason"], "stale_or_unknown_token")
        self.assertEqual(endpoint.move_count, 0)
        self.assertFalse(driver.capabilities()["active_combat_retreat_v1_token_ready"])

        driver, endpoint = _driver()
        _service, preview = _preview(driver)
        args = _order_arguments(preview)
        wrong_scope_step = order_active_combat_retreat_v1_step(
            SELECTED,
            expected_snapshot_revision=int(args["expected_revision"]),
            expected_combat_id=COMBAT_ID,
            expected_side_index=0,
            expected_scope="owner_subset",
            target_province_id=TARGET_PROVINCE,
            candidate_token=str(args["candidate_token"]),
        )
        rejected = driver.execute_step(
            wrong_scope_step,
            expected_revision=int(args["expected_revision"]),
        )
        self.assertEqual(rejected["rejection_reason"], "scope_changed")
        self.assertEqual(endpoint.move_count, 0)

    def test_revision_and_route_changes_reject_before_player_move(self) -> None:
        driver, endpoint = _driver()
        _service, preview = _preview(driver)
        args = _order_arguments(preview)
        endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
        rejected = driver.execute_step(
            str(preview["target_preview"]["order_step"]),
            expected_revision=int(args["expected_revision"]),
        )
        self.assertEqual(rejected["rejection_reason"], "revision_changed")
        self.assertEqual(endpoint.move_count, 0)

        driver, endpoint = _driver(
            routes=[[TARGET_PROVINCE], [MID_PROVINCE, TARGET_PROVINCE]]
        )
        _service, preview = _preview(driver)
        args = _order_arguments(preview)
        rejected = driver.execute_step(
            str(preview["target_preview"]["order_step"]),
            expected_revision=int(args["expected_revision"]),
        )
        self.assertEqual(rejected["rejection_reason"], "route_changed")
        self.assertEqual(endpoint.move_count, 0)

    def test_full_side_ack_is_partial_semantic_evidence_not_completion(self) -> None:
        driver, endpoint = _driver(publish_post_move=True)
        service, preview = _preview(driver)
        args = _order_arguments(preview)
        ack = _ck3_order_active_combat_retreat_v1(service, **args)

        self.assertTrue(ack["accepted"])
        self.assertTrue(ack["verification_pending"])
        self.assertEqual(endpoint.move_count, 1)
        self.assertEqual(
            ack["affected_public_cunit_ids_in_stored_order"],
            [SELECTED, SECOND_SELECTED_OWNER],
        )
        post = ack["semantic_postcondition"]
        self.assertEqual(post["status"], "observed_partial")
        self.assertTrue(post["all_affected_retreating_observed"])
        self.assertTrue(post["all_affected_target_observed"])
        self.assertTrue(post["all_affected_route_observed"])
        self.assertFalse(post["combat_id_post_query_performed"])
        self.assertFalse(post["winner_verified"])
        self.assertFalse(post["phase_verified"])
        self.assertFalse(post["full_postcondition_verified"])

        second = service.order_active_combat_retreat_v1(**args)
        self.assertFalse(second["accepted"])
        self.assertEqual(second["rejection_reason"], "stale_or_unknown_token")
        self.assertEqual(endpoint.move_count, 1)

    def test_owner_subset_preserves_stored_affected_and_unaffected_order(self) -> None:
        frame = _battle_frame(scope="owner_subset")
        driver, endpoint = _driver(
            frame=frame,
            publish_post_move=True,
        )
        service = GameplayBridgeService(driver)
        revision = int(service.snapshot()["revision"])
        preview = _ck3_preview_active_combat_retreat_v1(
            service,
            SELECTED,
            TARGET_PROVINCE,
            revision,
        )
        self.assertEqual(preview["side_scope"], "owner_subset")
        self.assertEqual(
            preview["affected_public_cunit_ids_in_stored_order"],
            [SELECTED, SECOND_SELECTED_OWNER],
        )
        self.assertEqual(
            preview[
                "unaffected_same_side_public_cunit_ids_in_stored_order"
            ],
            [SAME_SIDE_ALLY],
        )
        ack = service.order_active_combat_retreat_v1(
            **_order_arguments(preview)
        )
        self.assertTrue(ack["accepted"])
        self.assertEqual(
            [
                row["public_cunit_id"]
                for row in ack["semantic_postcondition"][
                    "affected_armies_in_stored_order"
                ]
            ],
            [SELECTED, SECOND_SELECTED_OWNER],
        )
        self.assertEqual(
            ack[
                "unaffected_same_side_public_cunit_ids_in_stored_order"
            ],
            [SAME_SIDE_ALLY],
        )
        self.assertEqual(endpoint.move_count, 1)

    def test_order_ack_normalizer_forbids_full_verification_claim(self) -> None:
        driver, _endpoint = _driver(publish_post_move=True)
        service, preview = _preview(driver)
        args = _order_arguments(preview)
        ack = service.order_active_combat_retreat_v1(**args)
        forged = copy.deepcopy(ack)
        forged["semantic_postcondition"]["full_postcondition_verified"] = True
        with self.assertRaisesRegex(ValueError, "explicitly false"):
            normalize_active_combat_retreat_v1_order_ack(
                forged,
                expected_selected_public_cunit_id=SELECTED,
                expected_snapshot_revision=int(args["expected_revision"]),
                expected_combat_id=COMBAT_ID,
                expected_side_index=0,
                expected_scope="full_side",
                expected_target_province_id=TARGET_PROVINCE,
                expected_candidate_token=str(args["candidate_token"]),
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ActiveCombatRetreatV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_typed_preview_and_order_tools(self) -> None:
        from mcp import Client

        driver, endpoint = _driver(publish_post_move=True)
        revision = int(driver.take_snapshot()["revision"])
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_preview_active_combat_retreat_v1", names)
            self.assertIn("ck3_order_active_combat_retreat_v1", names)
            preview_result = await client.call_tool(
                "ck3_preview_active_combat_retreat_v1",
                {
                    "selected_public_cunit_id": SELECTED,
                    "target_province_id": TARGET_PROVINCE,
                    "expected_revision": revision,
                },
            )
            self.assertFalse(preview_result.is_error)
            preview = preview_result.structured_content
            order_result = await client.call_tool(
                "ck3_order_active_combat_retreat_v1",
                _order_arguments(preview),
            )

        self.assertFalse(order_result.is_error)
        self.assertTrue(order_result.structured_content["verification_pending"])
        self.assertEqual(endpoint.move_count, 1)


if __name__ == "__main__":
    unittest.main()
