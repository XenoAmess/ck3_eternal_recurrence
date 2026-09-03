#!/usr/bin/env python3
"""Build a read-only delivery queue for the two phase-two promo cuts.

The existing planner and completion gates answer whether a cut is valid.  This
small companion answers the operator's more immediate question: what is
unblocked now, which of the eight shared capture spans is still missing, and
what should happen next for each independent cut?  It only reads runbooks and
an optional capture root, then writes one status report when ``--output`` is
requested.  It never launches CK3, invokes TTS/FFmpeg, creates media, or
changes a source artifact.

The report intentionally keeps relative estimates instead of inventing a
clock-time promise.  Estimates become useful only after the real capture
intake is GREEN; a RED capture remains the first shared blocker for both cuts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_footage_intake import validate_footage_intake
from zhongguo_phase2_promo_cuts import CUTS


KIND = "zg361_phase2_promo_delivery_queue"
SCHEMA_VERSION = 1
_SHA = re.compile(r"^[0-9A-Fa-f]{64}$")
_CUT_IDS = tuple(cut.cut_id for cut in CUTS)
_SPAN_IDS = tuple(scenario.span_id for scenario in PHASE2_CAPTURE_SCENARIOS)

# These are intentionally coarse planning ranges.  They describe work after
# its dependency is satisfied, not a guarantee that a failed live run will
# finish inside the range.
_ACTION_META: dict[str, dict[str, object]] = {
    "capture_eight_clean_spans": {
        "label": "取得并通过八段真实 CK3 clean-span intake",
        "estimate_minutes": [20, 40],
        "estimate_basis": "可用的正式 CK3 桌面会话已就绪后，录制与整理一轮",
    },
    "source_footage_human_review_1x": {
        "label": "逐段做 source footage 1× 人工审阅并写回执",
        "estimate_minutes": [15, 30],
        "estimate_basis": "八段素材已 GREEN；按原始片段完整观看一次",
    },
    "promote_reviewed_authoring_into_project": {
        "label": "把通过审阅的 claims 晋升为该 cut 的 project 配置",
        "estimate_minutes": [5, 10],
        "estimate_basis": "source-review 回执与 intake 已存在",
    },
    "refresh_media_receipt_after_fetch": {
        "label": "在已更新的宣传工具上重新生成 media preflight 回执",
        "estimate_minutes": [5, 15],
        "estimate_basis": "宣传工具 HEAD 已固定且工作树干净",
    },
    "prime_reviewed_xiaoxiao_cache": {
        "label": "为该 cut 准备已审阅 cue 的 Xiaoxiao 缓存",
        "estimate_minutes": [10, 25],
        "estimate_basis": "media preflight GREEN；仅使用真实 provider/cache",
    },
    "build_unreviewed_candidate": {
        "label": "生成该 cut 的候选视频",
        "estimate_minutes": [45, 90],
        "estimate_basis": "素材、TTS、字幕和 media preflight 均 GREEN；两条 cut 可并行",
    },
    "claims_audit_pending": {
        "label": "对候选视频运行 claims/visual integrity audit",
        "estimate_minutes": [5, 15],
        "estimate_basis": "候选媒体与绑定 probe 已生成",
    },
    "final_video_review_1x": {
        "label": "完成该 cut 的全长 1× 人工审片",
        "estimate_minutes": [20, 35],
        "estimate_basis": "候选时长约 8–12 分钟，含复核记录",
    },
    "review_round_1_pending": {
        "label": "完成第一轮独立 1× 审片回执",
        "estimate_minutes": [20, 35],
        "estimate_basis": "候选视频已通过自动审计",
    },
    "review_round_2_pending": {
        "label": "完成第二轮独立 1× 审片回执",
        "estimate_minutes": [20, 35],
        "estimate_basis": "候选视频已通过自动审计",
    },
    "record_signoff": {
        "label": "把两轮审片意见绑定到候选 SHA-256 并签核",
        "estimate_minutes": [5, 10],
        "estimate_basis": "两名不同审阅者的回执已齐",
    },
    "export_pending": {
        "label": "执行 release-profile 校验并导出本地交付包",
        "estimate_minutes": [5, 15],
        "estimate_basis": "候选已签核且导出 allowlist GREEN",
    },
    "publish_target_pending": {
        "label": "补齐明确的发布平台、账号和目标授权",
        "estimate_minutes": [5, 10],
        "estimate_basis": "需要项目所有者的外部发布目标信息",
    },
    "publish_pending": {
        "label": "在获授权的平台发布并保存远端校验回执",
        "estimate_minutes": [10, 20],
        "estimate_basis": "本地导出包 GREEN 且已有明确发布授权",
    },
}


class DeliveryQueueError(ValueError):
    """Raised when an input runbook cannot be inspected safely."""


def _sha256(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DeliveryQueueError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise DeliveryQueueError(f"JSON root is not an object: {path}")
    return value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _bool_checks(value: object) -> tuple[int, int, bool]:
    """Return (passed, total, all_green) for a runbook check mapping."""

    checks = _mapping(value).get("checks")
    checks = checks if isinstance(checks, Mapping) else {}
    values = [item is True for item in checks.values()]
    return sum(values), len(values), bool(values) and all(values)


def _record_if_file(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.is_file():
        return None
    try:
        return _sha256(path)
    except OSError:
        return None


def _absolute_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        return None
    return candidate.resolve()


def _runbook_cut(runbook: Mapping[str, object]) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    if runbook.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if runbook.get("kind") != "zg361_phase2_final_promo_deterministic_runbook":
        errors.append("runbook_kind_invalid")
    cut = _mapping(runbook.get("cut"))
    cut_id = cut.get("id") if isinstance(cut.get("id"), str) else None
    if cut_id not in _CUT_IDS:
        errors.append("cut_id_invalid")
    chapter_order = _mapping(runbook.get("editorial_plan")).get("chapter_order")
    expected = list(next((item.editorial_chapter_order for item in CUTS if item.cut_id == cut_id), ()))
    if not isinstance(chapter_order, list) or chapter_order != expected:
        errors.append("editorial_chapter_order_invalid")
    return cut_id, errors


def _first_blocker(runbook: Mapping[str, object], *, footage_ready: bool) -> str | None:
    raw = runbook.get("blockers")
    blockers = [str(item) for item in raw if isinstance(item, str)] if isinstance(raw, list) else []
    if not footage_ready:
        return "footage_pending"
    for blocker in blockers:
        if blocker != "footage_pending":
            return blocker
    if runbook.get("result") == "GREEN" and runbook.get("status") == "COMPLETE":
        return None
    return "runbook_pending"


def _planned_path(runbook: Mapping[str, object], name: str) -> Path | None:
    paths = _mapping(runbook.get("planned_paths"))
    return _absolute_path(paths.get(name))


def _next_dependency_blocker(
    runbook: Mapping[str, object], *, footage_ready: bool
) -> str | None:
    """Select the first *operational* step, not merely the first RED flag.

    The planner's top-level ``blockers`` intentionally lists every downstream
    gate.  Once footage turns GREEN, choosing the first list item would skip
    source review and authoring promotion.  This resolver walks the declared
    runbook paths in production order and only falls back to that blocker list
    after the path-based steps are present.
    """

    if not footage_ready:
        return "footage_pending"
    _, _, project_green = _bool_checks(runbook.get("project"))
    _, _, authoring_green = _bool_checks(runbook.get("authoring_claim_ledger"))
    if not project_green or not authoring_green:
        return "authoring_claim_ledger_invalid"
    path_steps = (
        ("source_footage_human_review_1x", "source_review_receipt"),
        ("promote_reviewed_authoring_into_project", "promoted_project_config"),
        ("refresh_media_receipt_after_fetch", "media_preflight_receipt"),
        ("prime_reviewed_xiaoxiao_cache", "tts_prime_receipt"),
        ("build_unreviewed_candidate", "candidate_run_manifest"),
        ("claims_audit_pending", "automated_audit_report"),
        ("review_round_1_pending", "claims_source_review_receipt"),
        ("review_round_2_pending", "final_candidate_review_receipt"),
    )
    for action_id, path_name in path_steps:
        path = _planned_path(runbook, path_name)
        if path is None or not path.is_file():
            return action_id

    export_dir = _planned_path(runbook, "export_directory")
    if export_dir is None or not export_dir.is_dir() or not (
        export_dir / "release-bundle-manifest.json"
    ).is_file():
        return "export_pending"

    target = _mapping(_mapping(runbook.get("inputs")).get("publish_target_authority"))
    if target.get("result") != "GREEN":
        return "publish_target_pending"
    if runbook.get("result") == "GREEN" and runbook.get("status") == "COMPLETE":
        return None
    blockers = runbook.get("blockers")
    if isinstance(blockers, list):
        for blocker in blockers:
            if isinstance(blocker, str) and blocker != "footage_pending":
                return blocker
    return "runbook_pending"


def _action_for_blocker(blocker: str | None) -> dict[str, object]:
    if blocker == "footage_pending":
        action_id = "capture_eight_clean_spans"
    elif blocker in _ACTION_META:
        action_id = blocker
    elif blocker in {"candidate_media_pending", "media_receipt_pending"}:
        action_id = "build_unreviewed_candidate" if blocker == "candidate_media_pending" else "refresh_media_receipt_after_fetch"
    elif blocker == "claims_audit_pending":
        action_id = "claims_audit_pending"
    elif blocker in {"review_round_1_pending", "review_round_2_pending"}:
        action_id = blocker
    elif blocker == "authoring_claim_ledger_invalid":
        action_id = "promote_reviewed_authoring_into_project"
    elif blocker is None:
        return {
            "id": "complete",
            "label": "该 cut 已完成所有交付门",
            "ready": False,
            "estimate_minutes": [0, 0],
            "estimate_basis": "runbook completion gate GREEN",
        }
    else:
        action_id = "inspect_runbook_blocker"
    meta = _ACTION_META.get(action_id, {})
    return {
        "id": action_id,
        "label": meta.get("label", f"处理 blocker：{blocker}"),
        "reason_code": blocker,
        "ready": False,
        "estimate_minutes": list(meta.get("estimate_minutes", [0, 0])),
        "estimate_basis": meta.get("estimate_basis", "需要先读取该 blocker 对应的 runbook 步骤"),
    }


def _span_rows(intake: Mapping[str, object] | None) -> tuple[list[dict[str, object]], int]:
    rows = _mapping(intake).get("spans")
    by_id = {
        str(row.get("span_id")): row
        for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("span_id"), str)
    } if isinstance(rows, list) else {}
    output: list[dict[str, object]] = []
    ready_count = 0
    for scenario in PHASE2_CAPTURE_SCENARIOS:
        source = by_id.get(scenario.span_id)
        clean = isinstance(source, Mapping) and source.get("clean_gate_green") is True
        postcondition = isinstance(source, Mapping) and source.get("postcondition_green") is True
        ready = clean and postcondition
        if ready:
            ready_count += 1
        output.append(
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "gameplay_entrypoint": scenario.gameplay_entrypoint,
                "gui_surfaces": list(scenario.gui_surfaces),
                "mcp_queries": list(scenario.mcp_queries),
                "mcp_actions": list(scenario.mcp_actions),
                "postcondition": scenario.postcondition,
                "status": "GREEN" if ready else "pending",
                "clean_gate_green": clean,
                "postcondition_green": postcondition,
                "reason_code": None if ready else (
                    "clean_gate_pending" if not clean else "postcondition_pending"
                ),
            }
        )
    return output, ready_count


def _capture_source(
    runbooks: Sequence[Mapping[str, object]], capture_root: Path | None
) -> tuple[dict[str, object], Path | None, str]:
    selected = capture_root.expanduser().resolve() if capture_root is not None else None
    source = "argument" if selected is not None else "none"
    if selected is None:
        # A runbook may already carry a hash-bound capture path.  Reusing it is
        # read-only and makes this queue useful immediately after a planner run;
        # a missing or RED path remains visibly RED.
        for runbook in runbooks:
            inputs = _mapping(runbook.get("inputs"))
            capture = _mapping(inputs.get("capture"))
            candidate = _absolute_path(capture.get("capture_root"))
            if candidate is not None:
                selected = candidate
                source = "runbook"
                break
    intake = validate_footage_intake(selected)
    return intake, selected, source


def _cut_report(
    runbook: Mapping[str, object],
    *,
    expected_cut_id: str,
    intake: Mapping[str, object],
    span_ready_count: int,
) -> dict[str, object]:
    cut_id, errors = _runbook_cut(runbook)
    if cut_id != expected_cut_id:
        errors.append("cut_order_or_identity_mismatch")
    cut = _mapping(runbook.get("cut"))
    footage_ready = intake.get("result") == "GREEN"
    blocker = (
        "runbook_invalid"
        if errors
        else _next_dependency_blocker(runbook, footage_ready=footage_ready)
    )
    if blocker is None and runbook.get("result") != "GREEN":
        blocker = "runbook_pending"
    action = _action_for_blocker(blocker)

    gate_rows = {
        "project": _bool_checks(runbook.get("project")),
        "authoring_claim_ledger": _bool_checks(runbook.get("authoring_claim_ledger")),
        "completion_gate": _bool_checks(runbook.get("completion_gate")),
    }
    passed = sum(row[0] for row in gate_rows.values())
    total = sum(row[1] for row in gate_rows.values())
    if footage_ready:
        passed += 1
    total += 1
    if not errors and blocker is None:
        status = "COMPLETE"
    elif blocker == "footage_pending":
        status = "BLOCKED"
    elif errors:
        status = "INVALID"
    else:
        status = "IN_PROGRESS"
    return {
        "cut_id": expected_cut_id,
        "status": status,
        "result": "GREEN" if status == "COMPLETE" else "RED",
        "current_progress": {
            "label": (
                "authoring-ready; real footage pending"
                if span_ready_count == 0
                else f"{span_ready_count}/8 shared real spans GREEN"
            ),
            "shared_spans_green": span_ready_count,
            "gate_checks_passed": passed,
            "gate_checks_total": total,
            "gate_checks": {
                name: {"passed": row[0], "total": row[1], "green": row[2]}
                for name, row in gate_rows.items()
            },
        },
        "blockers": list(runbook.get("blockers", [])) if isinstance(runbook.get("blockers"), list) else errors,
        "next_action": action,
        "deliverable": {
            "artifact_id": cut.get("deliverable_artifact_id"),
            "relative_path": cut.get("deliverable_relative_path"),
            "run_id": cut.get("run_id"),
        },
        "input": {
            "runbook_result": runbook.get("result"),
            "runbook_status": runbook.get("status"),
            "runbook_reason_code": runbook.get("reason_code"),
        },
        "errors": errors,
    }


def build_delivery_queue(
    character_runbook: Path,
    institution_runbook: Path,
    *,
    capture_root: Path | None = None,
) -> dict[str, object]:
    """Read two runbooks and return a deterministic operator queue."""

    paths = [character_runbook.expanduser().resolve(), institution_runbook.expanduser().resolve()]
    runbooks = [_read_json(path) for path in paths]
    intake, selected_capture, capture_source = _capture_source(runbooks, capture_root)
    spans, span_ready_count = _span_rows(intake)
    cut_reports = [
        _cut_report(
            runbook,
            expected_cut_id=expected,
            intake=intake,
            span_ready_count=span_ready_count,
        )
        for expected, runbook in zip(_CUT_IDS, runbooks)
    ]
    shared_errors: list[str] = []
    if len(runbooks) != 2:
        shared_errors.append("exactly_two_runbooks_required")
    if any(
        "cut_order_or_identity_mismatch" in row.get("errors", [])
        for row in cut_reports
    ):
        shared_errors.append("cut_order_must_be_character_then_institution")
    if len({row["deliverable"].get("artifact_id") for row in cut_reports}) != 2:
        shared_errors.append("deliverable_artifact_ids_must_be_distinct")
    footage_ready = intake.get("result") == "GREEN"
    shared_action = _action_for_blocker(None if footage_ready else "footage_pending")
    if shared_errors:
        shared_action = _action_for_blocker("runbook_invalid")
    complete = (
        not shared_errors
        and footage_ready
        and all(row["status"] == "COMPLETE" for row in cut_reports)
    )
    status = "COMPLETE" if complete else ("BLOCKED" if not footage_ready else "IN_PROGRESS")
    result = "GREEN" if complete else "RED"
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "result": result,
        "status": status,
        "shared": {
            "capture_root": None if selected_capture is None else str(selected_capture),
            "capture_source": capture_source,
            "footage_result": intake.get("result"),
            "footage_reason_code": intake.get("reason_code"),
            "spans_green": span_ready_count,
            "spans_total": len(_SPAN_IDS),
            "missing_span_ids": [
                row["span_id"] for row in spans if row["status"] != "GREEN"
            ],
            "span_status": spans,
            "next_action": shared_action,
            "errors": shared_errors,
        },
        "cuts": cut_reports,
        "delivery_window": {
            "ready_after": "shared eight-span intake GREEN" if not footage_ready else "current blockers cleared",
            "parallel_cuts": True,
            "estimate_minutes_after_footage": [45, 90],
            "estimate_basis": "每条 cut 独立 TTS/候选/审片/导出；素材齐备后两条可并行",
            "fixed_clock_time_promised": False,
        },
        "execution_attestation": {
            "ck3_started": False,
            "tts_started": False,
            "ffmpeg_started": False,
            "media_generated": False,
            "publish_performed": False,
        },
        "inputs": {
            "runbooks": [_record_if_file(path) for path in paths],
            "capture_intake": intake,
        },
    }


def _text_report(report: Mapping[str, object]) -> str:
    shared = _mapping(report.get("shared"))
    lines = [
        f"{report.get('result')} / {report.get('status')}",
        f"shared footage: {shared.get('spans_green', 0)}/{shared.get('spans_total', 8)} GREEN",
    ]
    action = _mapping(shared.get("next_action"))
    lines.append(f"shared next: {action.get('label')} ({action.get('estimate_minutes')})")
    for cut in report.get("cuts", []):
        if not isinstance(cut, Mapping):
            continue
        next_action = _mapping(cut.get("next_action"))
        lines.append(
            f"{cut.get('cut_id')}: {cut.get('status')}; "
            f"next={next_action.get('label')} ({next_action.get('estimate_minutes')})"
        )
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--character-runbook", type=Path, required=True)
    result.add_argument("--institution-runbook", type=Path, required=True)
    result.add_argument(
        "--capture-root",
        type=Path,
        help="optional real capture bundle; otherwise use the first absolute path in a runbook",
    )
    result.add_argument("--output", type=Path, help="write the JSON report; refuses to overwrite")
    result.add_argument("--text", action="store_true", help="print a compact human-readable summary")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report = build_delivery_queue(
        args.character_runbook,
        args.institution_runbook,
        capture_root=args.capture_root,
    )
    if args.output is not None:
        output = args.output.expanduser().resolve()
        if output.exists():
            raise DeliveryQueueError(f"refusing to overwrite existing output: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    rendered = _text_report(report) if args.text else json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["KIND", "SCHEMA_VERSION", "DeliveryQueueError", "build_delivery_queue"]
