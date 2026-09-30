"""Focused new-admission checks; never create a CK3 or desktop session."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from xar_autoplayer import h3937_cold_observer_once_enable as once
from xar_autoplayer import h3937_combined_once_enable as old_once


def check(value: bool) -> None:
    if not value:
        raise AssertionError("test condition failed")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_new_entry_is_isolated_and_outer_observer_stays_default_off() -> None:
    from inspect import signature

    check(old_once.ROUND == "R3945")
    check(old_once.NO_LAUNCH != once.NO_LAUNCH)
    check(old_once.OUTPUT != once.OUTPUT)
    check(old_once.GO != once.GO)
    check(old_once.SCREEN_TASK_ID != once.SCREEN_TASK_ID)
    check(once.ROUND == "R3948")
    check(once.LIVE_RUN_ID.endswith("--vanilla--R0117"))
    check(once.outer.COMBINED_DLL_SHA256 ==
          "3438E8725AA06839CA1F2DFAF6D6CC98D41A4F33C02AC0702AC8D48AD241531B")
    check(once.outer.COMBINED_INJECTOR_SHA256 ==
          "ECBC1B3B24E8A9BF1F85E9CBE195E4A5B8D3E928DB0FC8124ABF4D6D95A4B0D3")
    check(once.PIPE == old_once.PIPE)  # Exact raw driver-state contract.
    check(signature(once.outer.collect_h3937_combined_paused_war_scope_once)
          .parameters["cold_load_observation_dir"].default is None)
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)


def test_worker_completion_stdout_survives_legacy_gbk_console(monkeypatch) -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="gbk", errors="strict")
    monkeypatch.setattr(once, "run_exact_once", lambda nonce: {
        "status": "RED", "error": "unencodable \U0001f9ea diagnostic"})
    monkeypatch.setattr(sys, "stdout", stream)
    check(once.main("nonce") == 1)
    stream.flush()
    check(b"\\ud83e\\uddea" in raw.getvalue())


def test_wrong_interpreter_refuses_before_admission_or_go(
    monkeypatch, tmp_path,
) -> None:
    monkeypatch.setattr(once, "FROZEN_PYTHON", tmp_path / "wrong-python.exe")
    monkeypatch.setattr(once, "NO_LAUNCH", tmp_path / "missing-no-launch")
    monkeypatch.setattr(once, "GO", tmp_path / "go.json")
    with pytest.raises(ValueError, match="interpreter"):
        once._require_exact_admission()
    check(not once.NO_LAUNCH.exists())
    check(not once.GO.exists())


def test_exact_no_launch_requires_allocator_identity_and_16_source_blobs(
    monkeypatch, tmp_path,
) -> None:
    root = tmp_path / "no-launch"
    state = root / "state"
    verified = root / "source-verified"
    dll = verified / "xar_ck3_bridge.dll"
    injector = verified / "xar_ck3_bridge_injector.exe"
    save = state / "profile" / "save games" / "xar_checkpoint.ck3"
    sidecar = state / "player-child-matrilineal-formal-v1.json"
    driver = state / "native-session" / "driver-state.json"
    rebind = state / "ordinary-seed-rebind-v1.json"
    preflight = state / "preflights" / "report.json"
    game = tmp_path / "game"
    game_exe = game / "binaries" / "ck3.exe"
    for path, data in (
        (dll, b"dll"), (injector, b"injector"),
        (save, b"save"), (sidecar, b"sidecar"), (driver, b"driver"),
        (verified / "driver-state.json", b"raw driver"),
        (verified / "xar_checkpoint.ck3", b"save"),
        (verified / "player-child-matrilineal-formal-v1.json", b"sidecar"),
        (game_exe, b"game"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    lifecycle = {"lifecycle": "ordinary_campaign_succession",
                 "xar_enabled": "xar_off",
                 "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                 "environment_sha256": "E" * 64}
    preflight.parent.mkdir(parents=True, exist_ok=True)
    preflight.write_text(json.dumps({
        "status": "ready", "ok": True, "ck3_launch_attempted": False,
        "desktop_interaction": False, "process_inventory": {"processes": []},
        "profile": {"environment_sha256": "E" * 64,
                    "ck3_executable_sha256": sha(game_exe)},
        "resume_anchor": {
            "checkpoint": {"saved_date_raw": 53219928, "history_index": 3937,
                           "succession_lifecycle": lifecycle},
            "driver_state": {"episode_character_id": 29829,
                             "episode_run_id": "native-29829-2bc2d599f7f9",
                             "succession_lifecycle": lifecycle},
        },
    }), encoding="utf-8")
    rebind.write_text(json.dumps({
        "ok": True, "status": "rebound", "ck3_launch_attempted": False,
        "desktop_interaction": False, "pipe_name": once.PIPE,
        "state_dir": str(state), "environment": {"target_sha256": "E" * 64},
        "driver_state": {"target_sha256": sha(driver)},
    }), encoding="utf-8")
    live_identity_path = root / "live-run-identity.json"
    live_identity = {"schema": "xar.ck3-live-run-identity.v1",
                     "run_id": once.LIVE_RUN_ID,
                     "execution_id": once.LIVE_EXECUTION_ID,
                     "machine_id": "desktop-3fevhd2-1c74096080",
                      "mod_key": "vanilla", "sequence": 117}
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    head = "a" * 40
    admission = {
        "schema": "xar.war.h3937-cold-observer-disabled-no-launch-admission.v1",
        "candidate_head": head, "candidate_checkout_clean": True,
        "task_bus_cli_sha256": once.BUS_CLI_SHA256,
        "live_run_id": once.LIVE_RUN_ID,
        "live_run_identity_sha256": sha(live_identity_path),
        "cold_load_observer_default_off": True,
        "cold_load_observer_live_enabled": False,
        "prepared_state": str(state),
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "actor": 29829, "date_raw": 53219928, "history_index": 3937,
        "raw_driver_sha256": "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722",
        "prepared_driver_sha256": sha(driver),
        "official_rebind_receipt_sha256": sha(rebind),
        "official_preflight_report": str(preflight),
        "official_preflight_report_sha256": sha(preflight),
        "environment_sha256": "E" * 64,
        "dll_sha256": sha(dll), "injector_sha256": sha(injector),
        "combined_outer_hard_gate": False, "combined_inner_hard_gate": False,
        "target_inner_hard_gate": False,
        "ck3_launch_attempted": False, "live_authorized": False,
    }
    blobs = {f"source_{i}": "b" * 40 for i in range(15)}
    blobs["source_module_.h3937_cold_load_observer"] = "b" * 40
    manifest = {
        "candidate_head": head, "candidate_clean": True,
        "task_bus_cli_sha256": once.BUS_CLI_SHA256,
        "python": sys.executable,
        "python_version": (
            f"Python {sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        ),
        "live_run_id": once.LIVE_RUN_ID,
        "live_run_identity_sha256": sha(live_identity_path),
        "cold_load_observer_default_off": True,
        "cold_load_observer_live_enabled": False,
        "state_dir": str(state), "bridge_pipe": once.PIPE,
        "bridge_dll": str(dll), "bridge_injector": str(injector),
        "game_dir": str(game),
        "outer_hard_gate": False, "inner_hard_gate": False,
        "target_hard_gate": False, "ck3_launch_attempted": False,
        "live_output_created": False,
        "bridge_dll_sha256": sha(dll), "bridge_injector_sha256": sha(injector),
        "source_raw_driver_sha256": admission["raw_driver_sha256"],
        "source_checkpoint_sha256": "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6",
        "source_child_sidecar_sha256": "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7",
        "prepared_driver_sha256": admission["prepared_driver_sha256"],
        "rebind_receipt_sha256": admission["official_rebind_receipt_sha256"],
        "preflight_report_sha256": admission["official_preflight_report_sha256"],
        "environment_sha256": admission["environment_sha256"],
        "source_git_blobs": blobs,
    }
    admission_path = root / "admission.json"
    manifest_path = root / "operator-manifest.json"
    admission_path.write_text(json.dumps(admission), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    for key, value in {"NO_LAUNCH": root, "STATE": state, "DLL": dll,
                       "INJECTOR": injector, "GAME": game,
                       "LIVE_IDENTITY": live_identity_path,
                       "FROZEN_PYTHON": Path(sys.executable),
                       "FROZEN_PYTHON_VERSION": manifest["python_version"]}.items():
        monkeypatch.setattr(once, key, value)
    monkeypatch.setattr(once.outer, "COMBINED_DLL_SHA256", sha(dll))
    monkeypatch.setattr(once.outer, "COMBINED_INJECTOR_SHA256", sha(injector))

    def fake_git(*args):
        if args[0] == "status":
            return ""
        if args == ("rev-parse", "HEAD"):
            return head
        return "b" * 40

    monkeypatch.setattr(once, "_git", fake_git)
    monkeypatch.setattr(once, "_require_bus_cli_pair", lambda: tmp_path / "bus-cli.py")
    original_sha = once._sha

    def synthetic_source_sha(path):
        if path in (save, verified / "xar_checkpoint.ck3"):
            return manifest["source_checkpoint_sha256"]
        if path in (sidecar, verified / "player-child-matrilineal-formal-v1.json"):
            return manifest["source_child_sidecar_sha256"]
        if path == verified / "driver-state.json":
            return manifest["source_raw_driver_sha256"]
        return original_sha(path)

    monkeypatch.setattr(once, "_sha", synthetic_source_sha)
    expected_blobs = blobs.copy()
    monkeypatch.setattr(once, "_source_blob_identity",
                        lambda: (head, expected_blobs))
    bound = once._require_exact_admission()
    check(bound["live_run_identity_sha256"] == sha(live_identity_path))
    once._require_no_launch_unchanged(bound)
    manifest["task_bus_cli_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["task_bus_cli_sha256"] = once.BUS_CLI_SHA256
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    live_identity["sequence"] = 114
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    live_identity["sequence"] = 116  # Historical a13 allocator must not enter a14.
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    live_identity["sequence"] = 117
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    for key, old_hash in (
        ("dll_sha256", "F5E708FC554C377420B3D31D9B38B4FB6DE2D3A3B19C7D298DAA3DB61233793F"),
        ("injector_sha256", "8E2115CBE43358DD6F47C12CC94A2E96BF8049DE70204E425B37B5CE825AFE5E"),
    ):
        current_hash = admission[key]
        admission[key] = old_hash
        admission_path.write_text(json.dumps(admission), encoding="utf-8")
        with pytest.raises(ValueError, match="identity mismatch"):
            once._require_exact_admission()
        admission[key] = current_hash
        admission_path.write_text(json.dumps(admission), encoding="utf-8")
    live_identity["execution_id"] = "wrong"
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    with pytest.raises(ValueError, match="identity bytes changed"):
        once._require_no_launch_unchanged(bound)
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    live_identity["execution_id"] = once.LIVE_EXECUTION_ID
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    manifest["source_git_blobs"].pop("source_module_.h3937_cold_load_observer")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["source_git_blobs"] = expected_blobs.copy()
    manifest["source_git_blobs"]["source_0"] = "c" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="source Git blobs differ"):
        once._require_exact_admission()
    manifest["source_git_blobs"] = expected_blobs.copy()
    manifest["source_git_blobs"].pop("source_0")
    manifest["source_git_blobs"]["source_fake"] = "b" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="source Git blobs differ"):
        once._require_exact_admission()
    manifest["source_git_blobs"] = expected_blobs.copy()
    manifest["source_git_blobs"].pop("source_0")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["source_git_blobs"] = expected_blobs.copy()
    manifest["source_git_blobs"]["source_fake"] = "b" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["source_git_blobs"] = expected_blobs.copy()
    manifest["python"] = str(tmp_path / "wrong-python.exe")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["python"] = sys.executable
    manifest["python_version"] = "Python 0.0.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    manifest["python_version"] = (
        f"Python {sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )
    manifest["cold_load_observer_default_off"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()


@pytest.mark.parametrize("available,error,allowed", [
    (False, 2, True),   # ERROR_FILE_NOT_FOUND is the only admissible absence.
    (True, 0, False),   # Server exists and has a free instance.
    (False, 231, False),  # ERROR_PIPE_BUSY: server exists.
    (False, 5, False),  # Access denied is unavailable, not absence.
])
def test_exact_pipe_absence_gate(monkeypatch, available, error, allowed) -> None:
    calls = []

    class FakeWait:
        argtypes = None
        restype = None

        def __call__(self, name, timeout):
            calls.append((name, timeout))
            return int(available)

    wait = FakeWait()
    monkeypatch.setattr(once.ctypes, "WinDLL", lambda *a, **k:
                        type("Kernel32", (), {"WaitNamedPipeW": wait})())
    monkeypatch.setattr(once.ctypes, "get_last_error", lambda: error)
    if allowed:
        once._require_pipe_server_absent()
    else:
        with pytest.raises(RuntimeError, match="pipe"):
            once._require_pipe_server_absent()
    check(calls == [(once.PIPE, 0)])


def _fresh_go(monkeypatch, tmp_path):
    state = tmp_path / "state"
    output = tmp_path / "attempt-14"
    screen = tmp_path / "screen-attempt-14"
    bus = tmp_path / "task-bus"
    for path in (state, screen, bus):
        path.mkdir()
    go_path = tmp_path / "go-attempt-14.json"
    monkeypatch.setattr(once, "STATE", state)
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "SCREEN", screen)
    monkeypatch.setattr(once, "GO", go_path)
    monkeypatch.setattr(once, "TASK_BUS", bus)
    now = datetime.now(timezone.utc)
    stamp = lambda seconds: (now + timedelta(seconds=seconds)).isoformat()
    owner = {"task_id": once.SCREEN_TASK_ID, "state": "running",
             "resources": ["ck3-screen:acquired"], "last_sequence": 2415,
             "updated_at_utc": stamp(-50)}
    monkeypatch.setattr(once, "_require_live_screen_lease",
                        lambda sequence=None: owner)
    lease = screen / "screen-lease-snapshot.json"
    lease.write_text(json.dumps(owner), encoding="utf-8")
    challenge = {"schema": "xar.war.h3937-cold-observer-screen-challenge.v1",
                 "issued_at_utc": stamp(-45), "challenge_nonce": "a" * 48,
                 "candidate_head": "a" * 40, "round": once.ROUND,
                 "live_run_id": once.LIVE_RUN_ID,
                 "screen_attempt_dir": str(screen.resolve()),
                 "task_bus_dir": str(bus.resolve()),
                 "screen_task_id": once.SCREEN_TASK_ID,
                 "screen_task_last_sequence": owner["last_sequence"]}
    challenge_path = screen / "screen-challenge.json"
    challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
    steam = screen / "steam-moved.png"
    steam.write_bytes(b"fresh-window-movement")
    before = screen / "steam-before.png"
    before.write_bytes(b"first-window-position")
    frame = {"schema": "ck3.steam_fresh_desktop_frame.v1",
             "captured_at_utc": stamp(-35), "moving_edge_changed": True,
             "pixel_difference_bbox": [1, 2, 20, 30],
             "before_path": str(before), "before_sha256": sha(before),
             "before_rect": [0, 0, 100, 100],
             "moved_rect": [20, 0, 120, 100],
             "restored_rect": [0, 0, 100, 100], "clock_check": None,
             "moved_path": str(steam), "moved_sha256": sha(steam),
             "moved_identity": {"path": str(steam), "bytes": steam.stat().st_size,
                                "sha256": sha(steam)}}
    frame_path = screen / "steam-frame-freshness.json"
    frame_path.write_text(json.dumps(frame), encoding="utf-8")
    identity = {"head": "a" * 40, "admission_sha256": "A" * 64,
                 "manifest_sha256": "B" * 64, "preflight_sha256": "C" * 64,
                 "rebind_sha256": "D" * 64,
                 "live_run_identity_sha256": "E" * 64}
    review_path = screen / "steam-offline-direct-review.json"
    review = {
        "schema": "xar.war.h3937-a14-steam-offline-direct-review.v1",
        "candidate_head": identity["head"], "round": once.ROUND,
        "live_run_id": once.LIVE_RUN_ID,
        "screen_task_id": once.SCREEN_TASK_ID,
        "screen_challenge_nonce": challenge["challenge_nonce"],
        "reviewer": "operator",
        "steam_offline_direct_reviewed": True,
        "offline_indicator_text": "离线模式",
        "reviewed_at_utc": stamp(-25),
        "original_image": str(steam), "original_sha256": sha(steam),
        "freshness_receipt": str(frame_path),
        "freshness_receipt_sha256": sha(frame_path),
        "screen_challenge_sha256": sha(challenge_path),
        "screen_lease_snapshot_sha256": sha(lease),
    }
    review_path.write_text(json.dumps(review), encoding="utf-8")
    go = {"schema": "xar.war.h3937-cold-observer-once-go.v1",
          "decision": "GO_READ_ONLY_H3937_COMBINED",
          "candidate_head": identity["head"], "round": once.ROUND,
          "live_run_id": once.LIVE_RUN_ID,
          "live_run_identity_sha256": identity["live_run_identity_sha256"],
          "cold_load_observer_enabled": True,
          "cold_load_observer_dir": str((output / "cold-load-observation").resolve()),
          "state_dir": str(state), "output_dir": str(output), "pipe": once.PIPE,
          "admission_sha256": identity["admission_sha256"],
          "operator_manifest_sha256": identity["manifest_sha256"],
          "preflight_sha256": identity["preflight_sha256"],
          "rebind_sha256": identity["rebind_sha256"],
          "task_bus_dir": str(bus.resolve()),
          "screen_task_id": once.SCREEN_TASK_ID,
          "screen_task_last_sequence": owner["last_sequence"],
          "screen_attempt_dir": str(screen.resolve()),
          "screen_lease_exclusive": True,
          "steam_offline_direct_visual_reviewed": True,
          "account_single_instance_clear": True,
          "ck3_zero_process_before": True, "recorder_zero_before": True,
          "authorized_scope": "six_paused_readonly_queries",
          "maximum_query_actions": 6,
          "issued_at_utc": stamp(-15), "steam_direct_reviewed_at_utc": stamp(-25),
          "screen_challenge_nonce": challenge["challenge_nonce"],
          "steam_original_path": str(steam), "steam_original_sha256": sha(steam),
          "steam_frame_receipt_path": str(frame_path),
          "steam_frame_receipt_sha256": sha(frame_path),
          "screen_challenge_path": str(challenge_path),
          "screen_challenge_sha256": sha(challenge_path),
           "screen_lease_receipt_path": str(lease),
           "screen_lease_receipt_sha256": sha(lease),
           "operator_direct_review_evidence": {
               "review_receipt_path": str(review_path),
               "review_receipt_sha256": sha(review_path),
               "latest_original_sha256": sha(steam),
           }}
    go_path.write_text(json.dumps(go), encoding="utf-8")
    return identity, go, challenge, challenge_path


@pytest.mark.parametrize("field,value", [
    ("live_run_id", "desktop-wrong--vanilla--R0117"),
    ("live_run_identity_sha256", "F" * 64),
    ("cold_load_observer_enabled", False),
    ("cold_load_observer_dir", "D:/wrong-observer-output"),
    ("maximum_query_actions", 7),
    ("round", "R3945"),
    ("schema", "xar.war.h3937-combined-once-go.v1"),
])
def test_go_requires_new_run_observer_and_six_read_scope(
    monkeypatch, tmp_path, field, value,
) -> None:
    identity, go, _, _ = _fresh_go(monkeypatch, tmp_path)
    check(once._require_go(identity)[0] == go)
    go[field] = value
    once.GO.write_text(json.dumps(go), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)


def test_go_rejects_old_challenge_run_id(monkeypatch, tmp_path) -> None:
    identity, go, challenge, challenge_path = _fresh_go(monkeypatch, tmp_path)
    challenge["live_run_id"] = "desktop-wrong--vanilla--R0117"
    challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
    go["screen_challenge_sha256"] = sha(challenge_path)
    once.GO.write_text(json.dumps(go), encoding="utf-8")
    with pytest.raises(ValueError, match="screen challenge"):
        once._require_go(identity)


@pytest.mark.parametrize("mutation", [
    "missing_binding", "wrong_receipt_sha", "wrong_receipt_path",
    "wrong_offline_text", "wrong_reviewer", "wrong_review_time",
    "wrong_image_hash",
])
def test_go_requires_exact_direct_visual_review_receipt(
    monkeypatch, tmp_path, mutation,
) -> None:
    identity, go, _, _ = _fresh_go(monkeypatch, tmp_path)
    review_path = once.SCREEN / "steam-offline-direct-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if mutation == "missing_binding":
        go.pop("operator_direct_review_evidence")
    elif mutation == "wrong_receipt_sha":
        go["operator_direct_review_evidence"]["review_receipt_sha256"] = "F" * 64
    elif mutation == "wrong_receipt_path":
        go["operator_direct_review_evidence"]["review_receipt_path"] = str(
            tmp_path / "outside-review.json")
    else:
        field, value = {
            "wrong_offline_text": ("offline_indicator_text", "在线模式"),
            "wrong_reviewer": ("reviewer", " "),
            "wrong_review_time": ("reviewed_at_utc", "2020-01-01T00:00:00+00:00"),
            "wrong_image_hash": ("original_sha256", "0" * 64),
        }[mutation]
        review[field] = value
        review_path.write_text(json.dumps(review), encoding="utf-8")
        go["operator_direct_review_evidence"]["review_receipt_sha256"] = sha(
            review_path)
    once.GO.write_text(json.dumps(go), encoding="utf-8")
    with pytest.raises(ValueError, match="direct Steam review"):
        once._require_go(identity)


@pytest.mark.parametrize("mutate_review", [False, True])
def test_worker_passes_explicit_observer_and_keeps_gameplay_off(
    monkeypatch, tmp_path, mutate_review,
) -> None:
    output = tmp_path / "attempt-14"
    output.mkdir()
    (output / "supervisor-claim.json").write_text(json.dumps({
        "schema": "xar.war.h3937-cold-observer-supervisor-claim.v1",
        "claim_nonce": "nonce", "round": once.ROUND,
        "live_run_id": once.LIVE_RUN_ID,
        "output_dir": str(output), "head": "pinned",
    }), encoding="utf-8")
    go = tmp_path / "go.json"
    go.write_text("{}", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text("original review", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "GO", go)
    monkeypatch.setattr(once, "_git", lambda *args: "pinned")
    monkeypatch.setattr(once, "_require_exact_admission", lambda: {"head": "pinned"})
    monkeypatch.setattr(once, "_require_no_launch_unchanged", lambda identity: None)
    monkeypatch.setattr(once, "_require_go", lambda identity: ({
        "screen_task_last_sequence": 1,
        **{f"{name}_path": str(go) for name in (
            "steam_original", "steam_frame_receipt", "screen_challenge",
            "screen_lease_receipt")},
        **{f"{name}_sha256": sha(go) for name in (
            "steam_original", "steam_frame_receipt", "screen_challenge",
            "screen_lease_receipt")},
        "operator_direct_review_evidence": {
            "review_receipt_path": str(review),
            "review_receipt_sha256": sha(review),
        },
    }, sha(go)))
    monkeypatch.setattr(once, "_require_live_screen_lease", lambda sequence=None: {})
    monkeypatch.setattr(once, "_image_inventory", lambda image: {
        "returncode": 0, "found": False})
    monkeypatch.setattr(once, "_require_pipe_server_absent", lambda: None)
    calls = []

    def collect(*args, **kwargs):
        check(kwargs["cold_load_observation_dir"] == output / "cold-load-observation")
        check(kwargs["readiness_timeout_seconds"] == 1800)
        check(kwargs["timeout_seconds"] == 1890)
        check(kwargs["readiness_stall_watchdog"] is True)
        check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is True)
        check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is True)
        check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is True)
        calls.append(1)
        if mutate_review:
            review.write_text("changed review", encoding="utf-8")
        return {"ok": True, "status": "GREEN_READ_ONLY_TARGET",
                "action_authorized": False, "date_advance_authorized": False,
                "gameplay_actions": 0, "query_actions": 6,
                "cleanup": {"ok": True}}

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once",
                        collect)
    result = once.run_exact_once("nonce")
    check(result["status"] == ("RED" if mutate_review else "GREEN_READ_ONLY"))
    if mutate_review:
        check(result["error"] == "direct Steam review bytes changed")
    check(calls == [1])
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)


def test_preworker_pipe_collision_rejects_before_worker(monkeypatch, tmp_path) -> None:
    entry = tmp_path / "entry.py"
    output = tmp_path / "attempt-14"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": "pinned", "entry_blob": "blob", "entry_sha256": "A" * 64})
    monkeypatch.setattr(once, "_require_preworker_screen_gate",
                        lambda entry: once._require_pipe_server_absent())
    monkeypatch.setattr(once, "_require_pipe_server_absent",
                        lambda: (_ for _ in ()).throw(RuntimeError("pipe busy")))
    monkeypatch.setattr(once.subprocess, "Popen",
                        lambda *a, **k: check(False))
    monkeypatch.setattr(once, "_image_inventory", lambda image: {
        "returncode": 0, "found": False})
    check(once.supervise_exact_once(entry) == 1)
    receipt = json.loads((output / "supervisor-completion.json").read_text())
    check(receipt["status"] == "RED")
    check(receipt["worker_started"] is False)
    check(receipt["processes_gone"] is False)
    check("pipe busy" in str(receipt["error"]))


def test_preworker_wrong_interpreter_rejects_without_worker(
    monkeypatch, tmp_path,
) -> None:
    entry = tmp_path / "entry.py"
    output = tmp_path / "attempt-14"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "FROZEN_PYTHON", tmp_path / "wrong-python.exe")
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": "pinned", "entry_blob": "blob", "entry_sha256": "A" * 64})
    monkeypatch.setattr(once.subprocess, "Popen",
                        lambda *a, **k: check(False))
    monkeypatch.setattr(once, "_image_inventory", lambda image: {
        "returncode": 0, "found": False})
    check(once.supervise_exact_once(entry) == 1)
    receipt = json.loads((output / "supervisor-completion.json").read_text())
    check(receipt["status"] == "RED")
    check(receipt["worker_started"] is False)
    check("interpreter" in str(receipt["error"]))


def test_preworker_process_collision_rejects_without_worker(
    monkeypatch, tmp_path,
) -> None:
    output = tmp_path / "attempt-14"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": "pinned", "entry_blob": "blob", "entry_sha256": "A" * 64})
    monkeypatch.setattr(once, "_require_exact_admission", lambda: {"head": "pinned"})
    monkeypatch.setattr(once, "_require_go", lambda identity: ({}, "B" * 64))
    monkeypatch.setattr(once, "_require_pipe_server_absent",
                        lambda: check(False))
    monkeypatch.setattr(once, "_image_inventory", lambda image: {
        "returncode": 0, "found": image == "ck3.exe"})
    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: check(False))
    check(once.supervise_exact_once(tmp_path / "entry.py") == 1)
    receipt = json.loads((output / "supervisor-completion.json").read_text())
    check(receipt["status"] == "RED")
    check(receipt["worker_started"] is False)
    check(receipt["worker_pid"] is None)
    check("process inventory" in str(receipt["error"]))
    check(not (output / "worker-started.json").exists())


def test_heartbeat_failure_kills_and_reaps_worker_with_tail_stdio(
    monkeypatch, tmp_path,
) -> None:
    output = tmp_path / "attempt-14"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": "pinned", "entry_blob": "blob", "entry_sha256": "A" * 64})
    monkeypatch.setattr(once, "_require_preworker_screen_gate", lambda entry: None)
    monkeypatch.setattr(once, "_managed_screen_heartbeat",
                         lambda: (_ for _ in ()).throw(RuntimeError("lease heartbeat lost")))
    monkeypatch.setattr(once, "_image_inventory", lambda image: {
        "returncode": 0, "found": False})

    class Worker:
        pid = 424242
        args = ["worker"]
        returncode = None
        calls = 0

        def communicate(self, timeout):
            self.calls += 1
            if self.calls == 1:
                raise once.subprocess.TimeoutExpired(self.args, timeout,
                                                     output=b"partial")
            check(self.returncode == 1)
            check(timeout == 30)
            return b"partial and tail out", b"tail err"

    worker = Worker()
    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: worker)

    def kill_run(*args, **kwargs):
        check(args[0][:3] == ["taskkill", "/PID", str(worker.pid)])
        worker.returncode = 1
        return type("Result", (), {"returncode": 0, "stdout": b"killed",
                                    "stderr": b""})()

    monkeypatch.setattr(once.subprocess, "run", kill_run)
    check(once.supervise_exact_once(tmp_path / "entry.py") == 1)
    receipt = json.loads((output / "supervisor-completion.json").read_text())
    check(receipt["status"] == "RED")
    check(receipt["worker_started"] is True)
    check(receipt["worker_returncode"] == 1)
    check(receipt["taskkill"]["returncode"] == 0)
    check("lease heartbeat lost" in str(receipt["error"]))
    check(worker.calls == 2)
    check((output / "supervisor.stdout.txt").read_text() == "partial and tail out")
    check((output / "supervisor.stderr.txt").read_text() == "tail err")


def test_cas_heartbeat_binds_exact_sequence_and_cli_pair(monkeypatch) -> None:
    owner = {"last_sequence": 10}
    observed = []
    def lease(expected_sequence=None):
        observed.append(expected_sequence)
        if expected_sequence is not None:
            check(expected_sequence == 11)
        return owner
    monkeypatch.setattr(once, "_require_live_screen_lease", lease)
    cli = Path("D:/verified/codex_task_bus.py")
    pair_checks = []
    def pair():
        pair_checks.append(True)
        return cli
    monkeypatch.setattr(once, "_require_bus_cli_pair", pair)
    argv_seen = []
    def run(argv, **kwargs):
        argv_seen.extend(argv)
        payload = {"ok": True,
                   "event": {"kind": "heartbeat", "task_id": once.SCREEN_TASK_ID,
                             "sequence": 11},
                   "task": {"task_id": once.SCREEN_TASK_ID, "state": "running",
                            "resources": ["ck3-screen:acquired"], "last_sequence": 11}}
        return type("Result", (), {"returncode": 0, "stderr": "",
                                   "stdout": json.dumps(payload)})()
    monkeypatch.setattr(once.subprocess, "run", run)
    once._managed_screen_heartbeat()
    check(observed == [None, 11])
    check(pair_checks == [True, True])
    check(argv_seen[1] == str(cli))
    check(argv_seen[argv_seen.index("--expected-sequence") + 1] == "10")
    check(argv_seen[argv_seen.index("--expected-cli-sha256") + 1]
          == once.BUS_CLI_SHA256)


def test_bus_cli_source_and_installed_bytes_must_match(monkeypatch, tmp_path) -> None:
    checkout = tmp_path / "checkout"
    module_path = checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "entry.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_bytes(b"entry")
    source = checkout / "tools" / "codex_task_bus.py"
    source.parent.mkdir()
    source.write_bytes(b"reviewed bus CLI")
    bus = tmp_path / "bus"
    installed = bus / "bin" / "codex_task_bus.py"
    installed.parent.mkdir(parents=True)
    installed.write_bytes(source.read_bytes())
    monkeypatch.setattr(once, "__file__", str(module_path))
    monkeypatch.setattr(once, "TASK_BUS", bus)
    monkeypatch.setattr(once, "BUS_CLI_SHA256", sha(source))
    check(once._require_bus_cli_pair() == source)
    installed.write_bytes(b"old CLI")
    with pytest.raises(ValueError, match="source/install bytes differ"):
        once._require_bus_cli_pair()


def test_cas_heartbeat_refusal_or_bad_readback_is_red(monkeypatch) -> None:
    monkeypatch.setattr(once, "_require_live_screen_lease",
                        lambda expected_sequence=None: {"last_sequence": 10})
    monkeypatch.setattr(once, "_require_bus_cli_pair",
                        lambda: Path("D:/verified/codex_task_bus.py"))
    for returncode, sequence in ((3, 11), (0, 10), (0, 11)):
        payload = {"ok": True,
                   "event": {"kind": "heartbeat", "task_id": once.SCREEN_TASK_ID,
                             "sequence": sequence},
                   "task": {"task_id": once.SCREEN_TASK_ID, "state": "running",
                            "resources": ["ck3-screen:acquired"], "last_sequence": 10}}
        monkeypatch.setattr(once.subprocess, "run", lambda *a, **k:
                            type("Result", (), {"returncode": returncode,
                                                "stderr": "", "stdout": json.dumps(payload)})())
        with pytest.raises(RuntimeError, match="heartbeat CAS"):
            once._managed_screen_heartbeat()


def test_stale_or_done_screen_record_blocks_new_owner(monkeypatch, tmp_path) -> None:
    bus = tmp_path / "bus"
    tasks = bus / "tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setattr(once, "TASK_BUS", bus)
    now = datetime.now(timezone.utc)
    current = {"schema": "codex.task_bus.v1", "task_id": once.SCREEN_TASK_ID,
               "state": "running", "resources": ["ck3-screen:acquired"],
               "last_sequence": 10, "updated_at_utc": now.isoformat()}
    (tasks / f"{once.SCREEN_TASK_ID}.json").write_text(json.dumps(current), encoding="utf-8")
    check(once._require_live_screen_lease(10)["task_id"] == once.SCREEN_TASK_ID)
    other = {**current, "task_id": "old-screen", "last_sequence": 1,
             "updated_at_utc": (now - timedelta(days=2)).isoformat()}
    path = tasks / "old-screen.json"
    for state in ("running", "done"):
        other["state"] = state
        path.write_text(json.dumps(other), encoding="utf-8")
        with pytest.raises(ValueError, match="unreleased"):
            once._require_live_screen_lease(10)
