#!/usr/bin/env python3
"""Run the Raiktor three-way exit intake from hash-bound JSON artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.simulation.raiktor_three_way_exit_intake import (  # noqa: E402
    provide_raiktor_three_way_exit_intake,
)


MANIFEST_CONTRACT = "raiktor-three-way-exit-file-intake-manifest-v1"
OUTPUT_SCHEMA = "xar.ck3.g2_three_way_exit_file_intake.v1"
_INPUT_NAMES = (
    "candidate",
    "surrender_terms",
    "campaign_certificate",
    "owner_budget_source",
    "white_peace_terms_observation",
    "white_peace_utility_evaluation",
    "observed_surrender_outcome",
)
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class FileIntakeError(ValueError):
    """A manifest, bound JSON input, or output path is invalid."""


def run_file_intake(
    manifest_path: Path,
    output_path: Path,
    *,
    expected_manifest_sha256: str,
) -> dict[str, object]:
    """Validate one manifest and write one deterministic offline result."""

    manifest_path = manifest_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        raise FileIntakeError(f"output already exists: {output_path}")
    manifest_bytes = _read_bytes(manifest_path, "manifest")
    manifest_sha = _file_sha256(manifest_bytes)
    if manifest_sha != _sha256(
        expected_manifest_sha256, "expected_manifest_sha256"
    ):
        raise FileIntakeError("manifest hash differs from expected SHA-256")
    manifest = _json_object(manifest_bytes, "manifest")
    if set(manifest) != {"schema_version", "contract", "inputs"}:
        raise FileIntakeError("manifest keys drifted")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("contract") != MANIFEST_CONTRACT
    ):
        raise FileIntakeError("manifest identity drifted")
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != set(_INPUT_NAMES):
        raise FileIntakeError("manifest input names drifted")

    values: dict[str, object | None] = {}
    bindings: dict[str, object] = {}
    for name in _INPUT_NAMES:
        value, binding = _load_bound_input(
            inputs[name], manifest_path.parent, name
        )
        values[name] = value
        bindings[name] = binding

    owner_binding = bindings["owner_budget_source"]
    owner_path = (
        owner_binding["path"]
        if isinstance(owner_binding, dict)
        and owner_binding.get("supplied") is True
        else None
    )
    intake = provide_raiktor_three_way_exit_intake(
        candidate_value=values["candidate"],
        surrender_terms_value=values["surrender_terms"],
        campaign_value=values["campaign_certificate"],
        owner_budget_source_path=owner_path,
        white_peace_observation_value=values[
            "white_peace_terms_observation"
        ],
        white_peace_utility_evaluation_value=values[
            "white_peace_utility_evaluation"
        ],
        observed_surrender_outcome_value=values[
            "observed_surrender_outcome"
        ],
    )
    output = {
        "schema": OUTPUT_SCHEMA,
        "status": intake["status"],
        "ok": True,
        "manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha,
        },
        "input_bindings": bindings,
        "intake_result": intake,
        "boundaries": {
            "ck3_started_or_attached": False,
            "bridge_queried": False,
            "mutation_commands": [],
            "production_recommendation_ready": False,
            "action_ready": False,
            "gen034_closed": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output_path)
    return output


def _load_bound_input(
    value: object, manifest_root: Path, name: str
) -> tuple[dict[str, object] | None, dict[str, object]]:
    if value is None:
        return None, {"supplied": False, "path": None, "sha256": None}
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise FileIntakeError(f"{name} binding is malformed")
    raw_path = value.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise FileIntakeError(f"{name} path must be nonempty")
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_root / path
    path = path.resolve()
    payload = _read_bytes(path, name)
    actual_sha = _file_sha256(payload)
    expected_sha = _sha256(value.get("sha256"), f"{name}.sha256")
    if actual_sha != expected_sha:
        raise FileIntakeError(f"{name} hash differs from manifest")
    return _json_object(payload, name), {
        "supplied": True,
        "path": str(path),
        "sha256": actual_sha,
    }


def _read_bytes(path: Path, name: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise FileIntakeError(f"cannot read {name}: {path}") from error


def _json_object(payload: bytes, name: str) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise FileIntakeError(f"{name} must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise FileIntakeError(f"{name} must be a JSON object")
    return value


def _file_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise FileIntakeError(f"{name} must be an uppercase SHA-256")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result = run_file_intake(
            arguments.manifest,
            arguments.output,
            expected_manifest_sha256=arguments.manifest_sha256,
        )
    except (FileIntakeError, ValueError) as error:
        print(f"RED: {error}")
        return 2
    print(
        f"G2_THREE_WAY_FILE_INTAKE status={result['status']} "
        f"action_ready={str(result['boundaries']['action_ready']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
