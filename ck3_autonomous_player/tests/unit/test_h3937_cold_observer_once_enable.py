"""Focused new-admission checks; never create a CK3 or desktop session."""

from __future__ import annotations

import hashlib
import json
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
    check(once.ROUND == "R3946")
    check(once.LIVE_RUN_ID.endswith("--vanilla--R0114"))
    check(once.PIPE == old_once.PIPE)  # Exact raw driver-state contract.
    check(signature(once.outer.collect_h3937_combined_paused_war_scope_once)
          .parameters["cold_load_observation_dir"].default is None)
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)


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
                     "mod_key": "vanilla", "sequence": 114}
    live_identity_path.write_text(json.dumps(live_identity), encoding="utf-8")
    head = "a" * 40
    admission = {
        "schema": "xar.war.h3937-cold-observer-disabled-no-launch-admission.v1",
        "candidate_head": head, "candidate_checkout_clean": True,
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
                       "LIVE_IDENTITY": live_identity_path}.items():
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
    bound = once._require_exact_admission()
    check(bound["live_run_identity_sha256"] == sha(live_identity_path))
    once._require_no_launch_unchanged(bound)
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
    manifest["source_git_blobs"] = blobs | {
        "source_module_.h3937_cold_load_observer": "b" * 40}
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
    output = tmp_path / "attempt-12"
    screen = tmp_path / "screen-attempt-12"
    bus = tmp_path / "task-bus"
    for path in (state, screen, bus):
        path.mkdir()
    go_path = tmp_path / "go-attempt-12.json"
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
          "screen_lease_receipt_sha256": sha(lease)}
    go_path.write_text(json.dumps(go), encoding="utf-8")
    return identity, go, challenge, challenge_path


@pytest.mark.parametrize("field,value", [
    ("live_run_id", "desktop-wrong--vanilla--R0114"),
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
    challenge["live_run_id"] = "desktop-wrong--vanilla--R0114"
    challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
    go["screen_challenge_sha256"] = sha(challenge_path)
    once.GO.write_text(json.dumps(go), encoding="utf-8")
    with pytest.raises(ValueError, match="screen challenge"):
        once._require_go(identity)


def test_worker_passes_explicit_observer_and_keeps_gameplay_off(
    monkeypatch, tmp_path,
) -> None:
    output = tmp_path / "attempt-12"
    output.mkdir()
    (output / "supervisor-claim.json").write_text(json.dumps({
        "schema": "xar.war.h3937-cold-observer-supervisor-claim.v1",
        "claim_nonce": "nonce", "round": once.ROUND,
        "live_run_id": once.LIVE_RUN_ID,
        "output_dir": str(output), "head": "pinned",
    }), encoding="utf-8")
    go = tmp_path / "go.json"
    go.write_text("{}", encoding="utf-8")
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
        return {"ok": True, "status": "GREEN_READ_ONLY_TARGET",
                "action_authorized": False, "date_advance_authorized": False,
                "gameplay_actions": 0, "query_actions": 6,
                "cleanup": {"ok": True}}

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once",
                        collect)
    result = once.run_exact_once("nonce")
    check(result["status"] == "GREEN_READ_ONLY")
    check(calls == [1])
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)


def test_preworker_pipe_collision_rejects_before_worker(monkeypatch, tmp_path) -> None:
    entry = tmp_path / "entry.py"
    output = tmp_path / "attempt-12"
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
    check(receipt["processes_gone"] is False)
    check("pipe busy" in str(receipt["error"]))
