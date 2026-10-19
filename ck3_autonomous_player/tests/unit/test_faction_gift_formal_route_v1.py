"""Synthetic faction frames and ACKs; no CK3 execution or live qualification."""
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
        # Checkpoint/submit tests model an observed peaceful turn. An omitted
        # war vector is unknown and must not obtain the same spending permit.
        "active_wars": [],
        "episode_run_id": "native-32904-a", "active_event": None,
        "pending_character_interaction": None, "one_life_terminal_reason": None,
        "diagnostics": {"bridge_pid": 12345, "connection_generation": 2},
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


def stock_danger_alert() -> dict[str, object]:
    """Synthetic same-frame final Native danger for the positive spend case."""
    return {
        "command": "query-player-faction-alerts-v1", "ok": True,
        "result": {"player_faction_alerts": {
            "status": "available", "snapshot_revision": 12, "date_raw": DATE,
            "player_character_id": 32904,
            "readiness": {"targeting_rows_ready": True,
                          "stock_dangerous_predicate_ready": True,
                          "same_frame_ready": True},
            "targeting_factions": [{
                "faction_id": 771, "target_character_id": 32904,
                "leader_character_id": 33011, "character_member_ids": [33011],
                "dangerous_by_stock_rule": True, "faction_at_war": False,
            }],
        }},
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
        source_bridge_creation_date="20261019131054.525692+480", observation=observation(),
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
        driver, planned, snapshot(), root_history(count=1) + [stock_danger_alert()],
        {"save-checkpoint"}
    )
    assert save["plan"]["selected_step"] == "save-checkpoint"
    driver._last_checkpoint = {
        "status": "saved", "sha256": "a" * 64, "date_raw": DATE,
        "episode_run_id": "native-32904-a",
    }
    submit = route.plan_faction_gift_private_v1(
        driver, planned, snapshot(), root_history(count=1) + [stock_danger_alert()],
        {"save-checkpoint"}
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
                        lambda pid: {"creation_date": "20261019131054.525692+480"})
    same = route.plan_faction_gift_private_v1(driver, planned, current, [], set())
    assert same["plan"]["selected_step"] == route.RECEIPT_STEP
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "20261019051054.525693+000"})
    driver._session_bridge_pid = 23456
    driver.private_faction_round_id = "R744"
    cold = route.plan_faction_gift_private_v1(driver, planned, current, [], set())
    assert cold["plan"]["selected_step"] == route.COLD_RECOVERY_STEP
    assert cold["plan"]["faction_gift_pending_action"]["request_id"] == old["request_id"]


def test_pending_same_public_revision_does_not_advance_date(
    monkeypatch, tmp_path: Path,
) -> None:
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"])
    fresh = snapshot(revision=414, native_revision=old["pre_native_snapshot_revision"] + 1)
    driver = Driver(tmp_path, current)
    planned = {"snapshot_id": "s413", "revision": 413,
               "plan": {"selected_step": "life-advance"}}
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "20261019131054.525692+480"})
    calls: list[tuple[int, float]] = []

    def native_wait(start, predicate, *, timeout_seconds):
        calls.append((start["revision"], timeout_seconds))
        if not predicate(fresh):
            pytest.fail("bounded native wait did not recognize the new paused frame")
        return fresh

    driver._wait_for_snapshot = native_wait

    with pytest.raises(route.PreSubmissionRevisionMismatchError):
        route.plan_faction_gift_private_v1(
            driver, planned, current, [], set(),
        )
    if calls != [(413, 5.0)]:
        pytest.fail("pending gift did not use one existing bounded native wait")
    if read_faction_gift_ledger_v1(tmp_path)["pending"] != old:
        pytest.fail("pending gift ledger changed before material verification")

    # The runner's established revision-mismatch retry replans from fresh.
    receipt = route.plan_faction_gift_private_v1(
        driver, {"snapshot_id": "s414", "revision": 414,
                 "plan": {"selected_step": "life-advance"}},
        fresh, [], set(),
    )
    if receipt["plan"].get("selected_step") != route.RECEIPT_STEP:
        pytest.fail("new same-date paused frame did not reach native receipt")


