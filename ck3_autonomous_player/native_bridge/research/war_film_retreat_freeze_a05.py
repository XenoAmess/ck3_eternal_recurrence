"""Freeze reviewed move-command constructor evidence; no semantic/live proof."""
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
    root = research.parents[2]
    out = args.artifact_dir.resolve()
    contract_path = research / "war_film_retreat_evidence_a05.json"
    result_path = research / "war_film_retreat_results_plan_a05.json"
    if contract_path.exists() or result_path.exists():
        raise FileExistsError("a05 outputs already exist")
    sources = [research / name for name in (
        "war_film_retreat_extract.py", "war_film_retreat_score_locator.py", "war_film_retreat_vtable_a05.py",
        "war_film_retreat_classify_a05.py", "war_film_retreat_freeze_a05.py", "war_film_retreat_plan_a05.json",
        "war_film_retreat_evidence_a01.json", "war_film_retreat_evidence_a02.json", "war_film_retreat_evidence_a04.json")]
    sources += [root / "docs/ck3-native-ai" / name for name in (
        "active-combat-retreat.md", "battle-terminal-and-reentry.md")]
    snapshots = []
    for source in sources:
        target = out / ("source-snapshot-" + source.name)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        snapshots.append({"path": str(target), "original_path": str(source),
                          "sha256": sha(target), "size": target.stat().st_size})
    artifacts = []
    extracts = {}
    for path in sorted(out.glob("*.json")):
        if path.name.startswith("source-snapshot-"):
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if "exe_sha256" in value and value["exe_sha256"] != EXE_SHA:
            raise ValueError("EXE identity mismatch: " + str(path))
        artifacts.append({"path": str(path), "sha256": sha(path), "size": path.stat().st_size})
        extracts[path.name] = value
    excerpts = {}
    selections = {
        "new-constructor-functions.json": [(0xA84651, 0xA84674), (0xA8470F, 0xA84778),
                                           (0x26C1E50, 0x26C1EFB), (0x26C6F80, 0x26C7001)],
        "new-ui-upstream.json": [(0xA84C45, 0xA84CA5), (0xA84CDC, 0xA84CE8)],
    }
    for name, ranges in selections.items():
        rows = []
        for function in extracts[name].get("functions", []):
            for row in function["instructions"]:
                rva = int(row.split()[0], 16)
                if any(lo <= rva <= hi for lo, hi in ranges):
                    rows.append(row)
        if not rows:
            raise ValueError("missing reviewed excerpt: " + name)
        excerpts[name] = rows
    contract = {"schema": "xar.war-film-retreat-research-evidence.v1", "package": "a05",
                "version": "1.19.0.6", "exe_sha256": EXE_SHA,
                "proof_layer": "human-reviewed-exact-build-static-census-and-classification",
                "live_execution_performed": False, "automatic_semantic_verification": False,
                "production_mcp_capability_added": False, "prior_packages_modified": False,
                "artifacts": artifacts, "source_snapshots": snapshots, "reviewed_instruction_excerpts": excerpts,
                "vtables": extracts["verified-vtables.json"],
                "constructors": extracts["constructor-classification.json"],
                "ui_type_evidence": {name: extracts[name] for name in (
                    "new-ui-upstream-refs.json", "ui-vtable-neighborhood.json", "ui-rtti-col.json", "ui-rtti-type.json")},
                "claims": [
                    {"id": "actual_type", "status": "static-confirmed", "meaning": "RTTI CMoveUnitCommand, primary432BF18, secondary432BFB0 at object+18;432BF48 is validation slot, not address point."},
                    {"id": "constructor_census", "status": "static-confirmed", "meaning": "All29 decoded RIP hits across13 containing functions classified within declared pdata scan range."},
                    {"id": "new_provenance", "status": "static-confirmed", "meaning": "New paths bind player map input, payload clone and empty factory; none establishes ordinary active-retreat choice."},
                    {"id": "generic_policy", "status": "unknown", "meaning": "Unknown indirect producers and factory consumers remain; no attributable native AI retreat case."}],
                "limits": ["Scan classification completeness is not all-native-policy coverage",
                           "No alias/prototype-copy/indirect-producer recovery",
                           "No live command production, apply or postcondition observed",
                           "Factory consumer registration unresolved; not labeled network or deserialization"]}
    write_new(contract_path, contract)
    plan = json.loads((research / "war_film_retreat_plan_a05.json").read_text(encoding="utf-8"))
    plan["topic"] = "war-film-move-command-constructors-results-a05"
    plan["observation"]["producer"] = "29 declared RIP hits /13 functions classified; actual type CMoveUnitCommand; unknown dynamic producers remain."
    plan["observation"]["caller"] = "Known ordinary/mission paths reused; new CIngameInterfaceHandler, clone and empty factory classified."
    plan["evidence"] = [{"id": "reviewed_a05", "layer": "source-contract", "path": contract_path.name,
                         "sha256": sha(contract_path), "exe_sha256": EXE_SHA,
                         "supports": "Actual RTTI/address points and complete classification of declared scan hits, with bounded unknown policy."}]
    labels = {"apply_table": "Actual CMoveUnitCommand primary/secondary table and apply slot bound",
              "table_constructors": "29 of29 decoded RIP hits /13 functions classified"}
    for edge in plan["edges"]:
        edge["evidence"] = ["reviewed_a05"]
        if edge["id"] in labels:
            edge.update(status="static-confirmed", open_question=None, label=labels[edge["id"]])
        else:
            edge["open_question"] = "Unknown dynamic/factory consumers remain; no ordinary AI active-combat prediction-to-retreat choice recovered."
    write_new(result_path, plan)
    print(json.dumps({"contract": str(contract_path), "sha256": sha(contract_path),
                      "artifacts": len(artifacts), "source_snapshots": len(snapshots)}, indent=2))


if __name__ == "__main__":
    main()
