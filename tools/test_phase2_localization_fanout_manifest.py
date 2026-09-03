#!/usr/bin/env python3
"""Validate the Phase-2 localization fan-out audit artifact.

The default mode is offline and validates the committed JSON contract.  The
optional ``--verify-external`` mode re-reads the disposable projection roots
named by the artifact and checks every declared row byte-for-byte.  Neither
mode starts CK3 or mutates a source, runner, freeze, or profile tree.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Iterable


TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
DEFAULT_ARTIFACT = REPO / "docs" / "phase2-promo" / "phase2-localization-fanout-manifest-2026-09-03.json"
sys.path.insert(0, str(TOOLS))
import generate_phase2_localization_fanout_manifest as audit  # noqa: E402


class ValidationError(ValueError):
    """The machine-readable audit does not satisfy its contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"cannot read artifact {path}: {error}") from error
    require(isinstance(payload, dict), "artifact root must be an object")
    return payload


def declared_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = summary.get("rows")
    if rows is None:
        rows = summary.get("localization_rows")
    require(isinstance(rows, list), f"{summary.get('name')} has no row list")
    return rows


def validate_summary(
    label: str,
    summary: dict[str, Any],
    *,
    expected_count: int,
    verify_external: bool,
) -> list[dict[str, Any]]:
    require(isinstance(summary, dict), f"{label} summary is not an object")
    verification = summary.get("verification")
    require(isinstance(verification, dict), f"{label} has no verification block")
    rows = declared_rows(summary)
    canonical = audit.canonical_rows(rows)
    # Compact input summaries expose localization rows only.  The full row
    # count remains in verification and can be checked against the mounted
    # tree in --verify-external mode.
    if "rows" in summary:
        require(len(canonical) == expected_count, f"{label} row count mismatch")
        require(
            int(verification.get("rows_verified", -1)) == expected_count,
            f"{label} verification row count mismatch",
        )
        require(
            int(verification.get("bytes_verified", -1))
            == sum(int(row["bytes"]) for row in canonical),
            f"{label} verification byte count mismatch",
        )
        expected_hashes = {
            "source_tree_sha256": audit.source_tree_digest(canonical),
            "formal_overlay_tree_sha256": audit.formal_overlay_digest(canonical),
            "file_list_sha256": audit.file_list_digest(canonical),
        }
        for key, expected in expected_hashes.items():
            require(verification.get(key) == expected, f"{label} {key} mismatch")
    else:
        loc = canonical
        require(
            int(summary.get("localization", {}).get("files", -1)) == len(loc),
            f"{label} compact localization count mismatch",
        )

    for row in rows:
        if "language" in row:
            language, owner = audit.classify_localization(row["path"])
            require(row.get("language") == language, f"{label} language classification mismatch")
            require(row.get("owner") == owner, f"{label} owner classification mismatch")

    if verify_external:
        root_value = summary.get("source_root")
        require(isinstance(root_value, str), f"{label} source_root missing")
        root = Path(root_value)
        observed = audit.scan_runtime_rows(root)
        require(
            len(observed) == int(verification.get("rows_verified", -1)),
            f"{label} external row count mismatch",
        )
        require(
            sum(int(row["bytes"]) for row in observed)
            == int(verification.get("bytes_verified", -1)),
            f"{label} external byte count mismatch",
        )
        require(
            audit.source_tree_digest(observed) == verification.get("source_tree_sha256"),
            f"{label} external source tree digest mismatch",
        )
        require(
            audit.formal_overlay_digest(observed) == verification.get("formal_overlay_tree_sha256"),
            f"{label} external formal tree digest mismatch",
        )
        require(
            audit.file_list_digest(observed) == verification.get("file_list_sha256"),
            f"{label} external file-list digest mismatch",
        )
        if "rows" in summary:
            require(
                {row["path"]: row for row in audit.canonical_rows(rows)}
                == {row["path"]: row for row in observed},
                f"{label} external rows differ",
            )
        else:
            expected_loc = {
                row["path"]: row
                for row in audit.canonical_rows(audit.localization_rows(observed))
            }
            require(
                {
                    row["path"]: row
                    for row in audit.canonical_rows(canonical)
                }
                == expected_loc,
                f"{label} compact localization rows differ",
            )
    return canonical


