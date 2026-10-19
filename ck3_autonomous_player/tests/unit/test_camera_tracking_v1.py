"""Actual SDK camera mailbox in synthetic memory; no Win32/Game operation."""
from copy import deepcopy
import ctypes as C
from types import SimpleNamespace
import threading
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge import camera_tracking_v1 as t
from xar_autoplayer.bridge import realm_overview_camera as realm
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex
from test_auto_camera_pre_advance_v1 import tactical


def payload():
    return {"source_frame": {"actor_character_id": 40526, "date_raw": 1000},
            "tracking_scope": {"state": "armed", "generation": 0x100000001,
                "starting_date_raw": 1000, "target_date_raw": 1240, "watch_army_ids": [33554800]},
            "active_wars": [{"allied_armies": [{"army_id": 33554800, "controllable": True,
                "retreating": False, "in_combat": False, "current_province_id": 1,
                "route_province_ids": [2, 3], "move_target_province_id": 3}]}]}


INDEX = LandedProvinceIndex({i: f"b_p{i}" for i in range(1, 40)}, {}, ())


def memory_client(monkeypatch):
    memory = (C.c_ubyte * realm.MAPPING_BYTES)()
    shared = realm._Shared.from_buffer(memory)
    shared.magic, shared.version, shared.pid = realm.MAGIC, 1, 999
    tail = t.Shared.from_buffer(memory, t.OFFSET)
    tail.magic, tail.version, tail.byte_size, tail.provider_pid = t.MAGIC, 1, C.sizeof(t.Shared), 999
    tail.active, tail.owner_epoch, tail.capability_sequence = 1, 7, 2
    client = object.__new__(realm.NativeCameraPresentationClient)
    client.pid, client._view, client._handle, client._hwnd = 999, C.addressof(memory), None, None
    client._lock, client._tracking_binding = threading.Lock(), None
    client._last_result_sequence, client._latest = -1, None
    client._diagnostic_request_binding = None
    client._open = lambda: None
    client._kernel = SimpleNamespace(GetTickCount64=lambda: 10000, FlushProcessWriteBuffers=lambda: None)
    monkeypatch.setattr(realm, "desktop1_game_window", lambda pid, hwnd: 123)
    return memory, shared, tail, client


BUILD = {"game_version": "1.20.0.4", "executable_sha256": realm.EXACT_SHA}


def test_real_wire_layout_nonoverlap_and_native_generation_precision():
    assert (C.sizeof(t.Request), C.sizeof(t.Result), C.sizeof(t.Shared)) == (4264, 80, 4384)
    assert realm._Shared.result.offset + C.sizeof(realm._Result) == 65832
    assert 0x18000 + 168 < t.OFFSET < t.OFFSET + t.REGION_BYTES <= realm.MAPPING_BYTES
    p = payload(); intent = t.tracking_intent_v1(p, INDEX)
    assert intent["scope_generation"] == 0x100000001
    assert intent["provinces"] == [(1, "b_p1"), (2, "b_p2"), (3, "b_p3")]


def test_incompatible_layout_rejects_even_with_python_optimization():
    source = Path(t.__file__).read_text(encoding="utf-8")
    original = "!= (132, 4264, 80, 4384)"
    assert source.count(original) == 1
    poisoned = source.replace(original, "!= (132, 4265, 80, 4384)")
    with pytest.raises(RuntimeError, match="wire layout"):
        exec(compile(poisoned, t.__file__, "exec", optimize=2), {})


@pytest.mark.parametrize("change", ["unarmed", "not_watched", "foreign", "retreat", "unknown_province",
                                   "overflow", "date", "generation_bool", "conflicting_duplicate"])
def test_scope_and_finite_route_fail_closed(change):
    p = payload(); scope = p["tracking_scope"]; army = p["active_wars"][0]["allied_armies"][0]
    if change == "unarmed": scope["state"] = "triggered"
    if change == "not_watched": scope["watch_army_ids"] = [99]
    if change == "foreign": army["controllable"] = False
    if change == "retreat": army["retreating"] = True
    if change == "unknown_province": army["route_province_ids"] = [500]
    if change == "overflow": army["route_province_ids"] = list(range(1, 34))
    if change == "date": scope["target_date_raw"] = 1000
    if change == "generation_bool": scope["generation"] = True
    if change == "conflicting_duplicate":
        other = deepcopy(army); other["current_province_id"] = 2
        p["active_wars"].append({"allied_armies": [other]})
    assert t.tracking_intent_v1(p, INDEX) is None


