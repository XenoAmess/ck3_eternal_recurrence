"""Materialize a self-contained, hash-bound R691 candidate without CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from candidate_runtime_identity import (
    BUILD_RELEASE_GIT_BLOB_OID,
    SOURCE_COMMIT as RUNTIME_SOURCE_COMMIT,
    SOURCE_ROOT_RELATIVE,
    SOURCE_TREE_GIT_OID,
    build_source_identity,
)
from json_input_contract import load_json_object


SOURCE_SEALED_SHA256 = (
    "0EA046F6522947285C82802B45E393610AC797C9492A43BAC5927C05691EA4B6"
)
SOURCE_CANDIDATE_SHA256 = (
    "58511E7D4DE30A144412281C371724D2797D1A8B3EF85ECC274D3A076F53B59C"
)
SOURCE_HARNESS_COMMIT = "37bd888cdfc654f239dbf8f59194fb590e4b2c24"
SOURCE_PRODUCT_COMMIT = "a04ee02a04a3a86bb685395270d8cd23359b8ba2"
OLD_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_council13_r691_37bd888"
EXPECTED_INPUT_SHA256 = (
    "B3D477590BCC46C6E7B6DCB90967278C13EA385A081AFC0C7612D817E9EEA800"
)
R690_RED_SHA256 = (
    "E2D562A9BC88BFEA1752AAE55473B1148824B019917138FB3BF1B34D55C82F50"
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


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"required {label} token count differs")
    return text.replace(old, new)


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


def verify_source(source: Path) -> dict[str, Any]:
    sealed_path = source / "sealed-prep-manifest.json"
    if sha256(sealed_path) != SOURCE_SEALED_SHA256:
        raise RuntimeError("COUNCIL13 source sealed manifest SHA-256 differs")
    sealed = load_json_object(
        sealed_path,
        expected_schema="xar.ck3.g2_m4_council13_r691_sealed_prep_v1",
    )
    if (
        sealed.get("status") != "sealed-no-launch"
        or sealed.get("source_commit") != SOURCE_PRODUCT_COMMIT
        or sealed.get("harness_commit") != SOURCE_HARNESS_COMMIT
        or sealed.get("candidate_manifest_sha256") != SOURCE_CANDIDATE_SHA256
        or sealed.get("round_allocated") is not False
        or sealed.get("ck3_launched") is not False
    ):
        raise RuntimeError("COUNCIL13 source candidate identity differs")
    files = sealed.get("files")
    if not isinstance(files, list) or sealed.get("file_count") != len(files):
        raise RuntimeError("COUNCIL13 source inventory differs")
    for row in files:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise RuntimeError("COUNCIL13 source inventory row is invalid")
        path = (source / row["path"]).resolve()
        path.relative_to(source)
        if (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256(path) != row.get("sha256")
        ):
            raise RuntimeError(f"COUNCIL13 sealed file differs: {row['path']}")
    if (source / "live-r691").exists():
        raise RuntimeError("COUNCIL13 source candidate allocated R691")
    return sealed


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
    changed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            RUNTIME_SOURCE_COMMIT,
            "--",
            "ck3_autonomous_player/src",
            "tools/build_release.py",
        ],
        cwd=repo_root,
        check=False,
    )
    if changed.returncode != 0:
        raise RuntimeError("runtime source working tree differs from frozen commit")
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


def copy_candidate(source: Path, output: Path, rows: list[dict[str, Any]]) -> None:
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
    for relative in paths:
        target = output / "source-repo" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / relative, target)
    identity = build_source_identity(output / "source-repo")
    write_json(output / "source-repo/source-identity.json", identity)
    return identity


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


def patch_runner(output: Path) -> None:
    path = output / "run_r691.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "from json_input_contract import load_json_object\n",
        "from candidate_runtime_identity import (\n"
        "    assert_imported_module,\n"
        "    verify_candidate_source,\n"
        ")\n"
        "from json_input_contract import load_json_object\n",
        label="runner identity import",
    )
    text = replace_required(
        text,
        '    result.add_argument("--workspace-root", type=Path, required=True)\n',
        "",
        label="external workspace argument",
    )
    old = '''    workspace = args.workspace_root.expanduser().resolve()
    source_root = workspace / "ck3_autonomous_player" / "src"
    if not source_root.is_dir():
        raise RuntimeError(f"autoplayer source root does not exist: {source_root}")
    sys.path.insert(0, str(source_root))

    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked
'''
    new = '''    source_root, source_identity = verify_candidate_source(root)
    sys.path.insert(0, str(source_root))

    import xar_autoplayer.bridge.native_driver as native_driver_module
    import xar_autoplayer.environment as environment_module
    import xar_autoplayer.native_auto_run as native_auto_run_module
    import xar_autoplayer.runtime as runtime_module
    import build_release

    for module in (
        build_release,
        native_driver_module,
        environment_module,
        native_auto_run_module,
        runtime_module,
    ):
        assert_imported_module(
            module,
            expected_name=module.__name__,
            source_root=source_root,
            identity=source_identity,
        )
    NativeHeadlessGameplayDriver = native_driver_module.NativeHeadlessGameplayDriver
    ck3_process_inventory = environment_module.ck3_process_inventory
    make_spec = environment_module.make_spec
    _wait_for_readiness = native_auto_run_module._wait_for_readiness
    NativeBridgeLaunchConfig = runtime_module.NativeBridgeLaunchConfig
    launch = runtime_module.launch
    stop_tracked = runtime_module.stop_tracked
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
'''
    text = replace_required(text, old, new, label="candidate-local imports")
    text = replace_required(
        text,
        '            "ck3_inventory": pre_inventory,\n',
        '            "ck3_inventory": pre_inventory,\n'
        '            "runtime_source_commit": source_identity["source_commit"],\n'
        '            "runtime_source_tree_sha256": source_identity["source_tree_sha256"],\n',
        label="live runtime source binding",
    )
    text = text.replace("COUNCIL13", "COUNCIL14")
    text = text.replace("g2_m4_council13", "g2_m4_council14")
    path.write_text(text, encoding="utf-8")


def patch_verifier(output: Path, harness_commit: str, pipe: str) -> None:
    path = output / "verify_prep.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "from json_input_contract import load_json_object\n",
        "from candidate_runtime_identity import (\n"
        "    assert_imported_module,\n"
        "    verify_candidate_source,\n"
        ")\n"
        "from json_input_contract import load_json_object\n",
        label="verifier identity import",
    )
    text = replace_required(text, SOURCE_HARNESS_COMMIT, harness_commit, label="harness commit")
    text = replace_required(text, OLD_PIPE, pipe, label="pipe")
    text = replace_required(
        text,
        '    parser.add_argument("--workspace-root", type=Path, required=True)\n'
        "    args = parser.parse_args(argv)\n"
        "    workspace = args.workspace_root.expanduser().resolve()\n"
        '    source_root = workspace / "ck3_autonomous_player" / "src"\n'
        '    readiness_path = source_root / "xar_autoplayer" / "native_auto_run.py"\n'
        '    driver_path = source_root / "xar_autoplayer" / "bridge" / "native_driver.py"\n'
        '    require(readiness_path.is_file(), "runtime readiness source is missing")\n'
        '    require(driver_path.is_file(), "runtime native driver source is missing")\n',
        "    parser.parse_args(argv)\n"
        "    source_root, source_identity = verify_candidate_source(ROOT)\n"
        '    readiness_path = source_root / "xar_autoplayer" / "native_auto_run.py"\n'
        '    driver_path = source_root / "xar_autoplayer" / "bridge" / "native_driver.py"\n',
        label="verifier candidate source",
    )
    text = replace_required(
        text,
        '    require(candidate.get("harness_commit") == HARNESS_COMMIT, "candidate harness differs")\n',
        '    require(candidate.get("harness_commit") == HARNESS_COMMIT, "candidate harness differs")\n'
        '    require(candidate.get("runtime_source") == source_identity, "candidate runtime source differs")\n',
        label="candidate runtime identity",
    )
    old_import = '''    sys.path.insert(0, str(source_root))
    from xar_autoplayer.environment import ck3_process_inventory

    inventory = ck3_process_inventory()
'''
    new_import = '''    sys.path.insert(0, str(source_root))
    import xar_autoplayer.bridge.native_driver as native_driver_module
    import xar_autoplayer.environment as environment_module
    import xar_autoplayer.native_auto_run as native_auto_run_module
    import xar_autoplayer.runtime as runtime_module
    import build_release

    for module in (
        build_release,
        native_driver_module,
        environment_module,
        native_auto_run_module,
        runtime_module,
    ):
        assert_imported_module(
            module,
            expected_name=module.__name__,
            source_root=source_root,
            identity=source_identity,
        )
    inventory = environment_module.ck3_process_inventory()
'''
    text = replace_required(text, old_import, new_import, label="verifier module origins")
    text = replace_required(
        text,
        '                "ck3_launched": False,\n',
        '                "ck3_launched": False,\n'
        '                "runtime_source_commit": source_identity["source_commit"],\n'
        '                "runtime_source_tree_sha256": source_identity["source_tree_sha256"],\n',
        label="preflight result source identity",
    )
    text = text.replace("COUNCIL13", "COUNCIL14")
    text = text.replace("g2_m4_council13", "g2_m4_council14")
    path.write_text(text, encoding="utf-8")


def patch_invoke(output: Path, pipe: str) -> None:
    path = output / "invoke_r691.py"
    text = path.read_text(encoding="utf-8-sig")
    text = replace_required(
        text,
        "from json_input_contract import load_json_object\n",
        "from candidate_runtime_identity import (\n"
        "    isolated_import_probe_command,\n"
        "    verify_candidate_source,\n"
        ")\n"
        "from json_input_contract import load_json_object\n",
        label="invoke identity import",
    )
    text = replace_required(text, OLD_PIPE, pipe, label="invoke pipe")
    text = replace_required(
        text,
        '    workspace = resolve(str(config["workspace_root"]))\n',
        "",
        label="invoke external workspace",
    )
    text = replace_required(
        text,
        "    root = Path(__file__).resolve().parent\n"
        "    required = (\n"
        "        python,\n"
        '        workspace / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "runtime.py",\n'
        '        game / "binaries" / "ck3.exe",\n'
        "    )\n",
        "    root = Path(__file__).resolve().parent\n"
        "    verify_candidate_source(root)\n"
        "    required = (python, game / \"binaries\" / \"ck3.exe\")\n",
        label="invoke required runtime",
    )
    text = replace_required(
        text,
        "    dependency_probe = subprocess.run(\n",
        "    isolated_environment = os.environ.copy()\n"
        '    isolated_environment.pop("PYTHONPATH", None)\n'
        '    isolated_environment.pop("PYTHONHOME", None)\n'
        "    import_probe = subprocess.run(\n"
        "        isolated_import_probe_command(\n"
        "            python, root, optimized=not __debug__\n"
        "        ),\n"
        "        cwd=root,\n"
        "        env=isolated_environment,\n"
        "        check=False,\n"
        "        timeout=60,\n"
        "    )\n"
        "    if import_probe.returncode != 0:\n"
        "        return import_probe.returncode\n"
        "    dependency_probe = subprocess.run(\n",
        label="isolated import preflight",
    )
    text = text.replace('            "--workspace-root",\n            str(workspace),\n', "")
    text = text.replace('        "--workspace-root",\n        str(workspace),\n', "")
    if "workspace" in text:
        raise RuntimeError("invoke still contains an external workspace")
    text = text.replace("COUNCIL13", "COUNCIL14")
    text = text.replace("g2_m4_council13", "g2_m4_council14")
    path.write_text(text, encoding="utf-8")


def patch_metadata(
    source: Path,
    output: Path,
    harness_commit: str,
    pipe: str,
    source_identity: dict[str, Any],
) -> None:
    candidate_path = output / "candidate-manifest.json"
    candidate = load_json_object(candidate_path)
    candidate["schema"] = "xar.ck3.g2_m4_council14_r691_harness_candidate_v1"
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
    candidate["next_live"]["unique_pipe"] = pipe
    write_json(candidate_path, candidate)

    environment_sha, environment_manifest_sha = patch_environment(source, output)
    for name in ("profile-preflight.json", "preflight.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = str(payload["schema"]).replace(
            "g2_m4_council13", "g2_m4_council14"
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
    validation["schema"] = "xar.ck3.g2_m4_council14_r691_validation_v1"
    validation["self_contained_runtime_contract"] = {
        "normal": "pending",
        "optimized": "pending",
        "candidate_local_source": True,
        "source_commit": RUNTIME_SOURCE_COMMIT,
        "source_tree_sha256": source_identity["source_tree_sha256"],
        "module_file_and_sha_asserted": True,
        "external_workspace_root_allowed": False,
    }
    validation["candidate_no_launch_preflight"] = "pending"
    validation["ck3_launched"] = False
    write_json(validation_path, validation)
    preflight_path = output / "preflight.json"
    preflight = load_json_object(preflight_path)
    preflight["candidate_manifest_sha256"] = sha256(candidate_path)
    write_json(preflight_path, preflight)


def patch_text_bindings(source: Path, output: Path, harness_commit: str, pipe: str) -> None:
    for name in ("execute-command.txt", "preflight-command.txt", "R691-start-checklist.md"):
        path = output / name
        text = path.read_text(encoding="utf-8-sig")
        text = text.replace(str(source), str(output))
        text = text.replace(source.as_posix(), output.as_posix())
        text = text.replace(SOURCE_HARNESS_COMMIT, harness_commit)
        text = text.replace(OLD_PIPE, pipe)
        text = text.replace("COUNCIL13", "COUNCIL14")
        text = text.replace("g2_m4_council13", "g2_m4_council14")
        path.write_text(text, encoding="utf-8")
    for name in ("operator-runtime.json", "operator-runtime.example.json"):
        path = output / name
        payload = load_json_object(path)
        payload["schema"] = "xar.ck3.g2_m4_council14_operator_runtime_v1"
        payload.pop("workspace_root", None)
        payload["runtime_source"] = "candidate-local:source-repo/ck3_autonomous_player/src"
        payload["portability"] = (
            "replace Python and game paths with authorized equivalents; runtime code is sealed in this candidate"
        )
        write_json(path, payload)


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
        "schema": "xar.ck3.g2_m4_council14_r691_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": SOURCE_PRODUCT_COMMIT,
        "harness_commit": harness_commit,
        "suggested_round": "R691",
        "round_allocated": False,
        "ck3_launched": False,
        "candidate_manifest_sha256": candidate_hash,
        "bridge_dll_sha256": sha256(output / "candidate-bin/xar_ck3_bridge.dll"),
        "source_save_sha256": sha256(output / "source-save/dev3b_r639.ck3"),
        "unique_pipe": pipe,
        "source_candidate_sealed_manifest_sha256": SOURCE_SEALED_SHA256,
        "runtime_source": source_identity,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "runtime_red": {
            "report_sha256": R690_RED_SHA256,
            "failure": "AttributeError: missing take_internal_semantic_snapshot",
            "cleanup_proven": True,
            "saves_unchanged": True,
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
    if harness_commit[:7] not in output.name:
        raise ValueError("output directory must include the harness short hash")
    sealed = verify_source(source)
    tracked_paths = verify_runtime_repository(repo_root)
    pipe = rf"\\.\pipe\xar_ck3_bridge_g2_m4_council14_r691_{harness_commit[:7]}"
    copy_candidate(source, output, sealed["files"])
    try:
        source_identity = copy_runtime(repo_root, output, tracked_paths)
        shutil.copyfile(
            Path(__file__).with_name("candidate_runtime_identity.py"),
            output / "candidate_runtime_identity.py",
        )
        shutil.copyfile(
            Path(__file__).with_name("candidate_runtime_import_probe.py"),
            output / "candidate_runtime_import_probe.py",
        )
        patch_runner(output)
        patch_verifier(output, harness_commit, pipe)
        patch_invoke(output, pipe)
        patch_metadata(source, output, harness_commit, pipe, source_identity)
        patch_text_bindings(source, output, harness_commit, pipe)
        candidate_hash, sealed_hash = seal(output, harness_commit, pipe, source_identity)
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
