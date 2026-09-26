"""Bind CK3's pre-schedule per-regiment stat refresh to two live battle days.

The exact-build call chain proves that cache fields are reassigned before
schedule. The live comparison proves changed cached values; it does not infer
which trait, terrain, commander, or other source modifier caused each change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EDGES = (
    (0x27FB57A, 0x2308D50),  # per-combat refresh before schedule
    (0x27FB58F, 0x23C8750),  # side0 schedule
    (0x2308D66, 0x23CBCE0),
    (0x2308D72, 0x23CBCE0),
    (0x2308D82, 0x23CC2B0),
    (0x2308D95, 0x23CC2B0),
    (0x23CC2E8, 0x23D2CE0),
    (0x23CC316, 0x23D2CE0),
    (0x23D2D2F, 0x239CAE0),
)
WRITES = (
    (0x23D2D46, b"\x48\x89\x4b\x40", "entry+0x40 effective damage"),
    (0x23D2D4E, b"\x48\x89\x4b\x48", "entry+0x48 effective toughness"),
)
CASES = {
    11: ("d11r2", 53146488, 22),
    21: ("d21", 53146728, 28),
}


def _read(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def _static_check(exe: Path) -> dict:
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != EXE_SHA256:
        raise ValueError("CK3 executable differs from the 1.19.0.6 exact build")
    pe = pefile.PE(data=raw, fast_load=True)
    edges = []
    for site, target in EDGES:
        data = pe.get_data(site, 5)
        if len(data) != 5 or data[0] != 0xE8:
            raise ValueError(f"missing direct call at {site:#x}")
        observed = site + 5 + int.from_bytes(data[1:], "little", signed=True)
        if observed != target:
            raise ValueError(f"call target drift at {site:#x}: {observed:#x}")
        edges.append({"callsite_rva": f"0x{site:X}", "target_rva": f"0x{target:X}"})
    writes = []
    for site, expected, meaning in WRITES:
        if pe.get_data(site, len(expected)) != expected:
            raise ValueError(f"entry stat writer drift at {site:#x}")
        writes.append({"site_rva": f"0x{site:X}", "bytes_hex": expected.hex().upper(),
                       "meaning": meaning})
    return {"exe_sha256": EXE_SHA256, "direct_edges": edges, "stat_field_writes": writes,
            "refresh_call_precedes_side0_schedule_in_same_loop": True}


def _regiment_map(rows: list[dict], role: str) -> dict[int, dict]:
    result = {}
    for row in rows:
        regiment_id = row["regiment_id"]
        if regiment_id in result:
            raise ValueError(f"duplicate regiment in {role}: {regiment_id}")
        result[regiment_id] = row
    return result


def project(attempt: Path, source_day: int, exe: Path) -> dict:
    prefix, date_raw, candidate = CASES[source_day]
    base = attempt / "ck3-output/interactive-requests-responses"
    control_receipt, control_sha = _read(base / f"{prefix}-before-control.json")
    finish_receipt, finish_sha = _read(base / f"{prefix}-finish.json")
    if (control_receipt.get("result") != "CALL_COMPLETED"
            or finish_receipt.get("result") != "CALL_COMPLETED"):
        raise ValueError("live source response incomplete")
    control = control_receipt["body"]["battle_control_snapshot"]
    finish = finish_receipt["body"]
    trace = finish["managed_trace"]["trace"]
    records = trace["records"]
    if (control["combat_id"] != 16777218
            or control["observed_date_raw"] != date_raw
            or finish["status"] != "bounded_trace_available"
            or trace["failure_flags"] != 0 or len(records) != 7
            or records[0]["boundary"] !=
            "native_capture_before_side0_schedule_call_0x27FB58F"
            or records[0]["native_date_raw"] != date_raw
            or candidate in [a["army_id"] for a in records[0]["sides"][0]["armies"]]):
        raise ValueError("live pre-schedule boundary identity drifted")
    changes = []
    side_census = []
    for index, role in enumerate(("attacker", "defender")):
        previous = _regiment_map(
            [*control[role]["levy_entries"], *control[role]["men_at_arms_entries"]],
            f"control {role}",
        )
        refreshed = _regiment_map(records[0]["sides"][index]["regiments"],
                                  f"schedule side{index}")
        if previous.keys() != refreshed.keys():
            raise ValueError(f"regiment identity changed before schedule on side{index}")
        side_census.append({"side_index": index, "regiment_count": len(previous)})
        for regiment_id, before in previous.items():
            after = refreshed[regiment_id]
            old_damage = before["effective_damage_raw"]
            new_damage = after["effective_damage_raw"]
            old_toughness = before["effective_toughness_raw"]
            new_toughness = after["effective_toughness_raw"]
            if (old_damage, old_toughness) != (new_damage, new_toughness):
                changes.append({"side_index": index, "regiment_id": regiment_id,
                                "old_damage_raw": old_damage,
                                "new_damage_raw": new_damage,
                                "old_toughness_raw": old_toughness,
                                "new_toughness_raw": new_toughness})
    changes.sort(key=lambda row: (row["side_index"], row["regiment_id"]))
    return {"schema": "ck3.native_pre_schedule_stat_refresh.v1",
            "game_build": "1.19.0.6", "source_day": source_day,
            "combat_id": 16777218, "date_raw": date_raw,
            "control_response_sha256": control_sha, "finish_response_sha256": finish_sha,
            "static_call_chain": _static_check(exe),
            "side_census": side_census,
            "changed_regiment_count": len(changes), "changed_regiments": changes,
            "per_regiment_cached_stats_reassigned_before_schedule": True,
            "specific_modifier_source_for_each_change_proven": False,
            "cross_manager_global_tick_order_proven": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--source-day", type=int, choices=sorted(CASES), required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.attempt, args.source_day, args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "changed_regiment_count": report["changed_regiment_count"],
                      "side_census": report["side_census"]}))


if __name__ == "__main__":
    main()
