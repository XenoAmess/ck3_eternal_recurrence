"""Materialize a fresh, self-contained R692 candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from council16_candidate_runtime_identity import (
    BUILD_RELEASE_GIT_BLOB_OID,
    SOURCE_COMMIT as RUNTIME_SOURCE_COMMIT,
    SOURCE_TREE_GIT_OID,
    build_source_identity,
)
from json_input_contract import load_json_object


SOURCE_BRIDGE_COMMIT = "a04ee02a04a3a86bb685395270d8cd23359b8ba2"
SOURCE_HARNESS_COMMIT = "e5c6b4db63bf5d407c8bb04746f1e9d620b9599a"
SOURCE_SEALED_SHA256 = (
    "D585577C8A6AFF83537257DB4A26FF05EA2BD6EB479E4ACD46D8B847355C790C"
)
SOURCE_CANDIDATE_SHA256 = (
    "645CDCFA8A9B03E87C14E5D0C8967BA9783BD2AB08A75EA9C3A305C45B13FD02"
)
SOURCE_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_council14_r691_e5c6b4d"
EXPECTED_INPUT_SHA256 = (
    "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800"
)
SAVE_SHA256 = (
    "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
)
R691_RED_REPORT_SHA256 = (
    "5E6CB7FD3C632EF17877E0165E0B8012345AF77B10B303D0E988416633D6D62F"
)
R691_WER_SHA256 = (
    "78FBF1762EA54990639F25C38D7D7A444A806A3D7B9BB1DE571E7D84039CEAE4"
)
R691_ARTIFACT_MANIFEST_SHA256 = (
    "67CBFD8EAF69177E7615F9B10682B56DF7F4F09E04D8FF6E5FC44CCE0CE5EA57"
)
HARNESS_PATHS = (
    "ck3_autonomous_player/native_bridge/research/council16_candidate_runtime_identity.py",
    "ck3_autonomous_player/native_bridge/research/council16_candidate_runtime_import_probe.py",
    "ck3_autonomous_player/native_bridge/research/prepare_council16_r692_sealed_candidate.py",
    "ck3_autonomous_player/native_bridge/research/test_council16_r692_sealed_candidate.py",
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
    """Advance the frozen R690/R691 pair without cascading replacements."""

    return (
        text.replace("R691", "__COUNCIL16_UPPER_NEW__")
        .replace("R690", "R691")
        .replace("__COUNCIL16_UPPER_NEW__", "R692")
        .replace("r691", "__council16_lower_new__")
        .replace("r690", "r691")
        .replace("__council16_lower_new__", "r692")
    )


def verify_source(source: Path) -> dict[str, Any]:
    sealed_path = source / "sealed-prep-manifest.json"
    if sha256(sealed_path) != SOURCE_SEALED_SHA256:
        raise RuntimeError("R691 source sealed manifest SHA-256 differs")
    sealed = load_json_object(
        sealed_path,
        expected_schema="xar.ck3.g2_m4_council14_r691_sealed_prep_v1",
    )
    if (
        sealed.get("status") != "sealed-no-launch"
        or sealed.get("source_commit") != SOURCE_BRIDGE_COMMIT
        or sealed.get("harness_commit") != SOURCE_HARNESS_COMMIT
        or sealed.get("candidate_manifest_sha256") != SOURCE_CANDIDATE_SHA256
        or sealed.get("suggested_round") != "R691"
        or sealed.get("round_allocated") is not False
        or sealed.get("ck3_launched") is not False
    ):
        raise RuntimeError("R691 source candidate identity differs")
    files = sealed.get("files")
    if not isinstance(files, list) or sealed.get("file_count") != len(files):
        raise RuntimeError("R691 source inventory differs")
    for row in files:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise RuntimeError("R691 source inventory row is invalid")
        path = (source / row["path"]).resolve()
        path.relative_to(source)
        if (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256(path) != row.get("sha256")
        ):
            raise RuntimeError(f"R691 sealed file differs: {row['path']}")
    verify_r691_red(source)
    return sealed


def verify_r691_red(source: Path) -> None:
    live = source / "live-r691"
    required = {
        "harness-red-report.json": R691_RED_REPORT_SHA256,
        "pythoncom313-appcrash.wer": R691_WER_SHA256,
        "artifact-manifest.json": R691_ARTIFACT_MANIFEST_SHA256,
    }
    for name, expected in required.items():
        path = live / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"R691 RED evidence differs: {name}")
    report = load_json_object(
        live / "harness-red-report.json",
        expected_schema="xar.ck3.g2_m4_council14_r691_harness_red_v1",
    )
    if (
        report.get("status") != "red"
        or report.get("failure_layer") != "harness"
        or report.get("attempted_round") != "R691"
        or report.get("next_new_round") != "R692"
        or report.get("ck3_process_started") is not False
        or report.get("ck3_pid") is not None
    ):
        raise RuntimeError("R691 RED report contract differs")
    manifest = load_json_object(
        live / "artifact-manifest.json",
        expected_schema=(
            "xar.ck3.g2_m4_council14_r691_harness_red_artifact_manifest_v1"
        ),
    )
    rows = manifest.get("files")
    if manifest.get("status") != "sealed-red" or not isinstance(rows, list):
        raise RuntimeError("R691 RED artifact manifest differs")
    for row in rows:
        path = (live / str(row["path"])).resolve()
        path.relative_to(live)
        if (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256(path) != row.get("sha256")
        ):
            raise RuntimeError(f"R691 RED artifact differs: {row['path']}")


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
        ("run_r691.py", "run_r692.py"),
        ("invoke_r691.py", "invoke_r692.py"),
        ("verify_prep.py", "verify_prep.py"),
    )
    for old_name, new_name in bindings:
        path = output / old_name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(SOURCE_PIPE, pipe)
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = advance_rounds(text)
        text = text.replace("COUNCIL14", "COUNCIL16")
        text = text.replace("council14", "council16")
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
) -> None:
    candidate_path = output / "candidate-manifest.json"
    candidate = load_json_object(candidate_path)
    candidate["schema"] = "xar.ck3.g2_m4_council16_r692_harness_candidate_v1"
    candidate["harness_commit"] = harness_commit
    candidate["runtime_source"] = source_identity
    candidate["driver_snapshot_api_contract"].update(
        {
            "baseline_commit": RUNTIME_SOURCE_COMMIT,
            "operator_workspace_preflight_required": False,
            "candidate_local_source_required": True,
            "module_file_and_sha_asserted": True,
        }
    )
    candidate["next_live"] = {
        "suggested_round": "R692",
        "unique_pipe": pipe,
        "paused_only": True,
        "publish_timeout_seconds": 20,
        "same_round_retry": False,
    }
    candidate["r691_harness_red"] = {
        "classification": "pythoncom_watchdog_bootstrap_harness_red",
        "report_sha256": R691_RED_REPORT_SHA256,
        "wer_sha256": R691_WER_SHA256,
        "artifact_manifest_sha256": R691_ARTIFACT_MANIFEST_SHA256,
        "ck3_process_started": False,
        "attempted_round_consumed": True,
        "same_candidate_retry_allowed": False,
    }
    candidate["pythoncom_launch_fix"] = {
        "integrated_commit": RUNTIME_SOURCE_COMMIT,
        "wmi_dispatch_proxies_released_before_co_uninitialize": True,
        "public_surface_changed": False,
    }
    write_json(candidate_path, candidate)

    environment_sha, environment_manifest_sha = patch_environment(source, output)
    for name in ("profile-preflight.json", "preflight.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = advance_rounds(str(payload["schema"])).replace(
            "council14", "council16"
        )
        payload["harness_commit"] = harness_commit
        payload["environment_sha256"] = environment_sha
        if name == "profile-preflight.json":
            payload["environment_manifest_sha256"] = environment_manifest_sha
        write_json(path, payload)

    ownership_path = output / "round-ownership-proposal.json"
    ownership = load_json_object(ownership_path)
    ownership.update(
        {
            "suggested_new_round": "R692",
            "allocated": False,
            "current": "R692 suggested; not allocated",
            "expected_old_round": "R691",
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
    validation["schema"] = "xar.ck3.g2_m4_council16_r692_validation_v1"
    validation["status"] = "static-ready-no-launch"
    validation["next_round"] = "R692"
    validation["ck3_launched"] = False
    validation["candidate_no_launch_preflight"] = "pending-one-shot"
    validation["r691_harness_red"] = candidate["r691_harness_red"]
    validation["pythoncom_launch_fix"] = {
        "integrated_commit": RUNTIME_SOURCE_COMMIT,
        "focused_normal": "4/4 passed",
        "focused_optimized": "4/4 passed",
        "real_non_ck3_wmi_create": "normal/optimized exit 0",
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
        payload["schema"] = "xar.ck3.g2_m4_council16_operator_runtime_v1"
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
        ("R691-start-checklist.md", "R692-start-checklist.md"),
    ):
        path = output / old_name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(str(source), str(output))
        text = text.replace(source.as_posix(), output.as_posix())
        text = text.replace(SOURCE_PIPE, pipe)
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = advance_rounds(text)
        text = text.replace("COUNCIL14", "COUNCIL16")
        text = text.replace("council14", "council16")
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
        "schema": "xar.ck3.g2_m4_council16_r692_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": SOURCE_BRIDGE_COMMIT,
        "harness_commit": harness_commit,
        "suggested_round": "R692",
        "expected_old_round": "R691",
        "round_allocated": False,
        "ck3_launched": False,
        "candidate_manifest_sha256": candidate_hash,
        "bridge_dll_sha256": sha256(output / "candidate-bin/xar_ck3_bridge.dll"),
        "source_save_sha256": sha256(output / "source-save/dev3b_r639.ck3"),
        "unique_pipe": pipe,
        "source_r691_sealed_manifest_sha256": SOURCE_SEALED_SHA256,
        "source_r691_red": {
            "report_sha256": R691_RED_REPORT_SHA256,
            "wer_sha256": R691_WER_SHA256,
            "artifact_manifest_sha256": R691_ARTIFACT_MANIFEST_SHA256,
        },
        "runtime_source": source_identity,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "fresh_state_contract": {
            "source_manifest_rows_only": True,
            "r691_live_copied": False,
            "r691_control_copied": False,
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
    source: Path, output: Path, harness_commit: str, repo_root: Path
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
    if not output.name.startswith("g2-m4-council16-r692-"):
        raise ValueError("output directory must use the COUNCIL16 R692 prefix")
    sealed = verify_source(source)
    tracked_paths = verify_runtime_repository(repo_root)
    pipe = rf"\\.\pipe\xar_ck3_bridge_g2_m4_council16_r692_{harness_commit[:7]}"
    copy_sealed_inputs(source, output, sealed["files"])
    try:
        source_identity = copy_runtime(repo_root, output, tracked_paths)
        shutil.copyfile(
            Path(__file__).with_name("council16_candidate_runtime_identity.py"),
            output / "candidate_runtime_identity.py",
        )
        shutil.copyfile(
            Path(__file__).with_name("council16_candidate_runtime_import_probe.py"),
            output / "candidate_runtime_import_probe.py",
        )
        patch_python_entrypoints(output, harness_commit, pipe)
        patch_metadata(source, output, harness_commit, pipe, source_identity)
        patch_text_bindings(source, output, harness_commit, pipe)
        if (output / "live-r691").exists() or (output / "live-r692").exists():
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
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args(argv)
    print(
        json.dumps(
            materialize(args.source, args.output, args.harness_commit, args.repo_root),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
