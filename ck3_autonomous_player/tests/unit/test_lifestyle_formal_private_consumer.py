from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    FOCUS_QUERY_STEP,
    FOCUS_SUBMIT_STEP,
    PERK_SUBMIT_STEP,
    QUERY_STEP,
    STATE_QUERY_STEP,
    RECEIPT_STEP,
    query_player_lifestyle_private_v1,
    query_player_lifestyle_stock_focus_combined_private_v1,
    query_player_lifestyle_receipt_private_v1,
    submit_player_lifestyle_stock_focus_private_v1,
    submit_player_lifestyle_perk_private_v1,
)
from xar_autoplayer.lifestyle_formal_consumer import (
    consume_lifestyle_private_query,
    same_frame_feudal_peace_scope,
    unresolved_lifestyle_perk_action,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


def _life_snapshot() -> dict[str, object]:
    return {
        "status": "available", "snapshot_id": "native:3",
        "public_revision": 3, "native_revision": 3, "proof_epoch": 3,
        "date_raw": 53178312, "player_character_id": 29829,
        "current_focus": {"presence": "present", "key": "stewardship_domain_focus",
                          "lifestyle_key": "stewardship_lifestyle"},
        "current_lifestyle_progress": {"presence": "present",
            "lifestyle_key": "stewardship_lifestyle", "unspent_perk_points": 1},
        "owned_perk_keys": [],
        "legal_focus_candidates": {"status": "available", "items": []},
        "legal_perk_candidates": {"status": "available", "items": [
            {"key": "cutting_corners_perk", "lifestyle_key": "stewardship_lifestyle"}]},
        "readiness": {key: True for key in (
            "current_focus_ready", "lifestyle_progress_ready", "owned_perks_ready",
            "legal_focus_candidates_ready", "legal_perk_candidates_ready", "same_frame_ready")},
    }


def _game_frame(
    revision: int = 3, *, native_revision: int | None = None
) -> dict[str, object]:
    if native_revision is None:
        native_revision = revision
    return {"paused": True, "map_ready": True,
        "snapshot_id": f"native:{native_revision}", "revision": revision,
        "native_revision": native_revision, "date_raw": 53178312,
        "episode_run_id": "native-29829-ee172aa720db",
        "played_character": {"character_id": 29829, "alive": True},
        "active_wars": []}


def _scope_root() -> list[dict[str, object]]:
    return [{"command": "query-campaign-root-context-v1", "ok": True,
        "result": {"campaign_root_context": {"status": "available",
            "snapshot_revision": 3, "date_raw": 53178312,
            "player_character_id": 29829,
            "government": {"key": "feudal_government",
                           "flags": ["government_is_feudal"]}}}}]


class _State:
    def __init__(self) -> None:
        self.last: dict[str, object] | None = None
        self.fail_query = False
        self.focus_legal = True

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        assert self.last is not None and self.last["request_id"] == request_id
        req = self.last
        step = req["step"]
        assert req["expected_snapshot_id"] == f'native:{req["expected_revision"]}'
        assert req["expected_date_raw"] == 53178312
        assert req["expected_player_character_id"] == 29829
        assert req[
            "episode_run_id" if step in {QUERY_STEP, STATE_QUERY_STEP, FOCUS_QUERY_STEP}
            else "expected_episode_run_id"
        ] == "native-29829-ee172aa720db"
        if step in {PERK_SUBMIT_STEP, FOCUS_SUBMIT_STEP}:
            assert req["expected_native_revision"] == req["expected_revision"]
            assert req["expected_proof_epoch"] == req["expected_revision"]
            assert req["kind"] == ("focus" if step == FOCUS_SUBMIT_STEP else "perk")
        if step == RECEIPT_STEP:
            assert req["action_request_id"].startswith(("life-perk-", "life-focus-"))
        if step == QUERY_STEP and self.fail_query:
            return {"request_id": request_id, "ok": False,
                    "error": "native_lifestyle_state_or_final_candidates_unavailable"}
        if step == QUERY_STEP:
            result = {"step": step, "private_build": True, "advertised": False,
                "status": "available", "episode_run_id": req["episode_run_id"],
                "formal_precondition_status": "ready", "snapshot": _life_snapshot()}
        elif step == STATE_QUERY_STEP:
            life = _life_snapshot()
            life["current_focus"] = {"presence": "absent"}
            life["current_lifestyle_progress"] = {"presence": "absent"}
            life["readiness"]["legal_focus_candidates_ready"] = False
            life["readiness"]["legal_perk_candidates_ready"] = False
            result = {"step": step, "private_build": True, "advertised": False,
                "status": "available", "episode_run_id": req["episode_run_id"],
                "snapshot": life}
        elif step == FOCUS_QUERY_STEP:
            result = {"step": step, "private_build": True, "advertised": False,
                "read_only": True, "policy_scoped": True,
                "status": (
                    "observed_native_legal" if self.focus_legal
                    else "observed_native_illegal"
                ), "native_legal": self.focus_legal,
                "snapshot_id": req["expected_snapshot_id"],
                "episode_run_id": req["episode_run_id"],
                "target_key": "stewardship_wealth_focus",
                "target_lifestyle_key": "stewardship_lifestyle",
                "scanned_database_rows": 23,
                "target_lifestyle_progress": {"presence": "present",
                    "source": "exact_native_getters", "xp_total_raw": 0,
                    "xp_within_level_raw": 0, "xp_per_level": 1000,
                    "unspent_perk_points": 0, "used_perk_points": 0}}
        elif step in {PERK_SUBMIT_STEP, FOCUS_SUBMIT_STEP}:
            result = {"step": step, "private_build": True, "advertised": False,
                "status": "submitted_verification_pending", "verification_pending": True,
                "action_request_id": request_id, "target_key": req["target_key"],
                "pre_snapshot_id": req["expected_snapshot_id"],
                "episode_run_id": req["expected_episode_run_id"],
                "pre_public_revision": req["expected_revision"]}
        else:
            result = {"step": step, "private_build": True, "advertised": False,
                "status": "applied", "action_request_id": req["action_request_id"],
                "post_snapshot_id": req["expected_snapshot_id"],
                "episode_run_id": req["expected_episode_run_id"],
                "post_public_revision": req["expected_revision"],
                "post_target_perk_owned": True,
                "post_has_current_focus": True,
                "post_current_focus_key": "stewardship_wealth_focus",
                "postcondition_verified": True}
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": result}


class _Driver:
    def __init__(self) -> None:
        self.frame = _game_frame()
        self.allow_private_lifestyle_formal_trial = True
        self.command_timeout_seconds = 10.0
        self._driver_state_error = None
        self.history: list[dict[str, object]] = []
        self.state = _State()
        self.endpoint = self

    def take_snapshot(self) -> dict[str, object]:
        return {**self.frame, "native_command_history": list(self.history)}

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["life-advance", "query-campaign-root-context-v1"],
                "bridge_capabilities": []}

    def send(self, request: dict[str, object]) -> None:
        self.state.last = request
        if request["step"] in {PERK_SUBMIT_STEP, FOCUS_SUBMIT_STEP}:
            assert self.history and self.history[-1]["result"]["status"] == "action_state_unknown"

    def _record_command(self, step: str, *, ok: bool,
                        result: dict[str, object]) -> None:
        self.history.append({"command": step, "ok": ok, "result": result})

    def query_player_lifestyle_formal_private_v1(self, *, expected_revision: int):
        return query_player_lifestyle_private_v1(self, expected_revision=expected_revision)

    def submit_player_lifestyle_perk_private_v1(self, *, query, action,
                                                 expected_revision: int):
        return submit_player_lifestyle_perk_private_v1(
            self, query=query, action=action, expected_revision=expected_revision)

    def query_player_lifestyle_stock_focus_combined_private_v1(
        self, *, expected_revision: int,
    ):
        return query_player_lifestyle_stock_focus_combined_private_v1(
            self, expected_revision=expected_revision)

    def submit_player_lifestyle_stock_focus_private_v1(
        self, *, query, action, expected_revision: int,
    ):
        return submit_player_lifestyle_stock_focus_private_v1(
            self, query=query, action=action, expected_revision=expected_revision)


