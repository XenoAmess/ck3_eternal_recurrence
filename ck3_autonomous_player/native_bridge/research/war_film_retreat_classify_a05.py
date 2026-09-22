"""Classify every hit of the frozen move-vtable RIP census, not native semantics.

Labels are reviewed research annotations. Completeness means every hit in the
declared input census has a label; it does not mean every possible native caller.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


CLASSIFICATIONS = {
    "0xa83fb0": ("player_map_input", "new-a05", "CIngameInterfaceHandler input -> kind1, queue flags14; target from interface+16A90"),
    "0x186b190": ("shared_ai_move_builder", "a01", "Callers include ordinary representative and mission families; builder capability is not a retreat policy"),
    "0x18721b0": ("ordinary_representative_move", "a01", "1872208/187220F active-combat gate returns before construction"),
    "0x18726c0": ("ordinary_follower_move", "a01", "1872916/187291D active-combat gate skips the unit before construction"),
    "0x1873100": ("ordinary_route_replan", "a04", "Only verified direct parent1872348 inherits representative active gate"),
    "0x1874a10": ("current_province_route_cancel", "a02", "Known stack merge/cancel sources; no attributed odds-to-active-retreat choice"),
    "0x18793b0": ("mission_return", "a02", "Known callers belong to raid/barter return and cleanup"),
    "0x18cb790": ("counterraid_target_move", "inherited-active-topic", "Mission target pursuit; counterraid active reachability is not negated"),
    "0x18ce530": ("raid_mission_move", "a02", "Known main caller has active exclusion; no expansion in a05"),
    "0x18d0da0": ("barter_mission_move", "a02", "Known main caller has active exclusion; no expansion in a05"),
    "0x23c9f00": ("postcombat_loser_route", "inherited-terminal-topic", "230AEF6 terminal caller; route/state after battle, not voluntary policy"),
    "0x26c1e50": ("heap_clone", "new-a05", "Primary vtable+40 slot; copies existing command payload and route"),
    "0x26c6f80": ("empty_heap_factory", "new-a05", "Allocates168 bytes, invalid Unit ID and empty route; consumer provenance unresolved"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.census.read_bytes()
    census = json.loads(raw)
    if census["exe_sha256"] != "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86":
        raise ValueError("unexpected EXE identity")
    grouped = {}
    for row in census["rip_references"]:
        function = row["runtime_function"][0]
        if function not in CLASSIFICATIONS:
            raise ValueError("unclassified input function: " + function)
        grouped.setdefault(function, []).append(row)
    if set(grouped) != set(CLASSIFICATIONS):
        raise ValueError("input census differs from reviewed 13-function inventory")
    rows = []
    for function in sorted(grouped, key=lambda value: int(value, 0)):
        label, source, boundary = CLASSIFICATIONS[function]
        rows.append({"runtime_function": function, "classification": label, "evidence_package": source,
                     "boundary": boundary, "reference_count": len(grouped[function]), "references": grouped[function]})
    result = {"schema": "xar.war-film-retreat-constructor-classification.v1",
              "proof_layer": "reviewed-labels-over-exact-build-census", "exe_sha256": census["exe_sha256"],
              "census_path": str(args.census.resolve()), "census_sha256": hashlib.sha256(raw).hexdigest(),
              "declared_range": census["range"], "targets": census["targets"],
              "reference_count": len(census["rip_references"]), "containing_function_count": len(rows),
              "references_per_target": dict(Counter(row["target"] for row in census["rip_references"])),
              "every_input_hit_classified": True, "all_possible_producers_proven": False,
              "live_execution_performed": False, "automatic_semantic_verification": False, "functions": rows,
              "limits": ["Only decoded pdata ranges in the declared interval", "No RIP-relative memory alias recovery",
                         "Runtime factory/clone consumers are not fully recovered", "Counterraid is not ordinary war policy"]}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "references": result["reference_count"],
                      "functions": len(rows), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
