from __future__ import annotations

"""Freeze the complete committed Root delta consumed by the public runtime builder.

Only small metadata is written. This does not prepare, allocate, launch, compile,
copy a profile, alter Steam, or qualify business behavior.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import ck3_mod_acceptance_build_runtime as builder


def git(root, arguments, *, binary=False):
    argv = ["git", *arguments]
    result = subprocess.run(argv, cwd=root, capture_output=True, check=False)
    builder.require(result.returncode == 0, "Read-only Git observation failed: " + repr(argv))
    return (result.stdout if binary else result.stdout.decode("utf-8").strip()), argv


def root_state(root, commit):
    head, _ = git(root, ["rev-parse", "HEAD"])
    status, _ = git(root, ["status", "--porcelain", "--untracked-files=all"])
    builder.require(head == commit and not status, "Actual Root must be clean at the explicit source commit")


def freeze(args):
    runtime, manifest, refs, source = builder.load_base(args.base_runtime)
    root = Path(runtime["repo_root"]).resolve()
    sys.path.insert(0, str(root / "tools"))
    import ck3_live_run_id
    machine = ck3_live_run_id.current_machine_id()
    builder.require(machine == runtime["machine_id"] == manifest["machine_id"], "Actual source/base machine differs")
    builder.require(re.fullmatch("[0-9a-f]{40}", args.source_commit), "Exact actual Root commit required")
    root_state(root, args.source_commit)
    scene = args.scene_root.resolve()
    grant_ref = builder.pin(args.storage_admission)
    grant = builder.read(args.storage_admission)
    current = datetime.now(timezone.utc)
    builder.require(grant.get("machine_id") == machine and grant.get("active") is True
                    and any(word in grant.get("schema", "").lower() for word in ("capture", "scene", "live"))
                    and Path(grant["approved_root"]).resolve() == scene
                    and datetime.fromisoformat(grant["observed_at_utc"].replace("Z", "+00:00")) <= current
                    < datetime.fromisoformat(grant["expires_at_utc"].replace("Z", "+00:00")),
                    "Actual fresh next-scene storage admission required")
    builder.require(shutil.disk_usage(scene).free >= grant["required_free_bytes"], "Fresh storage admission minimum no longer holds")
    destination = args.output.resolve()
    builder.require(destination != scene and destination.is_relative_to(scene)
                    and not destination.is_relative_to(root) and not destination.exists(),
                    "Write only to a fresh metadata child of the admitted scene")
    paths_raw, argv = git(root, ["diff", "--name-only", "--no-renames", "-z", manifest["source_commit"], args.source_commit, "--"], binary=True)
    names = [name for name in paths_raw.decode("utf-8").split("\0") if name]
    builder.require(len(names) == len(set(names)) and len(names) <= 10000, "Complete finite unique committed path list required")
    native_source = builder.read(refs["native_source_index"]["path"])
    changes = []
    for name in names:
        builder.require("\n" not in name and "\r" not in name, "Multiline source path is not supported")
        builder.classify(name)
        path = (root / name).resolve()
        builder.require(path.is_relative_to(root) and not path.is_symlink(), "Changed source escaped actual Root")
        after = builder.sig(path.read_bytes()) if path.is_file() else None
        changes.append({"path": name, "before": source["files"].get(name), "after": after,
                        "previous_native_pin": native_source["files"].get(name)})
    root_state(root, args.source_commit)
    observed = builder.now()
    paths_bytes = ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    paths_ref = {"path": str(destination / "Root-diff.paths.txt"), **builder.sig(paths_bytes)}
    receipt = {"schema": "ck3-complete-committed-source-diff-v1", "machine_id": machine,
               "observed_at_utc": observed, "base_commit": manifest["source_commit"], "source_commit": args.source_commit,
               "complete_changed_paths": True, "working_tree_clean": True,
               "untracked_runtime_source_inputs_checked": True, "argv": argv, "exit_code": 0,
               "original_wait_returncode": 0, "paths_sha256": paths_ref["sha256"], "path_count": len(names),
               "source_scope": "actual complete committed git diff with renames expanded; current HEAD/status checked before and after hashing changed source",
               "producer": builder.pin(__file__), "game_started": False, "source_changed": False}
    receipt_raw = builder.encoded(receipt)
    receipt_ref = {"path": str(destination / "Root-diff.actual.json"), **builder.sig(receipt_raw)}
    delta = {"schema": "ck3-shared-source-delta-v1", "machine_id": machine,
             "observed_at_utc": observed, "base_source_commit": manifest["source_commit"], "source_commit": args.source_commit,
             "complete_changed_paths_declared_by_Root": True, "base_runtime": builder.pin(args.base_runtime),
             "Root_diff_receipt": receipt_ref, "Root_diff_paths": paths_ref, "new_scene_admission": grant_ref,
             "changes": changes, "native_scope": "native before pins retained separately; a new qualified-native-build is mandatory for all changed native implementation"}
    output = {"Root-diff.paths.txt": paths_bytes, "Root-diff.actual.json": receipt_raw,
              "source-delta.actual.json": builder.encoded(delta)}
    builder.require(sum(map(len, output.values())) + 16384 <= 256 * 1024, "Source delta metadata exceeds 256 KiB bound")
    builder.require(builder.pin(args.storage_admission) == grant_ref, "Admission changed while freezing source metadata")
    destination.mkdir(parents=False)
    for name, raw in output.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    return builder.pin(destination / "source-delta.actual.json")


def main(argv=None):
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base-runtime", "scene-root", "storage-admission", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    print(json.dumps({"source_delta": freeze(args), "game_started": False, "runtime_generated": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
