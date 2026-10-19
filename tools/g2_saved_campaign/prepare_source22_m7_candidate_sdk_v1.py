"""RAM-only, default-off minimal M7 composition over the actual Source22.

Only frozen object reads and source reads are performed.  This module has no
materializer, Git writer, process launcher, Native reader, or deployment CLI.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import prepare_c16_perf_warm_sdk_v1 as exact

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs/ck3-native-ai/evidence"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE_ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src18")
BASE_FREEZE = BASE_ROOT.parent.parent / "robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C22.json"
BASE_PIN = (449181, "07fe7edd6bf76cf7a3c2c438de9d13178ced61c00f1d701b748745f4bc33e443")
BASE_COMMIT = "0722bef48d412ed5e49d0109177493846d988745"
BASE_ROWS_PIN = (372481, "7290b3370b64335b27ff375713dd92de331b0ca114bf99440014d40404593a85")
OLD_PROOF = EVIDENCE / "c18-m7-minimal-cold-sdk-qualification-2026-10-20.json"
OLD_PROOF_PIN = (45511, "f7b415cba9949ce283984ef1cff03e9689e0503acf59e42f80187f059e78b0f4")
EXACT_PIN = (25869, "ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b")
WAL_PATCH = EVIDENCE / "succession-binding-refresh-wal-v1.patch"
WAL_PATCH_PIN = (5800, "23a15c97291a18706fc453347151eda9259204dd3a6ad97d502a3e27410d319c")
DONOR = "36717710ccebefa1c893fc6f7471869e5b9a8f77"
PREFIX = "ck3_autonomous_player/src/"
DRIVER = "xar_autoplayer/bridge/native_driver.py"
RUNTIME = "xar_autoplayer/runtime.py"
EPOCH = "xar_autoplayer/successor_ui_pending_ledger_v1.py"
MCP = "xar_autoplayer/bridge/mcp_server.py"
BASE_DRIVER_PIN = (1640335, "e15fdf47aca82572ff0663d33511e566e9ed6e19a46d22500722058b387f34e2")
A0_WITHOUT_THIN_WAL_PIN = (1638219, "b26db9389bb5e015e5607122c3d0eb8cf66fe828df0e2036419683e3cd6f8eb1")
ALLOWED_DRIVER = {
    "NativeHeadlessGameplayDriver.__init__",
    "NativeHeadlessGameplayDriver._adopt_bridge_session",
    "NativeHeadlessGameplayDriver._execute_campaign_root_context_v1_query",
    "NativeHeadlessGameplayDriver._ingest",
    "NativeHeadlessGameplayDriver._invalidate_player_heir_provider_v1",
    "NativeHeadlessGameplayDriver._mark_bridge_disconnected_v1",
    "NativeHeadlessGameplayDriver.close",
}
OWNED_FILES = (
    REPO / "tools/g2_saved_campaign/prepare_source22_m7_candidate_sdk_v1.py",
    REPO / "tools/g2_saved_campaign/qualify_source22_m7_candidate_sdk_v1.py",
    EVIDENCE / "source22-m7-candidate-sdk-source-plan-2026-10-20.json",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git_read(*args):
    """Only this finite source-object read vocabulary is admitted."""
    exact.require(args and args[0] in ("show", "diff"), "read-only object operation required")
    return subprocess.check_output([
        "git", "-C", str(REPO), "-c", "core.autocrlf=false", *args,
    ])


def read_manifest():
    exact.check_bytes(Path(exact.__file__).read_bytes(), EXACT_PIN, "frozen exact helper")
    raw = exact.check_bytes(BASE_FREEZE.read_bytes(), BASE_PIN, "actual Source22 full freeze")
    doc = json.loads(raw)
    exact.require(doc["machine_id"] == MACHINE and doc["status"] == "FINAL_SOURCE_FROZEN"
                  and doc["business_source_commit"] == BASE_COMMIT
                  and Path(doc["source_root"]).resolve() == BASE_ROOT.resolve()
                  and doc["source_file_count"] == 1449 and doc["source_bytes"] == 59095358,
                  "Source22 source binding differs")
    rows = {}
    for row in doc["files"]:
        name = exact.safe_relative(row["relative"])
        exact.require(name not in rows and row["git_mode"] in ("100644", "100755")
                      and type(row["bytes"]) is int and 0 <= row["bytes"] <= 8 * 1024**2
                      and re.fullmatch("[0-9a-f]{64}", row["sha256"])
                      and re.fullmatch("[0-9a-f]{40}", row["git_blob_sha1"]), "invalid actual source row")
        rows[name] = dict(row)
    exact.require(len(rows) == 1449 and len({n.casefold() for n in rows}) == 1449
                  and sum(r["bytes"] for r in rows.values()) == 59095358, "full base inventory differs")
    exact.check_bytes(canonical([rows[n] for n in sorted(rows)]), BASE_ROWS_PIN, "all1449 canonical rows")
    return doc, rows


def read_base(name, rows):
    path = BASE_ROOT / exact.safe_relative(name)
    exact.require(path.is_file() and not path.is_symlink(), "missing/symlink actual source")
    raw = path.read_bytes()
    row = rows[name]
    exact.check_bytes(raw, (row["bytes"], row["sha256"]), "actual source " + name)
    exact.require(exact.blob_sha(raw) == row["git_blob_sha1"], "actual source blob differs")
    return raw


def inverse_hunks(payload, hunks):
    return exact.transfer_exact_hunks(payload, [(after, before) for before, after in reversed(hunks)])


def frozen_inputs():
    raw = exact.check_bytes(OLD_PROOF.read_bytes(), OLD_PROOF_PIN, "old M7 qualification")
    proof = json.loads(raw)
    exact.require(proof["machine_id"] == MACHINE and len(proof["delta"]) == 12,
                  "frozen M7 source provenance differs")
    old_delta = {r["relative"]: r for r in proof["delta"]}
    new = {n: r["after"] for n, r in old_delta.items() if r["before"] is None}
    operations = proof["operations"]
    exact.require(len(new) == 7 and len(operations) == 14
                  and {r["relative"] for r in operations if r["kind"] == "exact_reversible_committed_hunks"}
                  == {DRIVER, RUNTIME, EPOCH, "xar_autoplayer/bridge/campaign_root_context_contract.py",
                      "xar_autoplayer/bridge/successor_ui_app_owner_v1.py"}, "M7 scope differs")
    return old_delta, new, operations


def read_patch(operation):
    raw = git_read("diff", "--no-ext-diff", "--no-color", "--binary",
                   operation["from_commit"], operation["to_commit"], "--", PREFIX + operation["relative"])
    exact.check_bytes(raw, (operation["patch"]["bytes"], operation["patch"]["sha256"]), "frozen M7 diff")
    hunks = exact.parse_hunks(raw)
    exact.require(len(hunks) == operation["hunk_count"], "M7 hunk count differs")
    return hunks


def dependencies(changed, rows):
    result = {}
    for name, raw in sorted(changed.items()):
        package = name[:-3].replace("/", ".").rpartition(".")[0]
        found = set()
        for node in ast.walk(ast.parse(raw)):
            modules = []
            if isinstance(node, ast.ImportFrom) and node.level:
                module = importlib.util.resolve_name("." * node.level + (node.module or ""), package)
                modules = [module] if node.module else [module + "." + a.name for a in node.names]
            elif isinstance(node, ast.Import):
                modules = [a.name for a in node.names if a.name.startswith("xar_autoplayer.")]
            for module in modules:
                candidates = (module.replace(".", "/") + ".py", module.replace(".", "/") + "/__init__.py")
                match = next((p for p in candidates if p in rows), None)
                exact.require(match is not None, "missing full-tree dependency " + module)
                found.add(match)
        result[name] = sorted(found)
    return result


def compose(*, verify_all_base=True):
    """Return twelve changed bytes, complete1456 rows and a source-only proof."""
    base, indexed = read_manifest()
    old_delta, new, operations = frozen_inputs()
    originals = {name: read_base(name, indexed) for name, r in old_delta.items() if r["before"] is not None}
    exact.check_bytes(originals[DRIVER], BASE_DRIVER_PIN, "actual Source22 Driver")
    for name, raw in originals.items():
        if name != DRIVER:
            before = old_delta[name]["before"]
            exact.check_bytes(raw, (before["bytes"], before["sha256"]), "unchanged M7 preimage " + name)
    changed = {}
    for name, row in sorted(new.items()):
        exact.require(name not in indexed, "M7 new leaf already present")
        raw = git_read("show", DONOR + ":" + PREFIX + name)
        exact.check_bytes(raw, (row["bytes"], row["sha256"]), "frozen independent M7 leaf")
        exact.require(exact.blob_sha(raw) == row["git_blob_sha1"], "M7 new blob differs")
        changed[name] = raw
    applied = []
    driver_hunks = []
    per_file_hunks = {}
    for operation in operations:
        if operation["kind"] != "exact_reversible_committed_hunks":
            continue
        name = operation["relative"]
        hunks = read_patch(operation)
        before = changed.get(name, originals[name])
        changed[name] = exact.transfer_exact_hunks(before, hunks)
        per_file_hunks.setdefault(name, []).extend(hunks)
        if name == DRIVER:
            driver_hunks.extend(hunks)
        applied.append({"relative": name, "from_commit": operation["from_commit"],
                        "to_commit": operation["to_commit"], "patch": operation["patch"],
                        "hunks": len(hunks), "entire_leaf_inverse": True})
    exact.require(len(changed) == 12 and len(per_file_hunks) == 5, "seven new plus five changed required")
    for name, hunks in per_file_hunks.items():
        exact.require(inverse_hunks(changed[name], hunks) == originals[name], "complete M7 inverse differs")
        if name != DRIVER:
            row = old_delta[name]["after"]
            exact.check_bytes(changed[name], (row["bytes"], row["sha256"]), "qualified non-Driver M7 output")

    # Remove only the already-qualified Source22 thin-WAL patch, leaving a0.
    # Apply the same full M7 hunks, then WAL: this independently exercises the
    # shared __init__ domain and proves equality of the entire Driver output.
    wal_raw = exact.check_bytes(WAL_PATCH.read_bytes(), WAL_PATCH_PIN, "Source22 thin-WAL patch")
    wal_header = ("--- a/" + PREFIX + DRIVER + "\n+++ b/" + PREFIX + DRIVER + "\n").encode()
    exact.require(wal_raw.startswith(wal_header) and wal_raw.count(b"--- a/") == 1
                  and wal_raw.count(b"+++ b/") == 1, "one frozen thin-WAL file required")
    # This frozen producer used difflib's ordinary two-line header. Adapt only
    # that exact pinned input to the existing strict Git-hunk parser in RAM.
    wal_hunks = exact.parse_hunks(("diff --git a/" + PREFIX + DRIVER + " b/" + PREFIX + DRIVER + "\n").encode() + wal_raw)
    without_wal = inverse_hunks(originals[DRIVER], wal_hunks)
    exact.check_bytes(without_wal, A0_WITHOUT_THIN_WAL_PIN, "Source22 a0 without thin WAL")
    other_order = exact.transfer_exact_hunks(exact.transfer_exact_hunks(without_wal, driver_hunks), wal_hunks)
    exact.require(other_order == changed[DRIVER], "M7/WAL application orders differ")
    exact.require(inverse_hunks(inverse_hunks(changed[DRIVER], wal_hunks), driver_hunks) == without_wal,
                  "reverse WAL then M7 differs")
    before_asts = exact.function_asts(originals[DRIVER])
    after_asts = exact.function_asts(changed[DRIVER])
    modified = sorted(k for k in set(before_asts) | set(after_asts) if before_asts.get(k) != after_asts.get(k))
    exact.require(set(modified) == ALLOWED_DRIVER, "non-owned Driver function AST changed")
    runtime_before = exact.function_asts(originals[RUNTIME])
    runtime_after = exact.function_asts(changed[RUNTIME])
    runtime_modified = sorted(k for k in set(runtime_before) | set(runtime_after)
                              if runtime_before.get(k) != runtime_after.get(k))
    exact.require(runtime_modified == ["_apply_pre_native_resume_v1", "launch"], "unowned Runtime change")
    if verify_all_base:
        for name in indexed:
            if name not in originals:
                read_base(name, indexed)
    rows = {n: dict(r) for n, r in indexed.items()}
    delta = []
    for name, raw in sorted(changed.items()):
        compile(raw, name, "exec", dont_inherit=True)
        before = rows.get(name)
        row = {"relative": name, **exact.pin(raw), "git_blob_sha1": exact.blob_sha(raw),
               "git_mode": before["git_mode"] if before else "100644"}
        rows[name] = row
        delta.append({"relative": name, "before": before, "after": row,
                      "net_bytes": len(raw) - (before["bytes"] if before else 0)})
    stable = [rows[n] for n in sorted(rows)]
    exact.require(len(stable) == 1456 and len({n.casefold() for n in rows}) == 1456, "complete1456 paths differ")
    untouched = [n for n in indexed if n not in per_file_hunks]
    exact.require(len(untouched) == 1444 and all(rows[n] == indexed[n] for n in untouched), "unchanged source rows differ")
    epoch_names = []
    for node in ast.walk(ast.parse(changed[EPOCH])):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "names" for t in node.targets):
            epoch_names = list(ast.literal_eval(node.value))
    exact.require(epoch_names and all("xar_autoplayer/" + n in rows for n in epoch_names), "epoch dependency missing")
    epoch_inputs = {name: rows["xar_autoplayer/" + name]["sha256"] for name in epoch_names}
    logical = sum(len(raw) for raw in changed.values())
    source_refs = [{"relative": n, **exact.pin(raw)} for n, raw in sorted(changed.items())]
    report = {
        "schema": "xar.source22.minimal-m7-candidate-sdk/v1", "machine_id": MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_source": "py -3 -B tools/ck3_live_run_id.py machine; actual tool c707cc; Source22 freeze agrees; no Game/runtime observation",
        "status": "RAM_SOURCE_CANDIDATE_DEFAULT_OFF_NOT_CANONICAL_NOT_DEPLOYED",
        "base": {"freeze": {"path": str(BASE_FREEZE), **exact.pin(BASE_FREEZE.read_bytes())},
                 "source_root": str(BASE_ROOT), "business_commit": BASE_COMMIT,
                 "files": 1449, "source_bytes": 59095358, "rows": {"bytes": BASE_ROWS_PIN[0], "sha256": BASE_ROWS_PIN[1]}},
        "output": {"files": 1456, "source_bytes": sum(r["bytes"] for r in stable),
                   "canonical_rows_JSON": exact.pin(canonical(stable)), "new": 7, "changed_existing": 5,
                   "unchanged_original_rows": 1444, "changed_source_logical_bytes_each": logical,
                   "prospective_dual4096cluster_data_upper": 2 * sum(((len(v) + 4095) // 4096) * 4096 for v in changed.values())},
        "delta": delta, "exact_M7_operations": applied,
        "Driver_changed_functions": modified, "Runtime_changed_functions": runtime_modified,
        "entire_each_existing_leaf_inverse": True, "M7_then_WAL_equals_WAL_then_M7_entire_Driver": True,
        "WAL_inverse_leaves_exact_a0": {"bytes": A0_WITHOUT_THIN_WAL_PIN[0], "sha256": A0_WITHOUT_THIN_WAL_PIN[1]},
        "non_owned_Driver_function_ASTs_unchanged": True,
        "all1449_source_bodies_verified": verify_all_base,
        "static_internal_dependency_closure": dependencies(changed, rows),
        "epoch_names": epoch_names, "epoch_inputs_after_final_Driver": epoch_inputs,
        "source_epoch_detached_model": hashlib.sha256(canonical(epoch_inputs)).hexdigest(),
        "source_epoch_actual_filesystem_authority": False,
        "retained": ["all Source20 typed ROOT/shared once budget/bounded diagnostics/audit/family",
                     "all Source21 five outputs including durable receipt", "Source22 WAL thin and exact-clock error DTO",
                     "original WAL persistence/barriers and same-speed behavior", "Native29 historical metadata"],
        "not_included": ["old C19 M2 finite", "old bounded-multiday WAL", "any other master leaf", "any controls or Native30 bytes"],
        "controls_separate": "Future genuine enabled custody graph, preserve C22 child WAL env; then-bound source/entry pins and epoch. No disabled timing graph substitution.",
        "Native_transition": "Separate new finite09-FAILED-child-facts plus actual11-artifact protocol required; never relabel08B or09. No Native metadata issuer here.",
        "actual_H": "unknown", "actual_loaded_provider": False, "clock_root_cause": "UNKNOWN; diagnostic only",
        "source_participation": {"twelve_output_refs_RAM_only": source_refs, "twelve_output_logical_bytes": logical,
                                 "new_three_source_hard_bytes": 98304, "logical_payload_plus_new_source_hard_upper": logical + 98304,
                                 "logical_participation_hard_bytes": 2621440,
                                 "shared_original_inputs": "Existing src18/Native29 freeze, old M7 proof/helper and frozen Git objects retained under original cards; no second source tree/candidate copy",
                                 "physical_RAM_peak_bytes": None,
                                 "RAM_limit_claim": "2.5MiB is the logical participating-source envelope, not measured interpreter/AST resident memory; transient original/output/AST buffers are not disk allocation",
                                 "scratch_files": 0, "new_production_source_copies": 0},
        "operations": {"Git_read_only_show_diff": True, "Git_writes": 0, "SDK_exports": 0,
                       "D_writes": 0, "Game_Task_Native_RPC": 0, "Driver_SAVE_state_body_reads": 0},
        "future_writes_after_freeze": 0,
    }
    exact.require(logical + 98304 <= 2621440, "complete logical source quote exceeds2.5MiB")
    return changed, stable, report


if __name__ == "__main__":
    raise SystemExit("Library only: compose() returns RAM bytes/rows/proof; no writer or materializer")
