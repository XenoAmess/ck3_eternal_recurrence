"""Explicitly bind the three reviewed offline research changes beside Q21.

The original build and every other Native byte stay frozen.  This is not an
exact-Native-tree contract and does not qualify these scripts' game behavior.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
from typing import TypedDict

SCHEMA = "ck3-native-worktree-research-delta-source-binding-v1"
PREFIX = "ck3_autonomous_player/native_bridge/"
REVIEWED_ORIGIN = "39e59acce6624edbc30322e4797d2e421c0a44aa"
JSONObject = dict[str, object]


class Signature(TypedDict):
    bytes: int
    sha256: str


class FilePin(Signature):
    path: str


class ResearchContext(TypedDict):
    runtime_research_pins: dict[str, FilePin]
    added_runtime_research_paths: tuple[str, ...]


# This is the reviewed M/A/M transition, not a caller-supplied allowlist.
APPROVED: tuple[tuple[str, str, Signature | None, Signature], ...] = (
    ("research/maintenance_writer_cold_12004/run_cold_fixture.py", "M",
     {"bytes": 18315, "sha256": "d55853f9302b118b047c738b419025922959436b1c7768ecb0fabc625cd5a761"},
     {"bytes": 21033, "sha256": "40ce68187f30774364756478cf9c425b9c36e1fe7356158327bb776a751dc316"}),
    ("research/maintenance_writer_cold_12004/test_run_cold_fixture_selection.py", "A", None,
     {"bytes": 9780, "sha256": "7b9a2cc7e4fb0fc777b39163f1039506e01aed05a42948a4f948d9f00a3b5371"}),
    ("research/refill_add_live_12004/consume_live_refill_add.py", "M",
     {"bytes": 6158, "sha256": "ae99e511ba8a44430417a47103d6d535c4508384d200123372b9655954597c2b"},
     {"bytes": 6391, "sha256": "cc64032d7ffb1325724871b3a4c124d042d1c643c22125b6db7f825770e9c4b8"}),
)


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def fields(value: object) -> JSONObject:
    if not isinstance(value, dict):
        raise ValueError("Research source evidence must be an object")
    result: JSONObject = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Research source evidence keys must be text")
        result[key] = item
    return result


def items(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Research source evidence must contain a list")
    result: list[object] = value
    return result


def text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Research source evidence text is missing")
    return value


def signature(raw: bytes) -> Signature:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def pin(path: Path) -> FilePin:
    require(not path.is_symlink(), "Research evidence cannot be symbolic")
    path = path.resolve()
    return {"path": str(path), **signature(path.read_bytes())}


def checked(value: object) -> FilePin:
    row = fields(value)
    require(set(row) == {"path", "bytes", "sha256"}, "Research evidence pin fields differ")
    actual = pin(Path(text(row.get("path"))))
    require(actual == row, "Research evidence raw pin changed")
    return actual


def read(path: Path) -> JSONObject:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return fields(value)


def git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True).stdout


def dependency_paths(raw: bytes, build: Path) -> tuple[set[Path], int]:
    """Strictly read Ninja v4 path/checksum and dependency records.

    No binary, compiler or Ninja process is executed by the public consumer.
    Unknown versions, partial records, invalid IDs and malformed padding fail.
    All path records are checked, including superseded dependency records.
    """
    require(raw[:16] == b"# ninjadeps\n\x04\x00\x00\x00", "Only complete Ninja v4 dependencies are supported")
    offset, records = 16, 0
    paths: list[Path] = []
    while offset < len(raw):
        require(offset + 4 <= len(raw), "Truncated Ninja dependency record size")
        flagged = struct.unpack_from("<I", raw, offset)[0]
        size = flagged & 0x7fffffff
        offset += 4
        require(0 < size <= (1 << 19) - 1 and size % 4 == 0 and offset + size <= len(raw),
                "Malformed Ninja dependency record")
        body = raw[offset:offset + size]
        offset += size
        if flagged & 0x80000000:
            require(size >= 12, "Ninja dependency body is truncated")
            ids = [struct.unpack_from("<I", body, at)[0] for at in [0, *range(12, size, 4)]]
            require(all(index < len(paths) for index in ids), "Ninja dependency references an unknown path")
            records += 1
        else:
            require(size >= 8, "Ninja dependency path is truncated")
            payload = body[:-4]
            name_raw = payload.rstrip(b"\x00")
            require(name_raw and len(payload) - len(name_raw) <= 3 and b"\x00" not in name_raw,
                    "Ninja dependency path padding differs")
            require(struct.unpack_from("<I", body, size - 4)[0] == (~len(paths) & 0xffffffff),
                    "Ninja dependency path checksum differs")
            name = name_raw.decode("utf-8")
            path = Path(name)
            paths.append(path.resolve() if path.is_absolute() else (build / path).resolve())
    require(records > 0 and paths, "Actual compiler dependency records are required")
    return set(paths), records


def dependency_exclusion(qualification: JSONObject, snapshot: JSONObject) -> JSONObject:
    scope_ref = checked(qualification.get("configured_scope"))
    scope = read(Path(scope_ref["path"]))
    require(scope.get("snapshot") == qualification.get("snapshot"), "Research FileAPI snapshot differs")
    model_ref = checked(scope.get("codemodel"))
    commands_ref = checked(scope.get("compile_commands"))
    model = read(Path(model_ref["path"]))
    paths = fields(model.get("paths"))
    native = Path(text(snapshot.get("snapshot_native_base"))).resolve()
    require(Path(text(paths.get("source"))).resolve() == native, "Research FileAPI uses another source checkout")
    build = Path(text(paths.get("build"))).resolve()
    forbidden = {native / relative for relative, _, _, _ in APPROVED}
    reply = Path(model_ref["path"]).parent
    configurations = items(model.get("configurations"))
    require(len(configurations) == 1, "Research FileAPI configuration is ambiguous")
    targets = items(fields(configurations[0]).get("targets"))
    for entry in targets:
        target_path = (reply / text(fields(entry).get("jsonFile"))).resolve()
        require(target_path.is_relative_to(reply), "Research FileAPI target escapes its original reply")
        target = read(target_path)
        for source in items(target.get("sources", [])):
            path = Path(text(fields(source).get("path")))
            actual = path.resolve() if path.is_absolute() else (native / path).resolve()
            require(actual not in forbidden, "Reviewed research path entered an actual FileAPI target")
    command_value: object = json.loads(Path(commands_ref["path"]).read_text(encoding="utf-8-sig"))
    for command in items(command_value):
        row = fields(command)
        path = Path(text(row.get("file"))).resolve()
        require(path not in forbidden, "Reviewed research path entered compile commands")
        command_text = text(row.get("command")).replace("\\", "/").lower()
        require(not any(relative.lower() in command_text for relative, _, _, _ in APPROVED),
                "Reviewed research path entered a compiler command argument")
    ninja = build / "build.ninja"
    deps = build / ".ninja_deps"
    ninja_ref, deps_ref = pin(ninja), pin(deps)
    ninja_text = ninja.read_bytes().replace(b"\\", b"/").lower()
    require(not any(relative.encode().lower() in ninja_text for relative, _, _, _ in APPROVED),
            "Reviewed research path entered the configured Ninja graph")
    dependencies, records = dependency_paths(deps.read_bytes(), build)
    require(not (dependencies & forbidden), "Reviewed research path entered actual compiler dependencies")
    require(pin(ninja) == ninja_ref and pin(deps) == deps_ref,
            "Actual compiler dependency inputs changed during observation")
    return {"configured_scope": scope_ref, "codemodel": model_ref, "compile_commands": commands_ref,
            "build_ninja": ninja_ref, "ninja_deps": deps_ref, "dependency_path_count": len(dependencies),
            "dependency_record_count": records, "all_fileapi_target_count": len(targets)}


def produce_research_delta(*, root: Path, native_repo: Path, runtime_commit: str,
                           native_commit: str, qualification: JSONObject, snapshot: JSONObject) -> JSONObject:
    """Produce the sole approved M/A/M declaration from actual Git/raw inputs."""
    diff = git_bytes(root, "diff", "--name-status", "--no-renames", native_commit, runtime_commit, "--", PREFIX)
    actual_diff = {tuple(line.split("\t")) for line in diff.decode("utf-8").splitlines()}
    require(actual_diff == {(status, PREFIX + relative) for relative, status, _, _ in APPROVED},
            "Only the three reviewed offline research changes may differ from the compile tree")
    snapshot_rows = {text(fields(row).get("native_relative")): fields(row) for row in items(snapshot.get("files"))}
    rows: list[JSONObject] = []
    for relative, status, before, after in APPROVED:
        repo_relative = PREFIX + relative
        require(signature(git_bytes(root, "show", runtime_commit + ":" + repo_relative)) == after,
                "Runtime research Git blob differs from its reviewed exact raw identity")
        actual = pin(root / repo_relative)
        require({"bytes": actual["bytes"], "sha256": actual["sha256"]} == after,
                "Runtime research checkout differs from its reviewed exact raw identity")
        if before is None:
            exists = subprocess.run(["git", "cat-file", "-e", native_commit + ":" + repo_relative],
                                    cwd=native_repo, capture_output=True)
            require(exists.returncode != 0 and relative not in snapshot_rows
                    and not (native_repo / repo_relative).exists(), "Added research test already exists in the compile source")
        else:
            require(signature(git_bytes(native_repo, "show", native_commit + ":" + repo_relative)) == before
                    and signature((native_repo / repo_relative).read_bytes()) == before,
                    "Original compile research bytes differ from the reviewed before identity")
            row = snapshot_rows.get(relative, {})
            require({key: row.get(key) for key in ("bytes", "sha256")} == before,
                    "Original snapshot does not preserve the reviewed research before identity")
        rows.append({"native_relative": relative, "status": status, "before": before, "after": after})
    return {"schema": "ck3-three-offline-native-research-delta-v1", "reviewed_origin_commit": REVIEWED_ORIGIN,
            "source_classification": "offline_native_research", "paths": rows,
            "dependency_exclusion": dependency_exclusion(qualification, snapshot)}


def qualify_research_delta(declared: object, *, root: Path, native_repo: Path, runtime_commit: str,
                           native_commit: str, qualification: JSONObject, snapshot: JSONObject) -> ResearchContext:
    actual = produce_research_delta(root=root, native_repo=native_repo, runtime_commit=runtime_commit,
                                   native_commit=native_commit, qualification=qualification, snapshot=snapshot)
    # JSON equality must distinguish true from 1 in observed dependency counts.
    require(json.dumps(declared, sort_keys=True, separators=(",", ":"))
            == json.dumps(actual, sort_keys=True, separators=(",", ":")),
            "Explicit research delta differs from the actual reviewed Git/raw/dependency evidence")
    return {"runtime_research_pins": {relative: pin(root / PREFIX / relative) for relative, _, _, _ in APPROVED},
            "added_runtime_research_paths": tuple(relative for relative, status, _, _ in APPROVED if status == "A")}
