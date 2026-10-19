"""Wire trust boundaries and the actual adopted Python serialization path.

No files are patched and no Native/Game/OS mapping is opened. Native C++ fixture
qualification is separate; Python success is not Native/Game qualification.
"""
from __future__ import annotations
import ctypes
import json
import math
from pathlib import Path
import sys
import threading
import types

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
from xar_autoplayer.bridge.camera_settle_diagnostics_v1 import (
    CameraSettleDiagnosticsV1 as Wire, DIAGNOSTICS_BYTES, DIAGNOSTICS_MAGIC,
    DIAGNOSTICS_OFFSET, MAPPING_BYTES, MAPPING_MAGIC,
    decode_camera_settle_diagnostics_v1 as decode,
)

REALM = "ck3_autonomous_player/src/xar_autoplayer/bridge/realm_overview_camera.py"
WORKER = "ck3_autonomous_player/src/xar_autoplayer/bridge/auto_camera_follow.py"
EXPECTED = [1884., 0., 2362., 100., 1., 0.]


def fixture(reason=4):
    d = Wire()
    d.magic, d.version, d.byte_size = DIAGNOSTICS_MAGIC, 1, DIAGNOSTICS_BYTES
    d.request_sequence, d.legacy_status, d.reason = 50, 7, reason
    d.provider_pid, d.actor = 15512, 40526
    d.request_date_raw, d.submit_date_raw = 53197944, 53197968
    d.request_mode, d.county_count = 1, 9
    d.client_width, d.client_height, d.zoom_index = 1920, 1080, 15
    d.bounds[:] = [1787, 2214, 1982, 2510]
    d.expected_target[:] = EXPECTED
    d.observed_current[:] = EXPECTED
    d.observed_target[:] = EXPECTED
    d.observation_flags, d.target_difference_mask = 15, 4
    d.observed_target[2] += 1
    d.observation_uptime_ms = 90000
    result = {"status": "target_changed", "request_sequence": 50,
        "actor_character_id": 40526, "date_raw": 53197968, "county_count": 9,
        "client_size": [1920, 1080], "zoom_index": 15,
        "bounds": [1787, 2214, 1982, 2510], "target": EXPECTED.copy()}
    binding = {"request_sequence": 50, "source_frame": {
        "actor_character_id": 40526, "date_raw": 53197944, "bridge_pid": 15512,
        "episode_run_id": "native-40526-test", "connection_generation": 2}}
    return d, result, binding


def decoded(d, result, binding, **extra):
    args = dict(result=result, mapping_identity=(MAPPING_MAGIC, 1, 15512),
                result_region_end=65832, request_binding=binding)
    args.update(extra)
    return decode(bytes(d), **args)


def actual_module(path, name):
    """Load current adopted source into an isolated module; no patch replay."""
    module = types.ModuleType(name)
    module.__package__ = "xar_autoplayer.bridge"
    module.__file__ = str(ROOT / path)
    sys.modules[name] = module
    source = (ROOT / path).read_text(encoding="utf-8")
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def fake_client(module, d=None, result=None, binding=None):
    memory = (ctypes.c_ubyte * MAPPING_BYTES)()
    shared = module._Shared.from_buffer(memory)
    shared.magic, shared.version, shared.pid, shared.result_sequence = MAPPING_MAGIC, 1, 15512, 2
    client = object.__new__(module.NativeCameraPresentationClient)
    client.pid, client._handle, client._hwnd = 15512, None, None
    client._view, client._lock = ctypes.addressof(memory), threading.Lock()
    client._last_result_sequence, client._latest = -1, None
    client._diagnostic_request_binding = binding
    client._tracking_binding = None
    if d is not None:
        r = shared.result
        r.status, r.request_sequence, r.actor, r.date_raw = 7, 50, d.actor, d.submit_date_raw
        r.county_count, r.client_width, r.client_height = 9, 1920, 1080
        r.zoom_index, r.bounds[:], r.target[:] = 15, result["bounds"], EXPECTED
        ctypes.memmove(client._view + DIAGNOSTICS_OFFSET, bytes(d), DIAGNOSTICS_BYTES)
    return client, shared, memory


def test_tail_layout_and_legacy_nonoverlap():
    realm = actual_module(REALM, "xar_autoplayer.bridge._camdiag_layout_fixture")
    assert ctypes.sizeof(Wire) == 168
    assert Wire.observation_uptime_ms.offset == 160
    assert realm._Shared.request.offset == 24
    assert ctypes.sizeof(realm._Request) == 168
    assert ctypes.sizeof(realm._Result) == 65640
    assert realm._Shared.result.offset == 192
    assert ctypes.sizeof(realm._Shared) == 65832
    assert realm._Shared.result.offset + ctypes.sizeof(realm._Result) <= DIAGNOSTICS_OFFSET
    assert DIAGNOSTICS_OFFSET + DIAGNOSTICS_BYTES <= MAPPING_BYTES


