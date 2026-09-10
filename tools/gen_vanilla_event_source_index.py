#!/usr/bin/env python3
"""Generate the exact-build lexical source index for reviewed vanilla events.

The index deliberately calls references *caller candidates*.  Finding an exact
event-definition token in Paradox script is useful source provenance, but does
not by itself prove that the enclosing branch executes at runtime.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Final, Iterable, Mapping


REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC: Final = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    SOURCE_INDEX_SCHEMA,
    SOURCE_INDEX_SCHEMA_VERSION,
    compute_source_index_dataset_sha256,
)


DEFAULT_OUTPUT: Final = (
    AUTOPLAYER_SRC
    / "xar_autoplayer"
    / "vanilla_events"
    / "data"
    / "source_index_1_19_0_6.json"
)
_SOURCE_SUFFIXES: Final = (".txt",)


class SourceIndexGenerationError(RuntimeError):
    """Raised when the local CK3 tree cannot prove the frozen source index."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _read_script(path: Path) -> str:
    payload = path.read_bytes()
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        # A small amount of stock Clausewitz data remains Windows encoded.
        return payload.decode("cp1252")


def _relative_game_path(path: Path, game_data_dir: Path) -> str:
    return path.relative_to(game_data_dir).as_posix()


def _script_files(root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in _SOURCE_SUFFIXES
        )
    )


def _default_game_dir() -> Path:
    configured = os.environ.get("XAR_CK3_GAME_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        (
            REPOSITORY_ROOT / "Crusader Kings III",
            REPOSITORY_ROOT.parent / "Crusader Kings III",
        )
    )
    for candidate in candidates:
        if (candidate / "binaries" / "ck3.exe").is_file():
            return candidate.resolve()
    return candidates[0].resolve() if candidates else REPOSITORY_ROOT.resolve()


def validate_exact_game_dir(game_dir: Path) -> tuple[Path, Path]:
    """Return normalized install/data roots after proving the exact EXE."""
    install_dir = game_dir.resolve()
    executable = install_dir / "binaries" / "ck3.exe"
    if not executable.is_file():
        raise SourceIndexGenerationError(
            f"missing frozen CK3 executable: {executable}"
        )
    observed_sha256 = _sha256_bytes(executable.read_bytes())
    if observed_sha256 != EXACT_CK3_EXE_SHA256:
        raise SourceIndexGenerationError(
            "unexpected ck3.exe SHA-256: "
            f"expected {EXACT_CK3_EXE_SHA256}, observed {observed_sha256}"
        )
    game_data_dir = install_dir / "game"
    for required in (game_data_dir / "events", game_data_dir / "common"):
        if not required.is_dir():
            raise SourceIndexGenerationError(
                f"missing exact-build source root: {required}"
            )
    return install_dir, game_data_dir


def _token_alternation(event_keys: Iterable[str]) -> str:
    # Longest first avoids prefix backtracking for keys such as x.1 / x.10.
    return "|".join(
        sorted((re.escape(key) for key in event_keys), key=len, reverse=True)
    )


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _file_record(
    path: Path,
    *,
    game_data_dir: Path,
    line: int,
    column: int | None = None,
    file_sha256_by_path: dict[Path, str],
) -> dict[str, object]:
    file_sha256 = file_sha256_by_path.get(path)
    if file_sha256 is None:
        file_sha256 = _sha256_bytes(path.read_bytes())
        file_sha256_by_path[path] = file_sha256
    record: dict[str, object] = {
        "relative_path": _relative_game_path(path, game_data_dir),
        "line": line,
        "file_sha256": file_sha256,
    }
    if column is not None:
        record["column"] = column
    return record


