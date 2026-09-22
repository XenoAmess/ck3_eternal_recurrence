"""Freeze three reviewed consumer/caller chains, not an automatic semantic proof."""
import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--research-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    research = args.research_dir.resolve()
    out = args.artifact_dir.resolve()
    contract_path = research / "war_film_retreat_evidence_a04.json"
    result_path = research / "war_film_retreat_results_plan_a04.json"
    if contract_path.exists() or result_path.exists():
        raise FileExistsError("a04 output already exists")
    sources = []
    for source in [research / name for name in (
        "war_film_retreat_extract.py", "war_film_retreat_freeze_a04.py", "war_film_retreat_plan_a04.json")
    ] + [out.parent / "retreat-a01/initial-functions.json"]:
        target = out / ("source-snapshot-" + source.name)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        sources.append({"path": str(target), "original_path": str(source),
                        "sha256": sha(target), "size": target.stat().st_size})
    artifacts = []
    extracts = {}
    for path in sorted(out.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        extracts[path.name] = value
        if path.name.startswith("source-snapshot-"):
            continue
        if "exe_sha256" in value and value["exe_sha256"] != EXE_SHA:
            raise ValueError("EXE identity mismatch: " + str(path))
        artifacts.append({"path": str(path), "sha256": sha(path), "size": path.stat().st_size})
    selections = {
        "winner-transition-complete.json": [(0x230A071, 0x230A080), (0x230A0D7, 0x230A0E4),
                                              (0x230A15B, 0x230A162), (0x230A25D, 0x230A27B)],
        "consumer-parent-functions.json": [(0x2309EA6, 0x2309EE5), (0x24E1B5C, 0x24E1B72),
                                              (0x24E3B6C, 0x24E3B93), (0x24E3CA8, 0x24E3D08),
                                              (0x24E3D45, 0x24E3D4C)],
        "full-side-complete.json": [(0x2309138, 0x2309154), (0x2309278, 0x230929F)],
        "source-snapshot-initial-functions.json": [(0x18721EB, 0x187220F), (0x1872338, 0x187234D)],
        "selected-first-windows.json": [(0x187390B, 0x1873935), (0x1873A44, 0x1873A55)],
        "subset-upstream.json": [(0x24E56AF, 0x24E56C5)],
        "subset-relation-predicate.json": [(0x230B658, 0x230B69A)],
        "subset-consumer.json": [(0x23CAA2C, 0x23CAA6D), (0x23CAB6F, 0x23CAB88),
                                  (0x23CAC1C, 0x23CAC2D)],
    }
    excerpts = {}
    for name, ranges in selections.items():
        rows = []
        for function in extracts[name].get("functions", []):
            for row in function["instructions"]:
                rva = int(row.split()[0], 16)
                if any(lo <= rva <= hi for lo, hi in ranges):
                    rows.append(row)
        if not rows:
            raise ValueError("missing excerpt: " + name)
        excerpts[name] = rows
    claims = [
        {"id": "winner_transition", "status": "static-confirmed",
         "meaning": "230A010 writes winner before querying loser retreat legality; transition is pursuit/done, not an AI choice.",
         "spine": ["2309ECA/2309EE5 -> 230A010", "230929F -> 230A010", "230A080 winner", "230A162 phase3", "230A264 phase2"]},
        {"id": "known_move_caller_excludes_active", "status": "static-confirmed",
         "meaning": "The verified direct 1872348 caller is gated out by 1872208/187220F active combat test.",
         "limit": "Does not exclude unknown indirect callers or all queue timing changes."},
        {"id": "succession_subset", "status": "static-confirmed",
         "meaning": "24E3D08 belongs to ExecuteSuccessionWithTheocracyLeaseFreeze; no opposing relation match triggers subset extraction at current province with fifth bool false.",
         "spine": ["24E56C5 -> 24E1A60", "24E3CEA -> 230B570", "230B65E -> 2900470", "24E3CF1 true skips", "24E3D08 -> 23CA360"]},
        {"id": "optional_subset_pursuit", "status": "static-confirmed",
         "meaning": "23CAA37 skips 23CAA6D pursuit when fifth bool is false; succession passes false."},
        {"id": "generic_active_policy", "status": "unknown",
         "meaning": "Three bounded chains classified. No global absence proof or attributable ordinary AI retreat case."},
    ]
    contract = {"schema": "xar.war-film-retreat-research-evidence.v1", "package": "a04",
                "proof_layer": "human-reviewed-exact-build-static-chain", "version": "1.19.0.6", "exe_sha256": EXE_SHA,
                "live_execution_performed": False, "automatic_semantic_verification": False,
                "production_mcp_capability_added": False, "prior_packages_modified": False,
                "claims": claims, "artifacts": artifacts, "source_snapshots": sources,
                "reviewed_instruction_excerpts": excerpts,
                "direct_census": extracts["selected-consumer-refs.json"],
                "business_name_data": extracts["subset-context-strings.json"],
                "limits": ["at most three chains", "unverified2306507 byte candidate excluded",
                           "pdata fragments are not semantic function boundaries", "no full indirect/vtable census",
                           "2900470 formal relation enum remains unknown", "no live choice or outcome"]}
    write_new(contract_path, contract)
    plan = json.loads((research / "war_film_retreat_plan_a04.json").read_text(encoding="utf-8"))
    plan["topic"] = "war-film-active-retreat-policy-results-a04"
    plan["observation"]["producer"] = "Classified winner transition, known active-gated movement caller and succession subset cleanup; generic AI choice remains unknown."
    plan["observation"]["caller"] = "2309E80/2309070;18721B0;24E53A0/24E1A60"
    plan["evidence"] = [{"id": "reviewed_a04", "layer": "source-contract", "path": contract_path.name,
                         "sha256": sha(contract_path), "exe_sha256": EXE_SHA,
                         "supports": "Bounded classified upstreams and negative reachability; no generic AI absence claim."}]
    plan["nodes"] += [{"id": "classification", "label": "Settlement / active gate / succession cleanup"}]
    plan["edges"] = [
        {"id": edge_id, "from": source, "to": "classification", "label": label,
         "status": "static-confirmed", "evidence": ["reviewed_a04"], "open_question": None}
        for edge_id, source, label in (
            ("winner_classified", "legality_wrapper", "Winner precedes legality and pursuit/done"),
            ("active_excluded", "move_candidate", "Known direct caller returns on active combat before builder"),
            ("subset_classified", "side_retreat", "Move apply or succession cleanup; latter skips pursuit"))]
    plan["edges"].append({"id": "generic_unknown", "from": "classification", "to": "policy",
                          "label": "No ordinary odds-to-retreat policy established by these chains",
                          "status": "unknown", "evidence": ["reviewed_a04"],
                          "open_question": "Classify remaining indirect movement producers that read active combat and prediction."})
    write_new(result_path, plan)
    print(json.dumps({"contract": str(contract_path), "sha256": sha(contract_path),
                      "artifacts": len(artifacts), "source_snapshots": len(sources)}, indent=2))


if __name__ == "__main__":
    main()
