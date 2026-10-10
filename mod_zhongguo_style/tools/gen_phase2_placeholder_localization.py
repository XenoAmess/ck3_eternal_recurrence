#!/usr/bin/env python3
"""Keep authored key coverage in the seven non-authoring locales.

Daily development authors Simplified Chinese and English only. CK3 requires
every active language to expose the same keys. Preserve existing translated
values, insert missing keys in English authority order, and use explicit
English placeholders unless format-checked release candidates are supplied.
An explicit source migration may repair a proved existing token mismatch.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MOD_ROOT.parent / "tools"))
from translate_localization_minimax import (  # noqa: E402
    ENTRY,
    TranslationError,
    assert_protected_tokens,
    extract_candidate,
    parse_ck3_localization,
)

SOURCE = MOD_ROOT / "localization" / "english" / "zg361_l_english.yml"
START_KEY = "zg361_view_result_statement_decision"
LANGUAGES = (
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)
BOM = b"\xef\xbb\xbf"
PROTECTED_TERMS = ("3.75", "3.5", "3.25", "361", "KPI", "OKR", "PIP", "HC")


def phase2_lines() -> list[str]:
    lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith(f"{START_KEY}:")
        )
    except StopIteration as exc:
        raise ValueError(f"phase-two localization marker missing from {SOURCE}") from exc
    selected = [
        line
        for line in lines[start:]
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not selected or not selected[-1].lstrip().startswith("zg361.53.a:"):
        raise ValueError("phase-two English localization block has an unexpected boundary")
    return selected


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate release-candidate JSON key: {key}")
        result[key] = value
    return result


def outputs(candidates_json: Path | None = None,
            replace_token_drift_keys: tuple[str, ...] = ()) -> dict[Path, bytes]:
    phase2_lines()  # Preserve the original bounded English phase-two contract.
    source_values = parse_ck3_localization(SOURCE)
    source_by_key = {
        match[1]: line
        for line in SOURCE.read_text(encoding="utf-8-sig").splitlines()
        if (match := ENTRY.fullmatch(line))
    }
    if tuple(source_by_key) != tuple(source_values):
        raise ValueError("English authority entry inventory differs from parsed keys")
    additions: dict[str, object] = {}
    if len(set(replace_token_drift_keys)) != len(replace_token_drift_keys):
        raise ValueError("duplicate token-drift replacement key")
    if replace_token_drift_keys and candidates_json is None:
        raise ValueError("token-drift replacements require explicit release candidates")
    if candidates_json is not None:
        additions = json.loads(
            candidates_json.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_unique_json_pairs,
        )
        if not isinstance(additions, dict) or set(additions) != set(LANGUAGES):
            raise ValueError("release candidates must cover the seven target languages exactly")
    result: dict[Path, bytes] = {}
    for language in LANGUAGES:
        path = MOD_ROOT / "localization" / language / f"zg361_l_{language}.yml"
        existing_values = parse_ck3_localization(path) if path.is_file() else {}
        if set(existing_values) - set(source_values):
            raise ValueError(f"existing target contains keys outside English authority: {language}")
        candidates: dict[str, str] = {}
        if candidates_json is not None:
            values = additions[language]
            if not isinstance(values, dict) or set(values) - set(source_values):
                raise ValueError(f"invalid release-candidate key inventory: {language}")
            candidates = extract_candidate(json.dumps(values, ensure_ascii=False), tuple(values))
            assert_protected_tokens(
                {key: source_values[key] for key in candidates}, candidates, PROTECTED_TERMS
            )
            if set(replace_token_drift_keys) - set(candidates):
                raise ValueError(f"token-drift replacement key lacks a candidate: {language}")
            for key, value in candidates.items():
                if key not in existing_values or existing_values[key] == value:
                    continue
                if key not in replace_token_drift_keys:
                    raise ValueError(f"release candidates would replace an existing translation: {language}/{key}")
                try:
                    assert_protected_tokens(
                        {key: source_values[key]}, {key: existing_values[key]}, PROTECTED_TERMS
                    )
                except TranslationError:
                    pass
                else:
                    raise ValueError(f"existing translation has no token drift to repair: {language}/{key}")
        existing = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else [f"l_{language}:"]
        if not existing or existing[0] != f"l_{language}:":
            raise ValueError(f"target localization header differs: {language}")
        entry_lines: dict[str, str] = {}
        leading: dict[str, list[str]] = {}
        pending: list[str] = []
        for line in existing[1:]:
            match = ENTRY.fullmatch(line)
            if match:
                key = match[1]
                leading[key] = pending
                pending = []
                entry_lines[key] = line
            else:
                pending.append(line)
        lines = [existing[0]]
        for key in source_values:
            if key in entry_lines:
                lines.extend(leading[key])
                if key in replace_token_drift_keys and key in candidates:
                    lines.append(f' {key}:0 "{candidates[key]}"')
                else:
                    lines.append(entry_lines[key])
            elif key in candidates:
                lines.append(f' {key}:0 "{candidates[key]}"')
            else:
                lines.append(" # English development placeholder for an unauthored locale key.")
                lines.append(source_by_key[key])
        lines.extend(pending)
        result[path] = BOM + ("\n".join(lines) + "\n").encode("utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--candidates-json", type=Path,
                        help="Format-checked translations; existing values require a proved explicit token-drift migration")
    parser.add_argument("--replace-token-drift-key", action="append", default=[],
                        help="Explicit source migration; replaces only a proved protected-token mismatch")
    args = parser.parse_args(argv)
    stale: list[Path] = []
    for path, payload in outputs(args.candidates_json, tuple(args.replace_token_drift_key)).items():
        if args.check:
            if not path.is_file() or path.read_bytes() != payload:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    if stale:
        for path in stale:
            print(f"STALE: {path.relative_to(MOD_ROOT)}")
        return 1
    print(
        "GREEN: phase-two locale coverage "
        + ("is current" if args.check else "updated without replacing translations")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
