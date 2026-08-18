#!/usr/bin/env python3
"""Run the four passive CK3 balance fixtures serially and aggregate reports."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_acceptance.py"
FIXTURES = ("count", "king", "emperor", "synthetic")


def markdown_report(matrix):
    lines = [
        "# Passive Balance Matrix",
        "",
        f"- Started UTC: `{matrix['started_at_utc']}`",
        f"- Result: **{matrix['result']}**",
        "- Protocol: first blessing A and curse A; no strategic actions, shop purchases, contracts, refusals, rerolls, or seals.",
        "- Endpoint: natural death after year 30, early death if it occurs, otherwise right-censored at year 40.",
        "- Scope: instrumented engineering samples, not strategic play or statistical proof.",
        "",
        "| Fixture | Endpoint | Years reached | Pairs | Growth score | Absolute score | Realm | Runner |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for cell in matrix["cells"]:
        evidence = cell.get("scenario_evidence", {})
        samples = evidence.get("samples", [])
        elapsed = samples[-1].get("elapsed_days") if samples else None
        years = f"{elapsed / 365:.1f}" if elapsed is not None else "n/a"
        lines.append(
            f"| {cell['fixture']} | {evidence.get('end_reason', 'n/a')} | "
            f"{years} | {evidence.get('completed_pairs', 'n/a')} | "
            f"{evidence.get('final_score', 'n/a')} | "
            f"{evidence.get('final_absolute_score', 'n/a')} | "
            f"{evidence.get('final_realm_size', 'n/a')} | {cell['result']} |")
    lines.extend([
        "",
        "## Interpretation Guardrails",
        "",
        "- Historical starts differ in attributes, family, titles, resources, realm, wars, and random events; rank is not the only changed variable.",
        "- The synthetic cell is a controlled scripted Ota-title replacement, not native Ruler Designer.",
        "- GREEN means the fixture, cadence, passive policy, sampling, restoration, and zero-XAR-error gates completed. It does not mean the values are balanced.",
        "- Pair 10 should expose one reroll. A seal is not naturally reachable before pair 20, around year 57, outside this matrix.",
        "",
    ])
    return "\n".join(lines)


def main(fixtures, artifacts_dir=None):
    started_at = datetime.now(timezone.utc).isoformat()
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        artifacts.mkdir(parents=True, exist_ok=False)
    else:
        artifacts = Path(tempfile.mkdtemp(prefix="xar_balance_matrix_"))

    cells = []
    for fixture in fixtures:
        cell_dir = artifacts / fixture
        command = [
            sys.executable,
            str(RUNNER),
            "--scenario", "balance-long",
            "--balance-fixture", fixture,
            "--artifacts-dir", str(cell_dir),
        ]
        print(f"\n===== BALANCE CELL {fixture} =====", flush=True)
        completed = subprocess.run(command, cwd=ROOT)
        report_path = cell_dir / "report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        else:
            report = {
                "result": "RED",
                "error_reason": "runner did not write report.json",
            }
        cells.append({
            "fixture": fixture,
            "runner_exit_code": completed.returncode,
            **report,
        })

    result = "GREEN" if all(
        cell["runner_exit_code"] == 0 and cell.get("result") == "GREEN"
        for cell in cells) else "RED"
    matrix = {
        "schema_version": 1,
        "started_at_utc": started_at,
        "result": result,
        "protocol": "passive-first-options-v1",
        "fixtures": list(fixtures),
        "cells": cells,
        "minimum_horizon_cells": sum(
            bool(cell.get("scenario_evidence", {}).get("reached_minimum_horizon"))
            for cell in cells),
    }
    (artifacts / "balance-matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (artifacts / "balance-matrix.md").write_text(
        markdown_report(matrix), encoding="utf-8", newline="\n")
    print(f"\nMatrix report: {artifacts / 'balance-matrix.md'}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run serial CK3 passive balance cells")
    parser.add_argument(
        "--fixtures", nargs="+", choices=FIXTURES, default=list(FIXTURES),
        help="serial fixture subset (default: all four)")
    parser.add_argument(
        "--artifacts-dir",
        help="create this exact matrix artifact directory")
    args = parser.parse_args()
    sys.exit(main(args.fixtures, args.artifacts_dir))
