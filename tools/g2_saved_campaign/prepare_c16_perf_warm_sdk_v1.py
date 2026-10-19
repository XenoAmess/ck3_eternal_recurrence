"""Compose the minimal C16 warm SDK in memory over its actual frozen tree.

No Game/Driver/SAVE body, SDK process or output tree is opened here.  The donor
Driver is never used as a replacement: only exact, uniquely matched reversible
hunks are transferred from pinned commits.  The returned complete manifest is
the original actual manifest plus its explicitly listed small delta.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
PREFIX = "ck3_autonomous_player/src/"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE_FREEZE = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C16.json")
BASE_FREEZE_BYTES = 375121
BASE_FREEZE_SHA = "4d609077db641724096d019d970839e974e293fa07f39a6b369343163647e6b9"
BASE_ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src13")
WAL_PARENT = "f17196cd5557e3b56d61f5f2291d4b9e5da1c0ee"
WAL_COMMIT = "798a28e908e686e69eada051d08d2cb06d73bd5d"
SPEED_COMMIT = "9bd0557b6ab7c05059c7114fe02b508959b38958"
M6_COMMIT = "18c4bfcdac7e7afaff64c2802907d8c9e644b378"
DRIVER = "xar_autoplayer/bridge/native_driver.py"
WAL_FILES = (
    DRIVER,
    "xar_autoplayer/bridge/driver_state_history_json.py",
    "xar_autoplayer/native_session.py",
    "xar_autoplayer/bridge/driver_state_wal_v1.py",
)
SPEED_HELPER = "xar_autoplayer/bridge/exact_day_speed_configuration_v1.py"
PAUSE_HELPER = "xar_autoplayer/war_results_scope_pause_v1.py"
M6_FILES = (
    "xar_autoplayer/bridge/sway_terminal_source_producer_12004.py",
    "xar_autoplayer/sway_lifecycle_consumer.py",
)
M2_FILES = (
    "xar_autoplayer/vanilla_events/event_offline_analysis.py",
    "xar_autoplayer/vanilla_events/reviewed_letter_source_rebind_v1.py",
)
M2_CURRENT = {
    M2_FILES[0]: (28093, "f76ee3f2bb7fb3951da5a4e75533c72fb48a3eff01f860cd31a9518c5766c52f"),
    M2_FILES[1]: (12122, "24d7937aa3d6be34adb1da9fb67eb5536e9494c4615dac810f98f6fae10c98f9"),
}
DONOR_PINS = {
    (WAL_COMMIT, WAL_FILES[1]): (4172, "224f0422a8e17e77b988a0482d6bdd6bdd2d231b74a88031ee8cac991882ee7c"),
    (WAL_COMMIT, WAL_FILES[2]): (76143, "b88e5162902ca5407132e04e23acc9db292cb6b3a35560b09236c14b795eee49"),
    (WAL_COMMIT, WAL_FILES[3]): (23998, "8a738446148f33dd92d0e3489dfb002c675fb50b23e00320df11cbfad855324d"),
    (SPEED_COMMIT, SPEED_HELPER): (3412, "7ae8f53a2bbe1a241c8b6f3f00779cd199f6209155c371a962767b9a7d3a4185"),
    (SPEED_COMMIT, PAUSE_HELPER): (11069, "26f8facdf8235f7ef2a0640044d588351a8aeefc81e2417d487fd3b72b2eb771"),
    (M6_COMMIT, M6_FILES[0]): (18986, "5c33c735f3e5b5a76b1f9498528cf10821d5ff30257aa9846c274cd557feb7f4"),
    (M6_COMMIT, M6_FILES[1]): (19194, "cfa0e5680ec4ca7a6c691c2388f85ce38d1ec9643aa060b244caed460c990353"),
}
BASE_DRIVER = (1620598, "db9f8fb05483146abe1bea7c00d5ec4c53e5fc6a9c370133ba7e8ff7ebedb3da")
EXPECTED_BASE_COUNT = 1443
EXPECTED_BASE_BYTES = 58993449
MAX_SOURCE_BYTES = 64 * 1024**2
MAX_LEAF_BYTES = 4 * 1024**2
MAX_BASE_LEAF_BYTES = 8 * 1024**2


def require(ok, why):
    if not ok:
        raise ValueError("C16 perf warm denied: " + why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(raw):
    return {"bytes": len(raw), "sha256": sha(raw)}


def blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def check_bytes(raw, expected, label):
    require((len(raw), sha(raw)) == expected, label + " bytes/SHA differ")
    return raw


def safe_relative(name):
    require(isinstance(name, str) and "\\" not in name and ":" not in name
            and "\0" not in name, "unsafe relative path")
    rel = PurePosixPath(name)
    require(not rel.is_absolute() and rel.as_posix() == name
            and name not in ("", ".") and not any(p in (".", "..") for p in rel.parts),
            "unsafe relative path")
    return name


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def git_source(commit, relative):
    safe_relative(relative)
    raw = git("show", commit + ":" + PREFIX + relative)
    require(len(raw) <= MAX_LEAF_BYTES, "donor leaf too large")
    expected = DONOR_PINS.get((commit, relative))
    if expected is not None:
        check_bytes(raw, expected, "donor " + relative)
    return raw


def read_actual_manifest():
    raw = BASE_FREEZE.read_bytes()
    check_bytes(raw, (BASE_FREEZE_BYTES, BASE_FREEZE_SHA), "actual C16 manifest")
    doc = json.loads(raw)
    require(doc["schema"] == "root.ck3.final-sdk-freeze/v1"
            and doc["status"] == "FINAL_SOURCE_FROZEN" and doc["machine_id"] == MACHINE
            and Path(doc["source_root"]).resolve() == BASE_ROOT.resolve(), "actual SDK binding differs")
    rows = doc["files"]
    require(len(rows) == EXPECTED_BASE_COUNT == doc["source_file_count"]
            and sum(r["bytes"] for r in rows) == EXPECTED_BASE_BYTES == doc["source_bytes"],
            "actual SDK manifest count/bytes differ")
    indexed = {}
    for row in rows:
        name = safe_relative(row["relative"])
        require(name not in indexed and type(row["bytes"]) is int
                and 0 <= row["bytes"] <= MAX_BASE_LEAF_BYTES
                and re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                and re.fullmatch(r"[0-9a-f]{40}", row["git_blob_sha1"])
                and row["git_mode"] in ("100644", "100755"), "actual SDK row differs")
        indexed[name] = dict(row)
    require(len({n.casefold() for n in indexed}) == len(indexed), "case-colliding SDK paths")
    return doc, indexed


def read_base(relative, indexed):
    row = indexed[relative]
    path = BASE_ROOT / relative
    require(path.is_file() and not path.is_symlink(), "actual source leaf missing/symlink")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BASE_LEAF_BYTES + 1)
    check_bytes(raw, (row["bytes"], row["sha256"]), "actual " + relative)
    require(blob_sha(raw) == row["git_blob_sha1"], "actual Git blob differs: " + relative)
    return raw


def parse_hunks(diff):
    """Parse ordinary one-file Git unified output, preserving exact byte lines."""
    require(isinstance(diff, bytes) and diff.count(b"diff --git ") == 1,
            "one ordinary file diff required")
    lines = diff.splitlines(keepends=True)
    result = []
    old = new = None
    for line in lines:
        if line.startswith(b"@@ "):
            if old is not None:
                result.append((b"".join(old), b"".join(new)))
            require(re.fullmatch(rb"@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@[^\r\n]*\r?\n", line),
                    "ordinary hunk header required")
            old, new = [], []
        elif old is not None:
            require(line[:1] in (b" ", b"-", b"+"), "unsupported diff marker")
            if line[:1] in (b" ", b"-"):
                old.append(line[1:])
            if line[:1] in (b" ", b"+"):
                new.append(line[1:])
    if old is not None:
        result.append((b"".join(old), b"".join(new)))
    require(result and all(a and b and a != b for a, b in result), "empty/unusable hunks")
    return result


def transfer_exact_hunks(original, hunks):
    result = original
    for before, after in hunks:
        require(result.count(before) == 1, "exact hunk context absent or ambiguous")
        result = result.replace(before, after, 1)
    inverse = result
    for before, after in reversed(hunks):
        require(inverse.count(after) == 1, "inverse hunk absent or ambiguous")
        inverse = inverse.replace(after, before, 1)
    require(inverse == original, "hunk inverse changed original bytes")
    return result


def transfer_committed(original, parent, commit, relative):
    before = git_source(parent, relative)
    after = git_source(commit, relative)
    if before == after:
        return original, {"kind": "unchanged_donor", "relative": relative}
    diff = git("diff", "--no-ext-diff", "--no-color", "--unified=3", parent, commit,
               "--", PREFIX + relative)
    hunks = parse_hunks(diff)
    require(transfer_exact_hunks(before, hunks) == after, "donor diff does not reconstruct pinned commit")
    result = transfer_exact_hunks(original, hunks)
    return result, {"kind": "exact_reversible_committed_hunks", "relative": relative,
                    "from_commit": git("rev-parse", parent + "^{commit}").decode().strip(),
                    "to_commit": git("rev-parse", commit + "^{commit}").decode().strip(),
                    "donor_before": pin(before), "donor_after": pin(after),
                    "patch": pin(diff), "hunk_count": len(hunks),
                    "inverse_restores_entire_actual_leaf": True}


def function_asts(raw):
    """Stable top-level/function/class-method AST map, without line positions."""
    tree = ast.parse(raw)
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name + "." + method.name] = ast.dump(method, include_attributes=False)
    return result


def compose(*, construction_pin=None, verify_all_base=True):
    """Return changed bytes, the complete new manifest rows and a small plan.

    construction_pin is deliberately mandatory before READY: callers may inspect
    all other exact changes while the construction source owner is still freezing.
    No source bytes are written by this function.
    """
    base, indexed = read_actual_manifest()
    changed = {}
    operations = []
    original = {}

    def old(name):
        if name not in original:
            original[name] = read_base(name, indexed)
        return original[name]

    check_bytes(old(DRIVER), BASE_DRIVER, "actual Driver")
    for name in WAL_FILES:
        if name not in indexed:
            require(name == WAL_FILES[3], "unexpected missing WAL baseline dependency")
            raw = git_source(WAL_COMMIT, name)
            operations.append({"kind": "new_exact_committed_leaf", "relative": name,
                               "commit": WAL_COMMIT, "after": pin(raw)})
        else:
            raw, operation = transfer_committed(old(name), WAL_PARENT, WAL_COMMIT, name)
            operations.append(operation)
        changed[name] = raw
    changed[DRIVER], operation = transfer_committed(changed[DRIVER], WAL_COMMIT, SPEED_COMMIT, DRIVER)
    operations.append(operation)
    require(SPEED_HELPER not in indexed, "speed helper unexpectedly exists")
    changed[SPEED_HELPER] = git_source(SPEED_COMMIT, SPEED_HELPER)
    operations.append({"kind": "new_exact_committed_leaf", "relative": SPEED_HELPER,
                       "commit": SPEED_COMMIT, "after": pin(changed[SPEED_HELPER])})
    for name in (PAUSE_HELPER, *M6_FILES):
        commit = SPEED_COMMIT if name == PAUSE_HELPER else M6_COMMIT
        donor = git_source(commit, name)
        before = old(name)
        if before == donor:
            operations.append({"kind": "already_present_unchanged", "relative": name,
                               "before": pin(before)})
            continue
        # For independent leaves only, require that applying the exact historical
        # commit delta to the actual leaf reconstructs the complete donor bytes.
        result, operation = transfer_committed(before, commit + "^", commit, name)
        require(result == donor, "independent donor differs outside its exact change: " + name)
        changed[name] = result
        operations.append(operation)
    for name in M2_FILES:
        path = REPO / PREFIX / name
        raw = check_bytes(path.read_bytes(), M2_CURRENT[name], "frozen M2 " + name)
        parent = git_source(SPEED_COMMIT, name)
        require(old(name) == parent, "M2 actual source differs from exact prepatch baseline")
        diff = git("diff", "--no-ext-diff", "--no-color", "--unified=3", SPEED_COMMIT,
                   "--", PREFIX + name)
        result = transfer_exact_hunks(parent, parse_hunks(diff))
        require(result == raw, "M2 exact delta does not reconstruct frozen leaf")
        changed[name] = result
        operations.append({"kind": "exact_reversible_frozen_worktree_hunks", "relative": name,
                           "from_commit": SPEED_COMMIT, "patch": pin(diff),
                           "donor_after": pin(raw), "inverse_restores_entire_actual_leaf": True})
    construction_status = "WAITING_FROZEN_CONSTRUCTION_CONSUMER"
    if construction_pin is not None:
        name = "xar_autoplayer/construction_formal_consumer.py"
        expected = (construction_pin["bytes"], construction_pin["sha256"])
        raw = check_bytes((REPO / PREFIX / name).read_bytes(), expected, "frozen construction consumer")
        parent = git_source(SPEED_COMMIT, name)
        require(old(name) == parent, "construction baseline differs")
        diff = git("diff", "--no-ext-diff", "--no-color", "--unified=3", SPEED_COMMIT,
                   "--", PREFIX + name)
        result = transfer_exact_hunks(parent, parse_hunks(diff))
        require(result == raw, "construction delta does not reconstruct frozen leaf")
        changed[name] = result
        operations.append({"kind": "exact_reversible_frozen_worktree_hunks", "relative": name,
                           "from_commit": SPEED_COMMIT, "patch": pin(diff),
                           "donor_after": pin(raw), "inverse_restores_entire_actual_leaf": True})
        construction_status = "FROZEN_EXACT_DELTA_COMPOSED"
    # All untouched bytes remain original; never use the newest whole Driver.
    driver_before = function_asts(old(DRIVER))
    driver_after = function_asts(changed[DRIVER])
    ast_changed = sorted(k for k in set(driver_before) | set(driver_after)
                         if driver_before.get(k) != driver_after.get(k))
    allowed = {
        "load_native_driver_state_for_resume", "NativeHeadlessGameplayDriver.__init__",
        "NativeHeadlessGameplayDriver._record_command", "NativeHeadlessGameplayDriver._adopt_bridge_session",
        "NativeHeadlessGameplayDriver._read_driver_state", "NativeHeadlessGameplayDriver._persist_driver_state",
        "NativeHeadlessGameplayDriver._route_horizon_wal_eligible_v1",
        "NativeHeadlessGameplayDriver._driver_state_wal_scalar_fields_locked_v1",
        "NativeHeadlessGameplayDriver._try_persist_driver_state_wal_append_v1",
        "NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel",
        "NativeHeadlessGameplayDriver.close",
    }
    require(set(ast_changed) <= allowed, "unexpected Driver method changed: " + repr(set(ast_changed) - allowed))
    # close intentionally gains only the committed WAL flush predicate.  Its
    # original callback/cleanup body is preserved by the exact inverse above;
    # importing the donor's entire method would also import unrelated M7 code.
    for name, raw in changed.items():
        require(len(raw) <= MAX_LEAF_BYTES, "composed leaf too large")
        if name.endswith(".py"):
            compile(raw, name, "exec", dont_inherit=True)
    if verify_all_base:
        for name in indexed:
            old(name)
    rows = {name: dict(row) for name, row in indexed.items()}
    delta = []
    for name, raw in sorted(changed.items()):
        before_row = rows.get(name)
        after_row = {"relative": name, **pin(raw), "git_blob_sha1": blob_sha(raw),
                     "git_mode": before_row["git_mode"] if before_row else "100644"}
        rows[name] = after_row
        delta.append({"relative": name, "before": before_row,
                      "after": after_row, "net_bytes": len(raw) - (before_row["bytes"] if before_row else 0)})
    require(sum(row["bytes"] for row in rows.values()) <= MAX_SOURCE_BYTES, "composed SDK too large")
    stable_rows = [rows[name] for name in sorted(rows)]
    manifest_raw = json.dumps(stable_rows, sort_keys=True, separators=(",", ":")).encode()
    plan = {"schema": "xar.c16.perf-warm-minimal-sdk-composition/v1",
            "machine_id": MACHINE, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "SOURCE_COMPOSITION_READY_NOT_ADMITTED" if construction_pin else construction_status,
            "actual_base_freeze": {"path": str(BASE_FREEZE), "bytes": BASE_FREEZE_BYTES, "sha256": BASE_FREEZE_SHA},
            "actual_source_root": str(BASE_ROOT), "base_business_commit": base["business_source_commit"],
            "base_source_file_count": len(indexed), "base_source_bytes": base["source_bytes"],
            "all_actual_base_leaves_content_verified": verify_all_base,
            "complete_composed_manifest": {"file_count": len(stable_rows),
                                          "source_bytes": sum(row["bytes"] for row in stable_rows),
                                          "canonical_rows_json": pin(manifest_raw),
                                          "reconstruction": "Original pinned full manifest plus exact delta below; unchanged rows retained byte for byte."},
            "delta": delta, "operations": operations,
            "driver_changed_function_asts": ast_changed,
            "close_only_exact_WAL_flush_hunk_and_original_callback_cleanup_preserved": True,
            "constructor_only_exact_WAL_hunk": True,
            "M7_camera_Service_strategy_newest_tree_overlay": False,
            "construction": construction_status,
            "changed_leaf_count": len(changed), "changed_logical_bytes_each": sum(map(len, changed.values())),
            "candidate_and_reference_changed_data_logical_bytes": 2 * sum(map(len, changed.values())),
            "unchanged_frozen_leaves_may_be_hardlinked_only_after_new_admission": True,
            "current_runtime_Game_Native_OBS_modified": False, "D_output_writes": 0,
            "Driver_SAVE_body_reads": 0, "Game_MCP_RPC_calls": 0,
            "WAL_default": "OFF; explicit new SDK owner environment required for writer adoption",
            "actual_runtime_or_performance_credit": False}
    return changed, stable_rows, plan


def canonical_anchor_with_root_writer(git_writer, *, anchor_ref, root_release_sha256):
    """Executable recipe; only Root supplies/executes the mutating Git callback.

    Not invoked by this module's CLI, compose(), or qualifier.  git_writer must
    accept ``(argument_list, input_bytes_or_None)`` and return stdout bytes.  It
    must execute against this same repository.  There is no checkout, index,
    working-tree write, master update or D: output.  Root must separately admit
    the Git-object upper bound before invoking this recipe.
    """
    require(callable(git_writer), "Root-owned Git writer required")
    require(re.fullmatch(r"[0-9a-f]{64}", root_release_sha256), "exact Root release SHA required")
    require(re.fullmatch(r"refs/heads/campaign/robert-v20261019-c17-perf-warm-[a-z0-9-]+", anchor_ref),
            "new dedicated campaign anchor ref required")
    construction = {"bytes": 40243, "sha256": "3bd067119b9d98eea6f1f57416fc5d42560dfde57183f67ff56926d314b62431"}
    changed, rows, plan = compose(construction_pin=construction)
    base = plan["base_business_commit"]
    existing = git("for-each-ref", "--format=%(refname)", anchor_ref).decode().splitlines()
    require(anchor_ref not in existing, "dedicated canonical anchor ref already exists")
    _, original_index = read_actual_manifest()
    original_git = {}
    for entry in git("ls-tree", "-r", "-l", "-z", base, "--", PREFIX[:-1]).split(b"\0"):
        if entry:
            header, name = entry.split(b"\t", 1)
            mode, kind, object_id, size = header.decode("ascii").split()
            require(kind == "blob", "actual baseline must remain ordinary Git blobs")
            original_git[name.decode("utf-8")[len(PREFIX):]] = (mode, object_id, int(size))
    require(original_git == {name: (row["git_mode"], row["git_blob_sha1"], row["bytes"])
                             for name, row in original_index.items()}, "actual full baseline Git tree differs")
    writes = []

    def write(args, data=None):
        result = git_writer(args, data)
        require(isinstance(result, bytes), "Root Git callback must return stdout bytes")
        writes.append(args[0])
        return result

    for relative, raw in sorted(changed.items()):
        actual = write(["hash-object", "-w", "--stdin"], raw).decode("ascii").strip()
        require(actual == blob_sha(raw), "Root materialized blob differs: " + relative)
    hierarchy = {}
    for row in rows:
        parts = safe_relative(row["relative"]).split("/")
        node = hierarchy
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            require(isinstance(node, dict), "source tree file/directory collision")
        require(parts[-1] not in node, "duplicate source tree member")
        node[parts[-1]] = (row["git_mode"], row["git_blob_sha1"])

    def tree(node):
        records = []
        for name, value in sorted(node.items()):
            require("\n" not in name and "\t" not in name, "unsupported tree member")
            if isinstance(value, dict):
                mode, kind, object_id = "040000", "tree", tree(value)
            else:
                mode, object_id = value
                kind = "blob"
            records.append(f"{mode} {kind} {object_id}\t{name}".encode("utf-8") + b"\0")
        result = write(["mktree", "-z"], b"".join(records)).decode("ascii").strip()
        require(re.fullmatch(r"[0-9a-f]{40}", result), "Root tree object ID differs")
        return result

    source_tree = tree(hierarchy)

    def splice(original_tree, parts, replacement):
        records = []
        found = 0
        for entry in git("ls-tree", "-z", original_tree).split(b"\0"):
            if not entry:
                continue
            header, name = entry.split(b"\t", 1)
            mode, kind, object_id = header.decode("ascii").split()
            if name.decode("utf-8") == parts[0]:
                require(kind == "tree", "canonical SDK ancestor must remain a tree")
                found += 1
                object_id = replacement if len(parts) == 1 else splice(object_id, parts[1:], replacement)
            records.append(f"{mode} {kind} {object_id}".encode("ascii") + b"\t" + name + b"\0")
        require(found == 1, "canonical SDK ancestor missing/ambiguous")
        return write(["mktree", "-z"], b"".join(records)).decode("ascii").strip()

    root_tree = splice(git("rev-parse", base + "^{tree}").decode("ascii").strip(),
                       ["ck3_autonomous_player", "src"], source_tree)
    message = ("C17 minimal warm SDK over the actual frozen C16 business tree\n\n"
               "Original actual manifest SHA256: " + BASE_FREEZE_SHA + "\n"
               "Complete composed rows SHA256: " + plan["complete_composed_manifest"]["canonical_rows_json"]["sha256"] + "\n"
               "Root release SHA256: " + root_release_sha256 + "\n"
               "Dedicated source anchor only; Game/Native/recording unchanged.\n").encode()
    commit_id = write(["commit-tree", root_tree, "-p", base], message).decode("ascii").strip()
    require(re.fullmatch(r"[0-9a-f]{40}", commit_id), "Root commit object ID differs")
    actual_rows = {}
    for entry in git("ls-tree", "-r", "-l", "-z", commit_id, "--", PREFIX[:-1]).split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, blob, size = header.decode("ascii").split()
        relative = name.decode("utf-8")[len(PREFIX):]
        require(kind == "blob", "canonical source non-blob")
        actual_rows[relative] = (mode, blob, int(size))
    require(actual_rows == {row["relative"]: (row["git_mode"], row["git_blob_sha1"], row["bytes"])
                            for row in rows}, "Root complete 1445-leaf canonical tree differs")
    # Create-only reference; never rewrite a prior anchor/master or any index.
    write(["update-ref", anchor_ref, commit_id, "0" * 40])
    return {"business_source_commit": commit_id, "business_source_ref": anchor_ref,
            "parent_commit": base, "source_tree": source_tree, "file_count": len(rows),
            "logical_source_bytes": sum(row["bytes"] for row in rows),
            "composed_rows_sha256": plan["complete_composed_manifest"]["canonical_rows_json"]["sha256"],
            "Root_owned_git_commands": writes, "master_or_worktree_or_index_changed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--construction-bytes", type=int)
    parser.add_argument("--construction-sha256")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    require((args.construction_bytes is None) == (args.construction_sha256 is None),
            "construction bytes and SHA required together")
    construction = None if args.construction_bytes is None else {
        "bytes": args.construction_bytes, "sha256": args.construction_sha256}
    _, _, report = compose(construction_pin=construction)
    if args.report:
        require(args.report.resolve().is_relative_to(REPO.resolve()), "report must remain in approved workspace")
        raw = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode()
        require(len(raw) <= 64 * 1024, "small composition report limit exceeded")
        with args.report.open("xb") as stream:
            stream.write(raw)
        print(json.dumps({"report": {"path": str(args.report.resolve()), **pin(raw)}}))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
