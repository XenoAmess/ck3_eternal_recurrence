"""Materialize a fresh hash-bound R690 candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from json_input_contract import load_json_object


SOURCE_SEALED_SHA256 = (
    "DA0DF733D815FD2191FF7DAAAF1670872DD985759F199A9FFD527C158E96242D"
)
SOURCE_CANDIDATE_SHA256 = (
    "C40AE642FFA40362772A1DEC94FFE300185E09A90DB48376E856578426E80C5C"
)
EXPECTED_INPUT_SHA256 = (
    "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800"
)
SOURCE_HARNESS_COMMIT = "5187ab805708b4e16676ef16583ca4db26704268"
SOURCE_COMMIT = "a04ee02a04a3a86bb685395270d8cd23359b8ba2"
OLD_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_council11_r690_5187ab8"
EXPECTED_INPUT_SCHEMA = "xar.ck3.g2_m4_council11_expected_steward_candidates_v1"
OLD_RED_REPORT_SHA256 = (
    "CE99DA6C7AF647A467764178D8B01B6E9E7951AB5903882A72AE1F161764D414"
)
OLD_RED_MANIFEST_SHA256 = (
    "74A6D2400D44445C8DC2334DC45B6BE104EE861BF3C98CE84336933C5A1E3108"
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


def verify_source(source: Path) -> dict[str, Any]:
    sealed_path = source / "sealed-prep-manifest.json"
    if sha256(sealed_path) != SOURCE_SEALED_SHA256:
        raise RuntimeError("source sealed-prep manifest SHA-256 differs")
    sealed = load_json_object(
        sealed_path,
        expected_schema="xar.ck3.g2_m4_council11_r690_sealed_prep_v1",
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
        if (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256(path) != row.get("sha256")
        ):
            raise RuntimeError(f"source sealed file differs: {row['path']}")
    expected = source / "expected-steward-candidates.json"
    if sha256(expected) != EXPECTED_INPUT_SHA256 or not expected.read_bytes().startswith(
        b"\xef\xbb\xbf"
    ):
        raise RuntimeError("source expected-candidates BOM fixture differs")
    load_json_object(expected, expected_schema=EXPECTED_INPUT_SCHEMA)
    old_live = source / "live-r689"
    if not old_live.is_dir() or any(old_live.iterdir()):
        raise RuntimeError("source empty live-r689 RED residue differs")
    return sealed


def copy_sealed_files(source: Path, output: Path, rows: list[dict[str, Any]]) -> None:
    output.mkdir(parents=True, exist_ok=False)
    try:
        for row in rows:
            relative = Path(row["path"])
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
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
    path = output / "run_r690.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "import sys\n",
        "import sys\n\nsys.dont_write_bytecode = True\n",
        label="runner bytecode anchor",
    )
    text = replace_required(
        text,
        "from typing import Any\n",
        "from typing import Any\n\nfrom json_input_contract import load_json_object\n",
        label="runner import anchor",
    )
    text = replace_required(
        text,
        'manifest = json.loads(manifest_path.read_text(encoding="utf-8"))',
        'manifest = load_json_object(\n        manifest_path,\n        expected_schema="xar.ck3.g2_m4_council12_r690_sealed_prep_v1",\n    )',
        label="sealed manifest JSON reader",
    )
    old_expected = '''expected_candidates = json.loads(
        (root / "expected-steward-candidates.json").read_text(encoding="utf-8")
    )["candidates"]'''
    new_expected = '''expected_candidates = load_json_object(
        root / "expected-steward-candidates.json",
        expected_schema="xar.ck3.g2_m4_council11_expected_steward_candidates_v1",
    )["candidates"]'''
    text = replace_required(
        text, old_expected, new_expected, label="expected-candidates JSON reader"
    )
    text = replace_required(
        text,
        'candidate = json.loads(candidate_manifest.read_text(encoding="utf-8"))',
        'candidate = load_json_object(\n            candidate_manifest,\n            expected_schema="xar.ck3.g2_m4_council12_r690_harness_candidate_v1",\n        )',
        label="candidate manifest JSON reader",
    )
    text = replace_required(text, 'artifacts = root / "live-r689"', 'artifacts = root / "live-r690"', label="fresh live directory")
    text = text.replace("COUNCIL11", "COUNCIL12")
    text = text.replace("g2_m4_council11_r689_live_v1", "g2_m4_council12_r690_live_v1")
    path.write_text(text, encoding="utf-8")


def patch_verifier(output: Path, harness_commit: str, pipe: str) -> None:
    path = output / "verify_prep.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "sys.dont_write_bytecode = True\n",
        "sys.dont_write_bytecode = True\n\nfrom json_input_contract import load_json_object\n",
        label="verifier import anchor",
    )
    text = replace_required(text, SOURCE_HARNESS_COMMIT, harness_commit, label="verifier harness commit")
    text = replace_required(text, OLD_PIPE, pipe, label="verifier pipe")
    text = text.replace("COUNCIL11", "COUNCIL12")
    text = text.replace("g2_m4_council11", "g2_m4_council12")
    replacements = {
        'manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))': 'manifest = load_json_object(\n        manifest_path,\n        expected_schema="xar.ck3.g2_m4_council12_r690_sealed_prep_v1",\n    )',
        '''candidate = json.loads(
        (ROOT / "candidate-manifest.json").read_text(encoding="utf-8-sig")
    )''': '''candidate = load_json_object(
        ROOT / "candidate-manifest.json",
        expected_schema="xar.ck3.g2_m4_council12_r690_harness_candidate_v1",
    )''',
        '''profile = json.loads(
        (ROOT / "profile-preflight.json").read_text(encoding="utf-8-sig")
    )''': '''profile = load_json_object(
        ROOT / "profile-preflight.json",
        expected_schema="xar.ck3.g2_m4_council12_r690_profile_preflight_v1",
    )''',
        '''ownership = json.loads(
        (ROOT / "round-ownership-proposal.json").read_text(encoding="utf-8-sig")
    )''': '''ownership = load_json_object(
        ROOT / "round-ownership-proposal.json",
        expected_schema="xar.ck3.round_ownership_proposal_v1",
    )''',
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, label="verifier JSON reader")
    bom_check = '''    expected_input = ROOT / "expected-steward-candidates.json"
    require(sha256(expected_input) == "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800", "expected input hash differs")
    require(expected_input.read_bytes().startswith(b"\\xef\\xbb\\xbf"), "expected input no longer carries the reproduced BOM")
    expected_payload = load_json_object(
        expected_input,
        expected_schema="xar.ck3.g2_m4_council11_expected_steward_candidates_v1",
    )
    require(len(expected_payload.get("candidates", [])) == 11, "expected candidate vector differs")
    require("live-r689" not in runner and 'live-r690' in runner, "runner output directory was not advanced")
    require("load_json_object(" in runner, "runner does not use the BOM-safe JSON contract")

'''
    text = replace_required(
        text,
        "    validator = load_validator()\n",
        bom_check + "    validator = load_validator()\n",
        label="verifier BOM contract anchor",
    )
    path.write_text(text, encoding="utf-8")


def patch_invoke(output: Path, pipe: str) -> None:
    path = output / "invoke_r690.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "import subprocess\n",
        "import subprocess\nimport sys\n\nsys.dont_write_bytecode = True\n",
        label="invoke import anchor",
    )
    text = replace_required(
        text,
        "from pathlib import Path\n",
        "from pathlib import Path\n\nfrom json_input_contract import load_json_object\n",
        label="invoke contract import anchor",
    )
    text = replace_required(
        text,
        'config = json.loads(config_path.read_text(encoding="utf-8-sig"))',
        'config = load_json_object(\n        config_path,\n        expected_schema="xar.ck3.g2_m4_council12_operator_runtime_v1",\n    )',
        label="operator config JSON reader",
    )
    text = replace_required(text, OLD_PIPE, pipe, label="invoke pipe")
    text = text.replace("g2_m4_council11", "g2_m4_council12")
    text = replace_required(
        text,
        '''    command = [
        str(python),
        str(root / "run_r690.py"),''',
        '''    command = [
        str(python),
        "-B",
        str(root / "run_r690.py"),''',
        label="runner no-bytecode launch",
    )
    path.write_text(text, encoding="utf-8")


def patch_metadata(source: Path, output: Path, harness_commit: str, pipe: str) -> None:
    candidate_path = output / "candidate-manifest.json"
    candidate = load_json_object(candidate_path)
    candidate["schema"] = "xar.ck3.g2_m4_council12_r690_harness_candidate_v1"
    candidate["harness_commit"] = harness_commit
    candidate["json_input_contract"] = {
        "loader": "json_input_contract.load_json_object",
        "encoding": "utf-8-sig",
        "accepts": ["utf-8", "utf-8-bom"],
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "legacy_failure_reproduced": True,
    }
    candidate["next_live"]["unique_pipe"] = pipe
    write_json(candidate_path, candidate)

    environment_sha, environment_manifest_sha = patch_environment(source, output)
    for name in ("profile-preflight.json", "preflight.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = str(payload["schema"]).replace(
            "g2_m4_council11", "g2_m4_council12"
        )
        payload["harness_commit"] = harness_commit
        payload["environment_sha256"] = environment_sha
        if name == "profile-preflight.json":
            payload["environment_manifest_sha256"] = environment_manifest_sha
        write_json(path, payload)

    ownership_path = output / "round-ownership-proposal.json"
    ownership = load_json_object(ownership_path)
    ownership["candidate_revision"] = harness_commit
    ownership["pipe"] = pipe
    write_json(ownership_path, ownership)

    validation_path = output / "validation-results.json"
    validation = load_json_object(validation_path)
    validation["schema"] = "xar.ck3.g2_m4_council12_r690_validation_v1"
    validation["r690_prelaunch_red"] = {
        "classification": "harness_prelaunch_json_bom",
        "report_sha256": OLD_RED_REPORT_SHA256,
        "artifact_manifest_sha256": OLD_RED_MANIFEST_SHA256,
        "ck3_launched": False,
        "failure": "JSONDecodeError: Unexpected UTF-8 BOM",
    }
    validation["bom_safe_json_contract"] = {
        "normal": "pending",
        "optimized": "pending",
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
    }
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
        "R690-start-checklist.md",
    ):
        path = output / name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(str(source), str(output))
        text = text.replace(source.as_posix(), output.as_posix())
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = text.replace(OLD_PIPE, pipe)
        text = text.replace("COUNCIL11", "COUNCIL12")
        path.write_text(text, encoding="utf-8")

    for name in ("operator-runtime.json", "operator-runtime.example.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = "xar.ck3.g2_m4_council12_operator_runtime_v1"
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
        "schema": "xar.ck3.g2_m4_council12_r690_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": SOURCE_COMMIT,
        "harness_commit": harness_commit,
        "suggested_round": "R690",
        "round_allocated": False,
        "ck3_launched": False,
        "candidate_manifest_sha256": candidate_hash,
        "bridge_dll_sha256": sha256(output / "candidate-bin/xar_ck3_bridge.dll"),
        "source_save_sha256": sha256(output / "source-save/dev3b_r639.ck3"),
        "unique_pipe": pipe,
        "source_sealed_manifest_sha256": SOURCE_SEALED_SHA256,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "json_input_contract": "json_input_contract.load_json_object:utf-8-sig",
        "prelaunch_red": {
            "report_sha256": OLD_RED_REPORT_SHA256,
            "artifact_manifest_sha256": OLD_RED_MANIFEST_SHA256,
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


def materialize(source: Path, output: Path, harness_commit: str) -> dict[str, str]:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    if not re.fullmatch(r"[0-9a-f]{40}", harness_commit):
        raise ValueError("harness commit must be a lowercase full Git hash")
    sealed = verify_source(source)
    expected_name_suffix = harness_commit[:7]
    if expected_name_suffix not in output.name:
        raise ValueError("output directory must include the harness short hash")
    pipe = rf"\\.\pipe\xar_ck3_bridge_g2_m4_council12_r690_{expected_name_suffix}"
    rows = sealed["files"]
    copy_sealed_files(source, output, rows)
    try:
        loader_source = Path(__file__).with_name("json_input_contract.py")
        shutil.copyfile(loader_source, output / "json_input_contract.py")
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--harness-commit", required=True)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            materialize(args.source, args.output, args.harness_commit),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
