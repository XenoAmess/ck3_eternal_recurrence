"""RAM-only qualification of A05's appended predecessor guard and real sources.

The existing A04 guard is a named seam, not granted qualification here. All
positive predecessor files are read through the actual frozen bounded checker.
Negative wrapper fixtures replace only an already checked unregister payload;
the independent pin-negative case uses the real checker without replacement.
No runtime, Task, Git, screen, Game or large protected body is written/read.
"""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
import prepare_c23_a05_union_v1 as producer


def require(ok, why):
    if not ok:
        raise ValueError(why)


def source_ref(path):
    data = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    observed = datetime.now(timezone.utc).isoformat()
    machine = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "ck3_live_run_id.py"), "machine"],
        check=True, capture_output=True, text=True).stdout.strip()
    require(machine == producer.MACHINE, "actual machine differs")
    source_path = producer.T4 / "root_native30_supervisor_c23.py"
    source = producer.raw(source_path).decode("utf-8-sig")
    tree = ast.parse(source)
    checker = next(node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == "_a03_checked")
    checker_source = ast.get_source_segment(source, checker)
    scope = {"Path": Path, "hashlib": hashlib, "json": json,
             "MACHINE": machine, "require": require,
             "_validate_a04_attempt": lambda args, config: config}
    exec(compile(checker_source, "frozen-A04-bounded-checker-RAM", "exec"), scope)
    real_checker = scope["_a03_checked"]
    exec(compile(producer._guard_source(), "generated-A05-appended-guard-RAM", "exec"), scope)
    launch = producer.checked(producer.ref(producer.T4 / "ROOT-LAUNCH-CONFIG-C23-A04.json"))
    value = copy.deepcopy(launch["cold_attempt"])
    value.update(prior_failure_a04=producer.ref(producer.O / "A04-FAILED-CLOSED-INDEX.json"),
                 prior_failure_a04_unregistered=producer.ref(producer.O / "SUPERVISOR-A04-UNREGISTER.json"))
    removed_ref = value["prior_failure_a04_unregistered"]
    actual_removed = real_checker(removed_ref)
    args = SimpleNamespace(attempt_nonce="f" * 32, task_nonce="e" * 32)
    validate = scope["_validate_a05_attempt"]
    require(validate(args, value) is value, "real pinned two-layer positive failed")
    cases = [{"case": "real-pinned-actual.actual.absent_after", "result": "PASS"}]

    def reject(name, *, receipt=None, config=None, arg=None):
        def fixture_checker(reference, limit=16384):
            checked = real_checker(reference, limit)
            return copy.deepcopy(receipt) if reference == removed_ref and receipt is not None else checked
        scope["_a03_checked"] = fixture_checker if receipt is not None else real_checker
        try:
            validate(arg or args, config or value)
        except (ValueError, TypeError, KeyError) as error:
            cases.append({"case": name, "result": "REJECTED", "diagnostic": str(error)})
        else:
            raise AssertionError("guard accepted negative: " + name)
        finally:
            scope["_a03_checked"] = real_checker

    fixture = copy.deepcopy(actual_removed)
    fixture["actual"]["actual"]["absent_after"] = False
    reject("known-present-task", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["actual"]["actual"]["absent_after"] = "true"
    reject("string-absence-is-not-True", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["actual"]["actual"]["instances"] = 1
    reject("remaining-instance", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["actual"] = fixture["actual"]["actual"]
    reject("shallow-one-layer-receipt", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["actual"]["operation"] = "register"
    reject("wrong-operation", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["actual"]["machine_id"] = "other-machine"
    reject("wrong-inner-machine", receipt=fixture)
    fixture = copy.deepcopy(actual_removed)
    fixture["machine_id"] = "other-machine"
    reject("wrong-outer-machine", receipt=fixture)
    reject("stdout-ACK-failure", receipt={"stdout": json.dumps(actual_removed), "returncode": 1})
    reject("stdout-oversize", receipt={"stdout": "x" * 16385, "returncode": 0})
    fixture_value = copy.deepcopy(value)
    fixture_value["prior_failure_a04_unregistered"]["sha256"] = "0" * 64
    reject("exact-source-pin-mismatch", config=fixture_value)
    closed_index = real_checker(value["prior_failure_a04"])
    closed_ref = next(row for row in closed_index["actual_facts"]
                      if Path(row["path"]).name == "ROOT-FRESH-SUPERVISOR-CLOSED-C23-A04.json")
    closed = real_checker(closed_ref)
    reject("old-attempt-nonce", arg=SimpleNamespace(
        attempt_nonce=closed["attempt_nonce"], task_nonce="e" * 32))
    source_values, review = producer.build_sources()
    for name, data in source_values.items():
        compile(data, name, "exec")
    require(len(source_values) == 89 and review["source_count"] == 86,
            "real source closure count differs")
    state = producer.state_guard()
    result = {
        "schema": "xar.C23-A05-union-guard-RAM-qualification/v1",
        "machine_id": machine, "observed_at_utc": observed,
        "status": "APPENDED_GUARD_AND_REAL_SOURCE_RAM_PASS",
        "producer": source_ref(producer.__file__), "qualification_script": source_ref(__file__),
        "unregister_actual": removed_ref, "failure_index_actual": value["prior_failure_a04"],
        "bounded_checker_source": source_ref(source_path), "cases": cases,
        "real_source_count": len(source_values),
        "source_logical_bytes": sum(map(len, source_values.values())),
        "generated_supervisor": {"bytes": len(source_values["root_native30_supervisor_c23.py"]),
                                 "sha256": hashlib.sha256(source_values["root_native30_supervisor_c23.py"]).hexdigest()},
        "state_guard": state,
        "scope": {"existing_A04_guard": "named upstream seam; not requalified",
                  "positive_payloads": "actual pinned files via frozen bounded checker",
                  "negative_payloads": "RAM replacements after real pin validation, except pin-negative",
                  "full_compose_or_cold_owner": "NOT_RUN",
                  "Task_Game_RPC_calls": 0, "runtime_or_Git_writes": 0,
                  "large_input_hash_bytes_read": 0},
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
