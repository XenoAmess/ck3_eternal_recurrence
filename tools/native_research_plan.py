"""Check new research plans and render their declared evidence graph, offline.

This checks records and file bytes, not CK3 semantics or permission to run CK3.
No historical topic, ABI, registry record, or evidence file is rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys


SCHEMA = "xar.native-research-plan.v1"
LAYERS = {
    "locator", "exact-build", "source-contract", "offline-fixture",
    "live-observation", "action-postcondition",
}
STATUSES = {"unknown", "inference", "static-confirmed", "live-confirmed", "counter-policy"}
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text_field(record: dict, key: str, where: str) -> str:
    value = record.get(key)
    require(isinstance(value, str) and bool(value.strip()), f"{where}.{key}: nonempty text required")
    return value


def choice(record: dict, key: str, allowed: set[str], where: str) -> str:
    value = text_field(record, key, where)
    require(value in allowed, f"{where}.{key}: expected one of {', '.join(sorted(allowed))}")
    return value


def fingerprint(path: Path) -> dict:
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return {"path": str(path.resolve()), "sha256": digest}


def template(topic: str, build: str, exe: Path | None = None) -> dict:
    require(bool(IDENTIFIER.fullmatch(topic)), "topic: use letters, digits, hyphen or underscore, starting with a letter")
    return {
        "schema": SCHEMA,
        "topic": topic,
        "question": None,
        "purpose": None,
        "build": {"version": build, "exe_sha256": fingerprint(exe)["sha256"] if exe else None},
        "observation": {
            "mode": "offline-only", "actor_kind": None,
            "owner_scope": None, "identity_kind": None, "identity_lifetime": None,
            "producer_trigger": "unknown", "producer": None, "caller": None,
            "consumer": None, "cache_lifetime": None, "expected_signal": None,
            "zero_sample_meaning": None, "stop_condition": None,
            "runtime_window_ref": None,
        },
        "evidence": [],
        "nodes": [{"id": "entry", "label": "Research entry"}, {"id": "result", "label": "Unresolved result"}],
        "edges": [{"id": "decision", "from": "entry", "to": "result", "label": "Unresolved transition",
                   "status": "unknown", "evidence": [], "open_question": "Replace with the specific missing branch or input."}],
        "cases": [],
    }


def parse_plan(raw: bytes) -> dict:
    def no_duplicates(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    plan = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=no_duplicates)
    require(isinstance(plan, dict), "plan must be an object")
    return plan


def load_plan(path: Path) -> dict:
    return parse_plan(path.read_bytes())


def indexed(plan: dict, key: str) -> dict[str, dict]:
    rows = plan.get(key)
    require(isinstance(rows, list), f"{key}: array required")
    result = {}
    for row in rows:
        require(isinstance(row, dict), f"{key}: object rows required")
        ident = text_field(row, "id", key)
        require(bool(IDENTIFIER.fullmatch(ident)), f"{key}: invalid id {ident}")
        require(ident not in result, f"{key}: duplicate id {ident}")
        result[ident] = row
    return result


def evidence_refs(row: dict, records: dict, where: str) -> set[str]:
    refs = row.get("evidence")
    require(isinstance(refs, list), f"{where}.evidence: array required")
    require(all(isinstance(ref, str) and ref in records for ref in refs), f"{where}: dangling evidence reference")
    require(len(set(refs)) == len(refs), f"{where}: duplicate evidence reference")
    return {records[ref]["layer"] for ref in refs}


def check(plan: dict, base: Path, *, for_observation: bool = False) -> dict:
    require(plan.get("schema") == SCHEMA, "unsupported schema")
    text_field(plan, "topic", "plan")
    text_field(plan, "question", "plan")
    choice(plan, "purpose", {"npc-choice", "player-legality", "engine-transition", "own-policy"}, "plan")
    build = plan.get("build")
    require(isinstance(build, dict), "build: object required")
    text_field(build, "version", "build")
    require(isinstance(build.get("exe_sha256"), str) and bool(SHA256.fullmatch(build["exe_sha256"])), "build.exe_sha256: exact file hash required")
    observation = plan.get("observation")
    require(isinstance(observation, dict), "observation: object required")
    choice(observation, "mode", {"offline-only", "paused-snapshot", "passive-runtime"}, "observation")
    choice(observation, "actor_kind", {"ai", "human", "engine"}, "observation")
    choice(observation, "identity_kind", {"definition-key", "generation-id", "process-ordinal", "none"}, "observation")
    choice(observation, "producer_trigger", {"paused-query", "daily-tick", "on-action", "not-applicable", "unknown"}, "observation")
    for key in ("owner_scope", "identity_lifetime", "producer", "caller", "consumer", "cache_lifetime",
                "expected_signal", "zero_sample_meaning", "stop_condition"):
        text_field(observation, key, "observation")

    issues = []
    if observation["mode"] == "offline-only":
        issues.append("offline-only plan does not define a live observation window")
    if plan["purpose"] == "npc-choice" and observation["actor_kind"] != "ai":
        issues.append("NPC choice requires an AI actor; player legality and own policy are separate questions")
    if observation["producer_trigger"] in {"unknown", "not-applicable"}:
        issues.append("the real producer trigger must be located before live sampling")
    if observation["mode"] == "paused-snapshot" and observation["producer_trigger"] in {"daily-tick", "on-action"}:
        issues.append("a paused capture cannot wait for a fresh daily-tick/action producer; describe the cached read path or an authorized passive runtime window")
    if observation["mode"] == "passive-runtime" and not (
        isinstance(observation.get("runtime_window_ref"), str) and observation["runtime_window_ref"].strip()
    ):
        issues.append("passive runtime sampling requires a reference to the separately authorized run/window")
    if for_observation:
        require(not issues, "; ".join(issues))

    evidence = indexed(plan, "evidence")
    for ident, row in evidence.items():
        choice(row, "layer", LAYERS, f"evidence {ident}")
        require(isinstance(row.get("exe_sha256"), str) and row["exe_sha256"].lower() == build["exe_sha256"].lower(), f"evidence {ident}: build hash differs from plan")
        path = base / text_field(row, "path", f"evidence {ident}")
        digest = row.get("sha256")
        require(isinstance(digest, str) and bool(SHA256.fullmatch(digest)), f"evidence {ident}: valid sha256 required")
        require(path.is_file(), f"evidence {ident}: missing file {path}")
        require(fingerprint(path)["sha256"] == digest.lower(), f"evidence {ident}: file hash mismatch")
        text_field(row, "supports", f"evidence {ident}")
        if row["layer"] in {"live-observation", "action-postcondition"}:
            for key in ("session", "frame", "identity"):
                text_field(row, key, f"evidence {ident}")

    nodes, edges, cases = (indexed(plan, key) for key in ("nodes", "edges", "cases"))
    require(bool(nodes), "nodes: at least one node required")
    for ident, row in nodes.items():
        text_field(row, "label", f"node {ident}")
    for ident, row in edges.items():
        require(isinstance(row.get("from"), str) and row["from"] in nodes and isinstance(row.get("to"), str) and row["to"] in nodes, f"edge {ident}: dangling node")
        text_field(row, "label", f"edge {ident}")
        require(row.get("open_question") is None or isinstance(row["open_question"], str), f"edge {ident}: open_question must be text or null")
        status = choice(row, "status", STATUSES, f"edge {ident}")
        layers = evidence_refs(row, evidence, f"edge {ident}")
        if status in {"unknown", "inference"}:
            text_field(row, "open_question", f"edge {ident}")
        if status == "inference":
            require(bool(layers), f"edge {ident}: inference requires cited evidence")
        if status == "static-confirmed":
            require("source-contract" in layers, f"edge {ident}: locator/byte identity alone cannot support static semantics")
        if status == "live-confirmed":
            require(bool(layers & {"live-observation", "action-postcondition"}), f"edge {ident}: offline evidence cannot establish live confirmation")
    for ident, row in cases.items():
        text_field(row, "question", f"case {ident}")
        choice(row, "status", {"pending", "observed", "not-applicable"}, f"case {ident}")
        layers = evidence_refs(row, evidence, f"case {ident}")
        if row["status"] == "observed":
            require(bool(layers & {"live-observation", "action-postcondition"}), f"case {ident}: observed requires live evidence, not an offline fixture")
        if row["status"] == "not-applicable":
            text_field(row, "reason", f"case {ident}")

    native_edges = [row for row in edges.values() if row["status"] != "counter-policy"]
    counts = {status: sum(row["status"] == status for row in edges.values()) for status in sorted(STATUSES)}
    return {
        "schema": "xar.native-research-plan-check.v1", "result": "plan-consistent",
        "proof_layer": "record-structure-and-file-integrity",
        "semantic_correctness_verified": False, "live_execution_performed": False,
        "observation_plan_issues": issues,
        "declared_edges_by_status": counts, "enumerated_native_edges": len(native_edges),
        "declared_cases_by_status": {status: sum(row["status"] == status for row in cases.values()) for status in ("pending", "observed", "not-applicable")},
        "checked_evidence_files": len(evidence),
        "limitations": ["Evidence layers and conclusions are author declarations; hashes bind bytes, not their truth.",
                        "Counts cover this enumerated graph only, not all CK3 branches.",
                        "A consistent observation plan is not authorization to run or manipulate CK3."],
    }


def mermaid_text(value: str) -> str:
    return html.escape(value, quote=True).replace("\r", " ").replace("\n", " ").replace("|", "&#124;").replace("`", "&#96;")


def render(plan: dict, result: dict) -> str:
    lines = [f"# Research plan: {mermaid_text(plan['topic'])}", "", "GENERATED from the supplied research plan; no native semantics are inferred.",
             "", f"Question: {mermaid_text(plan['question'])}", "", "```mermaid", "flowchart TD"]
    # Prefix and enumerate node IDs, so user IDs cannot become Mermaid keywords.
    names = {row["id"]: f"n{i}" for i, row in enumerate(plan["nodes"])}
    for row in plan["nodes"]:
        lines.append(f'    {names[row["id"]]}["{mermaid_text(row["label"])}"]')
    for row in plan["edges"]:
        label = mermaid_text(f'{row["id"]} [{row["status"]}] {row["label"]}')
        arrow = f'-. "{label}" .->' if row["status"] == "unknown" else f'-->|"{label}"|'
        lines.append(f'    {names[row["from"]]} {arrow} {names[row["to"]]}')
    lines.extend(["```", "", "| Edge | Declared status | Evidence IDs | Open question |", "|---|---|---|---|"])
    for row in plan["edges"]:
        values = (row["id"], row["status"], ", ".join(row["evidence"]), row.get("open_question") or "")
        lines.append("| " + " | ".join(mermaid_text(value) for value in values) + " |")
    lines.extend(["", "| Observation design | Value |", "|---|---|"])
    for key, value in plan["observation"].items():
        lines.append(f"| {mermaid_text(key)} | {mermaid_text(str(value))} |")
    lines.extend(["", "| Evidence ID | Declared layer | File | SHA-256 | Supports |", "|---|---|---|---|---|"])
    for row in plan["evidence"]:
        lines.append("| " + " | ".join(mermaid_text(row[key]) for key in ("id", "layer", "path", "sha256", "supports")) + " |")
    lines.extend(["", "Check result (file integrity and declarations only):", "", "```json", json.dumps(result, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def emit(body: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(body)
    else:
        # New attempt/output required; never rewrite a prior artifact.
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="write an incomplete draft; fill its null fields before checking")
    init.add_argument("--topic", required=True)
    init.add_argument("--build", required=True)
    init.add_argument("--exe", type=Path, help="read only to fingerprint; this does not identify game semantics")
    init.add_argument("--output", type=Path, required=True)
    stamp = sub.add_parser("fingerprint", help="print a local file's path and SHA-256 without modifying it")
    stamp.add_argument("path", type=Path)
    for name in ("check", "render"):
        action = sub.add_parser(name, help="check references/bytes" if name == "check" else "render the same checked edge records as Markdown/Mermaid")
        action.add_argument("plan", type=Path)
        action.add_argument("--for-observation", action="store_true", help="also reject unknown or incompatible sampling conditions; grants no runtime permission")
        action.add_argument("--output", type=Path, help="exclusive create; omit for stdout")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            emit(json.dumps(template(args.topic, args.build, args.exe), ensure_ascii=False, indent=2) + "\n", args.output)
        elif args.command == "fingerprint":
            emit(json.dumps(fingerprint(args.path), ensure_ascii=False, indent=2) + "\n", None)
        else:
            raw = args.plan.read_bytes()
            plan = parse_plan(raw)
            result = check(plan, args.plan.resolve().parent, for_observation=args.for_observation)
            result["plan_sha256"] = hashlib.sha256(raw).hexdigest()
            body = render(plan, result) if args.command == "render" else json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            emit(body, args.output)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
