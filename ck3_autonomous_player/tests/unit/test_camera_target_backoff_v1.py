"""Use the production selector/policy/publisher; fake only the Native boundary."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.realm_overview_camera import PeaceRealmCameraPolicy
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex


def payload(day=0, kind="battle", province=1, **frame_changes):
    frame = {"actor_character_id": 31254, "episode_run_id": "episode-1",
             "bridge_pid": 123, "connection_generation": 1,
             "date_raw": 53144328 + day * 24, "native_revision": day + 1,
             "revision": day + 1, "snapshot_id": f"native:{day + 1}"}
    frame.update(frame_changes)
    armies = [] if kind is None else [{"army_id": 3, "current_province_id": province,
        "controllable": True, "in_combat": kind == "battle",
        "army_state": kind, "retreating": False}]
    return {"source_frame": frame, "map_ready": True,
            "active_wars": [{"war_id": 1, "allied_armies": armies}],
            "source_build": {"game_version": "1.20.0.4"}}


class NativeBoundary:
    def __init__(self, pid):
        self.pid, self.sequence, self.actual = pid, 0, None
        self.requests = []

    def submit(self, intent, frame, source):
        self.sequence += 2
        self.requests.append((deepcopy(intent), dict(frame)))
        return {"status": "queued_native_presentation", "request_sequence": self.sequence,
                "native_command_pipe_used": False, "camera_postcondition_verified": False}

    def latest(self):
        return deepcopy(self.actual)

    def close(self):
        pass

    def result(self, status="window_unavailable", **changes):
        frame = self.requests[-1][1]
        self.actual = {"request_sequence": self.sequence, "status": status,
                       "actor_character_id": frame["actor_character_id"],
                       "date_raw": frame["date_raw"], "zoom_index": 4,
                       "target": [1., 2., 3., 4., 5., 6.],
                       "current": [1., 2., 3., 4., 5., 6.],
                       "camera_postcondition_verified": status == "settled"}
        self.actual.update(changes)
        return deepcopy(self.actual)


@pytest.fixture
def camera(monkeypatch):
    monkeypatch.setenv("XAR_CK3_ARMY_TIMING_JSONL", "")
    clients = []

    def factory(pid):
        client = NativeBoundary(pid)
        clients.append(client)
        return client

    monkeypatch.setattr("xar_autoplayer.bridge.realm_overview_camera.NativeCameraPresentationClient",
                        factory)
    obj = object.__new__(GameplayBridgeService)
    obj._camera_presentation_client = None
    obj._camera_presentation_requested_sequence = None
    obj._camera_presentation_failure_sequence = None
    obj._camera_presentation_owner_key = None
    obj._camera_presentation_request_context = None
    obj._camera_presentation_target_backoffs = {}
    obj._camera_test_clock = [100.0]
    obj._peace_realm_camera_policy = PeaceRealmCameraPolicy(clock=lambda: obj._camera_test_clock[0])
    obj._war_hotspot_camera_index = LandedProvinceIndex(
        {1: "b_first", 2: "b_second"}, {}, ())
    obj._war_hotspot_camera_index_error = None
    return obj, clients


@pytest.mark.parametrize("new_province", [1, 2])
def test_siege_failure_does_not_block_next_day_battle(camera, new_province):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload(kind="siege"))
    clients[0].result()
    result = obj._select_auto_camera_hotspot(payload(1, province=new_province))
    assert len(clients[0].requests) == 2
    assert clients[0].requests[-1][0]["reason"] == "battle"
    assert clients[0].requests[-1][0]["title_key"] == (
        "b_first" if new_province == 1 else "b_second")
    assert result["native_actual"] is None
    assert result["native_actual_source_frame"] is None
    assert result["available"] is False


def test_same_failed_battle_waits_then_reissues_and_ignores_previous_failure(camera):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    old = clients[0].result()
    for day in [1, 2, 29]:
        result = obj._select_auto_camera_hotspot(payload(day))
        assert result["reason"] == "camera_retry_cooldown"
        assert len(clients[0].requests) == 1
        assert obj._peace_realm_camera_policy.quiet_since is None
    assert obj._select_auto_camera_hotspot(payload(30))["status"] == "queued_native_presentation"
    assert len(clients[0].requests) == 2
    assert obj._select_auto_camera_hotspot(payload(31))["native_actual"] is None
    assert clients[0].actual == old
    assert not obj._camera_presentation_target_backoffs


@pytest.mark.parametrize("change", [
    {"actor_character_id": 40526}, {"episode_run_id": "episode-2"},
    {"bridge_pid": 456}, {"connection_generation": 2}])
@pytest.mark.parametrize("old_status", ["window_unavailable", "settled"])
def test_owner_change_clears_backoff_and_old_actual(camera, change, old_status):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    clients[0].result(old_status)
    if old_status != "settled":
        obj._select_auto_camera_hotspot(payload(1))
        assert obj._camera_presentation_target_backoffs
    result = obj._select_auto_camera_hotspot(payload(2, **change))
    assert sum(len(c.requests) for c in clients) == 2
    assert not obj._camera_presentation_target_backoffs
    assert result["native_actual"] is None and result["available"] is False
    assert obj._camera_presentation_request_context["owner"] == (
        40526 if "actor_character_id" in change else 31254,
        change.get("episode_run_id", "episode-1"), change.get("bridge_pid", 123),
        change.get("connection_generation", 1))


@pytest.mark.parametrize("change", [
    {"request_sequence": 0}, {"actor_character_id": 40526},
    {"date_raw": 53144327}, {"date_raw": 53144328 + 7 * 24 + 1}])
@pytest.mark.parametrize("status", ["window_unavailable", "settled"])
def test_unbound_native_failure_or_success_has_no_target_credit(camera, change, status):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    clients[0].result(status, **change)
    result = obj._select_auto_camera_hotspot(payload(1))
    assert result["native_actual"] is None and result["available"] is False
    assert not obj._camera_presentation_target_backoffs
    assert obj.realm_camera_status_v1()["native_actual"] is None


@pytest.mark.parametrize("delay", [1, 7 * 24])
def test_native_processing_date_can_legally_follow_cached_submission(camera, delay):
    obj, clients = camera
    original = payload()
    obj._select_auto_camera_hotspot(original)
    actual = clients[0].result("settled", date_raw=53144328 + delay)
    result = obj._select_auto_camera_hotspot(original)
    assert result["available"] is True
    assert result["native_actual"] == actual
    assert result["native_actual_source_frame"] == original["source_frame"]
    assert result["same_frame_with_gameplay_claim"] is False
    assert obj.realm_camera_status_v1()["native_actual"] == actual


def test_target_readback_cannot_change_within_a_request(camera):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    clients[0].result("submitted")
    assert obj._select_auto_camera_hotspot(payload())["native_actual"]["status"] == "submitted"
    clients[0].result("settled", target=[9.] * 6, current=[9.] * 6)
    assert obj._select_auto_camera_hotspot(payload(1))["native_actual"] is None


@pytest.mark.parametrize("status", [None, "unavailable", "submitted"])
def test_unconfirmed_original_request_retries_after_thirty_days_without_failure_credit(camera, status):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    if status == "unavailable":
        # Native can fail before read_snapshot; this cannot qualify an actor/date.
        clients[0].result(status, actor_character_id=-1, date_raw=0)
    elif status is not None:
        clients[0].result(status)
    for day in [1, 29]:
        result = obj._select_auto_camera_hotspot(payload(day))
        assert len(clients[0].requests) == 1 and result["available"] is False
        assert not obj._camera_presentation_target_backoffs
    result = obj._select_auto_camera_hotspot(payload(30))
    assert len(clients[0].requests) == 2
    assert result["status"] == "queued_native_presentation"
    assert result["native_actual"] is None and result["available"] is False
    assert not obj._camera_presentation_target_backoffs


@pytest.mark.parametrize("block", ["mandatory_choice", "has_active_event", "has_pending_interaction"])
def test_mandatory_cancel_bypasses_failed_target_backoff_and_resets_quiet(camera, block):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload(0, kind=None))
    obj._select_auto_camera_hotspot(payload(29))
    clients[0].result()
    blocked = payload(30)
    blocked[block] = True
    result = obj._select_auto_camera_hotspot(blocked)
    assert result["intent"]["mode"] == "cancel"
    assert clients[0].requests[-1][0]["mode"] == "cancel"
    assert obj._peace_realm_camera_policy.quiet_since is None
    # A cancel is published before Native captures actor/date, and cannot
    # become an applied hotspot result or impose target backoff.
    clients[0].result("cancelled", actor_character_id=-1, date_raw=0)
    assert obj.realm_camera_status_v1()["native_actual"]["status"] == "cancelled"
    obj._select_auto_camera_hotspot(payload(31, kind=None))
    assert obj._peace_realm_camera_policy.quiet_since == 100
    obj._camera_test_clock[0] += 9
    assert obj._select_auto_camera_hotspot(payload(60, kind=None))["intent"]["mode"] == "hold"
    obj._camera_test_clock[0] += 1
    assert obj._select_auto_camera_hotspot(payload(61, kind=None))["intent"]["mode"] == "realm"


def test_blocked_activity_resets_real_quiet_and_failure_expiry_keeps_anchor(camera):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    clients[0].result()
    obj._select_auto_camera_hotspot(payload(1))
    obj._select_auto_camera_hotspot(payload(2, kind=None))
    assert obj._peace_realm_camera_policy.quiet_since is not None
    obj._select_auto_camera_hotspot(payload(29))
    assert obj._peace_realm_camera_policy.quiet_since is None
    obj._select_auto_camera_hotspot(payload(30, kind=None))
    anchor = obj._camera_test_clock[0]
    obj._camera_test_clock[0] += 9
    assert obj._select_auto_camera_hotspot(payload(59, kind=None))["intent"]["mode"] == "hold"
    obj._camera_test_clock[0] += 1
    assert obj._select_auto_camera_hotspot(payload(60, kind=None))["intent"]["mode"] == "realm"
    clients[0].result()
    assert obj._select_auto_camera_hotspot(payload(61, kind=None))["reason"] == "camera_retry_cooldown"
    assert obj._select_auto_camera_hotspot(payload(89, kind=None))["reason"] == "camera_retry_cooldown"
    assert obj._select_auto_camera_hotspot(payload(90, kind=None))["intent"]["mode"] == "realm"
    assert obj._peace_realm_camera_policy.quiet_since == anchor
    assert [r[0]["mode"] for r in clients[0].requests] == ["hotspot", "realm", "realm"]


@pytest.mark.parametrize("query_only", [True, False])
def test_explicit_entry_uses_context_but_cannot_poison_auto_battle(camera, query_only):
    obj, clients = camera
    source = payload()
    snapshot = {"revision": 1}
    obj.snapshot = lambda **kwargs: snapshot
    obj._observed_planning_source_frame = lambda snapshot: {**source["source_frame"], "status": "complete"}
    obj._auto_camera_hotspot_input = lambda snapshot, frame: {**source, "source_frame": frame}
    obj.center_map_on_player_realm_v1(expected_revision=1, query_only=query_only)
    assert obj._camera_presentation_request_context["mode"] == ("query" if query_only else "realm")
    clients[0].result()
    result = obj._select_auto_camera_hotspot(payload(1))
    assert len(clients[0].requests) == 2
    assert clients[0].requests[-1][0]["mode"] == "hotspot"
    assert result["native_actual"] is None and result["available"] is False
    assert all(k[4] != "query" for k in obj._camera_presentation_target_backoffs)


def test_old_settled_and_query_do_not_claim_new_battle_success(camera):
    obj, clients = camera
    obj._select_auto_camera_hotspot(payload())
    clients[0].result("settled")
    obj._publish_camera_presentation_v1({"mode": "query", "reason": "explicit"}, payload(1))
    result = obj._select_auto_camera_hotspot(payload(2))
    assert len(clients[0].requests) == 3
    assert result["native_actual"] is None and result["available"] is False
    assert obj.realm_camera_status_v1()["native_actual"] is None
