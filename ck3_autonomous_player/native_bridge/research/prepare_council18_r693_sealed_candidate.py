"""Materialize a fresh, self-contained R693 candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from council18_candidate_runtime_identity import (
    BUILD_RELEASE_GIT_BLOB_OID,
    SOURCE_COMMIT as RUNTIME_SOURCE_COMMIT,
    SOURCE_TREE_GIT_OID,
    build_source_identity,
)
from json_input_contract import load_json_object


SOURCE_BRIDGE_COMMIT = "a04ee02a04a3a86bb685395270d8cd23359b8ba2"
SOURCE_HARNESS_COMMIT = "9cdb430849b98d9d807f10a23eca8c149b316630"
SOURCE_SEALED_SHA256 = (
    "F2AE0102A0D645F9FE4A71A010DF59D9048C3D3C1C860D47C8879100C6F85436"
)
SOURCE_CANDIDATE_SHA256 = (
    "DE8597D9440F9F65AFD6976E1F55250777C323D3E914A734703A4F5D90E837FD"
)
SOURCE_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_council16_r692_9cdb430"
EXPECTED_INPUT_SHA256 = (
    "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800"
)
SAVE_SHA256 = (
    "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
)
R692_RED_REPORT_SHA256 = (
    "3C436C1429CAA1529309C26A1B74B1CB0C60D4A02893FBE3F06A59BE81BCD5BA"
)
R692_RAW_PROBE_SHA256 = (
    "0155181C5E4556907D478E57B2324578267DD12208C3FE7E9D6FD8F928320496"
)
R692_EVIDENCE_MANIFEST_SHA256 = (
    "589FFE1526F3C98DFC5C04E5F0C8A48EC41D6DB893CC5497AE459781D4F2FFCB"
)
R692_POSTRUN_PDX_SETTINGS_SHA256 = (
    "592AB6C67BF24600FA3679509F63E0688DDF45A372FE709E71D7F35CD48F5244"
)
HARNESS_PATHS = (
    "ck3_autonomous_player/native_bridge/research/council18_candidate_runtime_identity.py",
    "ck3_autonomous_player/native_bridge/research/council18_candidate_runtime_import_probe.py",
    "ck3_autonomous_player/native_bridge/research/prepare_council18_r693_sealed_candidate.py",
    "ck3_autonomous_player/native_bridge/research/test_council18_r693_sealed_candidate.py",
)
CANDIDATE_BINARIES = (
    "xar_ck3_bridge.dll",
    "xar_ck3_bridge_injector.exe",
    "xar_ck3_bridge_host.exe",
    "xar_ck3_bridge_target.exe",
    "xar_ck3_council_composition_steward_candidates_private_probe_v1_test.exe",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def environment_digest(environment: dict[str, Any]) -> str:
    stable = json.loads(json.dumps(environment, ensure_ascii=False))
    stable.pop("prepared_at", None)
    stable.pop("environment_sha256", None)
    tutorial = stable.get("persistent_tutorial_state")
    if isinstance(tutorial, dict):
        tutorial.pop("initialized_this_prepare", None)
    raw = json.dumps(
        stable, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def advance_rounds(text: str) -> str:
    """Advance the frozen R691/R692 pair without cascading replacements."""

    return (
        text.replace("R692", "__COUNCIL18_UPPER_NEW__")
        .replace("R691", "R692")
        .replace("__COUNCIL18_UPPER_NEW__", "R693")
        .replace("r692", "__council18_lower_new__")
        .replace("r691", "r692")
        .replace("__council18_lower_new__", "r693")
    )


def verify_source(source: Path) -> dict[str, Any]:
    sealed_path = source / "sealed-prep-manifest.json"
    if sha256(sealed_path) != SOURCE_SEALED_SHA256:
        raise RuntimeError("R692 source sealed manifest SHA-256 differs")
    sealed = load_json_object(
        sealed_path,
        expected_schema="xar.ck3.g2_m4_council16_r692_sealed_prep_v1",
    )
    if (
        sealed.get("status") != "sealed-no-launch"
        or sealed.get("source_commit") != SOURCE_BRIDGE_COMMIT
        or sealed.get("harness_commit") != SOURCE_HARNESS_COMMIT
        or sealed.get("candidate_manifest_sha256") != SOURCE_CANDIDATE_SHA256
        or sealed.get("suggested_round") != "R692"
        or sealed.get("round_allocated") is not False
        or sealed.get("ck3_launched") is not False
    ):
        raise RuntimeError("R692 source candidate identity differs")
    files = sealed.get("files")
    if not isinstance(files, list) or sealed.get("file_count") != len(files):
        raise RuntimeError("R692 source inventory differs")
    files = [dict(row) for row in files]
    for row in files:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise RuntimeError("R692 source inventory row is invalid")
        path = (source / row["path"]).resolve()
        path.relative_to(source)
        actual_sha = sha256(path) if path.is_file() else None
        if (
            row["path"] == "fresh-profile-state/profile/pdx_settings.txt"
            and actual_sha == R692_POSTRUN_PDX_SETTINGS_SHA256
        ):
            row["size_bytes"] = path.stat().st_size
            row["sha256"] = actual_sha
        elif (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or actual_sha != row.get("sha256")
        ):
            raise RuntimeError(f"R692 sealed file differs: {row['path']}")
    sealed["files"] = files
    verify_r692_red(source)
    return sealed


def verify_r692_red(source: Path) -> None:
    live = source / "live-r692"
    required = {
        "report.json": R692_RED_REPORT_SHA256,
        "raw-probe.json": R692_RAW_PROBE_SHA256,
        "postrun-evidence-manifest.json": R692_EVIDENCE_MANIFEST_SHA256,
    }
    for name, expected in required.items():
        path = live / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"R692 RED evidence differs: {name}")
    report = load_json_object(
        live / "report.json",
        expected_schema="xar.ck3.g2_m4_council16_r692_live_v1",
    )
    round_record = report.get("round")
    red = report.get("red")
    if (
        report.get("status") != "red"
        or not isinstance(round_record, dict)
        or round_record.get("old") != "R691"
        or round_record.get("new") != "R692"
        or not isinstance(red, dict)
        or "typed result status differs" not in str(red.get("reason"))
    ):
        raise RuntimeError("R692 RED report contract differs")
    probe = load_json_object(live / "raw-probe.json")
    private = probe.get("probe")
    if not isinstance(private, dict) or private.get("last_submit_result") != 0:
        raise RuntimeError("R692 submitted-query evidence differs")
    if private.get("last_wait_result") != 4:
        raise RuntimeError("R692 cancelled-query evidence differs")
    manifest = load_json_object(
        live / "postrun-evidence-manifest.json",
        expected_schema="xar.ck3.g2_m4_council16_r692_red_evidence_manifest_v1",
    )
    rows = manifest.get("files")
    if (
        manifest.get("status") != "red"
        or manifest.get("red_reason") != "application_main_thread_required"
        or not isinstance(rows, list)
    ):
        raise RuntimeError("R692 RED evidence manifest differs")
    for row in rows:
        path = (source / str(row["path"])).resolve()
        path.relative_to(source)
        if (
            not path.is_file()
            or path.stat().st_size != row.get("bytes")
            or sha256(path) != row.get("sha256")
        ):
            raise RuntimeError(f"R692 RED artifact differs: {row['path']}")


def verify_runtime_repository(repo_root: Path) -> list[Path]:
    tree = subprocess.run(
        ["git", "rev-parse", f"{RUNTIME_SOURCE_COMMIT}:ck3_autonomous_player/src"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if tree != SOURCE_TREE_GIT_OID:
        raise RuntimeError("runtime source Git tree identity differs")
    tool_blob = subprocess.run(
        ["git", "rev-parse", f"{RUNTIME_SOURCE_COMMIT}:tools/build_release.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if tool_blob != BUILD_RELEASE_GIT_BLOB_OID:
        raise RuntimeError("build_release Git blob identity differs")
    result = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            RUNTIME_SOURCE_COMMIT,
            "ck3_autonomous_player/src",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = [Path(row) for row in result.stdout.splitlines() if row]
    paths.append(Path("tools/build_release.py"))
    if not paths:
        raise RuntimeError("runtime source Git tree is empty")
    return paths


def verify_harness_commit(repo_root: Path, harness_commit: str) -> None:
    commit = subprocess.run(
        ["git", "cat-file", "-e", f"{harness_commit}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0:
        raise RuntimeError("harness commit is not a Git commit in the repository")
    for relative in HARNESS_PATHS:
        blob = subprocess.run(
            ["git", "cat-file", "-e", f"{harness_commit}:{relative}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            raise RuntimeError(f"harness commit does not contain {relative}")
    clean = subprocess.run(
        ["git", "diff", "--quiet", harness_commit, "--", *HARNESS_PATHS],
        cwd=repo_root,
        check=False,
    )
    if clean.returncode != 0:
        raise RuntimeError("harness files differ from the requested harness commit")


def copy_sealed_inputs(
    source: Path, output: Path, rows: list[dict[str, Any]]
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    try:
        for row in rows:
            relative = Path(str(row["path"]))
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
            if (
                target.stat().st_size != row["size_bytes"]
                or sha256(target) != row["sha256"]
            ):
                raise RuntimeError(f"copied source file differs: {row['path']}")
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def copy_built_candidate_bin(
    candidate_bin: Path, cmake_cache: Path, output: Path, repo_root: Path
) -> str:
    """Replace the R692 binaries with the exact Council17 Release build."""

    candidate_bin = candidate_bin.resolve()
    cmake_cache = cmake_cache.resolve()
    native_source = (repo_root / "ck3_autonomous_player/native_bridge").resolve()
    cache = cmake_cache.read_text(encoding="utf-8-sig", errors="strict")
    required = (
        "XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_PROBE_V1:BOOL=ON"
    )
    if required not in cache:
        raise RuntimeError("Council private probe build option is not ON")
    for option in (
        "XAR_CK3_ENABLE_G2_MILITARY_PREPARATION_SUMMARY_PRIVATE_PROBE_V1",
        "XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1",
        "XAR_CK3_ENABLE_G2_CULTURE_INNOVATION_ASYNC_PRIVATE_PROBE_V1",
        "XAR_CK3_ENABLE_G2_ACTIVITY_PLANNING_SNAPSHOT_PRIVATE_GLUE_V1",
        "XAR_CK3_ENABLE_G2_MAJOR_DECISION_FOUND_KINGDOM_INTERNAL_ROUTE_V1",
    ):
        if f"{option}:BOOL=ON" in cache:
            raise RuntimeError(f"unrelated private probe is enabled: {option}")
    source_row = f"CMAKE_HOME_DIRECTORY:INTERNAL={native_source}"
    if source_row.replace("\\", "/") not in cache.replace("\\", "/"):
        raise RuntimeError("CMake source root differs from the candidate repository")
    target = output / "candidate-bin"
    shutil.rmtree(target)
    target.mkdir()
    for name in CANDIDATE_BINARIES:
        source = candidate_bin / name
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"Release candidate binary is missing: {name}")
        shutil.copyfile(source, target / name)
    return sha256(cmake_cache)


def copy_runtime(repo_root: Path, output: Path, paths: list[Path]) -> dict[str, Any]:
    target_repository = output / "source-repo"
    shutil.rmtree(target_repository, ignore_errors=True)
    for relative in paths:
        target = output / "source-repo" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(
            ["git", "show", f"{RUNTIME_SOURCE_COMMIT}:{relative.as_posix()}"],
            cwd=repo_root,
            capture_output=True,
            check=True,
        ).stdout
        target.write_bytes(blob)
    identity = build_source_identity(output / "source-repo")
    write_json(output / "source-repo/source-identity.json", identity)
    return identity


def patch_environment(source: Path, output: Path) -> tuple[str, str]:
    descriptor_path = output / "fresh-profile-state/profile/mod/xar_autoplayer.mod"
    descriptor = descriptor_path.read_text(encoding="utf-8-sig")
    if descriptor.count(source.as_posix()) != 1:
        raise RuntimeError("profile descriptor source binding differs")
    descriptor = descriptor.replace(source.as_posix(), output.as_posix())
    descriptor_path.write_text(descriptor, encoding="utf-8")
    environment_path = (
        output / "fresh-profile-state/profile/xar-autoplayer-environment.json"
    )
    environment = load_json_object(environment_path)

    def relocate(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(str(source), str(output))
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        return value

    environment = relocate(environment)
    if not isinstance(environment, dict):
        raise RuntimeError("relocated environment is not an object")
    load_profile = environment.get("load_profile")
    if not isinstance(load_profile, dict):
        raise RuntimeError("environment load profile is absent")
    load_profile["outer_descriptor_sha256"] = sha256(descriptor_path).lower()
    environment["environment_sha256"] = environment_digest(environment)
    write_json(environment_path, environment)
    return str(environment["environment_sha256"]), sha256(environment_path)


def patch_python_entrypoints(output: Path, harness_commit: str, pipe: str) -> None:
    bindings = (
        ("run_r692.py", "run_r693.py"),
        ("invoke_r692.py", "invoke_r693.py"),
        ("verify_prep.py", "verify_prep.py"),
    )
    for old_name, new_name in bindings:
        path = output / old_name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(SOURCE_PIPE, pipe)
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = advance_rounds(text)
        text = text.replace("COUNCIL16", "COUNCIL18")
        text = text.replace("council16", "council18")
        target = output / new_name
        target.write_text(text, encoding="utf-8")
        if target != path:
            path.unlink()


def patch_metadata(
    source: Path,
    output: Path,
    harness_commit: str,
    pipe: str,
    source_identity: dict[str, Any],
    cmake_cache_sha256: str,
) -> None:
    candidate_path = output / "candidate-manifest.json"
    candidate = load_json_object(candidate_path)
    candidate["schema"] = "xar.ck3.g2_m4_council18_r693_harness_candidate_v1"
    candidate["source_commit"] = RUNTIME_SOURCE_COMMIT
    candidate["harness_commit"] = harness_commit
    candidate["council17_commit"] = RUNTIME_SOURCE_COMMIT
    candidate["runtime_source"] = source_identity
    candidate["cmake_cache_sha256"] = cmake_cache_sha256
    candidate["files"] = [
        {
            "path": f"candidate-bin/{name}",
            "size_bytes": (output / "candidate-bin" / name).stat().st_size,
            "sha256": sha256(output / "candidate-bin" / name),
        }
        for name in CANDIDATE_BINARIES
    ]
    candidate["driver_snapshot_api_contract"].update(
        {
            "baseline_commit": RUNTIME_SOURCE_COMMIT,
            "operator_workspace_preflight_required": False,
            "candidate_local_source_required": True,
            "module_file_and_sha_asserted": True,
        }
    )
    candidate["next_live"] = {
        "suggested_round": "R693",
        "unique_pipe": pipe,
        "paused_only": True,
        "publish_timeout_seconds": 20,
        "same_round_retry": False,
    }
    candidate["r692_capability_red"] = {
        "classification": "queued_query_cancelled_before_execution",
        "report_sha256": R692_RED_REPORT_SHA256,
        "raw_probe_sha256": R692_RAW_PROBE_SHA256,
        "evidence_manifest_sha256": R692_EVIDENCE_MANIFEST_SHA256,
        "ck3_process_started": True,
        "attempted_round_consumed": True,
        "same_candidate_retry_allowed": False,
    }
    candidate["queued_query_fix"] = {
        "integrated_commit": RUNTIME_SOURCE_COMMIT,
        "queued_and_executing_requests_retained_across_heartbeats": True,
        "terminal_reclaim_only": True,
        "public_surface_changed": False,
    }
    candidate["fresh_profile_config"] = {
        "source": "R692 postrun pdx_settings only",
        "pdx_settings_sha256": R692_POSTRUN_PDX_SETTINGS_SHA256,
        "logs_copied": False,
        "control_state_copied": False,
        "target_save_reset_from_unchanged_R692_source": True,
    }
    write_json(candidate_path, candidate)

    environment_sha, environment_manifest_sha = patch_environment(source, output)
    for name in ("profile-preflight.json", "preflight.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = advance_rounds(str(payload["schema"])).replace(
            "council16", "council18"
        )
        payload["source_commit"] = RUNTIME_SOURCE_COMMIT
        payload["harness_commit"] = harness_commit
        payload["environment_sha256"] = environment_sha
        if name == "profile-preflight.json":
            payload["environment_manifest_sha256"] = environment_manifest_sha
        write_json(path, payload)

    ownership_path = output / "round-ownership-proposal.json"
    ownership = load_json_object(ownership_path)
    ownership.update(
        {
            "suggested_new_round": "R693",
            "allocated": False,
            "current": "R693 suggested; not allocated",
            "expected_old_round": "R692",
            "ck3_launched": False,
            "pid": None,
            "watchdog_pid": None,
            "candidate_revision": harness_commit,
            "pipe": pipe,
        }
    )
    write_json(ownership_path, ownership)

    validation_path = output / "validation-results.json"
    validation = load_json_object(validation_path)
    validation["schema"] = "xar.ck3.g2_m4_council18_r693_validation_v1"
    validation["status"] = "static-ready-no-launch"
    validation["next_round"] = "R693"
    validation["ck3_launched"] = False
    validation["candidate_no_launch_preflight"] = "pending-one-shot"
    validation["r692_capability_red"] = candidate["r692_capability_red"]
    validation["queued_query_fix"] = {
        "integrated_commit": RUNTIME_SOURCE_COMMIT,
        "python_normal": "passed",
        "python_optimized": "passed",
        "release_private_probe_test": "passed",
        "release_suspended_injection_test": "passed",
    }
    validation["self_contained_runtime_contract"] = {
        "normal": "passed",
        "optimized": "passed",
        "candidate_local_source": True,
        "source_commit": RUNTIME_SOURCE_COMMIT,
        "source_tree_sha256": source_identity["source_tree_sha256"],
        "module_file_and_sha_asserted": True,
        "external_workspace_root_allowed": False,
    }
    write_json(validation_path, validation)

    preflight = load_json_object(output / "preflight.json")
    preflight["candidate_manifest_sha256"] = sha256(candidate_path)
    write_json(output / "preflight.json", preflight)

    for name in ("operator-runtime.json", "operator-runtime.example.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = "xar.ck3.g2_m4_council18_operator_runtime_v1"
        payload["runtime_source"] = (
            "candidate-local:source-repo/ck3_autonomous_player/src"
        )
        write_json(path, payload)


def patch_text_bindings(
    source: Path, output: Path, harness_commit: str, pipe: str
) -> None:
    for old_name, new_name in (
        ("execute-command.txt", "execute-command.txt"),
        ("preflight-command.txt", "preflight-command.txt"),
        ("R692-start-checklist.md", "R693-start-checklist.md"),
    ):
        path = output / old_name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(str(source), str(output))
        text = text.replace(source.as_posix(), output.as_posix())
        text = text.replace(SOURCE_PIPE, pipe)
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = advance_rounds(text)
        text = text.replace("COUNCIL16", "COUNCIL18")
        text = text.replace("council16", "council18")
        target = output / new_name
        target.write_text(text, encoding="utf-8")
        if target != path:
            path.unlink()


def seal(
    output: Path,
    harness_commit: str,
    pipe: str,
    source_identity: dict[str, Any],
) -> tuple[str, str]:
    candidate_hash = sha256(output / "candidate-manifest.json")
    excluded = {"sealed-prep-manifest.json", "sealed-prep-manifest.sha256"}
    rows = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        relative = path.relative_to(output).as_posix()
        if relative in excluded:
            continue
        rows.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema": "xar.ck3.g2_m4_council18_r693_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": RUNTIME_SOURCE_COMMIT,
        "harness_commit": harness_commit,
        "suggested_round": "R693",
        "expected_old_round": "R692",
        "round_allocated": False,
        "ck3_launched": False,
        "candidate_manifest_sha256": candidate_hash,
        "bridge_dll_sha256": sha256(output / "candidate-bin/xar_ck3_bridge.dll"),
        "source_save_sha256": sha256(output / "source-save/dev3b_r639.ck3"),
        "unique_pipe": pipe,
        "source_r692_sealed_manifest_sha256": SOURCE_SEALED_SHA256,
        "source_r692_red": {
            "report_sha256": R692_RED_REPORT_SHA256,
            "raw_probe_sha256": R692_RAW_PROBE_SHA256,
            "evidence_manifest_sha256": R692_EVIDENCE_MANIFEST_SHA256,
        },
        "runtime_source": source_identity,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "fresh_state_contract": {
            "source_manifest_rows_only": True,
            "r692_live_copied": False,
            "r692_control_copied": False,
        },
        "file_count": len(rows),
        "files": rows,
    }
    manifest_path = output / "sealed-prep-manifest.json"
    write_json(manifest_path, manifest)
    manifest_hash = sha256(manifest_path)
    (output / "sealed-prep-manifest.sha256").write_text(
        f"{manifest_hash}  sealed-prep-manifest.json\n", encoding="ascii"
    )
    return candidate_hash, manifest_hash


def materialize(
    source: Path,
    output: Path,
    harness_commit: str,
    repo_root: Path,
    candidate_bin: Path,
    cmake_cache: Path,
) -> dict[str, str]:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    if not re.fullmatch(r"[0-9a-f]{40}", harness_commit):
        raise ValueError("harness commit must be a lowercase full Git hash")
    verify_harness_commit(repo_root, harness_commit)
    if harness_commit[:7] not in output.name:
        raise ValueError("output directory must include the harness short hash")
    if not output.name.startswith("g2-m4-council18-r693-"):
        raise ValueError("output directory must use the COUNCIL18 R693 prefix")
    sealed = verify_source(source)
    tracked_paths = verify_runtime_repository(repo_root)
    pipe = rf"\\.\pipe\xar_ck3_bridge_g2_m4_council18_r693_{harness_commit[:7]}"
    copy_sealed_inputs(source, output, sealed["files"])
    try:
        cache_hash = copy_built_candidate_bin(
            candidate_bin, cmake_cache, output, repo_root
        )
        source_identity = copy_runtime(repo_root, output, tracked_paths)
        shutil.copyfile(
            Path(__file__).with_name("council18_candidate_runtime_identity.py"),
            output / "candidate_runtime_identity.py",
        )
        shutil.copyfile(
            Path(__file__).with_name("council18_candidate_runtime_import_probe.py"),
            output / "candidate_runtime_import_probe.py",
        )
        patch_python_entrypoints(output, harness_commit, pipe)
        patch_metadata(
            source,
            output,
            harness_commit,
            pipe,
            source_identity,
            cache_hash,
        )
        patch_text_bindings(source, output, harness_commit, pipe)
        if (output / "live-r692").exists() or (output / "live-r693").exists():
            raise RuntimeError("fresh candidate contains a live directory")
        control = output / "fresh-profile-state/control"
        if control.exists() and any(control.iterdir()):
            raise RuntimeError("fresh candidate contains inherited control state")
        candidate_hash, sealed_hash = seal(
            output, harness_commit, pipe, source_identity
        )
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return {
        "output": str(output),
        "harness_commit": harness_commit,
        "candidate_manifest_sha256": candidate_hash,
        "sealed_prep_manifest_sha256": sealed_hash,
        "runtime_source_commit": RUNTIME_SOURCE_COMMIT,
        "runtime_source_tree_sha256": str(source_identity["source_tree_sha256"]),
        "unique_pipe": pipe,
        "ck3_launched": "false",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--harness-commit", required=True)
    parser.add_argument("--candidate-bin", type=Path, required=True)
    parser.add_argument("--cmake-cache", type=Path, required=True)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args(argv)
    print(
        json.dumps(
            materialize(
                args.source,
                args.output,
                args.harness_commit,
                args.repo_root,
                args.candidate_bin,
                args.cmake_cache,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
