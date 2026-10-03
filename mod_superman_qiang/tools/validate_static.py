"""Read-only source, localization and generated-byte validation for Superman Qiang.

This structural gate never starts CK3 and does not claim native scope validity,
save compatibility or actual-game acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from product import GAME_VERSION, LANGUAGES, REPO, RUNTIME_FILES, SOURCE, VERSION, spec

sys.path.insert(0, str(REPO / "tools"))
from ck3_text_projection import blocks, masked
from independent_mod_release import sha256_file, source_errors
from translate_localization_minimax import TranslationError, assert_protected_tokens, parse_ck3_localization

# Keep product generators ahead of similarly named shared modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))

TEST_MARKERS = re.compile(
    r"(?i)\b(?:sxadt[._\w]*|sxad_test[._\w]*|sxad_acceptance[._\w]*|selftest|test_only|acceptance_only|XAR_ACCEPTANCE_ONLY_BEGIN|XAR_ACCEPTANCE_ONLY_END)\b"
)


def top_level_blocks(source: str):
    """Return top-level block assignments; comments/strings cannot alter depth."""
    result = []
    previous_end = 0
    for block in blocks(source):
        if block.start >= previous_end:
            result.append(block)
            previous_end = block.end
    return result


def validate(game_root: Path | None = None) -> dict:
    errors = source_errors(spec())
    hashes = []
    texts = {}
    effect_counts = {}
    for relative in sorted(RUNTIME_FILES):
        path = SOURCE / relative
        if not path.is_file():
            continue
        data = path.read_bytes()
        hashes.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if path.suffix not in {".txt", ".yml", ".mod", ".gui"}:
            continue
        try:
            source = data.decode("utf-8-sig")
            texts[relative] = source
            if TEST_MARKERS.search(source):
                errors.append(f"acceptance marker leaked into runtime: {relative}")
            if path.suffix != ".yml":
                top = top_level_blocks(source)
                keys = [block.key for block in top]
                if len(keys) != len(set(keys)):
                    errors.append(f"duplicate top-level definitions: {relative}")
                if relative.startswith("common/scripted_effects/"):
                    effect_counts[relative] = len(top)
                    if len(top) > 20:
                        errors.append(f"scripted-effect definition count exceeds 20: {relative}: {len(top)}")
        except (UnicodeError, ValueError) as error:
            errors.append(f"invalid runtime text: {relative}: {error}")
    descriptor = texts.get("descriptor.mod", "")
    if not re.search(r'(?m)^\s*version\s*=\s*"' + re.escape(VERSION) + r'"\s*$', descriptor):
        errors.append(f"descriptor version must be {VERSION}")
    if not re.search(r'(?m)^\s*supported_version\s*=\s*"1\.20(?:\.\*)?"\s*$', descriptor):
        errors.append("descriptor supported_version must be 1.20 or 1.20.*")
    if not re.search(r'(?m)^\s*picture\s*=\s*"thumbnail\.png"\s*$', descriptor):
        errors.append("descriptor picture must be thumbnail.png")
    locs = {}
    for language in LANGUAGES:
        paths = [path for path in sorted(RUNTIME_FILES) if path.startswith(f"localization/{language}/") and path.endswith(".yml")]
        values = {}
        if not paths:
            errors.append(f"missing {language} localization inventory")
        for relative in paths:
            text = texts.get(relative, "")
            if not text.splitlines() or text.splitlines()[0] != f"l_{language}:":
                errors.append(f"wrong localization header: {relative}")
            try:
                parsed = parse_ck3_localization(SOURCE / relative)
                duplicate = values.keys() & parsed.keys()
                if duplicate:
                    errors.append(f"duplicate {language} localization across files: {sorted(duplicate)}")
                values.update(parsed)
            except (OSError, TranslationError, ValueError) as error:
                errors.append(f"invalid localization: {relative}: {error}")
        locs[language] = values
    english_keys = set(locs.get("english", {}))
    baseline = locs.get("simp_chinese", {})
    for language, values in locs.items():
        if set(values) != english_keys:
            errors.append(f"localization key inventories differ: {language}")
        if baseline and values.keys() == baseline.keys():
            try:
                assert_protected_tokens(baseline, values)
            except TranslationError as error:
                errors.append(f"invalid {language} localization formatting: {error}")
        for key, value in values.items():
            for referenced in re.findall(r"\$(sxad[\w.]+)\$", value):
                if referenced not in values:
                    errors.append(f"missing localization reference {language}: {key} -> {referenced}")
    references = set()
    for relative, source in texts.items():
        if relative.startswith("localization/"):
            continue
        try:
            clean = masked(source)
            fields = "title|desc|text|custom_tooltip|notification_text|show_as_unavailable_message|greeting"
            if relative.startswith("events/"):
                fields += "|name"
            references.update(re.findall(r"\b(?:" + fields + r")\s*=\s*(sxad[\w.]+)\b", clean))
            if relative.startswith("common/traits/"):
                for block in top_level_blocks(source):
                    if block.key.startswith("sxad_"):
                        references.update((f"trait_{block.key}", f"trait_{block.key}_desc"))
        except ValueError:
            # The first pass already records the malformed source. Continue so
            # an external attempt receives a complete RED validation report.
            continue
    for language, values in locs.items():
        for referenced in sorted(references - values.keys()):
            errors.append(f"missing script localization reference {language}: {referenced}")
    generated_count = 0
    try:
        from gen_runtime import render_outputs

        expected = render_outputs(game_root)
        generated_count = len(expected)
        outside = expected.keys() - RUNTIME_FILES
        if outside:
            errors.append(f"generator output outside reviewed runtime allowlist: {sorted(outside)}")
        for relative, content in expected.items():
            path = SOURCE / relative
            if not isinstance(content, bytes):
                errors.append(f"generator did not return bytes: {relative}")
            elif not path.is_file() or path.read_bytes() != content:
                errors.append(f"generated byte parity mismatch: {relative}")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"generated runtime validation failed: {error}")
    try:
        from compose_superman_qiang_key_art import rendered_bytes

        thumbnail = SOURCE / "thumbnail.png"
        if not thumbnail.is_file() or thumbnail.read_bytes() != rendered_bytes():
            errors.append("generated byte parity mismatch: thumbnail.png")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"cover projection validation failed: {error}")
    vanilla = []
    executable_sha = None
    if game_root is not None:
        try:
            from runtime_data import EXE_SHA256, ROMANCE_SOURCE_SHA256

            relative = "common/scripted_effects/00_romance_effects.txt"
            native_root = game_root / "game" if (game_root / "game" / relative).is_file() else game_root
            source_path = native_root / relative
            source_sha = sha256_file(source_path)
            vanilla.append({"path": str(source_path), "size": source_path.stat().st_size, "sha256": source_sha})
            if source_sha != ROMANCE_SOURCE_SHA256:
                errors.append("installed romance source SHA differs from reviewed 1.20.0.3 input")
            executable = native_root.parent / "binaries" / "ck3.exe"
            executable_sha = sha256_file(executable)
            if executable_sha != EXE_SHA256:
                errors.append("installed CK3 executable SHA differs from reviewed 1.20.0.3 executable")
        except (ImportError, OSError, ValueError) as error:
            errors.append(f"installed native source validation failed: {error}")
    revision = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    return {
        "schema": "sxad.static-validation.v1", "status": "RED" if errors else "GREEN", "errors": errors,
        "git_sha": revision, "runtime_file_count": len(RUNTIME_FILES), "source_files": hashes,
        "scripted_effect_counts": effect_counts,
        "localization_key_counts": {language: len(values) for language, values in locs.items()},
        "generated_file_count": generated_count,
        "vanilla_files": vanilla, "ck3_exe_sha256": executable_sha,
        "game_root": str(game_root) if game_root else None, "game_version_contract": GAME_VERSION,
        "evidence_layer": "static-structure-and-byte-contract", "ck3_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, help="optional CK3 installation or game directory for pinned source/executable SHA verification")
    parser.add_argument("--report", type=Path, help="new external evidence file; existing reports are never overwritten")
    args = parser.parse_args()
    try:
        if args.report is not None and args.report.exists():
            raise ValueError("report already exists; use a new attempt path")
        report = validate(args.game_root)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, ensure_ascii=True, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if not report["errors"] else 1
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"SXAD STATIC FAILED: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
