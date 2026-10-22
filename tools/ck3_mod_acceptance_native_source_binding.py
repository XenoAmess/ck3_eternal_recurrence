"""Explicit equivalence for an actual clean linked Native source worktree.

This verifies source provenance only. It never confers build or live credit.
The qualified build's snapshot and CMake paths retain their original identities.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
SCHEMA = "ck3-native-worktree-source-binding-v1"
FIELDS = frozenset({
    "schema", "machine_id", "observed_at_utc", "runtime_repo_root",
    "runtime_source_commit", "native_source_repo_root", "native_source_commit",
    "native_source_base", "native_subtree_tree_id", "common_git_directory",
    "qualified_native", "snapshot",
})


DELTA_FIELDS = FIELDS | {"runtime_native_subtree_tree_id", "shared_python_host_delta"}


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def timestamp(value):
    require(isinstance(value, str), "Explicit timezone-aware source observation required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Source observation must include its timezone")
    return result.astimezone(timezone.utc)


def checkout(repo, commit):
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
    if isinstance(value, dict) and value.get("schema") == "ck3-native-same-root-shared-python-host-binding-v1":
        path = Path(__file__).with_name("ck3_mod_acceptance_same_root_host_delta.py")
        spec = importlib.util.spec_from_file_location("ck3_same_root_host_source_binding", path)
        if spec is None or spec.loader is None:
            raise ValueError("Same-root source validator unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.qualify_same_root_host(binding_path, root=root, runtime_commit=runtime_commit,
            native_commit=native_commit, machine=machine, qualified_native_ref=qualified_native_ref,
            qualification=qualification, snapshot_ref=snapshot_ref, snapshot=snapshot,
            native_shared_python_host_delta=native_shared_python_host_delta)
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
            require({key: actual[key] for key in wanted} == wanted,
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