def validate_matrix(label: str, rows: Iterable[dict[str, Any]], owners: set[str]) -> None:
    loc = audit.localization_rows(rows)
    by_owner: dict[str, list[dict[str, Any]]] = {}
    for row in loc:
        by_owner.setdefault(str(row["owner"]), []).append(row)
    require(set(by_owner) == owners, f"{label} owner set mismatch")
    for owner in owners:
        owner_rows = by_owner[owner]
        require(len(owner_rows) == 9, f"{label} {owner} is not 9-way fan-out")
        require(
            {row["language"] for row in owner_rows} == set(audit.LANGUAGES),
            f"{label} {owner} language set mismatch",
        )
    counts = Counter(str(row["language"]) for row in loc)
    require(all(counts[language] == len(owners) for language in audit.LANGUAGES), f"{label} language matrix mismatch")


def validate_digest_contract(payload: dict[str, Any]) -> None:
    authority = payload["authority"]
    full = payload["comparison"]
    event = payload["inputs"]["event_core_manifest"]
    expected = {
        ("authority", "all"): (135, 3224382, "73617b045a30807646c1a4757a57d534bb3404ddcf6fb7d5b20a112daee93ea3"),
        ("authority", "workforce"): (81, 250910, "1dcdd35c38e175a564f58b06cc1f477ca3047e73c1ecea4f2a9d2126c43411ef"),
        ("authority", "b1"): (9, 66461, "e3af14373211668ab362d6f6bf64d26cb9d1eedf63fcfba150e213642aa3a036"),
        ("authority", "b2"): (9, 29553, "95b0a46293fcc1fd837a34264a0f0a020a8e7dfc7d2bfe07791b30b5bad9204a"),
        ("authority", "incident_platform"): (9, 69333, "6f46ed66a24dbe4fbffe7fe95f95715096abb3f141b2394fc8c0585d2516bbf3"),
        ("authority", "manager_governance"): (9, 14156, "c5c4d45cde9f1ab5a0a063a9cc649a4d9a7c668799f843a38178fc22c5b3ade5"),
        ("full", "all"): (198, 3916856, "cc98901d0b6785fd57c37519d58d8f3300295ee57baa82c14652fc6a84e56b38"),
        ("event", "all"): (18, 2793969, "0860cddfe5981da64b6d158999a993c522cb51048365a1c5062248ddcb72358c"),
    }
    summaries = {"authority": authority, "full": full, "event": event}
    for (summary_name, group), (files, bytes_count, digest) in expected.items():
        groups = summaries[summary_name]["localization"]["digests"]["named_groups"]
        record = groups[group]
        require(record["files"] == files, f"{summary_name}/{group} digest file count mismatch")
        require(record["bytes"] == bytes_count, f"{summary_name}/{group} digest bytes mismatch")
        require(record["source_tree_sha256"] == digest, f"{summary_name}/{group} source digest mismatch")


