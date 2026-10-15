import ctypes
import os
import threading
import time

from xar_autoplayer.bridge.auto_camera_follow import LatestCameraFollowWorker
from xar_autoplayer.bridge.realm_overview_camera import (
    EXACT_SHA, MAGIC, NativeCameraPresentationClient, PeaceRealmCameraPolicy,
    _Request, _Result, _Shared,
)


def payload(day=0, actor=29829, **extra):
    return {"source_frame": {"date_raw": 53144328 + day * 24,
                             "actor_character_id": actor, "episode_run_id": "episode",
                             "bridge_pid": 123, "connection_generation": 1},
            "map_ready": True, "active_wars": [], "has_active_event": False,
            "has_pending_interaction": False, "mandatory_choice": False,
            "source_build": {"game_version": "1.20.0.4", "executable_sha256": EXACT_SHA},
            "has_player_armies": False, **extra}


def test_peace_requires_thirty_game_days_and_refreshes_monthly():
    policy = PeaceRealmCameraPolicy()
    assert policy.observe(payload(), None)["mode"] == "hold"
    assert policy.observe(payload(29), None)["mode"] == "hold"
    assert policy.observe(payload(30), None)["mode"] == "realm"
    assert policy.observe(payload(59), None)["reason"] == "holding_realm_overview"
    assert policy.observe(payload(60), None)["mode"] == "realm"


def test_hotspot_preempts_realm_and_restarts_peace_timer():
    policy = PeaceRealmCameraPolicy()
    policy.observe(payload(), None)
    policy.observe(payload(30), None)
    hotspot = {"title_key": "b_bari", "reason": "battle"}
    assert policy.observe(payload(31), hotspot)["mode"] == "hotspot"
    assert policy.observe(payload(32), hotspot)["mode"] == "hold"
    assert policy.observe(payload(33), {**hotspot, "title_key": "b_napoli"})["mode"] == "hotspot"
    assert policy.observe(payload(34), None)["mode"] == "hold"
    assert policy.observe(payload(64), None)["mode"] == "realm"


def test_forced_choice_war_without_anchor_and_succession_reset_timer():
    for block in ({"mandatory_choice": True}, {"has_active_event": True},
                  {"has_pending_interaction": True}, {"active_wars": [{"war_id": 1}]},
                  {"has_player_armies": True}):
        policy = PeaceRealmCameraPolicy()
        policy.observe(payload(), None)
        policy.observe(payload(30), None)
        assert policy.observe(payload(31, **block), None)["mode"] == "cancel"
        assert policy.observe(payload(32), None)["mode"] == "hold"
        assert policy.observe(payload(61), None)["mode"] == "hold"
        assert policy.observe(payload(62), None)["mode"] == "realm"
    policy = PeaceRealmCameraPolicy()
    policy.observe(payload(), None)
    policy.observe(payload(30), None)
    assert policy.observe(payload(31, actor=40526), None)["mode"] == "hold"
    assert policy.observe(payload(61, actor=40526), None)["mode"] == "realm"


def test_sustained_requests_do_not_starve_latest_worker():
    entered = threading.Event()
    seen = []
    worker = LatestCameraFollowWorker(lambda value: (seen.append(value), entered.set(),
                                                     {"status": "available"})[-1],
                                    quiet_seconds=.03)
    try:
        deadline = time.monotonic() + .4
        index = 0
        while not entered.is_set() and time.monotonic() < deadline:
            worker.schedule(index)
            index += 1
            time.sleep(.005)
        assert entered.is_set()
        assert seen[0] > 0
    finally:
        worker.close_without_wait()


class FakeKernel:
    def GetTickCount64(self):
        return 9000

    def FlushProcessWriteBuffers(self):
        pass

    def InterlockedCompareExchange(self, pointer, exchange, compare):
        old = pointer.contents.value
        if old == compare:
            pointer.contents.value = exchange
        return old

    def InterlockedExchange(self, pointer, value):
        old = pointer.contents.value
        pointer.contents.value = value
        return old


def client_fixture():
    client = object.__new__(NativeCameraPresentationClient)
    shared = _Shared(magic=MAGIC, version=1, pid=123)
    client.pid, client._handle, client._hwnd = 123, None, None
    client._view = ctypes.addressof(shared)
    client._kernel, client._lock = FakeKernel(), threading.Lock()
    client._last_result_sequence, client._latest = -1, None
    return client, shared


def test_wire_layout_and_latest_only_publication_without_driver(monkeypatch):
    assert ctypes.sizeof(_Request) == 168
    assert _Shared.request.offset == 24
    assert _Shared.result.offset == 192
    assert _Result.county_ids.offset == 104
    monkeypatch.setattr("xar_autoplayer.bridge.realm_overview_camera.desktop1_game_window",
                        lambda pid, hwnd: 4242)
    client, shared = client_fixture()
    source = {"game_version": "1.20.0.4", "executable_sha256": EXACT_SHA}
    first = client.submit({"mode": "realm", "reason": "peace"}, payload()["source_frame"], source)
    assert abs(shared.request.padding - .32) < 1e-6
    second = client.submit({"mode": "hotspot", "title_key": "b_bari"},
                           payload(1)["source_frame"], source)
    assert abs(shared.request.padding - .15) < 1e-6
    assert first["request_sequence"] == 2 and second["request_sequence"] == 4
    assert shared.request.mode == 2 and shared.request.title_key == b"b_bari"
    assert shared.request.hwnd == 4242 and shared.request.expires_uptime_ms == 19000
    assert second["native_command_pipe_used"] is False
    assert second["camera_postcondition_verified"] is False