def build_source_index(
    game_dir: Path,
    *,
    event_keys: Iterable[str] | None = None,
) -> dict[str, object]:
    """Scan one frozen CK3 install and return a deterministic JSON document."""
    _, game_data_dir = validate_exact_game_dir(game_dir)
    keys = tuple(
        sorted(
            event_keys
            if event_keys is not None
            else DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
        )
    )
    if not keys or any(not isinstance(key, str) or not key for key in keys):
        raise SourceIndexGenerationError("event key catalog must be non-empty strings")
    if len(keys) != len(set(keys)):
        raise SourceIndexGenerationError("event key catalog contains duplicates")

    alternation = _token_alternation(keys)
    definition_pattern = re.compile(
        rf"(?m)^[ \t]*(?P<key>{alternation})[ \t]*=[ \t]*\{{"
    )
    token_pattern = re.compile(
        rf"(?<![A-Za-z0-9_.])(?P<key>{alternation})(?![A-Za-z0-9_.])"
    )
    namespace_pattern = re.compile(
        r"(?m)^[ \t]*namespace[ \t]*=[ \t]*([A-Za-z0-9_]+)"
    )

    events_root = game_data_dir / "events"
    event_files = _script_files(events_root)
    text_by_path = {path: _read_script(path) for path in event_files}
    definitions: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    namespaces_by_path: dict[Path, frozenset[str]] = {}
    for path, text in text_by_path.items():
        namespaces_by_path[path] = frozenset(namespace_pattern.findall(text))
        for match in definition_pattern.finditer(text):
            # The group start, rather than match start, is required: horizontal
            # whitespace is legal, but a definition must never inherit a prior
            # blank line as its source location.
            definitions[match.group("key")].append(
                (path, _line_number(text, match.start("key")))
            )

    missing = tuple(key for key in keys if not definitions[key])
    ambiguous = tuple(key for key in keys if len(definitions[key]) > 1)
    if missing or ambiguous:
        raise SourceIndexGenerationError(
            "event definitions are not unique: "
            f"missing={list(missing)!r}, ambiguous={list(ambiguous)!r}"
        )

    namespace_mismatches = []
    for key in keys:
        definition_path, _ = definitions[key][0]
        namespace = key.rsplit(".", 1)[0]
        if namespace not in namespaces_by_path[definition_path]:
            namespace_mismatches.append(
                (
                    key,
                    _relative_game_path(definition_path, game_data_dir),
                    sorted(namespaces_by_path[definition_path]),
                )
            )
    if namespace_mismatches:
        raise SourceIndexGenerationError(
            f"event namespace mismatch: {namespace_mismatches!r}"
        )

    scan_files = tuple(
        sorted(
            set(_script_files(events_root)).union(
                _script_files(game_data_dir / "common")
            )
        )
    )
    candidates: dict[str, list[tuple[Path, int, int]]] = defaultdict(list)
    for path in scan_files:
        text = text_by_path.get(path)
        if text is None:
            text = _read_script(path)
            text_by_path[path] = text
        for line_number, source_line in enumerate(text.splitlines(), start=1):
            # Comments are prose or disabled script, not lexical caller
            # candidates. CK3's data uses '#' as the line-comment delimiter.
            code = source_line.split("#", 1)[0]
            for match in token_pattern.finditer(code):
                key = match.group("key")
                if (path, line_number) == definitions[key][0]:
                    continue
                candidates[key].append((path, line_number, match.start("key") + 1))

    file_sha256_by_path: dict[Path, str] = {}
    event_rows: dict[str, dict[str, object]] = {}
    external_event_count = 0
    same_file_only_event_count = 0
    selected_candidate_paths: set[Path] = set()
    selected_candidate_count = 0
    for key in keys:
        definition_path, definition_line = definitions[key][0]
        external = tuple(
            candidate
            for candidate in candidates[key]
            if candidate[0] != definition_path
        )
        if external:
            selected = external
            resolution = "external-definition-file"
            external_event_count += 1
        else:
            selected = tuple(candidates[key])
            resolution = "same-definition-file-only"
            same_file_only_event_count += 1
        if not selected:
            raise SourceIndexGenerationError(
                f"event has no lexical caller candidate: {key}"
            )
        selected_candidate_count += len(selected)
        selected_candidate_paths.update(path for path, _, _ in selected)
        namespace = key.rsplit(".", 1)[0]
        event_rows[key] = {
            "namespace": namespace,
            "definition": _file_record(
                definition_path,
                game_data_dir=game_data_dir,
                line=definition_line,
                file_sha256_by_path=file_sha256_by_path,
            ),
            "caller_candidate_resolution": resolution,
            "caller_candidates": [
                {
                    **_file_record(
                        path,
                        game_data_dir=game_data_dir,
                        line=line,
                        column=column,
                        file_sha256_by_path=file_sha256_by_path,
                    ),
                    "kind": "exact-token-lexical-candidate",
                }
                for path, line, column in selected
            ],
        }

    document: dict[str, object] = {
        "schema": SOURCE_INDEX_SCHEMA,
        "schema_version": SOURCE_INDEX_SCHEMA_VERSION,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "scan_policy": {
            "definition_roots": ["events"],
            "caller_candidate_roots": ["events", "common"],
            "source_suffixes": list(_SOURCE_SUFFIXES),
            "token_boundary": "not-adjacent-to-ASCII-alphanumeric-underscore-or-dot",
            "comments": "strip-from-first-number-sign",
            "candidate_selection": (
                "prefer-external-definition-file; "
                "otherwise-retain-same-definition-file-only"
            ),
            "candidate_semantics": "lexical-candidate-not-proven-runtime-caller",
        },
        "audit": {
            "registered_event_count": len(keys),
            "unique_definition_count": len(keys),
            "definition_file_count": len(
                {definitions[key][0][0] for key in keys}
            ),
            "missing_definition_count": 0,
            "ambiguous_definition_count": 0,
            "namespace_mismatch_count": 0,
            "caller_candidate_reference_count": selected_candidate_count,
            "external_caller_event_count": external_event_count,
            "same_file_only_caller_event_count": same_file_only_event_count,
            "caller_candidate_file_count": len(selected_candidate_paths),
        },
        "events": event_rows,
    }
    document["dataset_sha256"] = compute_source_index_dataset_sha256(document)
    return document


def render_source_index(document: Mapping[str, object]) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def write_or_check(output: Path, payload: bytes, *, check: bool) -> None:
    if check:
        if not output.is_file():
            raise SourceIndexGenerationError(
                f"frozen source index is missing: {output}"
            )
        if output.read_bytes() != payload:
            raise SourceIndexGenerationError(
                f"frozen source index is stale: {output}"
            )
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=_default_game_dir(),
        help="CK3 installation root containing binaries/ck3.exe and game/",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the frozen output is byte-identical",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        document = build_source_index(args.game_dir)
        payload = render_source_index(document)
        write_or_check(args.output, payload, check=args.check)
    except (OSError, UnicodeError, SourceIndexGenerationError) as exc:
        print(f"VANILLA EVENT SOURCE INDEX: RED: {exc}", file=sys.stderr)
        return 1
    audit = document["audit"]
    assert isinstance(audit, Mapping)
    action = "CHECK" if args.check else "GENERATE"
    print(
        f"VANILLA EVENT SOURCE INDEX {action}: GREEN "
        f"definitions={audit['unique_definition_count']} "
        f"definition_files={audit['definition_file_count']} "
        f"caller_candidates={audit['caller_candidate_reference_count']} "
        f"caller_files={audit['caller_candidate_file_count']} "
        f"dataset_sha256={document['dataset_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
