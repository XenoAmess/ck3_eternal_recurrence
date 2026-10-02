"""Verify an existing fixture log; this does not launch, sign off, or publish."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


def verify(log: Path, contract: Path) -> dict:
    data = log.read_bytes()
    value = data.decode("utf-8-sig", errors="replace")
    definition = json.loads(contract.read_text(encoding="utf-8"))
    passes = Counter(re.findall(r"DJCT: TEST PASS ([A-Za-z0-9_]+)", value))
    failures = re.findall(r"DJCT: TEST FAIL ([A-Za-z0-9_]+)", value)
    expected = definition["markers"]
    errors = []
    if failures:
        errors.append("failure markers: " + ", ".join(failures))
    for marker in expected:
        if passes[marker] != 1:
            errors.append(f"expected one PASS {marker}, observed {passes[marker]}")
    if value.count("DJCT: TEST BEGIN scripted-war-1128") != 1:
        errors.append("fixture BEGIN count differs from one")
    if value.count(definition["requires_done_marker"]) != 1:
        errors.append("fixture DONE count differs from one")
    return {
        "result": "RED" if errors else "GREEN",
        "layer": definition["layer"],
        "player_history_id": definition["player_history_id"],
        "expected_pass_count": len(expected),
        "observed_pass_count": sum(passes.values()),
        "errors": errors,
        "log": str(log.resolve()), "log_sha256": hashlib.sha256(data).hexdigest(),
        "contract": str(contract.resolve()), "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
        "claims_excluded": definition["claims_excluded"],
        "boundary": "Log markers only; requires separate exact-build/runtime identity, error.log and protected-storage/exit validation.",
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report already exists; use a fresh output")
    result = verify(args.log, args.contract)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
