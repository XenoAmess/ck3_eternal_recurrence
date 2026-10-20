"""RAM-only Source25: precisely three qualified packages over actual Source24.

No source-tree export, canonical Git write, current runtime, Task or Game access.
The complete inventory is inherited from Source24's pinned composer and checked
against its actual canonical tree. Only the nine new output bodies are retained.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE_COMMIT = "6b55531b1d3a44ee73ab13ea40132556030f682e"
BASE_REF = "refs/heads/campaign/robert-v20261019-source24-camera-cold-01"
PREFIX = "ck3_autonomous_player/src/"
BRIDGE = "xar_autoplayer/bridge/"
PARENT_ANCHOR = REPO / "_runtime/source24-integration16/SOURCE24-CANONICAL-ANCHOR.json"
PARENT_ANCHOR_PIN = (6269, "fb4f7ef4933d7e86f82b81e0824332a92f49ae5562c8337460b87efb8031a8f8")
BASE_ROWS_PIN = (374409, "7828a4d94129aff19e0c830ecaf55303f2831038b9307b379ee151bc58da6b7d")
ROWS_PIN = (375121, "8ad5ba889feef72bf22cb18746894c44dd4d98cdc8d2904427efa3a474e0ac5a")
PLAN = REPO / "docs/ck3-native-ai/evidence/source25-sdk-source-plan-2026-10-20.json"
WAIT_ROOT = REPO / "tools/g2_saved_campaign/candidates/exact_clock_wait_progress_20261020"
INPUT_PINS = {
    "tools/g2_saved_campaign/prepare_source24_camera_sdk_v1.py": (14942, "1afd44c58f68824ef71da63048eadca51722f2c8c3cf0f3e62710bcc93a646e2"),
    "tools/g2_saved_campaign/transform_nonleading_siege_priority_v1.py": (4194, "8d8ac3251e075f44f1d2f0fec6eea0d087b8a856af21bf6d40edf10d951702fe"),
    "tools/g2_saved_campaign/candidates/exact_clock_wait_progress_20261020/prepare_candidate.py": (8267, "c21d8acb85d8ba83543c6a8842c48cde74e6e00cd084299cddbd31ff79cb1d67"),
    "tools/g2_saved_campaign/candidates/exact_clock_wait_progress_20261020/QUALIFICATION.json": (1305, "eedd17b5d3df6bff5ea43c4e2e231481c21fd67950439518288faee2093dc0b3"),
    "tools/g2_saved_campaign/candidates/exact_clock_wait_progress_20261020/SOURCE-READY.json": (924, "1e05533c4479e963e35916911ee022cf8ffeba2eafe6c92d9964a6f574420133"),
    "docs/ck3-native-ai/evidence/g2-m7-prenative-mem-image-source-2026-10-20.json": (3230, "3028c52e9acd331a0909d9d180987cb10566db0a7bc3bb0f955dc0e8bb19d507"),
    "docs/ck3-native-ai/evidence/nonleading-player-realm-siege-priority-2026-10-20.json": (6400, "195327c49105a54aceb25e99802d5678ed1993d48ae882e361f88dd956e3ecff"),
}


def require(ok, message):
    if not ok:
        raise ValueError("Source25: " + message)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def check(raw, expected, label):
    require(pin(raw) == {"bytes": expected[0], "sha256": expected[1]}, label + " pin differs")
    return raw


def safe_relative(name):
    require(type(name) is str and "\\" not in name and ":" not in name and "\0" not in name
            and name == str(PurePosixPath(name)) and not PurePosixPath(name).is_absolute()
            and all(p not in ("", ".", "..") for p in name.split("/")), "unsafe source path")
    return name


def file_pin(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink()
            and not (getattr(path.lstat(), "st_file_attributes", 0) & 0x400), "regular input required")
    return {"path": str(path.resolve()), **pin(path.read_bytes())}


def git_read(*parts):
    result = subprocess.run(["git", "-C", str(REPO), "--no-replace-objects", *parts],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(result.returncode == 0, "Git read failed: " + result.stderr[:512].decode(errors="replace"))
    require(len(result.stdout) <= 8 * 1024**2 and len(result.stderr) <= 65536, "Git read cap")
    return result.stdout


def verify_tree(revision, rows):
    actual = {}
    for entry in git_read("ls-tree", "-r", "-l", "-z", revision, "--", PREFIX).split(b"\0"):
        if entry:
            header, path = entry.split(b"\t", 1)
            mode, kind, blob, size = header.split()
            path = path.decode()
            require(kind == b"blob" and path.startswith(PREFIX), "ordinary SDK blob required")
            name = safe_relative(path[len(PREFIX):])
            require(name not in actual, "duplicate Git path")
            actual[name] = (mode.decode(), blob.decode(), int(size))
    require(actual == {r["relative"]: (r["git_mode"], r["git_blob_sha1"], r["bytes"]) for r in rows},
            "complete Git mode/blob/size differs")


def read_base(name, indexed):
    safe_relative(name)
    row = indexed[name]
    raw = git_read("cat-file", "blob", BASE_COMMIT + ":" + PREFIX + name)
    return check(raw, (row["bytes"], row["sha256"]), "actual Source24 " + name)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compose(*, verify_all_base=False):
    require(sys.dont_write_bytecode, "run with -B")
    for name, expected in INPUT_PINS.items():
        check((REPO / name).read_bytes(), expected, name)
    anchor_raw = check(PARENT_ANCHOR.read_bytes(), PARENT_ANCHOR_PIN, "actual Source24 anchor")
    anchor = json.loads(anchor_raw)
    require(anchor["machine_id"] == MACHINE and anchor["commit"] == BASE_COMMIT
            and anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and anchor["source_file_count"] == 1457 and anchor["source_bytes"] == 59209522
            and anchor["future_writes"] == 0, "actual Source24 closure differs")
    require(git_read("rev-parse", "--verify", BASE_REF).decode().strip() == BASE_COMMIT,
            "actual Source24 ref differs")
    import prepare_source24_camera_sdk_v1 as source24
    import transform_nonleading_siege_priority_v1 as siege
    inherited, base_rows, inherited_report = source24.compose(verify_all_base=verify_all_base)
    check(canonical(base_rows), BASE_ROWS_PIN, "complete actual Source24 rows")
    verify_tree(BASE_COMMIT, base_rows)
    indexed = {r["relative"]: r for r in base_rows}
    changed = {}
    m7_path = "docs/ck3-native-ai/evidence/g2-m7-prenative-mem-image-source-2026-10-20.json"
    m7 = json.loads((REPO / m7_path).read_bytes())
    require(m7["machine_id"] == MACHINE and m7["status"] == "SOURCE_AND_OWNED_PRE_RESUME_READY"
            and m7["unit"]["nodes_passed"] == 13 and m7["unit"]["subtests_passed"] == 32,
            "M7 existing qualification differs")
    for item in m7["sources"][:4]:
        name = safe_relative(item["path"][len(PREFIX):])
        require(item["path"].startswith(PREFIX) and name not in changed, "M7 source scope differs")
        changed[name] = check((REPO / item["path"]).read_bytes(), (item["bytes"], item["sha256"]), "M7 leaf")
    require(set(changed) == {BRIDGE + n for n in ("native_loaded_provider_custody_v1.py",
            "native_loaded_provider_windows_v1.py", "native_preload_mapped_images_v1.py")}
            | {"xar_autoplayer/successor_ui_pending_ledger_v1.py"}, "four M7 production leaves required")
    siege_path = "docs/ck3-native-ai/evidence/nonleading-player-realm-siege-priority-2026-10-20.json"
    siege_proof = json.loads((REPO / siege_path).read_bytes())
    require(siege_proof["machine_id"] == MACHINE and siege_proof["status"] == "future_source_qualified_not_deployed"
            and siege_proof["tests"]["final_exit_code"] == 0, "siege qualification differs")
    strategy = "xar_autoplayer/strategy.py"
    before = read_base(strategy, indexed)
    after = siege.transform_strategy_bytes(before)
    require(siege.transform_strategy_bytes(after, inverse=True) == before, "entire Strategy inverse differs")
    check(after, (1048459, "aa070e8c98bebeb625c581081efaac494db18d2b860db77c27a9e1ff0a2ae40b"), "qualified Strategy")
    changed[strategy] = after
    helper = "xar_autoplayer/nonleading_player_realm_siege_v1.py"
    changed[helper] = check((REPO / (PREFIX + helper)).read_bytes(),
        (3615, "3f5103e42c8d7d785aa7680d19be592407a55b8e3d6bb4fb55159817fbe925e6"), "qualified siege helper")
    wait = _load("source25_frozen_wait_candidate", WAIT_ROOT / "prepare_candidate.py")
    inputs = {n: inherited.get(BRIDGE + n) or read_base(BRIDGE + n, indexed) for n in wait.PINS}
    wait_outputs, _, changed_asts = wait.compose(inputs)
    wait_proof = json.loads((WAIT_ROOT / "QUALIFICATION.json").read_bytes())
    ready = json.loads((WAIT_ROOT / "SOURCE-READY.json").read_bytes())
    require(ready["status"] == "SOURCE_READY_NOT_ADOPTED" and wait_proof["machine_id"] == MACHINE
            and (wait_proof["tests"], wait_proof["failures"], wait_proof["errors"]) == (5, 0, 0),
            "wait B existing qualification differs")
    for name, raw in wait_outputs.items():
        require(pin(raw) == wait_proof["output_pins"][name], "wait B qualified body differs")
        require(BRIDGE + name not in changed, "qualified package write overlap")
        changed[BRIDGE + name] = raw
    rows = {n: dict(r) for n, r in indexed.items()}
    delta = []
    for name, raw in sorted(changed.items()):
        compile(raw, name, "exec", dont_inherit=True)
        old = rows.get(name)
        row = {"relative": name, **pin(raw), "git_blob_sha1": hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
            "git_mode": old["git_mode"] if old else "100644"}
        rows[name] = row
        delta.append({"relative": name, "before": old, "after": row,
                      "net_bytes": len(raw) - (old["bytes"] if old else 0)})
    stable = [rows[n] for n in sorted(rows)]
    require(len(changed) == 9 and len(stable) == len({n.casefold() for n in rows}) == 1460
            and sum(r["bytes"] for r in stable) == 59234989
            and sum(d["before"] is None for d in delta) == 3, "nine-output/three-new complete shape differs")
    require(all(rows[n] == indexed[n] for n in indexed if n not in changed), "unowned Source24 row differs")
    check(canonical(stable), ROWS_PIN, "complete Source25 rows")
    ledger = ast.parse(changed["xar_autoplayer/successor_ui_pending_ledger_v1.py"])
    epoch = next(n for n in ledger.body if isinstance(n, ast.FunctionDef) and n.name == "owner_source_epoch_v1")
    names = [ast.literal_eval(n.value) for n in epoch.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "names" for t in n.targets)]
    require(len(names) == 1 and "bridge/native_preload_mapped_images_v1.py" in names[0], "M7 helper epoch closure missing")
    epoch_inputs = {n: rows["xar_autoplayer/" + n]["sha256"] for n in names[0]}
    consumer_path = REPO / "tools/g2_saved_campaign/c23_a03_feeder_qualification_20261020.json"
    consumer_raw = check(consumer_path.read_bytes(),
        (3098, "05ab210a385b78e7ed2c0b116ca628c29586ac3eb18622d3ed25bd7c5d2582c5"), "focused DTO consumer qualification")
    consumer = json.loads(consumer_raw)
    require(consumer["machine_id"] == MACHINE and consumer["qualification"]["exit_code"] == 0
            and consumer["qualification"]["tests"] == 4 and consumer["DTO_v2_MCP_Queue_errors_preserved"] is True
            and consumer["mixed_v1_v2_rejected"] is True
            and consumer["DTO_v2_exact_candidate_pin"] == "6893/7645e52a2b221a5e9a813f0e243f9f8a2f6e59f9b08f998a15bc70500af16f0e",
            "focused DTO consumer result differs")
    report = {
        "schema": "xar.source25.three-package-sdk/v1", "machine_id": MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RAM_SOURCE25_NOT_CANONICAL_NOT_EXPORTED_NOT_RUNTIME_ADOPTED",
        "base": {"business_commit": BASE_COMMIT, "anchor": {"path": str(PARENT_ANCHOR), **pin(anchor_raw)},
                 "files": 1457, "source_bytes": 59209522, "rows": {"bytes": BASE_ROWS_PIN[0], "sha256": BASE_ROWS_PIN[1]}},
        "output": {"files": 1460, "source_bytes": 59234989, "canonical_rows_JSON": pin(canonical(stable)),
                   "changed_existing_from_Source24": 6, "new_from_Source24": 3, "unchanged_Source24_rows": 1451,
                   "new_output_payload_bytes": sum(len(v) for v in changed.values()),
                   "net_source_bytes": 25467},
        "delta": delta, "packages": {"M7": file_pin(REPO / m7_path),
            "nonleading_siege": file_pin(REPO / siege_path), "exact_clock_wait_B": file_pin(WAIT_ROOT / "SOURCE-READY.json")},
        "frozen_input_sources": {n: {"bytes": p[0], "sha256": p[1]} for n, p in INPUT_PINS.items()},
        "static_internal_dependency_closure": source24.prior.dependencies(changed, rows),
        "Strategy_entire_inverse": True, "Driver_B_entire_inverse_and_unowned_AST": True,
        "Driver_B_changed_function_ASTs": changed_asts, "package_production_write_overlap": False,
        "source_epoch_detached_model": hashlib.sha256(canonical(epoch_inputs)).hexdigest(),
        "epoch_inputs_after_final_three_packages": epoch_inputs, "source_epoch_actual_filesystem_authority": False,
        "original_13_19_5_qualifications_reused_not_rerun": True,
        "DTO_v2_consumer_qualification": {"path": str(consumer_path), **pin(consumer_raw)},
        "DTO_and_wait_helper_exact_pins_match_focused_consumer": True,
        "inherited_Source24_camera_and_M7_WAL_contracts_preserved": inherited_report["inherited_M7_WAL_fullinverse_and_commutativity_preserved"],
        "all_original_base_bodies_reread": verify_all_base,
        "actual_H": "unknown", "actual_Native30_loaded": False, "actual_war_or_camera_result": "NOTRUN",
        "clock_root_cause": "UNKNOWN; B is receipt-time diagnostic, not a clock fix",
        "operations": {"Git_reads_only": True, "Git_writes": 0, "SDK_exports": 0, "runtime_Task_Game_Native_RPC": 0,
                       "full_generated_leaf_disk_copies": 0, "scratch_bytes": 0},
        "RAM_participation": {"new_output_payload_bytes": sum(len(v) for v in changed.values()),
            "Source24_six_output_payload_bytes": sum(len(v) for v in inherited.values()),
            "complete_inventory_canonical_bytes": len(canonical(stable)), "physical_RSS_peak": None},
        "future_writes_after_freeze": 0,
    }
    return changed, stable, report


def object_upper(kind, size):
    # Header plus one conservative 4KiB compression overhead, rounded to NTFS.
    return ((size + len(kind) + len(str(size)) + 2 + 4096 + 4095) // 4096) * 4096


def tree_entries(revision):
    result = {}
    for item in git_read("ls-tree", "-z", revision).split(b"\0"):
        if item:
            head, name = item.split(b"\t", 1)
            require(name not in result, "duplicate tree entry")
            result[name] = tuple(head.split())
    return result


def quote(outputs, rows):
    directories = {""}
    for name in outputs:
        parent = (PREFIX + name).rpartition("/")[0]
        while parent:
            directories.add(parent)
            parent = parent.rpartition("/")[0]
    trees, objects = {}, []
    for name, raw in sorted(outputs.items()):
        objects.append({"kind": "blob", "path": name, "payload_bytes": len(raw), "upper": object_upper("blob", len(raw))})
    for directory in sorted(directories):
        entries = tree_entries(BASE_COMMIT + (":" + directory if directory else "^{tree}"))
        for name, raw in outputs.items():
            parent, _, leaf = (PREFIX + name).rpartition("/")
            if parent == directory:
                entries[leaf.encode()] = (b"100644", b"blob", b"0" * 40)
        size = sum(len(mode.lstrip(b"0")) + 1 + len(name) + 1 + 20 for name, (mode, kind, child) in entries.items())
        trees[directory or "<root>"] = size
        objects.append({"kind": "tree", "path": directory or "<root>", "payload_bytes": size, "upper": object_upper("tree", size)})
    objects.append({"kind": "commit", "payload_cap": 8192, "upper": object_upper("commit", 8192)})
    retained = sum(o["upper"] for o in objects)
    largest = max(o["upper"] for o in objects)
    require(trees == {"<root>": 1565, "ck3_autonomous_player": 1122, "ck3_autonomous_player/src": 41,
            "ck3_autonomous_player/src/xar_autoplayer": 12717, "ck3_autonomous_player/src/xar_autoplayer/bridge": 41245},
            "five ancestor tree payloads differ")
    require(len(objects) == 15 and (retained, largest) == (2949120, 1650688), "fifteen-object Git quote differs")
    cluster = sum(((r["bytes"] + 4095) // 4096) * 4096 for r in rows)
    return {"Git": {"objects": objects, "tree_payloads": trees, "retained_upper": retained,
            "largest_temporary_upper": largest, "refs_dirs_locks_reserve": 65536,
            "peak_upper": retained + largest + 65536, "compression_or_dedup_credit": 0,
            "old_Source24_Source23_holds_retained_separately": True},
        "full_export_data_only": {"files_each": len(rows), "logical_bytes_each": sum(r["bytes"] for r in rows),
            "cluster_bytes": 4096, "data_cluster_upper_each": cluster, "dual_data_cluster_upper": 2 * cluster,
            "rich_MFT_controls_runtime_not_included": True}, "source_epoch_actual_filesystem_authority": False}


if __name__ == "__main__":
    outputs, rows, report = compose()
    print(json.dumps({"output": report["output"], "delta": report["delta"], "quote": quote(outputs, rows)}, separators=(",", ":")))
