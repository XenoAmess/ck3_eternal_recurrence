"""Verify the reviewed CK3 1.20.0.3 reuse of the 1.20.0.2 native ABI.

The old manifests and verifiers retain their original identity. This new entry
checks the exact .3 PE identity, pins the reviewed .2 contracts, and validates
their native evidence directly against .3. Supplemental byte, function, field,
vtable and RTTI regions come from the frozen compatibility comparison. Shared
evidence is counted once per exact region tuple, not as unique capabilities.
There is no process access, native execution or live-readiness claim.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from scan_anchors import integer
from verify_ck3_12002_migration import OfflineVerifier, read_json


HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "ck3_1_20_0_3_abi_reuse.json"
BASELINE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
TARGET_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_contract(contract: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Check the reviewed inventory without reading or scanning an EXE."""
    failures = []
    if contract["baseline_build"]["sha256"] != BASELINE_SHA256:
        failures.append("baseline identity differs from reviewed 1.20.0.2")
    if contract["target_build"]["sha256"] != TARGET_SHA256:
        failures.append("target identity differs from reviewed 1.20.0.3")
    index_pin = contract["baseline_index"]
    index_path = HERE / index_pin["manifest"]
    if file_sha256(index_path) != index_pin["sha256"]:
        failures.append("reviewed baseline migration index differs")
    index = read_json(index_path)
    if index["executable_sha256"] != BASELINE_SHA256:
        failures.append("baseline index executable identity differs")
    indexed = {entry["id"]: entry for entry in index["modules"]}
    reviewed = contract["reviewed_core_modules"]
    if set(indexed) != {entry["id"] for entry in reviewed}:
        failures.append("reviewed core module inventory differs")
    for entry in reviewed:
        if entry["id"] in indexed and entry["manifest"] != indexed[entry["id"]]["manifest"]:
            failures.append(f"core manifest mapping differs: {entry['id']}")
    all_entries = reviewed + contract["reviewed_extra_modules"] + contract["reference_only_records"]
    for entry in all_entries:
        if file_sha256(HERE / entry["manifest"]) != entry["manifest_sha256"]:
            failures.append(f"reviewed manifest differs: {entry['manifest']}")
    regions = contract["expected_regions"]
    for position, region in enumerate(regions):
        if (integer(region["rva"]) < 0 or region["size"] <= 0 or
                re.fullmatch(r"[0-9a-f]{64}", region["sha256"]) is None):
            failures.append(f"invalid frozen region record: {position}")
    globals_ = contract["zero_initialized_globals"]
    for entry in contract["reviewed_extra_modules"]:
        if any(index < 0 or index >= len(regions) for index in entry["region_indices"]):
            failures.append(f"invalid region reference: {entry['manifest']}")
        if any(index < 0 or index >= len(globals_) for index in entry["global_layout_indices"]):
            failures.append(f"invalid global layout reference: {entry['manifest']}")
    return index, failures


class TargetVerifier(OfflineVerifier):
    def __init__(self, exe: Path, contract: dict[str, Any]) -> None:
        super().__init__(exe)
        self.contract = contract

    def verify_target_build(self) -> list[str]:
        expected = self.contract["target_build"]
        failures = []
        if self.sha256 != TARGET_SHA256 or self.sha256 != expected["sha256"]:
            failures.append(f"target executable SHA differs: {self.sha256}")
        actual = {"file_size": len(self.data), "pe_timestamp": self.image.timestamp,
                  "image_base": self.image.image_base, "size_of_image": self.image.size_of_image}
        for key, value in actual.items():
            if value != integer(expected[key]):
                failures.append(f"target PE {key} differs")
        return failures

    def verify_build(self, manifest: dict[str, Any]) -> tuple[list[str], int]:
        # The core verifier's native/source checks are reused, while build
        # validation belongs to this new contract. Both baseline pinning above
        # and exact .3 identity verification occur before any semantic checks.
        build = manifest.get("build", {})
        baseline = build.get("sha256", manifest.get(
            "ck3_exe_sha256", manifest.get("executable_sha256")))
        if baseline is None or baseline.upper() != BASELINE_SHA256:
            return ["core manifest is not bound to the reviewed baseline"], 0
        return [], 0

    def verify_extra_regions(self) -> tuple[list[str], list[str]]:
        region_failures = []
        for position, region in enumerate(self.contract["expected_regions"]):
            raw = self.bytes_at(integer(region["rva"]), region["size"])
            if hashlib.sha256(raw).hexdigest() != region["sha256"]:
                region_failures.append(f"frozen supplemental region differs: {position} at {region['rva']}")
        global_failures = []
        for position, record in enumerate(self.contract["zero_initialized_globals"]):
            rva = integer(record["rva"])
            expected = tuple(record["section_layout"])
            actual = next((section for section in self.image.sections
                           if section[0] <= rva < section[0] + section[1]), None)
            if actual != expected:
                global_failures.append(f"zero-initialized global virtual layout differs: {position}")
        return region_failures, global_failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, help="Frozen CK3 1.20.0.3 executable")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--manifest-only", action="store_true",
                        help="Check inventory/pins only; performs no target EXE verification")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.manifest_only and args.exe is None:
        parser.error("--exe is required unless --manifest-only is used")
    contract = read_json(args.manifest)
    index, failures = verify_contract(contract)
    modules = []
    counts: Counter[str] = Counter()
    native_checked = False
    if not args.manifest_only and not failures:
        verifier = TargetVerifier(args.exe, contract)
        failures.extend(verifier.verify_target_build())
        if not failures:
            native_checked = True
            for entry in index["modules"]:
                result = verifier.verify_module(entry)
                # Historical manifest readiness is retained solely as input.
                result["historical_readiness"] = result.pop("readiness", None)
                result["historical_live_verified"] = result.pop("live_verified", None)
                result["target_live_verified"] = False
                modules.append(result)
                counts.update(result["checks"])
                failures.extend(f"{entry['id']}: {item}" for item in result["failures"])
            region_failures, global_failures = verifier.verify_extra_regions()
            failures.extend(region_failures + global_failures)
    report = {"schema_version": 1, "status": "RED" if failures else "GREEN",
              "scope": "manifest inventory only" if args.manifest_only else "exact .3 offline ABI verification",
              "baseline_executable_sha256": BASELINE_SHA256,
              "target_executable_sha256": TARGET_SHA256,
              "target_executable_verified": native_checked,
              "live_validation_executed": False, "native_functions_executed": False,
              "old_build_acceptance_claimed": False,
              "manifest_sha256": file_sha256(args.manifest),
              "core_modules": modules, "core_checks": dict(counts),
              "supplemental_exact_regions": len(contract["expected_regions"]) if native_checked else 0,
              "supplemental_virtual_globals": len(contract["zero_initialized_globals"]) if native_checked else 0,
              "reviewed_extra_contracts": len(contract["reviewed_extra_modules"]),
              "count_scope": contract["count_scope"], "failures": failures}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{report['status']}: {report['scope']}; live validation=False")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
