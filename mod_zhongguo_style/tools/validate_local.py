#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZhongGuo 361 Style — local static validator (no CK3 launch required).

Checks (plain rule / code hygiene only, scoped to this mod directory):
  1. UTF-8 BOM present on all .txt/.yml/.gui; absent on descriptor.mod.
  2. descriptor.mod required fields; no remote_file_id anywhere.
  3. Brace balance for Clausewitz script files (comments/strings stripped).
  4. Localization: header line matches folder language; unique keys per file;
     all 9 language files expose the identical key set.
  5. Every localization-referenced key found in scripts exists in simp_chinese
     and english yml (game rules, modifiers, opinions, event .t/.desc/options).

Exit code 0 = GREEN, 1 = RED.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MOD_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = (
    "english", "simp_chinese", "french", "german", "japanese",
    "korean", "polish", "russian", "spanish",
)

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def strip_comments_and_strings(text: str) -> str:
    """Remove #-comments and double-quoted strings for brace counting."""
    out_lines = []
    for line in text.splitlines():
        line = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
        hash_pos = line.find("#")
        if hash_pos != -1:
            line = line[:hash_pos]
        out_lines.append(line)
    return "\n".join(out_lines)


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def check_bom() -> None:
    for path in sorted(MOD_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(MOD_ROOT).as_posix()
        if rel.startswith("tools/"):
            continue
        data = path.read_bytes()
        has_bom = data.startswith(b"\xef\xbb\xbf")
        if path.suffix in (".txt", ".yml", ".gui"):
            if not has_bom:
                err(f"missing UTF-8 BOM: {rel}")
        elif path.name == "descriptor.mod":
            if has_bom:
                err(f"descriptor.mod must NOT carry BOM: {rel}")


def check_descriptor() -> None:
    desc = MOD_ROOT / "descriptor.mod"
    text = read_text(desc)
    for field in ('version="', 'name="', 'supported_version="', 'picture="'):
        if field not in text:
            err(f"descriptor.mod missing field token: {field}")
    for path in MOD_ROOT.rglob("*"):
        if path.is_file() and path.suffix in (".txt", ".yml", ".gui", ".mod"):
            if b"remote_file_id" in path.read_bytes():
                err(f"remote_file_id must never live inside the repo: {path.relative_to(MOD_ROOT)}")


def check_braces() -> None:
    for path in sorted(MOD_ROOT.rglob("*.txt")):
        rel = path.relative_to(MOD_ROOT).as_posix()
        cleaned = strip_comments_and_strings(read_text(path))
        balance = 0
        for ch in cleaned:
            if ch == "{":
                balance += 1
            elif ch == "}":
                balance -= 1
            if balance < 0:
                err(f"unbalanced braces (extra '}}'): {rel}")
                break
        else:
            if balance != 0:
                err(f"unbalanced braces (net {balance:+d}): {rel}")


def parse_yml_keys(path: Path) -> list[str]:
    keys = []
    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        if lineno == 1 or not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+):\d+\s*\"(?:[^\"\\]|\\.)*\"\s*$", line)
        if m:
            keys.append(m.group(1))
        else:
            err(f"malformed yml line {lineno} in {path.relative_to(MOD_ROOT)}: {line.strip()[:80]}")
    return keys


def check_localization() -> dict[str, set[str]]:
    loc_dir = MOD_ROOT / "localization"
    key_sets: dict[str, set[str]] = {}
    for lang in LANGUAGES:
        yml = loc_dir / lang / f"zg361_l_{lang}.yml"
        if not yml.is_file():
            err(f"missing localization file: {yml.relative_to(MOD_ROOT)}")
            continue
        lines = read_text(yml).splitlines()
        if not lines or lines[0].strip() != f"l_{lang}:":
            err(f"bad yml header in {yml.relative_to(MOD_ROOT)}: expected 'l_{lang}:'")
        keys = parse_yml_keys(yml)
        if len(keys) != len(set(keys)):
            dupes = sorted({k for k in keys if keys.count(k) > 1})
            err(f"duplicate keys in {yml.relative_to(MOD_ROOT)}: {dupes}")
        key_sets[lang] = set(keys)
    reference = key_sets.get("english", set())
    for lang, keys in key_sets.items():
        if keys != reference:
            err(
                f"localization key set mismatch in {lang}: "
                f"missing={sorted(reference - keys)} extra={sorted(keys - reference)}"
            )
    return key_sets


def collect_referenced_keys() -> dict[str, set[str]]:
    """Scan scripts for keys that must exist in localization."""
    refs: dict[str, set[str]] = {"events": set(), "event_options": set(), "plain": set()}

    gr = MOD_ROOT / "common" / "game_rules" / "zg361_game_rules.txt"
    if gr.is_file():
        text = strip_comments_and_strings(read_text(gr))
        for m in re.finditer(r"^(zg361\w*)\s*=\s*\{", text, re.M):
            refs["plain"].add(f"rule_{m.group(1)}")
        for m in re.finditer(r"^[ \t]+(zg361_\w+)\s*=\s*\{", text, re.M):
            refs["plain"].add(f"setting_{m.group(1)}")
            refs["plain"].add(f"setting_{m.group(1)}_desc")

    for sub in ("modifiers", "opinion_modifiers"):
        folder = MOD_ROOT / "common" / sub
        if not folder.is_dir():
            continue
        for f in folder.glob("*.txt"):
            text = strip_comments_and_strings(read_text(f))
            for m in re.finditer(r"^\s*(zg361\w*)\s*=\s*\{", text, re.M):
                refs["plain"].add(m.group(1))
                if sub == "modifiers":
                    refs["plain"].add(f"{m.group(1)}_desc")

    ev = MOD_ROOT / "events" / "zg361_events.txt"
    if ev.is_file():
        text = strip_comments_and_strings(read_text(ev))
        ids = set(re.findall(r"^\s*(zg361\.\d+)\s*=\s*\{", text, re.M))
        for eid in ids:
            refs["events"].add(f"{eid}.t")
            refs["events"].add(f"{eid}.desc")
        for m in re.finditer(r"name\s*=\s*(zg361\.\d+\.\w+)", text):
            refs["event_options"].add(m.group(1))
        event_stems = {i.rsplit(".", 1)[0] for i in refs["event_options"]}
        missing_parent = event_stems - ids
        if missing_parent:
            err(f"event options reference unknown events: {sorted(missing_parent)}")
    return refs


def check_referenced_keys(key_sets: dict[str, set[str]]) -> None:
    refs = collect_referenced_keys()
    all_refs = refs["events"] | refs["event_options"] | refs["plain"]
    for lang in ("simp_chinese", "english"):
        missing = sorted(all_refs - key_sets.get(lang, set()))
        if missing:
            err(f"keys referenced in scripts but missing from {lang} yml: {missing}")


def main() -> int:
    if not MOD_ROOT.is_dir():
        print(f"mod root missing: {MOD_ROOT}")
        return 1
    check_bom()
    check_descriptor()
    check_braces()
    key_sets = check_localization()
    check_referenced_keys(key_sets)
    if errors:
        print(f"RED: {len(errors)} problem(s) in mod_zhongguo_style")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("GREEN: mod_zhongguo_style static checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
