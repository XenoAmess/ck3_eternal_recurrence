"""Explicit equivalence for an actual clean linked Native source worktree.

This verifies source provenance only. It never confers build or live credit.
The qualified build's snapshot and CMake paths retain their original identities.
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
from typing import Protocol, TypedDict, NotRequired, runtime_checkable

from build_native_configured_successor import (
    NONCOMPILED_CONSUMER_RELATIVE as NONCOMPILED_CONSUMER_RELATIVE,
    HOST_TEST_COMPANION_RELATIVE as HOST_TEST_COMPANION_RELATIVE,
    NoncompiledConsumerReplay,
)

NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
SCHEMA = "ck3-native-worktree-source-binding-v1"
FIELDS = frozenset({
    "schema", "machine_id", "observed_at_utc", "runtime_repo_root",
    "runtime_source_commit", "native_source_repo_root", "native_source_commit",
    "native_source_base", "native_subtree_tree_id", "common_git_directory",
    "qualified_native", "snapshot",
})


DELTA_FIELDS = FIELDS | {"runtime_native_subtree_tree_id", "shared_python_host_delta"}


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def pin(path: Path | str) -> FilePin:
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Explicit timezone-aware source observation required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Source observation must include its timezone")
    return result.astimezone(timezone.utc)


def checkout(repo: Path, commit: str) -> Path:
    require(Path(git(repo, "rev-parse", "--show-toplevel")).resolve() == repo,
            "Declared source repository is not its actual Git top level")
    require(git(repo, "rev-parse", "HEAD") == commit
            and not git(repo, "status", "--porcelain", "--untracked-files=all"),
            "Source checkout must be clean at its exact declared commit")
    return (repo / git(repo, "rev-parse", "--git-common-dir")).resolve()


def qualified_native_source_checkout(binding_path: Path | None, *, root: Path,
                                     runtime_commit: str, native_commit: str, machine: str,
                                     qualified_native_ref: object, qualification: dict[str, object],
                                     snapshot_ref: object, snapshot: dict[str, object],
                                     native_shared_python_host_delta: Path | None = None) -> dict[str, object]:
    """Return the actual original Native root and optional checked binding pin.

    Without an explicit binding the historical same-Root requirement is exact.
    Alternate source roots must be direct linked-worktree sources, never renamed
    copies or an inferred equivalence based on a path, commit or operator alone.
    """
    if (not isinstance(snapshot.get("Root_native_source_base"), str)
            or not isinstance(snapshot.get("snapshot_native_base"), str)
            or not isinstance(qualified_native_ref, dict) or not isinstance(snapshot_ref, dict)):
        raise ValueError("Native source paths and original reference objects required")
    original_base = snapshot["Root_native_source_base"]
    snapshot_base = snapshot["snapshot_native_base"]
    if not isinstance(original_base, str) or not isinstance(snapshot_base, str):
        raise ValueError("Native source paths must be strings")
    root = Path(root).resolve()
    runtime_native = (root / NATIVE_PREFIX).resolve()
    original_native = Path(original_base).resolve()
    require(native_shared_python_host_delta is None or binding_path is not None,
            "A shared-host delta requires an explicit actual source checkout binding")
    if binding_path is None:
        require(original_native == runtime_native, "Snapshot is from another Root native tree")
        return {"native_source_base": runtime_native, "binding_ref": None}

    binding_path = Path(binding_path)
    require(not binding_path.is_symlink(), "Source checkout binding cannot be symbolic")
    binding_ref = pin(binding_path)
    value = json.loads(binding_path.read_text(encoding="utf-8-sig"))
    if isinstance(value, dict) and value.get("schema") in {
            "ck3-native-same-root-shared-python-host-binding-v1",
            "ck3-native-same-root-host-and-fixture-cmake-binding-v1",
            "ck3-native-same-root-host-and-wire-consumer-binding-v1",
            "ck3-native-same-root-host-and-inactive-prisoner-cmake-binding-v1"}:
        context = qualify_same_root_host(binding_path, root=root, runtime_commit=runtime_commit,
            native_commit=native_commit, machine=machine, qualified_native_ref=qualified_native_ref,
            qualification=qualification, snapshot_ref=snapshot_ref, snapshot=snapshot,
            native_shared_python_host_delta=native_shared_python_host_delta)
        return {key: value for key, value in context.items()}
    require(original_native != runtime_native,
            "An alternate checkout binding must identify an actual distinct source root")
    exact_tree = (isinstance(value, dict)
                  and value.get("schema") == "ck3-native-worktree-exact-tree-source-binding-v1")
    research_delta = (isinstance(value, dict)
                      and value.get("schema") == "ck3-native-worktree-research-delta-source-binding-v1")
    require(not (exact_tree or research_delta) or native_shared_python_host_delta is None,
            "Exact-tree nonancestor binding cannot allow any shared-host source difference")
    fields = FIELDS if native_shared_python_host_delta is None else DELTA_FIELDS
    schema = SCHEMA if native_shared_python_host_delta is None else "ck3-native-worktree-shared-python-host-binding-v1"
    if exact_tree:
        fields = FIELDS | {"native_compile_commit_is_ancestor", "compiled_inputs"}
        schema = "ck3-native-worktree-exact-tree-source-binding-v1"
    if research_delta:
        fields = FIELDS | {"native_compile_commit_is_ancestor", "compiled_inputs",
                           "runtime_native_subtree_tree_id", "full_native_tree_equal",
                           "compiled_inputs_equal", "research_delta"}
        schema = "ck3-native-worktree-research-delta-source-binding-v1"
    require(isinstance(value, dict) and set(value) == fields and value.get("schema") == schema,
            "Exact explicit Native worktree source-binding schema required")
    require(value["machine_id"] == machine and qualification.get("machine_id") == machine
            and snapshot.get("machine_id") == machine,
            "Native source binding, qualification and snapshot must name this machine")
    require(value["runtime_source_commit"] == runtime_commit
            and value["native_source_commit"] == native_commit
            and qualification.get("source_commit") == native_commit
            and snapshot.get("root_commit") == native_commit
            and re.fullmatch("[0-9a-f]{40}", runtime_commit)
            and re.fullmatch("[0-9a-f]{40}", native_commit),
            "Source binding must preserve the distinct exact runtime and compile commits")
    require(value["qualified_native"] == qualified_native_ref
            and pin(qualified_native_ref["path"]) == qualified_native_ref
            and value["snapshot"] == snapshot_ref and pin(snapshot_ref["path"]) == snapshot_ref,
            "Source binding must pin the actual qualification and original source snapshot")
    observed = timestamp(value["observed_at_utc"])
    require(timestamp(qualification.get("observed_at_utc")) <= observed <= datetime.now(timezone.utc),
            "Source binding observation must follow the actual qualified build and not be in the future")
    native_repo = Path(value["native_source_repo_root"]).resolve()
    require(Path(value["runtime_repo_root"]).resolve() == root
            and (native_repo / NATIVE_PREFIX).resolve() == original_native
            and Path(value["native_source_base"]).resolve() == original_native
            and Path(snapshot_base).resolve() == original_native,
            "Explicit alternate source must retain its real direct Native worktree paths")
    root_common, native_common = checkout(root, runtime_commit), checkout(native_repo, native_commit)
    require(root_common == native_common == Path(value["common_git_directory"]).resolve(),
            "Native source and runtime repositories must be actual linked worktrees of the declared Git store")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", native_commit, runtime_commit],
                              cwd=root, capture_output=True)
    if exact_tree or research_delta:
        require(ancestor.returncode == 1 and value["native_compile_commit_is_ancestor"] is False,
                "Exact-tree opt-in must truthfully identify an actual nonancestor compile commit")
    else:
        require(ancestor.returncode == 0, "Native compile commit must be an ancestor of the actual runtime commit")
    subtree = git(root, "rev-parse", runtime_commit + ":" + NATIVE_PREFIX.rstrip("/"))
    compile_subtree = git(native_repo, "rev-parse", native_commit + ":" + NATIVE_PREFIX.rstrip("/"))
    shared_host = None
    research_context = None
    if research_delta:
        require(value["full_native_tree_equal"] is False and value["compiled_inputs_equal"] is True
                and subtree != compile_subtree and value["native_subtree_tree_id"] == compile_subtree
                and value["runtime_native_subtree_tree_id"] == subtree,
                "Research opt-in must truthfully preserve unequal full Native trees and unchanged compiled inputs")
        path = Path(__file__).with_name("ck3_mod_acceptance_native_research_delta.py")
        spec = importlib.util.spec_from_file_location("ck3_native_research_delta", path)
        if spec is None or spec.loader is None:
            raise ValueError("Research source validator unavailable")
        research_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(research_module)
        research_context = research_module.qualify_research_delta(
            value["research_delta"], root=root, native_repo=native_repo,
            runtime_commit=runtime_commit, native_commit=native_commit,
            qualification=qualification, snapshot=snapshot)
    elif native_shared_python_host_delta is None:
        require(subtree == value["native_subtree_tree_id"] == compile_subtree,
                "Runtime and compile commits have different Native Git trees")
    else:
        require(value["native_subtree_tree_id"] == compile_subtree
                and value["runtime_native_subtree_tree_id"] == subtree
                and value["shared_python_host_delta"] == pin(native_shared_python_host_delta),
                "Shared-host opt-in must preserve both actual trees and the exact explicit delta pin")
        path = Path(__file__).with_name("ck3_mod_acceptance_shared_python_host_delta.py")
        spec = importlib.util.spec_from_file_location("ck3_exact_shared_python_host_delta", path)
        if spec is None or spec.loader is None:
            raise ValueError("Shared-host source validator unavailable")
        delta_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(delta_module)
        shared_host = delta_module.qualify_shared_host_delta(
            native_shared_python_host_delta, root=root, native_repo=native_repo,
            runtime_commit=runtime_commit, native_commit=native_commit, machine=machine,
            qualified_native_ref=qualified_native_ref, qualification=qualification,
            snapshot_ref=snapshot_ref, snapshot=snapshot)
    tracked = set(git(root, "ls-files", "-z", "--", NATIVE_PREFIX).split("\0")) - {""}
    native_tracked = set(git(native_repo, "ls-files", "-z", "--", NATIVE_PREFIX).split("\0")) - {""}
    rows = snapshot.get("files", [])
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Native source rows must be objects")
    declared = {NATIVE_PREFIX + row["native_relative"] for row in rows if "source" not in row}
    added_research = (set(research_context["added_runtime_research_paths"])
                      if research_context is not None else set())
    require(tracked == declared | {NATIVE_PREFIX + relative for relative in added_research}
            and native_tracked == declared and len(declared) == len(rows)
            and snapshot.get("source_count") == len(rows),
            "Direct worktree snapshot must cover every unique tracked Native input, without derivatives")
    for row in rows:
        relative = row["native_relative"]
        require(isinstance(relative, str) and relative and "\\" not in relative and ":" not in relative
                and not relative.startswith("/") and all(p not in {"", ".", ".."} for p in relative.split("/"))
                and "original_source_pin" not in row,
                "Direct Native worktree source paths must be safe, unique, unmodified tracked inputs")
        expected = {"bytes": row["bytes"], "sha256": row["sha256"]}
        for base in (runtime_native, original_native):
            path = base / relative
            require(not path.is_symlink(), "Native worktree source inputs cannot be symbolic")
            actual = pin(path)
            wanted = expected
            if (shared_host is not None and base == runtime_native
                    and relative == "research/run_ck3_12002_mcp_live.py"):
                wanted = {key: shared_host["runtime_host_pin"][key] for key in ("bytes", "sha256")}
            if (research_context is not None and base == runtime_native
                    and relative in research_context["runtime_research_pins"]):
                wanted = {key: research_context["runtime_research_pins"][relative][key]
                          for key in ("bytes", "sha256")}
            require({"bytes": actual["bytes"], "sha256": actual["sha256"]} == wanted,
                    "Actual Native source raw pin differs across the runtime, compile checkout or frozen snapshot: " + relative)
    result = {"native_source_base": original_native, "binding_ref": binding_ref}
    if exact_tree or research_delta:
        # Strict exact-tree keeps equal trees/pathsets. The separate reviewed
        # research schema has checked its fixed M/A/M delta and every other raw
        # input; both routes retain the original actual compiled closure.
        path = Path(__file__).with_name("ck3_mod_acceptance_shared_python_host_delta.py")
        spec = importlib.util.spec_from_file_location("ck3_exact_tree_compiled_inputs", path)
        if spec is None or spec.loader is None:
            raise ValueError("Compiled cohort validator unavailable")
        compiled_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compiled_module)
        actual_compiled = compiled_module.compiled_inputs(qualification, snapshot)
        path = Path(__file__).with_name("ck3_mod_acceptance_exact_native_tree_binding.py")
        spec = importlib.util.spec_from_file_location("ck3_exact_native_tree_contract", path)
        if spec is None or spec.loader is None:
            raise ValueError("Exact-tree contract validator unavailable")
        contract_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contract_module)
        contract_module.validate_compiled_inputs(value["compiled_inputs"], actual_compiled)
        result.update(native_compile_commit_is_ancestor=False)
        if exact_tree:
            result.update(nonancestor_exact_tree_binding=binding_ref)
        else:
            if research_context is None:
                raise ValueError("Verified research context missing")
            result.update(nonancestor_research_delta_binding=binding_ref,
                          full_native_tree_equal=False, compiled_inputs_equal=True,
                          runtime_research_pins=research_context["runtime_research_pins"],
                          added_runtime_research_paths=research_context["added_runtime_research_paths"],
                          research_delta=value["research_delta"])
    if shared_host is not None:
        result.update(runtime_shared_host_pin=shared_host["runtime_host_pin"],
                      shared_python_host_delta=shared_host["ref"],
                      shared_host_qualification=shared_host["shared_host_qualification"])
    return result


# Same-root source successor maintenance; no Native build or live credit.
NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
HOST_RELATIVE = NATIVE_PREFIX + "research/run_ck3_12002_mcp_live.py"
HOST_NATIVE_RELATIVE = HOST_RELATIVE.removeprefix(NATIVE_PREFIX)
FIXTURE_CMAKE_RELATIVE = "cmake/player_pilgrimage_traits_12004.cmake"
FIXTURE_TARGET = "xar_ck3_12004_player_pilgrimage_traits_test"
HOST_BINDING_SCHEMA = "ck3-native-same-root-shared-python-host-binding-v1"
HOST_FIXTURE_BINDING_SCHEMA = "ck3-native-same-root-host-and-fixture-cmake-binding-v1"
HOST_DELTA_SCHEMA = "ck3-exact-same-root-python-host-delta-v1"
HOST_CONSUMER_BINDING_SCHEMA = "ck3-native-same-root-host-and-wire-consumer-binding-v1"
HOST_CONSUMER_DELTA_SCHEMA = "ck3-exact-same-root-host-and-wire-consumer-delta-v1"
HOST_INACTIVE_CMAKE_BINDING_SCHEMA = "ck3-native-same-root-host-and-inactive-prisoner-cmake-binding-v1"
INACTIVE_CMAKE_FLAGS = ("XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1",
                        "XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1")
INACTIVE_CMAKE_BEFORE = (
    b"if(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)\n"
    b"  target_sources(xar_ck3_bridge PRIVATE\n"
    b"    src/player_prisoner_collection_query_v1_private.cpp\n"
    b"    src/player_prisoner_collection_private_transport_v1.cpp)\n"
    b"  target_compile_definitions(xar_ck3_bridge PRIVATE\n"
    b"    XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1=1)\nendif()",
    b"if(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)\n"
    b"  target_sources(xar_ck3_bridge PRIVATE\n"
    b"    src/player_prisoner_ransom_private_v1.cpp\n"
    b"    src/player_prisoner_ransom_wire_v1.cpp)\n"
    b"  target_compile_definitions(xar_ck3_bridge PRIVATE\n"
    b"    XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1=1)\nendif()")
INACTIVE_CMAKE_AFTER = (
    INACTIVE_CMAKE_BEFORE[0].replace(b"    src/player_prisoner_collection_private_transport_v1.cpp)",
        b"    src/player_prisoner_collection_private_transport_v1.cpp\n    src/player_prisoner_ransom_wire_v1.cpp)"),
    INACTIVE_CMAKE_BEFORE[1].replace(b"    src/player_prisoner_ransom_private_v1.cpp\n"
        b"    src/player_prisoner_ransom_wire_v1.cpp)", b"    src/player_prisoner_ransom_private_v1.cpp)"))
WIRE_CONSUMER_DELTA_SCHEMA = "ck3-exact-refill-wire-consumer-delta-v1"
HOST_BINDING_FIELDS = frozenset({"schema", "machine_id", "observed_at_utc", "runtime_repo_root",
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
    original_fixture_cmake_blob: NotRequired[FilePin]
    runtime_fixture_cmake_pin: NotRequired[FilePin]
    original_inactive_cmake_blob: NotRequired[FilePin]
    runtime_inactive_cmake_pin: NotRequired[FilePin]
    original_research_blobs: NotRequired[dict[str, FilePin]]
    runtime_research_pins: NotRequired[dict[str, FilePin]]
    noncompiled_replay: NotRequired[NoncompiledConsumerReplay]


class FixtureCMakeContext(TypedDict):
    original_fixture_cmake_blob: FilePin
    runtime_fixture_cmake_pin: FilePin


class InactiveCMakeContext(TypedDict):
    original_inactive_cmake_blob: FilePin
    runtime_inactive_cmake_pin: FilePin


class WireConsumerContext(TypedDict):
    before_blob: FilePin
    after: FilePin


@runtime_checkable
class SharedDeltaAPI(Protocol):
    def compiled_inputs(self, qualification: dict[str, object], snapshot: dict[str, object]) -> object: ...
    def qualify_shared_host_delta(self, path: Path, *, root: Path, native_repo: Path,
        runtime_commit: str, native_commit: str, machine: str, qualified_native_ref: object,
        qualification: dict[str, object], snapshot_ref: object, snapshot: dict[str, object],
        same_root_before_blob: object = None, same_root_fixture_cmake: object = None,
        same_root_inactive_cmake: object = None,
        same_root_wire_consumer: object = None, same_root_host_test: object = None) -> object: ...


def host_require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def host_obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("JSON object keys must be strings")
        result[key] = item
    return result


def host_arr(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("JSON array required")
    return list(value)


def host_string(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty string required")
    return value


def host_exact_integer(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("Positive exact integer required")
    return value


def host_signature(raw: bytes) -> Signature:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def host_parse_signature(value: object) -> Signature:
    row = host_obj(value)
    host_require(set(row) == {"bytes", "sha256"}, "Exact signature fields required")
    digest = host_string(row["sha256"])
    host_require(re.fullmatch(r"[0-9a-f]{64}", digest), "Canonical SHA256 required")
    return {"bytes": host_exact_integer(row["bytes"]), "sha256": digest}


def host_pin(path: Path) -> FilePin:
    path = path.resolve()
    return {"path": str(path), **host_signature(path.read_bytes())}


def host_parse_pin(value: object) -> FilePin:
    row = host_obj(value)
    host_require(set(row) == {"path", "bytes", "sha256"}, "Exact file pin fields required")
    path = Path(host_string(row["path"]))
    host_require(path.is_absolute(), "Absolute pin path required")
    return {"path": str(path), **host_parse_signature({key: row[key] for key in ("bytes", "sha256")})}


def host_checked(value: object) -> FilePin:
    expected = host_parse_pin(value)
    host_require(not Path(expected["path"]).is_symlink() and host_pin(Path(expected["path"])) == expected,
            "Exact source/evidence pin changed: " + expected["path"])
    return expected


def host_read(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return host_obj(value)


def host_git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True, check=True).stdout


def host_timestamp(value: object) -> datetime:
    result = datetime.fromisoformat(host_string(value).replace("Z", "+00:00"))
    host_require(result.tzinfo is not None, "Timezone-aware observation required")
    return result.astimezone(timezone.utc)


def host_shared_api() -> SharedDeltaAPI:
    path = Path(__file__).with_name("ck3_mod_acceptance_shared_python_host_delta.py")
    spec = importlib.util.spec_from_file_location("same_root_original_shared_delta", path)
    if spec is None or spec.loader is None:
        raise ValueError("Shared host-delta validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module, SharedDeltaAPI):
        raise ValueError("Shared host-delta validator interface differs")
    return module


def host_validate_compiled_inputs(declared: object, actual: object) -> None:
    value = host_obj(declared)
    refs = {"configured_scope", "codemodel", "compile_commands", "production_freeze", "published_dll"}
    host_require(set(value) == refs | {"production_TUs", "unique_production_source_count", "production_source_set_sha256"},
            "Exact original compiled-input fields required")
    for name in refs:
        host_checked(value[name])
    counts = host_obj(value["production_TUs"])
    host_require(counts, "Actual production TU counts required")
    for count in counts.values():
        host_exact_integer(count)
    host_exact_integer(value["unique_production_source_count"])
    host_require(re.fullmatch(r"[0-9a-f]{64}", host_string(value["production_source_set_sha256"])),
            "Exact production source-set digest required")
    host_require(json.dumps(value, sort_keys=True, allow_nan=False) == json.dumps(actual, sort_keys=True, allow_nan=False),
            "Original compiled cohort changed")


def qualify_fixture_cmake_delta(proof: object, *, root: Path, native_commit: str,
    runtime_commit: str, machine: str, qualification: dict[str, object],
    snapshot: dict[str, object]) -> FixtureCMakeContext:
    """Accept one exact fixture-only link completion, never any compiled delta.

    The old actual linker response already included the protocol archive. This
    checks that original evidence and the qualified executable; it runs no link.
    """
    value = host_obj(proof)
    host_require(set(value) == {"schema", "original_blob", "fixture_link_receipt"}
        and value["schema"] == "ck3-exact-fixture-cmake-link-completion-v1", "Exact fixture CMake proof required")
    before = host_checked(value["original_blob"])
    before_path = Path(before["path"])
    host_require(not before_path.is_relative_to(root.resolve()), "Original fixture CMake must be separately preserved")
    old = before_path.read_bytes()
    host_require(host_signature(host_git(root, "show", native_commit + ":" + NATIVE_PREFIX + FIXTURE_CMAKE_RELATIVE))
        == host_signature(old), "Fixture CMake blob differs from its actual compile commit")
    rows = [host_obj(row) for row in host_arr(snapshot["files"])]
    frozen = [row for row in rows if row.get("native_relative") == FIXTURE_CMAKE_RELATIVE]
    host_require(len(frozen) == 1 and host_parse_signature({key: frozen[0][key] for key in ("bytes", "sha256")})
        == host_signature(old), "Fixture CMake blob differs from the original snapshot")
    target = FIXTURE_TARGET.encode("ascii")
    old_link = b"  target_link_libraries(" + target + b" PRIVATE\n    xar_ck3_12002_runtime)"
    new_link = old_link[:-1] + b" xar_bridge_protocol)"
    host_require(old.count(old_link) == 1 and old.count(b"  add_executable(" + target + b"\n") == 1,
        "Known narrow fixture target registration required")
    current_path = root / NATIVE_PREFIX / FIXTURE_CMAKE_RELATIVE
    after = current_path.read_bytes()
    host_require(after == old.replace(old_link, new_link)
        and after == host_git(root, "show", runtime_commit + ":" + NATIVE_PREFIX + FIXTURE_CMAKE_RELATIVE),
        "Only the known fixture protocol-library completion is allowed")
    for commit in (native_commit, runtime_commit):
        host_require(host_git(root, "ls-tree", commit, "--", NATIVE_PREFIX + FIXTURE_CMAKE_RELATIVE)
            .decode().startswith("100644 blob "), "Fixture CMake must remain a regular tracked file")
    fixtures = [host_obj(row) for row in host_arr(qualification["fixture_results"])]
    selected = [row for row in fixtures if row.get("target") == FIXTURE_TARGET]
    host_require(len(selected) == 1, "Original Q must qualify this exact fixture executable")
    executable = host_checked(selected[0]["executable"])
    execution_ref = host_checked(selected[0]["execution"])
    execution = host_read(Path(execution_ref["path"]))
    execution_argv = [host_string(arg) for arg in host_arr(execution["argv"])]
    host_require(type(execution.get("original_wait_returncode")) is int
        and execution["original_wait_returncode"] == 0 and execution.get("stopped_reason") is None
        and execution.get("machine_id") == machine and execution_argv
        and Path(execution_argv[0]).resolve() == Path(executable["path"]), "Original qualified fixture execution differs")
    link_ref = host_checked(value["fixture_link_receipt"])
    link = host_read(Path(link_ref["path"]))
    host_require(link.get("machine_id") == machine and link.get("source_commit") == native_commit
        and type(link.get("original_wait_returncode")) is int and link["original_wait_returncode"] == 0
        and link.get("stopped_reason") is None, "Actual original fixture zero linker wait required")
    responses = [host_checked(row) for row in host_arr(link["response_files"])]
    argv = [host_string(arg) for arg in host_arr(link["argv"])]
    host_require(len(responses) == 1 and len(argv) == 2 and Path(argv[0]).name.lower() == "link.exe"
        and argv[1] == "@" + responses[0]["path"], "Actual fixture linker response identity differs")
    response = Path(responses[0]["path"]).read_text(encoding="utf-8-sig")
    production_ref = host_checked(qualification["production_build_receipt"])
    production = host_read(Path(production_ref["path"]))
    production_responses = [host_checked(row) for row in host_arr(production["response_files"])]
    host_require(len(production_responses) == 1, "Original production linker response required")
    production_text = Path(production_responses[0]["path"]).read_text(encoding="utf-8-sig")
    archive_pattern = r'(?:"([^"\r\n]*xar_bridge_protocol\.lib)"|([^\s"]*xar_bridge_protocol\.lib))'
    old_archives = [left or right for left, right in re.findall(archive_pattern, production_text)]
    fixture_archives = [left or right for left, right in re.findall(archive_pattern, response)]
    host_require(len(old_archives) == len(fixture_archives) == 1
        and Path(old_archives[0]).resolve() == Path(fixture_archives[0]).resolve()
        and Path(old_archives[0]).is_file(), "Actual fixture did not already link the original production protocol archive")
    output = re.findall(r'(?:^|\s)/OUT:(?:"([^"]+)"|(\S+))', response, re.IGNORECASE)
    host_require(len(output) == 1 and Path(output[0][0] or output[0][1]).resolve() == Path(executable["path"]),
        "Original fixture response output differs from the qualified EXE")
    return {"original_fixture_cmake_blob": before, "runtime_fixture_cmake_pin": host_pin(current_path)}


def qualify_inactive_cmake_delta(proof: object, *, root: Path, native_commit: str,
    runtime_commit: str, machine: str, qualification: dict[str, object],
    snapshot: dict[str, object]) -> InactiveCMakeContext:
    """Prove the sole known prisoner wire relocation is inactive in the old build.

    This preserves the original build and DLL; it does not configure or compile.
    Both complete conditional bodies, the original actual cache/profile and all
    selected compiler inputs remain checked rather than accepting a CMake suffix.
    """
    value = host_obj(proof)
    host_require(set(value) == {"schema", "original_blob", "configured_cache", "configure_execution"}
        and value["schema"] == "ck3-exact-inactive-prisoner-cmake-relocation-v1",
        "Exact inactive prisoner CMake proof required")
    before = host_checked(value["original_blob"])
    old_path = Path(before["path"])
    host_require(not old_path.resolve().is_relative_to(root.resolve()), "Original inactive CMake must be separately preserved")
    old = old_path.read_bytes()
    host_require(old == host_git(root, "show", native_commit + ":" + NATIVE_PREFIX + "CMakeLists.txt"),
                 "Inactive CMake differs from its actual compile commit")
    frozen = [host_obj(row) for row in host_arr(snapshot["files"])
              if host_obj(row).get("native_relative") == "CMakeLists.txt"]
    host_require(len(frozen) == 1 and host_parse_signature({key: frozen[0][key] for key in ("bytes", "sha256")})
        == host_signature(old), "Inactive CMake differs from the original snapshot")
    expected = old
    for before_block, after_block in zip(INACTIVE_CMAKE_BEFORE, INACTIVE_CMAKE_AFTER):
        host_require(expected.count(before_block) == 1, "Exact known prisoner conditional bodies required")
        expected = expected.replace(before_block, after_block)
    current = root / NATIVE_PREFIX / "CMakeLists.txt"
    host_require(not current.is_symlink() and current.read_bytes() == expected
        == host_git(root, "show", runtime_commit + ":" + NATIVE_PREFIX + "CMakeLists.txt"),
        "Only the exact inactive prisoner wire relocation is allowed")
    for commit in (native_commit, runtime_commit):
        host_require(host_git(root, "ls-tree", commit, "--", NATIVE_PREFIX + "CMakeLists.txt")
                     .decode().startswith("100644 blob "), "Inactive CMake must remain a regular tracked file")
    profile = host_read(Path(host_checked(qualification["profile"])["path"]))
    flags = host_obj(profile.get("flags"))
    host_require(profile.get("machine_id") == machine and all(flags.get(flag) == "OFF" for flag in INACTIVE_CMAKE_FLAGS),
                 "Both original qualified prisoner flags must be explicitly OFF")
    scope = host_read(Path(host_checked(qualification["configured_scope"])["path"]))
    model = host_read(Path(host_checked(scope["codemodel"])["path"]))
    build = Path(host_string(host_obj(model["paths"])["build"])).resolve()
    native = (root / NATIVE_PREFIX).resolve()
    cache = host_checked(value["configured_cache"])
    host_require(Path(cache["path"]).resolve() == build / "CMakeCache.txt",
                 "Inactive CMake cache must belong to the original File API build")
    cache_lines = Path(cache["path"]).read_bytes().splitlines()
    for flag in INACTIVE_CMAKE_FLAGS:
        entries = [line for line in cache_lines if line.startswith(flag.encode("ascii") + b":")]
        host_require(entries == [(flag + ":BOOL=OFF").encode("ascii")], "Both actual cached prisoner flags must be BOOL OFF")
    home = [line for line in cache_lines if line.startswith(b"CMAKE_HOME_DIRECTORY:")]
    host_require(len(home) == 1 and home[0].startswith(b"CMAKE_HOME_DIRECTORY:INTERNAL=")
        and Path(home[0].split(b"=", 1)[1].decode("utf-8")).resolve() == native,
        "Original CMake cache source root differs")
    execution = host_read(Path(host_checked(value["configure_execution"])["path"]))
    argv = [host_string(arg) for arg in host_arr(execution.get("argv"))]
    host_require(execution.get("machine_id") == machine and execution.get("source_commit") == native_commit
        and type(execution.get("original_wait_returncode")) is int and execution["original_wait_returncode"] == 0
        and execution.get("stopped_reason") is None and execution.get("game_started_or_attached") is False,
        "Original actual zero-wait configure execution required")
    host_checked(execution.get("log"))
    for switch, wanted in (("-S", native), ("-B", build)):
        positions = [i for i, arg in enumerate(argv) if arg == switch]
        host_require(len(positions) == 1 and positions[0] + 1 < len(argv)
            and Path(argv[positions[0] + 1]).resolve() == wanted, "Original configure source/build argv differs")
    profile_include = host_checked(profile.get("profile"))
    include = "-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=" + profile_include["path"]
    host_require(argv.count(include) == 1 and not any(any(flag in arg for flag in INACTIVE_CMAKE_FLAGS) for arg in argv),
                 "Original configure must use the exact qualified profile without prisoner overrides")
    commands_ref = host_checked(scope["compile_commands"])
    host_require(Path(commands_ref["path"]).resolve() == build / "compile_commands.json",
                 "Original compiler commands must belong to the configured build")
    wire = native / "src/player_prisoner_ransom_wire_v1.cpp"
    reply = Path(host_checked(scope["codemodel"])["path"]).parent
    configs = host_arr(model["configurations"])
    host_require(len(configs) == 1, "Exact original File API configuration required")
    targets: dict[str, dict[str, object]] = {}
    for raw in host_arr(host_obj(configs[0])["targets"]):
        entry = host_obj(raw)
        path = (reply / host_string(entry["jsonFile"])).resolve()
        host_require(path.is_relative_to(reply.resolve()), "Unsafe original File API target")
        targets[host_string(entry["id"])] = host_read(path)
    pending = [key for key, target in targets.items() if target.get("name") == "xar_ck3_bridge"]
    host_require(len(pending) == 1, "Exact original production root required")
    production: set[str] = set()
    while pending:
        key = pending.pop()
        if key in production:
            continue
        host_require(key in targets, "Unknown original production dependency")
        production.add(key)
        pending.extend(host_string(host_obj(row)["id"]) for row in host_arr(targets[key].get("dependencies", [])))
    production_names = {host_string(targets[key]["name"]) for key in production}
    for key in production:
        for item in host_arr(targets[key].get("sources", [])):
            row = host_obj(item)
            source_path = Path(host_string(row["path"]))
            selected = source_path.resolve() if source_path.is_absolute() else (native / source_path).resolve()
            host_require(selected != wire or row.get("compileGroupIndex") is None,
                         "Inactive prisoner wire entered an actual production File API target")
    for raw in host_arr(json.loads(Path(commands_ref["path"]).read_text(encoding="utf-8-sig"))):
        command = host_obj(raw)
        output = Path(host_string(command.get("output")))
        output = output.resolve() if output.is_absolute() else (build / output).resolve()
        host_require(output.is_relative_to(build), "Original compiler output escaped its configured build")
        parts = output.relative_to(build).parts
        host_require(len(parts) >= 3 and parts[0] == "CMakeFiles" and parts[1].endswith(".dir"),
                     "Exact original compiler target identity required")
        if parts[1][:-4] in production_names:
            host_require(Path(host_string(command.get("file"))).resolve() != wire
                and "player_prisoner_ransom_wire_v1.cpp" not in host_string(command.get("command")),
                "Inactive prisoner wire entered actual production compiler commands")
    return {"original_inactive_cmake_blob": before, "runtime_inactive_cmake_pin": host_pin(current)}


def exclude_noncompiled_fileapi(native_relative: str, *, root: Path, qualification: object) -> None:
    """Exclude the two fixed reviewed Python leaves from every actual target."""
    host_require(native_relative in (NONCOMPILED_CONSUMER_RELATIVE, HOST_TEST_COMPANION_RELATIVE),
                 "Only the fixed refill reader and host test companion are eligible")
    native = (root / NATIVE_PREFIX).resolve()
    current = native / native_relative
    scope = host_read(Path(host_checked(host_obj(qualification).get("configured_scope"))["path"]))
    model_ref = host_checked(scope.get("codemodel"))
    model = host_read(Path(model_ref["path"]))
    host_require(Path(host_string(host_obj(model.get("paths")).get("source"))).resolve() == native,
                 "Noncompiled reader File API source differs")
    configurations = host_arr(model.get("configurations"))
    host_require(len(configurations) == 1, "Noncompiled reader File API configuration is ambiguous")
    reply = Path(model_ref["path"]).parent
    for raw in host_arr(host_obj(configurations[0]).get("targets")):
        target_path = (reply / host_string(host_obj(raw).get("jsonFile"))).resolve()
        host_require(target_path.is_relative_to(reply), "Noncompiled reader File API path escaped its reply")
        for item in host_arr(host_read(target_path).get("sources", [])):
            source = Path(host_string(host_obj(item).get("path")))
            actual = source.resolve() if source.is_absolute() else (native / source).resolve()
            host_require(actual != current.resolve(), "Noncompiled reader entered an actual File API target")
    commands_ref = host_checked(scope.get("compile_commands"))
    commands: object = json.loads(Path(commands_ref["path"]).read_text(encoding="utf-8-sig"))
    for raw in host_arr(commands):
        command = host_obj(raw)
        host_require(Path(host_string(command.get("file"))).resolve() != current.resolve(),
                     "Noncompiled reader entered actual compile commands")
        text = host_string(command.get("command")).replace("\\", "/").lower()
        host_require(native_relative.lower() not in text, "Noncompiled reader entered a compiler command argument")


def qualify_wire_consumer_delta(proof: object, *, root: Path, native_commit: str,
    runtime_commit: str, machine: str, qualification: object, snapshot: object) -> WireConsumerContext:
    """Bind only the existing refill wire reader, with its original Git bytes."""
    proof_ref = host_checked(proof)
    row = host_read(Path(proof_ref["path"]))
    wanted = {"schema", "machine_id", "runtime_source_commit", "native_source_commit",
              "canonical_repo_relative", "before_blob", "after", "source_delta", "source_consumer", "reviewed_change"}
    relative = NATIVE_PREFIX + NONCOMPILED_CONSUMER_RELATIVE
    host_require(set(row) == wanted and row.get("schema") == WIRE_CONSUMER_DELTA_SCHEMA,
                 "Exact reviewed refill wire consumer delta required")
    host_require(row["machine_id"] == machine and row["runtime_source_commit"] == runtime_commit
        and row["native_source_commit"] == native_commit and row["canonical_repo_relative"] == relative,
        "Refill wire consumer source identity differs")
    before, after = host_checked(row["before_blob"]), host_checked(row["after"])
    old_signature: Signature = {"bytes": before["bytes"], "sha256": before["sha256"]}
    new_signature: Signature = {"bytes": after["bytes"], "sha256": after["sha256"]}
    current = root / relative
    host_require(not Path(before["path"]).resolve().is_relative_to(root)
        and not current.is_symlink() and Path(after["path"]).resolve() == current.resolve()
        and old_signature != new_signature, "Exact external before blob and changed canonical refill reader required")
    for commit, expected in ((native_commit, old_signature), (runtime_commit, new_signature)):
        host_require(host_git(root, "ls-tree", commit, "--", relative).decode().startswith("100644 blob ")
            and host_signature(host_git(root, "show", commit + ":" + relative)) == expected,
            "Refill reader differs from its actual regular Git blob")
    rows = [host_obj(raw) for raw in host_arr(host_obj(snapshot).get("files"))]
    originals = [raw for raw in rows if raw.get("native_relative") == NONCOMPILED_CONSUMER_RELATIVE]
    host_require(len(originals) == 1 and host_parse_signature({key: originals[0].get(key)
        for key in ("bytes", "sha256")}) == old_signature, "Refill before blob differs from the original Native snapshot")

    exclude_noncompiled_fileapi(NONCOMPILED_CONSUMER_RELATIVE, root=root, qualification=qualification)

    delta_ref, consumer_ref, review_ref = (host_checked(row[key])
        for key in ("source_delta", "source_consumer", "reviewed_change"))
    delta, consumer, review = (host_read(Path(ref["path"])) for ref in (delta_ref, consumer_ref, review_ref))
    host_require(delta.get("target") == relative and host_parse_signature(delta.get("base_source")) == old_signature
        and delta.get("candidate_bytes") == new_signature["bytes"]
        and type(delta.get("candidate_bytes")) is int and delta.get("candidate_sha256") == new_signature["sha256"],
        "Refill consumer source delta differs from its actual before/after blobs")
    waits = [consumer[key] for key in ("original_wait_returncode", "exit_code") if key in consumer]
    host_require(consumer.get("machine_id") == machine and consumer.get("result") == "PASS"
        and type(consumer.get("skipped")) is int and consumer["skipped"] == 0
        and waits and all(type(code) is int and code == 0 for code in waits)
        and host_parse_signature(host_obj(consumer.get("pins")).get(delta_ref["path"]))
            == {"bytes": delta_ref["bytes"], "sha256": delta_ref["sha256"]},
        "Actual zero-skip refill source consumer must pin its reviewed delta")
    host_require(review.get("schema") == "ck3-reviewed-refill-wire-consumer-change-v1"
        and review.get("machine_id") == machine and review.get("result") == "PASS"
        and review.get("canonical_repo_relative") == relative
        and host_parse_signature(review.get("before")) == old_signature
        and host_parse_signature(review.get("after")) == new_signature
        and review.get("source_consumer") == consumer_ref and review.get("source_delta") == delta_ref
        and review.get("actual_live_business_qualified") is False,
        "Independent exact refill wire consumer source review required")
    return {"before_blob": before, "after": after}


def qualify_host_test_companion(change: object, *, root: Path, native_commit: str,
    runtime_commit: str, machine: str, qualification: object, snapshot: object,
    host_delta: object) -> WireConsumerContext:
    """Bind the sole existing host test to the same actual host test consumer."""
    pair = host_obj(change)
    host_require(set(pair) == {"before_blob", "after"}, "Exact host test companion fields required")
    before, after = host_checked(pair["before_blob"]), host_checked(pair["after"])
    relative = NATIVE_PREFIX + HOST_TEST_COMPANION_RELATIVE
    current = root / relative
    old_signature: Signature = {"bytes": before["bytes"], "sha256": before["sha256"]}
    new_signature: Signature = {"bytes": after["bytes"], "sha256": after["sha256"]}
    host_require(not Path(before["path"]).resolve().is_relative_to(root) and not current.is_symlink()
        and Path(after["path"]).resolve() == current.resolve() and old_signature != new_signature,
        "Exact external before blob and changed canonical host test required")
    for commit, expected in ((native_commit, old_signature), (runtime_commit, new_signature)):
        host_require(host_git(root, "ls-tree", commit, "--", relative).decode().startswith("100644 blob ")
            and host_signature(host_git(root, "show", commit + ":" + relative)) == expected,
            "Host test companion differs from its actual regular Git blob")
    rows = [host_obj(raw) for raw in host_arr(host_obj(snapshot).get("files"))]
    originals = [row for row in rows if row.get("native_relative") == HOST_TEST_COMPANION_RELATIVE]
    host_require(len(originals) == 1 and host_parse_signature({key: originals[0].get(key)
        for key in ("bytes", "sha256")}) == old_signature, "Host test before blob differs from the Native snapshot")
    exclude_noncompiled_fileapi(HOST_TEST_COMPANION_RELATIVE, root=root, qualification=qualification)
    delta = host_obj(host_delta)
    review = host_read(Path(host_checked(delta.get("reviewed_host_change"))["path"]))
    source_qualification = host_read(Path(host_checked(delta.get("shared_host_qualification"))["path"]))
    host_require(review.get("host_test_change") == pair and source_qualification.get("host_test_change") == pair,
                 "Host review and source qualification must retain the exact test companion")
    consumer_ref = host_checked(review.get("source_consumer"))
    consumer = host_read(Path(consumer_ref["path"]))
    waits = [consumer[key] for key in ("original_wait_returncode", "exit_code") if key in consumer]
    host_require(consumer.get("machine_id") == machine and consumer.get("result") == "PASS"
        and type(consumer.get("skipped")) is int and consumer["skipped"] == 0 and waits
        and all(type(code) is int and code == 0 for code in waits)
        and host_parse_signature(host_obj(consumer.get("pins")).get(after["path"])) == new_signature,
        "Actual zero-skip host consumer must pin the executed companion source")
    source_pins = [host_checked(row) for row in host_arr(source_qualification.get("source_pins"))]
    host_require(after in source_pins, "Shared-host qualification omitted its actual test companion source")
    return {"before_blob": before, "after": after}


def qualify_same_root_host(binding_path: Path, *, root: Path, runtime_commit: str,
    native_commit: str, machine: str, qualified_native_ref: object, qualification: object,
    snapshot_ref: object, snapshot: object, native_shared_python_host_delta: Path | None) -> SourceContext:
    root = root.resolve()
    native = (root / NATIVE_PREFIX).resolve()
    binding_ref = host_pin(binding_path)
    binding = host_read(binding_path)
    q, source = host_obj(qualification), host_obj(snapshot)
    fixture_delta = binding.get("fixture_cmake_delta")
    inactive_delta = binding.get("inactive_cmake_delta")
    consumer_delta = binding.get("noncompiled_consumer_delta")
    host_test_change = binding.get("host_test_change")
    host_require(host_test_change is None or consumer_delta is not None,
                 "Host test companion requires the explicit wire consumer transition")
    host_require(fixture_delta is None or consumer_delta is None,
                 "Fixture and refill consumer exceptions cannot be combined")
    host_require(inactive_delta is None or (fixture_delta is None and consumer_delta is None),
                 "Inactive CMake cannot combine with other source exceptions")
    wanted_fields = HOST_BINDING_FIELDS if fixture_delta is None else HOST_BINDING_FIELDS | {"fixture_cmake_delta"}
    wanted_schema = HOST_BINDING_SCHEMA if fixture_delta is None else HOST_FIXTURE_BINDING_SCHEMA
    if consumer_delta is not None:
        wanted_fields, wanted_schema = HOST_BINDING_FIELDS | {"noncompiled_consumer_delta"}, HOST_CONSUMER_BINDING_SCHEMA
    if inactive_delta is not None:
        wanted_fields, wanted_schema = HOST_BINDING_FIELDS | {"inactive_cmake_delta"}, HOST_INACTIVE_CMAKE_BINDING_SCHEMA
    if host_test_change is not None:
        wanted_fields = wanted_fields | {"host_test_change"}
    host_require(set(binding) == wanted_fields and binding["schema"] == wanted_schema, "Exact same-root host binding required")
    if native_shared_python_host_delta is None:
        raise ValueError("Explicit reviewed same-root host delta required")
    host_require(binding["machine_id"] == machine == q.get("machine_id") == source.get("machine_id"),
            "Same-root source identities belong to another machine")
    host_require(re.fullmatch(r"[0-9a-f]{40}", runtime_commit) and re.fullmatch(r"[0-9a-f]{40}", native_commit)
            and binding["runtime_source_commit"] == runtime_commit and binding["native_source_commit"] == native_commit
            and q.get("source_commit") == native_commit and source.get("root_commit") == native_commit,
            "Preserve the distinct exact runtime and original Native commits")
    qref, sref = host_checked(qualified_native_ref), host_checked(snapshot_ref)
    host_require(host_checked(binding["qualified_native"]) == qref and host_checked(binding["snapshot"]) == sref
            and host_read(Path(qref["path"])) == q and host_read(Path(sref["path"])) == source,
            "Original qualification/snapshot identity differs")
    host_require(host_timestamp(q.get("observed_at_utc")) <= host_timestamp(binding["observed_at_utc"]) <= datetime.now(timezone.utc),
            "Same-root binding observation must follow the original qualification")
    host_require(Path(host_string(binding["runtime_repo_root"])).resolve() == root
            == Path(host_string(binding["native_source_repo_root"])).resolve()
            and Path(host_string(binding["native_source_base"])).resolve() == native
            == Path(host_string(source["Root_native_source_base"])).resolve()
            == Path(host_string(source["snapshot_native_base"])).resolve(),
            "Same-root binding must retain the actual original compile paths")
    host_require(Path(host_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root
            and host_git(root, "rev-parse", "HEAD").decode().strip() == runtime_commit
            and not host_git(root, "status", "--porcelain", "--untracked-files=all").strip(),
            "Actual current runtime Root must be clean at its exact commit")
    common = (root / host_git(root, "rev-parse", "--git-common-dir").decode().strip()).resolve()
    host_require(Path(host_string(binding["common_git_directory"])).resolve() == common, "Actual Git store differs")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", native_commit, runtime_commit], cwd=root, capture_output=True)
    host_require(ancestor.returncode == 0, "Same-root Native compile commit must remain an ancestor")
    for key, commit in (("native_subtree_tree_id", native_commit), ("runtime_native_subtree_tree_id", runtime_commit)):
        host_require(binding[key] == host_git(root, "rev-parse", commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
                "Explicit Native Git tree identity differs")
    changed = {name for name in host_git(root, "diff", "--name-only", "-z", native_commit, runtime_commit,
        "--", NATIVE_PREFIX).decode().split("\0") if name}
    expected_changes = {HOST_RELATIVE}
    fixture_context: FixtureCMakeContext | None = None
    inactive_context: InactiveCMakeContext | None = None
    if inactive_delta is not None:
        inactive_context = qualify_inactive_cmake_delta(inactive_delta, root=root, native_commit=native_commit,
            runtime_commit=runtime_commit, machine=machine, qualification=q, snapshot=source)
        expected_changes.add(NATIVE_PREFIX + "CMakeLists.txt")
    if fixture_delta is not None:
        fixture_context = qualify_fixture_cmake_delta(fixture_delta, root=root, native_commit=native_commit,
            runtime_commit=runtime_commit, machine=machine, qualification=q, snapshot=source)
        expected_changes.add(NATIVE_PREFIX + FIXTURE_CMAKE_RELATIVE)
    consumer_context: WireConsumerContext | None = None
    if consumer_delta is not None:
        consumer_context = qualify_wire_consumer_delta(consumer_delta, root=root, native_commit=native_commit,
            runtime_commit=runtime_commit, machine=machine, qualification=q, snapshot=source)
        expected_changes.add(NATIVE_PREFIX + NONCOMPILED_CONSUMER_RELATIVE)
    test_context: WireConsumerContext | None = None
    if host_test_change is not None:
        delta_value = host_read(Path(host_checked(binding.get("shared_python_host_delta"))["path"]))
        host_require(delta_value.get("host_test_change") == host_test_change,
                     "Host test companion differs between the host and checkout contracts")
        test_context = qualify_host_test_companion(host_test_change, root=root, native_commit=native_commit,
            runtime_commit=runtime_commit, machine=machine, qualification=q, snapshot=source, host_delta=delta_value)
        expected_changes.add(NATIVE_PREFIX + HOST_TEST_COMPANION_RELATIVE)
    host_require(changed == expected_changes, "Same-root Native differences must be exactly the canonical host and explicit fixture exception")
    original_blob = host_checked(binding["original_shared_host_blob"])
    original_signature: Signature = {"bytes": original_blob["bytes"], "sha256": original_blob["sha256"]}
    host_require(not Path(original_blob["path"]).resolve().is_relative_to(root), "Original host blob must be separately preserved")
    host_require(host_signature(host_git(root, "show", native_commit + ":" + HOST_RELATIVE))
            == original_signature, "Original host blob is not the actual old Git content")
    rows = host_arr(source["files"])
    host_require(host_exact_integer(source["source_count"]) == len(rows), "Complete original Native source count differs")
    declared: set[str] = set()
    for raw in rows:
        row = host_obj(raw)
        host_require(set(row) == {"native_relative", "bytes", "sha256"}, "Direct original Native source rows required")
        name = host_string(row["native_relative"])
        host_require(not Path(name).anchor and "\\" not in name and ":" not in name
                and all(part not in {"", ".", ".."} for part in name.split("/"))
                and name not in declared, "Unsafe or duplicate Native source row")
        declared.add(name)
        expected = host_parse_signature({key: row[key] for key in ("bytes", "sha256")})
        current = native / name
        host_require(not current.is_symlink(), "Native inputs cannot be symbolic")
        if name == HOST_NATIVE_RELATIVE:
            host_require(expected == original_signature, "Before blob differs from the original snapshot host")
        elif name == NONCOMPILED_CONSUMER_RELATIVE and consumer_context is not None:
            before_consumer = consumer_context["before_blob"]
            host_require(expected == {"bytes": before_consumer["bytes"], "sha256": before_consumer["sha256"]},
                         "Refill before blob differs from the original snapshot")
        elif name == HOST_TEST_COMPANION_RELATIVE and test_context is not None:
            test_before = test_context["before_blob"]
            host_require(expected == {"bytes": test_before["bytes"], "sha256": test_before["sha256"]},
                         "Host test before blob differs from the original snapshot")
        elif name == FIXTURE_CMAKE_RELATIVE and fixture_context is not None:
            old_fixture = fixture_context["original_fixture_cmake_blob"]
            host_require(expected == {"bytes": old_fixture["bytes"], "sha256": old_fixture["sha256"]},
                "Fixture CMake before blob differs from the original snapshot")
        elif name == "CMakeLists.txt" and inactive_context is not None:
            old_inactive = inactive_context["original_inactive_cmake_blob"]
            host_require(expected == {"bytes": old_inactive["bytes"], "sha256": old_inactive["sha256"]},
                         "Inactive CMake before blob differs from the original snapshot")
        else:
            host_require(host_signature(current.read_bytes()) == expected, "Non-host Native raw input changed: " + name)
    for command in (("ls-files", "-z", "--", NATIVE_PREFIX),
                    ("ls-tree", "-r", "--name-only", "-z", native_commit, "--", NATIVE_PREFIX)):
        tracked = {name.removeprefix(NATIVE_PREFIX) for name in host_git(root, *command).decode().split("\0") if name}
        host_require(tracked == declared, "Complete original/current Native path set differs")
    delta_ref = host_checked(binding["shared_python_host_delta"])
    host_require(delta_ref == host_pin(native_shared_python_host_delta), "Reviewed same-root delta pin differs")
    delta = host_read(native_shared_python_host_delta)
    wanted_delta_schema = HOST_DELTA_SCHEMA if consumer_delta is None else HOST_CONSUMER_DELTA_SCHEMA
    host_require(delta.get("schema") == wanted_delta_schema, "Explicit same-root delta schema required")
    if consumer_delta is not None:
        host_require(host_checked(delta.get("noncompiled_consumer_delta")) == host_checked(consumer_delta),
                     "Refill consumer delta differs between the host and checkout contracts")
    api = host_shared_api()
    host_validate_compiled_inputs(delta.get("compiled_inputs"), api.compiled_inputs(q, source))
    context = host_obj(api.qualify_shared_host_delta(native_shared_python_host_delta, root=root, native_repo=root,
        runtime_commit=runtime_commit, native_commit=native_commit, machine=machine,
        qualified_native_ref=qualified_native_ref, qualification=q, snapshot_ref=snapshot_ref, snapshot=source,
        same_root_before_blob=original_blob, same_root_fixture_cmake=fixture_delta,
        same_root_inactive_cmake=inactive_delta,
        same_root_wire_consumer=consumer_delta, same_root_host_test=host_test_change))
    result: SourceContext = {"native_source_base": native, "binding_ref": binding_ref,
        "runtime_shared_host_pin": host_checked(context["runtime_host_pin"]), "original_shared_host_blob": original_blob,
        "shared_python_host_delta": delta_ref, "shared_host_qualification": host_checked(context["shared_host_qualification"])}
    if fixture_context is not None:
        result["original_fixture_cmake_blob"] = fixture_context["original_fixture_cmake_blob"]
        result["runtime_fixture_cmake_pin"] = fixture_context["runtime_fixture_cmake_pin"]
    if inactive_context is not None:
        result["original_inactive_cmake_blob"] = inactive_context["original_inactive_cmake_blob"]
        result["runtime_inactive_cmake_pin"] = inactive_context["runtime_inactive_cmake_pin"]
    if consumer_context is not None:
        result["original_research_blobs"] = {NONCOMPILED_CONSUMER_RELATIVE: consumer_context["before_blob"]}
        result["runtime_research_pins"] = {NONCOMPILED_CONSUMER_RELATIVE: consumer_context["after"]}
        result["noncompiled_replay"] = {"before_blob": consumer_context["before_blob"],
            "after": consumer_context["after"], "binding": binding_ref}
        if test_context is not None:
            result["original_research_blobs"][HOST_TEST_COMPANION_RELATIVE] = test_context["before_blob"]
            result["runtime_research_pins"][HOST_TEST_COMPANION_RELATIVE] = test_context["after"]
    return result


def produce_same_root_host_binding(root: Path, qualification_path: Path, delta_path: Path, original_blob: Path,
                    output: Path, machine: str, *, original_fixture_cmake_blob: Path | None = None,
                    fixture_link_receipt: Path | None = None,
                    noncompiled_consumer_delta: Path | None = None,
                    original_host_test_blob: Path | None = None,
                    inactive_cmake_delta: Path | None = None) -> FilePin:
    root = root.resolve()
    qref = host_pin(qualification_path)
    q = host_read(qualification_path)
    snapshot_ref = host_checked(q["snapshot"])
    source = host_read(Path(snapshot_ref["path"]))
    native_commit, runtime_commit = host_string(q["source_commit"]), host_git(root, "rev-parse", "HEAD").decode().strip()
    native = root / NATIVE_PREFIX
    value = {"schema": HOST_BINDING_SCHEMA, "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_repo_root": str(root), "runtime_source_commit": runtime_commit, "native_source_repo_root": str(root),
        "native_source_commit": native_commit, "native_source_base": str(native.resolve()),
        "native_subtree_tree_id": host_git(root, "rev-parse", native_commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
        "runtime_native_subtree_tree_id": host_git(root, "rev-parse", runtime_commit + ":" + NATIVE_PREFIX.rstrip("/")).decode().strip(),
        "common_git_directory": str((root / host_git(root, "rev-parse", "--git-common-dir").decode().strip()).resolve()),
        "qualified_native": qref, "snapshot": snapshot_ref, "shared_python_host_delta": host_pin(delta_path),
        "original_shared_host_blob": host_pin(original_blob)}
    if original_fixture_cmake_blob is not None or fixture_link_receipt is not None:
        host_require(noncompiled_consumer_delta is None, "Fixture and refill consumer exceptions cannot be combined")
        if original_fixture_cmake_blob is None or fixture_link_receipt is None:
            raise ValueError("Fixture CMake original blob and actual link receipt must be supplied together")
        value["schema"] = HOST_FIXTURE_BINDING_SCHEMA
        value["fixture_cmake_delta"] = {"schema": "ck3-exact-fixture-cmake-link-completion-v1",
            "original_blob": host_pin(original_fixture_cmake_blob), "fixture_link_receipt": host_pin(fixture_link_receipt)}
    if inactive_cmake_delta is not None:
        host_require(original_fixture_cmake_blob is None and fixture_link_receipt is None
            and noncompiled_consumer_delta is None and original_host_test_blob is None,
            "Inactive CMake cannot combine with other source exceptions")
        value["schema"] = HOST_INACTIVE_CMAKE_BINDING_SCHEMA
        value["inactive_cmake_delta"] = host_read(inactive_cmake_delta)
    if noncompiled_consumer_delta is not None:
        value["schema"] = HOST_CONSUMER_BINDING_SCHEMA
        value["noncompiled_consumer_delta"] = host_pin(noncompiled_consumer_delta)
    if original_host_test_blob is not None:
        host_require(noncompiled_consumer_delta is not None, "Host test companion requires the explicit wire consumer transition")
        value["host_test_change"] = {"before_blob": host_pin(original_host_test_blob),
            "after": host_pin(native / HOST_TEST_COMPANION_RELATIVE)}
    host_require(not output.resolve().is_relative_to(root), "Source-binding output must remain outside the checkout")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
    qualify_same_root_host(output, root=root, runtime_commit=runtime_commit, native_commit=native_commit,
        machine=machine, qualified_native_ref=qref, qualification=q, snapshot_ref=snapshot_ref,
        snapshot=source, native_shared_python_host_delta=delta_path)
    return host_pin(output)


def same_root_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo-root", "qualification", "host-delta", "original-host-blob", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--original-fixture-cmake-blob", type=Path)
    parser.add_argument("--inactive-cmake-delta", type=Path,
                        help="exact inactive prisoner wire relocation with original cache/configure evidence")
    parser.add_argument("--fixture-link-receipt", type=Path)
    parser.add_argument("--noncompiled-consumer-delta", type=Path,
                        help="explicit reviewed delta for the sole existing refill wire consumer")
    parser.add_argument("--original-host-test-blob", type=Path,
                        help="original Git bytes of the sole reviewed host test companion")
    args = parser.parse_args()
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
        str(args.repo_root / "tools/ck3_live_run_id.py"), "machine"], cwd=args.repo_root).decode().strip()
    result = produce_same_root_host_binding(args.repo_root, args.qualification, args.host_delta, args.original_host_blob,
        args.output, machine, original_fixture_cmake_blob=args.original_fixture_cmake_blob,
        fixture_link_receipt=args.fixture_link_receipt, noncompiled_consumer_delta=args.noncompiled_consumer_delta,
        original_host_test_blob=args.original_host_test_blob, inactive_cmake_delta=args.inactive_cmake_delta)
    print(json.dumps({"source_binding": result, "native_rebuilt": False, "game_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(same_root_main())
