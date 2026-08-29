#!/usr/bin/env python3
"""Project one GREEN ZhongGuo promo capture into a zero-placeholder manifest.

The capture runner intentionally keeps one long, lossless-ish MKV plus timeline
marks and lossless policy-card stills.  This tool turns that immutable bundle
into an external release-candidate manifest without trimming or overwriting any
source media.  Claims that lack an independent live shot remain conspicuous
generated evidence/boundary cards; they are never relabelled as gameplay.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence


TOOLS_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = TOOLS_DIRECTORY.parent
REPOSITORY_ROOT = PROJECT_DIRECTORY.parent
DEFAULT_BASE_MANIFEST = PROJECT_DIRECTORY / "promo" / "promo-manifest.json"

if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402


POLICY_IDS = (1, 7, 20, 22, 26, 361)
REQUIRED_MARKS = (
    "recording_started_after_gameplay_hud",
    "calibration_event_visible",
    "managed_scoreboard_visible",
    "policy_cockpit_visible",
    "jingcha_mandate_visible",
    "free_jingcha_planner_visible",
    "superior_assigned_325_visible",
    "received_scoreboard_with_325_visible",
    *(f"policy_card_{mechanism_id:03d}_visible" for mechanism_id in POLICY_IDS),
    "all_requested_product_screens_captured",
    "recording_stop_requested",
)


class PrepareError(RuntimeError):
    """A GREEN capture cannot safely become a release manifest."""


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise PrepareError(f"could not read {label}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PrepareError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PrepareError(f"{label} root must be an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _file_record(path: Path, label: str) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise PrepareError(f"required {label} does not exist: {path}")
    return {
        "path": str(path),
        "label": label,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _indexed_files(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = index.get("files")
    if not isinstance(rows, list):
        raise PrepareError("evidence index files must be an array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise PrepareError("evidence index contains an invalid file row")
        normalized = row["path"].replace("\\", "/")
        if normalized in result:
            raise PrepareError(f"evidence index repeats file {normalized}")
        result[normalized] = row
    return result


def _verify_indexed_file(
    artifact_root: Path,
    indexed: dict[str, dict[str, Any]],
    relative: str,
) -> Path:
    normalized = relative.replace("\\", "/")
    row = indexed.get(normalized)
    if row is None:
        raise PrepareError(f"evidence index is missing {normalized}")
    path = (artifact_root / Path(normalized)).resolve()
    try:
        path.relative_to(artifact_root)
    except ValueError as exc:
        raise PrepareError(f"indexed path escapes capture root: {normalized}") from exc
    if not path.is_file():
        raise PrepareError(f"indexed capture file is missing: {path}")
    actual_bytes = path.stat().st_size
    actual_sha = _sha256(path)
    if row.get("bytes") != actual_bytes:
        raise PrepareError(
            f"evidence index byte count mismatch for {normalized}: "
            f"{row.get('bytes')!r} != {actual_bytes}"
        )
    indexed_sha = row.get("sha256")
    if not isinstance(indexed_sha, str) or indexed_sha.upper() != actual_sha:
        raise PrepareError(f"evidence index SHA-256 mismatch for {normalized}")
    return path


def _mark_map(timeline: dict[str, Any]) -> dict[str, float]:
    rows = timeline.get("marks")
    if not isinstance(rows, list):
        raise PrepareError("capture timeline marks must be an array")
    marks: dict[str, float] = {}
    prior = -1.0
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("label"), str):
            raise PrepareError("capture timeline contains an invalid mark")
        seconds = row.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise PrepareError(f"timeline mark {row['label']!r} has invalid seconds")
        seconds = float(seconds)
        if seconds < 0 or seconds < prior:
            raise PrepareError("capture timeline marks must be non-negative and ordered")
        prior = seconds
        if row["label"] in marks:
            raise PrepareError(f"capture timeline repeats mark {row['label']!r}")
        marks[row["label"]] = seconds
    missing = [label for label in REQUIRED_MARKS if label not in marks]
    if missing:
        raise PrepareError("capture timeline is missing marks: " + ", ".join(missing))
    return marks


def _capture_bundle(artifact_root: Path) -> dict[str, Any]:
    artifact_root = artifact_root.expanduser().resolve()
    if not artifact_root.is_dir():
        raise PrepareError(f"capture artifact root does not exist: {artifact_root}")
    try:
        artifact_root.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise PrepareError("capture artifacts must stay outside the repository")

    report_path = artifact_root / "report.json"
    timeline_path = artifact_root / "cell" / "promo" / "capture-timeline.json"
    index_path = artifact_root / "evidence-index.json"
    report = _read_object(report_path, "capture report")
    timeline = _read_object(timeline_path, "capture timeline")
    index = _read_object(index_path, "evidence index")
    cell = report.get("cell")
    if report.get("result") != "GREEN" or not isinstance(cell, dict) or cell.get("result") != "GREEN":
        raise PrepareError(
            f"capture report must be GREEN at root and cell; got "
            f"{report.get('result')!r}/{cell.get('result') if isinstance(cell, dict) else None!r}"
        )
    if index.get("result") != "GREEN":
        raise PrepareError(f"evidence index must be GREEN, got {index.get('result')!r}")
    indexed_root = index.get("artifact_root")
    if not isinstance(indexed_root, str) or Path(indexed_root).resolve() != artifact_root:
        raise PrepareError("evidence index artifact_root does not match the requested run")
    if timeline.get("exclude_ck3_loading") is not True:
        raise PrepareError("capture timeline does not attest exclusion of CK3 loading")
    source_kind = timeline.get("source_kind")
    if not isinstance(source_kind, str) or "real CK3" not in source_kind:
        raise PrepareError("capture timeline is not classified as real CK3 capture")

    indexed = _indexed_files(index)
    _verify_indexed_file(artifact_root, indexed, "report.json")
    _verify_indexed_file(
        artifact_root, indexed, "cell/promo/capture-timeline.json"
    )
    raw_value = timeline.get("raw_path")
    if not isinstance(raw_value, str) or not Path(raw_value).is_absolute():
        raise PrepareError("capture timeline raw_path must be absolute")
    raw_path = Path(raw_value).resolve()
    try:
        raw_relative = raw_path.relative_to(artifact_root).as_posix()
    except ValueError as exc:
        raise PrepareError("capture raw MKV must be contained by the artifact root") from exc
    _verify_indexed_file(artifact_root, indexed, raw_relative)
    raw_sha = _sha256(raw_path)
    if not isinstance(timeline.get("raw_sha256"), str) or timeline["raw_sha256"].upper() != raw_sha:
        raise PrepareError("capture timeline raw_sha256 does not match the MKV")
    if timeline.get("raw_bytes") != raw_path.stat().st_size:
        raise PrepareError("capture timeline raw_bytes does not match the MKV")

    marks = _mark_map(timeline)
    if marks["recording_started_after_gameplay_hud"] >= marks["calibration_event_visible"]:
        raise PrepareError("capture begins too late to contain the calibration excerpt")
    if marks["recording_stop_requested"] <= marks["policy_card_361_visible"]:
        raise PrepareError("capture stopped before the final requested policy still")

    reported_capture = cell.get("promo_capture")
    if not isinstance(reported_capture, dict):
        raise PrepareError("GREEN report does not bind promo_capture evidence")
    if (
        not isinstance(reported_capture.get("raw_sha256"), str)
        or reported_capture["raw_sha256"].upper() != raw_sha
        or reported_capture.get("marks") != timeline.get("marks")
        or reported_capture.get("exclude_ck3_loading") is not True
    ):
        raise PrepareError("GREEN report promo_capture does not match the timeline/MKV")

    scenario = cell.get("scenario_evidence")
    if not isinstance(scenario, dict):
        raise PrepareError("GREEN report lacks scenario_evidence")
    if not isinstance(scenario.get("promo_received_scoreboard"), dict):
        raise PrepareError("GREEN report lacks the received-scoreboard promo evidence")
    policy_rows = scenario.get("promo_policy_cards")
    if not isinstance(policy_rows, list):
        raise PrepareError("GREEN report lacks promo_policy_cards")
    reported_policy_ids = [
        row.get("mechanism_id") for row in policy_rows if isinstance(row, dict)
    ]
    if reported_policy_ids != list(POLICY_IDS):
        raise PrepareError(
            f"GREEN report policy cards are {reported_policy_ids!r}; "
            f"expected {list(POLICY_IDS)!r}"
        )

    policy_paths: dict[int, Path] = {}
    for mechanism_id in POLICY_IDS:
        relative = f"cell/12_policy_{mechanism_id:03d}_event.png"
        policy_paths[mechanism_id] = _verify_indexed_file(
            artifact_root, indexed, relative
        )
    superior_result = _verify_indexed_file(
        artifact_root, indexed, "cell/10_superior_result.png"
    )
    return {
        "artifact_root": artifact_root,
        "report_path": report_path.resolve(),
        "timeline_path": timeline_path.resolve(),
        "index_path": index_path.resolve(),
        "report": report,
        "timeline": timeline,
        "index": index,
        "raw_path": raw_path,
        "marks": marks,
        "policy_paths": policy_paths,
        "superior_result_path": superior_result,
    }


def _clear_visual(chapter: dict[str, Any]) -> None:
    for key in (
        "source",
        "evidence_sources",
        "start_seconds",
        "end_seconds",
        "clip_duration_seconds",
        "fit",
        "capture",
    ):
        chapter.pop(key, None)


def _common_evidence(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        _file_record(bundle["index_path"], "Append-only evidence index"),
    ]


def _set_boundary(
    chapter: dict[str, Any],
    bundle: dict[str, Any],
    *,
    zh_status: str,
    en_status: str,
    body_zh: list[str],
    body_en: list[str],
) -> None:
    _clear_visual(chapter)
    chapter["type"] = "title_card"
    chapter["material_status"] = "generated"
    chapter["status"] = {
        "zh": zh_status,
        "en": en_status,
        "classification": "generated-evidence-boundary",
    }
    chapter["body_zh"] = body_zh
    chapter["body_en"] = body_en
    chapter["evidence_sources"] = _common_evidence(bundle)


def _set_still(
    chapter: dict[str, Any],
    bundle: dict[str, Any],
    *,
    path: Path,
    capture_id: str,
    label: str,
    zh_status: str,
    en_status: str,
    shot: str,
    classification: str = "fixture-live-policy-still",
) -> None:
    _clear_visual(chapter)
    chapter["type"] = "still"
    chapter["material_status"] = "captured"
    chapter["status"] = {
        "zh": zh_status,
        "en": en_status,
        "classification": classification,
    }
    chapter["source"] = _file_record(path, label)
    chapter["evidence_sources"] = _common_evidence(bundle)
    chapter["capture"] = {
        "id": capture_id,
        "exclude_ck3_loading": True,
        "shot": shot,
    }


def _clip_window(
    bundle: dict[str, Any],
    start_label: str,
    end_label: str,
    *,
    before: float,
    after: float,
) -> tuple[float, float]:
    marks = bundle["marks"]
    floor = marks["recording_started_after_gameplay_hud"]
    ceiling = marks["recording_stop_requested"] - 0.10
    start = max(floor, marks[start_label] - before)
    end = min(ceiling, marks[end_label] + after)
    if end <= start + 0.50:
        raise PrepareError(
            f"invalid clip window {start_label}..{end_label}: {start:.3f}..{end:.3f}"
        )
    return round(start, 3), round(end, 3)


def _set_video(
    chapter: dict[str, Any],
    bundle: dict[str, Any],
    *,
    capture_id: str,
    label: str,
    zh_status: str,
    en_status: str,
    shot: str,
    start_label: str,
    end_label: str,
    before: float = 1.25,
    after: float = 4.50,
) -> None:
    _clear_visual(chapter)
    start, end = _clip_window(
        bundle,
        start_label,
        end_label,
        before=before,
        after=after,
    )
    chapter["type"] = "video_clip"
    chapter["material_status"] = "captured"
    chapter["status"] = {
        "zh": zh_status,
        "en": en_status,
        "classification": "fixture-live-continuous",
    }
    chapter["source"] = _file_record(
        bundle["raw_path"], "GREEN real-CK3 raw MKV; loading excluded"
    )
    chapter["evidence_sources"] = _common_evidence(bundle)
    chapter["start_seconds"] = start
    chapter["end_seconds"] = end
    chapter["capture"] = {
        "id": capture_id,
        "exclude_ck3_loading": True,
        "shot": shot,
        "timeline_start_mark": start_label,
        "timeline_end_mark": end_label,
    }


def project_manifest(
    *, artifact_root: Path, base_manifest: Path = DEFAULT_BASE_MANIFEST
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = _capture_bundle(artifact_root)
    base_manifest = base_manifest.expanduser().resolve()
    base = _read_object(base_manifest, "base promo manifest")
    # Run the normal loader first so this projection never hides a broken
    # narration/topic/subtitle contract in the checked-in authoring manifest.
    promo.load_manifest(base_manifest)
    payload = copy.deepcopy(base)
    chapters = payload.get("chapters")
    if not isinstance(chapters, list):
        raise PrepareError("base manifest chapters must be an array")
    by_id = {
        chapter.get("id"): chapter
        for chapter in chapters
        if isinstance(chapter, dict) and isinstance(chapter.get("id"), str)
    }
    expected_ids = {
        "00-cold-open",
        "01-who-rates-whom",
        "02-okr-kpi",
        "03-forced-distribution",
        "04-calibration",
        "05-peer-review-politics",
        "06-jingcha",
        "07-scoreboard-receipt",
        "08-money-and-grade",
        "09-pip-bottom",
        "10-promotion-hc",
        "11-credit-and-dependencies",
        "12-appeal",
        "13-361-policy-cards",
        "14-core-loop",
        "15-honest-boundary",
        "16-finale",
    }
    if set(by_id) != expected_ids:
        raise PrepareError("base promo chapter set changed; review the release projection")

    payload["project_status"] = "captured_release_candidate"
    payload["release_manifest_provenance"] = {
        "schema_version": 1,
        "generator": "mod_zhongguo_style/tools/prepare_promo_release_manifest.py",
        "capture_artifact_root": str(bundle["artifact_root"]),
        "capture_result": "GREEN",
        "base_manifest": _file_record(base_manifest, "Checked-in promo authoring manifest"),
        "capture_report": _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        "capture_timeline": _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        "evidence_index": _file_record(bundle["index_path"], "Append-only evidence index"),
        "raw_capture": _file_record(bundle["raw_path"], "Preserved real-CK3 raw MKV"),
        "policy_card_ids": list(POLICY_IDS),
        "generated_boundary_chapters": [
            "01-who-rates-whom",
            "09-pip-bottom",
            "15-honest-boundary",
        ],
        "loading_exclusion": "raw recording began after gameplay HUD; every clip starts at or after that timeline mark",
    }

    opening = by_id["00-cold-open"]
    opening["status"] = {
        "zh": "正式候选开场卡",
        "en": "CAPTURED RELEASE CANDIDATE · OPENING",
        "classification": "captured-release-generated",
    }

    _set_boundary(
        by_id["01-who-rates-whom"],
        bundle,
        zh_status="生成证据边界卡：层级未单独录屏",
        en_status="GENERATED EVIDENCE/BOUNDARY · HIERARCHY NOT SEPARATELY RECORDED",
        body_zh=["实机报告确认公爵及以上入口", "伯爵、男爵边界不伪装成独立实录"],
        body_en=["GREEN report binds the duke-or-higher entry", "Count/baron boundary is not presented as a separate live shot"],
    )
    _set_still(
        by_id["02-okr-kpi"],
        bundle,
        path=bundle["policy_paths"][1],
        capture_id="CAP-RELEASE-POLICY-001",
        label="GREEN fixture-live policy card #001",
        zh_status="实机政策卡 #001：不冒充独立 OKR 面板",
        en_status="FIXTURE-LIVE POLICY #001 · NO STANDALONE OKR UI CLAIM",
        shot="同一 GREEN run 的 #001 KPI 分项证据单；只展示真实 A/B/C 政策卡。",
    )
    _set_video(
        by_id["03-forced-distribution"],
        bundle,
        capture_id="CAP-RELEASE-MANAGED-SCOREBOARD",
        label="GREEN continuous scoreboard and cockpit excerpt",
        zh_status="连续实机：新人保护榜与制度驾驶舱",
        en_status="FIXTURE-LIVE CONTINUOUS · NEWCOMER BOARD AND COCKPIT",
        shot="从同一原始 MKV 的考核榜时间标记开始；7/16/0 明示为新人保护样本。",
        start_label="managed_scoreboard_visible",
        end_label="policy_cockpit_visible",
    )
    _set_video(
        by_id["04-calibration"],
        bundle,
        capture_id="CAP-RELEASE-CALIBRATION",
        label="GREEN continuous calibration excerpt",
        zh_status="连续实机：真实校准会三选项",
        en_status="FIXTURE-LIVE CONTINUOUS · THREE REAL CALIBRATION CHOICES",
        shot="同一 GREEN run 的校准会连续片段；不声称存在命名档案或任意点名器。",
        start_label="calibration_event_visible",
        end_label="calibration_event_visible",
    )
    _set_still(
        by_id["05-peer-review-politics"],
        bundle,
        path=bundle["policy_paths"][7],
        capture_id="CAP-RELEASE-POLICY-007",
        label="GREEN fixture-live policy card #007",
        zh_status="实机政策卡 #007：同侪互动未单独录屏",
        en_status="FIXTURE-LIVE POLICY #007 · PEER INTERACTION NOT SEPARATELY RECORDED",
        shot="同一 GREEN run 的 #007 背靠背 360 邀评政策卡；不冒充举荐/攻讦互动录像。",
        classification="fixture-live-policy-still-boundary",
    )
    _set_video(
        by_id["06-jingcha"],
        bundle,
        capture_id="CAP-RELEASE-JINGCHA",
        label="GREEN continuous Jingcha mandate and free planner excerpt",
        zh_status="连续实机：京察弹窗与免费规划器",
        en_status="FIXTURE-LIVE CONTINUOUS · JINGCHA MANDATE AND FREE PLANNER",
        shot="同一 GREEN run 连续展示半强制京察弹窗与免费举办规划器。",
        start_label="jingcha_mandate_visible",
        end_label="free_jingcha_planner_visible",
    )
    _set_video(
        by_id["07-scoreboard-receipt"],
        bundle,
        capture_id="CAP-RELEASE-RECEIVED-SCOREBOARD",
        label="GREEN continuous received-scoreboard excerpt",
        zh_status="连续实机：本人所属考核单元与 3.25",
        en_status="FIXTURE-LIVE CONTINUOUS · RECEIVED BOARD WITH 3.25",
        shot="同一 GREEN run 的本人所属考核单元；管理者榜已在前章展示。",
        start_label="received_scoreboard_with_325_visible",
        end_label="received_scoreboard_with_325_visible",
    )
    _set_video(
        by_id["08-money-and-grade"],
        bundle,
        capture_id="CAP-RELEASE-SUPERIOR-325",
        label="GREEN continuous superior-assigned 3.25 excerpt",
        zh_status="连续实机：上司 3.25 告身与国库/金币/贤能/俸禄四重处分",
        en_status="FIXTURE-LIVE CONTINUOUS · SUPERIOR 3.25 AND FOURFOLD CONSEQUENCE",
        shot="同一 GREEN run 的上司 3.25 告身；正式重录画面使用四重精确文案，报告绑定罚没与退款断言。",
        start_label="superior_assigned_325_visible",
        end_label="received_scoreboard_with_325_visible",
        after=-1.0,
    )
    _set_boundary(
        by_id["09-pip-bottom"],
        bundle,
        zh_status="生成证据边界卡：PIP/末位未独立录屏",
        en_status="GENERATED EVIDENCE/BOUNDARY · PIP/BOTTOM NOT SEPARATELY RECORDED",
        body_zh=["3.25 告身已实录", "一年 PIP 与连续末位规则不伪装成现场镜头"],
        body_en=["The 3.25 receipt is captured", "One-year PIP and repeat-bottom rules are not impersonated as live footage"],
    )

    promotion_hc = by_id["10-promotion-hc"]
    original_cues = promotion_hc.get("cues")
    if not isinstance(original_cues, list) or len(original_cues) != 2:
        raise PrepareError("10-promotion-hc must retain exactly two authoring cues")
    hc_chapter = copy.deepcopy(promotion_hc)
    promotion_hc["cues"] = [copy.deepcopy(original_cues[0])]
    promotion_hc["topics"] = ["promotion_packet"]
    _set_still(
        promotion_hc,
        bundle,
        path=bundle["policy_paths"][20],
        capture_id="CAP-RELEASE-POLICY-020",
        label="GREEN fixture-live policy card #020",
        zh_status="实机政策卡 #020：晋升通道未单独录屏",
        en_status="FIXTURE-LIVE POLICY #020 · PROMOTION TRACK NOT SEPARATELY RECORDED",
        shot="同一 GREEN run 的 #020 晋升包与跨部门答辩政策卡。",
        classification="fixture-live-policy-still-boundary",
    )
    hc_chapter["id"] = "10b-hc-policy-022"
    hc_chapter["title_zh"] = "HC：编制不是许愿池，是压力账"
    hc_chapter["title_en"] = "HEADCOUNT: NOT A WISH ENGINE, A PRESSURE LEDGER"
    hc_chapter["cues"] = [copy.deepcopy(original_cues[1])]
    hc_chapter["topics"] = ["hc"]
    _set_still(
        hc_chapter,
        bundle,
        path=bundle["policy_paths"][22],
        capture_id="CAP-RELEASE-POLICY-022",
        label="GREEN fixture-live policy card #022",
        zh_status="实机政策卡 #022：不冒充招聘模拟器",
        en_status="FIXTURE-LIVE POLICY #022 · NO STANDALONE HIRING SIM CLAIM",
        shot="同一 GREEN run 的 #022 软 HC / 编制预算政策卡。",
    )
    promotion_index = chapters.index(promotion_hc)
    chapters.insert(promotion_index + 1, hc_chapter)

    _set_still(
        by_id["11-credit-and-dependencies"],
        bundle,
        path=bundle["policy_paths"][26],
        capture_id="CAP-RELEASE-POLICY-026",
        label="GREEN fixture-live policy card #026",
        zh_status="实机政策卡 #026：不冒充项目仲裁器",
        en_status="FIXTURE-LIVE POLICY #026 · NO PROJECT ARBITRATION UI CLAIM",
        shot="同一 GREEN run 的 #026 真实贡献 / 上司可见度双账政策卡。",
        classification="fixture-live-policy-still-boundary",
    )
    _set_still(
        by_id["12-appeal"],
        bundle,
        path=bundle["superior_result_path"],
        capture_id="CAP-RELEASE-APPEAL-ENTRY",
        label="GREEN fixture-live 3.25 receipt with appeal entry",
        zh_status="实机告身：申诉入口；退款由同 run 报告绑定",
        en_status="FIXTURE-LIVE RECEIPT · REFUND BOUND BY SAME-RUN REPORT",
        shot="同一 GREEN run 的 3.25 告身与申诉入口；不把报告断言伪装成连续退款录像。",
        classification="fixture-live-still-partial",
    )
    _set_still(
        by_id["13-361-policy-cards"],
        bundle,
        path=bundle["policy_paths"][361],
        capture_id="CAP-RELEASE-POLICY-361",
        label="GREEN fixture-live policy card #361",
        zh_status="实机政策卡 #361：六张样卡均绑定同一 run",
        en_status="FIXTURE-LIVE POLICY #361 · SIX CAPTURED CARDS, ONE GREEN RUN",
        shot="同一 GREEN run 的 #361 绩效宪章；其余样卡分别出现在 #001/#007/#020/#022/#026 章节。",
    )
    _set_video(
        by_id["14-core-loop"],
        bundle,
        capture_id="CAP-RELEASE-SAME-RUN-CORE",
        label="GREEN same-run core-loop excerpt",
        zh_status="连续实机节选：京察到 3.25；全链由同 run 报告绑定",
        en_status="FIXTURE-LIVE EXCERPT · JINGCHA TO 3.25, SAME-RUN REPORT BINDS LOOP",
        shot="同一原始 MKV 从京察弹窗连续到本人 3.25；校准与发榜来自同 run 的更早时间标记。",
        start_label="jingcha_mandate_visible",
        end_label="received_scoreboard_with_325_visible",
    )

    boundary = by_id["15-honest-boundary"]
    boundary["status"] = {
        "zh": "正式候选证据边界",
        "en": "RELEASE-CANDIDATE EVIDENCE BOUNDARY",
        "classification": "generated-evidence-boundary",
    }
    boundary["body_zh"] = [
        "零占位不等于每项都有独立实录",
        "未单拍章节明确显示 GENERATED EVIDENCE/BOUNDARY",
        "连续实机与六张政策卡绑定同一 GREEN run",
    ]
    boundary["body_en"] = [
        "Zero placeholders does not mean every claim has a separate live shot",
        "Unrecorded chapters are explicit GENERATED EVIDENCE/BOUNDARY cards",
        "Continuous gameplay and six policy cards bind to one GREEN run",
    ]
    # The draft wording says this is a placeholder animatic.  Keep its joke and
    # bilingual cadence while making the release candidate factually correct.
    boundary["cues"][0] = {
        "zh": "这是可调整的脚本和证据分镜。没单独实录的就明确写边界卡，漂亮卡片不冒充 CK3 现场。",
        "en": "This remains an editable evidence cut. Anything not separately recorded is an explicit boundary card; a polished card never impersonates live CK3.",
    }
    boundary["evidence_sources"] = _common_evidence(bundle)

    finale = by_id["16-finale"]
    finale["status"] = {
        "zh": "正式候选结尾卡",
        "en": "CAPTURED RELEASE CANDIDATE · FINALE",
        "classification": "captured-release-generated",
    }

    # Every concrete source in the external manifest is absolute and immutable.
    # The normal loader verifies each declared byte count and SHA before output.
    provenance = {
        "schema_version": 1,
        "kind": "zg361_promo_release_manifest_projection",
        "generator": str(Path(__file__).resolve()),
        "base_manifest": _file_record(base_manifest, "Checked-in promo authoring manifest"),
        "capture_artifact_root": str(bundle["artifact_root"]),
        "capture_result": "GREEN",
        "capture_report": _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        "capture_timeline": _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        "evidence_index": _file_record(bundle["index_path"], "Append-only evidence index"),
        "raw_capture": _file_record(bundle["raw_path"], "Preserved real-CK3 raw MKV"),
        "policy_stills": {
            f"{mechanism_id:03d}": _file_record(
                bundle["policy_paths"][mechanism_id],
                f"GREEN policy card #{mechanism_id:03d}",
            )
            for mechanism_id in POLICY_IDS
        },
        "policy_card_ids": list(POLICY_IDS),
        "generated_boundary_chapters": [
            "01-who-rates-whom",
            "09-pip-bottom",
            "15-honest-boundary",
        ],
        "source_files_modified": False,
    }
    return payload, provenance


def _serialized(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_projection(
    *,
    artifact_root: Path,
    output: Path,
    base_manifest: Path = DEFAULT_BASE_MANIFEST,
) -> tuple[Path, Path]:
    output = output.expanduser().resolve()
    try:
        output.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise PrepareError("release manifest output must be outside the repository")
    provenance_path = output.with_name(f"{output.stem}.provenance.json")
    if output.exists() or provenance_path.exists():
        existing = output if output.exists() else provenance_path
        raise PrepareError(f"refusing to overwrite preserved promo output: {existing}")

    payload, provenance = project_manifest(
        artifact_root=artifact_root, base_manifest=base_manifest
    )
    manifest_bytes = _serialized(payload)
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest().upper()
    provenance["output_manifest"] = {
        "path": str(output),
        "bytes": len(manifest_bytes),
        "sha256": manifest_sha,
    }

    # Exercise the real manifest loader, including declared source hashes,
    # before committing append-only output names.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zg361-promo-manifest-check-") as temporary:
        check_path = Path(temporary) / "captured-release-manifest.json"
        check_path.write_bytes(manifest_bytes)
        checked, _chapters = promo.load_manifest(check_path)
        if checked.get("project_status") != "captured_release_candidate":
            raise PrepareError("projected manifest lost release-candidate status")
        if checked.get("_placeholder_count") != 0:
            raise PrepareError("projected manifest still contains placeholders")

    with output.open("xb") as handle:
        handle.write(manifest_bytes)
    with provenance_path.open("xb") as handle:
        handle.write(_serialized(provenance))
    return output, provenance_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--artifact-root", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument(
        "--base-manifest", type=Path, default=DEFAULT_BASE_MANIFEST
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        output, provenance = write_projection(
            artifact_root=arguments.artifact_root,
            output=arguments.output,
            base_manifest=arguments.base_manifest,
        )
    except (PrepareError, promo.PromoError) as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    print(f"GREEN: captured release manifest: {output}")
    print(f"GREEN: immutable projection provenance: {provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
