"""Freeze reviewed a03 role/score evidence; does not verify native semantics.

Consumes preserved extraction JSON and writes fresh LF source-contract/results files.
The original a01/a02 packages are read-only dependencies.
"""
import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def digest(path):
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
    initial = research / "war_film_retreat_plan_a03.json"
    contract_path = research / "war_film_retreat_evidence_a03.json"
    result_path = research / "war_film_retreat_results_plan_a03.json"
    if contract_path.exists() or result_path.exists():
        raise FileExistsError("a03 outputs already exist; use a fresh package")

    snapshots = []
    for name in ("war_film_retreat_extract.py", "war_film_retreat_score_locator.py",
                 "war_film_retreat_freeze_a03.py", "war_film_retreat_plan_a03.json",
                 "war_film_retreat_evidence_a01.json"):
        source = research / name
        target = out / ("source-snapshot-" + name)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        snapshots.append({"path": str(target), "original_path": str(source),
                          "sha256": digest(target), "size": target.stat().st_size})

    artifacts = []
    extracts = {}
    for path in sorted(out.glob("*.json")):
        if path.name.startswith("source-snapshot-"):
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if "exe_sha256" in value and value["exe_sha256"] != EXE_SHA:
            raise ValueError("EXE identity mismatch: " + str(path))
        artifacts.append({"path": str(path), "sha256": digest(path), "size": path.stat().st_size})
        extracts[path.name] = value

    # Exact excerpts travel with the contract; external full scans remain preserved.
    excerpts = {}
    selections = {
        "trigger-name-registration.json": [(0x53A510, 0x53A657)],
        "score-trigger-factories.json": [(0x2849C00, 0x2849C20)],
        "score-trigger-allocation.json": [(0x284AAC1, 0x284AAD0), (0x284AB31, 0x284AB40)],
        "score-consumers.json": [(0x284B928, 0x284B93A), (0x284B9A8, 0x284B9BF),
                                  (0xD5D76C, 0xD5D7D0), (0x16AFD05, 0x16AFD3A)],
        "role-and-ui-registrations.json": [(0x329430, 0x329570), (0xB4470, 0xB4490),
                                           (0x2AE6A0, 0x2AE6C0)],
        "role-getters-and-ui-wrappers.json": [(0x19DADC2, 0x19DADCA), (0x19DAC72, 0x19DAC7A),
                                               (0xD5FA82, 0xD5FA92), (0x16B1082, 0x16B1092)],
        "gui-role-complete.json": [(0xC568E8, 0xC56949), (0xC569D4, 0xC569E7)],
        "coordinator-creators-and-role-tail.json": [(0x18854BD, 0x18854F6),
                                                   (0x188561A, 0x1885640),
                                                   (0x1885780, 0x18857CE)],
        "bounded-cache-active-entry.json": [(0x185163F, 0x185164B), (0x18519E1, 0x1851A36)],
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

    literal_and_vtable_data = {name: extracts[name] for name in (
        "score-literals.json", "role-literals.json", "trigger-entry-vtables.json",
        "score-trigger-instance-vtables.json", "primary-role-vtables.json")}
    claims = [
        {"id": "raw_attacker_score", "status": "static-confirmed",
         "spine": "attacker_war_score -> 284B8D0 -> 222A8A0; defender_war_score -> 284B950 -> neg eax",
         "meaning": "Raw integer score is attacker-relative; defender trigger negates it."},
        {"id": "coordinator_own_side", "status": "static-confirmed",
         "spine": "primary scope evaluators +288/+28C; UI roles pair +288/+20 and +28C/+80; 1885440 writes bit2 from +20 membership",
         "meaning": "bit2 is true for the coordinator's own attacker side; same Character joins coordinator."},
        {"id": "own_score_cache", "status": "static-confirmed",
         "spine": "184DE24 -> 222A8A0; 184DE29 multiply by 2*bit2-1; 184DE2D cache+FD8",
         "meaning": "coordinator+1B38 is own-side score."},
        {"id": "desperate_comparison", "status": "static-confirmed",
         "spine": "186B578 cmp own score, threshold; 186B57F jl false; 186B581 true",
         "meaning": "After a01 preconditions, ordinary defender passes the terminal score gate at own_score >= threshold.",
         "limits": "Mismatch with stock comment established; developer intent and live frequency not established."},
        {"id": "bounded_active_cache", "status": "static-confirmed",
         "spine": "184DCD9 -> 1851440 -> 2248A80 at1851642; 18519E1..1851A36 partition aggregates",
         "meaning": "This inspected active entry is a cache aggregation path, not an established generic retreat policy."},
        {"id": "generic_active_retreat", "status": "unknown",
         "meaning": "No global absence claim; unclassified indirect/vtable policy remains possible."},
    ]
    contract = {"schema": "xar.war-film-retreat-research-evidence.v1", "package": "a03",
                "proof_layer": "human-reviewed-exact-build-static-chain", "version": "1.19.0.6",
                "exe_sha256": EXE_SHA, "live_execution_performed": False,
                "automatic_semantic_verification": False, "production_mcp_capability_added": False,
                "claims": claims, "artifacts": artifacts, "source_snapshots": snapshots,
                "reviewed_instruction_excerpts": excerpts, "literal_and_vtable_data": literal_and_vtable_data,
                "a01_a02_modified": False,
                "limits": ["no producer execution observed", "no attributable active-retreat case",
                           "no loaded-text image integrity claim", "no developer-intent or defect claim",
                           "full-text references are locators, not an all-indirect-call census"]}
    write_new(contract_path, contract)
    plan = json.loads(initial.read_text(encoding="utf-8"))
    plan["topic"] = "war-film-retreat-score-direction-results-a03"
    plan["observation"]["producer"] = "1885440 own-side role producer; 184D960 own-score cache producer. No runtime freshness observation."
    plan["observation"]["caller"] = "Native attacker/defender trigger registrations and GetWarScoreFraction UI wrappers."
    plan["observation"]["expected_signal"] = "Static score and side mappings closed; developer intent and active-retreat native case remain unobserved."
    plan["evidence"] = [{"id": "reviewed_a03", "layer": "source-contract", "path": contract_path.name,
                         "sha256": digest(contract_path), "exe_sha256": EXE_SHA,
                         "supports": "Reviewed role and signed-score chains with exact raw artifacts and immutable a01 arithmetic."}]
    labels = {"score_role": "Raw total is attacker_war_score; defender trigger negates it",
              "cache_role": "bit2 means own attacker side; cache is own score",
              "predicate_meaning": "Ordinary defender terminal gate is own_score >= positive threshold"}
    for edge in plan["edges"]:
        edge.update(status="static-confirmed", evidence=["reviewed_a03"], open_question=None,
                    label=labels[edge["id"]])
    plan["nodes"].append({"id": "native_policy", "label": "Ordinary active-retreat policy / observed case"})
    plan["edges"].append({"id": "active_policy", "from": "predicate", "to": "native_policy",
                          "label": "Desperate selection does not establish active retreat",
                          "status": "unknown", "evidence": ["reviewed_a03"],
                          "open_question": "Recover attributable active policy caller or observe a natural producer window."})
    write_new(result_path, plan)
    print(json.dumps({"contract": str(contract_path), "sha256": digest(contract_path),
                      "artifacts": len(artifacts), "source_snapshots": len(snapshots)}, indent=2))


if __name__ == "__main__":
    main()