def test_partial_receipt_never_becomes_success():
    client, shared = client_fixture()
    shared.result_sequence = 2
    shared.result.request_sequence, shared.result.status = 2, 1
    shared.result.county_count = 2
    shared.result.county_ids[0], shared.result.county_ids[1] = 101, 202
    shared.result.bounds[:] = [10, 20, 1000, 900]
    actual = client.latest()
    assert actual["status"] == "submitted"
    assert actual["county_title_ids"] == [101, 202]
    assert actual["camera_postcondition_verified"] is False
    assert actual["coverage_verified"] is False
    shared.result_sequence = 3
    shared.result.status = 2
    assert client.latest()["status"] == "submitted"
    shared.result.zoom_index, shared.result_sequence = 5, 4
    assert client.latest()["camera_postcondition_verified"] is True
    assert client.latest()["coverage_verified"] is False


def test_service_selects_and_publishes_without_gameplay_snapshot_or_pipe():
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex

    class ForbiddenDriver:
        def take_snapshot(self, **_):
            raise AssertionError("presentation attempted another snapshot")

    class Client:
        pid = 123
        def __init__(self):
            self.intents = []
        def submit(self, intent, frame, source):
            self.intents.append(dict(intent))
            return {"status": "queued_native_presentation", "mode": intent["mode"]}
        def latest(self):
            return {"status": "submitted", "coverage_verified": False}

    service = GameplayBridgeService(ForbiddenDriver())
    service.bind_war_hotspot_camera_index(LandedProvinceIndex({}, {}, ()))
    client = Client()
    service._camera_presentation_client = client
    service._select_auto_camera_hotspot(payload())
    result = service._select_auto_camera_hotspot(payload(30))
    assert client.intents == [{"mode": "realm", "reason": "peace_realm_overview",
                               "quiet_days_observed": 30.0}]
    assert result["display_mode"] == "realm"
    assert result["same_frame_with_gameplay_claim"] is False
    service._auto_camera_worker.close_without_wait()


def test_stationary_peace_armies_allow_overview_but_movement_preempts():
    from xar_autoplayer.bridge.service import GameplayBridgeService
    frame = payload()["source_frame"]
    for army, expected in [({"army_state": "idle"}, False),
                           ({"army_state": "moving"}, True),
                           ({"move_target_province_id": 42}, True),
                           ({"in_combat": True}, True)]:
        observed = GameplayBridgeService._auto_camera_hotspot_input(
            {"player_armies": [army], "active_wars": [], "map_ready": True}, frame)
        assert observed["has_player_armies"] is expected


def test_repeated_auto_results_do_not_copy_complete_county_lists():
    reference = LatestCameraFollowWorker._reference({
        "request_id": "camera-1", "status": "completed",
        "receipt": {"display_mode": "realm", "native_actual": {
            "status": "settled", "county_count": 16384,
            "county_title_ids": list(range(16384)), "coverage_verified": False}}})
    assert reference["receipt"]["native_actual"]["county_count"] == 16384
    assert "county_title_ids" not in reference["receipt"]["native_actual"]


def test_windows_transport_binds_actual_exports_without_contacting_game():
    if os.name != "nt":
        return
    client = NativeCameraPresentationClient(123)
    assert client._view is None
    client.close()


def test_windows_mapping_publication_and_receipt_without_game_or_desktop(monkeypatch):
    if os.name != "nt":
        return
    import mmap
    pid = 0x60000000 + os.getpid()
    mapping = mmap.mmap(-1, 131072, tagname=f"Local\\XarCK3CameraPresentationV1-{pid}")
    shared = _Shared.from_buffer(mapping)
    shared.magic, shared.version, shared.pid = MAGIC, 1, pid
    client = NativeCameraPresentationClient(pid)
    monkeypatch.setattr("xar_autoplayer.bridge.realm_overview_camera.desktop1_game_window",
                        lambda owned_pid, cached: 4242)
    try:
        frame = payload()["source_frame"]
        queued = client.submit({"mode": "realm"}, frame,
                               {"game_version": "1.20.0.4", "executable_sha256": EXACT_SHA})
        assert shared.request_sequence == queued["request_sequence"] == 2
        assert shared.request.actor == frame["actor_character_id"]
        shared.result_sequence = 1
        shared.result.request_sequence, shared.result.status = 2, 2
        shared.result.zoom_index, shared.result.county_count = 3, 1
        shared.result.county_ids[0] = 101
        shared.result_sequence = 2
        actual = client.latest()
        assert actual["camera_postcondition_verified"] is True
        assert actual["county_title_ids"] == [101]
        assert actual["coverage_verified"] is False
    finally:
        client.close()
        del shared
        mapping.close()
