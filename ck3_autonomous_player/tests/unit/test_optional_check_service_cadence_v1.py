"""Exercise the ordinary Service boundary, including technical council deferral."""
from copy import deepcopy
from types import SimpleNamespace

from xar_autoplayer import optional_check_cadence_v1 as cadence
from xar_autoplayer.bridge import service as service_module
from xar_autoplayer.bridge.service import GameplayBridgeService


def _planned(day=0, revision=1):
    return {
        "revision": revision,
        "plan": {"selected_step": "life-advance"},
        "_private_council_snapshot_v1": {
            "episode_run_id": "ordinary-service-test", "paused": True,
            "date_raw": day * 24, "native_revision": revision,
        },
        "_private_council_history_v1": [],
    }


def test_technical_defer_skips_service_until_due_without_noop_or_action(tmp_path, monkeypatch):
    calls = []

    def original(self, planned, available_steps):
        calls.append(planned["revision"])
        current = cadence.frame(planned["_private_council_snapshot_v1"])
        cadence.defer_council_technical_read(
            self.driver.state_dir, current, evidence_path="captured-query.json")
        return planned

    monkeypatch.setattr(service_module, "_optional_check_council_original", original)
    service = GameplayBridgeService(SimpleNamespace(state_dir=tmp_path))
    first = service._plan_private_council_normal_v1(_planned(), {"life-advance"})
    row = cadence._load(tmp_path, "ordinary-service-test")["domains"]["council"]
    assert first["plan"]["selected_step"] == "life-advance"
    assert row["consecutive_no_action"] == 0
    assert row["last_actual_action_frame"] is None
    second = service._plan_private_council_normal_v1(_planned(1, 2), {"life-advance"})
    assert calls == [1]
    assert second["plan"]["council_periodic_review"]["status"] == "technical_read_unavailable_deferred"
    assert "_private_council_snapshot_v1" not in second
    assert second["plan"]["selected_step"] == "life-advance"
    service._plan_private_council_normal_v1(_planned(30, 3), {"life-advance"})
    assert calls == [1, 3]


def test_service_noop_counters_are_independent_and_deduplicate_same_frame(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(service_module, "_optional_check_council_original",
                        lambda self, planned, steps: calls.append(planned["revision"]) or planned)
    service = GameplayBridgeService(SimpleNamespace(state_dir=tmp_path))
    for day in range(3):
        planned = _planned(day, day + 1)
        service._plan_private_council_normal_v1(deepcopy(planned), {"life-advance"})
        if day < 2:
            service._plan_private_council_normal_v1(deepcopy(planned), {"life-advance"})
    state = cadence._load(tmp_path, "ordinary-service-test")
    assert state["domains"]["council"]["next_due_date_raw"] == 32 * 24
    assert all(state["domains"][name]["consecutive_no_action"] == 0
               and state["domains"][name]["next_due_date_raw"] is None
               for name in cadence.DOMAINS if name != "council")
    before = len(calls)
    result = service._plan_private_council_normal_v1(_planned(3, 4), {"life-advance"})
    assert len(calls) == before
    assert result["plan"]["council_periodic_review"]["remaining_game_days"] == 29


def test_pending_council_bypasses_cooldown_and_keeps_receipt_route(tmp_path, monkeypatch):
    from xar_autoplayer import private_council_formal_consumer_v1 as council
    initial = cadence.frame(_planned()["_private_council_snapshot_v1"])
    cadence.defer_council_technical_read(tmp_path, initial, evidence_path="captured-query.json")
    monkeypatch.setattr(council, "read_council_ledger", lambda state_dir: {"pending": {"original_id": 605}})
    seen = []

    def original(self, planned, steps):
        seen.append(planned)
        return {**planned, "plan": {**planned["plan"], "selected_step": "query-council-existing-receipt"}}

    monkeypatch.setattr(service_module, "_optional_check_council_original", original)
    service = GameplayBridgeService(SimpleNamespace(state_dir=tmp_path))
    result = service._plan_private_council_normal_v1(_planned(1, 2), {"life-advance"})
    assert len(seen) == 1
    assert result["plan"]["selected_step"] == "query-council-existing-receipt"
    assert "council_periodic_review" not in result["plan"]
