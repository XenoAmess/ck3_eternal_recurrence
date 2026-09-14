"""Refreeze the immutable DEV13 construction probe as a Python-only R691 candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any


SOURCE_COMMIT = "e08f4a1b5a807f176b29ce280383d93d9c051879"
SOURCE_TREE = "f405dc100a2b7e5ab42f5ba4b676b47ff448a4ba"
SOURCE_CANDIDATE_MANIFEST_SHA256 = (
    "7FE54643ED8E117F9802327C987BC4C6E36B4C767F8A470DE6983464D07B7584"
)
SOURCE_PREP_MANIFEST_SHA256 = (
    "BD2410AA0302E133B1AFDBBAC6132FD7B2556316E50F0E026FED9F999C753A64"
)
SOURCE_PREFLIGHT_SHA256 = (
    "C12E9B7A06DF75A0508D0AD666A3957FFA7E00888D4FBB49D76ECF92A818A3FA"
)
SOURCE_RUNNER_SHA256 = (
    "132D558B7B83F8F0E0EC564B7CEA7665FB2A9ECAE7AFA40076D9FBA34C9A829A"
)
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SAVE_SHA256 = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
OLD_ROUND = "R690"
NEW_ROUND = "R691"
SOURCE_PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_r690_construction_one_day_e08f4a1"
PIPE = r"\\.\pipe\xar_ck3_bridge_g2_m4_dev14_r691_construction_one_day_e08f4a1"
SCHEMA = "xar.ck3.g2_m4_dev14_r691_construction_one_day_candidate_v1"
SEALED_SCHEMA = "xar.ck3.g2_m4_dev14_r691_sealed_candidate_v1"


class FreezeError(RuntimeError):
    """An immutable source or generated R691 contract drifted."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def record(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(root).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def _git(source: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "-C", str(source), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
        env=environment,
    )
    require(completed.returncode == 0, f"Git check failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def validate_source_candidate(source: Path) -> dict[str, Any]:
    source = source.expanduser().resolve()
    require(source.is_dir(), f"source candidate is missing: {source}")
    expected = {
        "candidate-manifest.json": SOURCE_CANDIDATE_MANIFEST_SHA256,
        "prep-manifest.json": SOURCE_PREP_MANIFEST_SHA256,
        "preflight_r690.py": SOURCE_PREFLIGHT_SHA256,
        "run_r690.py": SOURCE_RUNNER_SHA256,
    }
    observed: dict[str, str] = {}
    for relative, digest in expected.items():
        path = source / relative
        require(path.is_file(), f"source candidate file is missing: {relative}")
        observed[relative] = sha256(path)
        require(observed[relative] == digest, f"source candidate file differs: {relative}")
    require(
        (source / "candidate-manifest.sha256").read_text(encoding="ascii").split()[0].upper()
        == SOURCE_CANDIDATE_MANIFEST_SHA256,
        "source candidate manifest sidecar differs",
    )
    require(
        (source / "prep-manifest.sha256").read_text(encoding="ascii").split()[0].upper()
        == SOURCE_PREP_MANIFEST_SHA256,
        "source prep manifest sidecar differs",
    )
    manifest = json.loads((source / "candidate-manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest.get("source", {}).get("commit") == SOURCE_COMMIT, "source commit differs")
    require(manifest.get("source", {}).get("tree") == SOURCE_TREE, "source tree differs")
    require(manifest.get("live_plan", {}).get("suggested_round") == "R690", "source round differs")
    source_repo = source / "source-repo"
    require(_git(source_repo, "rev-parse", "HEAD") == SOURCE_COMMIT, "source repo HEAD differs")
    require(
        not _git(source_repo, "status", "--porcelain=v1", "--untracked-files=no"),
        "source repo tracked files differ",
    )
    require(
        sha256(source / "source-save" / "dev3b_r639.ck3") == SAVE_SHA256,
        "source save differs",
    )
    for name, row in manifest.get("artifacts", {}).items():
        path = source / "bin" / name
        require(path.is_file(), f"source binary is missing: {name}")
        require(path.stat().st_size == row.get("size"), f"source binary size differs: {name}")
        require(sha256(path) == row.get("sha256"), f"source binary hash differs: {name}")
    return {"root": source, "manifest": manifest, "hashes": observed}


def rebind_live_runner(source: str) -> str:
    require("from preflight_r690 import" in source, "source runner preflight import differs")
    require(source.count('"resume-map"') == 1, "source runner resume site differs")
    require(source.count('"set-speed-3"') == 1, "source runner speed site differs")
    upper = "__XAR_NEW_ROUND_UPPER__"
    lower = "__xar_new_round_lower__"
    result = source.replace("R690", upper).replace("r690", lower)
    result = result.replace("R689", "R690").replace("r689", "r690")
    result = result.replace(upper, "R691").replace(lower, "r691")
    rendered_source_pipe = SOURCE_PIPE.replace("r690", "r691")
    require(rendered_source_pipe in result, "source named pipe was not found after round rebind")
    result = result.replace(rendered_source_pipe, PIPE)
    result = result.replace("DEV13", "DEV14").replace("dev13", "dev14")
    require("from preflight_r691 import" in result, "R691 preflight import was not rendered")
    require("state-r690" not in result and "live-r690" not in result, "old mutable path remains")
    require(PIPE in result, "R691 named pipe was not rendered")
    require("powershell" not in result.casefold(), "generated runner invokes PowerShell")
    return result


def render_preflight() -> str:
    return f'''"""No-launch preflight for the sealed DEV14 R691 construction one-day run."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_candidate import _windows_ck3_inventory
from xar_autoplayer.environment import make_spec, verify_profile

ART = Path(__file__).resolve().parent
STATE = ART / "state-r691"
BIN = ART / "bin"
SOURCE_REPO = ART / "source-repo"
SOURCE_SAVE = ART / "source-save" / "dev3b_r639.ck3"
TARGET_SAVE = STATE / "profile" / "save games" / "dev3b_r639.ck3"
GAME = Path(os.environ.get("XAR_CK3_GAME_DIR", "__MISSING_XAR_CK3_GAME_DIR__"))
EXPECTED_MASTER = {SOURCE_COMMIT!r}
EXPECTED_EXE = {EXE_SHA256!r}
EXPECTED_SAVE = {SAVE_SHA256!r}
EXPECTED_PIPE = {PIPE!r}
OBSERVER_KEY = "g2_domain_construction_native_runtime_callsite_observer_v1"
ARM_CAPABILITY = "game.command.research-arm-tactical-daily-sentinel-v1-N"
STATUS_CAPABILITY = "game.command.research-query-tactical-daily-sentinel-v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git(*args: str) -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", *args], cwd=SOURCE_REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=30,
        env=environment,
    )
    require(completed.returncode == 0, f"Git check failed: {{completed.stderr.strip()}}")
    return completed.stdout.strip()


def verify_round_authorization() -> dict[str, Any]:
    path = ART / "round-authorization.json"
    require(path.is_file(), "R691 has not been allocated by the global CK3 owner")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), "round authorization must be an object")
    require(value.get("status") == "AUTHORIZED", "round authorization is not active")
    require(value.get("new_round") == "R691", "round authorization is not for R691")
    require(value.get("old_round") == "R690", "R691 must follow R690")
    require(value.get("r690_confirmed_terminated") is True, "R690 termination is unconfirmed")
    require(
        isinstance(value.get("global_ck3_zero_confirmed_at"), str)
        and bool(value["global_ck3_zero_confirmed_at"].strip()),
        "global zero-CK3 confirmation is missing",
    )
    require(isinstance(value.get("owner"), str) and bool(value["owner"].strip()), "CK3 owner is missing")
    return value


def collect_preflight(
    *, require_zero_ck3: bool = True, require_round_authorization: bool = False
) -> dict[str, Any]:
    require("XAR_CK3_GAME_DIR" in os.environ, "explicit game path was not resolved")
    require(os.environ.get("XAR_CK3_PIPE_NAME", EXPECTED_PIPE) == EXPECTED_PIPE, "pipe differs")
    require(SOURCE_REPO.is_dir(), "sealed source repository is missing")
    require(git("rev-parse", "HEAD") == EXPECTED_MASTER, "source repo HEAD mismatch")
    require(not git("status", "--porcelain=v1", "--untracked-files=no"), "source repo is dirty")
    manifest_path = ART / "candidate-manifest.json"
    expected_manifest = (ART / "candidate-manifest.sha256").read_text(encoding="ascii").split()[0].upper()
    require(sha256(manifest_path) == expected_manifest, "candidate manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    require(manifest.get("schema") == {SCHEMA!r}, "candidate schema mismatch")
    require(manifest.get("source_commit") == EXPECTED_MASTER, "candidate source mismatch")
    require(manifest.get("next_live", {{}}).get("old_round") == "R690", "old round mismatch")
    require(manifest.get("next_live", {{}}).get("new_round") == "R691", "new round mismatch")
    require(manifest.get("next_live", {{}}).get("unique_pipe") == EXPECTED_PIPE, "manifest pipe mismatch")
    for name, record in manifest.get("artifacts", {{}}).items():
        path = BIN / name
        require(path.is_file(), f"candidate binary missing: {{name}}")
        require(sha256(path) == record.get("sha256"), f"candidate binary hash mismatch: {{name}}")
    spec = make_spec(STATE, GAME)
    verified = verify_profile(spec)
    require(sha256(SOURCE_SAVE) == EXPECTED_SAVE, "source save hash mismatch")
    require(sha256(TARGET_SAVE) == EXPECTED_SAVE, "target save hash mismatch")
    require(bool(SOURCE_SAVE.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY), "source save is writable")
    require(bool(TARGET_SAVE.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY), "target save is writable")
    require(sha256(spec.game_exe) == EXPECTED_EXE, "exact-build EXE mismatch")
    inventory = _windows_ck3_inventory()
    if require_zero_ck3:
        require(not inventory, "prelaunch CK3 inventory is nonzero")
    authorization = verify_round_authorization() if require_round_authorization else None
    if require_round_authorization:
        require(not (ART / "live-r691").exists(), "R691 live output exists; retry is forbidden")
    return {{
        "format_version": 1,
        "kind": "g2_m4_dev14_r691_construction_one_day_preflight_v1",
        "status": "GREEN_NO_LAUNCH",
        "checked_at": now(),
        "old_round": "R690",
        "proposed_round": "R691",
        "round_allocated": authorization is not None,
        "source_commit": EXPECTED_MASTER,
        "verified_profile_environment_sha256": verified.get("environment_sha256"),
        "candidate_manifest_sha256": expected_manifest,
        "unique_pipe": EXPECTED_PIPE,
        "state_relative_path": "state-r691",
        "live_relative_path": "live-r691",
        "source_save_sha256": sha256(SOURCE_SAVE),
        "target_save_sha256": sha256(TARGET_SAVE),
        "game_executable_sha256": sha256(spec.game_exe),
        "ck3_processes": inventory,
        "protocol": {{
            "target_date_raw_delta": 24,
            "speed": 3,
            "sentinel_mode": "terminal",
            "sentinel_armies": 0,
            "resume_submissions": 1,
            "readiness_timeout_seconds": 300,
            "post_resume_timeout_seconds": 30,
            "total_timeout_seconds": 330,
        }},
        "policy": {{
            "ui_inputs": 0,
            "gameplay_decision_actions": 0,
            "forced_producer": False,
            "forced_effects": 0,
            "forced_gui": 0,
            "save_mutation_requested": False,
            "same_round_retry": False,
        }},
    }}


def main() -> int:
    payload = collect_preflight(require_zero_ck3=True, require_round_authorization=False)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _prepare_profile(root: Path, game_dir: Path) -> dict[str, object]:
    source_root = root / "source-repo"
    source_path = source_root / "ck3_autonomous_player" / "src"
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source_path))
    try:
        environment = importlib.import_module("xar_autoplayer.environment")
        spec = environment.make_spec(root / "state-r691", game_dir)
        prepared = environment.prepare_profile(spec)
        target = spec.profile_dir / "save games" / "dev3b_r639.ck3"
        shutil.copy2(root / "source-save" / "dev3b_r639.ck3", target)
        target.chmod(stat.S_IREAD)
        (root / "source-save" / "dev3b_r639.ck3").chmod(stat.S_IREAD)
        verified = environment.verify_profile(spec)
    finally:
        sys.path.remove(str(source_path))
    require(sha256(target) == SAVE_SHA256, "prepared target save differs")
    return {
        "status": "GREEN_NO_LAUNCH",
        "prepared_at": now(),
        "state_relative_path": "state-r691",
        "source_save_sha256": SAVE_SHA256,
        "target_save_sha256": sha256(target),
        "source_and_target_read_only": True,
        "production_tree_sha256": prepared.get("mod", {}).get("production_tree_sha256"),
        "verified_profile_environment_sha256": verified.get("environment_sha256"),
        "ck3_launched": False,
    }


def _run_verifier(
    *, python: Path, verifier: Path, root: Path, game_dir: Path, optimized: bool,
) -> dict[str, object]:
    command = [str(python)]
    if optimized:
        command.append("-O")
    command.extend(
        [
            "-B",
            str(verifier),
            "--candidate-root",
            str(root),
            "--game-dir",
            str(game_dir),
            "--python",
            str(python),
            "--pre-seal",
        ]
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=180,
        env=environment,
    )
    require(completed.returncode == 0, f"pre-seal verifier failed: {completed.stderr.strip()}")
    result = json.loads(completed.stdout)
    require(result.get("status") == "GREEN_NO_LAUNCH", "verifier status differs")
    require(result.get("mode") == ("optimized" if optimized else "normal"), "verifier mode differs")
    return {
        "status": result["status"],
        "mode": result["mode"],
        "ck3_launched": result.get("ck3_launched"),
        "candidate_manifest_sha256": result.get("candidate_manifest_sha256"),
    }


def _sealed_inventory(root: Path) -> list[dict[str, object]]:
    excluded = {"sealed-prep-manifest.json", "sealed-prep-manifest.sha256"}
    return [
        record(path, root)
        for path in sorted(
            (
                path
                for path in root.rglob("*")
                if path.is_file() and path.relative_to(root).as_posix() not in excluded
            ),
            key=lambda value: value.relative_to(root).as_posix(),
        )
    ]


def freeze(source: Path, output: Path, game_dir: Path, python: Path) -> dict[str, object]:
    source_state = validate_source_candidate(source)
    source = source_state["root"]
    output = output.expanduser().resolve()
    game_dir = game_dir.expanduser().resolve()
    python = python.expanduser().resolve()
    require(not output.exists(), f"fresh output already exists: {output}")
    require(python.is_file(), f"Python executable is missing: {python}")
    game_exe = game_dir / "binaries" / "ck3.exe"
    require(game_exe.is_file(), f"game executable is missing: {game_exe}")
    require(sha256(game_exe) == EXE_SHA256, "exact-build game executable differs")
    output.mkdir(parents=True)
    for directory in ("bin", "source-repo", "source-save"):
        shutil.copytree(source / directory, output / directory, copy_function=shutil.copy2)
    for name in ("construction-runtime-observer-abi.json", "focused-ctest.log"):
        shutil.copy2(source / name, output / name)

    entry_source = Path(__file__).with_name("run_domain_construction_one_day_candidate.py")
    require(entry_source.is_file(), "candidate entry runner is missing")
    shutil.copy2(entry_source, output / "verify_candidate.py")
    live_source = (source / "run_r690.py").read_text(encoding="utf-8-sig")
    (output / "run_r691.py").write_text(
        rebind_live_runner(live_source), encoding="utf-8", newline="\n"
    )
    (output / "preflight_r691.py").write_text(
        render_preflight(), encoding="utf-8", newline="\n"
    )
    for generated_name in ("verify_candidate.py", "run_r691.py", "preflight_r691.py"):
        generated_path = output / generated_name
        compile(
            generated_path.read_text(encoding="utf-8-sig"),
            str(generated_path),
            "exec",
        )
    write_json(
        output / "operator-runtime.example.json",
        {
            "schema": "xar.ck3.g2_m4_dev14_r691_operator_runtime_v1",
            "python": "%XAR_PYTHON%",
            "game_dir": "%XAR_CK3_GAME_DIR%",
            "resolution": "explicit-operator-config-or-cli",
            "system_python_fallback": False,
        },
    )
    write_json(
        output / "round-authorization.example.json",
        {
            "format_version": 1,
            "status": "NOT_AUTHORIZED_EXAMPLE_ONLY",
            "old_round": OLD_ROUND,
            "new_round": NEW_ROUND,
            "r690_confirmed_terminated": False,
            "global_ck3_zero_confirmed_at": "",
            "owner": "",
        },
    )
    profile = _prepare_profile(output, game_dir)
    write_json(output / "profile-preparation.json", profile)

    source_manifest = source_state["manifest"]
    artifacts = {
        name: {
            "relative_path": f"bin/{name}",
            "size": (output / "bin" / name).stat().st_size,
            "sha256": sha256(output / "bin" / name),
        }
        for name in source_manifest["artifacts"]
    }
    manifest: dict[str, object] = {
        "format_version": 1,
        "schema": SCHEMA,
        "status": "sealed-no-launch",
        "created_at": now(),
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "source_candidate_manifest_sha256": SOURCE_CANDIDATE_MANIFEST_SHA256,
        "source_prep_manifest_sha256": SOURCE_PREP_MANIFEST_SHA256,
        "source_candidate_unchanged": True,
        "exact_build": {
            "game_version": "1.19.0.6",
            "executable_sha256": EXE_SHA256,
            "construction_patch_window": "0x18D2948..0x18D2958",
            "construction_direct_call": "0x18D294F -> 0x1921810",
            "daily_tick_final_stage": "0x26D3E80",
            "date_raw_hours_per_day": 24,
        },
        "build": source_manifest["build"],
        "artifacts": artifacts,
        "private_contract": {
            **source_manifest["private_contract"],
            "relative_path": "construction-runtime-observer-abi.json",
        },
        "runner": {
            "entry": {"path": "verify_candidate.py", "sha256": sha256(output / "verify_candidate.py")},
            "live": {"path": "run_r691.py", "sha256": sha256(output / "run_r691.py")},
            "preflight": {"path": "preflight_r691.py", "sha256": sha256(output / "preflight_r691.py")},
            "python_only": True,
            "normal_and_optimized_required": True,
        },
        "next_live": {
            "old_round": OLD_ROUND,
            "new_round": NEW_ROUND,
            "round_allocated": False,
            "unique_pipe": PIPE,
            "state_relative_path": "state-r691",
            "live_relative_path": "live-r691",
            "readiness_timeout_seconds": 300,
            "post_resume_timeout_seconds": 30,
            "total_observation_timeout_seconds": 330,
            "target_date_raw_delta": 24,
            "speed": 3,
            "sentinel_mode": "terminal",
            "sentinel_armies": 0,
            "resume_submissions": 1,
            "same_round_retry": False,
        },
        "profile": profile,
        "policy": {
            "ui_inputs": 0,
            "gameplay_decision_actions": 0,
            "forced_producer": False,
            "forced_effects": 0,
            "forced_gui": 0,
            "save_mutation_requested": False,
            "raw_before_validation": True,
            "managed_cleanup": True,
        },
        "public_surface": {
            "mcp_schema_changed": False,
            "planner_changed": False,
            "public_native_capability_changed": False,
            "open_kaishek_change_required": False,
        },
        "no_launch": {"ck3_launched": False, "screen_used": False},
    }
    write_json(output / "candidate-manifest.json", manifest)
    manifest_hash = sha256(output / "candidate-manifest.json")
    (output / "candidate-manifest.sha256").write_text(
        f"{manifest_hash}  candidate-manifest.json\n", encoding="ascii", newline="\n"
    )
    verifier = output / "verify_candidate.py"
    validation = {
        "format_version": 1,
        "schema": "xar.ck3.g2_m4_dev14_r691_candidate_validation_v1",
        "status": "GREEN_NO_LAUNCH",
        "normal": _run_verifier(
            python=python, verifier=verifier, root=output, game_dir=game_dir, optimized=False
        ),
        "optimized": _run_verifier(
            python=python, verifier=verifier, root=output, game_dir=game_dir, optimized=True
        ),
        "ck3_launched": False,
        "source_candidate_unchanged": True,
    }
    write_json(output / "validation-results.json", validation)
    sealed_files = _sealed_inventory(output)
    sealed = {
        "format_version": 1,
        "schema": SEALED_SCHEMA,
        "status": "sealed-no-launch",
        "sealed_at": now(),
        "source_commit": SOURCE_COMMIT,
        "candidate_manifest_sha256": manifest_hash,
        "old_round": OLD_ROUND,
        "new_round": NEW_ROUND,
        "unique_pipe": PIPE,
        "round_allocated": False,
        "ck3_launched": False,
        "mutable_live_paths": ["round-authorization.json", "live-r691/"],
        "file_count": len(sealed_files),
        "total_bytes": sum(int(row["size_bytes"]) for row in sealed_files),
        "files": sealed_files,
    }
    write_json(output / "sealed-prep-manifest.json", sealed)
    sealed_hash = sha256(output / "sealed-prep-manifest.json")
    (output / "sealed-prep-manifest.sha256").write_text(
        f"{sealed_hash}  sealed-prep-manifest.json\n", encoding="ascii", newline="\n"
    )
    after = validate_source_candidate(source)
    require(after["hashes"] == source_state["hashes"], "source candidate changed during refreeze")
    return {
        "status": "GREEN_NO_LAUNCH",
        "candidate_root": str(output),
        "candidate_manifest_sha256": manifest_hash,
        "sealed_manifest_sha256": sealed_hash,
        "file_count": len(sealed_files),
        "total_bytes": sealed["total_bytes"],
        "old_round": OLD_ROUND,
        "new_round": NEW_ROUND,
        "unique_pipe": PIPE,
        "source_candidate_unchanged": True,
        "ck3_launched": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars="@")
    parser.add_argument("--source-candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args(argv)
    result = freeze(args.source_candidate, args.output, args.game_dir, args.python)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