def validate_payload(payload: dict[str, Any], *, verify_external: bool) -> dict[str, Any]:
    require(payload.get("schema_version") == 1, "unexpected schema version")
    require(payload.get("kind") == "zg361_phase2_localization_fanout_audit", "unexpected artifact kind")
    generator = payload.get("generator") or {}
    require(generator.get("ck3_started_by_generator") is False, "generator must not launch CK3")
    require(generator.get("canonical_source_modified_by_generator") is False, "generator must be read-only")
    for script_name in ("generate_phase2_localization_fanout_manifest.py", "test_phase2_localization_fanout_manifest.py"):
        script_path = TOOLS / script_name
        require(script_path.read_bytes().startswith(b"\xef\xbb\xbf"), f"{script_name} is missing UTF-8 BOM")

    summaries = {
        "core": (payload["inputs"]["core_manifest"], 51),
        "callable": (payload["inputs"]["callable_core_manifest"], 66),
        "event": (payload["inputs"]["event_core_manifest"], 81),
        "authority": (payload["authority"], 201),
        "full": (payload["comparison"], 261),
        "locaug": (payload["intermediate_red"], 162),
        "current": (payload["current_source"], 279),
    }
    rows_by_name: dict[str, list[dict[str, Any]]] = {}
    for label, (summary, expected_count) in summaries.items():
        rows_by_name[label] = validate_summary(label, summary, expected_count=expected_count, verify_external=verify_external)

    validate_matrix("authority", rows_by_name["authority"], {
        "b1", "b2", "incident_platform", "base", "manager_governance", "mechanisms",
        "workforce_ad_fact", "workforce_appointment_fact", "workforce_attribution_fact",
        "workforce_endgame", "workforce_exit_fact", "workforce_normal_exit_fact",
        "workforce_probation_fact", "workforce_rehire_fact", "workforce_remediation_fact",
    })
    validate_matrix("full", rows_by_name["full"], {
        "b1", "b2", "incident_platform", "base", "manager_governance", "mechanisms",
        "workforce_ad_fact", "workforce_appointment_fact", "workforce_attribution_fact",
        "workforce_endgame", "workforce_exit_fact", "workforce_normal_exit_fact",
        "workforce_probation_fact", "workforce_rehire_fact", "workforce_remediation_fact",
        "career_hc", "career_learning", "compensation_runtime", "credit_project",
        "feedback_promotion_pip", "phase2_central", "phase3_metrics_delivery",
    })
    require(len(audit.localization_rows(rows_by_name["locaug"])) == 99, "locaug localization count mismatch")

    delta = payload["fanout_delta"]
    loc_delta = delta["authority_to_full_localization"]
    all_delta = delta["authority_to_full_all_runtime"]
    require((loc_delta["added_count"], loc_delta["removed_count"], loc_delta["changed_count"]) == (63, 0, 9), "localization delta mismatch")
    require((all_delta["added_count"], all_delta["removed_count"], all_delta["changed_count"]) == (63, 3, 9), "all-runtime delta mismatch")
    require(set(delta["full_added_owner_families"]) == {
        "career_hc", "career_learning", "compensation_runtime", "credit_project",
        "feedback_promotion_pip", "phase2_central", "phase3_metrics_delivery",
    }, "full added owner families mismatch")
    require(set(delta["intermediate_missing_owner_families_vs_authority"]) == {"b1", "b2", "incident_platform", "manager_governance"}, "locaug missing owner families mismatch")

    # Every captured run reached the same on_action enumeration boundary, but
    # none is promoted to a GREEN frontend claim.  The marker is evidence of
    # parser progress only; timeout/unfinished status remains authoritative.
    boundary = payload["runtime_boundary"]
    for label in ("authority_report", "event_core_report", "intermediate_locaug_report", "full_loc_report"):
        report = boundary[label]
        require(report.get("exists") is True, f"{label} report missing")
        markers = (report.get("debug_markers") or {}).get("total_on_actions", [])
        require(any("Total of : 881" in marker for marker in markers), f"{label} lacks Total881 marker")
        require(report.get("frontend_observed") is False, f"{label} incorrectly claims frontend GREEN")
    require(boundary["event_core_report"]["result"] == "timeout", "event-core RED boundary changed unexpectedly")
    require(boundary["intermediate_locaug_report"]["result"] == "timeout", "locaug RED boundary changed unexpectedly")
    require(boundary["full_loc_report"]["result"] == "timeout", "full RED boundary changed unexpectedly")

    validate_digest_contract(payload)
    return {
        "result": "GREEN",
        "authority_rows": len(rows_by_name["authority"]),
        "authority_loc_rows": len(audit.localization_rows(rows_by_name["authority"])),
        "full_rows": len(rows_by_name["full"]),
        "full_loc_rows": len(audit.localization_rows(rows_by_name["full"])),
        "locaug_loc_rows": len(audit.localization_rows(rows_by_name["locaug"])),
        "external_roots_verified": verify_external,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--verify-external", action="store_true", help="re-read every named disposable root and verify all bytes/SHA")
    args = parser.parse_args(argv)
    try:
        result = validate_payload(read_artifact(Path(args.artifact).resolve()), verify_external=args.verify_external)
    except (ValidationError, OSError, UnicodeError, KeyError, TypeError, ValueError) as error:
        print(f"phase2 localization fan-out validation failed: {error}", file=sys.stderr)
        return 2
    result["artifact"] = str(Path(args.artifact).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