def test_pending_same_revision_timeout_is_red_and_keeps_ledger(
    monkeypatch, tmp_path: Path,
) -> None:
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"])
    driver = Driver(tmp_path, current)
    driver._wait_for_snapshot = lambda start, predicate, *, timeout_seconds: start
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "20261019131054.525692+480"})

    with pytest.raises(route.BridgeUnavailableError,
                       match="same-date paused revision did not arrive"):
        route.plan_faction_gift_private_v1(
            driver, {"snapshot_id": "s413", "revision": 413,
                     "plan": {"selected_step": "life-advance"}},
            current, [], set(),
        )
    if read_faction_gift_ledger_v1(tmp_path)["pending"] != old:
        pytest.fail("timed out gift changed its unresolved ledger")


def test_submit_persists_identity_before_accepting_pending_ack(monkeypatch, tmp_path: Path) -> None:
    driver = Driver(tmp_path, snapshot())
    driver._last_checkpoint = {
        "status": "saved", "sha256": "a" * 64, "date_raw": DATE,
        "episode_run_id": "native-32904-a",
    }
    monkeypatch.setattr(route, "_process_identity",
                        lambda pid: {"creation_date": "20261019131054.525692+480"})
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
                        lambda pid: {"creation_date": "20261019051054.525693+000"})
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
                        lambda pid: {"creation_date": "20261019051054.525693+000"})
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


