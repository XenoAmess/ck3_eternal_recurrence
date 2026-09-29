#!/usr/bin/env python3
"""Exact-build, disk-only H2743 pre-action truce ABI probe.

The underlying extractor authenticates ck3.exe bytes, PE metadata, eight
bounded native ranges and their call edges. This H2743 projection admits only
an existing, already applied attacker-to-defender relation as a future live
read candidate. It never claims to observe the result of surrender.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import extract_g2_actual_truce_expiry_abi as native


CHECKPOINT_SHA256 = "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9"
WAR_ID = 16777231
ATTACKER_ID = 30097
DEFENDER_ID = 29829
EXISTING_READER_SOURCE_SHA256 = "9074C83277697F1F652FB7216BDA4647694AC1EF545BCD5F483055AFEC4C747C"

EXPECTED_BINDINGS = {
    "read_only_relation_lookup_rva": "0x2610840",
    "get_or_create_relation_rva": "0x26108F0",
    "has_truce_rva": "0x26631E0",
    "get_truce_end_date_rva": "0x2663250",
    "caddtruce_duration_evaluator_rva": "0x3373000",
}


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def project_probe(
    abi: dict[str, Any], *, owner_character_id: int = ATTACKER_ID,
    toward_character_id: int = DEFENDER_ID,
    claimed_existing_expiry_date_raw: int | None = None,
    claimed_post_surrender_expiry_date_raw: int | None = None,
) -> dict[str, Any]:
    """Project authenticated ABI metadata, never a live game observation."""
    _require(type(owner_character_id) is int and owner_character_id == ATTACKER_ID,
             "H2743 current-slot owner must be the full attacker ID")
    _require(type(toward_character_id) is int and toward_character_id == DEFENDER_ID,
             "H2743 current-slot target must be the full defender ID")
    _require(claimed_existing_expiry_date_raw is None,
             "disk probe cannot authenticate an existing live relation slot")
    _require(claimed_post_surrender_expiry_date_raw is None,
             "post-surrender expiry cannot be observed before surrender")
    _require(abi.get("schema") == "xar.ck3.g2_actual_truce_expiry_abi.v1",
             "wrong native ABI schema")
    _require(abi.get("build", {}).get("executable_sha256") == native.EXPECTED_SHA256,
             "wrong exact CK3 executable")
    _require(abi.get("read_only") is True and abi.get("default_enabled") is False,
             "native candidate is not read-only and default-off")
    _require(abi.get("status") == "static-ready_live-pending",
             "native candidate status changed")
    bindings = abi.get("bindings", {})
    for name, expected in EXPECTED_BINDINGS.items():
        _require(bindings.get(name) == expected, f"native binding changed: {name}")
    _require(bindings.get("directional_slot_offsets") == ["0x28", "0x58"],
             "directional truce slots changed")
    ranges = abi.get("native_ranges", {})
    for name, (start, end) in native.RANGES.items():
        row = ranges.get(name, {})
        _require(
            row.get("begin_rva") == f"0x{start:X}"
            and row.get("end_rva_exclusive") == f"0x{end:X}"
            and row.get("size") == end - start
            and row.get("sha256") == native.EXPECTED_RANGE_HASHES[name],
            f"native byte range changed: {name}",
        )
    candidate = abi.get("candidate", {})
    _require(candidate.get("owner_binding") == "living current played character",
             "existing reader owner binding changed")
    _require(candidate.get("owner_arbitrary_selection") is False,
             "existing reader arbitrary-owner claim changed")
    _require(candidate.get("ack_can_make_ready") is False,
             "candidate readiness contract changed")
    source_sha = abi.get("source_sha256", {}).get(
        "src/raiktor_actual_truce_expiry_v1.cpp")
    _require(source_sha == EXISTING_READER_SOURCE_SHA256,
             "existing reader implementation changed")
    temporal = abi.get("temporal_split", {})
    _require("prediction, not persisted-state observation" in
             temporal.get("before_application", ""),
             "before-application temporal boundary changed")
    _require("persisted owner-direction date" in temporal.get("after_application", ""),
             "after-application temporal boundary changed")

    return {
        "schema": "xar.ck3.h2743_preaction_truce_abi_probe.v1",
        "status": "static_abi_candidate_only",
        "checkpoint_sha256_claim": CHECKPOINT_SHA256,
        "checkpoint_bytes_authenticated_here": False,
        "target_frame_claim": {
            "snapshot_id": "native:3",
            "public_revision": 4,
            "native_revision": 3,
            "date_raw": 53217264,
            "connection_generation": 1,
        },
        "exe_sha256": native.EXPECTED_SHA256,
        "exe_bytes_authenticated_here": False,
        "native_call_edges_authenticated_here": False,
        "war_id": WAR_ID,
        "owner_character_id": ATTACKER_ID,
        "toward_character_id": DEFENDER_ID,
        "read_only_native_call_rvas": {
            "has_truce": bindings["has_truce_rva"],
            "get_truce_end_date": bindings["get_truce_end_date_rva"],
            "relation_lookup": bindings["read_only_relation_lookup_rva"],
        },
        "forbidden_query_call_rvas": {
            "relation_get_or_create": bindings["get_or_create_relation_rva"],
            "caddtruce_duration_evaluator": bindings["caddtruce_duration_evaluator_rva"],
        },
        "existing_reader_owner_binding": "current_played_character_only",
        "new_arbitrary_owner_provider_required": True,
        "same_frame_live_observed": False,
        "preaction_existing_truce_expiry_date_raw": None,
        "post_surrender_actual_expiry_date_raw": None,
        "script_candidate_days": None,
        "effect_projection_complete": False,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
        "unavailable_reason": "no_authenticated_arbitrary_owner_live_read_or_post_action_state",
    }


def build_report(exe: Path, native_root: Path) -> dict[str, Any]:
    # extract() checks exact EXE bytes, PE metadata, eight ranges and direct
    # call edges before any H2743-specific result is projected.
    result = project_probe(native.extract(exe, native_root))
    result["exe_bytes_authenticated_here"] = True
    result["native_call_edges_authenticated_here"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name(
                            "h2743_preaction_truce_abi_probe_v1.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = build_report(args.exe.resolve(), Path(__file__).resolve().parents[1])
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
                raise ValueError("H2743 preaction truce ABI probe artifact is stale")
            print("OK: H2743 exact-build static truce ABI probe")
        else:
            if args.output.exists():
                raise ValueError("refusing to overwrite an existing ABI probe artifact")
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
            print(args.output)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "RED", "reason": str(error),
                          "effect_projection_complete": False,
                          "action_literal": None}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
