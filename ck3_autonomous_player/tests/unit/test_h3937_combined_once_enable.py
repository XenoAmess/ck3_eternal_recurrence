"""Fail-closed checks for the one H3937 read-only enablement entry."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from xar_autoplayer import h3937_combined_once_enable as once


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def check(value: bool) -> None:
    if not value:
        raise AssertionError("test condition failed")


def zero_image(image: str) -> dict[str, object]:
    return {"image": image, "returncode": 0, "found": False, "raw": "no tasks"}


def green_outer() -> dict[str, object]:
    return {
        "ok": True, "status": "GREEN_READ_ONLY_TARGET",
        "action_authorized": False, "date_advance_authorized": False,
        "gameplay_actions": 0, "query_actions": 6, "cleanup": {"ok": True},
    }


def test_a05_unpinned_release_refuses_before_git_or_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(once.outer, "COMBINED_DLL_SHA256", None)
    monkeypatch.setattr(once.outer, "COMBINED_INJECTOR_SHA256", None)
    monkeypatch.setattr(once, "_git", lambda *args: check(False))
    with pytest.raises(ValueError, match="binary pins are not frozen"):
        once._require_exact_admission()


@pytest.fixture
def bounded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    output = tmp_path / "live-attempt"
    output.mkdir()
    (output / "supervisor-claim.json").write_text(json.dumps({
        "schema": "xar.war.h3937-combined-supervisor-claim.v1",
        "claim_nonce": "nonce", "round": once.ROUND,
        "output_dir": str(output), "head": "pinned",
    }), encoding="utf-8")
    go = tmp_path / "go.json"
    go.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "GO", go)
    monkeypatch.setattr(once, "_require_exact_admission", lambda: {"head": "pinned"})
    monkeypatch.setattr(once, "_git", lambda *args: "pinned")
    monkeypatch.setattr(once, "_require_go", lambda identity: ({
        "screen_task_last_sequence": 101,
        "steam_original_path": str(go), "steam_original_sha256": digest(go),
        "steam_frame_receipt_path": str(go),
        "steam_frame_receipt_sha256": digest(go),
        "screen_challenge_path": str(go),
        "screen_challenge_sha256": digest(go),
        "screen_lease_receipt_path": str(go),
        "screen_lease_receipt_sha256": digest(go),
    }, digest(go)))
    monkeypatch.setattr(once, "_require_live_screen_lease",
                        lambda sequence=None: {"last_sequence": sequence or 101})
    monkeypatch.setattr(once, "_image_inventory", zero_image)
    monkeypatch.setattr(once.outer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", False)
    monkeypatch.setattr(once.inner, "H3937_COMBINED_LIVE_AUTHORIZED", False)
    monkeypatch.setattr(once.target_reads, "H3937_TARGET_LIVE_AUTHORIZED", False)
    return output


def test_one_call_enables_only_during_read_and_restores_gates(bounded, monkeypatch):
    calls = []

    def collect(*args, **kwargs):
        check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is True)
        check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is True)
        check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is True)
        check(kwargs["ownership_round_id"] == once.ROUND)
        check(kwargs["cold_start_checkpoint"] is True)
        check(kwargs["native_bridge"].mode == "native-headless")
        check(kwargs["native_bridge"].pipe_name == once.PIPE)
        check(kwargs["readiness_timeout_diagnostic_probe"] is True)
        check(kwargs["readiness_stall_watchdog"] is True)
        check(kwargs["readiness_timeout_seconds"] == 1800)
        check(kwargs["timeout_seconds"] == 1890)
        calls.append(1)
        return green_outer()

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", collect)
    completion = once.run_exact_once("nonce")
    check(completion["status"] == "GREEN_READ_ONLY")
    check(completion["action_authorized"] is False)
    check(completion["date_advance_authorized"] is False)
    check(calls == [1])
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)
    check((bounded / "outer-report.json").exists())
    check((bounded / "completion.json").exists())
    with pytest.raises(FileExistsError):
        once.run_exact_once("nonce")
    check(calls == [1])


def test_live_lease_lost_during_read_marks_result_red(bounded, monkeypatch):
    checks = []

    def lease(sequence=None):
        checks.append(sequence)
        if len(checks) == 2:
            raise ValueError("screen lease was released")
        return {"last_sequence": 101}

    monkeypatch.setattr(once, "_require_live_screen_lease", lease)
    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once",
                        lambda *a, **k: green_outer())
    completion = once.run_exact_once("nonce")
    check(completion["status"] == "RED")
    check(completion["gates_restored"] is True)
    check("screen lease" in str(completion["error"]))


@pytest.mark.parametrize("failure", ["bad_claim", "bad_admission", "bad_go", "busy_process"])
def test_prelaunch_refusals_preserve_red_and_never_call_outer(
    bounded, monkeypatch, failure,
):
    def forbidden(*args, **kwargs):
        raise AssertionError("outer must not run")

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", forbidden)
    if failure == "bad_admission":
        monkeypatch.setattr(once, "_require_exact_admission", lambda: (_ for _ in ()).throw(ValueError("wrong source")))
    elif failure == "bad_go":
        monkeypatch.setattr(once, "_require_go", lambda identity: (_ for _ in ()).throw(ValueError("wrong GO")))
    else:
        monkeypatch.setattr(once, "_image_inventory", lambda image: {
            "image": image, "returncode": 0, "found": image == "ck3.exe", "raw": "busy"})
    completion = once.run_exact_once("wrong" if failure == "bad_claim" else "nonce")
    check(completion["status"] == "RED")
    check(completion["gates_restored"] is True)
    check((bounded / "error-traceback.txt").exists())
    check(not (bounded / "outer-report.json").exists())


def test_outer_exception_restores_all_gates_and_retains_trace(bounded, monkeypatch):
    def broken(*args, **kwargs):
        check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is True)
        check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is True)
        check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is True)
        raise RuntimeError("simulated native failure")

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", broken)
    completion = once.run_exact_once("nonce")
    check(completion["status"] == "RED")
    check(completion["outer_cleanup_proven"] is False)
    check(completion["gates_restored"] is True)
    check("simulated native failure" in (bounded / "error-traceback.txt").read_text(encoding="utf-8"))
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)
    check(once.target_reads.H3937_TARGET_LIVE_AUTHORIZED is False)


@pytest.mark.parametrize("bad_field,value", [
    ("action_authorized", True), ("date_advance_authorized", True),
    ("gameplay_actions", 1), ("query_actions", 1), ("cleanup", {"ok": False}),
])
def test_readonly_contract_mismatch_is_red(bounded, monkeypatch, bad_field, value):
    report = green_outer()
    report[bad_field] = value
    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", lambda *a, **k: report)
    completion = once.run_exact_once("nonce")
    check(completion["status"] == "RED")
    check(completion["action_authorized"] is False)
    check(completion["date_advance_authorized"] is False)


def fresh_go_fixture(monkeypatch, tmp_path):
    bus = tmp_path / "bus"
    tasks = bus / "tasks"
    tasks.mkdir(parents=True)
    screen = tmp_path / "screen-attempt"
    screen.mkdir()
    state = tmp_path / "prepared" / "state"
    output = tmp_path / "live"
    go_path = tmp_path / "go.json"
    monkeypatch.setattr(once, "STATE", state)
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "GO", go_path)
    monkeypatch.setattr(once, "SCREEN", screen)
    monkeypatch.setattr(once, "TASK_BUS", bus)
    now = datetime.now(timezone.utc)
    stamp = lambda seconds: (now + timedelta(seconds=seconds)).isoformat()
    owner = {"schema": "codex.task_bus.v1", "task_id": once.SCREEN_TASK_ID,
             "state": "running", "resources": ["ck3-screen:acquired"],
             "last_sequence": 101, "updated_at_utc": stamp(-55)}
    task_path = tasks / f"{once.SCREEN_TASK_ID}.json"
    task_path.write_text(json.dumps(owner), encoding="utf-8")
    lease = screen / "screen-lease-snapshot.json"
    lease.write_text(json.dumps(owner), encoding="utf-8")
    challenge = {"schema": "xar.war.h3937-combined-screen-challenge.v1",
                 "issued_at_utc": stamp(-50), "challenge_nonce": "a" * 48,
                 "candidate_head": "a" * 40, "round": once.ROUND,
                 "screen_attempt_dir": str(screen.resolve()),
                 "task_bus_dir": str(bus.resolve()),
                 "screen_task_id": once.SCREEN_TASK_ID,
                 "screen_task_last_sequence": 101}
    challenge_path = screen / "screen-challenge.json"
    challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
    steam = screen / "steam-moved.png"
    steam.write_bytes(b"newly-moved-screen")
    before = screen / "steam-before.png"
    before.write_bytes(b"screen-before-window-movement")
    frame = {"schema": "ck3.steam_fresh_desktop_frame.v1",
             "captured_at_utc": stamp(-40), "moving_edge_changed": True,
             "pixel_difference_bbox": [1, 2, 20, 30],
             "before_path": str(before), "before_sha256": digest(before),
             "before_rect": [0, 0, 100, 100], "moved_rect": [20, 0, 120, 100],
             "restored_rect": [0, 0, 100, 100], "clock_check": None,
             "moved_path": str(steam), "moved_sha256": digest(steam),
             "moved_identity": {"path": str(steam), "bytes": steam.stat().st_size,
                                "sha256": digest(steam)}}
    frame_path = screen / "steam-frame-freshness.json"
    frame_path.write_text(json.dumps(frame), encoding="utf-8")
    identity = {"head": "a" * 40, "admission_sha256": "A" * 64,
                "manifest_sha256": "B" * 64, "preflight_sha256": "C" * 64,
                "rebind_sha256": "D" * 64}
    value = {
        "schema": "xar.war.h3937-combined-once-go.v1",
        "decision": "GO_READ_ONLY_H3937_COMBINED", "candidate_head": identity["head"],
        "round": once.ROUND, "state_dir": str(state), "output_dir": str(output),
        "pipe": once.PIPE, "admission_sha256": identity["admission_sha256"],
        "operator_manifest_sha256": identity["manifest_sha256"],
        "preflight_sha256": identity["preflight_sha256"],
        "rebind_sha256": identity["rebind_sha256"],
        "task_bus_dir": str(bus.resolve()), "screen_task_id": once.SCREEN_TASK_ID,
        "screen_task_last_sequence": 101, "screen_attempt_dir": str(screen.resolve()),
        "screen_lease_exclusive": True,
        "steam_offline_direct_visual_reviewed": True,
        "account_single_instance_clear": True,
        "ck3_zero_process_before": True, "recorder_zero_before": True,
        "authorized_scope": "six_paused_readonly_queries",
        "maximum_query_actions": 6,
        "issued_at_utc": stamp(-20), "steam_direct_reviewed_at_utc": stamp(-30),
        "screen_challenge_nonce": challenge["challenge_nonce"],
        "steam_original_path": str(steam), "steam_original_sha256": digest(steam),
        "steam_frame_receipt_path": str(frame_path),
        "steam_frame_receipt_sha256": digest(frame_path),
        "screen_challenge_path": str(challenge_path),
        "screen_challenge_sha256": digest(challenge_path),
        "screen_lease_receipt_path": str(lease),
        "screen_lease_receipt_sha256": digest(lease),
    }
    go_path.write_text(json.dumps(value), encoding="utf-8")
    return identity, value, owner, task_path, steam, challenge_path, frame_path


def test_go_receipt_rejects_wrong_round_output_and_modified_screen(monkeypatch, tmp_path):
    identity, value, _, _, steam, _, _ = fresh_go_fixture(monkeypatch, tmp_path)
    check(once._require_go(identity)[0] == value)
    value["round"] = "R9999"
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)
    value["round"] = once.ROUND
    value["output_dir"] = str(tmp_path / "wrong-output")
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)
    value["output_dir"] = str(once.OUTPUT)
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    value["maximum_query_actions"] = 2
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)
    value["maximum_query_actions"] = 6
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    steam.write_bytes(b"modified")
    with pytest.raises(ValueError, match="steam_original"):
        once._require_go(identity)


def test_go_replacement_during_validation_is_red(monkeypatch, tmp_path):
    identity, _, _, _, _, _, _ = fresh_go_fixture(monkeypatch, tmp_path)
    original = once._require_live_screen_lease

    def revoke(sequence=None):
        owner = original(sequence)
        once.GO.write_text("{}", encoding="utf-8")
        return owner

    monkeypatch.setattr(once, "_require_live_screen_lease", revoke)
    with pytest.raises(ValueError, match="GO receipt bytes changed"):
        once._require_go(identity)


def test_worker_refuses_go_replacement_after_validation(bounded, monkeypatch):
    original_go = once._require_go

    def revoke(identity):
        verified = original_go(identity)
        once.GO.write_text("{} ", encoding="utf-8")
        return verified

    monkeypatch.setattr(once, "_require_go", revoke)
    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("native session must not start")))
    result = once.run_exact_once("nonce")
    check(result["status"] == "RED")
    check("GO receipt changed immediately" in str(result["error"]))


@pytest.mark.parametrize("failure", ["other_owner", "changed_sequence", "stale_owner",
                                    "stale_go", "stale_challenge", "old_frame",
                                    "wrong_challenge", "wrong_frame", "wrong_lease_copy",
                                    "wrong_task_id", "before_modified", "clock_stale",
                                    "old_attempt_image"])
def test_go_rejects_stale_or_mismatched_live_screen(monkeypatch, tmp_path, failure):
    identity, value, owner, task_path, steam, challenge_path, frame_path = (
        fresh_go_fixture(monkeypatch, tmp_path))
    now = datetime.now(timezone.utc)
    if failure == "other_owner":
        other = {**owner, "task_id": "another-live-task"}
        (task_path.parent / "another-live-task.json").write_text(
            json.dumps(other), encoding="utf-8")
    elif failure == "changed_sequence":
        owner["last_sequence"] = 102
        task_path.write_text(json.dumps(owner), encoding="utf-8")
    elif failure == "stale_owner":
        owner["updated_at_utc"] = (now - timedelta(minutes=11)).isoformat()
        task_path.write_text(json.dumps(owner), encoding="utf-8")
    elif failure == "stale_go":
        value["issued_at_utc"] = (now - timedelta(minutes=6)).isoformat()
    elif failure == "stale_challenge":
        challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
        challenge["issued_at_utc"] = (now - timedelta(minutes=11)).isoformat()
        challenge_path.write_text(json.dumps(challenge), encoding="utf-8")
        value["screen_challenge_sha256"] = digest(challenge_path)
    elif failure == "old_frame":
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        frame["captured_at_utc"] = (now - timedelta(minutes=6)).isoformat()
        frame_path.write_text(json.dumps(frame), encoding="utf-8")
        value["steam_frame_receipt_sha256"] = digest(frame_path)
    elif failure == "wrong_challenge":
        value["screen_challenge_nonce"] = "b" * 48
    elif failure == "wrong_frame":
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        frame["moved_sha256"] = "E" * 64
        frame_path.write_text(json.dumps(frame), encoding="utf-8")
        value["steam_frame_receipt_sha256"] = digest(frame_path)
    elif failure == "wrong_lease_copy":
        lease = Path(value["screen_lease_receipt_path"])
        lease.write_text(json.dumps({**owner, "last_sequence": 999}), encoding="utf-8")
        value["screen_lease_receipt_sha256"] = digest(lease)
    elif failure == "wrong_task_id":
        value["screen_task_id"] = "old-screen-task"
    elif failure == "before_modified":
        before = steam.with_name("steam-before.png")
        before.write_bytes(b"different-before")
    elif failure == "clock_stale":
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        frame["clock_check"] = {"clock_pixels_unchanged": True}
        frame_path.write_text(json.dumps(frame), encoding="utf-8")
        value["steam_frame_receipt_sha256"] = digest(frame_path)
    elif failure == "old_attempt_image":
        old = tmp_path / "old-attempt" / "steam-moved.png"
        old.parent.mkdir()
        old.write_bytes(steam.read_bytes())
        value["steam_original_path"] = str(old)
    once.GO.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        once._require_go(identity)


def test_challenge_requires_current_unique_owner_and_is_exclusive(monkeypatch, tmp_path):
    identity, _, owner, task_path, _, challenge_path, _ = fresh_go_fixture(
        monkeypatch, tmp_path)
    challenge_path.unlink()
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": identity["head"]})
    result = once.issue_screen_challenge(tmp_path / "entry.py")
    check(result["screen_task_id"] == once.SCREEN_TASK_ID)
    check(result["screen_task_last_sequence"] == 101)
    check(len(result["challenge_nonce"]) == 48)
    with pytest.raises(FileExistsError):
        once.issue_screen_challenge(tmp_path / "entry.py")
    challenge_path.unlink()
    owner["state"] = "done"
    task_path.write_text(json.dumps(owner), encoding="utf-8")
    with pytest.raises(ValueError, match="uniquely owned"):
        once.issue_screen_challenge(tmp_path / "entry.py")


def test_managed_heartbeat_uses_exact_bus_and_rechecks_lease(monkeypatch, tmp_path):
    _, _, owner, task_path, _, _, _ = fresh_go_fixture(monkeypatch, tmp_path)
    commands = []

    def heartbeat(argv, **kwargs):
        commands.append(argv)
        check(argv[argv.index("--bus-dir") + 1] == str(once.TASK_BUS))
        check(argv[argv.index("--task") + 1] == once.SCREEN_TASK_ID)
        owner["last_sequence"] = 102
        task_path.write_text(json.dumps(owner), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(once.subprocess, "run", heartbeat)
    once._managed_screen_heartbeat()
    check(len(commands) == 1)
    owner["state"] = "done"
    task_path.write_text(json.dumps(owner), encoding="utf-8")
    with pytest.raises(ValueError, match="uniquely owned"):
        once._managed_screen_heartbeat()
    check(len(commands) == 1)


def test_exact_prepared_source_rejects_driver_byte_and_head_drift(
    monkeypatch, tmp_path,
):
    root = tmp_path / "no-launch"
    state = root / "state"
    dll = root / "source-verified" / "xar_ck3_bridge.dll"
    injector = root / "source-verified" / "xar_ck3_bridge_injector.exe"
    save = state / "profile" / "save games" / "xar_checkpoint.ck3"
    sidecar = state / "player-child-matrilineal-formal-v1.json"
    driver = state / "native-session" / "driver-state.json"
    rebind = state / "ordinary-seed-rebind-v1.json"
    preflight = state / "preflights" / "report.json"
    game_exe = tmp_path / "game" / "binaries" / "ck3.exe"
    raw_driver = root / "source-verified" / "driver-state.json"
    raw_save = root / "source-verified" / "xar_checkpoint.ck3"
    raw_sidecar = root / "source-verified" / "player-child-matrilineal-formal-v1.json"
    for path, data in (
        (dll, b"dll"), (injector, b"injector"), (save, b"save"),
        (sidecar, b"sidecar"), (driver, b"driver"), (game_exe, b"game"),
        (raw_driver, b"raw driver"), (raw_save, b"save"),
        (raw_sidecar, b"sidecar"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    lifecycle = {
        "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
    }
    preflight.parent.mkdir(parents=True, exist_ok=True)
    preflight.write_text(json.dumps({
        "status": "ready", "ok": True, "ck3_launch_attempted": False,
        "desktop_interaction": False, "process_inventory": {"processes": []},
        "profile": {"environment_sha256": "E" * 64,
                    "ck3_executable_sha256": digest(game_exe)},
        "resume_anchor": {
            "checkpoint": {"saved_date_raw": 53219928, "history_index": 3937,
                           "succession_lifecycle": {**lifecycle,
                               "environment_sha256": "E" * 64}},
            "driver_state": {"episode_character_id": 29829,
                             "episode_run_id": "native-29829-2bc2d599f7f9",
                             "succession_lifecycle": {**lifecycle,
                                 "environment_sha256": "E" * 64}},
        },
    }), encoding="utf-8")
    rebind.write_text(json.dumps({
        "ok": True, "status": "rebound", "ck3_launch_attempted": False,
        "desktop_interaction": False, "pipe_name": once.PIPE,
        "state_dir": str(state),
        "environment": {"target_sha256": "E" * 64},
        "driver_state": {"target_sha256": digest(driver)},
    }), encoding="utf-8")
    head = "a" * 40
    admission = {
        "candidate_head": head, "candidate_checkout_clean": True,
        "prepared_state": str(state), "episode_run_id": "native-29829-2bc2d599f7f9",
        "actor": 29829, "date_raw": 53219928, "history_index": 3937,
        "raw_driver_sha256": "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722",
        "combined_outer_hard_gate": False, "combined_inner_hard_gate": False,
        "target_inner_hard_gate": False,
        "ck3_launch_attempted": False, "live_authorized": False,
        "prepared_driver_sha256": digest(driver),
        "official_rebind_receipt_sha256": digest(rebind),
        "official_preflight_report": str(preflight),
        "official_preflight_report_sha256": digest(preflight),
        "environment_sha256": "E" * 64,
        "dll_sha256": digest(dll),
        "injector_sha256": digest(injector),
    }
    manifest = {
        "candidate_head": head, "candidate_clean": True,
        "state_dir": str(state), "bridge_pipe": once.PIPE,
        "bridge_dll": str(dll), "bridge_injector": str(injector),
        "game_dir": str(tmp_path / "game"),
        "outer_hard_gate": False, "inner_hard_gate": False,
        "target_hard_gate": False,
        "ck3_launch_attempted": False, "live_output_created": False,
        "bridge_dll_sha256": digest(dll),
        "bridge_injector_sha256": digest(injector),
        "source_raw_driver_sha256": admission["raw_driver_sha256"],
        "source_checkpoint_sha256": "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6",
        "source_child_sidecar_sha256": "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7",
        "prepared_driver_sha256": admission["prepared_driver_sha256"],
        "rebind_receipt_sha256": admission["official_rebind_receipt_sha256"],
        "preflight_report_sha256": admission["official_preflight_report_sha256"],
        "environment_sha256": admission["environment_sha256"],
        "source_git_blobs": {f"source_{number}": "b" * 40 for number in range(15)},
    }
    (root / "admission.json").write_text(json.dumps(admission), encoding="utf-8")
    (root / "operator-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(once, "NO_LAUNCH", root)
    monkeypatch.setattr(once, "STATE", state)
    monkeypatch.setattr(once, "DLL", dll)
    monkeypatch.setattr(once, "INJECTOR", injector)
    monkeypatch.setattr(once, "GAME", tmp_path / "game")
    monkeypatch.setattr(once.outer, "COMBINED_DLL_SHA256", digest(dll))
    monkeypatch.setattr(once.outer, "COMBINED_INJECTOR_SHA256", digest(injector))
    monkeypatch.setattr(once.outer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", False)
    monkeypatch.setattr(once.inner, "H3937_COMBINED_LIVE_AUTHORIZED", False)
    monkeypatch.setattr(once.target_reads, "H3937_TARGET_LIVE_AUTHORIZED", False)

    def fake_git(*args):
        if args[0] == "status":
            return ""
        if args == ("rev-parse", "HEAD"):
            return head
        return "b" * 40

    monkeypatch.setattr(once, "_git", fake_git)
    true_sha = once._sha

    def synthetic_large_source_hash(path):
        if path in (save, raw_save):
            return "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6"
        if path in (sidecar, raw_sidecar):
            return "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7"
        if path == raw_driver:
            return "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722"
        return true_sha(path)

    monkeypatch.setattr(once, "_sha", synthetic_large_source_hash)
    check(once._require_exact_admission()["head"] == head)
    admission["target_inner_hard_gate"] = True
    (root / "admission.json").write_text(json.dumps(admission), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()
    admission["target_inner_hard_gate"] = False
    (root / "admission.json").write_text(json.dumps(admission), encoding="utf-8")
    driver.write_bytes(b"driver changed")
    with pytest.raises(ValueError, match="source asset hash"):
        once._require_exact_admission()
    driver.write_bytes(b"driver")
    admission["candidate_head"] = "c" * 40
    (root / "admission.json").write_text(json.dumps(admission), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        once._require_exact_admission()


def test_supervisor_hard_timeout_retains_red_and_kill_receipt(
    monkeypatch, tmp_path,
):
    output = tmp_path / "one-shot"
    entry = tmp_path / "entry.py"
    entry.write_text("", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_image_inventory", zero_image)
    monkeypatch.setattr(once, "_require_preworker_screen_gate", lambda entry: None)
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": "pinned", "entry_blob": "b" * 40, "entry_sha256": "A" * 64})
    calls = []

    class HungWorker:
        pid = 4242
        returncode = 1

        def communicate(self, *, timeout):
            calls.append(("communicate", timeout))
            if len(calls) == 1:
                raise once.subprocess.TimeoutExpired("worker", timeout, output=b"partial")
            return b"finished", b"failure"

    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: HungWorker())
    moments = iter((0.0, 0.0, float(once.SUPERVISOR_TIMEOUT_SECONDS + 1)))
    monkeypatch.setattr(once, "_monotonic", lambda: next(moments))

    def taskkill(argv, **kwargs):
        calls.append(("taskkill", argv))
        return SimpleNamespace(returncode=0, stdout=b"killed", stderr=b"")

    monkeypatch.setattr(once.subprocess, "run", taskkill)
    check(once.supervise_exact_once(entry) == 1)
    result = json.loads((output / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(result["status"] == "RED")
    check(result["timeout"] is True)
    check(result["taskkill"]["worker_pid"] == 4242)
    check(any(call[0] == "taskkill" for call in calls))
    check((output / "supervisor.stdout.txt").exists())


def test_supervisor_refuses_consumed_output_before_child(monkeypatch, tmp_path):
    output = tmp_path / "already-used"
    output.mkdir()
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": "pinned", "entry_blob": "b" * 40, "entry_sha256": "A" * 64})
    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("must not spawn worker")))
    with pytest.raises(FileExistsError):
        once.supervise_exact_once(tmp_path / "entry.py")


def test_supervisor_wrong_entry_records_red_without_child(monkeypatch, tmp_path):
    output = tmp_path / "wrong-entry"
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: (_ for _ in ()).throw(
        ValueError("entry differs from HEAD")))
    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("must not spawn worker")))
    check(once.supervise_exact_once(tmp_path / "entry.py") == 1)
    record = json.loads((output / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(record["status"] == "RED")
    check(record["worker_started"] is False)
    check(record["one_shot_output_consumed"] is True)


def test_supervisor_accepts_only_green_child_and_zero_processes(monkeypatch, tmp_path):
    output = tmp_path / "fresh"
    entry = tmp_path / "entry.py"
    entry.write_text("", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_image_inventory", zero_image)
    monkeypatch.setattr(once, "_require_preworker_screen_gate", lambda entry: None)
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": "pinned", "entry_blob": "b" * 40, "entry_sha256": "A" * 64})

    class FinishedWorker:
        pid = 5151
        returncode = 0

        def communicate(self, *, timeout):
            check(timeout == once.SUPERVISOR_HEARTBEAT_SECONDS)
            report = output / "outer-report.json"
            report.write_text(json.dumps(green_outer()), encoding="utf-8")
            (output / "completion.json").write_text(
                json.dumps({"status": "GREEN_READ_ONLY",
                            "action_authorized": False,
                            "date_advance_authorized": False,
                            "outer_cleanup_proven": True,
                            "gates_restored": True,
                            "processes_gone": True,
                            "outer_report_sha256": digest(report)}), encoding="utf-8")
            return b"worker ok", b""

    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: FinishedWorker())
    check(once.supervise_exact_once(entry) == 0)
    result = json.loads((output / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(result["status"] == "GREEN_READ_ONLY")
    check(result["processes_gone"] is True)
    check(result["timeout"] is False)


def test_supervisor_renews_exact_screen_lease_during_long_worker(monkeypatch, tmp_path):
    output = tmp_path / "long-worker"
    entry = tmp_path / "entry.py"
    entry.write_text("", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_image_inventory", zero_image)
    monkeypatch.setattr(once, "_require_preworker_screen_gate", lambda entry: None)
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": "pinned", "entry_blob": "b" * 40, "entry_sha256": "A" * 64})
    heartbeats = []
    monkeypatch.setattr(once, "_managed_screen_heartbeat", lambda: heartbeats.append(1))

    class SlowWorker:
        pid = 5152
        returncode = 0
        calls = 0

        def communicate(self, *, timeout):
            self.calls += 1
            check(timeout <= once.SUPERVISOR_HEARTBEAT_SECONDS)
            if self.calls == 1:
                raise once.subprocess.TimeoutExpired("worker", timeout)
            report = output / "outer-report.json"
            report.write_text(json.dumps(green_outer()), encoding="utf-8")
            (output / "completion.json").write_text(json.dumps({
                "status": "GREEN_READ_ONLY", "action_authorized": False,
                "date_advance_authorized": False, "outer_cleanup_proven": True,
                "gates_restored": True, "processes_gone": True,
                "outer_report_sha256": digest(report),
            }), encoding="utf-8")
            return b"worker ok", b""

    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: SlowWorker())
    check(once.supervise_exact_once(entry) == 0)
    check(heartbeats == [1])
    result = json.loads((output / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(result["timeout"] is False)


def test_supervisor_refuses_lost_screen_lease_before_worker(monkeypatch, tmp_path):
    identity, _, owner, task_path, _, _, _ = fresh_go_fixture(monkeypatch, tmp_path)
    entry = tmp_path / "entry.py"
    entry.write_text("", encoding="utf-8")
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": identity["head"], "entry_blob": "b" * 40,
        "entry_sha256": "A" * 64})
    monkeypatch.setattr(once, "_require_exact_admission", lambda: identity)
    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("worker must not start")))
    owner["state"] = "done"
    task_path.write_text(json.dumps(owner), encoding="utf-8")
    check(once.supervise_exact_once(entry) == 1)
    result = json.loads((once.OUTPUT / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(result["status"] == "RED")
    check(result["worker_pid"] is None)
    check(result["processes_gone"] is False)


@pytest.mark.parametrize("failure", ["inventory_error", "broken_child_json",
                                    "taskkill_failed_worker_alive"])
def test_supervisor_postcheck_failures_retain_red(monkeypatch, tmp_path, failure):
    output = tmp_path / "one-shot"
    entry = tmp_path / "entry.py"
    entry.write_text("", encoding="utf-8")
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "_require_entry_blob", lambda path: {
        "head": "pinned", "entry_blob": "b" * 40,
        "entry_sha256": "A" * 64})
    monkeypatch.setattr(once, "_require_preworker_screen_gate", lambda entry: None)
    monkeypatch.setattr(once, "_image_inventory",
                        lambda image: (_ for _ in ()).throw(OSError("inventory failed"))
                        if failure == "inventory_error" else zero_image(image))

    class Worker:
        pid = 9999
        returncode = None if failure == "taskkill_failed_worker_alive" else 0
        calls = 0

        def communicate(self, *, timeout):
            self.calls += 1
            if failure == "taskkill_failed_worker_alive":
                raise once.subprocess.TimeoutExpired("worker", timeout)
            report = output / "outer-report.json"
            report.write_text(json.dumps(green_outer()), encoding="utf-8")
            child = {"status": "GREEN_READ_ONLY", "action_authorized": False,
                     "date_advance_authorized": False, "outer_cleanup_proven": True,
                     "gates_restored": True, "processes_gone": True,
                     "outer_report_sha256": digest(report)}
            (output / "completion.json").write_text(
                "{broken" if failure == "broken_child_json" else json.dumps(child),
                encoding="utf-8")
            return b"done", b""

        def kill(self):
            raise OSError("worker still alive")

    monkeypatch.setattr(once.subprocess, "Popen", lambda *a, **k: Worker())
    if failure == "taskkill_failed_worker_alive":
        monkeypatch.setattr(once.subprocess, "run", lambda *a, **k: SimpleNamespace(
            returncode=1, stdout=b"", stderr=b"taskkill failed"))
    check(once.supervise_exact_once(entry) == 1)
    result = json.loads((output / "supervisor-completion.json").read_text(encoding="utf-8"))
    check(result["status"] == "RED")
    check(result["processes_gone"] is False if failure != "broken_child_json"
          else result["processes_gone"] is True)
    check((output / "supervisor.stdout.txt").exists())
    check((output / "supervisor.stderr.txt").exists())
