"""Default-OFF, Root-released create-only Source25 canonical Git writer.

No index/worktree/master/push/export/build/runtime/Task/Game mutation. Source-only
admission never admits Git: a separately pinned concrete Git card is mandatory.
One create-only anchor preserves failure or unknown outcome; never blindly rerun.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import prepare_source25_sdk_v1 as source

REPO, MACHINE, BASE, PREFIX = source.REPO, source.MACHINE, source.BASE_COMMIT, source.PREFIX
REF = "refs/heads/campaign/robert-v20261019-source25-a03-cold-01"
ROOT = REPO / "_runtime/source25-integration16"
ANCHOR = ROOT / "SOURCE25-CANONICAL-ANCHOR.json"
SOURCE_CARD_PIN = (17083, "25322655a77b4da074a0b6f65026c9b4386b7886738df066f07e312559ff77f8")
SOURCE_CARD_NAME = "RESUME-A03-SOURCE-SCREEN-0630-ADMITTED01.json"
NTFS = REPO / "tools/g2_saved_campaign/export_immutable_sdk_views_v1.py"
NTFS_PIN = (22964, "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432")
ANCHOR_HARD = 16384
SOURCE_HARD = 65536
COMPOSER = Path(source.__file__).resolve()
OWNED_SOURCE_NAMES = (
    "tools/g2_saved_campaign/prepare_source25_sdk_v1.py",
    "tools/g2_saved_campaign/write_source25_canonical_ref_v1.py",
    "docs/ck3-native-ai/evidence/source25-sdk-source-plan-2026-10-20.json",
    "docs/ck3-native-ai/evidence/source25-composition-qualification-2026-10-20.json",
)


def require(ok, why):
    if not ok:
        raise RuntimeError("Source25 writer: " + why)


def utc():
    return datetime.now(timezone.utc).isoformat()


def pin(raw):
    return source.pin(raw)


def oid(raw):
    value = raw.decode("ascii").strip()
    require(re.fullmatch("[0-9a-f]{40}", value), "one native SHA1 required")
    return value


def deadline(doc):
    result = datetime.fromisoformat(doc["review_at_utc"].replace("Z", "+00:00"))
    require(result.tzinfo is not None, "timezone required")
    return result


def checked_file_ref(item, path):
    require(type(item) is dict and Path(item["path"]).resolve() == Path(path).resolve(), "input locator differs")
    own = source.file_pin(path)
    require(all(item[k] == own[k] for k in ("bytes", "sha256")), "reviewed input pin differs")
    return own


def source_admission(path):
    require(path.name == SOURCE_CARD_NAME, "new source card locator differs")
    raw = source.check(path.read_bytes(), SOURCE_CARD_PIN, "new joint source card")
    card = json.loads(raw)
    require(card["schema"] == "xar.storage.A03-resume-finite-source-screen-admission.v1"
            and card["status"] == "SOURCE_AND_SCREEN_EVIDENCE_ONLY_ADMITTED"
            and card["machine_id"] == MACHINE and card["source_caps"]["source25_writer"] == SOURCE_HARD,
            "new source-only admission differs")
    require(set(OWNED_SOURCE_NAMES[:2]).issubset(card["writer_finite_names"]), "source finite names missing")
    require(datetime.now(timezone.utc) < deadline(card), "source admission expired")
    total = sum((REPO / n).stat().st_size for n in OWNED_SOURCE_NAMES if (REPO / n).exists())
    require(total <= SOURCE_HARD, "complete source/proof full bytes exceed64KiB")
    return card, {"path": str(path.resolve()), **pin(raw)}, total


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source-card", type=Path)
    parser.add_argument("--git-card", type=Path)
    parser.add_argument("--git-card-sha256")
    parser.add_argument("--execute-root-writer", action="store_true")
    parser.add_argument("--preflight-root-writer", action="store_true")
    args = parser.parse_args()
    if not args.execute_root_writer and not args.preflight_root_writer:
        print('{"status":"DISABLED","Git_mutations":0,"runtime_calls":0}')
        return
    require(args.source_card is not None and args.git_card is not None
            and type(args.git_card_sha256) is str and re.fullmatch("[0-9a-f]{64}", args.git_card_sha256),
            "reviewed source and concrete Git cards required")
    started = utc()
    source_card, source_ref, source_total = source_admission(args.source_card)
    raw_card = args.git_card.read_bytes()
    require(len(raw_card) <= 65536 and pin(raw_card)["sha256"] == args.git_card_sha256, "concrete Git card SHA differs")
    card = json.loads(raw_card)
    require(card["schema"] == "xar.storage.Source25-root-canonical-Git.v1"
            and card["machine_id"] == MACHINE and card["owner"] == "Root" and card["status"] == "ADMITTED"
            and card["root_direct_execution_release"] is True and card["canonical_parent"] == BASE,
            "concrete Root Git admission differs")
    require(datetime.now(timezone.utc) < deadline(card), "Git admission expired")
    checked_file_ref(card["source_admission"], args.source_card)
    own = checked_file_ref(card["writer"], Path(__file__))
    composer_ref = checked_file_ref(card["composer"], COMPOSER)
    plan_ref = checked_file_ref(card["source_plan"], source.PLAN)
    plan = json.loads(source.PLAN.read_bytes())
    require(Path(card["integration_root"]).resolve() == ROOT.resolve()
            and Path(card["future_anchor"]).resolve() == ANCHOR.resolve()
            and card["anchor_hard_bytes"] == ANCHOR_HARD
            and type(card["metadata_hard_bytes"]) is int and card["metadata_hard_bytes"] >= ANCHOR_HARD,
            "exact new integration/anchor bound differs")
    require(not ANCHOR.exists() and not ANCHOR.is_symlink(), "create-only Source25 anchor already exists")
    for path in (ROOT, *ROOT.parents):
        if path.exists():
            require(not path.is_symlink() and not (getattr(path.lstat(), "st_file_attributes", 0) & 0x400),
                    "integration root contains reparse node")
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
        str(REPO / "tools/ck3_live_run_id.py"), "machine"], cwd=REPO).decode().strip()
    require(machine == MACHINE, "actual execution machine differs")
    floor = card["capacity"]["Z_conservative_floor_bytes"]
    require(type(floor) is int and floor >= 0 and shutil.disk_usage(REPO).free >= floor,
            "fresh coordinated free floor unavailable")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        require(not os.environ.get(key), "ambient Git redirection: " + key)
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    hooks = ROOT / "disabled-hooks-must-remain-absent"
    require(not hooks.exists(), "unexpected hooks path")
    prefix = ["git", "-C", str(REPO), "-c", "gc.auto=0", "-c", "maintenance.auto=false",
              "-c", "commit.gpgsign=false", "-c", "i18n.commitEncoding=utf-8", "-c", "core.hooksPath=" + str(hooks)]

    def command(*parts, data=None, allowed=(0,)):
        result = subprocess.run(prefix + list(parts), input=data, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env, check=False)
        require(result.returncode in allowed, "Git " + parts[0] + " failed: " + result.stderr[:1024].decode(errors="replace"))
        require(len(result.stdout) <= 2 * 1024**2 and len(result.stderr) <= 65536, "Git metadata/body cap")
        return result.returncode, result.stdout

    def git(*parts, data=None):
        return command(*parts, data=data)[1]

    require(git("rev-parse", "--show-object-format").strip() == b"sha1", "Git object format differs")
    common = Path(os.fsdecode(git("rev-parse", "--git-common-dir").strip()))
    common = common.resolve() if common.is_absolute() else (REPO / common).resolve()
    require(common == (REPO / ".git").resolve() == Path(card["Git"]["root"]).resolve(), "canonical Git root differs")
    require(oid(git("rev-parse", "--verify", BASE + "^{commit}")) == BASE
            and oid(git("rev-parse", "--verify", source.BASE_REF)) == BASE, "actual Source24 parent differs")
    require(command("show-ref", "--verify", "--quiet", REF, allowed=(0, 1))[0] == 1
            and command("symbolic-ref", "--quiet", REF, allowed=(0, 1))[0] == 1, "Source25 ref already exists")
    source.check(NTFS.read_bytes(), NTFS_PIN, "frozen NTFS metadata helper")
    spec = importlib.util.spec_from_file_location("source25_metadata_only", NTFS)
    ntfs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ntfs)
    require(ntfs.ntfs_identity(common)["cluster_bytes"] == 4096, "actual allocation unit differs")
    outputs, rows, report = source.compose(verify_all_base=False)
    quote = source.quote(outputs, rows)["Git"]
    require(plan["schema"] == report["schema"] and plan["machine_id"] == MACHINE
            and all(plan[k] == report[k] for k in ("base", "output", "delta", "source_epoch_detached_model"))
            and plan["Git_object_quote"] == quote, "reviewed final source plan differs")
    require(card["Git"]["peak_upper_bytes"] == quote["peak_upper"]
            and type(card["Git"]["hard_bytes"]) is int and card["Git"]["hard_bytes"] >= quote["peak_upper"]
            and card["Git"]["prior_holds_retained"] is True, "concrete Git bound/old holds differ")
    require(len(git("var", "GIT_AUTHOR_IDENT")) + len(git("var", "GIT_COMMITTER_IDENT")) < 4096,
            "commit identities exceed bounded payload")
    expected = {r["relative"]: r for r in rows}
    changes = {(PREFIX + name).encode(): (expected[name]["git_mode"].encode(), b"blob", expected[name]["git_blob_sha1"].encode())
               for name in outputs}
    parent_raw = source.check(source.PARENT_ANCHOR.read_bytes(), source.PARENT_ANCHOR_PIN, "actual parent anchor")
    parent_anchor = json.loads(parent_raw)

    def parent_metadata():
        pairs = [(r["git_blob_sha1"], source.object_upper("blob", r["bytes"]))
                 for r in sorted(parent_anchor["six_output_pins"], key=lambda r: r["relative"])]
        for directory, size in (("ck3_autonomous_player/src/xar_autoplayer/bridge", 41124),
                ("ck3_autonomous_player/src/xar_autoplayer", 12654), ("ck3_autonomous_player/src", 41),
                ("ck3_autonomous_player", 1122), ("", 1565)):
            value = oid(git("rev-parse", BASE + (":" + directory if directory else "^{tree}")))
            require(int(git("cat-file", "-s", value)) == size, "original Source24 tree payload differs")
            pairs.append((value, source.object_upper("tree", size)))
        pairs.append((BASE, source.object_upper("commit", 8192)))
        require(len(pairs) == len({oid for oid, _ in pairs}) == 12, "twelve original Source24 objects required")
        metadata = []
        for value, charge in pairs:
            identity = ntfs.ntfs_identity(common / "objects" / value[:2] / value[2:])
            require(not identity["directory"] and type(identity["allocation_bytes"]) is int
                    and 0 <= identity["allocation_bytes"] <= charge, "original Source24 allocation differs")
            metadata.append({"oid": value, "charge": charge, **identity})
        require(pin(source.canonical(metadata)) == parent_anchor["exact_object_metadata"]["canonical_rows"]
                and sum(r["allocation_bytes"] for r in metadata) == 536824, "original Source24 exact identities changed")
        return pin(source.canonical(metadata))

    old_metadata_pin = parent_metadata()
    if args.preflight_root_writer:
        print(json.dumps({"status": "PREFLIGHT_READY_NO_WRITES", "parent": BASE, "ref": REF,
            "output": report["output"], "Git_object_quote": quote,
            "parent_twelve_exact_metadata": old_metadata_pin, "Git_mutations": 0,
            "SDK_exports": 0, "runtime_calls": 0}))
        return
    # All source/tree/admission checks above precede the first directory/Git write.
    ROOT.mkdir(exist_ok=True)
    record = {"schema": "xar.source25.canonical-git-anchor/v1", "machine_id": machine,
        "start_utc": started, "status": "RUNNING_OR_UNKNOWN", "execution_owner": "Root",
        "root_direct_execution_release": True, "parent": BASE, "ref": REF,
        "source_commitment": source_ref, "source_complete_logical_bytes": source_total,
        "capacity_card": {"path": str(args.git_card.resolve()), **pin(raw_card)},
        "writer": own, "composer": composer_ref, "source_plan": plan_ref,
        "actual_Source24_anchor": {"path": str(source.PARENT_ANCHOR), **pin(parent_raw)},
        "Source24_twelve_exact_metadata": old_metadata_pin, "metadata_only_helper": source.file_pin(NTFS),
        "Git_object_quote": {k: v for k, v in quote.items() if k != "objects"},
        "runtime_calls": 0, "SDK_export_calls": 0, "Native_Game_Task_calls": 0, "push_calls": 0,
        "index_or_tracked_worktree_mutations": 0, "actual_H": "unknown", "actual_loaded_provider": False,
        "Native30_bound": False}
    with ANCHOR.open("xb") as receipt:
        def save():
            raw = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode()
            require(len(raw) <= ANCHOR_HARD, "small anchor envelope exceeded")
            receipt.seek(0)
            receipt.truncate()
            receipt.write(raw)
            receipt.flush()
            os.fsync(receipt.fileno())

        save()
        charged, metadata = 0, []

        def still_admitted():
            require(datetime.now(timezone.utc) < min(deadline(card), deadline(source_card)), "admission expired before write")
            require(shutil.disk_usage(REPO).free >= floor, "coordinated free floor unavailable before write")

        def write_git(kind, size, *parts, data=None):
            nonlocal charged
            charge = source.object_upper(kind, size) if kind else 0
            require(charged + charge <= quote["retained_upper"]
                    and charged + charge + quote["largest_temporary_upper"] + 65536 <= card["Git"]["hard_bytes"],
                    "cumulative uncompressed Git envelope exceeded")
            still_admitted()
            charged += charge  # No credit even for native Git deduplication.
            result = git(*parts, data=data)
            if kind:
                value = oid(result)
                loose = common / "objects" / value[:2] / value[2:]
                if loose.exists():
                    identity = ntfs.ntfs_identity(loose)
                    require(not identity["directory"] and 0 <= identity["allocation_bytes"] <= charge
                            and 0 <= identity["bytes"] <= charge, "new exact loose allocation exceeds charge")
                    metadata.append({"oid": value, "charge": charge, **identity})
                else:
                    git("cat-file", "-e", value)
                    metadata.append({"oid": value, "charge": charge, "loose_file_absent": True, "allocation_bytes": None})
            return result

        try:
            for name, raw in sorted(outputs.items()):
                require(oid(write_git("blob", len(raw), "hash-object", "-w", "--stdin", data=raw))
                        == expected[name]["git_blob_sha1"], "native written blob differs")
            rewritten = []

            def rewrite(tree, pending, directory=b""):
                entries = source.tree_entries(tree)
                groups = {}
                for path, value in pending.items():
                    head, sep, tail = path.partition(b"/")
                    if sep:
                        groups.setdefault(head, {})[tail] = value
                    else:
                        require(entries.get(head, (None, b"blob"))[1] == b"blob", "leaf replaces a tree")
                        entries[head] = value
                for name, children in groups.items():
                    require(name in entries and entries[name][1] == b"tree", "missing unchanged ancestor")
                    subdir = directory + (b"/" if directory else b"") + name
                    entries[name] = (b"040000", b"tree", rewrite(entries[name][2].decode(), children, subdir).encode())
                size = sum(len(mode.lstrip(b"0")) + 1 + len(name) + 1 + 20 for name, (mode, kind, child) in entries.items())
                key = directory.decode() if directory else "<root>"
                require(quote["tree_payloads"].get(key) == size, "native tree payload differs")
                raw = b"".join(mode + b" " + kind + b" " + child + b"\t" + name + b"\0"
                               for name, (mode, kind, child) in sorted(entries.items()))
                result = oid(write_git("tree", size, "mktree", "-z", data=raw))
                rewritten.append(key)
                return result

            tree = rewrite(oid(git("rev-parse", BASE + "^{tree}")), changes)
            require(len(rewritten) == 5 and set(rewritten) == set(quote["tree_payloads"]), "tree closure differs")
            source.verify_tree(tree, rows)
            diff = [p for p in git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", BASE, tree).split(b"\0") if p]
            require(len(diff) == 9 and set(diff) == set(changes), "changes exceed nine package paths")
            for name, raw in outputs.items():
                require(pin(git("cat-file", "blob", tree + ":" + PREFIX + name)) == pin(raw), "new body SHA256 readback differs")
            env.update(GIT_AUTHOR_DATE=utc(), GIT_COMMITTER_DATE=utc())
            commit = oid(write_git("commit", 8192, "commit-tree", tree, "-p", BASE,
                data=b"Source25: qualified preload, nonleading siege and wait diagnostics over Source24\n"))
            body = git("cat-file", "commit", commit)
            headers = body.split(b"\n\n", 1)[0].splitlines()
            require(len(body) <= 8192 and [h for h in headers if h.startswith(b"tree ")] == [b"tree " + tree.encode()]
                    and [h for h in headers if h.startswith(b"parent ")] == [b"parent " + BASE.encode()], "single-parent commit differs")
            record.update(commit=commit, tree=tree, nine_output_pins=[expected[n] for n in sorted(outputs)],
                charged_retained_objects_upper=charged, exact_object_metadata={"count": len(metadata),
                    "canonical_rows": pin(source.canonical(metadata)),
                    "known_loose_allocated_bytes": sum(r["allocation_bytes"] or 0 for r in metadata),
                    "allocation_unknown_count": sum(r["allocation_bytes"] is None for r in metadata),
                    "no_directory_scan": True, "no_dedup_credit_or_hold_refund": True})
            save()
            require(parent_metadata() == old_metadata_pin, "Source24 objects changed before ref publication")
            write_git(None, 0, "update-ref", "--no-deref", REF, commit, "0" * 40)
            require(oid(git("rev-parse", "--verify", REF)) == commit, "created Source25 ref differs")
            source.verify_tree(commit, rows)
            require(parent_metadata() == old_metadata_pin and charged == quote["retained_upper"], "final object accounting differs")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED", end_utc=utc(), future_writes=0,
                source_file_count=1460, source_bytes=59234989, complete_rows_JSON=pin(source.canonical(rows)),
                all1460_Git_mode_blob_size_verified=True, nine_SHA256_body_readbacks=True,
                all1460_SHA256_bodies_reread=False, parent1457_Git_mode_blob_size_verified=True,
                source_epoch_detached_model=report["source_epoch_detached_model"],
                source_epoch_actual_filesystem_authority=False, original_13_19_5_qualifications_reused_not_rerun=True,
                original_Source24_Source23_holds_retained=True, clock_root_cause="UNKNOWN; diagnostic only",
                record_review_at_utc=(datetime.now(timezone.utc) + timedelta(days=180)).isoformat())
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY", end_utc=utc(), future_writes=None,
                          error={"type": type(error).__name__, "text": str(error)[:1024]})
            save()
            raise
        save()
    print(json.dumps({"status": record["status"], "ref": REF, "commit": record["commit"],
                      "tree": record["tree"], "anchor": source.file_pin(ANCHOR), "runtime_calls": 0}))


if __name__ == "__main__":
    main()
