"""Read actual host rows or frozen final logs only; no runtime/pipe/game action."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HELPER = Path(__file__).with_name("reclaim_the_motherland_effective_law_contract.py")
HELPER_SHA = "b0f58cb55dab63887062f1677cd82e05011e23f82f1ced0c12d943194c62349b"
BASE = Path(__file__).parent / "fixtures/reclaim_the_motherland_acceptance/common/scripted_effects/rqa_effects.txt"
BASE_SHA = "004615572553a07d62da0405d3e7b7d37f3e2d6c6922b54d632334233ad83407"


def pin(path: Path, raw: bytes | None = None) -> dict:
    if raw is None:
        raw = path.read_bytes()
    return {"path": path.resolve().as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(path: Path, value: dict | bytes) -> None:
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)


def load_helper():
    if pin(HELPER)["sha256"] != HELPER_SHA:
        raise ValueError("adopted exact helper changed")
    spec = importlib.util.spec_from_file_location("effective_law_contract27_final", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def extract(args, helper) -> int:
    raw = args.report.read_bytes()  # One actual report read, not repeated polling.
    report = json.loads(raw.decode("utf-8-sig"))
    evidence = {"schema": "rmtm-effective-single-heir-phase-actual-rows-v1", "phase": args.phase}
    for kind, step_id in [("root", args.root_step), ("physical", args.physical_step), ("script", args.script_step)]:
        rows = [row for row in report.get("steps", []) if row.get("id") == step_id]
        if len(rows) != 1:
            raise ValueError("missing/duplicate actual managed row: " + step_id)
        evidence[kind + "_record"] = rows[0]
    report_copy = args.output.with_suffix(args.output.suffix + ".host-report.raw")
    evidence["source_report"] = pin(report_copy, raw)
    evidence["original_report_path"] = args.report.resolve().as_posix()
    try:
        qualification = helper.evaluate_phase(evidence)
        code = 0
    except (helper.AdmissionError, KeyError, TypeError, AttributeError, ValueError) as error:
        qualification = {"phase": args.phase, "effective_single_heir_qualified": False,
                         "error": str(error), "source_pass": False, "business_pass": False}
        code = 1
    # Successful and rejected captures are immutable; never rewrite original report.
    for path in (args.output, report_copy, args.output.with_suffix(args.output.suffix + ".qualification.json")):
        if path.exists():
            raise FileExistsError(path)
    write(report_copy, raw)
    write(args.output, evidence)
    qualification["phase_evidence"] = pin(args.output)
    write(args.output.with_suffix(args.output.suffix + ".qualification.json"), qualification)
    print(json.dumps({"phase": args.phase, "qualified": code == 0, "evidence": pin(args.output),
                      "source_pass": False, "business_pass": False}))
    return code


def phase_evidence(path: Path) -> dict:
    value = json.loads(path.read_bytes().decode("utf-8-sig"))
    frozen = value["source_report"]
    raw = Path(frozen["path"]).read_bytes()
    if pin(Path(frozen["path"]), raw) != frozen:
        raise ValueError("immutable source report changed")
    report = json.loads(raw.decode("utf-8-sig"))
    for kind in ("root", "physical", "script"):
        row = value[kind + "_record"]
        actual = [entry for entry in report.get("steps", []) if entry.get("id") == row["id"]]
        if actual != [row]:
            raise ValueError("copied phase row differs from original report: " + kind)
    return value


def final(args, helper) -> int:
    import re
    if pin(BASE)["sha256"] != BASE_SHA:
        raise ValueError("original36 family source changed")
    original = BASE.read_text(encoding="utf-8-sig")
    families = [(kind, name) for kind, _, name in re.findall(r'RQA: (TEST|PROBE) (PASS|PENDING_PHYSICAL) ([a-z0-9_]+)"', original)]
    if len(families) != 34 or len(set(families)) != 34:
        raise ValueError("original36 marker contract differs")
    phases = [phase_evidence(path) for path in (args.d3, args.predeath, args.postdeath)]
    bundle = {"schema": "rmtm-effective-single-heir-actual-rows-v1", "phases": phases}
    raw = args.debug_log.read_bytes()
    lines = raw.decode("utf-8-sig", errors="replace").splitlines()
    result = {"schema": "rmtm-original36-effective-law-marker-verdict-v1",
              "debug_log": pin(args.debug_log, raw), "actual_phase_inputs": [pin(path) for path in (args.d3, args.predeath, args.postdeath)],
              "source_pass": False, "business_pass": False,
              "original_business_review_still_required": "actual predecessor death, original C1-C6/9ministers/loyal tree/personal land/real offer/14day/50-51 cells and normal0; marker/law credit never replaces GUI review"}
    try:
        law = helper.evaluate_bundle(bundle)  # Re-evaluate actual rows, never trust a qualification Boolean.
        pending = {item for items in helper.FAMILIES.values() for item in items}
        expected = [("RQA: " + kind + (" PENDING_PHYSICAL " if (kind, family) in pending else " PASS ") + family)
                    for kind, family in families]
        expected += ["RQA: TEST BEGIN reclaim", "RQA: TEST DONE reclaim"]
        forbidden = [line for line in lines if any(token in line for token in
                     ("RQA: TEST FAIL", "RQA: PROBE FAIL", "RQA120: TEST FAIL"))]
        counts = {literal: sum(literal in line for line in lines) for literal in expected}
        if forbidden or any(count != 1 for count in counts.values()):
            raise ValueError("original36 family count/FAIL gate rejected: " + str({key: count for key, count in counts.items() if count != 1}) + "; fail_lines=" + str(len(forbidden)))
        # Old PASS credit for the three pending families must not coexist.
        if any(any(f"RQA: {kind} PASS {family}" in line for line in lines) for kind, family in pending):
            raise ValueError("legacy PASS appeared for a physical-gated family")
        result.update(marker_and_effective_law_contract_qualified=True, original_family_count=36,
                      unchanged_family_count=33, physical_qualified_family_count=3,
                      marker_counts=counts, actual_law_qualification=law)
        code = 0
    except (helper.AdmissionError, KeyError, TypeError, AttributeError, ValueError) as error:
        result.update(marker_and_effective_law_contract_qualified=False, error=str(error),
                      physical_qualified_family_count=0)
        code = 1
    write(args.output, result)
    print(json.dumps({"marker_and_law_qualified": code == 0, "output": pin(args.output),
                      "source_pass": False, "business_pass": False}))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    capture = sub.add_parser("phase")
    capture.add_argument("--phase", choices=("d3", "predeath", "postdeath"), required=True)
    capture.add_argument("--report", type=Path, required=True)
    for kind in ("root", "physical", "script"):
        capture.add_argument("--" + kind + "-step", required=True)
    capture.add_argument("--output", type=Path, required=True)
    verdict = sub.add_parser("final")
    for kind in ("d3", "predeath", "postdeath", "debug-log", "output"):
        verdict.add_argument("--" + kind, type=Path, required=True)
    args = parser.parse_args()
    helper = load_helper()
    return extract(args, helper) if args.operation == "phase" else final(args, helper)


if __name__ == "__main__":
    raise SystemExit(main())
