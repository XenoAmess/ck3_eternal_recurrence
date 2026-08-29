#!/usr/bin/env python3
"""Request audited JSON translation candidates from MiniMax-M3.

This tool deliberately never edits localization files. The caller selects the
source/reference files, target languages, and context; the tool only sends the
minimal localization payload, validates the response, and prints candidate JSON.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import http.client
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib import error, request


MODEL = "MiniMax-M3"
ENDPOINT = "https://api.minimaxi.com/v1/chat/completions"
API_KEY_ENV = "MINIMAX_API_KEY"
HEADER = re.compile(r"l_[a-z][a-z0-9_]*:")
ENTRY = re.compile(r'^ ([^:\s]+):\d+ "((?:[^"\\]|\\.)*)"$')
PROTECTED = re.compile(
    r"https?://[^\s<>\"'\\]+"
    r"|<[^<>\r\n]+>"
    r"|\[[^\[\]\r\n]+\]"
    r"|\$\{[^{}\r\n]+\}"
    r"|\{\{[^{}\r\n]+\}\}"
    r"|\{[^{}\r\n]+\}"
    r"|\$[^$\r\n]+\$"
    r"|@[A-Za-z0-9_.:/-]+!"
    r"|#[A-Za-z0-9_]+|#!"
    r"|§."
    r"|%(?:\d+\$)?[-+0#]*\d*(?:\.\d+)?[hlLzjt]*[diuoxXfFeEgGaAcspn%]"
    r"|\\."
)


class TranslationError(RuntimeError):
    """A safe-to-print translation or response validation failure."""


def find_icu_blocks(value: str) -> tuple[str, ...]:
    """Return balanced ICU plural/select expressions for verbatim protection.

    CK3 localization normally does not use ICU. Preserving a rare ICU block in
    full is safer than translating its nested syntax as plain text.
    """
    blocks: list[str] = []
    stack: list[int] = []
    for index, character in enumerate(value):
        if character == "{":
            stack.append(index)
        elif character == "}" and stack:
            start = stack.pop()
            if not stack:
                block = value[start : index + 1]
                if re.match(
                    r"^\{[^{},]+,\s*(?:plural|selectordinal|select)\s*,",
                    block,
                ):
                    blocks.append(block)
    return tuple(blocks)


def protected_tokens(value: str) -> tuple[str, ...]:
    return tuple(PROTECTED.findall(value)) + find_icu_blocks(value)


def count_unescaped_ascii_quotes(value: str) -> int:
    """Count quotes that would terminate a raw CK3 localization value."""

    count = 0
    for index, character in enumerate(value):
        if character != '"':
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and value[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            count += 1
    return count


def normalize_raw_ck3_quote_escapes(
    source: dict[str, str], candidate: dict[str, str]
) -> dict[str, str]:
    """Restore raw YML quote escapes that JSON decoding legitimately removes.

    CK3 source values are intentionally kept in their raw YML representation, so
    an embedded quote is the two-character token ``\"``. Models commonly return
    an ordinary quote because JSON already escapes it syntactically. Only values
    whose source contains that raw token are normalized; the protected-token gate
    still rejects any missing, added, or otherwise changed escape afterwards.
    """

    normalized: dict[str, str] = {}
    for key, value in candidate.items():
        if '\\"' not in source[key]:
            normalized[key] = value
            continue
        output: list[str] = []
        for index, character in enumerate(value):
            if character == '"':
                backslashes = 0
                cursor = index - 1
                while cursor >= 0 and value[cursor] == "\\":
                    backslashes += 1
                    cursor -= 1
                if backslashes % 2 == 0:
                    output.append("\\")
            output.append(character)
        normalized[key] = "".join(output)
    return normalized


def parse_ck3_localization(path: Path) -> dict[str, str]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise TranslationError(f"cannot read localization: {path}") from exc
    if not data.startswith(b"\xef\xbb\xbf"):
        raise TranslationError(f"localization lacks UTF-8 BOM: {path}")
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise TranslationError(f"localization is not valid UTF-8: {path}") from exc
    entries: dict[str, str] = {}
    header_seen = False
    for line_number, line in enumerate(lines, 1):
        if not line or line.lstrip().startswith("#"):
            continue
        if HEADER.fullmatch(line):
            if header_seen:
                raise TranslationError(f"multiple localization headers at {path}:{line_number}")
            if entries:
                raise TranslationError(f"localization header follows entries at {path}:{line_number}")
            header_seen = True
            continue
        match = ENTRY.fullmatch(line)
        if not match:
            raise TranslationError(f"malformed localization line at {path}:{line_number}")
        if not header_seen:
            raise TranslationError(f"localization entry precedes header at {path}:{line_number}")
        key, value = match.groups()
        if key in entries:
            raise TranslationError(f"duplicate localization key at {path}:{line_number}: {key}")
        entries[key] = value
    if not header_seen:
        raise TranslationError(f"localization header missing: {path}")
    if not entries:
        raise TranslationError(f"no CK3 localization entries found: {path}")
    return entries


def parse_target(value: str) -> tuple[str, str]:
    key, separator, display = value.partition("=")
    if not separator or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not display.strip():
        raise argparse.ArgumentTypeError("target must be key=Display Name")
    return key, display.strip()


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TranslationError(f"response JSON contains duplicate key: {key}")
        result[key] = value
    return result


def extract_candidate(content: str, keys: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(content, str) or not content.strip():
        raise TranslationError("response content is empty or not text")
    try:
        candidate = json.loads(content, object_pairs_hook=_reject_duplicate_json_keys)
    except json.JSONDecodeError as exc:
        raise TranslationError("response is not one strict JSON object") from exc
    if not isinstance(candidate, dict):
        raise TranslationError("response JSON is not an object")
    if set(candidate) != set(keys):
        missing = sorted(set(keys) - set(candidate))
        extra = sorted(set(candidate) - set(keys))
        raise TranslationError(f"response key set differs (missing={missing}, extra={extra})")
    non_string = sorted(
        key for key, value in candidate.items() if not isinstance(value, str)
    )
    if non_string:
        raise TranslationError(
            f"response contains non-string translation values: {non_string}"
        )
    return {key: candidate[key] for key in keys}


def assert_protected_tokens(
    source: dict[str, str],
    candidate: dict[str, str],
    explicit: tuple[str, ...] = (),
) -> None:
    errors: list[str] = []
    for key, source_value in source.items():
        expected = Counter(protected_tokens(source_value))
        actual = Counter(protected_tokens(candidate[key]))
        if actual != expected:
            errors.append(f"{key}: protected tokens {dict(actual)} != {dict(expected)}")
        expected_quotes = count_unescaped_ascii_quotes(source_value)
        actual_quotes = count_unescaped_ascii_quotes(candidate[key])
        if actual_quotes != expected_quotes:
            errors.append(
                f"{key}: unescaped ASCII quote count {actual_quotes} != "
                f"{expected_quotes}"
            )
        for token in explicit:
            expected_count = source_value.count(token)
            actual_count = candidate[key].count(token)
            if expected_count and actual_count < expected_count:
                errors.append(
                    f"{key}: explicit token {token!r} count {actual_count} < {expected_count}"
                )
    if errors:
        raise TranslationError("protected-token mismatch: " + "; ".join(errors))


def make_prompt(
    source_language: str,
    reference_languages: tuple[str, ...],
    target_language: str,
    context: str,
    source: dict[str, str],
    references: tuple[dict[str, str], ...],
    explicit_protected: tuple[str, ...] = (),
) -> str:
    entries = {
        key: {
            "source": value,
            "references": [reference[key] for reference in references],
        }
        for key, value in source.items()
    }
    protected = sorted(
        {token for value in source.values() for token in protected_tokens(value)}
        | set(explicit_protected)
    )
    return f"""You only translate localization strings. Do not write code, explain, add, remove, merge, or split entries.

