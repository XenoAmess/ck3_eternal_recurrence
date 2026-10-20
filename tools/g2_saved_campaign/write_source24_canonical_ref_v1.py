"""Create the reviewed Source24 ref only after Root's explicit execution release.

Default OFF. No index, tracked checkout, master, push, export, build or runtime.
A source commitment is insufficient: --git-card must admit this concrete phase.
The create-only anchor preserves a failed/unknown attempt; never retry blindly.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE = "330d6e67c99eb22a60919b2bf7666c1ed0ca1b71"
BASE_REF = "refs/heads/campaign/robert-v20261019-c23-native30-m7-cold-01"
REF = "refs/heads/campaign/robert-v20261019-source24-camera-cold-01"
PREFIX = "ck3_autonomous_player/src/"
COMPOSER = REPO / "tools/g2_saved_campaign/prepare_source24_camera_sdk_v1.py"
COMPOSER_PIN = (14942, "1afd44c58f68824ef71da63048eadca51722f2c8c3cf0f3e62710bcc93a646e2")
PLAN = REPO / "docs/ck3-native-ai/evidence/source24-camera-sdk-source-plan-2026-10-20.json"
PLAN_PIN = (59167, "b7bcecc26413d36a409b9970fc5d2276304d2827a1d2581015418a55d952136f")
SOURCE_CARD_PIN = (1341, "14f0d69838e6634335f9bfb980a13edb561fd0038ce0b6914038a4f096f3e96d")
SOURCE_CARD_NAME = "SOURCE24-ROOTWRITER-NEW-SOURCE32KiB-COMMITMENT01.json"
ROWS_PIN = (374409, "7828a4d94129aff19e0c830ecaf55303f2831038b9307b379ee151bc58da6b7d")
BASE_ROWS_PIN = (374182, "f16995df275525a39ceacf3825f38f5f9a508a67970d59e83cb3bb43e7f7fdb4")
DRIVER_PIN = (1642169, "2d3fe6a71d8ee15e924446986fae4e27fe00ea59cc86baa31d1c79b11da2acc8")
GIT_HARD = 7340032
METADATA_HARD = 524288
ANCHOR_HARD = 12288
GIT_PEAK = 4411392
OLD_RETAINED_UPPER = 2187264
OLD_ALLOCATED = 483576
PARENT_ANCHOR = REPO / "_runtime/source23-integration16/SOURCE23-CANONICAL-ANCHOR.json"
PARENT_ANCHOR_PIN = (7206, "aa5880db457ba6b892fa24c11a4afe15f5a7ee1d28cd37b1e566a4ac75b67e39")
PARENT_CLOSE_NAME = "SOURCE23-CANONICAL-GIT-ROOT-ACTUAL-CLOSED01.json"
PARENT_CLOSE_PIN = (2687, "5ac111757fc7b43775de78d5a5db507fa55303272f595e96fa92b0a4f93b8ece")
MAX_COMMAND_STDOUT = 2 * 1024**2
NTFS_HELPER = REPO / "tools/g2_saved_campaign/export_immutable_sdk_views_v1.py"
NTFS_PIN = (22964, "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432")


def require(ok, why):
    if not ok:
        raise RuntimeError("Source24 writer: " + why)


def utc():
    return datetime.now(timezone.utc).isoformat()


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def check(raw, expected, label):
    require(pin(raw) == {"bytes": expected[0], "sha256": expected[1]}, label + " pin differs")
    return raw


def file_pin(path):
    require(path.is_file() and not path.is_symlink(), "regular source file required: " + str(path))
    return {"path": str(path.resolve()), **pin(path.read_bytes())}


def safe_relative(name):
    require(type(name) is str and "\\" not in name and "\x00" not in name
            and name == str(PurePosixPath(name)) and not PurePosixPath(name).is_absolute()
            and all(p not in ("", ".", "..") for p in name.split("/")), "unsafe SDK path")
    return name


def oid(raw):
    value = raw.decode("ascii").strip()
    require(re.fullmatch("[0-9a-f]{40}", value), "one native Git SHA1 required")
    return value


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source-card", type=Path, required=True)
    parser.add_argument("--git-card", type=Path)
    parser.add_argument("--git-card-sha256")
    parser.add_argument("--execute-root-writer", action="store_true")
    args = parser.parse_args()
    if not args.execute_root_writer:
        print('{"status":"DISABLED","Git_mutations":0,"runtime_calls":0}')
        return
    require(args.git_card is not None and type(args.git_card_sha256) is str
            and re.fullmatch("[0-9a-f]{64}", args.git_card_sha256), "reviewed concrete Git card required")
    start = utc()
    source_raw = check(args.source_card.read_bytes(), SOURCE_CARD_PIN, "source commitment")
    source = json.loads(source_raw)
    require(source["schema"] == "xar.storage.Source24-rootwriter-source32.v1"
            and source["machine_id"] == MACHINE and source["owner"] == "g2_m3_succession"
            and source["status"] == "SOURCE_ONLY_ADMITTED"
            and source["new_source_complete_hard_bytes"] == 32768 and source["scratch_hard_bytes"] == 0,
            "source-only commitment differs")
    require(args.source_card.name == SOURCE_CARD_NAME, "source commitment locator differs")
    own = file_pin(Path(__file__))
    require(Path(source["helper_path"]).resolve() == Path(__file__).resolve() and own["bytes"] <= 32768,
            "source-only path/size differs")
    raw_card = args.git_card.read_bytes()
    require(pin(raw_card)["sha256"] == args.git_card_sha256, "reviewed Git card SHA256 differs")
    card = json.loads(raw_card)
    # Concrete card shape is deliberately separate from the source-only card.
    require(card["schema"] == "xar.storage.Source24-root-canonical-Git.v1"
            and card["machine_id"] == MACHINE and card["owner"] == "Root"
            and card["status"] == "ADMITTED",
            "concrete Source24 Git admission required")
    require(card["Git"]["hard_bytes"] == card["components"]["Source24_canonical_Git"] == GIT_HARD
            and card["components"]["Root_writer_proof_metadata"] == METADATA_HARD,
            "concrete component caps differ")
    s = card["Root_writer_source"]
    require(Path(s["helper"]).resolve() == Path(__file__).resolve()
            and s["helper_bytes"] == own["bytes"] and s["helper_sha256"] == own["sha256"]
            and s["anchor_hard_bytes"] == ANCHOR_HARD,
            "reviewed writer pin differs")
    now = datetime.now(timezone.utc)
    for label, doc in (("source", source), ("Git", card)):
        deadline = datetime.fromisoformat(doc["review_at_utc"].replace("Z", "+00:00"))
        require(deadline.tzinfo is not None and now < deadline, label + " admission expired")
    root, anchor = Path(s["integration_root"]), Path(s["future_anchor"])
    require(root.resolve() == (REPO / "_runtime/source24-integration16").resolve()
            and anchor.parent.resolve() == root.resolve() and anchor.name == "SOURCE24-CANONICAL-ANCHOR.json"
            and not root.is_symlink() and not anchor.exists(), "exact absent Source24 anchor required")
    machine = subprocess.check_output(
        [sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"], cwd=REPO
    ).decode().strip()
    require(machine == MACHINE, "actual execution machine differs")
    floor = card["capacity"]["Z_conservative_floor_bytes"]
    require(type(floor) is int and floor >= 0, "explicit current Z free floor required")
    require(shutil.disk_usage(REPO).free >= floor,
            "fresh free floor, including all component holds, unavailable")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        require(not os.environ.get(key), "ambient Git redirection: " + key)
    os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    env = dict(os.environ)
    hooks = root / "disabled-hooks-must-remain-absent"
    require(not hooks.exists(), "unexpected hooks path")
    prefix = ["git", "-C", str(REPO), "-c", "gc.auto=0", "-c", "maintenance.auto=false",
              "-c", "commit.gpgsign=false", "-c", "i18n.commitEncoding=utf-8",
              "-c", "core.hooksPath=" + str(hooks)]

    def command(*parts, data=None, allowed=(0,)):
        out = subprocess.run(prefix + list(parts), input=data, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env, check=False)
        require(out.returncode in allowed,
                "Git " + parts[0] + " failed: " + out.stderr[:1024].decode(errors="replace"))
        require(len(out.stdout) <= MAX_COMMAND_STDOUT and len(out.stderr) <= 65536,
                "Git metadata/body output cap")
        return out.returncode, out.stdout

    def git(*parts, data=None):
        return command(*parts, data=data)[1]

    require(git("rev-parse", "--show-object-format").strip() == b"sha1", "Git object format differs")
    common = Path(os.fsdecode(git("rev-parse", "--git-common-dir").strip()))
    common = common.resolve() if common.is_absolute() else (REPO / common).resolve()
    require(common == (REPO / ".git").resolve() == Path(card["Git"]["root"]).resolve(),
            "canonical Git directory differs")
    check(NTFS_HELPER.read_bytes(), NTFS_PIN, "frozen metadata helper")
    ntfs_spec = importlib.util.spec_from_file_location("source24_metadata_only_helper", NTFS_HELPER)
    ntfs = importlib.util.module_from_spec(ntfs_spec)
    ntfs_spec.loader.exec_module(ntfs)
    require(ntfs.ntfs_identity(common)["cluster_bytes"] == 4096, "quoted 4096-byte NTFS allocation unit differs")
    require(oid(git("rev-parse", "--verify", BASE + "^{commit}")) == BASE
            and oid(git("rev-parse", "--verify", BASE_REF)) == BASE, "actual Source23 parent differs")
    require(command("show-ref", "--verify", "--quiet", REF, allowed=(0, 1))[0] == 1,
            "Source24 ref already exists")
    require(command("symbolic-ref", "--quiet", REF, allowed=(0, 1))[0] == 1, "symbolic Source24 ref exists")

    parent_raw = check(PARENT_ANCHOR.read_bytes(), PARENT_ANCHOR_PIN, "actual Source23 anchor")
    parent_anchor = json.loads(parent_raw)
    close_path = args.source_card.parent / PARENT_CLOSE_NAME
    close_raw = check(close_path.read_bytes(), PARENT_CLOSE_PIN, "Source23 actual closure")
    parent_close = json.loads(close_raw)
    require(parent_anchor["machine_id"] == parent_close["machine_id"] == MACHINE
            and parent_anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            and parent_anchor["commit"] == parent_close["commit"] == BASE and parent_anchor["future_writes"] == 0
            and parent_anchor["source_file_count"] == 1456 and parent_anchor["source_bytes"] == 59198354,
            "actual Source23 parent closure differs")
    require(Path(parent_close["actual_anchor"]["path"]).resolve() == PARENT_ANCHOR.resolve()
            and parent_close["actual_anchor"]["bytes"] == PARENT_ANCHOR_PIN[0]
            and parent_close["actual_anchor"]["sha256"] == PARENT_ANCHOR_PIN[1]
            and parent_close["Source23full16_and_Git3932160_quotes_retained"] is True,
            "Source23 original anchor/full holds differ")
    require(parent_anchor["Git_object_quote"]["retained_upper"] == OLD_RETAINED_UPPER
            and parent_anchor["Git_object_quote"]["hard_bytes"] == 3932160
            and parent_anchor["exact_object_metadata"]["count"] == 18
            and parent_anchor["exact_object_metadata"]["allocation_unknown_count"] == 0
            and parent_anchor["exact_object_metadata"]["known_loose_allocated_bytes"] == OLD_ALLOCATED,
            "closed eighteen-object Source23 baseline differs")
    plan_raw = check(PLAN.read_bytes(), PLAN_PIN, "source plan")
    plan = json.loads(plan_raw)
    check(COMPOSER.read_bytes(), COMPOSER_PIN, "frozen composer")
    spec = importlib.util.spec_from_file_location("source24_frozen_camera_composer", COMPOSER)
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    require(producer.BASE_COMMIT == BASE and producer.prior.PREFIX == PREFIX, "composer base differs")
    # The immutable parent's complete Git mode/blob/size is checked below.
    # Only six camera output bodies (plus frozen prior composition) are reread; no full SDK source copy.
    outputs, rows, report = producer.compose(verify_all_base=False)
    expected = {}
    for row in rows:
        name = safe_relative(row["relative"])
        require(name not in expected and row["git_mode"] in ("100644", "100755")
                and type(row["bytes"]) is int and 0 <= row["bytes"] <= 8 * 1024**2
                and re.fullmatch("[0-9a-f]{40}", row["git_blob_sha1"])
                and re.fullmatch("[0-9a-f]{64}", row["sha256"]), "invalid complete SDK row")
        expected[name] = row
    inventory = canonical([expected[n] for n in sorted(expected)])
    check(inventory, ROWS_PIN, "complete1457 canonical rows")
    require(len(expected) == 1457 and len({n.casefold() for n in expected}) == 1457
            and sum(r["bytes"] for r in rows) == 59209522, "complete1457 source shape differs")
    require(report["machine_id"] == plan["machine_id"] == MACHINE
            and report["base"] == plan["base"] and report["output"] == plan["output"]
            and report["delta"] == plan["delta"] and report["actual_H"] == plan["actual_H"] == "unknown"
            and report["actual_tracking_or_realm_result"] == plan["actual_tracking_or_realm_result"] == "NOTRUN",
            "candidate report/plan scope differs")
    require(report["unowned_function_ASTs_preserved"] is True
            and report["inherited_M7_WAL_fullinverse_and_commutativity_preserved"] is True
            and report["source_epoch_detached_model"] == plan["source_epoch_detached_model"]
            == "7616992f104d375b5758c148d95cb5e364dfabc535979fb48c7fea993d3e5461"
            and report["source_epoch_actual_authority"] is False,
            "qualified camera/M7 composition differs")
    require(type(outputs) is dict and len(outputs) == len(plan["delta"]) == 6,
            "exact six changed bodies required")
    planned = {safe_relative(r["relative"]): r for r in plan["delta"]}
    require(len(planned) == 6 and set(planned) == set(outputs)
            and sum(r["before"] is None for r in planned.values()) == 1, "one new/five changed required")
    base_expected = dict(expected)
    changes = {}
    for name, raw in outputs.items():
        require(type(raw) is bytes, "output body must be bytes")
        after = planned[name]["after"]
        require(expected[name] == after and pin(raw) == {"bytes": after["bytes"], "sha256": after["sha256"]}
                and producer.exact.blob_sha(raw) == after["git_blob_sha1"], "output differs: " + name)
        before = planned[name]["before"]
        if before is None:
            del base_expected[name]
        else:
            require(before["relative"] == name, "preimage path differs")
            base_expected[name] = before
        changes[(PREFIX + name).encode()] = (after["git_mode"].encode(), b"blob",
                                             after["git_blob_sha1"].encode())
    check(outputs["xar_autoplayer/bridge/native_driver.py"], DRIVER_PIN, "Driver candidate")
    check(canonical([base_expected[n] for n in sorted(base_expected)]), BASE_ROWS_PIN, "complete1456 parent rows")
    require(len(base_expected) == 1456, "complete1456 parent count differs")

    def verify_tree(value, wanted):
        actual = {}
        for entry in git("ls-tree", "-r", "-l", "-z", value, "--", PREFIX).split(b"\0"):
            if not entry:
                continue
            header, path = entry.split(b"\t", 1)
            mode, kind, blob, size = header.split()
            name = path.decode()
            require(kind == b"blob" and name.startswith(PREFIX), "non-blob SDK entry")
            name = safe_relative(name[len(PREFIX):])
            require(name not in actual, "duplicate SDK tree path")
            actual[name] = (mode.decode(), blob.decode(), int(size))
        require(actual == {n: (r["git_mode"], r["git_blob_sha1"], r["bytes"]) for n, r in wanted.items()},
                "complete SDK mode/blob/size readback differs")

    def tree_entries(tree):
        entries = {}
        for entry in git("ls-tree", "-z", tree).split(b"\0"):
            if entry:
                header, name = entry.split(b"\t", 1)
                require(name not in entries, "duplicate tree entry")
                entries[name] = tuple(header.split())
        return entries

    verify_tree(BASE, base_expected)
    # Quote all new objects with no compression or pre-existing dedup credit.
    def upper(kind, n):
        return ((n + len(kind) + len(str(n)) + 2 + 4096 + 4095) // 4096) * 4096

    def verify_closed_parent_objects():
        # Exact Source23 writer order: twelve sorted blobs, five postorder
        # ancestor trees, then its commit. No directory scan or body read.
        pairs = [(r["git_blob_sha1"], upper("blob", r["bytes"]))
                 for r in sorted(parent_anchor["twelve_output_pins"], key=lambda r: r["relative"])]
        old_trees = (("ck3_autonomous_player/src/xar_autoplayer/bridge", 41075),
                     ("ck3_autonomous_player/src/xar_autoplayer", 12654),
                     ("ck3_autonomous_player/src", 41), ("ck3_autonomous_player", 1122), ("", 1565))
        require(len(pairs) == 12, "original twelve Source23 blobs required")
        for directory, payload in old_trees:
            value = oid(git("rev-parse", BASE + (":" + directory if directory else "^{tree}")))
            require(int(git("cat-file", "-s", value)) == payload, "original Source23 tree size differs")
            pairs.append((value, upper("tree", payload)))
        pairs.append((BASE, upper("commit", 8192)))
        require(len({value for value, charge in pairs}) == 18, "original Source23 object set differs")
        metadata = []
        for value, charge in pairs:
            identity = ntfs.ntfs_identity(common / "objects" / value[:2] / value[2:])
            require(not identity["directory"] and type(identity["allocation_bytes"]) is int
                    and 0 <= identity["allocation_bytes"] <= charge, "closed Source23 object allocation unknown")
            metadata.append({"oid": value, "charge": charge, **identity})
        require(pin(canonical(metadata)) == parent_anchor["exact_object_metadata"]["canonical_rows"]
                and sum(r["allocation_bytes"] for r in metadata) == OLD_ALLOCATED,
                "eighteen exact Source23 metadata identities drifted")
        return pin(canonical(metadata))

    parent_metadata_pin = verify_closed_parent_objects()
    objects = [{"kind": "blob", "path": n, "payload_bytes": len(raw), "upper": upper("blob", len(raw))}
               for n, raw in sorted(outputs.items())]
    directories = {""}
    for path in changes:
        parent = path.rpartition(b"/")[0]
        while parent:
            directories.add(parent.decode())
            parent = parent.rpartition(b"/")[0]
    tree_quote = {}
    for directory in sorted(directories):
        entries = tree_entries(BASE + (":" + directory if directory else "^{tree}"))
        for path, value in changes.items():
            parent, _, name = path.rpartition(b"/")
            if parent.decode() == directory:
                require(entries.get(name, (None, b"blob"))[1] == b"blob", "leaf replaces a tree")
                entries[name] = value
        size = sum(len(mode.lstrip(b"0")) + 1 + len(name) + 1 + 20
                   for name, (mode, kind, child) in entries.items())
        key = directory or "<root>"
        tree_quote[key] = size
        objects.append({"kind": "tree", "path": key, "payload_bytes": size, "upper": upper("tree", size)})
    require(tree_quote == {"<root>": 1565, "ck3_autonomous_player": 1122,
                          "ck3_autonomous_player/src": 41, "ck3_autonomous_player/src/xar_autoplayer": 12654,
                          "ck3_autonomous_player/src/xar_autoplayer/bridge": 41124}, "five ancestor tree quote differs")
    objects.append({"kind": "commit", "payload_cap": 8192, "upper": upper("commit", 8192)})
    retained = sum(item["upper"] for item in objects)
    largest = max(item["upper"] for item in objects)
    require(retained == 2699264 and largest == 1646592
            and retained + largest + 65536 == GIT_PEAK and OLD_RETAINED_UPPER + GIT_PEAK <= GIT_HARD, "concrete uncompressed Git quote differs")
    require(len(git("var", "GIT_AUTHOR_IDENT")) + len(git("var", "GIT_COMMITTER_IDENT")) < 4096,
            "commit identities exceed bounded payload")
    # All source/tree/admission checks precede the first directory or Git write.
    root.mkdir(exist_ok=True)
    require(root.is_dir() and not root.is_symlink(), "integration directory differs")
    record = {
        "schema": "xar.source24.canonical-git-anchor/v1", "machine_id": machine,
        "start_utc": start, "status": "RUNNING_OR_UNKNOWN", "execution_owner": "Root",
        "root_direct_execution_release": True, "parent": BASE, "ref": REF,
        "source_commitment": {"path": str(args.source_card.resolve()), **pin(source_raw)},
        "capacity_card": {"path": str(args.git_card.resolve()), **pin(raw_card)},
        "writer": own, "composer": file_pin(COMPOSER), "source_plan": file_pin(PLAN),
        "actual_Source23_anchor": {"path": str(PARENT_ANCHOR), **pin(parent_raw)},
        "closed_Source23": {"path": str(close_path), **pin(close_raw)},
        "Source23_eighteen_exact_metadata": parent_metadata_pin,
        "metadata_only_helper": file_pin(NTFS_HELPER),
        "Git_object_quote": {"retained_upper": retained, "largest_temporary_upper": largest,
                             "refs_dirs_locks_reserve": 65536, "peak_upper": GIT_PEAK,
                             "hard_bytes": GIT_HARD, "compression_or_dedup_credit": 0,
                             "Source23_retained_uncompressed_upper": OLD_RETAINED_UPPER,
                             "Source23_known_closed_allocated_bytes": OLD_ALLOCATED,
                             "combined_no_compression_peak": OLD_RETAINED_UPPER + GIT_PEAK,
                             "combined_old_actual_variant_peak": OLD_ALLOCATED + GIT_PEAK,
                             "all_original_Source23_full_holds_retained": True},
        "runtime_calls": 0, "SDK_export_calls": 0, "Native_Game_Task_calls": 0,
        "push_calls": 0, "index_or_tracked_worktree_mutations": 0,
        "actual_H": "unknown", "actual_loaded_provider": False, "Native30_bound": False,
    }
    with anchor.open("xb") as receipt:
        def save():
            raw = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode()
            require(len(raw) <= ANCHOR_HARD, "small anchor envelope exceeded")
            receipt.seek(0)
            receipt.truncate()
            receipt.write(raw)
            receipt.flush()
            os.fsync(receipt.fileno())

        save()
        charged_upper = 0
        object_metadata = []

        def write_git(kind, payload_bytes, *parts, data=None):
            nonlocal charged_upper
            charge = upper(kind, payload_bytes) if kind else 0
            require(charged_upper + charge <= retained
                    and OLD_RETAINED_UPPER + charged_upper + charge + largest + 65536 <= GIT_HARD, "cumulative Git write envelope")
            require(shutil.disk_usage(REPO).free >= floor, "fresh full-holds free floor before Git write")
            require(datetime.now(timezone.utc) < datetime.fromisoformat(card["review_at_utc"].replace("Z", "+00:00")),
                    "Git admission expired before write")
            # Charge even if native Git deduplicates an already-existing object.
            charged_upper += charge
            result = git(*parts, data=data)
            if kind:
                written_oid = oid(result)
                loose = common / "objects" / written_oid[:2] / written_oid[2:]
                if loose.exists():
                    identity = ntfs.ntfs_identity(loose)
                    require(not identity["directory"] and type(identity["allocation_bytes"]) is int
                            and 0 <= identity["allocation_bytes"] <= charge and 0 <= identity["bytes"] <= charge,
                            "exact loose-object allocation exceeds conservative charge")
                    object_metadata.append({"oid": written_oid, "charge": charge, **identity})
                else:
                    # hash-object/mktree may reuse a packed object. No dedup or
                    # capacity refund is taken; no pack or Git-directory scan.
                    git("cat-file", "-e", written_oid)
                    object_metadata.append({"oid": written_oid, "charge": charge,
                                            "loose_file_absent": True, "allocation_bytes": None})
            return result

        try:
            for name, raw in sorted(outputs.items()):
                written = oid(write_git("blob", len(raw), "hash-object", "-w", "--stdin", data=raw))
                require(written == expected[name]["git_blob_sha1"], "native written blob differs")
            trees = []

            def rewrite(tree, pending, directory=b""):
                entries = tree_entries(tree)
                groups = {}
                for path, value in pending.items():
                    head, sep, tail = path.partition(b"/")
                    if sep:
                        groups.setdefault(head, {})[tail] = value
                    else:
                        require(entries.get(head, (None, b"blob"))[1] == b"blob", "leaf replaces tree")
                        entries[head] = value
                for name, children in groups.items():
                    require(name in entries and entries[name][1] == b"tree", "missing unchanged parent tree")
                    subdir = directory + (b"/" if directory else b"") + name
                    child = rewrite(entries[name][2].decode(), children, subdir)
                    entries[name] = (b"040000", b"tree", child.encode())
                size = sum(len(mode.lstrip(b"0")) + 1 + len(name) + 1 + 20
                           for name, (mode, kind, child) in entries.items())
                key = directory.decode() if directory else "<root>"
                require(tree_quote.get(key) == size, "native tree payload differs")
                raw = b"".join(mode + b" " + kind + b" " + child + b"\t" + name + b"\0"
                               for name, (mode, kind, child) in sorted(entries.items()))
                result = oid(write_git("tree", size, "mktree", "-z", data=raw))
                trees.append(key)
                return result

            tree = rewrite(oid(git("rev-parse", BASE + "^{tree}")), changes)
            require(len(trees) == len(tree_quote) and set(trees) == set(tree_quote), "tree closure differs")
            verify_tree(tree, expected)
            paths = [v for v in git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", BASE, tree).split(b"\0") if v]
            require(len(paths) == 6 and set(paths) == set(changes), "changes exceed the six admitted paths")
            for name, raw in outputs.items():
                require(pin(git("cat-file", "blob", tree + ":" + PREFIX + name)) == pin(raw),
                        "six body SHA256 readback differs")
            env.update(GIT_AUTHOR_DATE=utc(), GIT_COMMITTER_DATE=utc())
            commit = oid(write_git("commit", 8192, "commit-tree", tree, "-p", BASE,
                             data=b"Source24: frozen continuous-camera wiring over Source23\n"))
            body = git("cat-file", "commit", commit)
            headers = body.split(b"\n\n", 1)[0].splitlines()
            require(len(body) <= 8192 and [v for v in headers if v.startswith(b"tree ")] == [b"tree " + tree.encode()]
                    and [v for v in headers if v.startswith(b"parent ")] == [b"parent " + BASE.encode()],
                    "actual single-parent commit differs")
            record.update(commit=commit, tree=tree,
                          six_output_pins=[expected[n] for n in sorted(outputs)])
            record["charged_retained_objects_upper"] = charged_upper
            record["exact_object_metadata"] = {
                "count": len(object_metadata), "canonical_rows": pin(canonical(object_metadata)),
                "known_loose_allocated_bytes": sum(r["allocation_bytes"] or 0 for r in object_metadata),
                "allocation_unknown_count": sum(r["allocation_bytes"] is None for r in object_metadata),
                "no_directory_scan": True, "no_dedup_credit_or_hold_refund": True,
            }
            save()
            # Empty expected-old OID is a create-only CAS; no force/ref reset.
            require(verify_closed_parent_objects() == parent_metadata_pin, "Source23 metadata changed before ref publication")
            write_git(None, 0, "update-ref", "--no-deref", REF, commit, "0" * 40)
            require(oid(git("rev-parse", "--verify", REF)) == commit, "created Source24 ref differs")
            verify_tree(commit, expected)
            require(verify_closed_parent_objects() == parent_metadata_pin, "Source23 metadata changed during new writes")
            require(charged_upper == retained, "all twelve native object writes must be charged")
            record.update(
                status="CANONICAL_REF_CREATED_NOT_DEPLOYED", end_utc=utc(), future_writes=0,
                source_file_count=1457, source_bytes=59209522, complete_rows_JSON=pin(inventory),
                all1457_Git_mode_blob_size_verified=True, six_SHA256_body_readbacks=True,
                all1457_SHA256_bodies_reread=False, parent1456_Git_mode_blob_size_verified=True,
                complete_rows_SHA256_authority="Frozen full inventory plus Git mode/blob/size; six new body SHA256 readbacks",
                source_epoch_detached_model=report["source_epoch_detached_model"],
                source_epoch_actual_filesystem_authority=False, original_Native29_metadata_retained=True,
                Native_transition_qualification_reused=False, clock_root_cause="UNKNOWN; diagnostic only",
                record_review_at_utc=(datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
            )
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY", end_utc=utc(), future_writes=None,
                          error={"type": type(error).__name__, "text": str(error)[:1024]})
            save()
            raise
        save()
    print(json.dumps({"status": record["status"], "ref": REF, "commit": record["commit"],
                      "tree": record["tree"], "anchor": file_pin(anchor), "runtime_calls": 0}))


if __name__ == "__main__":
    main()

