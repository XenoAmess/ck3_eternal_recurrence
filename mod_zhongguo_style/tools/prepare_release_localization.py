#!/usr/bin/env python3
"""Generate, preserve, apply, and audit release localization candidates.

MiniMax-M3 is used only through the repository's read-only candidate caller.
This orchestrator selects small key batches, stores every returned JSON object
outside the repository, and applies candidates only in an explicit second step.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = MOD_ROOT.parent
ROOT_TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(ROOT_TOOLS))
sys.path.insert(0, str(MOD_ROOT / "tools"))

import translate_localization_minimax as minimax  # noqa: E402
from gen_361_mechanisms import (  # noqa: E402
    release_translation_source_sha256,
)
from zg361_mechanism_data import load_mechanisms  # noqa: E402


LANGUAGES = {
    "french": "French (France)",
    "german": "German",
    "japanese": "Japanese",
    "korean": "Korean",
    "polish": "Polish",
    "russian": "Russian",
    "spanish": "Spanish (Spain)",
}
PROTECTED_TERMS = ("3.75", "3.5", "3.25", "361", "KPI", "OKR", "PIP", "HC")
CORE_CONTEXT = (
    "Crusader Kings III ZhongGuo 361 performance-review UI. Preserve the dry, "
    "satirical Chinese internet-company tone while keeping buttons and tooltips concise."
)
MECHANISM_CONTEXT = (
    "Crusader Kings III ZhongGuo 361 performance-policy cards. Each five-key group is one "
    "distinct policy dilemma; preserve its concrete decision, tradeoff, humor, and concise UI tone."
)
ENTRY = re.compile(r'^(?P<prefix> (?P<key>[^:\s]+):\d+ ")(?P<value>(?:[^"\\]|\\.)*)(?P<suffix>")$')
MECHANISM_KEY = re.compile(r"^zg361m\.(\d+)\.(?:t|desc|a|b|c)$")
TECHNICAL_WORDS = re.compile(
    r"\b(?:KPI|OKR|PIP|HC|AI|CK3|DLC|UI|A|B|C|P0|P1|P2|P3)\b",
    re.I,
)
ALLOWED_IDENTICAL = {
    "german": {"zg361_scoreboard_col_status"},
    "polish": {"zg361_scoreboard_col_status"},
}


@dataclass(frozen=True)
class SourceSpec:
    name: str
    english: Path
    chinese: Path
    context: str


@dataclass(frozen=True)
class Batch:
    source: str
    name: str
    keys: tuple[str, ...]


SOURCES = {
    "core": SourceSpec(
        "core",
        MOD_ROOT / "localization" / "english" / "zg361_l_english.yml",
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml",
        CORE_CONTEXT,
    ),
    "mechanisms": SourceSpec(
        "mechanisms",
        MOD_ROOT / "localization" / "english" / "zg361_mechanisms_l_english.yml",
        MOD_ROOT
        / "localization"
        / "simp_chinese"
        / "zg361_mechanisms_l_simp_chinese.yml",
        MECHANISM_CONTEXT,
    ),
}


class ReleaseLocalizationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new_or_equal(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ReleaseLocalizationError(f"refusing to overwrite differing artifact: {path}")
        return
    path.write_bytes(data)


def build_batches() -> tuple[Batch, ...]:
    core = tuple(minimax.parse_ck3_localization(SOURCES["core"].english))
    mechanism = tuple(minimax.parse_ck3_localization(SOURCES["mechanisms"].english))
    batches: list[Batch] = []
    for index in range(0, len(core), 80):
        batches.append(
            Batch("core", f"core_{index // 80 + 1:02d}", core[index : index + 80])
        )
    common = tuple(key for key in mechanism if MECHANISM_KEY.fullmatch(key) is None)
    by_id: dict[int, list[str]] = {identifier: [] for identifier in range(1, 362)}
    for key in mechanism:
        match = MECHANISM_KEY.fullmatch(key)
        if match:
            by_id[int(match.group(1))].append(key)
    for identifier, keys in by_id.items():
        if len(keys) != 5:
            raise ReleaseLocalizationError(
                f"mechanism {identifier:03d} has {len(keys)} localization keys, expected 5"
            )
    for start in range(1, 362, 25):
        end = min(start + 24, 361)
        keys = tuple(
            key
            for identifier in range(start, end + 1)
            for key in by_id[identifier]
        )
        if start == 1:
            keys = common + keys
        batches.append(Batch("mechanisms", f"mechanisms_{start:03d}_{end:03d}", keys))
    covered = tuple(key for batch in batches if batch.source == "mechanisms" for key in batch.keys)
    if covered != mechanism:
        raise ReleaseLocalizationError("mechanism localization batching changed source key order")
    if len(batches) != 17:
        raise ReleaseLocalizationError(f"expected 17 translation batches, got {len(batches)}")
    return tuple(batches)


def plan_payload() -> dict[str, object]:
    batches = build_batches()
    return {
        "schema": 1,
        "model": minimax.MODEL,
        "languages": LANGUAGES,
        "protected_terms": list(PROTECTED_TERMS),
        "sources": {
            name: {
                "english": spec.english.relative_to(REPO_ROOT).as_posix(),
                "english_sha256": sha256(spec.english),
                "simp_chinese": spec.chinese.relative_to(REPO_ROOT).as_posix(),
                "simp_chinese_sha256": sha256(spec.chinese),
            }
            for name, spec in SOURCES.items()
        },
        "batches": [
            {"source": batch.source, "name": batch.name, "keys": list(batch.keys)}
            for batch in batches
        ],
        "request_count": len(batches) * len(LANGUAGES),
    }


def candidate_path(root: Path, batch: Batch, language: str) -> Path:
    return root / "candidates" / batch.source / batch.name / f"{language}.json"


def load_candidate(path: Path, source: dict[str, str]) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseLocalizationError(f"cannot read candidate {path}: {error}") from error
    candidate = minimax.extract_candidate(
        json.dumps(payload, ensure_ascii=False), tuple(source)
    )
    minimax.assert_protected_tokens(source, candidate, PROTECTED_TERMS)
    for key, value in candidate.items():
        if "\r" in value or "\n" in value:
            raise ReleaseLocalizationError(f"candidate contains a literal newline: {path} [{key}]")
    return candidate


def is_translatable_english(value: str) -> bool:
    stripped = TECHNICAL_WORDS.sub("", value)
    stripped = minimax.PROTECTED.sub("", stripped)
    return re.search(r"[A-Za-z]{2,}", stripped) is not None


def candidate_residuals(
    english: dict[str, str], candidate: dict[str, str], language: str | None = None
) -> list[str]:
    return [
        key
        for key, value in candidate.items()
        if value == english[key]
        and is_translatable_english(value)
        and key not in ALLOWED_IDENTICAL.get(language or "", set())
    ]


def request_with_bisection(
    language: str,
    spec: SourceSpec,
    english: dict[str, str],
    chinese: dict[str, str],
    api_key: str,
    max_tokens: int,
) -> dict[str, str]:
    """Retry malformed model batches as smaller, still-minimal requests."""

    def request_subset(keys: tuple[str, ...]) -> dict[str, str]:
        source = {key: english[key] for key in keys}
        reference = {key: chinese[key] for key in keys}
        try:
            _, result = minimax.request_candidate(
                language,
                LANGUAGES[language],
                minimax.make_prompt(
                    "English",
                    ("Simplified Chinese",),
                    LANGUAGES[language],
                    spec.context
                    + " This is a strict flat-string JSON batch; preserve escaped ASCII quotes exactly.",
                    source,
                    (reference,),
                    PROTECTED_TERMS,
                ),
                source,
                api_key,
                max_tokens,
                PROTECTED_TERMS,
            )
            return result
        except minimax.TranslationError as error:
            message = str(error)
            transport_failure = "HTTP " in message or message.endswith(
                ("URLError", "TimeoutError", "OSError", "IncompleteRead")
            )
            if len(keys) <= 1 or transport_failure:
                raise
            middle = len(keys) // 2
            left = request_subset(keys[:middle])
            right = request_subset(keys[middle:])
            return {key: (left if key in left else right)[key] for key in keys}

    return request_subset(tuple(english))


def translate(root: Path, workers: int, max_tokens: int) -> int:
    if not os.environ.get(minimax.API_KEY_ENV):
        raise ReleaseLocalizationError(f"{minimax.API_KEY_ENV} is not configured")
    plan = plan_payload()
    write_new_or_equal(root / "translation-plan.json", json_bytes(plan))
    failures: list[dict[str, str]] = []
    for batch in build_batches():
        spec = SOURCES[batch.source]
        full_english = minimax.parse_ck3_localization(spec.english)
        full_chinese = minimax.parse_ck3_localization(spec.chinese)
        batch_english = {key: full_english[key] for key in batch.keys}
        request_keys = tuple(
            key for key in batch.keys if is_translatable_english(full_english[key])
        )
        english = {key: full_english[key] for key in request_keys}
        chinese = {key: full_chinese[key] for key in request_keys}
        pending: list[str] = []
        for language in LANGUAGES:
            path = candidate_path(root, batch, language)
            if path.is_file():
                load_candidate(path, batch_english)
            else:
                pending.append(language)
        if not pending:
            print(f"SKIP {batch.name}: {len(LANGUAGES)} preserved candidates")
            continue
        print(f"REQUEST {batch.name}: {len(batch.keys)} keys x {len(pending)} languages")
        with ThreadPoolExecutor(max_workers=min(workers, len(pending))) as executor:
            futures = {
                executor.submit(
                    request_with_bisection,
                    language,
                    spec,
                    english,
                    chinese,
                    os.environ[minimax.API_KEY_ENV],
                    max_tokens,
                ): language
                for language in pending
            }
            for future in as_completed(futures):
                language = futures[future]
                try:
                    translated = future.result()
                    candidate = {
                        key: translated.get(key, batch_english[key])
                        for key in batch.keys
                    }
                    minimax.assert_protected_tokens(
                        batch_english, candidate, PROTECTED_TERMS
                    )
                    residuals = candidate_residuals(
                        batch_english, candidate, language
                    )
                    if residuals:
                        raise ReleaseLocalizationError(
                            f"untranslated English values: {residuals[:12]}"
                        )
                    write_new_or_equal(
                        candidate_path(root, batch, language), json_bytes(candidate)
                    )
                    print(f"  PASS {language}")
                except (minimax.TranslationError, ReleaseLocalizationError) as error:
                    safe_error = {
                        "batch": batch.name,
                        "language": language,
                        "error": str(error),
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                    error_path = root / "errors" / f"{stamp}_{batch.name}_{language}.json"
                    write_new_or_equal(error_path, json_bytes(safe_error))
                    failures.append(safe_error)
                    print(f"  RED {language}: {error}", file=sys.stderr)
    missing = [
        str(candidate_path(root, batch, language))
        for batch in build_batches()
        for language in LANGUAGES
        if not candidate_path(root, batch, language).is_file()
    ]
    completion = {
        "schema": 1,
        "complete": not missing,
        "candidate_count": len(build_batches()) * len(LANGUAGES) - len(missing),
        "expected_candidate_count": len(build_batches()) * len(LANGUAGES),
        "missing": missing,
        "failures_this_attempt": failures,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(root / "attempts" / f"{stamp}.json", json_bytes(completion))
    if missing:
        print(f"RED: {len(missing)} candidate batch/language files remain missing")
        return 1
    index = []
    for batch in build_batches():
        for language in LANGUAGES:
            path = candidate_path(root, batch, language)
            index.append(
                {
                    "batch": batch.name,
                    "language": language,
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    write_new_or_equal(root / "complete-index.json", json_bytes({"schema": 1, "files": index}))
    print(f"GREEN: preserved {len(index)} MiniMax candidate files in {root}")
    return 0


def collected_candidates(root: Path, source_name: str, language: str) -> dict[str, str]:
    spec = SOURCES[source_name]
    english = minimax.parse_ck3_localization(spec.english)
    result: dict[str, str] = {}
    for batch in build_batches():
        if batch.source != source_name:
            continue
        subset = {key: english[key] for key in batch.keys}
        candidate = load_candidate(candidate_path(root, batch, language), subset)
        residuals = candidate_residuals(subset, candidate, language)
        if residuals:
            raise ReleaseLocalizationError(
                f"{language}/{batch.name} contains English placeholders: {residuals[:12]}"
            )
        result.update(candidate)
    if tuple(result) != tuple(english):
        raise ReleaseLocalizationError(f"candidate order/coverage mismatch: {source_name}/{language}")
    return result


def merge_raw_yml(path: Path, translations: dict[str, str]) -> bytes:
    data = path.read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise ReleaseLocalizationError(f"target yml lacks UTF-8 BOM: {path}")
    lines = data.decode("utf-8-sig").splitlines()
    seen: list[str] = []
    output: list[str] = []
    for key, value in translations.items():
        if ENTRY.fullmatch(f' {key}:0 "{value}"') is None:
            raise ReleaseLocalizationError(
                f"candidate is not safe CK3 localization syntax: {path} [{key}]"
            )
    for line in lines:
        match = ENTRY.fullmatch(line)
        if match and match.group("key") in translations:
            key = match.group("key")
            output.append(match.group("prefix") + translations[key] + match.group("suffix"))
            seen.append(key)
        else:
            output.append(line)
    if tuple(seen) != tuple(translations):
        raise ReleaseLocalizationError(f"target yml key/order mismatch while merging: {path}")
    return b"\xef\xbb\xbf" + ("\n".join(output) + "\n").encode("utf-8")


def decode_raw_yml_value(value: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value):
            output.append(value[index + 1])
            index += 2
        else:
            output.append(value[index])
            index += 1
    return "".join(output)


def apply_candidates(root: Path) -> int:
    expected_plan = json_bytes(plan_payload())
    plan_path = root / "translation-plan.json"
    if not plan_path.is_file() or plan_path.read_bytes() != expected_plan:
        raise ReleaseLocalizationError("candidate plan is missing or source files changed")
    mechanism_digest = release_translation_source_sha256(load_mechanisms(MOD_ROOT))
    changed: list[str] = []
    for language in LANGUAGES:
        core = collected_candidates(root, "core", language)
        core_target = (
            MOD_ROOT / "localization" / language / f"zg361_l_{language}.yml"
        )
        core_data = merge_raw_yml(core_target, core)
        if core_target.read_bytes() != core_data:
            core_target.write_bytes(core_data)
            changed.append(core_target.relative_to(MOD_ROOT).as_posix())

        mechanism_raw = collected_candidates(root, "mechanisms", language)
        catalog = {
            "schema": 1,
            "language": language,
            "source_sha256": mechanism_digest,
            "translations": {
                key: decode_raw_yml_value(value) for key, value in mechanism_raw.items()
            },
        }
        catalog_path = MOD_ROOT / "tools" / "mechanism_translations" / f"{language}.json"
        catalog_data = json_bytes(catalog)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        if not catalog_path.is_file() or catalog_path.read_bytes() != catalog_data:
            catalog_path.write_bytes(catalog_data)
            changed.append(catalog_path.relative_to(MOD_ROOT).as_posix())
    apply_record = {
        "schema": 1,
        "candidate_root": str(root.resolve()),
        "mechanism_source_sha256": mechanism_digest,
        "changed_files": changed,
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_new_or_equal(root / "apply" / f"{stamp}.json", json_bytes(apply_record))
    print(f"GREEN: applied reviewed candidates to {len(changed)} authority/target files")
    print("NEXT: run gen_361_mechanisms.py to render the seven generated yml files")
    return 0


def audit() -> int:
    errors: list[str] = []
    report: dict[str, object] = {"schema": 1, "languages": {}}
    for language in LANGUAGES:
        language_report: dict[str, object] = {}
        for source_name, spec in SOURCES.items():
            english = minimax.parse_ck3_localization(spec.english)
            target_path = (
                MOD_ROOT
                / "localization"
                / language
                / spec.english.name.replace("_english.yml", f"_{language}.yml")
            )
            target = minimax.parse_ck3_localization(target_path)
            if tuple(target) != tuple(english):
                errors.append(f"key/order mismatch: {target_path}")
                continue
            try:
                minimax.assert_protected_tokens(english, target, PROTECTED_TERMS)
            except minimax.TranslationError as error:
                errors.append(f"{target_path}: {error}")
            residuals = candidate_residuals(english, target, language)
            if residuals:
                errors.append(f"English placeholders in {target_path}: {residuals[:12]}")
            target_chars = {
                "japanese": len(re.findall(r"[ぁ-んァ-ン一-龯]", "".join(target.values()))),
                "korean": len(re.findall(r"[가-힣]", "".join(target.values()))),
                "russian": len(re.findall(r"[А-Яа-яЁё]", "".join(target.values()))),
            }.get(language)
            if target_chars == 0:
                errors.append(f"no expected target-script characters in {target_path}")
            language_report[source_name] = {
                "entries": len(target),
                "exact_english_residuals": len(residuals),
                "target_script_characters": target_chars,
                "sha256": sha256(target_path),
            }
        report["languages"][language] = language_report
    if errors:
        print(f"RED: {len(errors)} release-localization problem(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("GREEN: seven-language structure, tokens, scripts, and English-placeholder audit passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    translate_parser = subparsers.add_parser("translate")
    translate_parser.add_argument("--artifact-root", type=Path, required=True)
    translate_parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    translate_parser.add_argument("--max-completion-tokens", type=int, default=12000)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--artifact-root", type=Path, required=True)
    subparsers.add_parser("audit")
    args = parser.parse_args(argv)
    try:
        if args.command == "translate":
            return translate(args.artifact_root, args.workers, args.max_completion_tokens)
        if args.command == "apply":
            return apply_candidates(args.artifact_root)
        return audit()
    except (ReleaseLocalizationError, minimax.TranslationError, OSError, ValueError) as error:
        print(f"RED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
