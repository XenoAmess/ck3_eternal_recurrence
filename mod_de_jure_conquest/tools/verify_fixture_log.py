"""Verify existing fixture logs, including three fresh tiers; never launch or sign off."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from typing import Literal, Sequence, TypedDict

from gen_acceptance_fixture import BEGIN_MARKER, CLAIMS_EXCLUDED, DONE_MARKER, Tier, expected_markers, reviewed_tier

BOUNDARY = "Log markers only; fresh scene/runtime/EXE, actual date/paused window, error.log, protected-storage and normal exit require separate evidence. No GUI/payment/SaveLoad/full-product qualification."


@dataclass(frozen=True)
class ParsedContract:
    tier: Tier
    layer: str
    markers: tuple[str, ...]
    claims_excluded: tuple[str, ...]


class SingleReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: str
    player_history_id: int
    tier: Tier
    expected_pass_count: int
    observed_pass_count: int
    observed_marker_counts: dict[str, int]
    errors: list[str]
    log: str
    log_sha256: str
    contract: str
    contract_sha256: str
    claims_excluded: list[str]
    boundary: str


class AggregateReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: str
    player_history_id: int
    expected_pass_count: int
    observed_pass_count: int
    observed_marker_counts: dict[str, int]
    errors: list[str]
    source_runs: list[SingleReport]
    claims_excluded: list[str]
    boundary: str


class InvalidReport(TypedDict):
    result: Literal["RED"]
    layer: Literal["fixture-input-rejected"]
    errors: list[str]
    boundary: str


def string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    result = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field} must be a list of strings")
        result.append(item)
    return result


def parse_contract(raw: bytes) -> ParsedContract:
    value: object = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture contract must be a JSON object")
    schema = value.get("schema")
    if schema not in ("djc.external-acceptance.v1", "djc.external-acceptance.v2"):
        raise ValueError("unsupported fixture contract schema")
    player = value.get("player_history_id")
    if type(player) is not int or player != 1128:
        raise ValueError("fixture player_history_id must be integer 1128")
    tier = reviewed_tier(value.get("tier", "all"))
    if schema == "djc.external-acceptance.v1" and tier != "all":
        raise ValueError("legacy v1 contract must retain the full all-tier marker set")
    markers = string_list(value.get("markers"), "markers")
    if markers != expected_markers(tier):
        raise ValueError("contract markers must match the exact original ordered tier predicates")
    exclusions = string_list(value.get("claims_excluded"), "claims_excluded")
    if not set(CLAIMS_EXCLUDED[:7]).issubset(exclusions):
        raise ValueError("contract must preserve original uncovered business obligations")
    if value.get("layer") != "scripted-war-production-CB" or value.get("requires_done_marker") != DONE_MARKER:
        raise ValueError("fixture layer or required DONE marker differs from the production-CB contract")
    if schema == "djc.external-acceptance.v2":
        bound = value.get("max_natural_days")
        nominal = value.get("nominal_completion_natural_day")
        expected_bound, expected_nominal = (48, 46) if tier == "all" else (18, 16)
        if type(bound) is not int or bound != expected_bound or type(nominal) is not int or nominal != expected_nominal:
            raise ValueError("fixture natural-day schedule differs from the reviewed tier bound")
        if value.get("fresh_start_date") != "1066.9.15":
            raise ValueError("fixture must start on the actual reviewed 1066.9.15 bookmark")
        latest = "1066.11.2" if tier == "all" else "1066.10.3"
        for field, expected in (("latest_date", latest), ("completion_event", "djct.800"), ("failure_event", "djct.900"), ("watchdog_event", "djct.901"), ("live", "NOT_RUN")):
            if value.get(field) != expected:
                raise ValueError(f"fixture {field} differs from the reviewed preparation contract")
        if type(value.get("pause_boundary")) is not str or type(value.get("fixture_isolation")) is not str:
            raise ValueError("fixture preparation and pause boundaries must be explicit strings")
    return ParsedContract(tier, "scripted-war-production-CB", tuple(markers), tuple(exclusions))


def verify(log: Path, contract: Path) -> SingleReport:
    data = log.read_bytes()
    raw_contract = contract.read_bytes()
    value = data.decode("utf-8-sig", errors="replace")
    definition = parse_contract(raw_contract)
    passes = Counter(re.findall(r"DJCT: TEST PASS ([A-Za-z0-9_]+)", value))
    failures = re.findall(r"DJCT: TEST FAIL ([A-Za-z0-9_]+)", value)
    errors = []
    if failures:
        errors.append("failure markers: " + ", ".join(failures))
    for marker in definition.markers:
        if passes[marker] != 1:
            errors.append(f"expected one PASS {marker}, observed {passes[marker]}")
    for marker in sorted(passes.keys() - set(definition.markers)):
        errors.append(f"unexpected PASS marker {marker}")
    if value.count(BEGIN_MARKER) != 1:
        errors.append("fixture BEGIN count differs from one")
    if value.count(DONE_MARKER) != 1:
        errors.append("fixture DONE count differs from one")
    if "DJCT: TEST STOP" in value:
        errors.append("fixture stopped at a known failure window")
    return {
        "result": "RED" if errors else "GREEN", "layer": definition.layer,
        "player_history_id": 1128, "tier": definition.tier,
        "expected_pass_count": len(definition.markers), "observed_pass_count": sum(passes.values()),
        "observed_marker_counts": dict(sorted(passes.items())), "errors": errors,
        "log": str(log.resolve()), "log_sha256": hashlib.sha256(data).hexdigest(),
        "contract": str(contract.resolve()), "contract_sha256": hashlib.sha256(raw_contract).hexdigest(),
        "claims_excluded": list(definition.claims_excluded), "boundary": BOUNDARY,
    }


def aggregate(inputs: Sequence[tuple[Path, Path]]) -> AggregateReport:
    if len(inputs) != 3 or len({log.resolve() for log, _ in inputs}) != 3 or len({contract.resolve() for _, contract in inputs}) != 3:
        raise ValueError("aggregation requires three distinct log/contract pairs from three fresh tier runs")
    reports = [verify(log, contract) for log, contract in inputs]
    if {report["tier"] for report in reports} != {"duchy", "kingdom", "empire"}:
        raise ValueError("aggregation requires exactly one duchy, one kingdom and one empire contract")
    errors = [f"{report['tier']}: {message}" for report in reports for message in report["errors"]]
    counts: Counter[str] = Counter()
    for report in reports:
        counts.update(report["observed_marker_counts"])
    for marker in expected_markers():
        if counts[marker] != 1:
            errors.append(f"aggregate expected one PASS {marker}, observed {counts[marker]}")
    if set(counts) != set(expected_markers()):
        errors.append("aggregate marker identity set differs from all original 72 predicates")
    return {
        "result": "RED" if errors else "GREEN", "layer": "scripted-war-production-CB-three-fresh-tiers",
        "player_history_id": 1128, "expected_pass_count": 72, "observed_pass_count": sum(counts.values()),
        "observed_marker_counts": dict(sorted(counts.items())), "errors": errors, "source_runs": reports,
        "claims_excluded": sorted({item for report in reports for item in report["claims_excluded"]}), "boundary": BOUNDARY,
    }


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, action="append", required=True)
    parser.add_argument("--contract", type=Path, action="append", required=True)
    parser.add_argument("--aggregate", action="store_true", help="three ordered --log/--contract pairs; exact original 72-marker union")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report already exists; use a fresh output")
    result: SingleReport | AggregateReport | InvalidReport
    try:
        if len(args.log) != len(args.contract):
            raise ValueError("each log needs its own corresponding contract")
        if args.aggregate:
            result = aggregate(list(zip(args.log, args.contract, strict=True)))
        elif len(args.log) == 1:
            result = verify(args.log[0], args.contract[0])
        else:
            raise ValueError("multiple logs require explicit --aggregate")
    except (OSError, UnicodeError, ValueError) as error:
        result = InvalidReport(result="RED", layer="fixture-input-rejected", errors=[str(error)], boundary=BOUNDARY)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
