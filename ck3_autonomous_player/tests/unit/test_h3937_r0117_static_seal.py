"""Offline fixture tests for the a14 pure-file seal (normal and Python -O)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "src" / "xar_autoplayer" / "h3937_r0117_static_seal.py"
SPEC = importlib.util.spec_from_file_location("h3937_r0117_static_seal_under_test", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("static seal module unavailable")
seal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seal)


def check(value: bool) -> None:
    if not value:
        raise AssertionError("test condition failed")


def _put(path: Path, data: bytes = b"fixture") -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest().upper()


def _put_json(path: Path, value: dict) -> str:
    return _put(path, (json.dumps(value, sort_keys=True) + "\n").encode())


def _fixture(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path]:
    checkout = tmp_path / "checkout"
    no_launch = tmp_path / "no-launch" / "attempt-14"
    output_root = tmp_path / "seals"
    game = tmp_path / "game"
    python = tmp_path / "python.exe"
    live_root = tmp_path / "live"
    head = "a" * 40
    run_id = "desktop-test--vanilla--R0117"
    execution_id = "test-execution"
    _put(checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "producer.py", b"producer")
    producer_blob = seal._blob(checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "producer.py")
    source = {"producer_module": ("producer.py", producer_blob)}
    entry_paths = {
        "ck3_autonomous_player/h3937_cold_observer_once.py": b"entry",
        "ck3_autonomous_player/src/xar_autoplayer/h3937_cold_observer_once_enable.py": b"enable",
        "tools/codex_task_bus.py": b"bus",
    }
    entries = {}
    for relative, raw in entry_paths.items():
        path = checkout / relative
        _put(path, raw)
        entries[relative] = seal._blob(path)
    bus_sha = seal._sha(checkout / "tools" / "codex_task_bus.py")
    dll_sha = _put(no_launch / "source-verified" / "xar_ck3_bridge.dll", b"dll")
    injector_sha = _put(no_launch / "source-verified" / "xar_ck3_bridge_injector.exe", b"injector")
    checkpoint_sha = _put(no_launch / "source-verified" / "xar_checkpoint.ck3", b"save")
    raw_driver_sha = _put(no_launch / "source-verified" / "driver-state.json", b"raw-driver")
    sidecar_sha = _put(no_launch / "source-verified" / "player-child-matrilineal-formal-v1.json", b"sidecar")
    game_sha = _put(game / "binaries" / "ck3.exe", b"game")
    _put(no_launch / "state" / "profile" / "save games" / "xar_checkpoint.ck3", b"save")
    _put(no_launch / "state" / "player-child-matrilineal-formal-v1.json", b"sidecar")
    prepared_driver = {"format_version": 2, "pipe_name": seal.PIPE,
                       "episode_run_id": "native-29829-2bc2d599f7f9",
                       "episode_character_id": 29829,
                       "last_checkpoint": {"sha256": checkpoint_sha,
                                           "date_raw": 53219928, "history_index": 3937}}
    prepared_driver_sha = _put_json(no_launch / "state" / "native-session" / "driver-state.json", prepared_driver)
    environment_sha = _put_json(no_launch / "state" / "profile" / "xar-autoplayer-environment.json",
                                {"format_version": 1, "agent_runtime": {"file_count": 1,
                                                                          "files": [{"path": "agent.py"}]}})
    state = no_launch / "state"
    identity = {"schema": "xar.ck3-live-run-identity.v1", "run_id": run_id,
                "execution_id": execution_id, "machine_id": "desktop-3fevhd2-1c74096080",
                "mod_key": "vanilla", "sequence": 117}
    identity_sha = _put_json(no_launch / "live-run-identity.json", identity)
    probe = {"schema": "xar.war.h3937-a14-interpreter-dependency-probe.v1",
             "candidate_head": head,
             "environment": {"python": str(python), "python_version": "Python 3.14.7"}}
    probe_sha = _put_json(no_launch / "interpreter-probe.json", probe)
    source_validation = {
        "schema": "xar.war.h3937-combined-no-launch-source-validation.v1",
        "candidate_head": head, "candidate_clean": True, "live_run_id": run_id,
        "live_run_identity_sha256": identity_sha, "interpreter_probe_sha256": probe_sha,
        "screen_lease_acquired": False, "steam_fresh_offline_reviewed": False,
        "source": {name: {"sha256": digest} for name, digest in (
            ("xar_checkpoint.ck3", checkpoint_sha), ("driver-state.json", raw_driver_sha),
            ("player-child-matrilineal-formal-v1.json", sidecar_sha),
            ("xar_ck3_bridge.dll", dll_sha), ("xar_ck3_bridge_injector.exe", injector_sha))}}
    _put_json(no_launch / "source-validation.json", source_validation)
    rebind = {"schema": "xar.ck3.ordinary-seed-rebind/v1",
              "ok": True, "status": "rebound", "ck3_launch_attempted": False,
              "desktop_interaction": False, "pipe_name": seal.PIPE,
              "state_dir": str(state), "environment": {"target_sha256": environment_sha},
              "driver_state": {"target_sha256": prepared_driver_sha}}
    rebind_sha = _put_json(state / "ordinary-seed-rebind-v1.json", rebind)
    lifecycle = {"lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
                 "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                 "environment_sha256": environment_sha}
    preflight = {"format_version": 1, "kind": "ck3_native_one_generation_preflight",
                 "ok": True, "status": "ready", "ck3_launch_attempted": False,
                 "desktop_interaction": False, "process_inventory": {"processes": []},
                 "resume_anchor": {"checkpoint": {"saved_date_raw": 53219928,
                                                   "history_index": 3937,
                                                   "succession_lifecycle": lifecycle},
                                   "driver_state": {"episode_run_id": "native-29829-2bc2d599f7f9",
                                                    "episode_character_id": 29829,
                                                    "succession_lifecycle": lifecycle}},
                 "profile": {"environment_sha256": environment_sha,
                             "ck3_executable_sha256": game_sha}}
    preflight_path = state / "preflights" / "new" / "report.json"
    preflight["report_path"] = str(preflight_path)
    preflight["pipe"] = seal.PIPE
    preflight_sha = _put_json(preflight_path, preflight)
    admission = {
        "schema": "xar.war.h3937-cold-observer-disabled-no-launch-admission.v1",
        "candidate_head": head, "candidate_checkout_clean": True,
        "live_run_id": run_id, "live_run_identity_sha256": identity_sha,
        "task_bus_cli_sha256": bus_sha, "cold_load_observer_default_off": True,
        "cold_load_observer_live_enabled": False, "ck3_launch_attempted": False,
        "interpreter_probe_sha256": probe_sha, "prepared_state": str(state),
        "episode_run_id": "native-29829-2bc2d599f7f9", "actor": 29829,
        "date_raw": 53219928, "history_index": 3937,
        "dll_sha256": dll_sha, "injector_sha256": injector_sha,
        "raw_driver_sha256": raw_driver_sha,
        "prepared_driver_sha256": prepared_driver_sha,
        "environment_sha256": environment_sha,
        "official_rebind_receipt_sha256": rebind_sha,
        "official_preflight_report": str(preflight_path),
        "official_preflight_report_sha256": preflight_sha,
        "combined_outer_hard_gate": False, "combined_inner_hard_gate": False,
        "target_inner_hard_gate": False, "live_authorized": False,
        "screen_lease_acquired": False, "fresh_steam_offline_proven": False,
        "date_move_attack_authorized": False}
    manifest = {
        "schema": "xar.war.h3937-cold-observer-disabled-operator-manifest.v1",
        "candidate_head": head, "candidate_checkout": str(checkout), "candidate_clean": True,
        "live_run_id": run_id, "live_run_identity_sha256": identity_sha,
        "task_bus_cli_sha256": bus_sha, "cold_load_observer_default_off": True,
        "cold_load_observer_live_enabled": False, "ck3_launch_attempted": False,
        "source_git_blobs": {"producer_module": producer_blob},
        "python": str(python), "python_version": "Python 3.14.7",
        "interpreter_probe_sha256": probe_sha,
        "state_dir": str(state), "bridge_pipe": seal.PIPE,
        "bridge_dll": str(no_launch / "source-verified" / "xar_ck3_bridge.dll"),
        "bridge_injector": str(no_launch / "source-verified" / "xar_ck3_bridge_injector.exe"),
        "game_dir": str(game), "game_exe_sha256": game_sha,
        "outer_hard_gate": False, "inner_hard_gate": False, "target_hard_gate": False,
        "episode_run_id": "native-29829-2bc2d599f7f9", "episode_character_id": 29829,
        "date_raw": 53219928, "history_index": 3937,
        "bridge_dll_sha256": dll_sha, "bridge_injector_sha256": injector_sha,
        "source_checkpoint_sha256": checkpoint_sha,
        "source_raw_driver_sha256": raw_driver_sha,
        "source_child_sidecar_sha256": sidecar_sha,
        "prepared_driver_sha256": prepared_driver_sha,
        "environment_sha256": environment_sha,
        "rebind_receipt_sha256": rebind_sha, "preflight_report_sha256": preflight_sha,
        "live_output_created": False, "screen_lease_acquired": False,
        "fresh_steam_offline_proven": False, "date_move_attack_authorized": False}
    _put_json(no_launch / "admission.json", admission)
    _put_json(no_launch / "operator-manifest.json", manifest)
    allocator = tmp_path / "allocator"
    allocator_stdout = allocator / "allocator-stdout.json"
    allocator_stdout_sha = _put_json(allocator_stdout, identity)
    allocator_command = allocator / "allocator-command.json"
    allocator_command_sha = _put_json(allocator_command, {
        "argv": [str(python), "allocator.py", "allocate", "--mod", "vanilla"],
        "candidate_head": "e7a1849b5455ef5ee31564a9b27f6472fa88770c"})
    allocations = allocator / "allocations.jsonl"
    allocations.write_text("{}\n" * 116 + json.dumps(identity, sort_keys=True) + "\n",
                           encoding="utf-8")
    counter = allocator / "counter.json"
    _put_json(counter, {"schema": "xar.ck3-live-run-counter.v1",
                        "last_sequence": 117, "last_run_id": run_id})
    statuses = allocator / "statuses.jsonl"
    _put(statuses, b"")
    producers = {}
    for label, name in (("operator_script", "a14-operator.py"),
                        ("command_receipt", "a14-command.json"),
                        ("postcheck_receipt", "a14-postcheck.json")):
        path = no_launch.parent / name
        producers[label] = (path, _put(path, name.encode()))
    frozen = {
        "admission.json": seal._sha(no_launch / "admission.json"),
        "operator-manifest.json": seal._sha(no_launch / "operator-manifest.json"),
        "live-run-identity.json": seal._sha(no_launch / "live-run-identity.json"),
        "source-validation.json": seal._sha(no_launch / "source-validation.json"),
        "interpreter-probe.json": seal._sha(no_launch / "interpreter-probe.json"),
        "state/native-session/driver-state.json": prepared_driver_sha,
        "state/profile/xar-autoplayer-environment.json": environment_sha,
        "state/ordinary-seed-rebind-v1.json": rebind_sha,
        "state/preflights/report.json": preflight_sha,
    }
    for name, value in (("HEAD", head), ("RUN_ID", run_id), ("EXECUTION_ID", execution_id),
                        ("SOURCE_BLOBS", source), ("ENTRY_BLOBS", entries),
                        ("BUS_SHA256", bus_sha), ("DLL_SHA256", dll_sha),
                        ("INJECTOR_SHA256", injector_sha),
                        ("CHECKPOINT_SHA256", checkpoint_sha),
                        ("RAW_DRIVER_SHA256", raw_driver_sha),
                        ("SIDECAR_SHA256", sidecar_sha), ("GAME_SHA256", game_sha),
                        ("NO_LAUNCH", no_launch), ("OUTPUT_ROOT", output_root),
                        ("LIVE_ROOT", live_root), ("GAME", game), ("PYTHON", python)):
        monkeypatch.setattr(seal, name, value)
    for name, value in (("ALLOCATOR_STDOUT", allocator_stdout),
                        ("ALLOCATOR_STDOUT_SHA256", allocator_stdout_sha),
                        ("ALLOCATOR_COMMAND", allocator_command),
                        ("ALLOCATOR_COMMAND_SHA256", allocator_command_sha),
                        ("ALLOCATIONS", allocations),
                        ("ALLOCATOR_COUNTER", counter),
                        ("ALLOCATOR_STATUSES", statuses),
                        ("FROZEN_A14_SHA256", frozen),
                        ("FROZEN_A14_PRODUCER", producers)):
        monkeypatch.setattr(seal, name, value)
    monkeypatch.setattr(seal, "_head", lambda path: head)
    return checkout, no_launch, output_root


def test_frozen_contract_has_all_six_read_sources() -> None:
    check(len(seal.SOURCE_BLOBS) == 16)
    check("source_module_.h3937_combined_readonly_queries" in seal.SOURCE_BLOBS)
    check("source_module_.h3937_target_readonly_queries" in seal.SOURCE_BLOBS)
    check("source_module_.bridge.h3937_date_hold" in seal.SOURCE_BLOBS)
    check("subprocess" not in Path(seal.__file__).read_text(encoding="utf-8"))


def test_static_seal_never_grants_live(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STATIC_SEALED")
    check(result["maximum_query_actions_if_later_authorized"] == 6)
    check(result["query_actions"] == 0)
    check(result["go_created"] is False)
    check(result["worker_created"] is False)
    check(result["live_authorized"] is False)
    check(result["ck3_launch_attempted"] is False)
    check(not (tmp_path / "live").exists())
    with pytest.raises(FileExistsError):
        seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)


@pytest.mark.parametrize("mutation,expected", [
    ("source", "source blob"), ("manifest", "SHA-256"),
    ("allocator", "SHA-256"), ("sidecar", "SHA-256"),
    ("observer", "SHA-256"), ("preflight", "preflight"),
])
def test_mutations_stop_before_any_live_action(monkeypatch, tmp_path, mutation, expected) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    if mutation == "source":
        _put(checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "producer.py", b"changed")
    elif mutation == "manifest":
        path = no_launch / "operator-manifest.json"
        item = seal._json(path)
        item["source_git_blobs"] = {}
        _put_json(path, item)
    elif mutation == "allocator":
        path = no_launch / "live-run-identity.json"
        item = seal._json(path)
        item["sequence"] = 116
        _put_json(path, item)
    elif mutation == "sidecar":
        _put(no_launch / "state" / "player-child-matrilineal-formal-v1.json", b"changed")
    elif mutation == "observer":
        path = no_launch / "admission.json"
        item = seal._json(path)
        item["cold_load_observer_live_enabled"] = True
        _put_json(path, item)
    else:
        path = no_launch / "state" / "preflights" / "new" / "report.json"
        item = seal._json(path)
        item["status"] = "blocked"
        _put_json(path, item)
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check(expected in result["reason"])
    check(result["worker_created"] is False)
    check(not (tmp_path / "live").exists())


def test_missing_official_a14_and_prior_attempt_refused(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="attempt-14"):
        seal.verify(checkout, no_launch.parent / "attempt-13")
    (no_launch / "admission.json").unlink()
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check(result["go_created"] is False)


def test_output_must_be_external_and_fresh(monkeypatch, tmp_path) -> None:
    checkout, no_launch, _ = _fixture(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="external"):
        seal.seal_attempt(no_launch / "attempt-01", checkout, no_launch)
    check(not (no_launch / "attempt-01").exists())


def test_unsafe_marker_blocks_seal(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    _put(no_launch / "state" / "control" / "unsafe-cleanup.json", b"unsafe")
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("unsafe native cleanup marker" in result["reason"])


def test_admission_change_during_final_readback_blocks_seal(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    original_sha = seal._sha
    admission_path = no_launch / "admission.json"
    calls = 0

    def mutate_before_readback(path: Path) -> str:
        nonlocal calls
        if path == admission_path:
            calls += 1
            if calls == 2:
                with path.open("ab") as stream:
                    stream.write(b"changed after validation")
        return original_sha(path)

    monkeypatch.setattr(seal, "_sha", mutate_before_readback)
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("SHA-256 differs" in result["reason"])


def test_unreviewed_a14_proof_freeze_stops_even_valid_fixture(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    monkeypatch.setattr(seal, "FROZEN_A14_SHA256", None)
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("proof SHA-256 freeze is absent" in result["reason"])


def test_self_consistent_bad_rebind_nested_type_still_writes_stop(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    rebind_path = no_launch / "state" / "ordinary-seed-rebind-v1.json"
    rebind = seal._json(rebind_path)
    rebind["environment"] = []
    new_sha = _put_json(rebind_path, rebind)
    for name, field in (("admission.json", "official_rebind_receipt_sha256"),
                        ("operator-manifest.json", "rebind_receipt_sha256")):
        path = no_launch / name
        value = seal._json(path)
        value[field] = new_sha
        _put_json(path, value)
        seal.FROZEN_A14_SHA256[name] = seal._sha(path)
    seal.FROZEN_A14_SHA256["state/ordinary-seed-rebind-v1.json"] = new_sha
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("AttributeError" in result["reason"])
    check((output_root / "attempt-01" / "seal.json").is_file())


def test_self_consistent_non_json_prepared_driver_still_stops(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    driver_path = no_launch / "state" / "native-session" / "driver-state.json"
    new_sha = _put(driver_path, b"not JSON")
    for name in ("admission.json", "operator-manifest.json"):
        path = no_launch / name
        value = seal._json(path)
        value["prepared_driver_sha256"] = new_sha
        _put_json(path, value)
        seal.FROZEN_A14_SHA256[name] = seal._sha(path)
    seal.FROZEN_A14_SHA256["state/native-session/driver-state.json"] = new_sha
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("JSONDecodeError" in result["reason"])


def test_hardlinked_source_input_stops(monkeypatch, tmp_path) -> None:
    checkout, no_launch, output_root = _fixture(monkeypatch, tmp_path)
    source = checkout / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "producer.py"
    os.link(source, source.with_name("other-hardlink.py"))
    result = seal.seal_attempt(output_root / "attempt-01", checkout, no_launch)
    check(result["status"] == "STOP_INPUTS_INVALID")
    check("hardlinked input" in result["reason"])
