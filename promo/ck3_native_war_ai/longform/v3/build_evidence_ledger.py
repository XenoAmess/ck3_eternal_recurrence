"""Bind v3 cue plans to real source files without promoting footage to causality."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from build_inputs import HEADING, HERE, SCRIPT, SOURCE


PLAN = HERE / "visual-bindings-plan.json"
OUTPUT = HERE / "evidence-visual-ledger.json"
REPO = HERE.parents[3]
CASE_DOCS = {
    "CASE-R": REPO / "docs/ck3-native-ai/war-film-robert-case-r-result-2026-09-23.md",
    "CASE-W": REPO / "docs/ck3-native-ai/war-film-case-w-result-2026-09-23.md",
    "CASE-C": REPO / "docs/ck3-native-ai/war-film-case-c-result-2026-09-23.md",
}
W_REPORT = Path("D:/workspace/ck3_war_film_research_20260923/case-w-bundle-r1/report.json")
STATES = {"verified-static", "exact-live-case", "illustrative-rule-scenario", "unbound"}
FAMILIES = {
    "robert-hud-data-card",
    "native-rule-excerpt",
    "labeled-rule-scenario",
    "case-w-wartime-map-context",
    "case-w-query-data-card",
    "pending-causal-shot",
    "ck3-source-index-endcard",
}


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Source link escaped the repository: {path}") from error


def source_notes() -> dict[str, list[dict]]:
    text = SOURCE.read_text(encoding="utf-8-sig")
    found = list(HEADING.finditer(text))
    if len(found) != 45:
        raise ValueError("Expected 45 source sections")
    result = {}
    for index, heading in enumerate(found):
        section = text[heading.end():found[index + 1].start() if index + 1 < len(found) else len(text)]
        note = re.search(r"\*\*主张/来源（不朗读）\*\*：([^\n]+)", section)
        if not note:
            raise ValueError(f"Missing source note: {heading.group(0)}")
        links = []
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", note.group(1)):
            path = (SOURCE.parent / target.split("#", 1)[0]).resolve()
            if not path.is_file():
                raise ValueError(f"Broken source link in V3-{index + 1:02d}: {target}")
            links.append({"label": label, "path": repo_path(path)})
        if not links:
            raise ValueError(f"No file-backed source link in V3-{index + 1:02d}")
        result[f"V3-{index + 1:02d}"] = links
    return result


def build() -> dict:
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = plan["cues"]
    ids = [f"V3-{index:02d}" for index in range(1, 46)]
    if ([row["id"] for row in rows] != ids
            or [row["id"] for row in script["cues"]] != ids
            or plan["schema"] != "ck3-war-ai.v3-visual-bindings-plan.v1"):
        raise ValueError("Plan and spoken script must list exactly V3-01..V3-45 in order")
    notes = source_notes()
    cases = {key: {"path": repo_path(path), "sha256": file_sha(path)}
             for key, path in CASE_DOCS.items()}
    report = json.loads(W_REPORT.read_text(encoding="utf-8"))
    if (report.get("result") != "GREEN"
            or report.get("native_ai_causality_verified") is not False
            or report.get("frame_synchronous_query_proven") is not False
            or report.get("human_1x_review_performed") is not False
            or report.get("natural_ai_declaration_proven") is not False):
        raise ValueError("CASE-W bundle does not have the reviewed limited GREEN scope")
    w_report = {"path": W_REPORT.as_posix(), "sha256": file_sha(W_REPORT),
                "result": "GREEN", "native_ai_causality_verified": False,
                "frame_synchronous_query_proven": False, "human_1x_review_performed": False}
    bound = []
    for row, spoken in zip(rows, script["cues"]):
        if (row["state"] not in STATES or row["asset_family"] not in FAMILIES
                or not row["asset_direction"].strip() or not row["claim_scope"].strip()
                or not row["limits"].strip() or not isinstance(row["case_refs"], list)
                or any(key not in cases for key in row["case_refs"])):
            raise ValueError(f"Incomplete or invalid binding: {row['id']}")
        if row["state"] == "exact-live-case" and not row["case_refs"]:
            raise ValueError(f"Exact live state requires a case source: {row['id']}")
        if row["state"] == "illustrative-rule-scenario" and row["asset_family"] != "labeled-rule-scenario":
            raise ValueError(f"Illustrative input needs its explicit visual label: {row['id']}")
        if row["state"] == "unbound" and "pending" not in row["asset_family"]:
            raise ValueError(f"Unbound cue needs pending visual family: {row['id']}")
        bound.append({**row, "shot_id": spoken["shot_id"],
                      "spoken_source_links": notes[row["id"]],
                      "case_source_paths": [cases[key]["path"] for key in row["case_refs"]]})
    count = {state: sum(row["state"] == state for row in bound) for state in sorted(STATES)}
    return {
        "schema": "ck3-war-ai.v3-evidence-visual-ledger.v1",
        "status": "editorial-planning-no-film-signoff",
        "repository_source_paths_relative": True,
        "external_media_path_local": True,
        "spoken_script_path": repo_path(SCRIPT),
        "spoken_script_sha256": file_sha(SCRIPT),
        "director_narration_path": repo_path(SOURCE),
        "director_narration_sha256": file_sha(SOURCE),
        "case_documents": cases,
        "case_w_media_bundle": w_report,
        "case_c_result": "30 game days observed; no sampled in_combat, no CombatID; pending interaction stopped window",
        "state_counts": count,
        "state_meaning": {
            "verified-static": "The cited native source supports the stated rule; no live decision outcome is implied.",
            "exact-live-case": "Only claim_scope is bound to the named game readback; limits remain open.",
            "illustrative-rule-scenario": "Author-provided numbers or roles demonstrate a verified rule and must be labelled as an example.",
            "unbound": "The cue needs a real causal shot or rewritten scope before final film use.",
        },
        "cues": bound,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--refresh", action="store_true", help="Update this uncommitted planning ledger after a source correction")
    args = parser.parse_args()
    ledger = build()
    data = (json.dumps(ledger, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.write:
        with OUTPUT.open("xb") as stream:
            stream.write(data)
    elif args.refresh:
        if not OUTPUT.is_file():
            raise FileNotFoundError(OUTPUT)
        temporary = OUTPUT.with_suffix(".json.refreshed")
        with temporary.open("xb") as stream:
            stream.write(data)
        temporary.replace(OUTPUT)
    elif OUTPUT.read_bytes() != data:
        raise ValueError("Ledger differs from current sources or checked-in plan")
    print(f"V3 evidence ledger PASS: 45 cues; {ledger['state_counts']}")


if __name__ == "__main__":
    main()
