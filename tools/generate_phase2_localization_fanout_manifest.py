#!/usr/bin/env python3
"""Generate a hash-bound Phase-2 localization fan-out audit artifact.

This tool is deliberately read-only with respect to CK3 source trees.  It
reads the disposable projection manifests/trees produced by the startup
bisect, verifies every declared row byte-for-byte, and writes one machine
readable comparison document.  It never starts CK3 or edits a product tree.

The default paths are the disposable artifacts captured on 2026-09-03.  Use
the path options when reproducing the audit from another frozen run.
"""

from __future__ import annotations

import argparse
from collections import Counter, OrderedDict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable


LANGUAGES = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)

SOURCE_ONLY_ROOTS = frozenset(
    {"artifacts", "docs", "fixtures", "images", "promo", "tools", "workshop"}
)
RUNTIME_SUFFIXES = {
    "common": frozenset({".txt"}),
    "events": frozenset({".txt"}),
    "gfx": frozenset({".dds"}),
    "gui": frozenset({".gui", ".txt"}),
    "localization": frozenset({".yml"}),
}
ROOT_FILES = frozenset({"descriptor.mod", "thumbnail.png"})
FORBIDDEN_PARTS = frozenset({"acceptance", "fixture", "fixtures", "test", "tests"})

REPO = Path(r"Z:\ck3_mod_rewrite")
DEFAULT_OUTPUT = REPO / "_root-promo-split-20260902" / "docs" / "phase2-promo" / "phase2-localization-fanout-manifest-2026-09-03.json"
DEFAULT_CORE_MANIFEST = REPO / "_root-promo-split-20260902" / "tools" / "phase2_product_projection_core.json"
DEFAULT_CALLABLE_MANIFEST = REPO / "_runtime" / "phase2-direct-union-v2-static-closure-r1-20260903" / "projection-callable-core.json"
DEFAULT_EVENT_MANIFEST = REPO / "_runtime" / "phase2-direct-union-v2-static-closure-r1-20260903" / "projection-event-core.json"
DEFAULT_AUTHORITY_MANIFEST = REPO / "_runtime" / "phase2-event-loc-manifests-20260903" / "projection-event-core-locfanout-201.json"
DEFAULT_FULL_MANIFEST = REPO / "_runtime" / "phase2-event-loc-manifests-20260903" / "projection-event-core-locfull-261.json"
DEFAULT_CORE_ROOT = REPO / "_runtime" / "phase2-bisect-source-legacy51-20260903" / "mod_zhongguo_style"
DEFAULT_CALLABLE_ROOT = REPO / "_runtime" / "phase2-direct-union-v2-static-closure-r1-20260903" / "callable-core" / "zhongguo_361"
DEFAULT_EVENT_ROOT = REPO / "_runtime" / "phase2-direct-union-v2-static-closure-r1-20260903" / "event-core" / "zhongguo_361"
DEFAULT_AUTHORITY_ROOT = REPO / "_runtime" / "phase2-bisect-source-direct-union-v2-20260903" / "mod_zhongguo_style"
DEFAULT_FULL_ROOT = REPO / "_runtime" / "phase2-event-locfull-clean-20260903" / "mod_zhongguo_style"
DEFAULT_LOCAUG_ROOT = REPO / "_runtime" / "phase2-event-locaug-clean-20260903" / "mod_zhongguo_style"
DEFAULT_CURRENT_ROOT = REPO / "_local-freezes" / "phase2-dual-cut-g2-static-integrated-20260903-clean" / "mod_zhongguo_style"
DEFAULT_AUTHORITY_REPORT = REPO / "_runtime" / "formal-phase2-direct-union-v2-20260903" / "report.json"
DEFAULT_EVENT_CORE_REPORT = REPO / "_runtime" / "formal-phase2-event-core-20260903" / "report.json"
DEFAULT_LOCAUG_REPORT = REPO / "_runtime" / "formal-phase2-event-locaug-20260903" / "report.json"
DEFAULT_FULL_REPORT = REPO / "_runtime" / "formal-phase2-event-locfull-20260903" / "report.json"


