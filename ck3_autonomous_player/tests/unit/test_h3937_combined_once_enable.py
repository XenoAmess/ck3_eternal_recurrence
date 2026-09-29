"""Fail-closed checks for the one H3937 read-only enablement entry."""

from __future__ import annotations

import hashlib
import json
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
        "ok": True, "status": "GREEN_READ_ONLY_COMBINED",
        "action_authorized": False, "date_advance_authorized": False,
        "gameplay_actions": 0, "query_actions": 2, "cleanup": {"ok": True},
    }


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
    monkeypatch.setattr(once, "_require_go", lambda identity: {
        "steam_original_path": str(go), "steam_original_sha256": digest(go),
        "screen_lease_receipt_path": str(go),
        "screen_lease_receipt_sha256": digest(go),
    })
    monkeypatch.setattr(once, "_image_inventory", zero_image)
    monkeypatch.setattr(once.outer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", False)
    monkeypatch.setattr(once.inner, "H3937_COMBINED_LIVE_AUTHORIZED", False)
    return output


def test_one_call_enables_only_during_read_and_restores_gates(bounded, monkeypatch):
    calls = []

    def collect(*args, **kwargs):
        check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is True)
        check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is True)
        check(kwargs["ownership_round_id"] == once.ROUND)
        check(kwargs["cold_start_checkpoint"] is True)
        check(kwargs["native_bridge"].mode == "native-headless")
        check(kwargs["native_bridge"].pipe_name == once.PIPE)
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
    check((bounded / "outer-report.json").exists())
    check((bounded / "completion.json").exists())
    with pytest.raises(FileExistsError):
        once.run_exact_once("nonce")
    check(calls == [1])


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


def test_outer_exception_restores_both_gates_and_retains_trace(bounded, monkeypatch):
    def broken(*args, **kwargs):
        check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is True)
        check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is True)
        raise RuntimeError("simulated native failure")

    monkeypatch.setattr(once.outer, "collect_h3937_combined_paused_war_scope_once", broken)
    completion = once.run_exact_once("nonce")
    check(completion["status"] == "RED")
    check(completion["outer_cleanup_proven"] is False)
    check(completion["gates_restored"] is True)
    check("simulated native failure" in (bounded / "error-traceback.txt").read_text(encoding="utf-8"))
    check(once.outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is False)
    check(once.inner.H3937_COMBINED_LIVE_AUTHORIZED is False)


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


def test_go_receipt_rejects_wrong_round_and_output(monkeypatch, tmp_path):
    state = tmp_path / "prepared" / "state"
    output = tmp_path / "live"
    go_path = tmp_path / "go.json"
    steam = tmp_path / "steam.png"
    lease = tmp_path / "lease.json"
    steam.write_bytes(b"screen")
    lease.write_bytes(b"lease")
    monkeypatch.setattr(once, "STATE", state)
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "GO", go_path)
    monkeypatch.setattr(once, "SCREEN", tmp_path)
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
        "screen_lease_exclusive": True,
        "steam_offline_direct_visual_reviewed": True,
        "account_single_instance_clear": True,
        "ck3_zero_process_before": True, "recorder_zero_before": True,
        "authorized_scope": "two_paused_readonly_queries",
        "steam_original_path": str(steam), "steam_original_sha256": digest(steam),
        "screen_lease_receipt_path": str(lease),
        "screen_lease_receipt_sha256": digest(lease),
    }
    go_path.write_text(json.dumps(value), encoding="utf-8")
    check(once._require_go(identity) == value)
    value["round"] = "R9999"
    go_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)
    value["round"] = once.ROUND
    value["output_dir"] = str(tmp_path / "wrong-output")
    go_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="GO receipt"):
        once._require_go(identity)


def test_go_receipt_rejects_modified_screen_bytes(monkeypatch, tmp_path):
    state = tmp_path / "state"
    output = tmp_path / "output"
    go_path = tmp_path / "go.json"
    screen = tmp_path / "screen.png"
    lease = tmp_path / "lease.json"
    screen.write_bytes(b"original")
    lease.write_bytes(b"lease")
    monkeypatch.setattr(once, "STATE", state)
    monkeypatch.setattr(once, "OUTPUT", output)
    monkeypatch.setattr(once, "GO", go_path)
    monkeypatch.setattr(once, "SCREEN", tmp_path)
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
        "screen_lease_exclusive": True,
        "steam_offline_direct_visual_reviewed": True,
        "account_single_instance_clear": True,
        "ck3_zero_process_before": True, "recorder_zero_before": True,
        "authorized_scope": "two_paused_readonly_queries",
        "steam_original_path": str(screen), "steam_original_sha256": digest(screen),
        "screen_lease_receipt_path": str(lease),
        "screen_lease_receipt_sha256": digest(lease),
    }
    go_path.write_text(json.dumps(value), encoding="utf-8")
    screen.write_bytes(b"modified")
    with pytest.raises(ValueError, match="steam_original"):
        once._require_go(identity)


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
        "source_git_blobs": {f"source_{number}": "b" * 40 for number in range(12)},
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
    monkeypatch.setattr(once, "_require_entry_blob", lambda entry: {
        "head": "pinned", "entry_blob": "b" * 40, "entry_sha256": "A" * 64})

    class FinishedWorker:
        pid = 5151
        returncode = 0

        def communicate(self, *, timeout):
            check(timeout == once.SUPERVISOR_TIMEOUT_SECONDS)
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
