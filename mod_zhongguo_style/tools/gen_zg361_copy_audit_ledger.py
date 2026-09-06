#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a reproducible ledger for final Simplified Chinese event copy.

The ledger binds the bytes CK3 loads to visible event definitions.  Machine
checks are deliberately separate from the open human semantic review: a clean
regex result is not presented as proof that a scene is logical or well written.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


MOD_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MOD_ROOT.parent
EVENT_ROOT = MOD_ROOT / "events"
LOC_ROOT = MOD_ROOT / "localization" / "simp_chinese"
OUTPUT_ROOT = REPO_ROOT / "docs" / "content-audits" / "zg361-copy-ledger"
INDEX_PATH = OUTPUT_ROOT / "index.json"

SCHEMA_VERSION = 1
EVENT_CHUNK_SIZE = 40
LOC_CHUNK_SIZE = 180

LOC_ROW_RE = re.compile(r'^\s*(?P<key>[^\s:#]+):\d+\s+"(?P<value>.*)"\s*$')
EVENT_START_RE = re.compile(r"^\s*(?P<key>zg361[\w.]*)\s*=\s*{")
FIELD_RE = re.compile(
    r"(?<![\w])(?P<field>title|desc)\s*=\s*(?P<key>zg361[\w.]*)\b"
)
NAME_RE = re.compile(r"(?<![\w])name\s*=\s*(?P<key>zg361[\w.]*)\b")
DIRECT_NAME_RE = re.compile(r"^\s*name\s*=\s*(?P<key>zg361[\w.]*)\b")
TYPE_RE = re.compile(r"^\s*type\s*=\s*(?P<type>[\w.]+)")
HIDDEN_RE = re.compile(r"(?<![\w])hidden\s*=\s*yes\b")
OPTION_START_RE = re.compile(r"^\s*option\s*=\s*{")
GENERATED_AUTHORITY_RE = re.compile(r"GENERATED FILE.*?edit\s+(.+)$", re.IGNORECASE)
AUTHORITY_PATH_RE = re.compile(r"tools/[A-Za-z0-9_./*?-]+(?:\.py|\.json)")

OPENING_PUNCTUATION = frozenset(
    "。！？；：，、,.!?;:)]}）】》〉」』”’…—-·/／"
)
BODY_CHOICE_META_RE = re.compile(
    r"(?:路线\s*[甲乙丙ＡＢＣABC]"
    r"|[甲乙丙ＡＢＣABC]\s*[/／、和与或]\s*[甲乙丙ＡＢＣABC]"
    r"\s*(?:的)?\s*(?:具体|实际|所述)?\s*(?:路线|方案|选项|动作|处理|后果|选择)"
    r"|按\s*[ＡＢＣABC](?:做|办|执行|处理|走)?"
    r"|(?:按钮|选项)(?:上|中|里)?[^。！？；]{0,12}"
    r"(?:写明|列明|说明|展示)[^。！？；]{0,12}(?:动作|选择|处理|后果)"
    r"|(?:下方|以下)[^。！？；]{0,8}按钮|按钮及说明)",
    re.IGNORECASE,
)
GENERIC_OPTION_RE = re.compile(
    r"(?:(?:按|照|选|走|采用)\s*[ＡＢＣABC](?:做|办|执行|处理|路线)?"
    r"|路线\s*[甲乙丙ＡＢＣABC]|登记\s*路线\s*[甲乙丙ＡＢＣABC]\s*倾向"
    r"|按\s*(?:证据|政治)\s*办|^(?:照办|接受安排|继续|就这样)[。！!…]*$)",
    re.IGNORECASE,
)
OPTION_LIKE_SUFFIX_RE = re.compile(
    r"(?:[a-d]|r\d+|option_\d+|route_[a-z]|accept|reject|fail|ack|submit|decline)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LocEntry:
    key: str
    value: str
    path: Path
    line: int


@dataclass(frozen=True)
class EventEntry:
    key: str
    path: Path
    line: int
    event_type: str | None
    hidden: bool
    titles: tuple[str, ...]
    descriptions: tuple[str, ...]
    options: tuple[str, ...]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def stable_json(payload: object, *, pretty: bool = False) -> bytes:
    options = {"indent": 2} if pretty else {"separators": (",", ":")}
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, **options) + "\n").encode(
        "utf-8"
    )


def unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def script_code(row: str) -> str:
    """Remove comments and quoted strings while preserving script structure."""

    result: list[str] = []
    quoted = False
    escaped = False
    for character in row:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
            continue
        if character == "#":
            break
        result.append(character)
    return "".join(result)


def read_localization() -> tuple[dict[str, LocEntry], list[dict[str, object]]]:
    entries: dict[str, LocEntry] = {}
    duplicates: list[dict[str, object]] = []
    for path in sorted(LOC_ROOT.glob("*.yml")):
        rows = path.read_text(encoding="utf-8-sig").splitlines()
        for line_number, row in enumerate(rows, 1):
            match = LOC_ROW_RE.match(row)
            if match is None:
                continue
            key = match.group("key")
            entry = LocEntry(key, match.group("value"), path, line_number)
            if key in entries:
                previous = entries[key]
                duplicates.append(
                    {
                        "key": key,
                        "previous": f"{relative(previous.path)}:{previous.line}",
                        "replacement": f"{relative(path)}:{line_number}",
                    }
                )
            entries[key] = entry
    return entries, duplicates


def read_events() -> tuple[list[EventEntry], list[dict[str, object]]]:
    events: list[EventEntry] = []
    seen: dict[str, EventEntry] = {}
    duplicates: list[dict[str, object]] = []
    for path in sorted(EVENT_ROOT.glob("*.txt")):
        active: dict[str, object] | None = None
        depth = 0
        option_depth: int | None = None
        for line_number, row in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), 1
        ):
            code = script_code(row)
            if active is None:
                match = EVENT_START_RE.match(code)
                if match is None:
                    continue
                active = {
                    "key": match.group("key"),
                    "line": line_number,
                    "event_type": None,
                    "hidden": False,
                    "titles": [],
                    "descriptions": [],
                    "options": [],
                }
                # Parse the remainder of a one-line event declaration too.
                # Generated dispatch events legitimately use
                # ``type = character_event hidden = yes`` on the opening row.
                code = code[match.end() :]
                depth = 1

            pre_depth = depth
            option_started = False
            if pre_depth == 1:
                if (match := TYPE_RE.match(code)) is not None:
                    active["event_type"] = match.group("type")
                if HIDDEN_RE.search(code) is not None:
                    active["hidden"] = True
                if OPTION_START_RE.match(code) is not None:
                    option_depth = pre_depth + 1
                    option_started = True

            for match in FIELD_RE.finditer(code):
                target = "titles" if match.group("field") == "title" else "descriptions"
                cast_list = active[target]
                assert isinstance(cast_list, list)
                cast_list.append(match.group("key"))

            if option_depth is not None and option_started:
                match = NAME_RE.search(code[OPTION_START_RE.match(code).end() :])  # type: ignore[union-attr]
                if match is not None:
                    cast_options = active["options"]
                    assert isinstance(cast_options, list)
                    cast_options.append(match.group("key"))
            elif option_depth is not None and pre_depth == option_depth:
                match = DIRECT_NAME_RE.match(code)
                if match is not None:
                    cast_options = active["options"]
                    assert isinstance(cast_options, list)
                    cast_options.append(match.group("key"))

            depth += code.count("{") - code.count("}")
            if option_depth is not None and depth < option_depth:
                option_depth = None

            if depth == 0:
                event = EventEntry(
                    key=str(active["key"]),
                    path=path,
                    line=int(active["line"]),
                    event_type=(
                        str(active["event_type"])
                        if active["event_type"] is not None
                        else None
                    ),
                    hidden=bool(active["hidden"]),
                    titles=unique(active["titles"]),  # type: ignore[arg-type]
                    descriptions=unique(active["descriptions"]),  # type: ignore[arg-type]
                    options=unique(active["options"]),  # type: ignore[arg-type]
                )
                if event.key in seen:
                    previous = seen[event.key]
                    duplicates.append(
                        {
                            "key": event.key,
                            "previous": f"{relative(previous.path)}:{previous.line}",
                            "replacement": f"{relative(path)}:{event.line}",
                        }
                    )
                seen[event.key] = event
                events.append(event)
                active = None
                option_depth = None
        if active is not None:
            raise ValueError(f"unterminated event {active['key']} in {relative(path)}")
    return events, duplicates


