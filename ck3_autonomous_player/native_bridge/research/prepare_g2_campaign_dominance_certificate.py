#!/usr/bin/env python3
"""Render GEN-034-A from a hash-bound strategic-power live report."""

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

from xar_autoplayer.simulation.raiktor_campaign_dominance_provider import (  # noqa: E402
    provide_raiktor_campaign_dominance,
)


OUTPUT_SCHEMA = "xar.ck3.g2_campaign_dominance_receipt.v1"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def render_receipt(
    report_path: Path,
    report_sha256: str,
    *,
    reclassification_path: Path | None,
    reclassification_sha256: str | None,
    war_id: int,
    opponent_character_id: int,
) -> dict[str, object]:
    report_bytes = _read_bound(report_path, report_sha256, "report")
    report = _json(report_bytes, "report")
    if report.get("kind") != "ck3_active_war_strategic_power_live_acceptance":
        raise ValueError("report kind drifted")

    if report.get("ok") is not True:
        if reclassification_path is None or reclassification_sha256 is None:
            raise ValueError("RED report requires a bound GREEN reclassification")
        reclassification_bytes = _read_bound(
            reclassification_path, reclassification_sha256, "reclassification"
        )
        reclassification = _json(reclassification_bytes, "reclassification")
        _validate_reclassification(reclassification, report_sha256)
        reclassification_binding = {
            "path": str(reclassification_path.resolve()),
            "sha256": reclassification_sha256,
        }
    else:
        reclassification_binding = None

    sequence = _object(report.get("mcp_sequence"), "mcp_sequence")
    provider = provide_raiktor_campaign_dominance(
        sequence.get("before_snapshot"),
        sequence.get("first_query"),
        sequence.get("between_snapshot"),
        sequence.get("second_query"),
        sequence.get("after_snapshot"),
        war_id=war_id,
        opponent_character_id=opponent_character_id,
        source_artifact_sha256=report_sha256,
    )
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "GREEN",
        "ok": True,
        "source_report": {
            "path": str(report_path.resolve()),
            "sha256": report_sha256,
        },
        "reclassification": reclassification_binding,
        "provider_result": provider,
        "boundaries": {
            "ck3_started_or_attached": False,
            "bridge_queried": False,
            "mutation_commands": [],
            "campaign_outcome_forecast_ready": False,
            "exit_utility_ready": False,
            "action_ready": False,
        },
    }


def _validate_reclassification(value: dict[str, object], report_sha: str) -> None:
    source = _object(value.get("source_report"), "source_report")
    checks = _object(value.get("corrected_checks"), "corrected_checks")
    exact_build = _object(value.get("exact_build_proof"), "exact_build_proof")
    if (
        value.get("kind")
        != "ck3_active_war_strategic_power_live_acceptance_reclassification"
        or source.get("sha256") != report_sha
        or value.get("query_evidence") is None
        or not checks
        or any(check is not True for check in checks.values())
        or exact_build.get("ok") is not True
    ):
        raise ValueError("reclassification is not a complete GREEN correction")


def _read_bound(path: Path, expected_sha: str, name: str) -> bytes:
    expected = _sha256(expected_sha, f"{name}_sha256")
    payload = path.resolve().read_bytes()
    if hashlib.sha256(payload).hexdigest().upper() != expected:
        raise ValueError(f"{name} hash differs from expected SHA-256")
    return payload


def _json(payload: bytes, name: str) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} must be valid UTF-8 JSON") from exc
    return _object(value, name)


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be an uppercase SHA-256")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--report-sha256", required=True)
    parser.add_argument("--reclassification", type=Path)
    parser.add_argument("--reclassification-sha256")
    parser.add_argument("--war-id", type=int, required=True)
    parser.add_argument("--opponent-character-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if (args.reclassification is None) != (
        args.reclassification_sha256 is None
    ):
        parser.error("reclassification path and SHA-256 must be supplied together")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"output already exists: {output}")
    try:
        receipt = render_receipt(
            args.report,
            args.report_sha256,
            reclassification_path=args.reclassification,
            reclassification_sha256=args.reclassification_sha256,
            war_id=args.war_id,
            opponent_character_id=args.opponent_character_id,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
