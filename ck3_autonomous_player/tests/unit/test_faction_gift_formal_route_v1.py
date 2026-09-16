from __future__ import annotations

from pathlib import Path

import pytest

from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.faction_gift_pending_v1 import (
    begin_faction_gift_submission_v1,
    read_faction_gift_ledger_v1,
)


DATE = 53_789_952


def snapshot(*, revision: int = 10, native_revision: int = 12) -> dict[str, object]:
    return {
        "snapshot_id": f"s{revision}", "revision": revision,
        "native_revision": native_revision, "date_raw": DATE,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 32904, "alive": True},
        "episode_run_id": "native-32904-a", "active_event": None,
        "pending_character_interaction": None, "one_life_terminal_reason": None,
    }


def root_history(*, count: int) -> list[dict[str, object]]:
    return [{
        "command": "query-campaign-root-context-v1", "ok": True,
        "result": {"status": "available", "campaign_root_context": {
            "status": "available", "snapshot_revision": 12,
            "date_raw": DATE, "player_character_id": 32904,
            "player_character_alive": True,
            "government": {"key": "feudal_government"},
            "player_targeting_faction_count": count,
            "direct_landed_vassal_character_ids": [33011],
        }},
    }]


def observation() -> dict[str, object]:
    return {
        "available": True, "paused": True,
        "snapshot_revision": 12, "native_snapshot_revision": 13,
        "observed_date_raw": DATE, "player_resources_query_complete": True,
        "player_character_id": 32904, "player_gold_raw": 25_000_000,
        "player_gold_scale": 100_000,
        "source_faction_requery_complete": True,
        "queried_source_faction_id": 771, "source_faction_present": True,
        "source_faction_target_character_id": 32904,
        "source_faction_targeting_player": True, "source_faction_at_war": False,
        "source_faction_metrics_available": True,
        "source_faction_power_raw": 65_000_000,
        "source_faction_discontent_raw": 45_000_000,
        "source_faction_metric_scale": 100_000,
        "source_faction_leader_character_id": 33011,
        "source_faction_member_character_ids": [33011],
        "recipient_identity_resolved": True, "recipient_character_id": 33011,
        "recipient_alive": True, "recipient_is_ai": True,
        "recipient_is_direct_landed_vassal": True,
        "recipient_opinion_query_complete": True,
        "recipient_opinion_of_player": -40, "gift_opinion_present": False,
        "gift_opinion_modifier_value": None,
        "gift_preview": {
            "available": True, "definition_key": "gift_interaction",
            "definition_stable_hash": 9191, "interaction_legal": True,
            "auto_accept": True, "gold_cost_raw": 7_500_000,
            "gold_scale": 100_000, "opinion_delta": 25,
        },
    }


def candidate() -> dict[str, object]:
    return {
        "status": "selected", "observation": observation(),
        "choice": {
            "source_faction_id": 771, "recipient_character_id": 33011,
            "membership_role": "leader", "snapshot_revision": 12,
            "native_snapshot_revision": 13, "date_raw": DATE,
            "player_character_id": 32904, "definition_stable_hash": 9191,
            "gold_cost_raw": 7_500_000, "opinion_delta": 25,
            "minimum_gold_reserve_raw": 10_000_000,
        },
        "public_capability_advertised": False,
        "gift_submission_enabled": False,
    }


class State:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.result = result

    def wait_for_command_result(self, request_id: str, timeout: float):
        assert timeout > 0
        if self.result is None:
            return None
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True, "result": self.result}


class Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, payload: dict[str, object]) -> None:
        self.sent.append(payload)


class Driver:
    def __init__(self, state_dir: Path, current: dict[str, object]) -> None:
        import threading
        self.state_dir = state_dir
        self._session_bridge_pid = 12345
        self.private_faction_round_id = "R742"
        self._driver_state_lock = threading.RLock()
        self._last_checkpoint = None
        self.current = current
        self.endpoint = Endpoint()
        self.state = State()
        self.recorded: list[tuple[object, ...]] = []

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return dict(self.current)

    def query_faction_gift_private_candidate_v1(self, **kwargs):
        return candidate()

    def _record_command(self, step, *, ok, result=None, error=None):
        self.recorded.append((step, ok, result, error))