class AuditError(ValueError):
    """A projection row or digest failed the audit contract."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(payload, dict):
        raise AuditError(f"JSON root is not an object: {path}")
    return payload


def canonical_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise AuditError(f"row {index} is not an object")
        path = raw.get("path")
        size = raw.get("bytes", raw.get("size"))
        digest = raw.get("sha256")
        if not isinstance(path, str) or not path or "\\" in path:
            raise AuditError(f"row {index} has malformed path: {path!r}")
        if path in seen:
            raise AuditError(f"duplicate path: {path}")
        seen.add(path)
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise AuditError(f"row {index} has malformed bytes: {size!r}")
        if not isinstance(digest, str) or len(digest) != 64:
            raise AuditError(f"row {index} has malformed sha256")
        try:
            int(digest, 16)
        except ValueError as error:
            raise AuditError(f"row {index} sha256 is not hexadecimal") from error
        result.append({"path": path, "bytes": size, "sha256": digest.lower()})
    return sorted(result, key=lambda row: row["path"])


def source_tree_digest(rows: Iterable[dict[str, Any]]) -> str:
    mapping = {
        row["path"]: {"size": row["bytes"], "sha256": row["sha256"]}
        for row in sorted(rows, key=lambda item: item["path"])
    }
    encoded = json.dumps(mapping, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256_bytes(encoded)


def formal_overlay_digest(rows: Iterable[dict[str, Any]]) -> str:
    ordered = [
        {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
        for row in sorted(rows, key=lambda item: item["path"])
    ]
    encoded = json.dumps(ordered, ensure_ascii=True, sort_keys=False, separators=(",", ":")).encode("ascii")
    return sha256_bytes(encoded)


def file_list_digest(rows: Iterable[dict[str, Any]]) -> str:
    paths = [row["path"] for row in sorted(rows, key=lambda item: item["path"])]
    encoded = json.dumps(paths, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return sha256_bytes(encoded)


def runtime_path_allowed(relative: str) -> bool:
    path = PurePosixPath(relative)
    if len(path.parts) == 1:
        return relative in ROOT_FILES
    return path.parts[0] in RUNTIME_SUFFIXES and path.suffix.lower() in RUNTIME_SUFFIXES[path.parts[0]]


def forbidden_runtime_path(relative: str) -> bool:
    for part in PurePosixPath(relative).parts:
        lowered = part.lower()
        stem = PurePosixPath(lowered).stem
        if lowered in FORBIDDEN_PARTS or "acceptance" in lowered or "fixture" in lowered:
            return True
        if stem.startswith("test_") or stem.endswith("_test") or "_test_" in stem:
            return True
    return False


def scan_runtime_rows(root: Path) -> list[dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise AuditError(f"source root is missing: {root}")
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if ".git" in PurePosixPath(relative).parts or not runtime_path_allowed(relative):
            continue
        if path.is_symlink() or forbidden_runtime_path(relative):
            raise AuditError(f"unsafe runtime path in {root}: {relative}")
        data = path.read_bytes()
        rows.append({"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)})
    return canonical_rows(rows)


def verify_rows(root: Path, declared: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise AuditError(f"source root is missing: {root}")
    rows = canonical_rows(declared)
    for row in rows:
        relative = row["path"]
        if not runtime_path_allowed(relative) or forbidden_runtime_path(relative):
            raise AuditError(f"manifest row outside runtime allowlist: {relative}")
        source = root / PurePosixPath(relative)
        if not source.is_file() or source.is_symlink():
            raise AuditError(f"manifest row missing or symlinked: {source}")
        data = source.read_bytes()
        observed = {"bytes": len(data), "sha256": sha256_bytes(data)}
        if observed["bytes"] != row["bytes"] or observed["sha256"] != row["sha256"]:
            raise AuditError(
                f"row mismatch for {relative}: observed {observed}, declared "
                f"{{'bytes': {row['bytes']}, 'sha256': '{row['sha256']}'}}"
            )
    return rows


def classify_localization(relative: str) -> tuple[str | None, str | None]:
    path = PurePosixPath(relative)
    if len(path.parts) != 3 or path.parts[0] != "localization":
        return None, None
    language = path.parts[1]
    stem = path.stem
    if language not in LANGUAGES:
        raise AuditError(f"unknown localization language in {relative}")
    base_name = f"zg361_l_{language}"
    if stem == base_name:
        return language, "base"
    suffix = f"_l_{language}"
    prefix = "zg361_"
    if stem.startswith(prefix) and stem.endswith(suffix):
        owner = stem[len(prefix) : -len(suffix)]
        if owner:
            return language, owner
    raise AuditError(f"cannot classify localization owner: {relative}")


def enrich_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in canonical_rows(rows):
        language, owner = classify_localization(row["path"])
        value = dict(row)
        if language is not None:
            value["language"] = language
            value["owner"] = owner
        enriched.append(value)
    return enriched


def localization_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in enrich_rows(rows) if "language" in row]


def owner_stats(rows: Iterable[dict[str, Any]]) -> OrderedDict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in localization_rows(rows):
        owner = str(row["owner"])
        language = str(row["language"])
        item = stats.setdefault(owner, {"files": 0, "bytes": 0, "languages": {}})
        item["files"] += 1
        item["bytes"] += int(row["bytes"])
        item["languages"][language] = {
            "files": item["languages"].get(language, {}).get("files", 0) + 1,
            "bytes": item["languages"].get(language, {}).get("bytes", 0) + int(row["bytes"]),
        }
    ordered: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for owner in sorted(stats):
        item = stats[owner]
        item["languages"] = OrderedDict((lang, item["languages"][lang]) for lang in sorted(item["languages"]))
        ordered[owner] = item
    return ordered


def language_stats(rows: Iterable[dict[str, Any]]) -> OrderedDict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    for row in localization_rows(rows):
        language = str(row["language"])
        item = stats.setdefault(language, {"files": 0, "bytes": 0})
        item["files"] += 1
        item["bytes"] += int(row["bytes"])
    return OrderedDict((lang, stats.get(lang, {"files": 0, "bytes": 0})) for lang in LANGUAGES)


def digest_record(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return the three projection-compatible digests for a row subset."""

    canonical = canonical_rows(rows)
    return {
        "files": len(canonical),
        "bytes": sum(int(row["bytes"]) for row in canonical),
        "source_tree_sha256": source_tree_digest(canonical),
        "formal_overlay_tree_sha256": formal_overlay_digest(canonical),
        "file_list_sha256": file_list_digest(canonical),
    }