@pytest.mark.parametrize("reason,flags", [(1, 0), (2, 5), (3, 11), (4, 15)])
def test_four_reasons_preserve_unread_missing_and_nonfinite(reason, flags):
    d, result, binding = fixture(reason)
    d.observation_flags = flags
    if reason != 4: d.target_difference_mask = 0
    if reason == 3: d.observed_current[0] = math.nan
    actual = decoded(d, result, binding)
    assert actual["available"]
    assert actual["current_read_success"] == bool(flags & 1)
    assert actual["target_read_success"] == bool(flags & 2)
    if not flags & 1:
        assert actual["observed_current"] is None
        assert actual["observed_current_float_bits"] is None
        assert actual["current_finite"] is None
    if not flags & 2:
        assert actual["observed_target"] is None
        assert actual["observed_target_float_bits"] is None
    if reason == 3:
        assert actual["observed_current"][0] is None
        assert actual["observed_current_float_bits"][0] != 0
    assert actual["observation_game_frame"] is None
    assert actual["provider"]["native_epoch"] is None
    assert actual["request_source_frame"]["connection_generation"] == 2
    json.dumps(actual, allow_nan=False)


@pytest.mark.parametrize("field,value", [
    ("request_sequence", 48), ("actor", 31254), ("provider_pid", 123),
    ("submit_date_raw", 53197969), ("zoom_index", 14),
    ("version", 2), ("byte_size", 172), ("reserved", 1),
    ("observation_flags", 31), ("target_difference_mask", 1)])
def test_wrong_identity_geometry_layout_and_difference_fail_closed(field, value):
    d, result, binding = fixture()
    setattr(d, field, value)
    assert not decoded(d, result, binding)["available"]


def test_old_5873_without_extension_remains_unknown():
    d, result, binding = fixture()
    d.magic = 0
    assert decoded(d, result, binding)["reason"] == "legacy_or_absent_extension"
    assert not decoded(d, result, None)["available"]
    d.magic = DIAGNOSTICS_MAGIC
    assert decoded(d, result, None)["reason"] == "request_context_not_observed"
    binding["source_frame"]["connection_generation"] = None
    assert not decoded(d, result, binding)["available"]


def test_future_mapping_layout_and_nonoverlap_fail_closed():
    d, result, binding = fixture()
    for identity in [(MAPPING_MAGIC, 2, 15512), (0, 1, 15512), None]:
        assert not decoded(d, result, binding, mapping_identity=identity)["available"]
    assert not decoded(d, result, binding, result_region_end=DIAGNOSTICS_OFFSET + 1)["available"]
    assert not decoded(d, result, binding, result_region_end=65840)["available"]


def test_current_interpolation_without_target_change_not_a_failure():
    d, result, binding = fixture()
    d.observed_target[:] = EXPECTED
    d.observed_current[0] -= 50
    d.target_difference_mask = 0
    assert decoded(d, result, binding)["reason"] == "failure_reason_or_difference_mismatch"


def test_actual_candidate_latest_and_compact_reference_keep_same_diagnostic():
    realm = actual_module(REALM, "xar_autoplayer.bridge._camdiag_latest_fixture")
    worker = actual_module(WORKER, "xar_autoplayer.bridge._camdiag_worker_fixture")
    d, result, binding = fixture()
    client, shared, memory = fake_client(realm, d, result, binding)
    latest = client.latest()
    diag = latest["settle_diagnostics"]
    assert diag["available"] and diag["request_sequence"] == 50
    assert diag["reason"] == "target_changed" and diag["observed_target"][2] == 2363
    assert latest["camera_postcondition_verified"] is False
    summary = worker.LatestCameraFollowWorker._reference({
        "request_id": "future50", "status": "failed", "receipt": {"native_actual": latest}})
    assert summary["receipt"]["native_actual"]["settle_diagnostics"] == diag
    assert worker.camera_receipt_outcome({"native_actual": latest})[:2] == ("failed", False)
    shared.result.request_sequence = 52
    shared.result_sequence = 4
    stale = client.latest()
    assert not stale["settle_diagnostics"]["available"]
    assert stale["settle_diagnostics"]["reason"] == "result_binding_mismatch"


def test_torn_publication_never_accepts_mixed_tail():
    realm = actual_module(REALM, "xar_autoplayer.bridge._camdiag_torn_fixture")
    d, result, binding = fixture()
    client, shared, memory = fake_client(realm, d, result, binding)
    previous = {"request_sequence": 48, "settle_diagnostics": {"available": False}}
    client._latest = previous
    sequence = iter((2, 4))
    client._sequence = lambda name: next(sequence)
    assert client.latest() is previous


def test_candidate_submit_records_only_one_actual_request_context_without_query(monkeypatch):
    realm = actual_module(REALM, "xar_autoplayer.bridge._camdiag_submit_fixture")
    client, shared, memory = fake_client(realm)
    client._open = lambda: None
    class Kernel:
        def GetTickCount64(self): return 90000
        def FlushProcessWriteBuffers(self): pass
    client._kernel = Kernel()
    monkeypatch.setattr(realm, "desktop1_game_window", lambda pid, cached: 4242)
    _, _, binding = fixture()
    frame = binding["source_frame"]
    queued = client.submit({"mode": "realm"}, frame,
        {"game_version": "1.20.0.4", "executable_sha256": realm.EXACT_SHA})
    assert queued["request_sequence"] == 2 and shared.request_sequence == 2
    assert client._diagnostic_request_binding == {"request_sequence": 2, "source_frame": frame}
    frame["connection_generation"] = 999
    assert client._diagnostic_request_binding["source_frame"]["connection_generation"] == 2

