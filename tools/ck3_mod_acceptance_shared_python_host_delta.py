"""Exact opt-in for one reviewed shared Python host beside unchanged Native inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

NATIVE_PREFIX = "ck3_autonomous_player/native_bridge/"
HOST_RELATIVE = NATIVE_PREFIX + "research/run_ck3_12002_mcp_live.py"
HOST_NATIVE_RELATIVE = HOST_RELATIVE.removeprefix(NATIVE_PREFIX)
CONTRACT_FIELDS = frozenset({
    "schema", "machine_id", "observed_at_utc", "runtime_source_commit", "native_source_commit",
    "canonical_repo_relative", "source_classification", "before", "after", "qualified_native",
    "snapshot", "compiled_inputs", "reviewed_host_change", "shared_host_qualification",
})


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def signature(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def pin(path):
    path = Path(path).resolve()
    return {"path": str(path), **signature(path.read_bytes())}


def checked(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "bytes", "sha256"}
            and pin(ref["path"]) == ref, "Exact shared-host source/evidence pin changed")
    return ref


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True).stdout


def compiled_inputs(qualification, snapshot):
    """Read the original actual File API cohort; never infer it from a suffix."""
    scope_ref = checked(qualification["configured_scope"])
    scope = read(scope_ref["path"])
    require(scope.get("snapshot") == qualification["snapshot"], "Compiled cohort snapshot differs")
    model_ref = checked(scope["codemodel"])
    commands_ref = checked(scope["compile_commands"])
    model = read(model_ref["path"])
    native_root = Path(snapshot["snapshot_native_base"]).resolve()
    require(Path(model["paths"]["source"]).resolve() == native_root,
            "Shared-host contract must retain the actual compile source path")
    reply = Path(model_ref["path"]).resolve().parent
    targets = {}
    for row in model["configurations"][0]["targets"]:
        path = (reply / row["jsonFile"]).resolve()
        require(path.is_relative_to(reply), "Unsafe actual File API target path")
        targets[row["id"]] = read(path)
    starts = [key for key, row in targets.items() if row["name"] == "xar_ck3_bridge"]
    require(len(starts) == 1, "Exact original production target required")
    pending, production = starts[:], {}
    while pending:
        key = pending.pop()
        if key in production:
            continue
        production[key] = targets[key]
        pending.extend(row["id"] for row in targets[key].get("dependencies", []) if row["id"] in targets)
    require(not any("fixture" in row["name"].lower() for row in production.values()),
            "Fixture entered unchanged production cohort")
    declared = {row["name"]: row for row in scope["targets"]}
    indexed = {row["native_relative"]: row for row in snapshot["files"]}
    counts, sources = {}, set()
    for row in production.values():
        require(row["name"] in declared, "Production File API target is not in the sealed scope")
        for key in ("type", "sources", "compileGroups", "artifacts"):
            require(row.get(key, []) == declared[row["name"]].get(key, []),
                    "Actual production File API cohort drifted")
        compiled = [src for src in row.get("sources", []) if src.get("compileGroupIndex") is not None]
        counts[row["name"]] = len(compiled)
        for src in compiled:
            path = Path(src["path"])
            path = path.resolve() if path.is_absolute() else (native_root / path).resolve()
            require(path.is_relative_to(native_root), "Compiled body escapes the original Native source")
            relative = path.relative_to(native_root).as_posix()
            require(relative != HOST_NATIVE_RELATIVE and relative in indexed
                    and "source" not in indexed[relative],
                    "Canonical shared Python host cannot be a compiled production body")
            sources.add(relative)
    require(counts == scope["production_TUs"], "Actual production TU counts differ from the sealed scope")
    commands = read(commands_ref["path"])
    command_sources = {Path(row["file"]).resolve() for row in commands}
    require(native_root / HOST_NATIVE_RELATIVE not in command_sources
            and all(native_root / relative in command_sources for relative in sources),
            "Compile commands include the host or omit an actual production body")
    fingerprint = [[relative, indexed[relative]["bytes"], indexed[relative]["sha256"]]
                   for relative in sorted(sources)]
    return {
        "configured_scope": scope_ref, "codemodel": model_ref, "compile_commands": commands_ref,
        "production_freeze": checked(qualification["production_freeze"]),
        "published_dll": checked(qualification["published_dll"]),
        "production_TUs": counts, "unique_production_source_count": len(sources),
        "production_source_set_sha256": hashlib.sha256(json.dumps(fingerprint, separators=(",", ":")).encode()).hexdigest(),
    }


def qualify_shared_host_delta(path: Path, *, root: Path, native_repo: Path, runtime_commit: str, native_commit: str,
                              machine: str, qualified_native_ref: object, qualification: dict[str, object],
                              snapshot_ref: object, snapshot: dict[str, object],
                              same_root_before_blob: object = None) -> dict[str, object]:
    ref = pin(path)
    value = read(path)
    schema = "ck3-exact-shared-python-host-delta-v1"
    old_blob = None
    if same_root_before_blob is not None:
        require(native_repo.resolve() == root.resolve(), "Before-blob source is only for an explicit same-root delta")
        old_blob = checked(same_root_before_blob)
        require(not Path(old_blob["path"]).resolve().is_relative_to(root.resolve()),
                "Original host blob must remain separately preserved")
        schema = "ck3-exact-same-root-python-host-delta-v1"
    require(isinstance(value, dict) and set(value) == CONTRACT_FIELDS
            and value.get("schema") == schema,
            "Exact single shared Python-host delta contract required")
    require(value["machine_id"] == machine and value["runtime_source_commit"] == runtime_commit
            and value["native_source_commit"] == native_commit
            and value["qualified_native"] == qualified_native_ref and value["snapshot"] == snapshot_ref,
            "Shared-host contract must bind this machine, runtime/compile commits and original Q3/snapshot")
    require(value["canonical_repo_relative"] == HOST_RELATIVE and value["source_classification"] == "shared_host",
            "Only the canonical shared Python host is eligible for this source delta")
    observed = datetime.fromisoformat(value["observed_at_utc"].replace("Z", "+00:00"))
    qualified_observation = qualification["observed_at_utc"]
    if not isinstance(qualified_observation, str):
        raise ValueError("Qualified source observation must be a string")
    qualified_at = datetime.fromisoformat(qualified_observation.replace("Z", "+00:00"))
    require(observed.tzinfo is not None and qualified_at.tzinfo is not None
            and qualified_at <= observed <= datetime.now(timezone.utc), "Actual late shared-host observation required")
    for key in ("before", "after"):
        row = value[key]
        require(isinstance(row, dict) and set(row) == {"bytes", "sha256"}
                and type(row["bytes"]) is int and row["bytes"] > 0,
                "Exact reviewed shared-host raw signature required")
    require(value["before"] != value["after"], "An explicit shared-host delta must actually change its source")
    changed = {name for name in git(root, "diff", "--name-only", "-z", native_commit, runtime_commit,
                                   "--", NATIVE_PREFIX).decode("utf-8").split("\0") if name}
    require(changed == {HOST_RELATIVE}, "Native Git differences must be exactly the one canonical shared Python host")
    for repo, commit, expected in ((native_repo, native_commit, value["before"]),
                                   (root, runtime_commit, value["after"])):
        require(signature(git(repo, "show", commit + ":" + HOST_RELATIVE)) == expected,
                "Reviewed shared-host signature differs from its actual committed blob")
        entry = git(repo, "ls-tree", commit, "--", HOST_RELATIVE).decode("utf-8")
        require(entry.startswith("100644 blob "), "Canonical shared host must remain a regular tracked Python file")
        raw_path = Path(old_blob["path"]) if old_blob is not None and commit == native_commit else repo / HOST_RELATIVE
        require(signature(raw_path.read_bytes()) == expected,
                "Actual shared-host checkout raw differs from its reviewed commit")
    snapshot_rows = snapshot["files"]
    if not isinstance(snapshot_rows, list) or not all(isinstance(row, dict) for row in snapshot_rows):
        raise ValueError("Native snapshot source rows must be objects")
    host = [row for row in snapshot_rows if row["native_relative"] == HOST_NATIVE_RELATIVE]
    require(len(host) == 1 and {key: host[0][key] for key in ("bytes", "sha256")} == value["before"],
            "Shared-host before pin is not the original frozen Native source")
    require(value["compiled_inputs"] == compiled_inputs(qualification, snapshot),
            "Shared-host contract changed the original actual compiled cohort")
    review_ref = checked(value["reviewed_host_change"])
    review = read(review_ref["path"])
    require(review.get("schema") == "ck3-reviewed-canonical-shared-python-host-change-v1"
            and review.get("machine_id") == machine and review.get("result") == "PASS"
            and review.get("canonical_repo_relative") == HOST_RELATIVE
            and review.get("source_classification") == "shared_host"
            and review.get("before") == value["before"] and review.get("after") == value["after"]
            and review.get("actual_live_business_qualified") is False,
            "Independent source review must bind this exact one-host transition")
    consumer_ref = checked(review["source_consumer"])
    consumer = read(consumer_ref["path"])
    delta_ref = checked(review["source_delta"])
    delta = read(delta_ref["path"])
    require(delta.get("target") == HOST_RELATIVE
            and {key: delta.get("base_source", {}).get(key) for key in ("bytes", "sha256")} == value["before"]
            and {"bytes": delta.get("candidate_bytes"), "sha256": delta.get("candidate_sha256")} == value["after"]
            and consumer.get("pins", {}).get(delta_ref["path"]) == {key: delta_ref[key] for key in ("bytes", "sha256")},
            "Actual finite consumer must pin the reviewed exact before/after host source delta")
    waits = [consumer[key] for key in ("original_popen_wait_returncode", "original_Popen_wait_returncode",
                                     "original_wait_returncode", "exit_code") if key in consumer]
    require(consumer.get("machine_id") == machine and consumer.get("result") == "PASS"
            and waits and all(type(code) is int and code == 0 for code in waits)
            and (consumer.get("no_skips") is True or type(consumer.get("skipped")) is int and consumer["skipped"] == 0),
            "Exact actual finite shared-host source consumer and original zero wait required")
    qualification_ref = checked(value["shared_host_qualification"])
    source_qualification = read(qualification_ref["path"])
    require(source_qualification.get("source_consumer") == consumer_ref
            and source_qualification.get("source_delta") == delta_ref
            and source_qualification.get("reviewed_host_change") == review_ref,
            "Runtime shared-host qualification must retain the original finite source consumer and independent review")
    return {"ref": ref, "runtime_host_pin": pin(root / HOST_RELATIVE),
            "shared_host_qualification": qualification_ref, "review": review_ref,
            "source_consumer": consumer_ref, "compiled_inputs": value["compiled_inputs"]}
