"""Offline qualification for the patch3 materialized fullscreen event reader.

This replaces only the event-window source slice of the historical .2 ABI
reuse ledger. It neither reads a process nor executes any native function.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from verify_ck3_12002_migration import OfflineVerifier, read_json
from verify_ck3_12003_abi_reuse import TARGET_SHA256

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "ck3_1_20_0_3_fullscreen_event_context.json"


def verify(exe: Path) -> dict:
    manifest = read_json(MANIFEST)
    failures = []
    if (manifest.get("contract") != "ck3-1.20.0.3-fullscreen-event-context-v1"
            or manifest.get("build", {}).get("sha256") != TARGET_SHA256):
        failures.append("fullscreen manifest is not the reviewed exact patch3 contract")
    baseline = HERE / manifest["baseline_manifest"]
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != manifest["baseline_manifest_sha256"]:
        failures.append("historical baseline manifest changed")
    result = {}
    if not failures:
        verifier = OfflineVerifier(exe)
        result = verifier.verify_module({
            "id": "fullscreen-event-context",
            "manifest": MANIFEST.name,
            "source_hash_policy": "git-lf-with-bom",
            "source_git_lf_sha256": manifest["source_files"],
        })
        failures.extend(result["failures"])
    return {
        "schema_version": 1,
        "status": "RED" if failures else "GREEN",
        "scope": "exact patch3 fullscreen event context offline ABI and source",
        "target_executable_sha256": TARGET_SHA256.lower(),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "checks": result.get("checks", {}),
        "source_hash_policy": "git-lf-with-bom",
        "live_validation_executed": False,
        "native_functions_executed": False,
        "full_campaign_acceptance_claimed": False,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.exe)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
    print(encoded, end="")
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