def pending(state: Path) -> dict[str, object]:
    return begin_faction_gift_submission_v1(
        state, request_id="gift-real-1", episode_run_id="native-32904-a",
        source_round_id="R742", source_bridge_pid=12345,
        source_bridge_creation_date="old-process", observation=observation(),
        minimum_gold_reserve_raw=10_000_000,
        checkpoint_sha256_before_submit="a" * 64,
    )["pending"]


def test_planner_preserves_known_empty_and_requires_pre_submit_checkpoint(tmp_path: Path) -> None:
    driver = Driver(tmp_path, snapshot())
    planned = {"snapshot_id": "s10", "revision": 10,
               "plan": {"selected_step": "life-advance"}}
    empty = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), root_history(count=0), {"save-checkpoint"}
    )
    assert empty["plan"]["selected_step"] == "life-advance"
    assert empty["plan"]["faction_gift_private_candidate_v1"][
        "faction_dissolved_or_gift_applied"] == "not_inferred"
    save = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), root_history(count=1), {"save-checkpoint"}
    )
    assert save["plan"]["selected_step"] == "save-checkpoint"
    driver._last_checkpoint = {
        "status": "saved", "sha256": "a" * 64, "date_raw": DATE,
        "episode_run_id": "native-32904-a",
    }
    submit = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), root_history(count=1), {"save-checkpoint"}
    )
    assert submit["plan"]["selected_step"] == route.SUBMIT_STEP


def test_planner_refreshes_missing_same_frame_root_before_private_query(
    tmp_path: Path,
) -> None:
    driver = Driver(tmp_path, snapshot())
    planned = {"snapshot_id": "s10", "revision": 10,
               "plan": {"selected_step": "life-advance"}}

    query = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), [], {"query-campaign-root-context-v1"}
    )

    assert query["plan"]["phase"] == "faction_gift_root_query"
    assert query["plan"]["selected_step"] == "query-campaign-root-context-v1"
    assert "faction_gift_private_candidate_v1" not in query["plan"]

    blocked = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), [], set()
    )
    assert blocked["plan"]["phase"] == "faction_gift_root_query_unavailable"
    assert blocked["plan"]["selected_step"] is None


def test_pending_routes_by_exact_process_identity(monkeypatch, tmp_path: Path) -> None:
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=415)
    driver = Driver(tmp_path, current)
    planned = {"snapshot_id": "s413", "revision": 413,
               "plan": {"selected_step": "life-advance"}}
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "old-process"})
    same = route.plan_faction_gift_private_v1(driver, planned, current, [], set())
    assert same["plan"]["selected_step"] == route.RECEIPT_STEP
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "new-process"})
    driver._session_bridge_pid = 23456
    driver.private_faction_round_id = "R744"
    cold = route.plan_faction_gift_private_v1(driver, planned, current, [], set())
    assert cold["plan"]["selected_step"] == route.COLD_RECOVERY_STEP
    assert cold["plan"]["faction_gift_pending_action"]["request_id"] == old["request_id"]


def test_submit_persists_identity_before_accepting_pending_ack(monkeypatch, tmp_path: Path) -> None:
    driver = Driver(tmp_path, snapshot())
    driver._last_checkpoint = {
        "status": "saved", "sha256": "a" * 64, "date_raw": DATE,
        "episode_run_id": "native-32904-a",
    }
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "old-process"})
    driver.state.result = {
        "step": route.SUBMIT_STEP, "private_build": True, "advertised": False,
        "status": "submitted_verification_pending",
        "native": {"ack": {
            "schema_version": 1, "request_id": "placeholder",
            "status": "submitted_verification_pending", "verification_pending": True,
            "source_faction_id": 771, "recipient_character_id": 33011,
        }},
    }
    # The wire request ID is intentionally generated inside the route. Mirror it
    # in the fake native ACK once the endpoint observes the request.
    original_wait = driver.state.wait_for_command_result
    def wait(request_id, timeout):
        driver.state.result["native"]["ack"]["request_id"] = request_id
        return original_wait(request_id, timeout)
    driver.state.wait_for_command_result = wait
    result = route.submit_faction_gift_private_v1(
        driver, candidate=candidate(), checkpoint=driver._last_checkpoint,
        expected_revision=10,
    )
    assert result["status"] == "submitted_verification_pending"
    stored = read_faction_gift_ledger_v1(tmp_path)["pending"]
    assert stored["request_id"] == driver.endpoint.sent[0]["request_id"]
    assert stored["status"] == "submitted_verification_pending"