class LifestyleFormalPrivateConsumerTests(unittest.TestCase):
    def test_windowless_stock_focus_one_submit_and_material_receipt(self) -> None:
        driver = _Driver()
        scope = same_frame_feudal_peace_scope(driver.frame, _scope_root())
        query = query_player_lifestyle_stock_focus_combined_private_v1(
            driver, expected_revision=3)
        self.assertEqual(query["status"], "stock_focus_available")
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance"}, scope=scope, query=query)
        self.assertEqual(plan["selected_step"], FOCUS_SUBMIT_STEP)
        pending = submit_player_lifestyle_stock_focus_private_v1(
            driver, query=query, action=plan["lifestyle_action"],
            expected_revision=3)
        self.assertEqual(pending["status"], "submitted_verification_pending")
        self.assertEqual(unresolved_lifestyle_perk_action(driver.frame, driver.history), pending)
        driver.frame = _game_frame(4)
        applied = query_player_lifestyle_receipt_private_v1(
            driver, pending=pending, expected_revision=4)
        self.assertEqual(applied["status"], "applied")
        self.assertTrue(applied["post_has_current_focus"])
        self.assertEqual(applied["post_current_focus_key"], "stewardship_wealth_focus")
        self.assertIsNone(unresolved_lifestyle_perk_action(driver.frame, driver.history))

    def test_focus_submit_keeps_public_and_native_revisions_distinct(self) -> None:
        driver = _Driver()
        driver.frame = _game_frame(4, native_revision=3)
        query = query_player_lifestyle_stock_focus_combined_private_v1(
            driver, expected_revision=4)
        self.assertEqual(query["status"], "stock_focus_available")
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance"},
            scope={"status": "admitted"}, query=query)
        self.assertEqual(plan["selected_step"], FOCUS_SUBMIT_STEP)
        pending = submit_player_lifestyle_stock_focus_private_v1(
            driver, query=query, action=plan["lifestyle_action"],
            expected_revision=4)
        self.assertEqual(driver.state.last["expected_revision"], 3)
        self.assertEqual(pending["pre_public_revision"], 4)
        driver.frame = _game_frame(5, native_revision=4)
        applied = query_player_lifestyle_receipt_private_v1(
            driver, pending=pending, expected_revision=5)
        self.assertEqual(applied["post_public_revision"], 4)

    def test_stock_focus_native_illegal_never_becomes_a_submit(self) -> None:
        driver = _Driver()
        driver.state.focus_legal = False
        query = query_player_lifestyle_stock_focus_combined_private_v1(
            driver, expected_revision=3)
        self.assertEqual(query["status"], "stock_focus_readback_red")
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance"},
            scope={"status": "admitted"}, query=query)
        self.assertIsNone(plan["selected_step"])
        self.assertFalse(driver.history)

    def test_query_binds_native_frame_when_public_revision_is_ahead(self) -> None:
        driver = _Driver()
        driver.frame = _game_frame(4, native_revision=3)
        query = query_player_lifestyle_private_v1(driver, expected_revision=4)
        self.assertEqual(query["status"], "available")
        self.assertEqual(driver.state.last["expected_revision"], 3)
        self.assertEqual(driver.state.last["expected_snapshot_id"], "native:3")
        self.assertEqual(query["source_frame"]["revision"], 4)
        self.assertEqual(query["source_frame"]["native_revision"], 3)

    def test_query_rejects_stale_expected_public_revision_without_send(self) -> None:
        driver = _Driver()
        driver.frame = _game_frame(4, native_revision=3)
        query = query_player_lifestyle_private_v1(driver, expected_revision=3)
        self.assertEqual(query["status"], "paused_frame_unavailable")
        self.assertIsNone(driver.state.last)

    def test_independent_feudal_root_and_exact_slot43_select_one_typed_perk(self) -> None:
        driver = _Driver()
        scope = same_frame_feudal_peace_scope(driver.frame, _scope_root())
        self.assertEqual(scope["status"], "admitted")
        query = query_player_lifestyle_private_v1(driver, expected_revision=3)
        self.assertEqual(query["status"], "available")
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance", "phase": "peacetime"},
            scope=scope, query=query)
        self.assertEqual(plan["selected_step"], PERK_SUBMIT_STEP)
        self.assertEqual(plan["lifestyle_action"]["target_key"], "cutting_corners_perk")
        pending = submit_player_lifestyle_perk_private_v1(
            driver, query=query, action=plan["lifestyle_action"], expected_revision=3)
        self.assertEqual(pending["status"], "submitted_verification_pending")
        self.assertEqual(unresolved_lifestyle_perk_action(driver.frame, driver.history), pending)
        driver.frame = _game_frame(4)
        applied = query_player_lifestyle_receipt_private_v1(
            driver, pending=pending, expected_revision=4)
        self.assertEqual(applied["status"], "applied")
        self.assertTrue(applied["post_target_perk_owned"])
        self.assertIsNone(unresolved_lifestyle_perk_action(driver.frame, driver.history))

    def test_missing_native_window_is_red_observation_not_legal_empty(self) -> None:
        driver = _Driver()
        driver.state.fail_query = True
        query = query_player_lifestyle_private_v1(driver, expected_revision=3)
        self.assertEqual(query["status"], "native_query_unavailable")
        plan = consume_lifestyle_private_query(
            {"selected_step": "life-advance"},
            scope=same_frame_feudal_peace_scope(driver.frame, _scope_root()),
            query=query)
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["phase"], "lifestyle_native_query_unavailable")

    def test_service_uses_stock_focus_only_in_admitted_peace_scope(self) -> None:
        driver = _Driver()
        driver.state.fail_query = True
        service = GameplayBridgeService(driver)
        planned = service._plan_private_lifestyle_trial_v1(
            {"snapshot_id": "native:3", "revision": 3,
             "plan": {"selected_step": "life-advance", "phase": "peacetime"},
             "_private_lifestyle_scope_v1": same_frame_feudal_peace_scope(
                 driver.frame, _scope_root())},
            {"life-advance"},
        )
        self.assertEqual(planned["plan"]["selected_step"], FOCUS_SUBMIT_STEP)
        driver.frame["active_wars"] = [{"war_id": 1}]
        self.assertEqual(
            same_frame_feudal_peace_scope(driver.frame, _scope_root())["status"],
            "outside_scene",
        )
        last_request = driver.state.last
        war_plan = service._plan_private_lifestyle_trial_v1(
            {"snapshot_id": "native:3", "revision": 3,
             "plan": {"selected_step": "life-advance", "phase": "wartime"},
             "_private_lifestyle_scope_v1": {"status": "outside_scene"}},
            {"life-advance"},
        )
        self.assertEqual(war_plan["plan"]["selected_step"], "life-advance")
        self.assertIs(driver.state.last, last_request)

    def test_missing_public_root_query_blocks_trial_instead_of_advancing(self) -> None:
        service = GameplayBridgeService(_Driver())
        planned = service._plan_private_lifestyle_trial_v1(
            {"snapshot_id": "native:3", "revision": 3,
             "plan": {"selected_step": "life-advance", "phase": "peacetime"},
             "_private_lifestyle_scope_v1": {"status": "root_query_needed"}},
            {"life-advance"},
        )
        self.assertIsNone(planned["plan"]["selected_step"])
        self.assertEqual(
            planned["plan"]["required_step"], "query-campaign-root-context-v1")

    def test_service_routes_only_controlled_perk_then_independent_receipt(self) -> None:
        driver = _Driver()
        service = GameplayBridgeService(driver)
        planned = service._plan_private_lifestyle_trial_v1(
            {"snapshot_id": "native:3", "revision": 3,
             "plan": {"selected_step": "life-advance", "phase": "peacetime"},
             "_private_lifestyle_scope_v1": same_frame_feudal_peace_scope(
                 driver.frame, _scope_root())},
            {"life-advance"},
        )
        self.assertEqual(planned["plan"]["selected_step"], PERK_SUBMIT_STEP)
        submitted = driver.submit_player_lifestyle_perk_private_v1(
            query=planned["plan"]["lifestyle_query"],
            action=planned["plan"]["lifestyle_action"], expected_revision=3)
        driver.frame = _game_frame(4)
        receipt_plan = service._plan_private_lifestyle_trial_v1(
            {"snapshot_id": "native:4", "revision": 4,
             "plan": {"selected_step": "life-advance", "phase": "peacetime"},
             "_private_lifestyle_pending_v1": submitted},
            {"life-advance"},
        )
        self.assertEqual(receipt_plan["plan"]["selected_step"], RECEIPT_STEP)
        self.assertEqual(receipt_plan["plan"]["lifestyle_pending_action"], submitted)
        applied = query_player_lifestyle_receipt_private_v1(
            driver, pending=submitted, expected_revision=4)
        self.assertTrue(applied["postcondition_verified"])
        driver.history.extend(_scope_root())
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value={"selected_step": "life-advance", "phase": "peacetime"},
        ):
            following = service.plan_turn()
        self.assertEqual(
            following["plan"]["lifestyle_receipt_consumed"]["action_request_id"],
            submitted["action_request_id"],
        )
        self.assertNotIn(PERK_SUBMIT_STEP, driver.capabilities()["action_steps"])


if __name__ == "__main__":
    unittest.main()
