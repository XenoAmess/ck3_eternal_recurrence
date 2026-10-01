"""Offline, read-only stock religion evidence inventory and line extraction.

This does not attach to, launch, or enumerate a CK3 process. The only writes are
the evidence artifacts selected by the caller. Source paths are frozen files.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("Z:/ck3_mod_rewrite")
OLD = ROOT / "Crusader Kings III/game"
NEW = ROOT / "artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/game"
OUT = ROOT / "artifacts/g2-offline-2026-10-01/religion/stock"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relevant_paths(game: Path) -> list[Path]:
    files = []
    for rel in ("common/defines/00_defines.txt", "common/defines/ai/00_ai.txt", "common/scripted_rules/00_rules.txt",
                "common/scripted_modifiers/00_religion_scripted_modifiers.txt", "common/on_action/yearly_on_actions.txt",
                "events/global_religion_events.txt", "events/dlc/pam/pam_decision_events.txt",
                "events/dlc/pam/heresy/pam_heresy_pulse.txt"):
        if (game / rel).is_file():
            files.append(game / rel)
    for rel in ("common/religion", "common/spiritual_fulfillment", "events/religion_events"):
        files.extend(p for p in (game / rel).rglob("*") if p.is_file())
    for folder in ("common/defines", "common/decisions", "common/character_interactions",
                   "common/on_action", "common/scripted_rules", "common/scripted_triggers",
                   "common/scripted_effects", "common/script_values", "common/scripted_costs",
                   "common/modifiers", "common/schemes", "common/council_tasks",
                   "events/religion_events"):
        files.extend(p for p in (game / folder).rglob("*") if p.is_file() and
                     re.search(r"relig|faith|rite|doctrine|tenet|fervor|pam|study_scripture|study_faith|court_chaplain", p.name, re.I))
    return sorted({p.relative_to(game) for p in files if
                   not re.search(r"holy_order|great_holy_war|crusade", p.relative_to(game).as_posix(), re.I)})


def inventory() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = sorted(set(relevant_paths(OLD)) | set(relevant_paths(NEW)))
    records = []
    diffs = []
    for rel in paths:
        a, b = OLD / rel, NEW / rel
        record = {"relative_path": rel.as_posix()}
        for label, p in (("old", a), ("new", b)):
            record[label] = ({"path": str(p), "size": p.stat().st_size, "sha256": sha(p),
                              "lines": len(p.read_text(encoding="utf-8-sig").splitlines())}
                             if p.is_file() else None)
        record["status"] = ("added" if not a.is_file() else "removed" if not b.is_file() else
                            "unchanged" if record["old"]["sha256"] == record["new"]["sha256"] else "changed")
        record["same_decoded_text"] = (a.read_text(encoding="utf-8-sig") == b.read_text(encoding="utf-8-sig")
                                       if a.is_file() and b.is_file() else None)
        records.append(record)
        if record["status"] != "unchanged":
            aa = a.read_text(encoding="utf-8-sig").splitlines(keepends=True) if a.is_file() else []
            bb = b.read_text(encoding="utf-8-sig").splitlines(keepends=True) if b.is_file() else []
            diffs.extend(difflib.unified_diff(aa, bb, fromfile=f"1.19/{rel.as_posix()}",
                                            tofile=f"1.20/{rel.as_posix()}", n=3))
    identities = {}
    for label, base in (("old", OLD.parent), ("new", NEW.parent)):
        exe = base / "binaries/ck3.exe"
        identities[label] = {"root": str(base), "exe_path": str(exe),
                             "exe_sha256": sha(exe) if exe.is_file() else None}
    payload = {"scope": "filename-scoped stock religion, excluding holy order and great holy war files",
               "identities": identities, "files": records,
               "counts": {s: sum(r["status"] == s for r in records) for s in
                          ("added", "removed", "changed", "unchanged")},
               "text_changed_existing": sum(r["same_decoded_text"] is False for r in records)}
    output = OUT / "stock-inventory.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "stock-religion.diff").write_text("".join(diffs), encoding="utf-8")
    print(json.dumps({"identities": identities, "counts": payload["counts"],
                      "inventory_sha256": sha(output), "diff_sha256": sha(OUT / "stock-religion.diff")}, indent=2))
    for r in records:
        print(f"{r['status']:9} {r['relative_path']}")


def inspect(args: argparse.Namespace) -> None:
    game = OLD if args.old else NEW
    for rel in args.files:
        p = game / rel
        lines = p.read_text(encoding="utf-8-sig").splitlines()
        print(f"FILE {rel} SHA256 {sha(p)} LINES {len(lines)}")
        if args.pattern:
            rx = re.compile(args.pattern, re.I)
            indexes = {j for i, line in enumerate(lines) if rx.search(line)
                       for j in range(max(0, i-args.context), min(len(lines), i+args.context+1))}
        else:
            indexes = range(max(0, args.start-1), min(len(lines), args.end or len(lines)))
        for i in sorted(indexes):
            print(f"{i+1:5}: {lines[i]}")


def blocks(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    result = []
    depth = 0
    current = None
    for i, line in enumerate(lines, 1):
        code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line.split("#", 1)[0])
        match = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*\{", code)
        if depth == 0 and match:
            current = {"key": match[1], "start": i, "fields": []}
        if current:
            field = re.match(r"\s*(ai_[a-zA-Z0-9_]+|is_shown|is_valid|is_valid_showing_failures|cost|effect|on_accept|on_decline|on_start|trigger|random_events|on_actions)\s*=", code)
            if field and depth == 1:
                current["fields"].append({"key": field[1], "line": i})
        depth += code.count("{") - code.count("}")
        if current and depth == 0:
            current["end"] = i
            result.append(current)
            current = None
    return result


def entrypoints() -> None:
    inventory_path = OUT / "stock-inventory.json"
    source = json.loads(inventory_path.read_text(encoding="utf-8"))
    result = []
    for record in source["files"]:
        rel = Path(record["relative_path"])
        if not record["new"] or rel.suffix != ".txt":
            continue
        parsed = blocks(NEW / rel)
        item = {"relative_path": rel.as_posix(), "sha256": record["new"]["sha256"], "blocks": parsed}
        result.append(item)
        if any(x in rel.as_posix() for x in ("character_interactions/00_religious", "character_interactions/pam", "decisions/dlc_decisions/pam", "schemes/scheme_types", "on_action/religion")):
            print(f"FILE {rel.as_posix()}")
            for block in parsed:
                if re.search(r"holy_order|crusade|holy_war", block["key"], re.I):
                    continue
                fields = ",".join(f"{f['key']}:{f['line']}" for f in block["fields"])
                print(f"  {block['key']} {block['start']}-{block['end']} {fields}")
    output = OUT / "stock-entrypoints.json"
    catalogs = {}
    for folder in ("faith_types", "rite_types", "tenet_types", "doctrine_category_types"):
        selected = [x for x in result if x["relative_path"].startswith(f"common/religion/{folder}/")]
        catalogs[folder] = {"block_count": sum(len(x["blocks"]) for x in selected),
                            "files": {x["relative_path"]: len(x["blocks"]) for x in selected}}
    catalogs["old_core_tenets"] = len(blocks(OLD / "common/religion/doctrine_types/30_core_tenets.txt"))
    old_tenets = {x["key"] for x in blocks(OLD / "common/religion/doctrine_types/30_core_tenets.txt")}
    new_tenets = {b["key"] for f in result if f["relative_path"].startswith("common/religion/tenet_types/") for b in f["blocks"]}
    catalogs["tenet_key_delta"] = {"added": sorted(new_tenets-old_tenets), "removed": sorted(old_tenets-new_tenets)}
    output.write_text(json.dumps({"parser": "top-level brace spans; fields are direct children; comments and quoted strings ignored", "catalogs": catalogs, "files": result}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(catalogs, indent=2))
    print(f"ENTRYPOINTS SHA256 {sha(output)}")


def evidence() -> None:
    windows = [
        ("old", "common/religion/religion_types/_religion_types.info", [(4, 31), (51, 64)]),
        ("old", "common/religion/doctrine_types/30_core_tenets.txt", [(4, 38)]),
        ("old", "common/defines/00_defines.txt", [(790, 798)]),
        ("old", "common/scripted_rules/00_rules.txt", [(22, 105)]),
        ("new", "common/religion/faith_types/_faith_types.info", [(1, 64)]),
        ("new", "common/religion/rite_types/_rite_types.info", [(24, 81)]),
        ("new", "common/religion/tenet_types/_tenet_types.info", [(44, 108), (130, 160)]),
        ("new", "common/religion/tenet_types/00_tenet_types.txt", [(64, 112)]),
        ("new", "common/religion/faith_types/00_faith_types.txt", [(453, 475), (535, 545), (656, 680)]),
        ("new", "common/religion/rite_types/00_rite_types.txt", [(1, 29)]),
        ("new", "common/defines/00_defines.txt", [(794, 843), (876, 878), (888, 929)]),
        ("new", "common/defines/ai/00_ai.txt", [(1839, 1842)]),
        ("new", "common/scripted_rules/00_rules.txt", [(22, 126)]),
        ("new", "common/scripted_triggers/00_religious_triggers.txt", [(3022, 3253)]),
        ("new", "common/on_action/religion_on_actions.txt", [(3, 25), (711, 828), (1255, 1259), (1261, 1267), (1591, 1607), (1609, 1678), (1811, 1855), (1861, 1917)]),
        ("new", "common/script_values/02_religion_values.txt", [(3350, 3442), (4805, 4806)]),
        ("new", "common/script_values/pam_values.txt", [(166, 170), (2255, 2300), (8030, 8057), (9563, 9599)]),
        ("new", "common/scripted_effects/00_religion_effects.txt", [(338, 344)]),
        ("new", "common/scripted_effects/pam_effects.txt", [(11516, 11524), (11641, 11781)]),
        ("new", "common/decisions/dlc_decisions/pam/pam_decisions.txt", [(26, 124), (3627, 3823), (6106, 6207)]),
        ("new", "common/scripted_triggers/pam_scripted_triggers.txt", [(2459, 2508), (2564, 2600), (2675, 2709)]),
        ("new", "common/character_interactions/pam_interactions.txt", [(3201, 3291), (3392, 3473), (3476, 3614)]),
        ("new", "common/spiritual_fulfillment/_spiritual_fulfillment_type.info", [(1, 42)]),
        ("new", "common/spiritual_fulfillment/00_spiritual_fulfillment_types.txt", [(1, 177)]),
        ("new", "events/dlc/pam/heresy/pam_heresy_pulse.txt", [(1, 40), (67, 86), (118, 137), (170, 177)]),
    ]
    text_parts = []
    records = []
    for version, rel, ranges in windows:
        path = (OLD if version == "old" else NEW) / rel
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        record = {"version": version, "relative_path": rel, "sha256": sha(path), "ranges": ranges}
        records.append(record)
        text_parts.append(f"FILE {version}/{rel} SHA256 {record['sha256']}\n")
        for start, end in ranges:
            if not 1 <= start <= end <= len(lines):
                raise ValueError((rel, start, end, len(lines)))
            text_parts.extend(f"{i+1:5}: {lines[i]}\n" for i in range(start-1, end))
            text_parts.append("\n")
    text_output = OUT / "stock-evidence-windows.txt"
    text_output.write_text("".join(text_parts), encoding="utf-8")
    inventory = json.loads((OUT / "stock-inventory.json").read_text(encoding="utf-8"))
    output = OUT / "stock-evidence-manifest.json"
    payload = {"readiness": "research; stock static-confirmed only; no native ABI, fixture or live qualification",
               "identities": inventory["identities"], "counts": inventory["counts"],
               "text_changed_existing": inventory["text_changed_existing"], "windows": records,
               "artifacts": {str(p): sha(p) for p in (OUT / "stock-inventory.json", OUT / "stock-religion.diff", OUT / "stock-entrypoints.json", text_output)},
               "research_script_sha256": sha(Path(__file__))}
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": payload["counts"], "text_changed_existing": payload["text_changed_existing"],
                      "manifest_path": str(output), "manifest_sha256": sha(output), "artifacts": payload["artifacts"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("inventory")
    sub.add_parser("entrypoints")
    sub.add_parser("evidence")
    ip = sub.add_parser("inspect")
    ip.add_argument("files", nargs="+")
    ip.add_argument("--old", action="store_true")
    ip.add_argument("--pattern")
    ip.add_argument("--context", type=int, default=0)
    ip.add_argument("--start", type=int, default=1)
    ip.add_argument("--end", type=int)
    args = parser.parse_args()
    if args.mode == "inventory":
        inventory()
    elif args.mode == "entrypoints":
        entrypoints()
    elif args.mode == "evidence":
        evidence()
    else:
        inspect(args)


if __name__ == "__main__":
    main()
