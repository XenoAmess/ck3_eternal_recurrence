#!/usr/bin/env python3
"""Build one hash-bound, no-launch Raiktor terms comparison artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.simulation.raiktor_same_frame_white_peace_comparator import (  # noqa: E402
    SameFrameWhitePeaceComparisonError,
    provide_raiktor_same_frame_white_peace_comparison,
)


OUTPUT_SCHEMA = "xar.ck3.g2_same_frame_white_peace_comparison_artifact.v1"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class ComparisonArtifactError(RuntimeError):
    """An immutable input or output boundary was not satisfied."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ComparisonArtifactError(f"{name} must be an uppercase SHA-256")
    return value


def _load(path: Path, expected_sha256: str, name: str) -> dict[str, object]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ComparisonArtifactError(f"{name} is missing: {resolved}")
    expected = _expected_sha256(expected_sha256, f"{name} SHA-256")
    actual = _sha256_file(resolved)
    if actual != expected:
        raise ComparisonArtifactError(
            f"{name} SHA-256 differs: {actual} != {expected}"
        )
    try:
        value = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ComparisonArtifactError(f"could not read {name}: {error}") from error
    if not isinstance(value, dict):
        raise ComparisonArtifactError(f"{name} must be a JSON object")
    return value


def prepare_comparison_artifact(
    *,
    source_checkpoint_path: Path,
    source_checkpoint_sha256: str,
    white_peace_observation_path: Path,
    white_peace_observation_sha256: str,
    surrender_terms_path: Path,
    surrender_terms_sha256: str,
    output_path: Path,
) -> dict[str, object]:
    """Read three pinned inputs and atomically create a static-only artifact."""

    output = output_path.resolve()
    if output.exists():
        raise ComparisonArtifactError(f"output already exists: {output}")
    inputs = {
        "source_checkpoint": (
            source_checkpoint_path.resolve(),
            _expected_sha256(source_checkpoint_sha256, "source checkpoint SHA-256"),
        ),
        "white_peace_observation": (
            white_peace_observation_path.resolve(),
            _expected_sha256(
                white_peace_observation_sha256,
                "white-peace observation SHA-256",
            ),
        ),
        "surrender_terms": (
            surrender_terms_path.resolve(),
            _expected_sha256(surrender_terms_sha256, "surrender terms SHA-256"),
        ),
    }
    values = {
        name: _load(path, sha256, name)
        for name, (path, sha256) in inputs.items()
    }
    comparison = provide_raiktor_same_frame_white_peace_comparison(
        source_checkpoint_value=values["source_checkpoint"],
        white_peace_observation_value=values["white_peace_observation"],
        surrender_terms_value=values["surrender_terms"],
    )
    artifact = {
        "schema": OUTPUT_SCHEMA,
        "status": comparison["status"],
        "inputs": {
            name: {"path": str(path), "sha256": sha256}
            for name, (path, sha256) in inputs.items()
        },
        "comparison": comparison,
        "boundaries": {
            "ck3_started_or_attached": False,
            "bridge_queried": False,
            "mutation_commands": [],
            "production_live": False,
            "production_recommendation_ready": False,
            "action_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    return artifact


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--source-checkpoint-sha256", required=True)
    parser.add_argument("--white-peace-observation", type=Path, required=True)
    parser.add_argument("--white-peace-observation-sha256", required=True)
    parser.add_argument("--surrender-terms", type=Path, required=True)
    parser.add_argument("--surrender-terms-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result = prepare_comparison_artifact(
            source_checkpoint_path=arguments.source_checkpoint,
            source_checkpoint_sha256=arguments.source_checkpoint_sha256,
            white_peace_observation_path=arguments.white_peace_observation,
            white_peace_observation_sha256=(
                arguments.white_peace_observation_sha256
            ),
            surrender_terms_path=arguments.surrender_terms,
            surrender_terms_sha256=arguments.surrender_terms_sha256,
            output_path=arguments.output,
        )
    except (ComparisonArtifactError, SameFrameWhitePeaceComparisonError) as error:
        print(f"RED: {error}")
        return 2
    print(
        f"{result['status']} "
        "production_live=false action_ready=false gen034_closed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
