"""Explicit one-Python-host successor for the real original Native source root.

The old Q/snapshot/File API/DLL remain immutable. The original host bytes are
preserved separately and verified against the original Git blob; every other
Native input is still read at its real path. This grants source equivalence,
never a new Native build or live qualification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Protocol, TypedDict, runtime_checkable

NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
HOST_RELATIVE = NATIVE_PREFIX + "research/run_ck3_12002_mcp_live.py"
HOST_NATIVE_RELATIVE = HOST_RELATIVE.removeprefix(NATIVE_PREFIX)
SCHEMA = "ck3-native-same-root-shared-python-host-binding-v1"
DELTA_SCHEMA = "ck3-exact-same-root-python-host-delta-v1"
FIELDS = frozenset({"schema", "machine_id", "observed_at_utc", "runtime_repo_root",
    "runtime_source_commit", "native_source_repo_root", "native_source_commit", "native_source_base",
    "native_subtree_tree_id", "runtime_native_subtree_tree_id", "common_git_directory",
    "qualified_native", "snapshot", "shared_python_host_delta", "original_shared_host_blob"})


class Signature(TypedDict):
    bytes: int
    sha256: str


class FilePin(Signature):
    path: str


class SourceContext(TypedDict):
    native_source_base: Path
    binding_ref: FilePin
    runtime_shared_host_pin: FilePin
    original_shared_host_blob: FilePin
    shared_python_host_delta: FilePin
    shared_host_qualification: FilePin


@runtime_checkable
class SharedDeltaAPI(Protocol):
    def compiled_inputs(self, qualification: dict[str, object], snapshot: dict[str, object]) -> object: ...
    def qualify_shared_host_delta(self, path: Path, *, root: Path, native_repo: Path,
        runtime_commit: str, native_commit: str, machine: str, qualified_native_ref: object,
        qualification: dict[str, object], snapshot_ref: object, snapshot: dict[str, object],
        same_root_before_blob: object = None) -> object: ...


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("JSON object keys must be strings")
        result[key] = item
    return result


def arr(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("JSON array required")
    return list(value)


def string(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty string required")
    return value


def exact_integer(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("Positive exact integer required")
    return value


def signature(raw: bytes) -> Signature:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def parse_signature(value: object) -> Signature:
    row = obj(value)
    require(set(row) == {"bytes", "sha256"}, "Exact signature fields required")
    digest = string(row["sha256"])
    require(re.fullmatch(r"[0-9a-f]{64}", digest), "Canonical SHA256 required")
    return {"bytes": exact_integer(row["bytes"]), "sha256": digest}


def pin(path: Path) -> FilePin:
    path = path.resolve()
    return {"path": str(path), **signature(path.read_bytes())}


def parse_pin(value: object) -> FilePin:
    row = obj(value)
    require(set(row) == {"path", "bytes", "sha256"}, "Exact file pin fields required")
    path = Path(string(row["path"]))
    require(path.is_absolute(), "Absolute pin path required")
    return {"path": str(path), **parse_signature({key: row[key] for key in ("bytes", "sha256")})}


def checked(value: object) -> FilePin:
    expected = parse_pin(value)
    require(not Path(expected["path"]).is_symlink() and pin(Path(expected["path"])) == expected,
            "Exact source/evidence pin changed: " + expected["path"])
    return expected


def read(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return obj(value)


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True, check=True).stdout


def timestamp(value: object) -> datetime:
    result = datetime.fromisoformat(string(value).replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Timezone-aware observation required")
    return result.astimezone(timezone.utc)


def shared_api() -> SharedDeltaAPI:
    path = Path(__file__).with_name("ck3_mod_acceptance_shared_python_host_delta.py")
    spec = importlib.util.spec_from_file_location("same_root_original_shared_delta", path)
    if spec is None or spec.loader is None:
        raise ValueError("Shared host-delta validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module, SharedDeltaAPI):
        raise ValueError("Shared host-delta validator interface differs")
    return module


def validate_compiled_inputs(declared: object, actual: object) -> None:
    value = obj(declared)
    refs = {"configured_scope", "codemodel", "compile_commands", "production_freeze", "published_dll"}
    require(set(value) == refs | {"production_TUs", "unique_production_source_count", "production_source_set_sha256"},
            "Exact original compiled-input fields required")
    for name in refs:
        checked(value[name])
    counts = obj(value["production_TUs"])
    require(counts, "Actual production TU counts required")
    for count in counts.values():
        exact_integer(count)
    exact_integer(value["unique_production_source_count"])
    require(re.fullmatch(r"[0-9a-f]{64}", string(value["production_source_set_sha256"])),
            "Exact production source-set digest required")
    require(json.dumps(value, sort_keys=True, allow_nan=False) == json.dumps(actual, sort_keys=True, allow_nan=False),
            "Original compiled cohort changed")


def qualify_same_root_host(binding_path: Path, *, root: Path, runtime_commit: str,
    native_commit: str, machine: str, qualified_native_ref: object, qualification: object,
    snapshot_ref: object, snapshot: object, native_shared_python_host_delta: Path | None) -> SourceContext:
    root = root.resolve()
    native = (root / NATIVE_PREFIX).resolve()
    binding_ref = pin(binding_path)
    binding = read(binding_path)
    q, source = obj(qualification), obj(snapshot)
    require(set(binding) == FIELDS and binding["schema"] == SCHEMA, "Exact same-root host binding required")
    if native_shared_python_host_delta is None:
        raise ValueError("Explicit reviewed same-root host delta required")
    require(binding["machine_id"] == machine == q.get("machine_id") == source.get("machine_id"),
            "Same-root source identities belong to another machine")
    require(re.fullmatch(r"[0-9a-f]{40}", runtime_commit) and re.fullmatch(r"[0-9a-f]{40}", native_commit)
            and binding["runtime_source_commit"] == runtime_commit and binding["native_source_commit"] == native_commit
            and q.get("source_commit") == native_commit and source.get("root_commit") == native_commit,
            "Preserve the distinct exact runtime and original Native commits")
    qref, sref = checked(qualified_native_ref), checked(snapshot_ref)
    require(checked(binding["qualified_native"]) == qref and checked(binding["snapshot"]) == sref
            and read(Path(qref["path"])) == q and read(Path(sref["path"])) == source,
            "Original qualification/snapshot identity differs")
    require(timestamp(q.get("observed_at_utc")) <= timestamp(binding["observed_at_utc"]) <= datetime.now(timezone.utc),
            "Same-root binding observation must follow the original qualification")
    require(Path(string(binding["runtime_repo_root"])).resolve() == root
            == Path(string(binding["native_source_repo_root"])).resolve()
            and Path(string(binding["native_source_base"])).resolve() == native
            == Path(string(source["Root_native_source_base"])).resolve()
            == Path(string(source["snapshot_native_base"])).resolve(),
            "Same-root binding must retain the actual original compile paths")
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root
            and git(root, "rev-parse", "HEAD").decode().strip() == runtime_commit
            and not git(root, "status", "--porcelain", "--untracked-files=all").strip(),
            "Actual current runtime Root must be clean at its exact commit")
    common = (root / git(root, "rev-parse", "--git-common-dir").decode().strip()).resolve()
    require(Path(string(binding["common_git_directory"])).resolve() == common, "Actual Git store differs")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", native_commit, runtime_commit], cwd=root, capture_output=True)
    require(ancestor.returncode == 0, "Same-root Native compile commit must remain an ancestor")
    for key, commit in (("native_subtree_tree_id", native_commit), ("runtime_native_subtree_tree_id", runtime_commit)):
        require(binding[key] == git(root, "rev-parse", commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
                "Explicit Native Git tree identity differs")
    changed = {name for name in git(root, "diff", "--name-only", "-z", native_commit, runtime_commit,
        "--", NATIVE_PREFIX).decode().split("\0") if name}
    require(changed == {HOST_RELATIVE}, "Same-root Native differences must be exactly the canonical host")
    original_blob = checked(binding["original_shared_host_blob"])
    original_signature: Signature = {"bytes": original_blob["bytes"], "sha256": original_blob["sha256"]}
    require(not Path(original_blob["path"]).resolve().is_relative_to(root), "Original host blob must be separately preserved")
    require(signature(git(root, "show", native_commit + ":" + HOST_RELATIVE))
            == original_signature, "Original host blob is not the actual old Git content")
    rows = arr(source["files"])
    require(exact_integer(source["source_count"]) == len(rows), "Complete original Native source count differs")
    declared: set[str] = set()
    for raw in rows:
        row = obj(raw)
        require(set(row) == {"native_relative", "bytes", "sha256"}, "Direct original Native source rows required")
        name = string(row["native_relative"])
        require(not Path(name).anchor and "\\" not in name and ":" not in name
                and all(part not in {"", ".", ".."} for part in name.split("/"))
                and name not in declared, "Unsafe or duplicate Native source row")
        declared.add(name)
        expected = parse_signature({key: row[key] for key in ("bytes", "sha256")})
        current = native / name
        require(not current.is_symlink(), "Native inputs cannot be symbolic")
        if name == HOST_NATIVE_RELATIVE:
            require(expected == original_signature, "Before blob differs from the original snapshot host")
        else:
            require(signature(current.read_bytes()) == expected, "Non-host Native raw input changed: " + name)
    for command in (("ls-files", "-z", "--", NATIVE_PREFIX),
                    ("ls-tree", "-r", "--name-only", "-z", native_commit, "--", NATIVE_PREFIX)):
        tracked = {name.removeprefix(NATIVE_PREFIX) for name in git(root, *command).decode().split("\0") if name}
        require(tracked == declared, "Complete original/current Native path set differs")
    delta_ref = checked(binding["shared_python_host_delta"])
    require(delta_ref == pin(native_shared_python_host_delta), "Reviewed same-root delta pin differs")
    delta = read(native_shared_python_host_delta)
    require(delta.get("schema") == DELTA_SCHEMA, "Explicit same-root delta schema required")
    api = shared_api()
    validate_compiled_inputs(delta.get("compiled_inputs"), api.compiled_inputs(q, source))
    context = obj(api.qualify_shared_host_delta(native_shared_python_host_delta, root=root, native_repo=root,
        runtime_commit=runtime_commit, native_commit=native_commit, machine=machine,
        qualified_native_ref=qualified_native_ref, qualification=q, snapshot_ref=snapshot_ref, snapshot=source,
        same_root_before_blob=original_blob))
    return {"native_source_base": native, "binding_ref": binding_ref,
        "runtime_shared_host_pin": checked(context["runtime_host_pin"]), "original_shared_host_blob": original_blob,
        "shared_python_host_delta": delta_ref, "shared_host_qualification": checked(context["shared_host_qualification"])}


def produce_binding(root: Path, qualification_path: Path, delta_path: Path, original_blob: Path,
                    output: Path, machine: str) -> FilePin:
    root = root.resolve()
    qref = pin(qualification_path)
    q = read(qualification_path)
    snapshot_ref = checked(q["snapshot"])
    source = read(Path(snapshot_ref["path"]))
    native_commit, runtime_commit = string(q["source_commit"]), git(root, "rev-parse", "HEAD").decode().strip()
    native = root / NATIVE_PREFIX
    value = {"schema": SCHEMA, "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_repo_root": str(root), "runtime_source_commit": runtime_commit, "native_source_repo_root": str(root),
        "native_source_commit": native_commit, "native_source_base": str(native.resolve()),
        "native_subtree_tree_id": git(root, "rev-parse", native_commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
        "runtime_native_subtree_tree_id": git(root, "rev-parse", runtime_commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
        "common_git_directory": str((root / git(root, "rev-parse", "--git-common-dir").decode().strip()).resolve()),
        "qualified_native": qref, "snapshot": snapshot_ref, "shared_python_host_delta": pin(delta_path),
        "original_shared_host_blob": pin(original_blob)}
    require(not output.resolve().is_relative_to(root), "Source-binding output must remain outside the checkout")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
    qualify_same_root_host(output, root=root, runtime_commit=runtime_commit, native_commit=native_commit,
        machine=machine, qualified_native_ref=qref, qualification=q, snapshot_ref=snapshot_ref,
        snapshot=source, native_shared_python_host_delta=delta_path)
    return pin(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo-root", "qualification", "host-delta", "original-host-blob", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
        str(args.repo_root / "tools/ck3_live_run_id.py"), "machine"], cwd=args.repo_root).decode().strip()
    result = produce_binding(args.repo_root, args.qualification, args.host_delta, args.original_host_blob, args.output, machine)
    print(json.dumps({"source_binding": result, "native_rebuilt": False, "game_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