def test_gameplay_service_dispatches_private_typed_submit_without_advertising(
    tmp_path: Path,
) -> None:
    driver = Driver(tmp_path, snapshot())
    called: list[dict[str, object]] = []
    driver.submit_faction_gift_private_v1 = lambda **kwargs: (
        called.append(kwargs) or {"status": "submitted_verification_pending"}
    )
    service = GameplayBridgeService(driver)
    service.plan_turn = lambda: {
        "snapshot_id": "s10", "revision": 10,
        "plan": {
            "selected_step": route.SUBMIT_STEP,
            "faction_gift_action": candidate(),
            "faction_gift_pre_submit_checkpoint": {
                "status": "saved", "sha256": "a" * 64,
            },
        },
    }
    outcome = service.auto_turn()
    assert outcome["status"] == "executed"
    assert outcome["selected_step"] == route.SUBMIT_STEP
    assert called[0]["expected_revision"] == 10


def test_cold_recovery_uses_independent_entity_facts_and_retires_applied_id(
    monkeypatch, tmp_path: Path
) -> None:
    old = pending(tmp_path)
    current = snapshot(revision=1, native_revision=2)
    driver = Driver(tmp_path, current)
    driver._session_bridge_pid = 23456
    driver.private_faction_round_id = "R744"
    driver._last_checkpoint = {
        "status": "saved", "sha256": "b" * 64, "date_raw": DATE,
        "episode_run_id": "native-32904-a",
    }
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "new-process"})
    post = {
        "available": True, "paused": True, "snapshot_revision": 2,
        "native_snapshot_revision": 3, "observed_date_raw": DATE,
        "player_resources_query_complete": True, "player_character_id": 32904,
        "player_gold_raw": 17_500_000,
        "source_faction_requery_complete": True,
        "queried_source_faction_id": 771, "source_faction_present": False,
        "source_faction_metrics_available": False,
        "recipient_identity_resolved": True, "recipient_character_id": 33011,
        "recipient_alive": True, "recipient_opinion_query_complete": True,
        "recipient_opinion_of_player": -15, "gift_opinion_present": True,
        "gift_opinion_modifier_value": 25,
    }
    driver.state.result = {
        "step": route.COLD_RECOVERY_STEP, "private_build": True,
        "advertised": False, "status": "independent_read_complete",
        "native": {"failure_flags": 0, "observation": post},
    }
    result = route.query_faction_gift_cold_recovery_private_v1(
        driver, pending=old, expected_revision=1,
    )
    assert result["cold_recovery_classification"]["status"] == "applied"
    assert read_faction_gift_ledger_v1(tmp_path)["pending"] is None


def test_cold_unknown_is_red_and_keeps_pending(monkeypatch, tmp_path: Path) -> None:
    old = pending(tmp_path)
    driver = Driver(tmp_path, snapshot(revision=1, native_revision=2))
    driver._session_bridge_pid = 23456
    driver.private_faction_round_id = "R744"
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "new-process"})
    driver.state.result = {
        "step": route.COLD_RECOVERY_STEP, "private_build": True,
        "advertised": False, "status": "independent_read_complete",
        "native": {"failure_flags": 1, "observation": {}},
    }
    with pytest.raises(route.StepPostconditionError, match="unresolved"):
        route.query_faction_gift_cold_recovery_private_v1(
            driver, pending=old, expected_revision=1,
        )
    assert read_faction_gift_ledger_v1(tmp_path)["pending"] is not None
