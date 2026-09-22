#!/usr/bin/env python3
"""Report current vanilla-event research metadata without reading CK3 or saves.

The canonical registry remains the owner. This report does not reinterpret the
existing discovery API's evidence classes or infer gameplay evidence from them.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "xar.ck3.vanilla-event-research-report"
SCHEMA_VERSION = 1
TOOL_VERSION = "1"
SHA256 = re.compile(r"[0-9a-fA-F]{64}")
BOUNDARIES = (
    "Counts use registered event keys, not all CK3 events or decision-tree branches.",
    "Source-hash coverage checks declared metadata syntax; it does not read source files or prove semantic review completeness.",
    "Non-legacy observations include RED and visual observations; their presence does not prove a successful action or material postcondition.",
    "Repository HEAD is context only; catalog digests identify the exact working-tree data used.",
)


def load_catalog() -> tuple[dict[str, object], str, str]:
    """Load the same canonical tables used by the registry and discovery API."""
    source = str(ROOT / "ck3_autonomous_player" / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from xar_autoplayer.vanilla_events import (
        DEFAULT_VANILLA_EVENT_ANALYSIS,
        DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
        EXACT_CK3_BUILD,
        EXACT_CK3_EXE_SHA256,
    )

    return (
        {
            "contracts": DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
            "analysis": DEFAULT_VANILLA_EVENT_ANALYSIS,
            "observations": DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        },
        EXACT_CK3_BUILD,
        EXACT_CK3_EXE_SHA256,
    )


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, child in value.items():
            if not isinstance(key, (str, int)) or isinstance(key, bool):
                raise ValueError("metadata keys must be strings or integers")
            normalized = str(key)
            if normalized in result:
                raise ValueError("metadata contains colliding JSON keys")
            result[normalized] = _json_value(child)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(child) for child in value]
    return value


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        _json_value(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> dict[str, object]:
    payload = canonical_bytes(value)
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def _coverage(count: int, denominator: int) -> dict[str, object]:
    return {
        "count": count,
        "registered_event_denominator": denominator,
        "percent": round(100 * count / denominator, 2) if denominator else None,
    }


def _source_hash_status(analysis: object) -> str:
    if not isinstance(analysis, Mapping) or "source_sha256" not in analysis:
        return "missing"
    hashes = analysis["source_sha256"]
    if not isinstance(hashes, Mapping):
        return "invalid"
    if not hashes:
        return "empty"
    if any(
        not isinstance(path, str) or not path.strip()
        or not isinstance(digest, str) or SHA256.fullmatch(digest) is None
        for path, digest in hashes.items()
    ):
        return "invalid"
    return "valid_nonempty_map"


def _observation_status(observation: object, *, present: bool) -> str:
    if not present:
        return "missing"
    if not isinstance(observation, Mapping):
        return "invalid"
    exemplars = observation.get("exemplars")
    if not isinstance(exemplars, (list, tuple)):
        return "invalid"
    if not exemplars:
        return "empty"
    kinds = [e.get("kind") if isinstance(e, Mapping) else None for e in exemplars]
    if any(isinstance(kind, str) and kind.strip() and kind != "legacy-live-binding" for kind in kinds):
        return "nonlegacy_present"
    if all(kind == "legacy-live-binding" for kind in kinds):
        return "legacy_only"
    return "unclassified"


def _summary(catalog: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    contracts, analysis, observations = (
        catalog["contracts"], catalog["analysis"], catalog["observations"]
    )
    count = len(contracts)
    source_counts = dict.fromkeys(("missing", "empty", "invalid", "valid_nonempty_map"), 0)
    observation_counts = dict.fromkeys(
        ("missing", "empty", "invalid", "legacy_only", "nonlegacy_present", "unclassified"), 0
    )
    for key in contracts:
        source_counts[_source_hash_status(analysis.get(key))] += 1
        observation_counts[_observation_status(observations.get(key), present=key in observations)] += 1
    return {
        "registered_events": count,
        "analysis_metadata_rows": len(analysis),
        "observation_metadata_rows": len(observations),
        "source_hash_field_counts": source_counts,
        "valid_source_hash_field_coverage": _coverage(source_counts["valid_nonempty_map"], count),
        "observation_metadata_counts": observation_counts,
        "nonlegacy_observation_metadata_coverage": _coverage(observation_counts["nonlegacy_present"], count),
        "digests": {**{name: _digest(value) for name, value in catalog.items()}, "catalog": _digest(catalog)},
    }


def build_report(
    catalog: Mapping[str, object], *, ck3_build: str, ck3_exe_sha256: str,
    repository_head: str | None = None,
    event_keys: Sequence[str] = (), namespaces: Sequence[str] = (),
) -> dict[str, object]:
    """Create a deterministic, detached report; no I/O or gameplay inference."""
    normalized = json.loads(canonical_bytes(catalog))
    tables: dict[str, dict[str, object]] = {}
    for name in ("contracts", "analysis", "observations"):
        table = normalized.get(name)
        if not isinstance(table, dict):
            raise ValueError(f"catalog.{name} must be a mapping")
        tables[name] = table
    registered = set(tables["contracts"])
    for name in ("analysis", "observations"):
        if set(tables[name]) - registered:
            raise ValueError(f"catalog.{name} references unregistered event keys")
    key_filter, namespace_filter = sorted(set(event_keys)), sorted(set(namespaces))
    if any(not value or value != value.strip() for value in [*key_filter, *namespace_filter]):
        raise ValueError("filters must be non-empty and have no surrounding whitespace")
    unknown_keys = set(key_filter) - registered
    known_namespaces = {key.rsplit(".", 1)[0] for key in registered}
    unknown_namespaces = set(namespace_filter) - known_namespaces
    if unknown_keys or unknown_namespaces:
        raise ValueError(f"unknown event keys: {sorted(unknown_keys)}; unknown namespaces: {sorted(unknown_namespaces)}")
    selected_keys = sorted(
        key for key in registered
        if (not key_filter or key in key_filter)
        and (not namespace_filter or key.rsplit(".", 1)[0] in namespace_filter)
    )
    selected = {
        name: {key: table[key] for key in selected_keys if key in table}
        for name, table in tables.items()
    }
    report: dict[str, object] = {
        "schema": SCHEMA, "schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION,
        "ck3_build": ck3_build, "ck3_exe_sha256": ck3_exe_sha256,
        "repository_head": repository_head,
        "filters": {"event_keys": key_filter, "namespaces": namespace_filter, "combination": "intersection"},
        "catalog": _summary(tables), "selected": _summary(selected),
        "interpretation_boundaries": list(BOUNDARIES),
    }
    if key_filter or namespace_filter:
        report["selected_events"] = [
            {
                "event_definition_key": key,
                "source_hash_field_status": _source_hash_status(selected["analysis"].get(key)),
                "observation_metadata_status": _observation_status(selected["observations"].get(key), present=key in selected["observations"]),
            }
            for key in selected_keys
        ]
    return report


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(report: Mapping[str, object], format_name: str) -> str:
    if format_name == "json":
        return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if format_name != "markdown":
        raise ValueError(f"unsupported report format: {format_name}")
    lines = [
        f"CK3 {_markdown_cell(report['ck3_build'])} event research metadata",
        "", f"Schema: `{SCHEMA}` v{report['schema_version']}; tool v{report['tool_version']}.",
        f"CK3 EXE SHA-256: `{report['ck3_exe_sha256']}`.",
        f"Repository HEAD (context): `{report['repository_head'] or 'unavailable'}`.",
        "", f"Filters: `{json.dumps(report['filters'], ensure_ascii=False, sort_keys=True)}`.",
        "", "| Metadata measure | Whole catalog | Selected events |", "| --- | ---: | ---: |",
    ]
    for label, field in (("Registered event keys", "registered_events"), ("Analysis metadata rows", "analysis_metadata_rows"), ("Observation metadata rows", "observation_metadata_rows")):
        lines.append(f"| {label} | {report['catalog'][field]} | {report['selected'][field]} |")
    for label, field in (("Valid source-hash field coverage", "valid_source_hash_field_coverage"), ("Non-legacy observation metadata coverage", "nonlegacy_observation_metadata_coverage")):
        cells = []
        for scope in ("catalog", "selected"):
            row = report[scope][field]
            percentage = f"{row['percent']:.2f}%" if row['percent'] is not None else "N/A"
            cells.append(f"{row['count']}/{row['registered_event_denominator']} ({percentage})")
        lines.append(f"| {label} | {' | '.join(cells)} |")
    for field in ("source_hash_field_counts", "observation_metadata_counts"):
        for status in report["catalog"][field]:
            lines.append(f"| {field}: {status} | {report['catalog'][field][status]} | {report['selected'][field][status]} |")
    lines.extend(["", "| Scope / canonical data | Bytes | SHA-256 |", "| --- | ---: | --- |"])
    for scope in ("catalog", "selected"):
        for name, digest in report[scope]["digests"].items():
            lines.append(f"| {scope} / {name} | {digest['bytes']} | `{digest['sha256']}` |")
    if "selected_events" in report:
        lines.extend(["", "| Event key | Source-hash field | Observation metadata |", "| --- | --- | --- |"])
        for row in report["selected_events"]:
            lines.append("| " + " | ".join(_markdown_cell(row[field]) for field in ("event_definition_key", "source_hash_field_status", "observation_metadata_status")) + " |")
    lines.append("")
    lines.extend(f"- {boundary}" for boundary in report["interpretation_boundaries"])
    return "\n".join(lines) + "\n"


def _repository_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40,64}", value) else None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format (default: json).")
    parser.add_argument("--event-key", action="append", default=[], help="Exact registered event key; repeat for a union of keys.")
    parser.add_argument("--namespace", action="append", default=[], help="Exact namespace; repeat for a union. Combined with keys by intersection.")
    parser.add_argument("--output", type=Path, help="Explicit new output file; parent must exist and existing files are never overwritten.")
    args = parser.parse_args(argv)
    try:
        catalog, build, exe_hash = load_catalog()
        report = build_report(
            catalog, ck3_build=build, ck3_exe_sha256=exe_hash,
            repository_head=_repository_head(), event_keys=args.event_key, namespaces=args.namespace,
        )
        text = render_report(report, args.format)
        if args.output is None:
            sys.stdout.write(text)
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
