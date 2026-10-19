import ctypes
import os
import sys
import threading
import time
import types
import uuid

import pytest

from xar_autoplayer.bridge.auto_camera_follow import LatestCameraFollowWorker
from xar_autoplayer.bridge.realm_overview_camera import (
    EXACT_SHA, MAGIC, NativeCameraPresentationClient, PeaceRealmCameraPolicy,
    _Request, _Result, _Shared, desktop1_game_window,
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


def test_forced_choice_and_succession_reset_timer():
    for block in ({"mandatory_choice": True}, {"has_active_event": True},
                  {"has_pending_interaction": True}):
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


@pytest.mark.parametrize("anchor", [None, {"title_key": "b_bari", "reason": "war_objective"},
                                    {"title_key": "b_bari", "reason": "player_army"}])
def test_war_without_activity_reaches_overview_without_refreshing_quiet_timer(anchor):
    policy = PeaceRealmCameraPolicy()
    for day in range(30):
        result = policy.observe(payload(day, active_wars=[{"war_id": 1}],
                                        has_player_armies=True), anchor)
        assert result["mode"] == "hold"
        assert policy.quiet_since == payload()["source_frame"]["date_raw"]
    assert policy.observe(payload(30, active_wars=[{"war_id": 1}],
                                  has_player_armies=True), anchor)["mode"] == "realm"


@pytest.mark.parametrize("reason", ["battle", "siege", "objective_siege",
                                   "moving_player_army", "army_destination"])
def test_activity_preempts_overview_and_restarts_quiet_period(reason):
    policy = PeaceRealmCameraPolicy()
    policy.observe(payload(), None)
    policy.observe(payload(30), None)
    hotspot = {"title_key": "b_bari", "reason": reason}
    assert policy.observe(payload(31), hotspot)["mode"] == "hotspot"
    assert policy.observe(payload(32), hotspot)["mode"] == "hold"
    assert policy.quiet_since is None
    assert policy.observe(payload(33, active_wars=[{}]), None)["mode"] == "hold"
    assert policy.observe(payload(62, active_wars=[{}]), None)["mode"] == "hold"
    assert policy.observe(payload(63, active_wars=[{}]), None)["mode"] == "realm"


def window_fixture(monkeypatch, *, handles=(4242,), client=(0, 0, 1920, 1080),
                   owner=123, desktop_id=None):
    desktop = uuid.UUID("11111111-1111-1111-1111-111111111111")
    calls = []

    def forbidden(*args, **kwargs):
        raise AssertionError("camera must not query placement, restore, activate or move the window")

    gui = types.SimpleNamespace(
        IsWindow=lambda hwnd: hwnd in handles,
        GetWindowText=lambda hwnd: "Crusader Kings III",
        EnumWindows=lambda callback, context: [callback(hwnd, context) for hwnd in handles],
        GetClientRect=lambda hwnd: (calls.append(hwnd), client)[1],
        IsIconic=forbidden, GetWindowPlacement=forbidden, ShowWindow=forbidden,
        SetForegroundWindow=forbidden, MoveWindow=forbidden)
    process = types.SimpleNamespace(GetWindowThreadProcessId=lambda hwnd: (1, owner))

    class Key:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    registry = types.SimpleNamespace(HKEY_CURRENT_USER=0, OpenKey=lambda *args: Key(),
                                     QueryValueEx=lambda *args: (desktop.bytes_le, 0))
    virtual = types.SimpleNamespace(window_virtual_desktop=lambda hwnd: {
        "desktop_id": desktop_id or str(desktop)})
    for name, module in [("win32gui", gui), ("win32process", process), ("winreg", registry),
                         ("xar_autoplayer.bridge.windows_virtual_desktop", virtual)]:
        monkeypatch.setitem(sys.modules, name, module)
    return calls


def test_owned_minimized_window_uses_only_real_nonzero_client_viewport(monkeypatch):
    # No IsIconic/placement call is permitted: iconic state cannot reject an
    # otherwise owned HWND or supply guessed viewport dimensions.
    calls = window_fixture(monkeypatch)
    client, shared = client_fixture()
    queued = client.submit({"mode": "hotspot", "title_key": "b_bari"},
                           payload()["source_frame"], payload()["source_build"])
    assert queued["status"] == "queued_native_presentation"
    assert queued["camera_postcondition_verified"] is False
    assert shared.request.hwnd == 4242 and shared.request.mode == 2
    assert calls == [4242]


@pytest.mark.parametrize("client", [(0, 0, 0, 1080), (0, 0, 1920, 0), (0, 0, -1, 1080)])
def test_zero_or_invalid_actual_client_viewport_rejects(monkeypatch, client):
    window_fixture(monkeypatch, client=client)
    with pytest.raises(ValueError, match="nonzero"):
        desktop1_game_window(123)


def test_cached_window_does_not_bypass_uniqueness_or_owner_checks(monkeypatch):
    window_fixture(monkeypatch, handles=(4242, 4243))
    with pytest.raises(ValueError, match="unique owned"):
        desktop1_game_window(123, 4242)
    window_fixture(monkeypatch, owner=999)
    with pytest.raises(ValueError, match="unique owned"):
        desktop1_game_window(123, 4242)


def test_owned_window_on_other_desktop_still_rejects(monkeypatch):
    window_fixture(monkeypatch, desktop_id="22222222-2222-2222-2222-222222222222")
    with pytest.raises(ValueError, match="outside Desktop 1"):
        desktop1_game_window(123)


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


def test_native_diagnostic_statuses_decode_as_failures_and_preserve_legacy_wire():
    from xar_autoplayer.bridge.auto_camera_follow import camera_receipt_outcome

    expected = (
        "window_unavailable", "camera_resolve_unavailable",
        "camera_target_write_blocked_or_unreadable",
        "camera_transient_x_active_or_unreadable",
        "camera_transient_z_active_or_unreadable",
        "camera_viewport_extent_unavailable", "camera_bucket_table_unavailable",
        "camera_bucket_read_or_match_unavailable", "camera_zoom_index_unavailable",
        "camera_zoom_or_target_state_unavailable", "camera_angle_state_unavailable",
        "camera_canonical_target_unavailable", "camera_target_write_or_readback_unavailable",
    )
    client, shared = client_fixture()
    shared.result.request_sequence = 2
    shared.result.zoom_index = 4
    for code, name in enumerate(expected, 16):
        shared.result_sequence += 2
        shared.result.status = code
        actual = client.latest()
        assert actual["status"] == name
        assert actual["camera_postcondition_verified"] is False
        assert camera_receipt_outcome({"native_actual": actual})[:2] == ("failed", False)
    # Existing Native26 settled receipts remain compatible with the same layout.
    shared.result_sequence += 2
    shared.result.status = 2
    actual = client.latest()
    assert actual["status"] == "settled"
    assert camera_receipt_outcome({"native_actual": actual})[:2] == ("completed", True)
    shared.result_sequence += 2
    shared.result.status = 9  # Reserved values are not promoted to known failures/success.
    with pytest.raises(ValueError, match="malformed native presentation receipt"):
        client.latest()


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
    assert client.intents == [{"mode": "realm", "reason": "no_hotspot_realm_overview",
                               "quiet_days_observed": 30.0}]
    assert result["display_mode"] == "realm"
    assert result["same_frame_with_gameplay_claim"] is False
    service._auto_camera_worker.close_without_wait()


def test_service_wartime_static_anchor_falls_back_and_battle_preempts_without_driver():
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex

    class ForbiddenDriver:
        def take_snapshot(self, **_):
            raise AssertionError("camera requested another gameplay snapshot")

    class Client:
        pid = 123
        def __init__(self):
            self.intents = []
        def latest(self):
            return None
        def submit(self, intent, frame, source):
            self.intents.append(dict(intent))
            return {"status": "queued_native_presentation", "request_sequence": len(self.intents) * 2}

    service = GameplayBridgeService(ForbiddenDriver())
    service.bind_war_hotspot_camera_index(LandedProvinceIndex({4242: "b_bari"}, {4242: "c_bari"}, ()))
    client = Client()
    service._camera_presentation_client = client
    try:
        static = {"war_id": 1, "war_objective_province_ids": [4242]}
        service._select_auto_camera_hotspot(payload(0, active_wars=[static]))
        realm = service._select_auto_camera_hotspot(payload(30, active_wars=[static]))
        battle = {**static, "allied_armies": [{"army_id": 7, "current_province_id": 4242,
                                             "in_combat": True, "controllable": True}]}
        hotspot = service._select_auto_camera_hotspot(payload(31, active_wars=[battle]))
        assert [intent["mode"] for intent in client.intents] == ["realm", "hotspot"]
        assert hotspot["hotspot"]["reason"] == "battle"
        assert hotspot["hotspot"]["title_key"] == "b_bari"
        assert realm["available"] is False and hotspot["available"] is False
        assert realm["same_frame_with_gameplay_claim"] is False
    finally:
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
