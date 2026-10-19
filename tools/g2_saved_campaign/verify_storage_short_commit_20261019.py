"""One bounded source/owned-lock qualification; no production bus or assets."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
from audit_storage_lock_boundaries import inventory

B = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01")
PROOF = REPO / "docs/maintenance/evidence/2026-10-19-storage-short-commit-qualification.json"
RETIRED = REPO / "docs/maintenance/evidence/2026-10-19-storage-retired-lock-producers.json"
FIXTURE = REPO / ".task-tmp/storage-short-commit-20261019"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_new(path, value, cap):
    raw = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(raw) > cap:
        raise ValueError("small qualification output cap exceeded")
    with path.open("xb") as stream:
        stream.write(raw)
    return pin(path)


def main():
    if FIXTURE.exists() or PROOF.exists():
        raise FileExistsError("single owned qualification attempt already exists")
    prior_draft = None
    if RETIRED.exists():
        prior_draft = pin(RETIRED)
        if prior_draft["sha256"] != "2595dc815bcf88d019782d7f55a330ceab8eb2cf83c974aa3c2b523e92f3039c":
            raise ValueError("unexpected prior source inventory")
        retired = json.loads(RETIRED.read_bytes())
    machine = subprocess.run([sys.executable, "-B", str(TOOLS / "ck3_live_run_id.py"), "machine"],
                             capture_output=True, text=True, check=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186":
        raise ValueError("this incident qualification belongs to another machine")
    FIXTURE.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               XAR_STORAGE_LOCK_TEST_ROOT=str(FIXTURE))
    suites = []
    for name in ("test_storage_short_commit", "test_storage_retention_inspect", "test_storage_retention_daily_local"):
        run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tools",
                              "-p", name + ".py", "-v"], cwd=REPO, env=env,
                             capture_output=True, text=True, timeout=40)
        output = run.stdout + run.stderr
        if len(output.encode("utf-8")) > 8192:
            raise ValueError("bounded test output exceeded 8 KiB")
        suites.append({"suite": name, "returncode": run.returncode, "output": output})
        if run.returncode:
            failure = {"machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                       "status": "ACTUAL_FIRST_QUALIFICATION_RED", "suites": suites}
            write_new(FIXTURE / "FIRST-RED.json", failure, 12288)
            print(json.dumps(failure, ensure_ascii=False))
            return run.returncode
    if prior_draft is None:
        retired = inventory(B)
        retired.update(machine_id=machine, observed_at_utc=datetime.now(timezone.utc).isoformat())
    rows = retired.pop("retired_direct_global_lock_producers")
    retired["retired_producer_columns"] = ["name", "sha256", "bus_lock_lines"]
    retired["retired_producers"] = [[r["name"], r["sha256"], r["bus_lock_lines"]] for r in rows]
    if prior_draft is None:
        retired_pin = write_new(RETIRED, retired, 24576)
    else:
        # The first unsealed formatted draft caused aggregate-budget refusal.
        # Keep its exact former pin in the qualification and retain the same
        # complete source inventory as compact columns, without duplicate data.
        raw_retired = (json.dumps(retired, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if len(raw_retired) > 24576:
            raise ValueError("compact source inventory cap exceeded")
        RETIRED.write_bytes(raw_retired)
        retired_pin = pin(RETIRED)
    source = B / "observe_remaining_account_v13.py"
    adapter_path = TOOLS / "g2_saved_campaign/storage_account_observer_v14.py"
    spec = importlib.util.spec_from_file_location("storage_observer_v14_qualification", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    code = adapter.compile_unlocked_source(source.read_bytes())
    if "bus_lock" in code.co_names:
        raise AssertionError("legacy observer global lock survived")
    new = [TOOLS / "storage_short_commit.py", TOOLS / "test_storage_short_commit.py",
           TOOLS / "audit_storage_lock_boundaries.py", adapter_path, Path(__file__),
           REPO / "docs/maintenance/storage-lock-boundaries.md"]
    changed = [TOOLS / "storage_retention_inspect.py", TOOLS / "test_storage_retention_daily_local.py"]
    deltas = []
    for path in changed:
        relative = path.relative_to(REPO).as_posix()
        old = subprocess.run(["git", "show", "HEAD:" + relative], cwd=REPO,
                             capture_output=True, check=True).stdout
        current = pin(path)
        deltas.append({**current, "before_bytes": len(old),
                       "before_sha256": hashlib.sha256(old).hexdigest(),
                       "net_new_bytes": current["bytes"] - len(old)})
    sources = [pin(path) for path in new]
    remaining = list(FIXTURE.iterdir())
    if remaining:
        raise AssertionError("test temporary state did not self-clean")
    FIXTURE.rmdir()  # Only this newly owned, now empty exact directory.
    rootcause = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c13-auto6356-failure88/display-closed/GAME-SUPERVISOR-EXIT-FROZEN.json")
    result = {
        "schema": "xar.storage.short-commit-lock-boundary-qualification/v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "QUALIFIED_SOURCE_ONLY",
        "incident": {"global_lock": "Z:/.codex-task-bus/.lock first byte",
            "producer": pin(B / "delete_native28_two_derived01.py"),
            "before": pin(B / "NATIVE28-TWO-LARGE-DERIVED-BEFORE01.json"),
            "actual_deletion": pin(B / "NATIVE28-TWO-LARGE-DERIVED-DELETED01.json"),
            "runtime_rootcause": pin(rootcause),
            "recorded_interval_utc": ["2026-10-19T13:48:40.300880+00:00", "2026-10-19T13:49:05.385858+00:00"],
            "lock_entry_timestamp": None, "lock_heartbeat_calls": 0,
            "slow_call": "psutil.process_iter plus per-process cmdline inside global lock",
            "per_process_error_timings": None, "unavailable_count": 175,
            "root_closed_failure_chain": "keeper bus read Err36 -> LOST/UNCERTAIN STOP -> WM_CLOSE/forced Game exit1",
            "acknowledgement": "storage maintenance lock boundary was incorrect; original receipts retained"},
        "suites": suites, "new_source_pins": sources, "changed_source_deltas": deltas,
        "retired_historical_producer_inventory": retired_pin,
        "first_qualification_budget_refusal": {"actual_tests_completed_before_refusal": prior_draft is not None,
            "formal_proof_was_not_written": True, "unsealed_formatted_inventory_historical_pin": prior_draft,
            "fix": "same complete source pins represented as compact columns; no budget expansion or incident receipt mutation"},
        "sealed_observer_base": pin(source), "sealed_observer_lock_removed_by_actual_AST_compile": True,
        "production_observer_executed": False, "production_bus_lock_acquisitions": 0,
        "new_game_or_live_source_mutations": 0, "asset_deletions_or_capacity_scans": 0,
        "actual_owned_temporary_bus_regression": True, "fixture_state_self_cleaned": True,
        "maintenance_remains_paused": True, "producer_closed": True, "future_writes": 0,
        "allocated_bytes": None, "physical_release_credit_bytes": 0,
        "original_budget_review_at_utc": "2026-10-20T01:48:56.993837+00:00",
        "storage_budget_component": "code3", "aggregate_hard_net_new_bytes": 65536,
        "known_net_new_before_this_proof_bytes": sum(row["bytes"] for row in sources) +
            sum(row["net_new_bytes"] for row in deltas) + retired_pin["bytes"]}
    raw = (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if result["known_net_new_before_this_proof_bytes"] + len(raw) > 65536:
        raise ValueError("aggregate 64 KiB source/qualification budget would be exceeded")
    proof_pin = write_new(PROOF, result, 16384)
    print(json.dumps({"proof": proof_pin, "retired": retired_pin,
                      "net_new_bytes": result["known_net_new_before_this_proof_bytes"] + proof_pin["bytes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