def strip_ck3_markup(value: str) -> str:
    value = value.replace(r"\n", " ")
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = re.sub(r"\$[^$]+\$", "", value)
    value = re.sub(r"@[A-Za-z0-9_./-]+!", "", value)
    value = re.sub(r"#[A-Za-z0-9_]+\s*|#!", "", value)
    return re.sub(r"\s+", " ", value).strip()


def leading_visible_text(value: str) -> str:
    remaining = value.lstrip()
    markup = re.compile(r"^(?:#[A-Za-z_]+\s*|#!\s*|@[A-Za-z0-9_./-]+!\s*)")
    while (match := markup.match(remaining)) is not None:
        remaining = remaining[match.end() :].lstrip()
    return remaining


def comparison_text(value: str) -> str:
    return re.sub(r"[^\u3400-\u9fffA-Za-z0-9]+", "", strip_ck3_markup(value))


def status(checks: Iterable[dict[str, object]]) -> str:
    statuses = {str(check["status"]) for check in checks}
    if "fail" in statuses:
        return "fail"
    if "review" in statuses:
        return "review"
    if statuses == {"not_applicable"} or not statuses:
        return "not_applicable"
    return "pass"


def binding(key: str, loc: dict[str, LocEntry]) -> dict[str, object]:
    entry = loc.get(key)
    if entry is None:
        return {"key": key, "status": "fail", "text_sha256": None}
    return {"key": key, "status": "pass", "text_sha256": sha256_text(entry.value)}


def authority_for(path: Path, generator_sources: dict[str, tuple[str, ...]]) -> dict[str, object]:
    text = path.read_text(encoding="utf-8-sig")
    header_match = next(
        (GENERATED_AUTHORITY_RE.search(row) for row in text.splitlines()[:6] if GENERATED_AUTHORITY_RE.search(row)),
        None,
    )
    if header_match is not None:
        raw = header_match.group(1).strip()
        candidates: list[str] = []
        for candidate in AUTHORITY_PATH_RE.findall(raw):
            if "*" in candidate or "?" in candidate:
                candidates.extend(
                    relative(item) for item in sorted(MOD_ROOT.glob(candidate)) if item.is_file()
                )
            else:
                candidates.append(relative(MOD_ROOT / candidate))
        candidates = list(dict.fromkeys(candidates))
        exists = bool(candidates) and all((REPO_ROOT / item).is_file() for item in candidates)
        return {
            "status": "pass" if exists else "review",
            "method": (
                "generated_file_header"
                if len(candidates) == 1
                else "generated_file_header_multi_source"
            ),
            "declaration": raw,
            "candidates": candidates,
        }
    candidates = list(generator_sources.get(path.name, ()))
    if len(candidates) == 1:
        return {
            "status": "pass",
            "method": "unique_generator_output_literal",
            "candidates": candidates,
        }
    if not candidates:
        return {
            "status": "pass",
            "method": "hand_authored_source",
            "candidates": [relative(path)],
        }
    return {
        "status": "review",
        "method": "no_unique_authority",
        "candidates": candidates,
    }


def generator_source_index(source_paths: Iterable[Path]) -> dict[str, tuple[str, ...]]:
    generators = [
        path
        for path in sorted((MOD_ROOT / "tools").glob("*.py"))
        if (path.name.startswith("gen_") or path.name.endswith("_gen.py"))
        and path.name != Path(__file__).name
    ]
    generator_text = {
        path: path.read_text(encoding="utf-8-sig", errors="replace") for path in generators
    }
    index: dict[str, tuple[str, ...]] = {}
    for source in source_paths:
        needles = {source.name}
        if source.name.endswith("simp_chinese.yml"):
            needles.add(source.name[: -len("simp_chinese.yml")])
        matches = tuple(
            relative(generator)
            for generator, text in generator_text.items()
            if any(needle in text for needle in needles)
        )
        index[source.name] = matches
    return index


def input_inventory(source_paths: list[Path]) -> tuple[list[dict[str, object]], str]:
    generator_index = generator_source_index(source_paths)
    records: list[dict[str, object]] = []
    digest = hashlib.sha256()
    for path in source_paths:
        data = path.read_bytes()
        source_sha = sha256_bytes(data)
        rel = relative(path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_sha.encode("ascii"))
        digest.update(b"\n")
        records.append(
            {
                "path": rel,
                "bytes": len(data),
                "lines": len(data.decode("utf-8-sig").splitlines()),
                "sha256": source_sha,
                "authority": authority_for(path, generator_index),
            }
        )
    return records, digest.hexdigest()