def test_actual_submit_binds_same_even_request_and_small_result(monkeypatch):
    memory, shared, tail, client = memory_client(monkeypatch)
    p = payload(); intent = t.tracking_intent_v1(p, INDEX)
    queued = client.submit(intent, p["source_frame"], BUILD)
    assert queued["mode"] == "tracked_hotspot" and queued["camera_postcondition_verified"] is False
    assert shared.request.mode == 4 and shared.request_sequence == tail.request.request_sequence == 2
    assert tail.request.owner_epoch == 7 and tail.request.scope_generation == 0x100000001
    assert shared.request.expires_uptime_ms == 130000
    r = tail.result
    for key, value in client._tracking_binding.items(): setattr(r, key, value)
    r.state, r.date_raw, r.province_id, r.combat_id, r.target_updates = 1, 1024, 2, 42, 2
    tail.result_sequence = 2
    actual = client.latest()
    assert actual["tracking_active"] is True and actual["province_id"] == 2
    assert actual["camera_postcondition_verified"] is False
    assert actual["continuous_frame_coverage_verified"] is False
    from xar_autoplayer.bridge.auto_camera_follow import LatestCameraFollowWorker
    r.state, r.reader_reason, r.pending_slot_capacity, r.pending_slots_visited = 11, 18, 1024, 32
    tail.result_sequence += 2
    ref = LatestCameraFollowWorker._reference({"request_id": "t", "status": "completed",
        "receipt": {"native_actual": client.latest()}})["receipt"]["native_actual"]
    assert (ref["state"], ref["reader_reason"], ref["pending_slot_capacity"], ref["pending_slots_visited"]) == (11, 18, 1024, 32)
    r.scope_generation += 1
    assert client.latest() is None


def test_missing_native_capability_and_torn_capability_never_submit(monkeypatch):
    memory, shared, tail, client = memory_client(monkeypatch)
    p = payload(); intent = t.tracking_intent_v1(p, INDEX)
    for mode in ("absent", "wrong_pid", "inactive", "odd"):
        tail.magic, tail.provider_pid, tail.active, tail.capability_sequence = t.MAGIC, 999, 1, 2
        if mode == "absent": tail.magic = 0
        if mode == "wrong_pid": tail.provider_pid += 1
        if mode == "inactive": tail.active = 0
        if mode == "odd": tail.capability_sequence = 3
        assert client.submit(intent, p["source_frame"], BUILD)["status"] == "unavailable"
        assert shared.request_sequence == 0 and shared.request.mode == 0


def test_torn_result_and_foreign_binding_are_not_observations(monkeypatch):
    memory, shared, tail, client = memory_client(monkeypatch)
    p = payload(); client.submit(t.tracking_intent_v1(p, INDEX), p["source_frame"], BUILD)
    for key, value in client._tracking_binding.items(): setattr(tail.result, key, value)
    tail.result.state, tail.result_sequence = 1, 3
    assert client.latest() is None
    tail.result_sequence = 4; tail.result.owner_epoch += 1
    assert client.latest() is None


@pytest.mark.parametrize("mode,number", [("cancel", 0), ("realm", 1), ("hotspot", 2), ("query", 3)])
def test_legacy_modes_keep_original_wire_and_lease(monkeypatch, mode, number):
    memory, shared, tail, client = memory_client(monkeypatch)
    p = payload()
    queued = client.submit({"mode": mode, "title_key": "b_p1"}, p["source_frame"], BUILD)
    assert shared.request.mode == number and shared.request.expires_uptime_ms == 20000
    assert client._tracking_binding is None and tail.request.request_sequence == 0
    assert queued["native_command_pipe_used"] is False


def test_real_auto_passes_only_validated_arm_scope_before_same_resume(monkeypatch):
    with tactical(monkeypatch) as (service, driver, planned, order, initial):
        service.auto_turn(before_submit=lambda _: None)
        urgent = service._auto_camera_worker.calls[0][0]
        scope = urgent["tracking_scope"]
        assert scope["state"] == "armed" and scope["generation"] == 7
        assert scope["watch_army_ids"] == [501]
        assert order.index("urgent") < order.index("resume-map")
        submits = []
        service._publish_camera_presentation_v1 = lambda intent, data: submits.append(intent) or {"status": "queued"}
        assert service._select_auto_camera_hotspot(urgent)["status"] == "queued"
        assert submits[0]["mode"] == "tracked_hotspot" and submits[0]["army_id"] == 501
        before = len(order)
        # A second ordinary projection does not query or replay any gameplay.
        service._select_auto_camera_hotspot(urgent)
        assert len(order) == before
