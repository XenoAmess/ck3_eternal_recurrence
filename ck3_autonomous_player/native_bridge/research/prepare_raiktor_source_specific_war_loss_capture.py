#!/usr/bin/env python3
"""Verify the default-OFF Raiktor source-attribution provider offline.

This entry only reads the exact executable and repository sources.  It does
not inventory, launch, attach to, or communicate with a CK3 process.  An
optional completed private capture can be normalized through the typed
provider contract, but absence of such a capture remains honestly static.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import verify_raiktor_spawn_army_execute_v1 as abi_verifier  # noqa: E402
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    CONTRACT,
    normalize_raiktor_source_specific_capture,
)


DEFAULT_CONTRACT = (
    RESEARCH_ROOT
    / "fixtures"
    / "raiktor_source_specific_war_loss_attribution_v1_contract.json"
)
OUTPUT_SCHEMA = "xar.ck3.raiktor_source_specific_war_loss_preflight.v1"
OUTPUT_STATUS = "GREEN_STATIC_SOURCE_ATTRIBUTION_PROVIDER"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class PreflightError(RuntimeError):
    """Frozen source, ABI, provider, or capture contract drifted."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PreflightError(f"{name} must be an object")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise PreflightError(f"{name} must be an uppercase SHA-256")
    return value


def _load_object(path: Path, name: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), name)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"could not read {name}: {error}") from error


def _resolve(value: object, *, repo_root: Path) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _validate_file(
    name: str,
    *,
    paths: dict[str, object],
    hashes: dict[str, object],
    repo_root: Path,
) -> Path:
    path = _resolve(paths[name], repo_root=repo_root)
    if not path.is_file():
        raise PreflightError(f"{name} is missing: {path}")
    expected = _sha256(hashes[name], f"{name} hash")
    actual = _sha256_file(path)
    if actual != expected:
        raise PreflightError(f"{name} hash differs: {actual} != {expected}")
    return path


def run_preflight(
    contract_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    capture_path: Path | None = None,
) -> dict[str, object]:
    output_path = output_path.resolve()
    if output_path.exists():
        raise PreflightError(f"output already exists: {output_path}")
    contract_path = contract_path.resolve()
    contract = _load_object(contract_path, "contract")
    if (
        contract.get("schema_version") != 1
        or contract.get("contract") != CONTRACT
        or contract.get("status")
        != "static-ready-private-capture-live-not-run"
        or contract.get("default_off") is not True
        or contract.get("private_only") is not True
        or contract.get("read_only_observer") is not True
        or contract.get("live_authorized") is not False
    ):
        raise PreflightError("provider contract boundary drifted")
    paths = _object(contract.get("paths"), "paths")
    hashes = _object(contract.get("sha256"), "sha256")
    checked = {
        name: _validate_file(
            name, paths=paths, hashes=hashes, repo_root=repo_root
        )
        for name in (
            "game_executable",
            "capture_executable",
            "preflight",
            "spawn_army_abi",
            "spawn_army_verifier",
            "capture_source",
            "capture_manifest",
            "cmake",
            "provider",
        )
    }

    abi_failures = abi_verifier.verify(
        checked["game_executable"], checked["spawn_army_abi"]
    )
    if abi_failures:
        raise PreflightError(f"spawn_army ABI verification failed: {abi_failures}")
    capture_manifest = _load_object(
        checked["capture_manifest"], "capture manifest"
    )
    observation = _object(
        capture_manifest.get("observation"), "capture observation"
    )
    action_filter = _object(
        capture_manifest.get("action_filter"), "capture action_filter"
    )
    implementation = _object(
        contract.get("implementation"), "implementation"
    )
    hard_boundaries = _object(
        contract.get("hard_boundaries"), "hard_boundaries"
    )
    if (
        observation.get("stop_rva") != "0x2E7F951"
        or observation.get("window_end_rva_exclusive") != "0x2E7F9A6"
        or action_filter.get("required_unique_loaded_nodes") != 6
        or action_filter.get("required_unique_army_generation_ids") != 6
        or capture_manifest.get("production_installed") is not False
        or capture_manifest.get("production_abi_changed") is not False
        or capture_manifest.get("readiness_promotion") is not False
        or implementation.get("default_enabled") is not False
        or implementation.get("shared_bridge_dll_changed") is not False
        or implementation.get("public_wire_changed") is not False
        or any(value is not False for value in hard_boundaries.values())
    ):
        raise PreflightError("existing private capture boundary drifted")
    cmake_source = checked["cmake"].read_text(encoding="utf-8")
    if not re.search(
        r"option\(\s*XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1\s+"
        r'"[^"]+"\s+OFF\s*\)',
        cmake_source,
        flags=re.MULTILINE,
    ):
        raise PreflightError("private capture CMake option is not default OFF")
    if (
        "research/raiktor_war_bound_private_capture_v1.cpp"
        not in cmake_source
        or "xar_ck3_raiktor_war_bound_private_capture_v1" not in cmake_source
    ):
        raise PreflightError("standalone private capture target is unavailable")
    offline_build = _object(contract.get("offline_build"), "offline_build")
    self_test = subprocess.run(
        [str(checked["capture_executable"]), "--self-test"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    expected_self_test = offline_build.get("self_test_expected")
    if (
        self_test.returncode != offline_build.get("self_test_exit_code")
        or self_test.stdout.strip() != expected_self_test
        or self_test.stderr.strip()
    ):
        raise PreflightError(
            "standalone capture self-test failed: "
            f"exit={self_test.returncode} stdout={self_test.stdout!r} "
            f"stderr={self_test.stderr!r}"
        )

    normalized_capture = None
    if capture_path is not None:
        capture_path = capture_path.resolve()
        normalized_capture = normalize_raiktor_source_specific_capture(
            _load_object(capture_path, "private capture"),
            capture_sha256=_sha256_file(capture_path),
        )
    report = {
        "schema": OUTPUT_SCHEMA,
        "status": OUTPUT_STATUS,
        "ok": True,
        "contract": str(contract_path),
        "contract_sha256": _sha256_file(contract_path),
        "checked_files": {
            name: {"path": str(path), "sha256": hashes[name]}
            for name, path in checked.items()
        },
        "ck3_started_or_attached": False,
        "process_inventory_not_required_for_offline_source_read": True,
        "exact_build_abi_verified": True,
        "standalone_default_off_target_ready": True,
        "standalone_capture_self_test": {
            "exit_code": self_test.returncode,
            "stdout": self_test.stdout.strip(),
            "stderr": self_test.stderr.strip(),
        },
        "capture_supplied": normalized_capture is not None,
        "normalized_capture": normalized_capture,
        "readiness": {
            "provider_code_ready": True,
            "capture_shape_fixture_ready": True,
            "private_capture_live_executed": False,
            "source_specific_loss_ready": False,
            "comparison_input_ready": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "next_live_completion": contract["next_live_completion"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report = run_preflight(
            arguments.contract,
            arguments.output,
            capture_path=arguments.capture,
        )
    except (PreflightError, ValueError) as error:
        print(f"RED: {error}")
        return 2
    print(
        f"{report['status']} exact_build_abi_verified=true "
        "standalone_default_off_target_ready=true "
        "private_capture_live_executed=false comparison_input_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
