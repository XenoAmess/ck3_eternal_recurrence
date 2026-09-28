#!/usr/bin/env python3
"""Read-only exact-EXE verifier for the private realm-law final terms reader."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_realm_law_enact_mutation_v1 import PeImage, VerificationError, file_sha256


EXPECTED_RESOURCES = (
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods",
)


def integer(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise VerificationError(f"expected integer, got {value!r}")


def verify(executable: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != "realm_law_final_terms_11906_abi":
        raise VerificationError("contract mismatch")
    build = manifest["build"]
    if executable.stat().st_size != integer(build["file_size"]):
        raise VerificationError("executable size mismatch")
    if file_sha256(executable) != build["sha256"]:
        raise VerificationError("executable SHA-256 mismatch")
    image = PeImage(executable)
    if image.machine != 0x8664 or image.image_base != integer(build["preferred_image_base"]):
        raise VerificationError("PE machine or preferred base mismatch")
    if image.image_size != integer(build["image_size"]):
        raise VerificationError("PE image size mismatch")
    if tuple(manifest["native_cost_slots"]) != EXPECTED_RESOURCES:
        raise VerificationError("native resource slot mapping mismatch")
    interaction_abi = json.loads(manifest_path.with_name(
        "pending_character_interaction_context_v1_abi.json").read_text(encoding="utf-8"))
    generic_costs = interaction_abi["generic_authored_costs"]
    if "0x2CDB7B0" not in generic_costs["native_evaluator"]:
        raise VerificationError("generic cost evaluator source mismatch")
    mapped = tuple(row["resource_key"] for row in generic_costs["mapping"])
    if mapped != EXPECTED_RESOURCES or tuple(row["slot"] for row in generic_costs["mapping"]) != tuple(range(10)):
        raise VerificationError("generic native resource ordinals mismatch")
    entries = manifest["entrypoints"]
    if integer(entries["cost_block_offset_from_law"]) != 0xCD8:
        raise VerificationError("cost block offset mismatch")
    if integer(entries["native_cost_raw_scale"]) != 100000 or integer(entries["native_cost_slot_count"]) != 10:
        raise VerificationError("cost scale or slot count mismatch")

    functions = image.runtime_functions()
    reports: list[str] = []
    for span in manifest["instruction_spans"]:
        start, end = integer(span["rva"]), integer(span["end_rva"])
        digest = hashlib.sha256(image.read_rva(start, end - start)).hexdigest().upper()
        if digest != span["sha256"]:
            raise VerificationError(f"instruction span mismatch: {span['name']}")
        if "runtime_function" in span:
            runtime = tuple(integer(value) for value in span["runtime_function"])
            if runtime not in functions:
                raise VerificationError(f"runtime function mismatch: {span['name']}")
        reports.append(f"{span['name']} exact")
    for call in manifest["relative_calls"]:
        site, target = integer(call["site"]), integer(call["target"])
        encoded = image.read_rva(site, 5)
        if encoded[0] != 0xE8:
            raise VerificationError(f"not a relative call: {site:#x}")
        actual_target = site + 5 + struct.unpack_from("<i", encoded, 1)[0]
        if actual_target != target:
            raise VerificationError(f"relative call target mismatch: {site:#x}")
    reports.append("relative call chain exact")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name(
        "realm_law_final_terms_11906_abi.json"))
    args = parser.parse_args()
    try:
        reports = verify(args.exe, args.manifest)
    except (OSError, ValueError, KeyError, VerificationError) as error:
        print(f"RED realm-law final terms ABI: {error}")
        return 1
    for report in reports:
        print(f"GREEN {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