def generation_base_commit(input_digest: str) -> str:
    if INDEX_PATH.is_file():
        try:
            previous = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            snapshot = previous["source_snapshot"]
            if snapshot["input_digest_sha256"] == input_digest:
                return str(snapshot.get("git_commit") or snapshot["git_commit_at_generation"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    result = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            relative(EVENT_ROOT),
            relative(LOC_ROOT),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def chunks(values: list[object], size: int) -> Iterable[list[object]]:
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def build_outputs() -> tuple[dict[Path, bytes], dict[str, object]]:
    loc, loc_duplicates = read_localization()
    all_events, event_duplicates = read_events()
    visible = [event for event in all_events if not event.hidden]
    event_keys = {event.key for event in all_events}
    visible_option_refs = {key for event in visible for key in event.options}
    all_option_refs = {key for event in all_events for key in event.options}

    source_paths = sorted(EVENT_ROOT.glob("*.txt")) + sorted(LOC_ROOT.glob("*.yml"))
    inventory, input_digest = input_inventory(source_paths)

    machine_failures: list[dict[str, object]] = []
    if loc_duplicates:
        machine_failures.append({"check": "duplicate_localization_key", "items": loc_duplicates})
    if event_duplicates:
        machine_failures.append({"check": "duplicate_event_key", "items": event_duplicates})

    event_records: list[dict[str, object]] = []
    check_counts: dict[str, dict[str, int]] = {}

    def note(check_name: str, check_status: str) -> None:
        bucket = check_counts.setdefault(check_name, {})
        bucket[check_status] = bucket.get(check_status, 0) + 1

    for event in visible:
        body_opening_items: list[dict[str, object]] = []
        body_meta_items: list[dict[str, object]] = []
        generic_option_items: list[dict[str, object]] = []
        option_loc_items: list[dict[str, object]] = []
        title_body_items: list[dict[str, object]] = []

        for key in event.descriptions:
            entry = loc.get(key)
            if entry is None:
                item_status = "fail"
                body_opening_items.append({"key": key, "status": item_status, "reason": "missing_loc"})
                body_meta_items.append({"key": key, "status": item_status, "reason": "missing_loc"})
                continue
            leading = leading_visible_text(entry.value)
            opening_status = "fail" if not leading or leading[0] in OPENING_PUNCTUATION else "pass"
            body_opening_items.append(
                {
                    "key": key,
                    "status": opening_status,
                    "first_visible_character": leading[:1] or None,
                }
            )
            match = BODY_CHOICE_META_RE.search(strip_ck3_markup(entry.value))
            body_meta_items.append(
                {
                    "key": key,
                    "status": "fail" if match else "pass",
                    "match": match.group(0) if match else None,
                }
            )

        for key in event.options:
            entry = loc.get(key)
            option_loc_items.append(
                {"key": key, "status": "pass" if entry is not None else "fail"}
            )
            if entry is None:
                generic_option_items.append({"key": key, "status": "fail", "reason": "missing_loc"})
                continue
            match = GENERIC_OPTION_RE.search(strip_ck3_markup(entry.value))
            generic_option_items.append(
                {
                    "key": key,
                    "status": "fail" if match else "pass",
                    "match": match.group(0) if match else None,
                }
            )

        for title_key in event.titles:
            title = loc.get(title_key)
            for body_key in event.descriptions:
                body = loc.get(body_key)
                if title is None or body is None:
                    title_body_items.append(
                        {
                            "title_key": title_key,
                            "body_key": body_key,
                            "status": "fail",
                            "reason": "missing_loc",
                        }
                    )
                    continue
                title_text = comparison_text(title.value)
                body_text = comparison_text(body.value)
                similarity = SequenceMatcher(None, title_text, body_text).ratio()
                contains = len(title_text) >= 4 and title_text in body_text
                relation_status = "fail" if contains else ("review" if similarity >= 0.50 else "pass")
                title_body_items.append(
                    {
                        "title_key": title_key,
                        "body_key": body_key,
                        "status": relation_status,
                        "normalized_title_contained": contains,
                        "similarity": round(similarity, 6),
                    }
                )

        checks = {
            "stripped_opening_punctuation": {
                "status": status(body_opening_items),
                "items": body_opening_items,
            },
            "title_similarity_contains": {
                "status": status(title_body_items),
                "items": title_body_items,
            },
            "body_choice_meta": {"status": status(body_meta_items), "items": body_meta_items},
            "generic_option": {
                "status": status(generic_option_items),
                "items": generic_option_items,
            },
            "dead_option_loc": {
                "status": status(option_loc_items),
                "items": option_loc_items,
            },
            "manual_semantic_review": {
                "status": "review",
                "reason": "context, causal logic, voice, and useful information require human review",
            },
        }
        for check_name, check in checks.items():
            note(check_name, str(check["status"]))
            if check["status"] == "fail":
                machine_failures.append(
                    {"check": check_name, "event_key": event.key, "source": relative(event.path)}
                )
        event_records.append(
            {
                "event_key": event.key,
                "event_type": event.event_type,
                "source": {"path": relative(event.path), "line": event.line},
                "title": [binding(key, loc) for key in event.titles],
                "description": [binding(key, loc) for key in event.descriptions],
                "options": [binding(key, loc) for key in event.options],
                "checks": checks,
            }
        )

    option_like_review: list[dict[str, object]] = []
    for key, entry in sorted(loc.items()):
        matching_event = next(
            (event_key for event_key in event_keys if key.startswith(f"{event_key}.")),
            None,
        )
        if matching_event is None:
            continue
        suffix = key[len(matching_event) + 1 :]
        if not OPTION_LIKE_SUFFIX_RE.fullmatch(suffix):
            continue
        if key not in all_option_refs:
            option_like_review.append(
                {
                    "key": key,
                    "source": f"{relative(entry.path)}:{entry.line}",
                    "status": "review",
                    "reason": "option-like localization is not bound by an event option; another UI surface may own it",
                }
            )

    missing_visible_options = sorted(key for key in visible_option_refs if key not in loc)
    dead_option_status = "fail" if missing_visible_options else (
        "review" if option_like_review else "pass"
    )
    if missing_visible_options:
        machine_failures.append(
            {"check": "dead_option_loc", "missing_visible_option_localization": missing_visible_options}
        )

    loc_roles: dict[str, dict[str, set[str]]] = {}
    for event in visible:
        for role, keys in (
            ("title", event.titles),
            ("description", event.descriptions),
            ("option", event.options),
        ):
            for key in keys:
                slot = loc_roles.setdefault(key, {"roles": set(), "events": set()})
                slot["roles"].add(role)
                slot["events"].add(event.key)

    loc_records: list[dict[str, object]] = []
    for key, entry in sorted(loc.items()):
        role = loc_roles.get(key, {"roles": set(), "events": set()})
        loc_records.append(
            {
                "key": key,
                "text": entry.value,
                "text_sha256": sha256_text(entry.value),
                "source": {"path": relative(entry.path), "line": entry.line},
                "visible_event_roles": sorted(role["roles"]),
                "visible_event_keys": sorted(role["events"]),
            }
        )

    outputs: dict[Path, bytes] = {}
    shard_index: list[dict[str, object]] = []
    for kind, records, chunk_size in (
        ("events", event_records, EVENT_CHUNK_SIZE),
        ("localization", loc_records, LOC_CHUNK_SIZE),
    ):
        for number, chunk in enumerate(chunks(records, chunk_size), 1):
            path = OUTPUT_ROOT / kind / f"{kind}-{number:03d}.json"
            payload = {
                "schema_version": SCHEMA_VERSION,
                "kind": kind,
                "records": chunk,
            }
            data = stable_json(payload)
            outputs[path] = data
            shard_index.append(
                {
                    "path": relative(path),
                    "kind": kind,
                    "records": len(chunk),
                    "bytes": len(data),
                    "sha256": sha256_bytes(data),
                }
            )

    review_open_items: list[dict[str, object]] = [
        {
            "kind": "manual_semantic_review",
            "status": "review",
            "count": len(visible),
            "reason": "machine checks do not prove that scene context, causality, voice, or information value is sound",
            "records": "event shards",
        },
        {
            "kind": "live_render_validation",
            "status": "pending",
            "count": 1,
            "reason": "static source binding cannot validate dynamic scopes, rendered layout, or in-game wording",
        },
    ]
    if option_like_review:
        review_open_items.append(
            {
                "kind": "unbound_option_like_localization",
                "status": "review",
                "count": len(option_like_review),
                "items": option_like_review,
            }
        )
    ambiguous_authorities = [
        item for item in inventory if item["authority"]["status"] == "review"  # type: ignore[index]
    ]
    if ambiguous_authorities:
        review_open_items.append(
            {
                "kind": "authority_source_not_unique",
                "status": "review",
                "count": len(ambiguous_authorities),
                "source_paths": [item["path"] for item in ambiguous_authorities],
            }
        )

    summary = {
        "all_event_definitions": len(all_events),
        "visible_events": len(visible),
        "hidden_events": sum(event.hidden for event in all_events),
        "final_localization_keys": len(loc),
        "visible_title_bindings": sum(len(event.titles) for event in visible),
        "visible_description_bindings": sum(len(event.descriptions) for event in visible),
        "visible_option_bindings": sum(len(event.options) for event in visible),
        "machine_failure_count": len(machine_failures),
        "manual_review_open_count": sum(int(item["count"]) for item in review_open_items),
        "check_status_counts": check_counts,
        "dead_option_loc": {
            "status": dead_option_status,
            "bound_visible_option_count": len(visible_option_refs),
            "missing_visible_option_count": len(missing_visible_options),
            "unbound_option_like_review_count": len(option_like_review),
        },
    }
    index = {
        "schema_version": SCHEMA_VERSION,
        "ledger_status": "fail" if machine_failures else "review",
        "machine_checks_status": "fail" if machine_failures else "pass",
        "human_semantic_review_status": "review",
        "live_render_validation_status": "pending",
        "scope": {
            "language": "simp_chinese",
            "event_visibility_rule": "event definition without direct hidden = yes",
            "localization_resolution": "unique keys across lexically sorted simp_chinese yml files",
            "authority_resolution": "join each record source.path to source_snapshot.files[].authority",
        },
        "source_snapshot": {
            "git_commit": generation_base_commit(input_digest),
            "git_commit_semantics": "latest commit touching event/localization inputs at generation",
            "input_digest_sha256": input_digest,
            "files": inventory,
        },
        "summary": summary,
        "checks": {
            "stripped_opening_punctuation": "first visible character after CK3 style/icon markup",
            "title_similarity_contains": "literal normalized containment fails; similarity >= 0.50 remains review",
            "body_choice_meta": BODY_CHOICE_META_RE.pattern,
            "generic_option": GENERIC_OPTION_RE.pattern,
            "dead_option_loc": "every visible option reference must resolve; unbound option-like rows remain review",
        },
        "machine_failures": machine_failures,
        "open_items": review_open_items,
        "shards": shard_index,
    }
    # Keep the routing/index document reviewable.  Data shards stay compact so
    # checked-in evidence does not manufacture a six-digit line-count diff.
    outputs[INDEX_PATH] = stable_json(index, pretty=True)
    return outputs, index


def check_outputs(expected: dict[Path, bytes]) -> list[str]:
    failures: list[str] = []
    existing = set(OUTPUT_ROOT.rglob("*.json")) if OUTPUT_ROOT.is_dir() else set()
    expected_paths = set(expected)
    for path in sorted(existing - expected_paths):
        failures.append(f"unexpected stale shard: {relative(path)}")
    for path in sorted(expected_paths):
        if not path.is_file():
            failures.append(f"missing: {relative(path)}")
        elif path.read_bytes() != expected[path]:
            failures.append(f"stale: {relative(path)}")
    return failures


def write_outputs(expected: dict[Path, bytes]) -> None:
    existing = set(OUTPUT_ROOT.rglob("*.json")) if OUTPUT_ROOT.is_dir() else set()
    for path in sorted(existing - set(expected)):
        path.unlink()
    for path, data in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify checked-in ledger bytes")
    args = parser.parse_args(argv)
    expected, index = build_outputs()
    if args.check:
        failures = check_outputs(expected)
        if failures:
            print("ZG361 copy ledger RED:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
    else:
        write_outputs(expected)
    summary = index["summary"]
    print(
        "ZG361 copy ledger "
        f"{index['ledger_status'].upper()}: {summary['visible_events']} visible events, "
        f"{summary['final_localization_keys']} final loc keys, "
        f"{summary['machine_failure_count']} machine failures; "
        "human semantic review remains open"
    )
    return 1 if index["machine_checks_status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
