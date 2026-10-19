"""Qualify the existing default-off WAL with bounded synthetic files only.

Does not install its patches, enable a runtime, dispatch an action, or read a
runtime Driver/SAVE. The work root must be a freshly admitted exact directory.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ck3_autonomous_player"
EXPERIMENT = PROJECT / "experimental/driver_state_wal_v1"
SRC = PROJECT / "src/xar_autoplayer"
sys.path.insert(0, str(PROJECT / "src"))
MAX_PEAK = 64 * 1024 * 1024


def require(condition, message=None):
    """Keep offline software acceptance checks active under Python -O."""
    if not condition:
        if message is None:
            raise AssertionError
        raise AssertionError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pinned_source(commit, relative):
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)


def prepare_driver(work, label, patch_bytes):
    leaf = work / label
    target = leaf / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
    target.parent.mkdir(parents=True)
    shutil.copyfile(SRC / "bridge/native_driver.py", target)
    patch_path = leaf / "driver.patch"
    patch_path.write_bytes(patch_bytes)
    subprocess.run(["git", "apply", str(patch_path)], cwd=leaf, check=True, capture_output=True)
    return load(f"xar_autoplayer.bridge.native_driver_wal_{label}", target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--resume-existing", action="store_true",
                        help="finish the existing closed synthetic pair without repeating writes or negative controls")
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    admission_bytes = args.admission.read_bytes()
    admission = json.loads(admission_bytes)
    # Exact admitted root and machine must be recorded in the frozen child receipt.
    if machine not in admission_bytes.decode("utf-8-sig") or args.work_root.as_posix().lower() not in admission_bytes.decode("utf-8-sig").replace("\\\\", "/").replace("\\", "/").lower():
        raise ValueError("admission does not bind this machine and exact work root")
    if args.resume_existing:
        if not args.work_root.is_dir():
            raise ValueError("resume requires the existing admitted synthetic root")
    else:
        args.work_root.mkdir(parents=True, exist_ok=False)
    disk_before = shutil.disk_usage(args.work_root)
    portable = load("wal_portable_qualification", EXPERIMENT / "test_portable.py")
    wal = portable.wal
    original_helper_bytes = pinned_source(args.baseline, "ck3_autonomous_player/experimental/driver_state_wal_v1/driver_state_wal_v1.py")
    original_patch = pinned_source(args.baseline, "ck3_autonomous_player/experimental/driver_state_wal_v1/bridge-native_driver.py.patch")
    helper_path = args.work_root / "original-helper.py"
    if not args.resume_existing:
        helper_path.write_bytes(original_helper_bytes)
    original_wal = load("xar_autoplayer.bridge.driver_state_wal_original_qualification", helper_path)
    if args.resume_existing:
        old_driver = load("xar_autoplayer.bridge.native_driver_wal_original", args.work_root / "original/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")
        candidate = load("xar_autoplayer.bridge.native_driver_wal_candidate", args.work_root / "candidate/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")
    else:
        old_driver = prepare_driver(args.work_root, "original", original_patch)
        candidate = prepare_driver(args.work_root, "candidate", (EXPERIMENT / "bridge-native_driver.py.patch").read_bytes())
    cold_path = args.work_root / "candidate/ck3_autonomous_player/src/xar_autoplayer/native_session.py"
    if not args.resume_existing:
        shutil.copyfile(SRC / "native_session.py", cold_path)
        subprocess.run(["git", "apply", str(EXPERIMENT / "native_session.py.patch")], cwd=args.work_root / "candidate", check=True, capture_output=True)
    cold = load("xar_autoplayer.native_session_wal_qualification", cold_path)

    def make_driver(module, path, enabled=True):
        obj = portable.fake_driver(module, path)
        obj._succession_lifecycle = module.legacy_rogue_one_life_binding_v1()
        obj.allow_driver_state_wal_v1 = enabled
        return obj

    def active_pair(module, path):
        obj = make_driver(module, path)
        obj._persist_driver_state()
        obj._record_command("life-advance-one-day", ok=True, result={"step": "life-advance-one-day"})
        base = obj._native_driver_state_path()
        return obj, base, base.with_name(wal.FILENAME)

    cases = []
    for label, module, helper in (() if args.resume_existing else (("original", old_driver, original_wal), ("candidate", candidate, wal))):
        with patch.dict(sys.modules, {"xar_autoplayer.bridge.driver_state_wal_v1": helper}):
            for fault in ("missing-base", "journal-read-oserror"):
                obj, base, journal = active_pair(module, args.work_root / f"{label}-{fault}")
                initial_history = copy.deepcopy(obj._command_history)
                journal_sha = sha(journal.read_bytes())
                outcome = None
                if fault == "missing-base":
                    base.unlink()  # Exact synthetic file owned by this new work root.
                    try:
                        returned = obj._read_driver_state()
                        outcome = "returned_none" if returned is None else "returned_state"
                    except helper.JournalInvalid:
                        outcome = "JournalInvalid"
                else:
                    original_read = Path.read_bytes
                    def unreadable(path):
                        if path == journal:
                            raise PermissionError("synthetic journal read denied")
                        return original_read(path)
                    with patch.object(Path, "read_bytes", unreadable):
                        try:
                            returned = obj._read_driver_state()
                            outcome = "returned_none" if returned is None else "returned_state"
                        except helper.JournalInvalid:
                            outcome = "JournalInvalid"
                require(outcome == ("returned_none" if label == "original" else "JournalInvalid"))
                require(journal_sha == sha(journal.read_bytes()) and obj._command_history == initial_history)
                cases.append({"source": label, "fault": fault, "observed": outcome,
                              "journal_unchanged": True, "history_unchanged": True})
    empty = make_driver(candidate, args.work_root / "empty-fresh")
    require(empty._read_driver_state() is None)
    cases.append({"source": "candidate", "case": "neither-base-nor-journal", "observed": "legal_fresh_none"})
    full = make_driver(candidate, args.work_root / "full", enabled=False)
    journaled = make_driver(candidate, args.work_root / "journaled", enabled=True)
    seed_rows = [{"index": index, "command": "synthetic-readonly-history", "ok": True,
                  "result": {"opaque_preserved_evidence": "x" * 32768}} for index in range(1, 129)]
    if args.resume_existing:
        full._command_history = json.loads(full._native_driver_state_path().read_bytes())["command_history"]
        journaled._command_history = wal.load_pair(journaled._native_driver_state_path())[0]["command_history"]
    for obj in (() if args.resume_existing else (full, journaled)):
        obj._command_history = copy.deepcopy(seed_rows)
        obj._persist_driver_state()
    samples = {"full": [], "wal": []}
    writes = {"full": [], "wal": []}
    actual_writer = candidate.write_bytes_atomic
    for turn in range(1, 1 if args.resume_existing else 17):
        row = {"index": len(seed_rows) + turn, "command": "life-advance-one-day", "ok": True,
               "result": {"step": "life-advance-one-day", "synthetic_turn": turn},
               "recorded_at_utc": "2000-01-01T00:00:00Z"}
        for label, obj in (("full", full), ("wal", journaled)) if turn % 2 else (("wal", journaled), ("full", full)):
            obj._command_history.append(copy.deepcopy(row))
            obj._driver_state_dirty = True
            def counted(path, payload, **kwargs):
                writes[label].append({"leaf": path.name, "bytes": len(payload)})
                return actual_writer(path, payload, **kwargs)
            tick = time.perf_counter_ns()
            with patch.object(candidate, "write_bytes_atomic", counted):
                obj._persist_driver_state(journal_append=True)
            samples[label].append((time.perf_counter_ns() - tick) / 1e9)
            require(obj._driver_state_error is None)
    full_path, pair_path = full._native_driver_state_path(), journaled._native_driver_state_path()
    recovered, status = wal.load_pair(pair_path)
    require(status == "replayed")
    full_bytes = full_path.read_bytes()
    recovered_bytes = wal.full_state_bytes(recovered)
    full_payload = json.loads(full_bytes)
    canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    require(canonical(recovered) == canonical(full_payload))
    require(recovered["command_history"] == full_payload["command_history"])
    key_order_differences = [index for index, (left, right) in enumerate(zip(full_payload["command_history"], recovered["command_history"]), 1)
                             if list(left) != list(right)]
    strict_resume = journaled._read_driver_state()
    require(strict_resume["command_history"] == journaled._command_history)
    try:
        cold.validate_cold_start_checkpoint_for_pipe(SimpleNamespace(state_dir=journaled.state_dir), journaled.pipe_name)
        raise AssertionError("active pair accepted as a cold checkpoint")
    except cold.AgentError as error:
        require("committed daily journal" in str(error))
    materialized = wal.materialize_closed_directory(journaled.state_dir, args.work_root / "materialized",
        owner_closed=True, expected_base_sha256=sha(pair_path.read_bytes()),
        expected_journal_sha256=sha(pair_path.with_name(wal.FILENAME).read_bytes()))
    materialized_path = Path(materialized["output_path"])
    require(canonical(json.loads(materialized_path.read_bytes())) == canonical(full_payload))
    strict_cold = candidate.load_native_driver_state_for_resume(materialized_path, journaled.pipe_name)
    require(strict_cold["command_history"] == journaled._command_history)
    # A failed publish keeps the one existing history row; no action is sent or repeated.
    row = {"index": len(journaled._command_history) + 1, "command": "life-advance-one-day", "ok": True,
           "result": {"step": "life-advance-one-day", "synthetic_failed_publish": True}}
    journaled._command_history.append(copy.deepcopy(row))
    before_failed_history = copy.deepcopy(journaled._command_history)
    with patch.object(candidate, "write_bytes_atomic", side_effect=OSError("synthetic WAL publish denied")):
        journaled._persist_driver_state(journal_append=True)
    require(journaled._driver_state_dirty and "synthetic WAL publish denied" in journaled._driver_state_error)
    require(journaled._command_history == before_failed_history)
    require(len(wal.load_pair(pair_path)[0]["command_history"]) == len(seed_rows) + 16)
    checkpoint = {"history_index": len(journaled._command_history) + 1,
                  "pipe_name": journaled.pipe_name, "bridge_pid": journaled._session_bridge_pid,
                  "episode_character_id": journaled._episode_character_id, "episode_run_id": journaled._episode_run_id}
    journaled._last_checkpoint = copy.deepcopy(checkpoint)
    save_receipt = journaled._record_command("save-checkpoint", ok=True, result={"checkpoint": checkpoint})
    require(save_receipt["status"] == "replaced" and save_receipt["save_binding_verified"])
    saved, saved_status = wal.load_pair(pair_path)
    require(saved_status == "base_only" and not pair_path.with_name(wal.FILENAME).exists())
    require(saved["command_history"] == journaled._command_history)
    require([row["index"] for row in saved["command_history"]] == list(range(1, len(saved["command_history"]) + 1)))
    require(sum(row["command"] == "save-checkpoint" for row in saved["command_history"]) == 1)
    # Normal close must consolidate an otherwise clean committed journal first.
    journaled._record_command("life-advance-one-day", ok=True, result={"step": "life-advance-one-day"})
    observed_close = []
    journaled.endpoint = SimpleNamespace(close=lambda: observed_close.append(wal.load_pair(pair_path)[1]))
    with patch("xar_autoplayer.bridge.normal_exit_pending_observer_v1.dispose_normal_exit_observer_v1"):
        journaled.close()
    require(observed_close == ["base_only"])
    manifest = []
    for path in sorted(args.work_root.rglob("*")):
        if path.is_file():
            manifest.append({"relative_path": path.relative_to(args.work_root).as_posix(),
                             "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())})
    logical_bytes = sum(item["bytes"] for item in manifest)
    require(logical_bytes <= MAX_PEAK)
    receipt = {"schema": "xar.driver-wal-offline-qualification.v1", "machine_id": machine,
        "observed_started_utc": started.isoformat(), "observed_ended_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPERIMENTAL_SOFTWARE_QUALIFIED_NOT_LIVE_ADOPTED", "baseline_commit": args.baseline,
        "negative_and_candidate_cases": cases,
        "resumed_existing_pair": args.resume_existing,
        "first_attempt": ({"exit_code": 1, "failed_assertion": "wal.full_state_bytes(recovered) == full_bytes",
                           "reason": "canonical journal sorts history object keys; raw textual byte identity is not preserved",
                           "preserved_producer": "PRODUCER-ATTEMPT01.py",
                           "prior_negative_controls": "original missing-base and journal-read-OSError returned None; candidate raised JournalInvalid; these assertions completed before first raw-byte assertion",
                           "prior_writes": "16 exact synthetic rows written in full and WAL branches before first assertion; not repeated",
                           "prior_timing_samples": None} if args.resume_existing else None),
        "preservation": {"full_vs_replay_bytes_equal": recovered_bytes == full_bytes,
                         "full_vs_replay_canonical_bytes_equal": True, "full_vs_replay_all_history_values_equal": True,
                         "history_object_key_order_differences": key_order_differences,
                         "full_json_sha256": sha(full_bytes), "recovered_json_sha256": sha(recovered_bytes),
                         "canonical_full_and_recovered_sha256": sha(canonical(recovered)),
                         "preserved_history_rows_before_save": len(seed_rows) + 16,
                         "strict_driver_resume_history_equal": True, "active_pair_cold_start_rejected": True,
                         "materialized_v2_raw_bytes_equal": materialized_path.read_bytes() == full_bytes,
                         "materialized_v2_all_values_equal": True, "strict_materialized_resume_history_equal": True,
                         "failed_publish_row_not_resent_or_duplicated": True,
                         "synthetic_save_bookkeeping_barrier": save_receipt,
                         "save_row_count": 1, "save_history_contiguous": True,
                         "normal_close_observed_pair_status": observed_close},
        "bounded_synthetic_write_comparison": {"baseline_json_bytes": len(full_bytes), "append_count": 16,
                    "logical_write_bytes": None if args.resume_existing else {key: sum(item["bytes"] for item in value) for key, value in writes.items()},
                    "write_calls": None if args.resume_existing else {key: len(value) for key, value in writes.items()},
                    "elapsed_seconds": None if args.resume_existing else samples,
                    "total_seconds": None if args.resume_existing else {key: sum(value) for key, value in samples.items()},
                    "first_wal_sample_includes_activation": True, "same_history_rows_and_state": True},
        "source_pins": {str(path.relative_to(ROOT)).replace("\\", "/"): {"bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
                        for path in (EXPERIMENT / "driver_state_wal_v1.py", EXPERIMENT / "bridge-native_driver.py.patch",
                                     EXPERIMENT / "native_session.py.patch", SRC / "bridge/native_driver.py", SRC / "native_session.py", Path(__file__))},
        "historical_SOURCE_PINS_and_DELIVERY": "unchanged historical qualification; this receipt supersedes current helper/patch identities only",
        "game_calls": 0, "native_calls": 0, "rpc": 0, "runtime_or_SAVE_bodies_read": 0,
        "production_modified": False, "WAL_enabled_for_runtime": False,
        "limits": ["synthetic small state and bookkeeping SAVE; no actual CK3 SAVE or game acceptance", "write-and-replace returned, not power-loss/fsync durability", "relative local timing cannot predict old 8GB or current runtime throughput", "old direct readers require full v2 materialization; no active pair can be used as a cold checkpoint"],
        "storage": {"policy_version": "1.0.0", "admission_path": str(args.admission), "admission_sha256": sha(admission_bytes),
                    "work_root": str(args.work_root), "peak_budget_bytes": MAX_PEAK, "retained_logical_bytes": logical_bytes,
                    "free_at_start_bytes": disk_before.free, "free_at_close_bytes": shutil.disk_usage(args.work_root).free,
                    "derived_review_at_utc": "2026-10-21T02:32:53Z", "producer_closed": True,
                    "unconsumed_planned_writes_bytes": 0, "unrelated_deletions": 0,
                    "synthetic_exact_deletions": ["original-missing-base/native-session/driver-state.json", "candidate-missing-base/native-session/driver-state.json"],
                    "manifest": manifest}}
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(encoded) <= 1024 * 1024)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes(encoded)
    (args.work_root / "QUALIFICATION.json").write_bytes(encoded)
    print(json.dumps({"receipt": str(args.receipt), "bytes": len(encoded), "retained_logical_bytes": logical_bytes,
                      "logical_writes": receipt["bounded_synthetic_write_comparison"]["logical_write_bytes"],
                      "total_seconds": receipt["bounded_synthetic_write_comparison"]["total_seconds"]}))


if __name__ == "__main__":
    main()
