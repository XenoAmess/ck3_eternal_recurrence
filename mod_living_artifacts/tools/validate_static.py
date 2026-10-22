"""Validate generated structure and localization; never awards live acceptance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from generate import BOM, render_files
from living_artifacts_model import AFFIX_IDS, CURSE_IDS
from product import LANGUAGES, SOURCE, REPO, spec

sys.path.append(str(REPO / "tools"))
from ck3_text_projection import blocks
from independent_mod_release import source_errors
from translate_localization_minimax import assert_protected_tokens, parse_ck3_localization


def validate(game: Path, *, release: bool = False) -> list[str]:
    errors: list[str] = []
    from living_artifacts_content import AFFIXES, CURSES
    if tuple(item.number for item in AFFIXES) != AFFIX_IDS or tuple(item.number for item in CURSES) != CURSE_IDS:
        errors.append("Enabled content IDs differ between the core pool and content registry")
    if len({item.key for item in (*AFFIXES, *CURSES)}) != len(AFFIXES) + len(CURSES):
        errors.append("Content registry contains duplicate identities")
    expected = render_files(game)
    for relative, data in expected.items():
        path = SOURCE / relative
        if not path.is_file() or path.read_bytes() != data:
            errors.append(f"Generated file missing or differs: {relative}")
    for path in sorted(SOURCE.rglob("*.txt")):
        if path.relative_to(SOURCE).parts[0] in {"docs", "tools"}:
            continue
        try:
            raw = path.read_bytes()
            if not raw.startswith(BOM):
                errors.append(f"Missing UTF-8 BOM: {path.relative_to(SOURCE)}")
            source = raw.decode("utf-8-sig")
            definitions = blocks(source)
            top = [block for block in definitions if not any(parent.opening < block.start < parent.end for parent in definitions)]
            if path.parent.name == "scripted_effects" and len(top) > 10:
                errors.append(f"Effect file exceeds ten top-level definitions: {path.name}")
            keys = [block.key for block in top]
            if len(keys) != len(set(keys)):
                errors.append(f"Duplicate top-level definitions: {path.name}")
        except (UnicodeError, ValueError) as error:
            errors.append(f"{path.relative_to(SOURCE)}: {error}")
    baseline_path = SOURCE / "localization/simp_chinese/xalw_l_simp_chinese.yml"
    baseline = parse_ck3_localization(baseline_path)
    for language in LANGUAGES if release else ("simp_chinese", "english"):
        path = SOURCE / f"localization/{language}/xalw_l_{language}.yml"
        try:
            if not path.read_bytes().startswith(BOM):
                errors.append(f"Localization lacks BOM: {language}")
            if path.read_text(encoding="utf-8-sig").splitlines()[0] != f"l_{language}:":
                errors.append(f"Localization header mismatch: {language}")
            values = parse_ck3_localization(path)
            if set(values) != set(baseline):
                errors.append(f"Localization key set mismatch: {language}")
            common = baseline.keys() & values.keys()
            assert_protected_tokens({key: baseline[key] for key in common}, {key: values[key] for key in common})
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"Localization {language}: {error}")
    # Check generated display references independently from the renderer.
    referenced: set[str] = set()
    for relative, data in expected.items():
        if relative.endswith(".txt"):
            text = data.decode("utf-8-sig")
            referenced.update(re.findall(r"(?:title|desc|custom_tooltip|text|set_artifact_name)\s*=\s*(xalw_[A-Za-z0-9_]+)", text))
    for key in sorted(referenced - baseline.keys()):
        errors.append(f"Missing visible localization key: {key}")
    defined: set[str] = set()
    calls: set[str] = set()
    for relative, data in expected.items():
        if relative.endswith(".txt"):
            source = data.decode("utf-8-sig")
            defined.update(block.key for block in blocks(source) if block.key.startswith("xalw_"))
            calls.update(re.findall(r"\b(xalw_[A-Za-z0-9_]+_(?:effect|trigger))\s*=\s*(?:yes|no)\b", source))
    errors.extend(f"Undefined scripted call: {key}" for key in sorted(calls - defined))
    if release:
        from living_artifacts_content import CONTENT_GAPS
        for gap in CONTENT_GAPS:
            errors.append(f"Unfinished enabled content: {gap.content_key}: {gap.requirement}: {gap.reason}")
        errors.extend(source_errors(spec()))
        thumbnail = SOURCE / "thumbnail.png"
        if not thumbnail.is_file() or not 16 <= thumbnail.stat().st_size < 1048576:
            errors.append("Workshop thumbnail must be present and strictly under 1 MiB")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True, help="CK3 game/ script root inside the installation")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    try:
        errors = validate(args.game, release=args.release)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors, "scope": "offline_structure_only", "live_verified": False}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