Source language: {source_language}
Reference languages: {', '.join(reference_languages) if reference_languages else 'none'}
Target language: {target_language}
Context: {context}

Requirements:
1. Return exactly one valid flat JSON object with the same {len(source)} keys and translated string values.
2. Preserve meaning, tone, concise game-interface style, punctuation intent, and wordplay where practical.
3. Preserve every protected-token occurrence already present, including spelling. Do not remove or alter one. A required product term may be introduced or repeated only when the reference meaning needs it.
4. Do not output Markdown, reasoning, commentary, code, or a second JSON object.
5. Every JSON value MUST be one string. Never return nested objects, arrays, numbers, booleans, or null.

Required output shape (using the real input keys): {{"key_one":"translated text","key_two":"translated text"}}

Protected tokens:
{json.dumps(protected, ensure_ascii=False)}

Translation input:
{json.dumps(entries, ensure_ascii=False, separators=(",", ":"))}
"""


def request_candidate(
    target_key: str,
    target_name: str,
    prompt: str,
    source: dict[str, str],
    api_key: str,
    max_completion_tokens: int,
    explicit_protected: tuple[str, ...] = (),
    raw_response_sink: Callable[[int, bytes], None] | None = None,
) -> tuple[str, dict[str, str]]:
    body = json.dumps(
        {
            "model": MODEL,
            "max_completion_tokens": max_completion_tokens,
            "temperature": 0.2,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    last_error = "unknown response failure"
    for attempt in range(2):
        req = request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=180) as response:
                raw_response = response.read()
            if raw_response_sink is not None:
                raw_response_sink(attempt + 1, raw_response)
            payload = json.loads(raw_response.decode("utf-8"))
            if not isinstance(payload, dict):
                raise TranslationError("response envelope is not an object")
            base_response = payload.get("base_resp")
            if isinstance(base_response, dict) and base_response.get("status_code", 0) != 0:
                raise TranslationError("MiniMax returned a nonzero API status")
            if payload.get("input_sensitive") or payload.get("output_sensitive"):
                raise TranslationError("MiniMax rejected sensitive input or output")
            choice = payload["choices"][0]
            if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
                raise TranslationError("response did not finish normally")
            message = choice["message"]
            if not isinstance(message, dict):
                raise TranslationError("response message is not an object")
            content = message.get("content")
            candidate = extract_candidate(content, tuple(source))
            candidate = normalize_raw_ck3_quote_escapes(source, candidate)
            assert_protected_tokens(source, candidate, explicit_protected)
            return target_key, candidate
        except error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if raw_response_sink is not None:
                error_body = exc.read()
                if error_body:
                    raw_response_sink(attempt + 1, error_body)
            if exc.code not in {408, 429} and exc.code < 500:
                raise TranslationError(f"{target_name} translation failed: {last_error}") from exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if not attempt and retry_after and retry_after.isdigit():
                time.sleep(min(int(retry_after), 30))
                continue
        except TranslationError as exc:
            last_error = str(exc)
        except (
            error.URLError,
            http.client.HTTPException,
            KeyError,
            IndexError,
            OSError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            TimeoutError,
        ) as exc:
            last_error = type(exc).__name__
        if not attempt:
            time.sleep(2)
    raise TranslationError(f"{target_name} translation failed after two attempts: {last_error}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-language", required=True)
    parser.add_argument("--reference", action="append", type=Path, default=[])
    parser.add_argument("--reference-language", action="append", default=[])
    parser.add_argument("--target", action="append", type=parse_target, required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help="translate only this source key; repeat for a caller-selected small batch",
    )
    parser.add_argument(
        "--protect",
        action="append",
        default=[],
        help="additional exact token or product name to preserve; repeat as needed",
    )
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument(
        "--max-completion-tokens",
        "--max-tokens",
        dest="max_completion_tokens",
        type=int,
        default=12000,
    )
    args = parser.parse_args(argv)
    try:
        if len(args.reference) != len(args.reference_language):
            raise TranslationError("each --reference requires one --reference-language")
        if not 1 <= args.workers <= 4:
            raise TranslationError("--workers must be between 1 and 4")
        if not 1000 <= args.max_completion_tokens <= 524288:
            raise TranslationError("--max-completion-tokens must be between 1000 and 524288")
        targets = dict(args.target)
        if len(targets) != len(args.target):
            raise TranslationError("target keys must be unique")
        if any(not token for token in args.protect) or len(set(args.protect)) != len(args.protect):
            raise TranslationError("--protect values must be nonempty and unique")
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise TranslationError(f"{API_KEY_ENV} is not configured")
        full_source = parse_ck3_localization(args.source)
        selected_keys = args.key or list(full_source)
        if len(set(selected_keys)) != len(selected_keys):
            raise TranslationError("--key values must be unique")
        unknown_keys = [key for key in selected_keys if key not in full_source]
        if unknown_keys:
            raise TranslationError(f"unknown source keys requested: {unknown_keys}")
        source = {key: full_source[key] for key in selected_keys}
        full_references = tuple(parse_ck3_localization(path) for path in args.reference)
        references: list[dict[str, str]] = []
        for path, reference in zip(args.reference, full_references):
            missing = [key for key in selected_keys if key not in reference]
            if missing:
                raise TranslationError(f"reference lacks selected keys at {path}: {missing}")
            references.append({key: reference[key] for key in selected_keys})
        reference_tuple = tuple(references)
        results: dict[str, dict[str, str]] = {}
        failures: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=min(args.workers, len(targets))) as executor:
            futures = {
                executor.submit(
                    request_candidate,
                    target_key,
                    target_name,
                    make_prompt(
                        args.source_language,
                        tuple(args.reference_language),
                        target_name,
                        args.context,
                        source,
                        reference_tuple,
                        tuple(args.protect),
                    ),
                    source,
                    api_key,
                    args.max_completion_tokens,
                    tuple(args.protect),
                ): target_key
                for target_key, target_name in targets.items()
            }
            for future in as_completed(futures):
                target_key = futures[future]
                try:
                    key, candidate = future.result()
                    results[key] = candidate
                except TranslationError as exc:
                    failures[target_key] = str(exc)
        print(
            json.dumps(
                {key: results[key] for key in targets if key in results},
                ensure_ascii=False,
                indent=2,
            )
        )
        if failures:
            for key in targets:
                if key in failures:
                    print(f"MINIMAX TARGET FAILED [{key}]: {failures[key]}", file=sys.stderr)
            return 1
        return 0
    except TranslationError as exc:
        print(f"MINIMAX TRANSLATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