def localization_digest_stats(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Expose stable digests for all localization and named owner groups.

    ``workforce`` is an intentional aggregate over the nine workforce owner
    families.  Keeping this aggregate alongside per-owner rows makes the
    201/261/81 boundaries easy to compare without re-reading the large arrays.
    """

    loc = localization_rows(rows)
    by_owner: dict[str, list[dict[str, Any]]] = {}
    for row in loc:
        by_owner.setdefault(str(row["owner"]), []).append(row)
    owner_families = OrderedDict(
        (owner, digest_record(by_owner[owner])) for owner in sorted(by_owner)
    )
    named: OrderedDict[str, dict[str, Any]] = OrderedDict()
    named["all"] = digest_record(loc)
    workforce = [row for row in loc if str(row["owner"]).startswith("workforce_")]
    named["workforce"] = digest_record(workforce)
    for owner in ("b1", "b2", "incident_platform", "manager_governance", "phase2_central"):
        if owner in by_owner:
            named[owner] = digest_record(by_owner[owner])
    return {
        "named_groups": named,
        "owner_families": owner_families,
    }


def load_declared_manifest(path: Path, root: Path, *, include_all_rows: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = read_json(path)
    declared = payload.get("files")
    if not isinstance(declared, list):
        raise AuditError(f"manifest has no files list: {path}")
    rows = verify_rows(root, declared)
    expected = {
        "source_tree_sha256": source_tree_digest(rows),
        "formal_overlay_tree_sha256": formal_overlay_digest(rows),
        "file_list_sha256": file_list_digest(rows),
    }
    for key, observed in expected.items():
        declared_hash = payload.get(key)
        if declared_hash is not None and str(declared_hash).lower() != observed:
            raise AuditError(f"{path.name} {key} mismatch: {declared_hash} != {observed}")
    return payload, (enrich_rows(rows) if include_all_rows else localization_rows(rows))


def report_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"report_path": str(path), "exists": False}
    payload = read_json(path)
    summary: dict[str, Any] = {
        "report_path": str(path),
        "report_sha256": sha256_file(path),
        "exists": True,
        "result": payload.get("result"),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "frontend_observed": bool((payload.get("frontend") or {}).get("observed", False)),
        "process_exit_code": payload.get("process_exit_code_before_runtime_cleanup"),
        "timeout_seconds": payload.get("timeout_seconds"),
        "bridge_mode": payload.get("bridge_mode"),
        "game_dir": payload.get("game_dir"),
        "executable": payload.get("executable"),
        "executable_sha256": payload.get("executable_sha256"),
        "working_directory": payload.get("working_directory"),
        "arguments": payload.get("arguments"),
        "product_source": payload.get("product_source"),
        "fixture_source": payload.get("fixture_source"),
        "profile": payload.get("profile"),
        "product_tree": {
            key: (payload.get("product_tree") or {}).get(key)
            for key in ("file_count", "bytes", "tree_sha256")
        },
        "cleanup": payload.get("close"),
    }
    # Older/in-flight reports may not yet have written their post-run
    # ``error_log``/``debug_log`` metadata.  The runner always records the
    # profile path, so fall back to the concrete log files when present.  This
    # keeps the 201-file unfinished run's Total-of-881 boundary observable
    # without treating it as a successful frontend result.
    profile = payload.get("profile")
    profile_logs = Path(profile) / "logs" if isinstance(profile, str) else None
    error = payload.get("error_log") or {}
    if not isinstance(error, dict):
        error = {}
    if not error and profile_logs is not None:
        candidate = profile_logs / "error.log"
        if candidate.is_file():
            error = {
                "path": str(candidate),
                "exists": True,
                "bytes": candidate.stat().st_size,
                "sha256": sha256_file(candidate),
                "line_count": len(candidate.read_text(encoding="utf-8", errors="replace").splitlines()),
                "source": "profile-log-fallback",
            }
    summary["error_log"] = {
        key: error.get(key)
        for key in ("path", "exists", "bytes", "sha256", "line_count")
        if key in error
    }
    error_path = error.get("path")
    if error_path and Path(error_path).is_file():
        lines = Path(error_path).read_text(encoding="utf-8", errors="replace").splitlines()
        keys = []
        for line in lines:
            match = re.search(r"Unrecognized loc key ([^ .]+)", line)
            if match:
                keys.append(match.group(1))
        summary["missing_localization"] = {
            "error_lines": len(lines),
            "unrecognized_loc_lines": len(keys),
            "unique_keys": len(set(keys)),
            "sample_keys": sorted(set(keys))[:20],
        }
    debug_meta = payload.get("debug_log") or {}
    debug_path = debug_meta.get("path") if isinstance(debug_meta, dict) else None
    if not debug_path and profile_logs is not None:
        candidate = profile_logs / "debug.log"
        if candidate.is_file():
            debug_path = str(candidate)
    if debug_path and Path(debug_path).is_file():
        lines = Path(debug_path).read_text(encoding="utf-8", errors="replace").splitlines()
        total = [line for line in lines if "Total of :" in line]
        frontend = [line for line in lines if "frontend_main.gui" in line and "complete" in line.lower()]
        history = [line for line in lines if "End loading of history" in line]
        summary["debug_markers"] = {
            "total_on_actions": total[-5:],
            "frontend_complete": frontend[-5:],
            "history_complete": history[-5:],
        }
    return summary


def projection_summary(
    *,
    name: str,
    role: str,
    manifest_path: Path | None,
    source_root: Path,
    include_all_rows: bool,
    report_path: Path | None = None,
) -> dict[str, Any]:
    if manifest_path is None:
        rows = scan_runtime_rows(source_root)
        manifest_payload: dict[str, Any] = {}
        manifest_sha = None
        declared_hashes = {}
    else:
        manifest_payload, rows = load_declared_manifest(manifest_path, source_root, include_all_rows=True)
        # Re-read all rows for summaries even when the compact representation
        # stores only localization rows.
        all_declared = manifest_payload["files"]
        full_rows = enrich_rows(verify_rows(source_root, all_declared))
        rows = full_rows if include_all_rows else localization_rows(full_rows)
        manifest_sha = sha256_file(manifest_path)
        declared_hashes = {
            key: manifest_payload.get(key)
            for key in ("source_tree_sha256", "formal_overlay_tree_sha256", "file_list_sha256")
        }
    all_rows = rows if include_all_rows else rows
    # For compact projections, reconstruct the complete rows from the source
    # tree so the digest/count values always describe the mounted projection.
    if not include_all_rows:
        all_rows = scan_runtime_rows(source_root) if manifest_path is None else verify_rows(source_root, manifest_payload["files"])
    all_rows = canonical_rows(all_rows)
    loc = localization_rows(all_rows)
    summary: dict[str, Any] = {
        "name": name,
        "role": role,
        "source_root": str(source_root),
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "manifest_sha256": manifest_sha,
        "declared_hashes": declared_hashes,
        "verified": True,
        "verification": {
            "rows_verified": len(all_rows),
            "bytes_verified": sum(int(row["bytes"]) for row in all_rows),
            "source_tree_sha256": source_tree_digest(all_rows),
            "formal_overlay_tree_sha256": formal_overlay_digest(all_rows),
            "file_list_sha256": file_list_digest(all_rows),
        },
        "localization": {
            "files": len(loc),
            "bytes": sum(int(row["bytes"]) for row in loc),
            "languages": language_stats(all_rows),
            "owners": owner_stats(all_rows),
            "digests": localization_digest_stats(all_rows),
        },
    }
    if include_all_rows:
        summary["rows"] = enrich_rows(all_rows)
    else:
        summary["localization_rows"] = enrich_rows(loc)
    if report_path is not None:
        summary["runtime_evidence"] = report_summary(report_path)
    return summary


def path_delta(left: Iterable[dict[str, Any]], right: Iterable[dict[str, Any]]) -> dict[str, Any]:
    a = {row["path"]: row for row in left}
    b = {row["path"]: row for row in right}
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = sorted(path for path in set(a) & set(b) if a[path]["sha256"] != b[path]["sha256"])
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
    }


def build_document(args: argparse.Namespace) -> dict[str, Any]:
    # Import the checked-in utility and bind its bytes to the audit.  The
    # private function is intentionally used only to record the exact utility
    # implementation hash; all verification below is independently repeated.
    utility_path = Path(args.utility).resolve()
    if not utility_path.is_file():
        raise AuditError(f"projection utility is missing: {utility_path}")

    core = projection_summary(
        name="core-51", role="input-core", manifest_path=Path(args.core_manifest),
        source_root=Path(args.core_root), include_all_rows=False,
    )
    callable_core = projection_summary(
        name="callable-core-66", role="input-static-candidate", manifest_path=Path(args.callable_manifest),
        source_root=Path(args.callable_root), include_all_rows=False,
    )
    event_core = projection_summary(
        name="event-core-81", role="input-static-candidate", manifest_path=Path(args.event_manifest),
        source_root=Path(args.event_root), include_all_rows=False,
    )
    authority = projection_summary(
        name="event-core-locfanout-201", role="authority-complete-fanout", manifest_path=Path(args.authority_manifest),
        source_root=Path(args.authority_root), include_all_rows=True, report_path=Path(args.authority_report),
    )
    full = projection_summary(
        name="event-core-locfull-261", role="comparison-full-localization", manifest_path=Path(args.full_manifest),
        source_root=Path(args.full_root), include_all_rows=True, report_path=Path(args.full_report),
    )
    locaug = projection_summary(
        name="event-locaug-162", role="runtime-red-intermediate", manifest_path=None,
        source_root=Path(args.locaug_root), include_all_rows=True, report_path=Path(args.locaug_report),
    )
    current = projection_summary(
        name="current-clean-release-279", role="current-source-reference", manifest_path=None,
        source_root=Path(args.current_root), include_all_rows=False,
    )

    authority_rows = authority["rows"]
    full_rows = full["rows"]
    authority_loc = [row for row in authority_rows if "language" in row]
    full_loc = [row for row in full_rows if "language" in row]
    locaug_loc = [row for row in locaug["rows"] if "language" in row]
    if len(authority_loc) != 135 or len(full_loc) != 198:
        raise AuditError(f"unexpected fan-out counts: authority={len(authority_loc)}, full={len(full_loc)}")
    if len(owner_stats(authority_rows)) != 15 or any(item["files"] != 9 for item in owner_stats(authority_rows).values()):
        raise AuditError("authority is not a 15 x 9 localization matrix")
    if len(owner_stats(full_rows)) != 22 or any(item["files"] != 9 for item in owner_stats(full_rows).values()):
        raise AuditError("full comparison is not a 22 x 9 localization matrix")

    loc_delta = path_delta(authority_loc, full_loc)
    all_delta = path_delta(authority_rows, full_rows)
    authority_manifest_payload = read_json(Path(args.authority_manifest))
    full_manifest_payload = read_json(Path(args.full_manifest))

    document: dict[str, Any] = OrderedDict()
    document["schema_version"] = 1
    document["kind"] = "zg361_phase2_localization_fanout_audit"
    document["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    document["generator"] = {
        "path": str(Path(__file__).resolve()),
        "utility_path": str(utility_path),
        "utility_sha256": sha256_file(utility_path),
        "ck3_started_by_generator": False,
        "canonical_source_modified_by_generator": False,
    }
    document["purpose"] = (
        "Byte-level audit of the 201-file complete localization fan-out authority "
        "against the 261-file all-language candidate and the 162-file intermediate. "
        "This is diagnostic startup evidence, not a release/workshop manifest."
    )
    document["hash_algorithms"] = {
        "source_tree_sha256": "sha256(json.dumps({path:{size,sha256}}, ensure_ascii=True, sort_keys=True, separators=(\",\",\":\")))",
        "formal_overlay_tree_sha256": "sha256(json.dumps(sorted([{path,bytes,sha256}], key=path), ensure_ascii=True, sort_keys=False, separators=(\",\",\":\")))",
        "file_list_sha256": "sha256(json.dumps(sorted(paths), ensure_ascii=True, separators=(\",\",\":\")))",
        "row_sha256": "sha256(raw file bytes)",
    }
    document["languages"] = list(LANGUAGES)
    document["inputs"] = {
        "core_manifest": core,
        "callable_core_manifest": callable_core,
        "event_core_manifest": event_core,
    }
    document["authority"] = authority
    document["comparison"] = full
    document["intermediate_red"] = locaug
    document["current_source"] = current
    document["fanout_delta"] = {
        "authority_to_full_localization": loc_delta,
        "authority_to_full_all_runtime": all_delta,
        "authority_localization_files": len(authority_loc),
        "full_localization_files": len(full_loc),
        "intermediate_localization_files": len(locaug_loc),
        "authority_localization_bytes": sum(int(row["bytes"]) for row in authority_loc),
        "full_localization_bytes": sum(int(row["bytes"]) for row in full_loc),
        "intermediate_localization_bytes": sum(int(row["bytes"]) for row in locaug_loc),
        "full_added_owner_families": sorted(set(owner_stats(full_rows)) - set(owner_stats(authority_rows))),
        "intermediate_missing_owner_families_vs_authority": sorted(set(owner_stats(authority_rows)) - set(owner_stats(locaug["rows"]))),
    }
    document["runtime_boundary"] = {
        "authority_report": authority["runtime_evidence"],
        "event_core_report": report_summary(Path(args.event_core_report)),
        "intermediate_locaug_report": locaug["runtime_evidence"],
        "full_loc_report": full["runtime_evidence"],
        "interpretation": [
            "The 201-file authority has a complete 15 x 9 localization matrix; its report is a static/unfinished v2 run and does not certify Frontend.",
            "The 162-file intermediate reached the Total of : 881 on_actions marker but timed out with 68 unrecognized localization lines.",
            "The 261-file all-language comparison has 22 x 9 localization rows and an empty error.log, but the formal run still timed out before Frontend/history completion.",
            "No localization or source bytes were changed by this audit; no CK3 launch was performed by the generator.",
        ],
    }
    # Keep a small immutable copy of the parent-generated manifest identities
    # at top level for quick review without opening the large row arrays.
    document["manifest_identities"] = {
        "authority": {
            "path": str(Path(args.authority_manifest)),
            "manifest_sha256": sha256_file(Path(args.authority_manifest)),
            "projection": authority_manifest_payload.get("projection"),
            "files": len(authority_rows),
            "bytes": sum(int(row["bytes"]) for row in authority_rows),
            "source_tree_sha256": authority["verification"]["source_tree_sha256"],
            "formal_overlay_tree_sha256": authority["verification"]["formal_overlay_tree_sha256"],
            "file_list_sha256": authority["verification"]["file_list_sha256"],
        },
        "full": {
            "path": str(Path(args.full_manifest)),
            "manifest_sha256": sha256_file(Path(args.full_manifest)),
            "projection": full_manifest_payload.get("projection"),
            "files": len(full_rows),
            "bytes": sum(int(row["bytes"]) for row in full_rows),
            "source_tree_sha256": full["verification"]["source_tree_sha256"],
            "formal_overlay_tree_sha256": full["verification"]["formal_overlay_tree_sha256"],
            "file_list_sha256": full["verification"]["file_list_sha256"],
        },
    }
    return document


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--utility", type=Path, default=REPO / "_root-promo-split-20260902" / "tools" / "zg361_phase2_product_projection.py")
    parser.add_argument("--core-manifest", type=Path, default=DEFAULT_CORE_MANIFEST)
    parser.add_argument("--callable-manifest", type=Path, default=DEFAULT_CALLABLE_MANIFEST)
    parser.add_argument("--event-manifest", type=Path, default=DEFAULT_EVENT_MANIFEST)
    parser.add_argument("--authority-manifest", type=Path, default=DEFAULT_AUTHORITY_MANIFEST)
    parser.add_argument("--full-manifest", type=Path, default=DEFAULT_FULL_MANIFEST)
    parser.add_argument("--core-root", type=Path, default=DEFAULT_CORE_ROOT)
    parser.add_argument("--callable-root", type=Path, default=DEFAULT_CALLABLE_ROOT)
    parser.add_argument("--event-root", type=Path, default=DEFAULT_EVENT_ROOT)
    parser.add_argument("--authority-root", type=Path, default=DEFAULT_AUTHORITY_ROOT)
    parser.add_argument("--full-root", type=Path, default=DEFAULT_FULL_ROOT)
    parser.add_argument("--locaug-root", type=Path, default=DEFAULT_LOCAUG_ROOT)
    parser.add_argument("--current-root", type=Path, default=DEFAULT_CURRENT_ROOT)
    parser.add_argument("--authority-report", type=Path, default=DEFAULT_AUTHORITY_REPORT)
    parser.add_argument("--event-core-report", type=Path, default=DEFAULT_EVENT_CORE_REPORT)
    parser.add_argument("--locaug-report", type=Path, default=DEFAULT_LOCAUG_REPORT)
    parser.add_argument("--full-report", type=Path, default=DEFAULT_FULL_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        document = build_document(args)
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (AuditError, OSError, UnicodeError) as error:
        print(f"localization fan-out audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({
        "result": "GREEN",
        "output": str(output),
        "authority_rows": len(document["authority"]["rows"]),
        "authority_loc_rows": document["authority"]["localization"]["files"],
        "full_rows": len(document["comparison"]["rows"]),
        "full_loc_rows": document["comparison"]["localization"]["files"],
        "locaug_loc_rows": document["intermediate_red"]["localization"]["files"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