def _service_planning_wrapper():
    """Use the actual consumer seam without constructing a live Driver."""
    import ast
    source = Path(__file__).parents[2] / "src/xar_autoplayer/bridge/service.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    service = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "GameplayBridgeService")
    wrapper = next(n for n in service.body if isinstance(n, ast.FunctionDef)
                   and n.name == "_plan_turn_internal")
    namespace = {"__package__": "xar_autoplayer.bridge"}
    exec(compile(ast.Module(body=[wrapper], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["_plan_turn_internal"]


def test_pending_ready_replans_whole_service_once_then_queries_original_receipt(
    monkeypatch, tmp_path: Path,
) -> None:
    from types import SimpleNamespace
    old = pending(tmp_path)
    driver = Driver(tmp_path, snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"]))
    fresh = snapshot(revision=414, native_revision=old["pre_native_snapshot_revision"] + 1)
    monkeypatch.setattr(route, "_process_identity", lambda pid: {"creation_date": "20261019131054.525692+480"})
    calls, waits = [], []
    ledger_bytes = (tmp_path / "native-session/faction-gift-pending-v1.json").read_bytes()

    def wait(start, predicate, *, timeout_seconds):
        waits.append(timeout_seconds)
        assert predicate(fresh)
        driver.current = fresh
        return fresh

    def plan_once(**kwargs):
        current = driver.take_internal_semantic_snapshot()
        calls.append((current["revision"], current["native_revision"]))
        return route.plan_faction_gift_private_v1(driver, {
            "snapshot_id": current["snapshot_id"], "revision": current["revision"],
            "plan": {"selected_step": "life-advance"}}, current, [], set())

    driver._wait_for_snapshot = wait
    planned = _service_planning_wrapper()(SimpleNamespace(
        _plan_turn_internal_without_readonly_retry_v1=plan_once))
    assert calls == [(413, 13), (414, 14)] and waits == [5.0]
    assert planned["snapshot_id"] == "s414" and planned["revision"] == 414
    assert planned["plan"]["selected_step"] == route.RECEIPT_STEP
    assert planned["plan"]["faction_gift_pending_action"]["request_id"] == old["request_id"]
    proof = planned["readonly_planning_replan_v1"]
    assert proof["fresh_replans"] == 1 and proof["business_actions_replayed"] == 0
    assert proof["original_rejections"][0]["class"] == "faction_pending_receipt_paused_frame_ready"
    assert driver.endpoint.sent == []
    assert (tmp_path / "native-session/faction-gift-pending-v1.json").read_bytes() == ledger_bytes

    # An independent synthetic receipt, separate from ACK and the frame proof.
    driver.state.result = {"step": route.RECEIPT_STEP, "status": "applied", "receipt": {
        "schema_version": 1, "request_id": old["request_id"], "status": "mitigated",
        "postcondition_verified": True, "mitigation_applied": True,
        "source_faction_id": old["source_faction_id"], "recipient_character_id": old["recipient_character_id"],
        "player_character_id": old["pre_player_character_id"],
        "post_snapshot_revision": 14, "post_native_snapshot_revision": 14,
        "post_observed_date_raw": DATE, "post_player_gold_raw": 17_500_000,
        "post_gift_opinion_present": True, "post_gift_opinion_modifier_value": 25}}
    result = route.query_faction_gift_receipt_private_v1(driver,
        pending=planned["plan"]["faction_gift_pending_action"], expected_revision=planned["revision"])
    assert result["status"] == "applied"
    assert [sent["step"] for sent in driver.endpoint.sent] == [route.RECEIPT_STEP]
    assert read_faction_gift_ledger_v1(tmp_path)["pending"] is None


@pytest.mark.parametrize("change", ["actor", "date", "episode", "pid", "generation",
                                   "regressed_native", "regressed_public", "timeout", "event"])
def test_pending_wait_foreign_or_unready_frame_never_qualifies_for_replan(
    monkeypatch, tmp_path: Path, change: str,
) -> None:
    from xar_autoplayer.bridge.readonly_planning_retry_v1 import retry_readonly_planning_once_v1
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"])
    fresh = snapshot(revision=414, native_revision=old["pre_native_snapshot_revision"] + 1)
    if change == "actor":
        fresh["played_character"] = {"character_id": 123, "alive": True}
    elif change == "date":
        fresh["date_raw"] += 24
    elif change == "episode":
        fresh["episode_run_id"] = "foreign-episode"
    elif change == "pid":
        fresh["diagnostics"]["bridge_pid"] += 1
    elif change == "generation":
        fresh["diagnostics"]["connection_generation"] += 1
    elif change == "regressed_native":
        fresh["native_revision"] = old["pre_native_snapshot_revision"] - 1
    elif change == "regressed_public":
        fresh["revision"] = current["revision"]
    elif change == "timeout":
        fresh = current
    else:
        fresh["active_event"] = {"instance_id": 1}
    driver = Driver(tmp_path, current)
    driver._wait_for_snapshot = lambda *args, **kwargs: fresh
    monkeypatch.setattr(route, "_process_identity", lambda pid: {"creation_date": "20261019131054.525692+480"})
    calls = []

    def plan_once():
        calls.append(1)
        return route.plan_faction_gift_private_v1(driver, {
            "snapshot_id": current["snapshot_id"], "revision": current["revision"],
            "plan": {"selected_step": "life-advance"}}, current, [], set())

    with pytest.raises(route.BridgeUnavailableError) as caught:
        retry_readonly_planning_once_v1(plan_once)
    assert not isinstance(caught.value, route.FactionGiftPendingFrameReadyError)
    assert calls == [1] and driver.endpoint.sent == []
    assert read_faction_gift_ledger_v1(tmp_path)["pending"] == old


def test_untyped_or_altered_pending_ready_proof_is_not_retried(monkeypatch, tmp_path: Path) -> None:
    from copy import deepcopy
    from xar_autoplayer.bridge.readonly_planning_retry_v1 import classify_readonly_planning_error_v1
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"])
    fresh = snapshot(revision=414, native_revision=old["pre_native_snapshot_revision"] + 1)
    driver = Driver(tmp_path, current)
    driver._wait_for_snapshot = lambda *args, **kwargs: fresh
    monkeypatch.setattr(route, "_process_identity", lambda pid: {"creation_date": "20261019131054.525692+480"})
    with pytest.raises(route.FactionGiftPendingFrameReadyError) as caught:
        route.plan_faction_gift_private_v1(driver, {"plan": {"selected_step": "life-advance"}},
                                         current, [], set())
    original = caught.value.readonly_faction_pending_frame_v1
    assert classify_readonly_planning_error_v1(caught.value) is not None
    assert classify_readonly_planning_error_v1(route.PreSubmissionRevisionMismatchError(str(caught.value))) is None
    for mutation in ("business_submission_attempted", "receipt_query_attempted", "gift_submission_replayed"):
        proof = deepcopy(original)
        proof[mutation] = True
        assert classify_readonly_planning_error_v1(route.FactionGiftPendingFrameReadyError(proof)) is None
    unknown = deepcopy(original)
    unknown["unreviewed"] = True
    assert classify_readonly_planning_error_v1(route.FactionGiftPendingFrameReadyError(unknown)) is None


def test_repeated_typed_ready_race_shares_existing_one_retry_budget(monkeypatch, tmp_path: Path) -> None:
    from xar_autoplayer.bridge.readonly_planning_retry_v1 import retry_readonly_planning_once_v1
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"])
    fresh = snapshot(revision=414, native_revision=old["pre_native_snapshot_revision"] + 1)
    driver = Driver(tmp_path, current)
    driver._wait_for_snapshot = lambda *args, **kwargs: fresh
    monkeypatch.setattr(route, "_process_identity", lambda pid: {"creation_date": "20261019131054.525692+480"})
    calls = []

    def plan_once():
        calls.append(1)
        return route.plan_faction_gift_private_v1(driver, {"plan": {"selected_step": "life-advance"}},
                                                 current, [], set())

    with pytest.raises(route.FactionGiftPendingFrameReadyError):
        retry_readonly_planning_once_v1(plan_once)
    assert calls == [1, 1] and driver.endpoint.sent == []
    assert read_faction_gift_ledger_v1(tmp_path)["pending"] == old


def test_equal_dmtf_birth_spellings_select_receipt_and_forbid_cold_query(monkeypatch, tmp_path: Path) -> None:
    old = pending(tmp_path)
    current = snapshot(revision=413, native_revision=old["pre_native_snapshot_revision"] + 1)
    driver = Driver(tmp_path, current)
    # Same physical instant: WMI local+480 versus Toolhelp UTC+000.
    monkeypatch.setattr(route, "_process_identity", lambda pid: {"creation_date": "20261019051054.525692+000"})
    before = (tmp_path / "native-session/faction-gift-pending-v1.json").read_bytes()
    planned = route.plan_faction_gift_private_v1(driver, {
        "snapshot_id": current["snapshot_id"], "revision": current["revision"],
        "plan": {"selected_step": "life-advance"}}, current, [], set())
    assert planned["plan"]["selected_step"] == route.RECEIPT_STEP
    assert planned["plan"]["faction_gift_pending_action"]["source_bridge_creation_date"] == "20261019131054.525692+480"
    # The same normalized comparison must guard the independent cold executor.
    with pytest.raises(route.BridgeUnavailableError, match="requires a replaced CK3 process"):
        route.query_faction_gift_cold_recovery_private_v1(driver, pending=old, expected_revision=413)
    # And the receipt executor must permit this same birth, without submitting a gift.
    driver.state.result = {"status": "not_applied"}
    with pytest.raises(route.StepPostconditionError):
        route.query_faction_gift_receipt_private_v1(driver, pending=old, expected_revision=413)
    assert [row["step"] for row in driver.endpoint.sent] == [route.RECEIPT_STEP]
    assert (tmp_path / "native-session/faction-gift-pending-v1.json").read_bytes() == before


def test_different_microsecond_birth_is_a_new_process_even_at_same_pid():
    old = {"source_bridge_pid": 12345, "source_bridge_creation_date": "20261019131054.525692+480"}
    assert route._same_pending_process(12345, "20261019051054.525693+000", old) is False
    assert route._same_pending_process(23456, "20261019051054.525692+000", old) is False
    # Preserve exact historical synthetic/archived spellings, not a new parse claim.
    assert route._same_pending_process(12345, "historic-process-marker", {
        "source_bridge_pid": 12345, "source_bridge_creation_date": "historic-process-marker"}) is True


@pytest.mark.parametrize("current,original", [
    ("malformed", "20261019131054.525692+480"),
    ("20261019051054.525692+000", None),
    (None, "20261019131054.525692+480"),
    ("None", "None"),
])
def test_unequal_or_missing_process_birth_is_unknown_not_cold(current, original):
    with pytest.raises(route.BridgeUnavailableError, match="birth comparison is unknown"):
        route._same_pending_process(12345, current, {
            "source_bridge_pid": 12345, "source_bridge_creation_date": original})
