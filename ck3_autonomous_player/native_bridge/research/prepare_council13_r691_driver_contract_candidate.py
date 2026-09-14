"""Materialize a fresh hash-bound R691 candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from json_input_contract import load_json_object
from validate_private_probe_readiness_contract import validate_runner_contract


SOURCE_SEALED_SHA256 = (
    "93B680E80CE8B62E2D402E8CB9F391A282D123873A0B5F106AA359261DB68E8B"
)
SOURCE_CANDIDATE_SHA256 = (
    "5C59E143A63FFC1699A17E9F2E8CA7630019279CDF361E8FD226783ECC962DC5"
)
EXPECTED_INPUT_SHA256 = (
    "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800"
)
SOURCE_HARNESS_COMMIT = "1669785837dbee660f58d8b46fbe48ccfd86a240"
SOURCE_COMMIT = "a04ee02a04a3a86bb685395270d8cd23359b8ba2"
OLD_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_council12_r690_1669785"
EXPECTED_INPUT_SCHEMA = "xar.ck3.g2_m4_council11_expected_steward_candidates_v1"
OLD_RED_REPORT_SHA256 = (
    "E2D562A9BC88BFEA1752AAE55473B1148824B019917138FB3BF1B34D55C82F50"
)
RECOVERY_SEALED_SHA256 = (
    "DA0DF733D815FD2191FF7DAAAF1670872DD985759F199A9FFD527C158E96242D"
)
RECOVERY_PATH = "fresh-profile-state/profile/pdx_settings.txt"
RECOVERY_SHA256 = "52BF916EC3F1CD2ACC14618743F26202302F5EBE74ACD993E773F85897449C5B"
DRIVER_API_INTRODUCED_COMMIT = "79b8d2acfbe1f80a7a7f88da3fed7cda1791017c"
SAVE_SHA256 = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
BASELINE_COMMIT = "a905af184798439a41cdc6f63bfeb47d67f62608"


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


def snapshot_digest(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def environment_digest(environment: dict[str, Any]) -> str:
    stable = json.loads(json.dumps(environment, ensure_ascii=False))
    stable.pop("prepared_at", None)
    stable.pop("environment_sha256", None)
    tutorial = stable.get("persistent_tutorial_state")
    if isinstance(tutorial, dict):
        tutorial.pop("initialized_this_prepare", None)
    return snapshot_digest(stable)


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count == 0:
        raise RuntimeError(f"required {label} token is missing")
    return text.replace(old, new)


def verify_source(source: Path, recovery_source: Path) -> dict[str, Any]:
    sealed_path = source / "sealed-prep-manifest.json"
    if sha256(sealed_path) != SOURCE_SEALED_SHA256:
        raise RuntimeError("source sealed-prep manifest SHA-256 differs")
    sealed = load_json_object(
        sealed_path,
        expected_schema="xar.ck3.g2_m4_council12_r690_sealed_prep_v1",
    )
    if (
        sealed.get("status") != "sealed-no-launch"
        or sealed.get("source_commit") != SOURCE_COMMIT
        or sealed.get("harness_commit") != SOURCE_HARNESS_COMMIT
        or sealed.get("candidate_manifest_sha256") != SOURCE_CANDIDATE_SHA256
    ):
        raise RuntimeError("source candidate identity differs")
    files = sealed.get("files")
    if not isinstance(files, list) or sealed.get("file_count") != len(files):
        raise RuntimeError("source sealed file inventory differs")
    for row in files:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise RuntimeError("source sealed inventory contains an invalid row")
        path = (source / row["path"]).resolve()
        path.relative_to(source)
        matches = (
            path.is_file()
            and path.stat().st_size == row.get("size_bytes")
            and sha256(path) == row.get("sha256")
        )
        if not matches and row["path"] != RECOVERY_PATH:
            raise RuntimeError(f"source sealed file differs: {row['path']}")
    expected = source / "expected-steward-candidates.json"
    if sha256(expected) != EXPECTED_INPUT_SHA256 or not expected.read_bytes().startswith(
        b"\xef\xbb\xbf"
    ):
        raise RuntimeError("source expected-candidates BOM fixture differs")
    load_json_object(expected, expected_schema=EXPECTED_INPUT_SCHEMA)
    report_path = source / "live-r690" / "report.json"
    if sha256(report_path) != OLD_RED_REPORT_SHA256:
        raise RuntimeError("source R690 RED report SHA-256 differs")
    report = load_json_object(
        report_path, expected_schema="xar.ck3.g2_m4_council12_r690_live_v1"
    )
    if (
        report.get("status") != "red"
        or report.get("ok") is not False
        or report.get("red", {}).get("reason")
        != "AttributeError: 'NativeHeadlessGameplayDriver' object has no attribute 'take_internal_semantic_snapshot'"
        or report.get("cleanup", {}).get("cleanup_proven") is not True
        or report.get("cleanup", {}).get("tree_gone") is not True
        or report.get("source_save_unchanged") is not True
        or report.get("target_save_unchanged") is not True
        or report.get("source_save_after_sha256") != SAVE_SHA256
        or report.get("target_save_after_sha256") != SAVE_SHA256
    ):
        raise RuntimeError("source R690 RED evidence differs")

    recovery_manifest = recovery_source / "sealed-prep-manifest.json"
    if sha256(recovery_manifest) != RECOVERY_SEALED_SHA256:
        raise RuntimeError("recovery sealed-prep manifest SHA-256 differs")
    recovery_row = next(
        (row for row in files if row.get("path") == RECOVERY_PATH), None
    )
    recovery_file = recovery_source / RECOVERY_PATH
    if (
        recovery_row is None
        or recovery_row.get("sha256") != RECOVERY_SHA256
        or not recovery_file.is_file()
        or sha256(recovery_file) != RECOVERY_SHA256
    ):
        raise RuntimeError("clean recovery file differs")
    return sealed


def copy_sealed_files(
    source: Path,
    recovery_source: Path,
    output: Path,
    rows: list[dict[str, Any]],
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    try:
        for row in rows:
            relative = Path(row["path"])
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            origin = recovery_source / relative if row["path"] == RECOVERY_PATH else source / relative
            shutil.copyfile(origin, target)
            if (
                target.stat().st_size != row["size_bytes"]
                or sha256(target) != row["sha256"]
            ):
                raise RuntimeError(f"copied sealed file differs: {row['path']}")
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def patch_environment(source: Path, output: Path) -> tuple[str, str]:
    descriptor_path = output / "fresh-profile-state/profile/mod/xar_autoplayer.mod"
    descriptor = descriptor_path.read_text(encoding="utf-8-sig")
    descriptor = replace_required(
        descriptor,
        source.as_posix(),
        output.as_posix(),
        label="profile descriptor candidate root",
    )
    descriptor_path.write_text(descriptor, encoding="utf-8")

    environment_path = output / "fresh-profile-state/profile/xar-autoplayer-environment.json"
    environment = load_json_object(environment_path)
    old_root = str(source)
    new_root = str(output)

    def relocate(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(old_root, new_root)
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
        raise RuntimeError("environment load_profile is absent")
    load_profile["outer_descriptor_sha256"] = sha256(descriptor_path).lower()
    environment["environment_sha256"] = environment_digest(environment)
    write_json(environment_path, environment)
    return str(environment["environment_sha256"]), sha256(environment_path)


def patch_runner(output: Path) -> None:
    path = output / "run_r691.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        'artifacts = root / "live-r690"',
        'artifacts = root / "live-r691"',
        label="fresh live directory",
    )
    for old, new in (
        ("COUNCIL12", "COUNCIL13"),
        ("g2_m4_council12", "g2_m4_council13"),
        ("R690", "R691"),
        ("r690", "r691"),
    ):
        text = text.replace(old, new)
    if "driver.take_internal_semantic_snapshot()" not in text:
        raise RuntimeError("runner paused semantic snapshot call differs")
    path.write_text(text, encoding="utf-8")


def patch_verifier(output: Path, harness_commit: str, pipe: str) -> None:
    path = output / "verify_prep.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(text, SOURCE_HARNESS_COMMIT, harness_commit, label="verifier harness commit")
    text = replace_required(text, OLD_PIPE, pipe, label="verifier pipe")
    for old, new in (
        ("COUNCIL12", "COUNCIL13"),
        ("g2_m4_council12", "g2_m4_council13"),
        ("R690", "R691"),
        ("r690", "r691"),
    ):
        text = text.replace(old, new)
    text = replace_required(
        text,
        'ownership.get("expected_old_round") == "R689"',
        'ownership.get("expected_old_round") == "R690"',
        label="verifier actual old round",
    )
    text = replace_required(
        text,
        '    readiness_path = source_root / "xar_autoplayer" / "native_auto_run.py"\n'
        '    require(readiness_path.is_file(), "runtime readiness source is missing")\n',
        '    readiness_path = source_root / "xar_autoplayer" / "native_auto_run.py"\n'
        '    driver_path = source_root / "xar_autoplayer" / "bridge" / "native_driver.py"\n'
        '    require(readiness_path.is_file(), "runtime readiness source is missing")\n'
        '    require(driver_path.is_file(), "runtime native driver source is missing")\n',
        label="operator driver source binding",
    )
    text = replace_required(
        text,
        "        readiness_source=readiness_path.read_text(encoding=\"utf-8-sig\"),\n"
        "        runner_source=runner,\n",
        "        readiness_source=readiness_path.read_text(encoding=\"utf-8-sig\"),\n"
        "        driver_source=driver_path.read_text(encoding=\"utf-8-sig\"),\n"
        "        runner_source=runner,\n",
        label="operator driver API validation",
    )
    path.write_text(text, encoding="utf-8")


def patch_invoke(output: Path, pipe: str) -> None:
    path = output / "invoke_r691.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(text, OLD_PIPE, pipe, label="invoke pipe")
    for old, new in (
        ("COUNCIL12", "COUNCIL13"),
        ("g2_m4_council12", "g2_m4_council13"),
        ("R690", "R691"),
        ("r690", "r691"),
    ):
        text = text.replace(old, new)
    text = replace_required(
        text,
        '''    if args.preflight_only:
        return subprocess.run(
            [
                str(python),
                *optimization,
                "-B",
                str(root / "verify_prep.py"),
                "--workspace-root",
                str(workspace),
            ],
            cwd=root,
            check=False,
        ).returncode
    command = [''',
        '''    preflight_returncode = subprocess.run(
        [
            str(python),
            *optimization,
            "-B",
            str(root / "verify_prep.py"),
            "--workspace-root",
            str(workspace),
        ],
        cwd=root,
        check=False,
    ).returncode
    if preflight_returncode != 0 or args.preflight_only:
        return preflight_returncode
    command = [''',
        label="mandatory prelaunch verifier",
    )
    text = replace_required(
        text,
        '        "--old-round",\n        "R689",\n',
        '        "--old-round",\n        "R690",\n',
        label="actual old round",
    )
    path.write_text(text, encoding="utf-8")


def patch_metadata(source: Path, output: Path, harness_commit: str, pipe: str) -> None:
    candidate_path = output / "candidate-manifest.json"
    candidate = load_json_object(candidate_path)
    candidate["schema"] = "xar.ck3.g2_m4_council13_r691_harness_candidate_v1"
    candidate["harness_commit"] = harness_commit
    repo_root = Path(__file__).resolve().parents[3]
    source_root = repo_root / "ck3_autonomous_player" / "src"
    contract = validate_runner_contract(
        readiness_source=(source_root / "xar_autoplayer" / "native_auto_run.py").read_text(
            encoding="utf-8-sig"
        ),
        driver_source=(
            source_root / "xar_autoplayer" / "bridge" / "native_driver.py"
        ).read_text(encoding="utf-8-sig"),
        runner_source=(output / "run_r691.py").read_text(encoding="utf-8-sig"),
        expected_character_id=29829,
    )
    for key in ("readiness_call_line", "snapshot_line", "character_check_line"):
        contract.pop(key, None)
    candidate["readiness_call_contract"] = contract
    candidate["driver_snapshot_api_contract"] = {
        **contract["driver_snapshot_api"],
        "baseline_commit": BASELINE_COMMIT,
        "introduced_commit": DRIVER_API_INTRODUCED_COMMIT,
        "operator_workspace_preflight_required": True,
        "live_invoke_runs_preflight_first": True,
    }
    candidate["next_live"]["unique_pipe"] = pipe
    candidate["next_live"]["suggested_round"] = "R691"
    candidate["r690_runtime_red"] = {
        "classification": "harness_driver_api_mismatch",
        "report_sha256": OLD_RED_REPORT_SHA256,
        "ck3_launched": True,
        "cleanup_proven": True,
        "source_save_unchanged": True,
        "target_save_unchanged": True,
        "failure": "AttributeError: missing take_internal_semantic_snapshot",
    }
    write_json(candidate_path, candidate)

    environment_sha, environment_manifest_sha = patch_environment(source, output)
    for name in ("profile-preflight.json", "preflight.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = (
            str(payload["schema"])
            .replace("g2_m4_council12", "g2_m4_council13")
            .replace("r690", "r691")
        )
        payload["harness_commit"] = harness_commit
        payload["environment_sha256"] = environment_sha
        if name == "profile-preflight.json":
            payload["environment_manifest_sha256"] = environment_manifest_sha
        write_json(path, payload)

    ownership_path = output / "round-ownership-proposal.json"
    ownership = load_json_object(ownership_path)
    ownership["suggested_new_round"] = "R691"
    ownership["current"] = "R691 suggested; not allocated"
    ownership["expected_old_round"] = "R690"
    ownership["candidate_revision"] = harness_commit
    ownership["pipe"] = pipe
    write_json(ownership_path, ownership)

    validation_path = output / "validation-results.json"
    validation = load_json_object(validation_path)
    validation["schema"] = "xar.ck3.g2_m4_council13_r691_validation_v1"
    validation["r690_runtime_red"] = {
        "classification": "harness_driver_api_mismatch",
        "report_sha256": OLD_RED_REPORT_SHA256,
        "ck3_launched": True,
        "cleanup_proven": True,
        "saves_unchanged": True,
        "failure": "AttributeError: missing take_internal_semantic_snapshot",
    }
    validation["driver_snapshot_api_contract"] = {
        "normal": "5/5 passed",
        "optimized": "5/5 passed",
        "missing_api_rejected": True,
        "wrong_call_shape_rejected": True,
        "public_snapshot_substitution_rejected": True,
        "operator_workspace_preflight_required": True,
    }
    validation["candidate_no_launch_preflight"] = "pending"
    validation["next_round"] = "R691"
    validation["ck3_launched"] = False
    write_json(validation_path, validation)

    candidate_hash = sha256(candidate_path)
    preflight_path = output / "preflight.json"
    preflight = load_json_object(preflight_path)
    preflight["candidate_manifest_sha256"] = candidate_hash
    write_json(preflight_path, preflight)


def patch_text_bindings(source: Path, output: Path, harness_commit: str, pipe: str) -> None:
    for name in (
        "execute-command.txt",
        "preflight-command.txt",
        "R691-start-checklist.md",
    ):
        path = output / name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(str(source), str(output))
        text = text.replace(source.as_posix(), output.as_posix())
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = text.replace(OLD_PIPE, pipe)
        for old, new in (
            ("COUNCIL12", "COUNCIL13"),
            ("g2_m4_council12", "g2_m4_council13"),
            ("R690", "R691"),
            ("r690", "r691"),
            ("R689", "R690"),
        ):
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    for name in ("operator-runtime.json", "operator-runtime.example.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = "xar.ck3.g2_m4_council13_operator_runtime_v1"
        write_json(path, payload)


def seal(output: Path, harness_commit: str, pipe: str) -> tuple[str, str]:
    candidate_hash = sha256(output / "candidate-manifest.json")
    rows = []
    excluded = {"sealed-prep-manifest.json", "sealed-prep-manifest.sha256"}
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
        "schema": "xar.ck3.g2_m4_council13_r691_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": SOURCE_COMMIT,
        "harness_commit": harness_commit,
        "suggested_round": "R691",
        "round_allocated": False,
        "ck3_launched": False,
        "candidate_manifest_sha256": candidate_hash,
        "bridge_dll_sha256": sha256(output / "candidate-bin/xar_ck3_bridge.dll"),
        "source_save_sha256": sha256(output / "source-save/dev3b_r639.ck3"),
        "unique_pipe": pipe,
        "source_sealed_manifest_sha256": SOURCE_SEALED_SHA256,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "json_input_contract": "json_input_contract.load_json_object:utf-8-sig",
        "runtime_red": {
            "report_sha256": OLD_RED_REPORT_SHA256,
            "failure": "AttributeError: missing take_internal_semantic_snapshot",
            "cleanup_proven": True,
            "saves_unchanged": True,
        },
        "recovered_sealed_file": {
            "path": RECOVERY_PATH,
            "sha256": RECOVERY_SHA256,
            "recovery_source_sealed_manifest_sha256": RECOVERY_SEALED_SHA256,
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
    recovery_source: Path,
    output: Path,
    harness_commit: str,
) -> dict[str, str]:
    source = source.expanduser().resolve()
    recovery_source = recovery_source.expanduser().resolve()
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    if not re.fullmatch(r"[0-9a-f]{40}", harness_commit):
        raise ValueError("harness commit must be a lowercase full Git hash")
    sealed = verify_source(source, recovery_source)
    expected_name_suffix = harness_commit[:7]
    if expected_name_suffix not in output.name:
        raise ValueError("output directory must include the harness short hash")
    pipe = rf"\\.\pipe\xar_ck3_bridge_g2_m4_council13_r691_{expected_name_suffix}"
    rows = sealed["files"]
    copy_sealed_files(source, recovery_source, output, rows)
    try:
        for old_name, new_name in (
            ("run_r690.py", "run_r691.py"),
            ("invoke_r690.py", "invoke_r691.py"),
            ("R690-start-checklist.md", "R691-start-checklist.md"),
        ):
            (output / old_name).rename(output / new_name)
        loader_source = Path(__file__).with_name("json_input_contract.py")
        shutil.copyfile(loader_source, output / "json_input_contract.py")
        validator_source = Path(__file__).with_name(
            "validate_private_probe_readiness_contract.py"
        )
        shutil.copyfile(
            validator_source,
            output / "validate_private_probe_readiness_contract.py",
        )
        patch_runner(output)
        patch_verifier(output, harness_commit, pipe)
        patch_invoke(output, pipe)
        patch_metadata(source, output, harness_commit, pipe)
        patch_text_bindings(source, output, harness_commit, pipe)
        candidate_hash, sealed_hash = seal(output, harness_commit, pipe)
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return {
        "output": str(output),
        "harness_commit": harness_commit,
        "candidate_manifest_sha256": candidate_hash,
        "sealed_prep_manifest_sha256": sealed_hash,
        "unique_pipe": pipe,
        "ck3_launched": "false",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--recovery-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--harness-commit", required=True)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            materialize(
                args.source,
                args.recovery_source,
                args.output,
                args.harness_commit,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
