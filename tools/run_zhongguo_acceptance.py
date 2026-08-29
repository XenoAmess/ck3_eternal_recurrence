#!/usr/bin/env python3
"""Run isolated CK3 1.19.0.6 live acceptance for ZhongGuo 361 Style."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
import unicodedata
import uuid
from pathlib import Path

import run_acceptance as acceptance
import build_mod_zhongguo_style_release as release
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_zhongguo_style"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
PROMO_TOOLS_DIRECTORY = SOURCE / "tools"
if str(PROMO_TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(PROMO_TOOLS_DIRECTORY))

import promo_real_character_contract as real_characters

# CK3 writes into its -userdir. Keep both the evidence bundle and complete
# writable profile durable but outside the repository/protected real profile.
RUNS_ROOT = ROOT.parent / f"{ROOT.name}_process_assets" / "zg361" / "runs"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
EXPECTED_PLAYER_HISTORY_ID = real_characters.MANAGER_HISTORY_ID
EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS = tuple(
    real_characters.REVIEWED_OFFICIAL_CONTRACT
)
EXPECTED_HISTORICAL_COHORT_HISTORY_IDS = tuple(
    real_characters.HISTORICAL_COHORT_CONTRACT
)
HISTORICAL_TARGET_DATA_MARKER_PREFIX = real_characters.TARGET_DATA_MARKER_PREFIX
HISTORICAL_TARGET_PASS_MARKER = real_characters.TARGET_PASS_MARKER
PROMO_CLEAN_SPANS = (
    "calibration",
    "managed_scoreboard",
    "policy_cockpit",
    "jingcha_mandate",
    "free_jingcha_planner",
    "superior_assigned_325",
    "received_scoreboard_with_325",
    "policy_card_001",
    "policy_card_007",
    "policy_card_020",
    "policy_card_022",
    "policy_card_026",
    "policy_card_361",
)
PROMO_FORBIDDEN_VISIBLE_TEXT = (
    "决议和大型工程",
    "361制实机验收",
    "开始361制实机验收",
    "验收上司给我的绩效",
    "验收免费京察规划器",
    "演示政策卡",
    "演示触发器",
    "切换至宋帝并开考",
    "切换受考",
    "发出京察召集令",
    "打开此卡",
    "ZhongGuo 361 live acceptance",
    "Verify My Superior's Rating",
    "Verify the Free Jingcha Planner",
    "Promo Policy Card",
    "Switch to Song and begin review",
    "Open this card",
    "ZGA",
    "zga_",
    "zga.",
)
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_S = 300
PRODUCT_OUTER = "zg361_acceptance.mod"
FIXTURE_OUTER = "zga_acceptance_fixture.mod"
PROJECT_TOKENS = ("zg361", "zga_acceptance", "zga_", "zga.")
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
REQUIRED_FIXTURE_MARKERS = (
    "ZGA: TEST BEGIN zg361",
    "ZGA: TEST PASS exact_build_song_emperor",
    "ZGA: TEST PASS song_independent_sample",
    "ZGA: TEST PASS song_direct_governors_at_least_three",
    "ZGA: TEST PASS non_independent_celestial_liege_entry",
    "ZGA: TEST PASS switched_to_song_emperor",
    "ZGA: TEST PASS player_song_review_entry",
    "ZGA: TEST PASS newcomer_snapshot_prepared_by_product",
    "ZGA: TEST PASS newcomer_first_review_protected",
    "ZGA: TEST PASS player_calibration_pending",
    "ZGA: TEST PASS calibration_c_all_newcomer_noop",
    "ZGA: TEST PASS calibration_c_mixed_newcomer_atomic_swap",
    "ZGA: TEST PASS pending_review_idempotent",
    "ZGA: TEST PASS grade_325_fourfold_penalty",
    "ZGA: TEST PASS appeal_exact_fixed_refund_and_salary_stop",
    "ZGA: TEST PASS appeal_refund_idempotent",
    "ZGA: MECHANISM BATCH BEGIN 361",
    "ZGA: MECHANISM LEDGER PASS",
    "ZGA: MECHANISM IDEMPOTENCE PASS",
    "ZGA: MECHANISM BATCH DONE 361",
    "ZGA: TEST PASS scoreboard_header_and_rows",
    "ZGA: TEST PASS three_grade_counts",
    "ZGA: TEST PASS newcomer_first_review_result_without_325",
    "ZGA: TEST DONE zg361",
    "ZGA: TEST PASS historical_song_direct_whitelist_complete",
    "ZGA: TEST PASS generated_city_officials_excluded_from_provenance",
)
REQUIRED_LATE_FIXTURE_MARKERS = (
    "ZGA: TEST PASS personal_result_target_selected_from_prior_historical_assessor_tail",
    "ZGA: TEST PASS personal_result_target_can_assess_others",
    HISTORICAL_TARGET_PASS_MARKER,
    "ZGA: TEST PASS personal_result_target_projected_bottom_two",
)
REQUIRED_PRODUCT_MARKERS = {
    "ZG361: annual review tick": 2,
    "ZG361: newcomer enters first review with 3.25 protection": 1,
    "ZG361: scoreboard published": 1,
    "ZG361M: REFERENCE CHARTER COMPLETE 361": 2,
}
SOURCE_ONLY_RUNTIME_ROOTS = {
    "artifacts",
    "docs",
    "fixtures",
    "images",
    "promo",
    "tools",
    "workshop",
}
PROMO_POLICY_CARDS = (
    (1, "演示政策卡 #001", "KPI 分项证据单", "建立分项证据单"),
    (7, "演示政策卡 #007", "背靠背 360 邀评", "只邀请有真实协作"),
    (20, "演示政策卡 #020", "晋升包与跨部门答辩", "用冻结治理成果"),
    (22, "演示政策卡 #022", "软 HC / 编制预算", "按团队成果"),
    (26, "演示政策卡 #026", "真实贡献 / 上司可见度双账", "分别冻结真实贡献"),
    (361, "演示政策卡 #361", "三六一绩效宪章", "锁定证据公平"),
)
PROMO_INTERRUPTION_MAX_DISMISSALS = 3
PROMO_INTERRUPTION_DEFAULT_OBSERVE_S = 1.0
PROMO_PREFERRED_PRODUCT_EVENT_OPTIONS = (
    # The punitive alternative forces every "little white rabbit" to step
    # down, mutating the real 23-person cohort before historical target
    # selection.  The retention option closes the ordinary product event
    # without manufacturing or removing a promo subject.
    ("野狗与小白兔", "宽严相济"),
)
# CK3 character-event titles occupy this left-half lane.  The bottom-right
# pause reason may repeat the title of an event hidden behind another modal;
# it must never satisfy a "target event is visibly on top" assertion.
PROMO_EVENT_TITLE_REGION = (0.18, 0.16, 0.48, 0.32)
# The generated 180x44 toggle is anchored immediately left of CK3's 50-unit
# right HUD rail.  Constrain positive OCR to this normalized lane so the old
# detached {-205,165} placement cannot accidentally satisfy live acceptance.
SCOREBOARD_BUTTON_REGION = (0.86, 0.05, 0.985, 0.16)
DECISIONS_HEADER_REGION = (0.55, 0.00, 0.90, 0.13)
# CK3 acceptance is pinned to 2560x1440 and the isolated profile's UI scale.
# This normalized point is the native Decisions drawer's title-bar X.  The
# drawer is flush with the right HUD rail, so its close glyph sits near the
# screen's right edge (2460, 92 in the pinned 2560x1440 acceptance profile).
DECISIONS_CLOSE_BUTTON = (0.961, 0.064)
# The generated 1220x820 modal is centered.  Its inherited header close glyph
# is centered at (1991, 240) in the same pinned acceptance profile.  The
# backdrop probe deliberately stays far outside the panel's left edge.
SCOREBOARD_TITLE_CLOSE_BUTTON = (0.778, 0.167)
SCOREBOARD_BACKDROP_POINT = (0.050, 0.500)
SCOREBOARD_ROW_NAME_REGION = (0.30, 0.33, 0.45, 0.76)
CHARACTER_WINDOW_NAME_REGION = (0.00, 0.05, 0.38, 0.80)
# CK3's native character sidebar is 610 GUI units wide and the isolated
# profile uses 1.30 GUI scale.  Pixel inspection of the unscaled 2560x1440
# evidence frame places its inherited 30x30 close glyph at (740, 26).
# Escape does not close this sidebar reliably, so the row-link audit uses the
# product-native title-bar control directly.
CHARACTER_WINDOW_CLOSE_BUTTON = (0.2891, 0.0181)
SCOREBOARD_GENERATED_ROW_LINKS = 160
JINGCHA_PERSONAL_SWITCH_DELAY_DAYS = 2
PERSONAL_SWITCH_SCHEDULED_MARKER = (
    "ZGA: TEST PASS personal_result_switch_scheduled"
)


def log(message: str) -> None:
    acceptance.log(f"zg361: {message}")


class PromoRecorder:
    """Append-only desktop recorder started only after CK3 gameplay is visible."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.raw_dir = artifact_dir / "raw"
        self.raw_path = self.raw_dir / "zg361-promo-live-full-take-01.mkv"
        self.log_path = self.raw_dir / "ffmpeg-take-01.log"
        self.timeline_path = artifact_dir / "capture-timeline.json"
        self.process: subprocess.Popen[bytes] | None = None
        self.log_handle = None
        self.started_monotonic: float | None = None
        self.started_at_utc: str | None = None
        self.marks: list[dict[str, object]] = []
        self.clean_frame_gates: dict[str, dict[str, object]] = {}
        self.reviewed_official_history_id: str | None = None
        self.real_character_provenance: dict[str, object] | None = None

    def resolve_reviewed_subject(self, history_id: str) -> None:
        """Freeze the one runtime-selected historical subject for this take."""

        if (
            self.reviewed_official_history_id is not None
            and self.reviewed_official_history_id != history_id
        ):
            raise acceptance.RunnerError(
                "promo recorder received conflicting reviewed subjects: "
                f"{self.reviewed_official_history_id} and {history_id}"
            )
        self.real_character_provenance = promo_real_character_provenance(history_id)
        self.reviewed_official_history_id = history_id

    def start(self) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise acceptance.RunnerError("ffmpeg is required for --promo-capture")
        self.raw_dir.mkdir(parents=True)
        if self.raw_path.exists() or self.log_path.exists() or self.timeline_path.exists():
            raise acceptance.RunnerError(
                f"promo capture output already exists: {self.artifact_dir}"
            )
        self.log_handle = self.log_path.open("wb")
        command = [
            ffmpeg,
            "-hide_banner",
            "-f",
            "gdigrab",
            "-framerate",
            "30",
            "-draw_mouse",
            "1",
            "-i",
            "desktop",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(self.raw_path),
        ]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=self.log_handle,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.started_monotonic = time.monotonic()
        self.started_at_utc = datetime.now(timezone.utc).isoformat()
        time.sleep(1.5)
        if self.process.poll() is not None:
            raise acceptance.RunnerError(
                f"promo recorder exited during startup; inspect {self.log_path}"
            )
        self.mark("recording_started_after_gameplay_hud")

    def mark(self, label: str) -> None:
        if self.started_monotonic is None:
            return
        self.marks.append(
            {
                "label": label,
                "seconds": round(time.monotonic() - self.started_monotonic, 3),
            }
        )

    def hold(self, seconds: float = 2.5) -> None:
        if self.process is not None:
            time.sleep(seconds)

    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None:
        """Record one exact promo-safe span with full-screen begin/end proof."""

        if self.process is None:
            return
        if label not in PROMO_CLEAN_SPANS:
            raise acceptance.RunnerError(f"unknown promo clean span: {label}")
        if label in self.clean_frame_gates:
            raise acceptance.RunnerError(f"duplicate promo clean span: {label}")
        begin_mark = f"{label}_clean_begin"
        end_mark = f"{label}_clean_end"
        begin = assert_promo_frame_clean(
            artifacts, f"promo_clean_{label}_begin", label=label, phase="begin"
        )
        self.mark(begin_mark)
        self.hold(seconds)
        end = assert_promo_frame_clean(
            artifacts, f"promo_clean_{label}_end", label=label, phase="end"
        )
        self.mark(end_mark)
        self.clean_frame_gates[label] = {
            "span_id": label,
            "result": "GREEN",
            "begin_mark": begin_mark,
            "end_mark": end_mark,
            "full_screen": True,
            "fixture_test_ui_absent": True,
            "native_decisions_drawer_absent": True,
            "frames": [begin, end],
        }

    def stop(self) -> dict[str, object]:
        if self.process is None:
            return {}
        self.mark("recording_stop_requested")
        if self.process.stdin:
            try:
                self.process.stdin.write(b"q\n")
                self.process.stdin.flush()
            except OSError:
                pass
        try:
            returncode = self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            returncode = self.process.wait(timeout=10)
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None
        if returncode != 0 or not self.raw_path.is_file() or self.raw_path.stat().st_size == 0:
            raise acceptance.RunnerError(
                f"promo recorder failed with exit {returncode}; inspect {self.log_path}"
            )
        missing_clean_spans = [
            label for label in PROMO_CLEAN_SPANS if label not in self.clean_frame_gates
        ]
        payload = {
            "schema": 2,
            "started_at_utc": self.started_at_utc,
            "exclude_ck3_loading": True,
            "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
            "raw_path": str(self.raw_path),
            "raw_bytes": self.raw_path.stat().st_size,
            "raw_sha256": isolated.sha256_file(self.raw_path),
            "ffmpeg_log": str(self.log_path),
            "marks": self.marks,
            "clean_frame_gates": [
                self.clean_frame_gates[label] for label in PROMO_CLEAN_SPANS
                if label in self.clean_frame_gates
            ],
            "clean_capture_complete": not missing_clean_spans,
            "missing_clean_spans": missing_clean_spans,
            "real_character_provenance": self.real_character_provenance,
        }
        write_json(self.timeline_path, payload)
        self.process = None
        if missing_clean_spans:
            raise acceptance.RunnerError(
                "promo capture is missing clean spans: " + ", ".join(missing_clean_spans)
            )
        if self.real_character_provenance is None:
            raise acceptance.RunnerError(
                "promo capture completed without resolving its historical reviewed subject"
            )
        return payload


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _paradox_top_level_block(text: str, key: str) -> str:
    """Return one exact top-level Paradox block for provenance checks."""

    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{", text)
    if match is None:
        raise acceptance.RunnerError(f"vanilla history block is missing: {key}")
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
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
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise acceptance.RunnerError(f"vanilla history block is unterminated: {key}")


def fixture_constructor_counts() -> dict[str, int]:
    """Derive, rather than assert, fixture construction-command counts."""

    fixture_files = (
        tuple(FIXTURE_SOURCE.rglob("*.txt"))
        + tuple(FIXTURE_SOURCE.rglob("*.gui"))
        + tuple(FIXTURE_SOURCE.rglob("*.yml"))
    )
    text = "\n".join(path.read_text(encoding="utf-8-sig") for path in fixture_files)
    return {
        token: len(re.findall(rf"\b{re.escape(token)}\b", text))
        for token in (
            "create_character",
            "create_title",
            "grant_title",
            "set_father",
            "set_mother",
            "set_spouse",
            "add_relation",
            "set_relation",
        )
    }


def promo_real_character_provenance(
    reviewed_history_id: str,
) -> dict[str, object]:
    """Bind a take to Zhao Shu and one resolved, hard-allowed real official."""

    history_path = ROOT / "Crusader Kings III" / "game" / "history" / "characters" / "han.txt"
    title_history_path = (
        ROOT / "Crusader Kings III" / "game" / "history" / "titles" / "e_china.txt"
    )
    history_text = history_path.read_text(encoding="utf-8-sig")
    title_history_text = title_history_path.read_text(encoding="utf-8-sig")
    try:
        manager = real_characters.manager()
        reviewed = real_characters.reviewed_official(reviewed_history_id)
    except ValueError as exc:
        raise acceptance.RunnerError(str(exc)) from exc
    manager.update(
        {
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "expected_runtime_contract": {
                "is_player": True,
                "is_ai": False,
                "has_h_china": True,
                "independent": True,
            },
        }
    )
    reviewed.update(
        {
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "historical_title": reviewed["title_id"],
            "historical_liege_title": reviewed["liege_title_id"],
            "selection": "runtime_lowest_ranked_historical_duke_plus_from_hard_allowlist",
            "expected_runtime_contract": {
                "pre_switch_ai": True,
                "post_switch_player": True,
                "direct_liege_runtime": True,
                "current_review_record_runtime": True,
                "lowest_prior_rank_within_historical_duke_plus_allowlist": True,
            },
        }
    )
    records = []
    for subject in (manager, reviewed):
        history_id = str(subject["history_id"])
        _paradox_top_level_block(history_text, history_id)
        records.append(
            {
                **subject,
                "history_source": {
                    "path": str(history_path.resolve()),
                    "bytes": history_path.stat().st_size,
                    "sha256": isolated.sha256_file(history_path),
                },
            }
        )

    china_block = _paradox_top_level_block(title_history_text, "h_china")
    if re.search(
        r"1063\.4\.30\s*=\s*\{[^}]*holder\s*=\s*han_8052",
        china_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            "vanilla h_china history does not bind han_8052 at the 1066 start"
        )
    reviewed_title = str(reviewed["title_id"])
    reviewed_holder_date = str(reviewed["holder_date"])
    reviewed_liege_title = str(reviewed["liege_title_id"])
    reviewed_liege_holder_id = str(reviewed["liege_holder_id"])
    reviewed_liege_holder_date = str(reviewed["liege_holder_date"])
    reviewed_title_block = _paradox_top_level_block(
        title_history_text, reviewed_title
    )
    if re.search(
        rf"{re.escape(reviewed_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_history_id)}",
        reviewed_title_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_title} history does not bind "
            f"{reviewed_history_id} on {reviewed_holder_date}"
        )
    if re.search(
        rf"\bliege\s*=\s*{re.escape(reviewed_liege_title)}\b",
        reviewed_title_block,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_title} history does not bind its holder under "
            f"{reviewed_liege_title}"
        )
    reviewed_liege_block = _paradox_top_level_block(
        title_history_text, reviewed_liege_title
    )
    if re.search(
        rf"{re.escape(reviewed_liege_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_liege_holder_id)}",
        reviewed_liege_block,
        re.S,
    ) is None:
        raise acceptance.RunnerError(
            f"vanilla {reviewed_liege_title} history does not bind direct liege "
            f"holder {reviewed_liege_holder_id} on {reviewed_liege_holder_date}"
        )
    constructor_counts = fixture_constructor_counts()
    if any(constructor_counts.values()):
        raise acceptance.RunnerError(
            f"promo fixture manufactures historical subjects: {constructor_counts}"
        )
    return {
        "schema_version": 1,
        "bookmark": dict(real_characters.BOOKMARK),
        "subjects": records,
        "title_history_source": {
            "path": str(title_history_path.resolve()),
            "bytes": title_history_path.stat().st_size,
            "sha256": isolated.sha256_file(title_history_path),
        },
        "title_history_assertions": {
            "h_china_holder_at_start": "han_8052",
            "reviewed_official_title_at_start": reviewed_title,
            "reviewed_official_holder_at_start": reviewed_history_id,
            "reviewed_official_holder_date": reviewed_holder_date,
            "reviewed_official_title_liege_at_start": reviewed_liege_title,
            "reviewed_official_direct_liege_holder_at_start": reviewed_liege_holder_id,
            "reviewed_official_direct_liege_holder_date": reviewed_liege_holder_date,
        },
        "fixture_constructor_counts": constructor_counts,
        "fixture_state_kind": "fixture_preconditioned_real_characters",
        "performance_and_refusal_evidence_preconditioned": True,
        "test_decision_visibility_contract": {
            "initialization_decision_before_recording_only": True,
            "all_other_fixture_decisions_permanently_hidden": True,
        },
        "native_drawer_close_required_before_first_clean_span": True,
        "selection_contract": (
            "han_8052 is the historical Song emperor; the fixture selected exactly "
            f"{reviewed_history_id} as the lowest-prior-ranked eligible official "
            "inside the frozen 18-person historical duke+ allowlist; three "
            "historical counts are assessed-only, and two generated city officials "
            "in the 23-person runtime cohort are never eligible for promo identity"
        ),
    }


def _normalize_promo_visible_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum() or character == "_")


def _promo_decisions_header_hits(
    items: list[dict[str, object]], width: int, height: int
) -> tuple[list[str], str]:
    left, top, right, bottom = DECISIONS_HEADER_REGION
    header_text: list[str] = []
    for item in items:
        center = item.get("center")
        if (
            not isinstance(center, (list, tuple))
            or len(center) != 2
            or not all(isinstance(value, (int, float)) for value in center)
        ):
            continue
        x, y = float(center[0]), float(center[1])
        if left * width <= x <= right * width and top * height <= y <= bottom * height:
            header_text.append(str(item.get("text", "")))
    normalized = _normalize_promo_visible_text("".join(header_text))
    hits = [
        token
        for token in ("决议", "Decisions")
        if _normalize_promo_visible_text(token) in normalized
    ]
    return hits, normalized


def assert_promo_frame_clean(
    artifacts: Path, stem: str, *, label: str, phase: str
) -> dict[str, object]:
    """Save two consecutive full-screen proofs and reject fixture UI/drawer text."""

    width, height = acceptance.pyautogui.size()
    samples: list[dict[str, object]] = []
    for sample_index, sample_stem in enumerate(
        (stem, f"{stem}_drawer_confirmation"), start=1
    ):
        if sample_index > 1:
            time.sleep(acceptance.POLL_INTERVAL_S)
        items = acceptance.capture_ocr_bundle(
            artifacts, sample_stem, acceptance.FULL_SCREEN_REGION
        )
        if not items:
            raise acceptance.RunnerError(
                f"promo clean frame has no OCR evidence: {sample_stem}"
            )
        joined = "".join(str(item.get("text", "")) for item in items)
        normalized = _normalize_promo_visible_text(joined)
        forbidden_hits = [
            token
            for token in PROMO_FORBIDDEN_VISIBLE_TEXT
            if _normalize_promo_visible_text(token) in normalized
        ]
        drawer_hits, header_ocr = _promo_decisions_header_hits(items, width, height)
        product_event_overlay = promo_product_event_overlay_evidence(
            label, items, width, height
        )
        if forbidden_hits or drawer_hits or product_event_overlay:
            write_json(
                artifacts / f"red_{sample_stem}.json",
                {
                    "schema_version": 1,
                    "result": "RED",
                    "span": label,
                    "phase": phase,
                    "sample_index": sample_index,
                    "forbidden_hits": forbidden_hits,
                    "decisions_header_hits": drawer_hits,
                    "product_event_overlay": product_event_overlay,
                    "normalized_ocr": normalized,
                    "normalized_decisions_header_ocr": header_ocr,
                },
            )
            raise acceptance.RunnerError(
                f"promo clean frame {label}/{phase} contains fixture/test UI or "
                "the Decisions drawer, or overlays the free Jingcha planner with "
                "a product event: "
                f"forbidden={forbidden_hits}, drawer={drawer_hits}, "
                f"product_event_overlay={product_event_overlay}"
            )
        image_path = artifacts / f"{sample_stem}.png"
        ocr_path = artifacts / f"{sample_stem}_ocr.json"
        samples.append(
            {
                "sample_index": sample_index,
                "normalized_decisions_header_ocr": header_ocr,
                "image": {
                    "path": str(image_path.resolve()),
                    "bytes": image_path.stat().st_size,
                    "sha256": isolated.sha256_file(image_path),
                },
                "ocr": {
                    "path": str(ocr_path.resolve()),
                    "bytes": ocr_path.stat().st_size,
                    "sha256": isolated.sha256_file(ocr_path),
                },
            }
        )
    gate_path = artifacts / f"{stem}_gate.json"
    payload = {
        "schema_version": 1,
        "result": "GREEN",
        "span": label,
        "phase": phase,
        "full_screen": True,
        "fixture_test_ui_absent": True,
        "native_decisions_drawer_absent": True,
        "forbidden_hits": [],
        "drawer_absence_consecutive_samples": 2,
        "drawer_absence_samples": samples,
        "image": samples[0]["image"],
        "ocr": samples[0]["ocr"],
    }
    write_json(gate_path, payload)
    payload["gate"] = {
        "path": str(gate_path.resolve()),
        "bytes": gate_path.stat().st_size,
        "sha256": isolated.sha256_file(gate_path),
    }
    return payload


def git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def write_evidence_index(artifacts: Path, matrix: dict[str, object]) -> None:
    files: list[dict[str, object]] = []
    for path in sorted(item for item in artifacts.rglob("*") if item.is_file()):
        if path.name == "evidence-index.json":
            continue
        files.append(
            {
                "path": path.relative_to(artifacts).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": isolated.sha256_file(path),
            }
        )
    try:
        git_head = git_text("rev-parse", "HEAD")
        git_status = git_text(
            "status",
            "--short",
            "--",
            "mod_zhongguo_style",
            "tools/run_zhongguo_acceptance.py",
            "tools/fixtures/zg361_acceptance",
        ).splitlines()
    except (OSError, subprocess.SubprocessError) as error:
        git_head = f"unavailable: {error}"
        git_status = []
    write_json(
        artifacts / "evidence-index.json",
        {
            "schema_version": 1,
            "result": matrix.get("result"),
            "artifact_root": str(artifacts),
            "git_head": git_head,
            "scoped_git_status": git_status,
            "files": files,
        },
    )


def script_tree_errors(root: Path, label: str) -> list[str]:
    if not root.is_dir():
        return [f"{label} missing: {root}"]
    errors: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"{label} text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        runtime_product_file = not (
            root == SOURCE
            and (
                relative == "README.md"
                or relative.split("/", 1)[0] in SOURCE_ONLY_RUNTIME_ROOTS
            )
        )
        if runtime_product_file and "remote_file_id" in text:
            errors.append(f"{label} contains Workshop identity: {relative}")
        if root == FIXTURE_SOURCE and path.suffix.lower() in {".txt", ".gui"}:
            depth = 0
            for line_number, line in enumerate(text.splitlines(), 1):
                body = line.split("#", 1)[0]
                depth += body.count("{") - body.count("}")
                if depth < 0:
                    errors.append(
                        f"fixture has unexpected closing brace: {relative}:{line_number}"
                    )
                    break
            if depth > 0:
                errors.append(f"fixture has {depth} unclosed brace(s): {relative}")
    return errors


def product_source_errors() -> list[str]:
    errors = script_tree_errors(SOURCE, "product")
    descriptor = SOURCE / "descriptor.mod"
    if not descriptor.is_file():
        errors.append("product descriptor.mod is missing")
    else:
        text = descriptor.read_text(encoding="utf-8-sig")
        if f'supported_version="{EXPECTED_GAME_VERSION}"' not in text:
            errors.append(f"product descriptor must support {EXPECTED_GAME_VERSION}")

    triggers = SOURCE / "common" / "scripted_triggers" / "zg361_triggers.txt"
    if not triggers.is_file():
        errors.append("production 361 entry trigger is missing")
    else:
        text = triggers.read_text(encoding="utf-8-sig")
        match = re.search(
            r"zg361_is_celestial_liege_trigger\s*=\s*\{(?P<body>.*?)^\}",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if match is None:
            errors.append("cannot isolate zg361_is_celestial_liege_trigger")
        else:
            body = match.group("body")
            for token in (
                "government_has_flag = government_is_celestial",
                "highest_held_title_tier >= tier_duchy",
                "is_landed = yes",
                "is_alive = yes",
            ):
                if token not in body:
                    errors.append(f"duchy-plus celestial entry missing {token}")
            if "is_independent" in body:
                errors.append(
                    "361 entry must include non-independent celestial dukes and kings"
                )

    effects = SOURCE / "common" / "scripted_effects" / "zg361_effects.txt"
    effects_text = effects.read_text(encoding="utf-8-sig") if effects.is_file() else ""
    snapshot_effects = (
        SOURCE
        / "common"
        / "scripted_effects"
        / "zg361_generated_scoreboard_snapshots.txt"
    )
    scoreboard_effects_text = effects_text + (
        snapshot_effects.read_text(encoding="utf-8-sig")
        if snapshot_effects.is_file()
        else ""
    )
    for token in (
        "zg361_run_review_effect = {",
        'debug_log = "ZG361: annual review tick"',
        "limit = { var:zg361_cohort_n >= 1 }",
        "name = zg361_pending_35_n value = var:zg361_cohort_n",
        "name = zg361_pending_grade value = 2",
        'debug_log = "ZG361: small cohort bypassed forced distribution and settled at 3.5"',
        "zg361_publish_scoreboard_effect = yes",
        "zg361_clear_scoreboard_m_slots_effect = yes",
        "zg361_write_managed_scoreboard_slot_effect = yes",
        "zg361_sb_m_01_char",
        "zg361_scoreboard_managed_375_n",
        "zg361_scoreboard_managed_35_n",
        "zg361_scoreboard_managed_325_n",
        "zg361_scoreboard_managed_shown_n",
        "zg361_sb_m_01_title",
        "zg361_sb_m_01_promotion",
        "zg361_sb_m_01_pip",
        "zg361_copy_received_scoreboard_slots_effect = yes",
    ):
        if token not in scoreboard_effects_text:
            errors.append(f"production review/scoreboard contract missing {token}")

    events = SOURCE / "events" / "zg361_events.txt"
    event_text = events.read_text(encoding="utf-8-sig") if events.is_file() else ""
    for token in ("zg361.10 = {", "name = zg361.10.a", "zg361_apply_pending_grades_effect"):
        if token not in event_text:
            errors.append(f"direct-publication calibration contract missing {token}")
    for token in (
        "zg361_snapshot_player_result_effect = {",
        "save_scope_as = zg361_reviewing_superior",
        "name = zg361_result_kpi",
        "name = zg361_result_rank",
        "name = zg361_result_cohort_n",
    ):
        if token not in effects_text:
            errors.append(f"personal result snapshot contract missing {token}")
    if effects_text.count("zg361_snapshot_player_result_effect = yes") != 3:
        errors.append("all three player grades must freeze their result payload")
    if any(
        token in event_text
        for token in (
            "save_scope_as = zg361_reviewing_superior",
            "name = zg361_result_kpi",
            "name = zg361_result_rank",
            "name = zg361_result_cohort_n",
        )
    ):
        errors.append("delayed result events must not re-read live review data")

    phase_icon = (
        SOURCE
        / "gfx"
        / "interface"
        / "icons"
        / "activity_phases"
        / "zg361_jingcha_phase.dds"
    )
    if not phase_icon.is_file() or phase_icon.stat().st_size == 0:
        errors.append("production jingcha phase icon is missing")

    chinese_loc = SOURCE / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml"
    chinese_text = (
        chinese_loc.read_text(encoding="utf-8-sig") if chinese_loc.is_file() else ""
    )
    for token in (
        'zg361.1.t:0 "你主持的考核：名册已定"',
        'zg361.2.t:0 "上司考定：3.75',
        'zg361.3.t:0 "上司考定：3.5',
        'zg361.4.t:0 "上司考定：3.25',
        "TopScope.GetValue('zg361_result_kpi')",
        "TopScope.GetValue('zg361_result_rank')",
    ):
        if token not in chinese_text:
            errors.append(f"personal result localization contract missing {token}")

    gui = SOURCE / "gui" / "zg361_scoreboard.gui"
    gui_text = gui.read_text(encoding="utf-8-sig") if gui.is_file() else ""
    for token in (
        'name = "zg361_scoreboard_toggle"',
        'position = { -60 90 }',
        "Not(IsRightWindowOpen)",
        "Not(IsGameViewOpen('outliner'))",
        "Not(IsPauseMenuShown)",
        "IsDefaultGUIMode",
        'name = "zg361_scoreboard_panel"',
        "zg361_sb_m_01_kpi",
        "zg361_scoreboard_tab_managed",
        "zg361_scoreboard_tab_received",
        "zg361_scoreboard_tab_system",
        'shortcut = "close_window"',
    ):
        if token not in gui_text:
            errors.append(f"production managed scoreboard GUI missing {token}")
    registration = SOURCE / "gui" / "scripted_widgets" / "zg361_scripted_widgets.txt"
    if not registration.is_file() or (
        "gui/zg361_scoreboard.gui = zg361_scoreboard_window"
        not in registration.read_text(encoding="utf-8-sig")
    ):
        errors.append("production scoreboard widget registration is missing")
    return errors


def fixture_source_errors() -> list[str]:
    errors = script_tree_errors(FIXTURE_SOURCE, "fixture")
    required = (
        "descriptor.mod",
        "common/decisions/zga_decisions.txt",
        "common/scripted_effects/zga_effects.txt",
        "common/scripted_effects/zga_generated_361_cases.txt",
        "common/scripted_guis/zga_guis.txt",
        "events/zga_events.txt",
        "gui/zga_bridge.gui",
        "gui/scripted_widgets/zga_scripted_widgets.txt",
        "localization/simp_chinese/zga_l_simp_chinese.yml",
        "localization/english/zga_l_english.yml",
    )
    for relative in required:
        if not (FIXTURE_SOURCE / relative).is_file():
            errors.append(f"fixture file missing: {relative}")
    effects = FIXTURE_SOURCE / "common" / "scripted_effects" / "zga_effects.txt"
    text = effects.read_text(encoding="utf-8-sig") if effects.is_file() else ""
    generated_cases = (
        FIXTURE_SOURCE
        / "common"
        / "scripted_effects"
        / "zga_generated_361_cases.txt"
    )
    fixture_events = FIXTURE_SOURCE / "events" / "zga_events.txt"
    fixture_decisions = FIXTURE_SOURCE / "common" / "decisions" / "zga_decisions.txt"
    scenario_text = text + (
        generated_cases.read_text(encoding="utf-8-sig")
        if generated_cases.is_file()
        else ""
    ) + (
        fixture_events.read_text(encoding="utf-8-sig")
        if fixture_events.is_file()
        else ""
    ) + (
        fixture_decisions.read_text(encoding="utf-8-sig")
        if fixture_decisions.is_file()
        else ""
    )
    for token in (
        "character:han_8052",
        "title:h_china",
        "zg361_run_review_effect = yes",
        "zg361_scoreboard_managed",
        "highest_held_title_tier >= tier_duchy",
        "non_independent_celestial_liege_entry",
        "set_player_character = scope:zga_personal_result_target",
        "superior_assigned_player_grade",
        "personal_result_switch_scheduled",
        "zga_verify_361_mechanism_batch_effect = yes",
        "ZGA: MECHANISM CASE PASS 001",
        "ZGA: MECHANISM CASE PASS 361",
        "zga_verify_fixed_scoreboard_slots_effect = yes",
        "zg361_sb_m_01_char",
        "zga_jingcha_planner_decision",
        "set_variable = { name = zg361_jingcha_pending value = 1 }",
        "trigger_event = zg361.40",
        "jingcha_mandate_issued",
        "grade_325_fourfold_penalty",
        "appeal_exact_fixed_refund_and_salary_stop",
        "appeal_refund_idempotent",
        "newcomer_first_review_protected",
        "pending_review_idempotent",
        "newcomer_first_review_result_without_325",
        "calibration_c_all_newcomer_noop",
        "calibration_c_mixed_newcomer_atomic_swap",
        "var:zga_all_new_protected_actual = var:zg361_cohort_n",
        "zga_original_pending_grade",
        "var:zga_mixed_35_actual = var:zga_mixed_35_actual_before",
        "var:zga_mixed_325_actual = var:zga_mixed_325_actual_before",
        "zga_mark_historical_song_direct_candidate_effect",
        "historical_song_direct_whitelist_complete",
        "generated_city_officials_excluded_from_provenance",
        "personal_result_target_selected_from_prior_historical_assessor_tail",
        "personal_result_target_can_assess_others",
        "personal_result_target_projected_bottom_two",
        HISTORICAL_TARGET_DATA_MARKER_PREFIX,
        HISTORICAL_TARGET_PASS_MARKER,
        "clean_jingcha_dispatch_scheduled",
        "clean_jingcha_dispatched",
        "clean_policy_chain_scheduled",
        "clean_policy_001_dispatched",
        "clean_policy_007_dispatched",
        "clean_policy_020_dispatched",
        "clean_policy_022_dispatched",
        "clean_policy_026_dispatched",
        "clean_policy_361_dispatched",
        "clean_policy_chain_completed",
        "trigger_event = { id = zga_acceptance.5 days = 2 }",
        "trigger_event = { id = zga_acceptance.12 days = 1 }",
        "settled_review_same_year_idempotent",
        "jingcha_refusal_superior_opinion_and_kpi_minus_50",
        "refusal_reason_consumed_once_by_original_superior",
        "ai_small_cohort_review_scheduled",
        "ai_small_cohort_candidate_unavailable",
        "ai_small_cohort_neutral_settlement",
        "ai_small_cohort_same_year_idempotent",
    ):
        if token not in scenario_text:
            errors.append(f"fixture scenario contract missing {token}")
    expected_historical_ids = set(EXPECTED_HISTORICAL_COHORT_HISTORY_IDS)
    expected_target_ids = set(EXPECTED_REVIEWED_OFFICIAL_HISTORY_IDS)
    marked_historical_id_rows = re.findall(
        r"character:(han_\d+)\s*=\s*\{\s*"
        r"zga_mark_historical_song_direct_candidate_effect\s*=\s*yes\s*\}",
        text,
    )
    marked_historical_ids = set(marked_historical_id_rows)
    data_marker_id_rows = re.findall(
        re.escape(HISTORICAL_TARGET_DATA_MARKER_PREFIX) + r"(han_\d+)\b",
        text,
    )
    data_marker_ids = set(data_marker_id_rows)
    if (
        marked_historical_ids != expected_historical_ids
        or len(marked_historical_id_rows) != len(expected_historical_ids)
    ):
        errors.append(
            "fixture historical candidate marks drifted from the frozen 21-person "
            f"allowlist: missing={sorted(expected_historical_ids - marked_historical_ids)}, "
            f"extra={sorted(marked_historical_ids - expected_historical_ids)}"
        )
    if (
        data_marker_ids != expected_target_ids
        or len(data_marker_id_rows) != len(expected_target_ids)
    ):
        errors.append(
            "fixture historical target DATA branches drifted from the frozen "
            f"18-person duke+ allowlist: missing={sorted(expected_target_ids - data_marker_ids)}, "
            f"extra={sorted(data_marker_ids - expected_target_ids)}"
        )
    if text.count(f'debug_log = "{HISTORICAL_TARGET_PASS_MARKER}"') != 1:
        errors.append(
            "fixture must emit exactly one generic historical target PASS branch"
        )
    for token in (
        "create_character",
        "create_title",
        "grant_title",
        "set_father",
        "set_mother",
        "set_spouse",
        "add_relation",
        "set_relation",
    ):
        if re.search(rf"\b{re.escape(token)}\b", scenario_text):
            errors.append(
                f"fixture must use vanilla history subjects, found constructor {token}"
            )
    return errors


def verified_workshop_runtime(
    runtime_source: Path, workshop_manifest: Path
) -> dict[str, object]:
    """Verify a real Workshop cache leaf against the tagged release sidecar."""

    runtime_source = Path(runtime_source).expanduser().resolve()
    workshop_manifest = Path(workshop_manifest).expanduser().resolve()
    if not runtime_source.is_dir():
        raise acceptance.RunnerError(
            f"Workshop runtime source directory missing: {runtime_source}"
        )
    if not workshop_manifest.is_file():
        raise acceptance.RunnerError(
            f"Workshop verification manifest missing: {workshop_manifest}"
        )
    try:
        count = release.verify_manifest(
            runtime_source, workshop_manifest, workshop_cache=True
        )
        payload = json.loads(workshop_manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise acceptance.RunnerError(
            f"Workshop runtime manifest verification failed: {error}"
        ) from error
    item_id = str(payload["workshop_item_id"])
    if runtime_source.name != item_id:
        raise acceptance.RunnerError(
            "Workshop runtime source must be the numeric cache leaf matching "
            f"the manifest item ID: {runtime_source.name!r} != {item_id!r}"
        )
    steam_root = terminal.steam_userdata_root()
    app_roots = [
        path.resolve() for path in isolated.steam_workshop_app_roots(steam_root)
    ]
    isolated.validate_workshop_target(runtime_source, app_roots)
    try:
        head = git_text("rev-parse", "HEAD")
    except (OSError, subprocess.SubprocessError) as error:
        raise acceptance.RunnerError(
            f"cannot bind Workshop cache to Git HEAD: {error}"
        ) from error
    if payload["git_sha"] != head:
        raise acceptance.RunnerError(
            f"Workshop manifest Git SHA {payload['git_sha']} does not match HEAD {head}"
        )
    if payload["git_tag"] != release.product_tag(str(payload["mod_version"])):
        raise acceptance.RunnerError(
            "Workshop manifest is not bound to the formal product tag"
        )
    return {
        "verified_workshop_cache": True,
        "runtime_source_kind": "verified_workshop_cache",
        "runtime_source_path": str(runtime_source),
        "workshop_item_id": item_id,
        "workshop_manifest_path": str(workshop_manifest),
        "workshop_manifest_sha256": isolated.sha256_file(workshop_manifest),
        "workshop_manifest_git_sha": payload["git_sha"],
        "workshop_manifest_git_tag": payload["git_tag"],
        "verified_file_count": count,
    }


def preflight(
    runtime_source: Path = SOURCE, workshop_manifest: Path | None = None
) -> dict[str, object]:
    errors = fixture_source_errors()
    errors.extend(product_source_errors())
    runtime_source = Path(runtime_source).expanduser().resolve()
    runtime_identity: dict[str, object] = {
        "verified_workshop_cache": False,
        "runtime_source_kind": "canonical_development_projection",
        "runtime_source_path": str(SOURCE.resolve()),
        "workshop_item_id": None,
        "workshop_manifest_path": None,
        "workshop_manifest_sha256": None,
        "workshop_manifest_git_sha": None,
        "workshop_manifest_git_tag": None,
        "verified_file_count": None,
    }
    if runtime_source == SOURCE.resolve():
        if workshop_manifest is not None:
            errors.append(
                "--workshop-manifest requires --workshop-cache-source"
            )
    elif workshop_manifest is None:
        errors.append(
            "a non-canonical runtime source requires --workshop-manifest"
        )
    else:
        try:
            runtime_identity = verified_workshop_runtime(
                runtime_source, workshop_manifest
            )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    fixture_generation = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "gen_zhongguo_acceptance_cases.py"), "--check"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if fixture_generation.returncode != 0:
        errors.append(
            "361 live fixture generator is RED:\n"
            + (fixture_generation.stdout + fixture_generation.stderr).strip()
        )
    clean_fixture_contract = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "test_zg361_clean_promo_fixture.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if clean_fixture_contract.returncode != 0:
        errors.append(
            "clean historical promo fixture contract is RED:\n"
            + (
                clean_fixture_contract.stdout + clean_fixture_contract.stderr
            ).strip()
        )
    validation = subprocess.run(
        [sys.executable, str(SOURCE / "tools" / "validate_local.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if validation.returncode != 0:
        errors.append(
            "product static validator is RED:\n"
            + (validation.stdout + validation.stderr).strip()
        )
    if os.name != "nt":
        errors.append("ZhongGuo 361 acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("CK3 live acceptance is forbidden on official GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            version = isolated.installed_game_version()
            if version != EXPECTED_GAME_VERSION:
                errors.append(f"CK3 version is {version}, expected {EXPECTED_GAME_VERSION}")
            executable_sha256 = isolated.sha256_file(acceptance.CK3_EXE)
            if executable_sha256 != EXPECTED_EXE_SHA256:
                errors.append(
                    "CK3 executable SHA-256 is "
                    f"{executable_sha256}, expected {EXPECTED_EXE_SHA256}"
                )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    width, height = acceptance.pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: CK3={EXPECTED_GAME_VERSION}, "
        f"exe_sha256={EXPECTED_EXE_SHA256}, desktop={width}x{height}"
    )
    return runtime_identity


def render_presets() -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    settings.extend(("zg361_on", "zg361_freq_yearly", "zg361_ratio_strict"))
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate game-rule setting in acceptance preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def bootstrap_userdir(
    userdir: Path, product_source: Path = SOURCE
) -> dict[str, object]:
    product_source = Path(product_source).resolve()
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)

    product = userdir / "mod-content" / "zhongguo_361"
    product.mkdir(parents=True)
    product_files: list[str] = []
    for source_path in sorted(
        path for path in product_source.rglob("*") if path.is_file()
    ):
        relative = source_path.relative_to(product_source)
        if (
            relative.as_posix() == "README.md"
            or relative.parts[0] in SOURCE_ONLY_RUNTIME_ROOTS
        ):
            continue
        destination = product / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        product_files.append(relative.as_posix())

    fixture = userdir / "mod-content" / "fixture"
    shutil.copytree(FIXTURE_SOURCE, fixture)
    isolated.write_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(
        fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
    )
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(), encoding="utf-8", newline="\n"
    )
    (userdir / "dlc_load.json").write_text(
        json.dumps(
            {"enabled_mods": enabled_mods, "disabled_dlcs": []},
            separators=(",", ":"),
        ),
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "pdx_settings.txt").write_text(
        terminal.render_settings(), encoding="utf-8", newline="\n"
    )
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    manifest = {
        "projection": "release-runtime-allowlist-equivalent",
        "files": product_files,
        "tree_sha256": isolated.snapshot_digest(snapshots["product"]),
    }
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot) for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "manifest": manifest,
    }


def verify_runtime_load_order(
    userdir: Path, bootstrap: dict[str, object]
) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    try:
        text = debug_log.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise acceptance.RunnerError(f"cannot read runtime mod inventory: {error}") from error
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            f"isolated enabled-mod inventory drifted: {enabled} != {expected_enabled}"
        )
    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [Path(bootstrap["targets"][key]).resolve() for key in ("product", "fixture")]
    if mounted != expected:
        raise acceptance.RunnerError(
            "isolated mount order drifted: "
            f"{[path.as_posix() for path in mounted]} != "
            f"{[path.as_posix() for path in expected]}"
        )
    return [path.as_posix() for path in mounted]


class MarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""
        self.lines: list[str] = []

    def pump(self, final: bool = False) -> None:
        try:
            with self.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self.offset:
                    self.offset = 0
                    self.pending = b""
                source.seek(self.offset)
                data = source.read()
                self.offset = source.tell()
        except OSError as error:
            if final:
                raise acceptance.RunnerError(f"cannot finalize fixture log: {error}") from error
            data = b""
        payload = self.pending + data
        if final:
            complete, self.pending = payload, b""
        else:
            boundary = max(payload.rfind(b"\n"), payload.rfind(b"\r"))
            if boundary < 0:
                self.pending = payload
                return
            complete, self.pending = payload[: boundary + 1], payload[boundary + 1 :]
        for line in complete.decode("utf-8", errors="ignore").splitlines():
            if "ZGA:" in line or "ZG361:" in line or "ZG361M:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                if not (
                    "ZGA: MECHANISM CASE PASS" in stripped
                    or "ZG361M: CASE" in stripped
                    or "ZGA: DATA player_scoreboard" in stripped
                    or "ZGA: DATA player_grade" in stripped
                ):
                    log(stripped)
        failures = [
            line
            for line in self.lines
            if "ZGA: TEST FAIL" in line or "ZGA: MECHANISM CASE FAIL" in line
            or "ZGA: MECHANISM LEDGER FAIL" in line
            or "ZGA: MECHANISM IDEMPOTENCE FAIL" in line
        ]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def count(self, marker: str) -> int:
        return sum(marker in line for line in self.lines)

    def wait(self, marker: str, timeout_s: float = 20) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.pump()
            if self.count(marker):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def counts(self) -> dict[str, int]:
        return {
            "rows": self.count("ZGA: DATA player_scoreboard_row"),
            "grade_375": self.count("ZGA: DATA player_grade_375"),
            "grade_35": self.count("ZGA: DATA player_grade_35"),
            "grade_325": self.count("ZGA: DATA player_grade_325"),
            "ai_non_independent_rows": self.count(
                "ZGA: DATA ai_non_independent_scoreboard_row"
            ),
        }

    def validate(self, final: bool = False) -> None:
        self.pump(final=final)
        required_markers = REQUIRED_FIXTURE_MARKERS
        if final:
            required_markers += REQUIRED_LATE_FIXTURE_MARKERS
        for marker in required_markers:
            count = self.count(marker)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )
        for marker, minimum in REQUIRED_PRODUCT_MARKERS.items():
            count = self.count(marker)
            if count < minimum:
                raise acceptance.RunnerError(
                    f"product marker count for {marker!r} is {count}, expected >= {minimum}"
                )
        case_pass_ids = [
            int(match.group(1))
            for line in self.lines
            if (match := re.search(r"ZGA: MECHANISM CASE PASS (\d{3})", line))
        ]
        if case_pass_ids != list(range(1, 362)):
            raise acceptance.RunnerError(
                "361 fixture case coverage drifted: "
                f"count={len(case_pass_ids)}, unique={len(set(case_pass_ids))}"
            )
        batch_begin = next(
            index
            for index, line in enumerate(self.lines)
            if "ZGA: MECHANISM BATCH BEGIN 361" in line
        )
        batch_done = next(
            index
            for index, line in enumerate(self.lines[batch_begin:], batch_begin)
            if "ZGA: MECHANISM BATCH DONE 361" in line
        )
        batch_lines = self.lines[batch_begin : batch_done + 1]
        applied = [
            (int(match.group(1)), match.group(2).lower())
            for line in batch_lines
            if (
                match := re.search(
                    r"ZG361M: CASE (\d{3}) CHOICE ([ABC]) APPLIED", line
                )
            )
        ]
        manifest = json.loads(
            (SOURCE / "docs" / "361-mechanism-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        expected_applied = [
            (int(item["id"]), str(item["reference_choice"]))
            for item in manifest["items"]
        ]
        if applied != expected_applied:
            raise acceptance.RunnerError(
                "product mechanism markers do not match the 361 reference portfolio: "
                f"count={len(applied)}, unique={len(set(applied))}"
            )
        failures = [
            line
            for line in self.lines
            if "ZGA: TEST FAIL" in line or "ZGA: MECHANISM CASE FAIL" in line
            or "ZGA: MECHANISM LEDGER FAIL" in line
            or "ZGA: MECHANISM IDEMPOTENCE FAIL" in line
        ]
        if failures:
            raise acceptance.RunnerError(
                f"fixture emitted {len(failures)} failure marker(s)"
            )
        counts = self.counts()
        if counts["rows"] < 3:
            raise acceptance.RunnerError(
                f"managed scoreboard emitted only {counts['rows']} row marker(s)"
            )
        if (
            counts["grade_375"] + counts["grade_35"] + counts["grade_325"]
            != counts["rows"]
        ):
            raise acceptance.RunnerError(f"grade marker totals do not match rows: {counts}")
        scheduled = self.count("ZGA: TEST INFO ai_non_independent_review_scheduled")
        unavailable = self.count(
            "ZGA: TEST INFO ai_non_independent_review_candidate_unavailable"
        )
        if scheduled + unavailable != 1:
            raise acceptance.RunnerError(
                "AI non-independent probe must be either scheduled or explicitly unavailable"
            )
        if scheduled:
            for marker in (
                "ZGA: TEST PASS ai_non_independent_newcomer_snapshot",
                "ZGA: TEST PASS ai_non_independent_full_review",
                "ZGA: TEST PASS settled_review_same_year_idempotent",
            ):
                if self.count(marker) != 1:
                    raise acceptance.RunnerError(
                        f"scheduled AI non-independent probe missing {marker}"
                    )
            if counts["ai_non_independent_rows"] < 3:
                raise acceptance.RunnerError(
                    "scheduled AI non-independent probe emitted fewer than 3 rows"
                )
        # The natural 1–2-person probe is deliberately scheduled only after the
        # manager board and the player's superior-assigned result are frozen.
        # The mid-run validation immediately after direct publication therefore
        # cannot demand its terminal marker; final validation remains strict.
        if final:
            self.validate_small_cohort_probe()

    def validate_small_cohort_probe(self) -> None:
        small_scheduled = self.count("ZGA: TEST INFO ai_small_cohort_review_scheduled")
        small_unavailable = self.count(
            "ZGA: TEST INFO ai_small_cohort_candidate_unavailable"
        )
        if small_scheduled + small_unavailable != 1:
            raise acceptance.RunnerError(
                "AI small-cohort probe must be either scheduled or explicitly unavailable"
            )
        if small_scheduled:
            for marker in (
                "ZGA: TEST PASS ai_small_cohort_neutral_settlement",
                "ZGA: TEST PASS ai_small_cohort_same_year_idempotent",
            ):
                if self.count(marker) != 1:
                    raise acceptance.RunnerError(
                        f"scheduled AI small-cohort probe missing {marker}"
                    )


def resolved_historical_personal_result_target(stream: MarkerStream) -> str:
    """Parse one exact target marker and enforce the frozen historical set."""

    stream.pump()
    pattern = re.compile(
        re.escape(HISTORICAL_TARGET_DATA_MARKER_PREFIX) + r"(han_\d+)\b"
    )
    matches = [
        match.group(1)
        for line in stream.lines
        if (match := pattern.search(line)) is not None
    ]
    if len(matches) != 1:
        raise acceptance.RunnerError(
            "historical personal-result target marker must resolve exactly once; "
            f"found={matches!r}"
        )
    history_id = matches[0]
    if history_id not in real_characters.REVIEWED_OFFICIAL_CONTRACT:
        raise acceptance.RunnerError(
            "historical personal-result target is outside the frozen 1066 Song "
            f"allowlist: {history_id}"
        )
    return history_id


def project_diagnostics(
    userdir: Path, artifacts: Path, stem: str
) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    observed_engine_warnings: list[str] = []
    for name in ("error.log", "game.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"{stem}_{name}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            context = " ".join(lines[max(0, index - 2) : index + 3]).lower()
            attributed = any(token in lowered for token in PROJECT_TOKENS)
            duplicate = any(pattern in lowered for pattern in DUPLICATE_PATTERNS)
            dynastic_cycle_stepdown_warning = (
                name == "game.log"
                and "situation.cpp:1314" in lowered
                and "attempted to remove" in lowered
                and "dynastic_cycle" in lowered
            )
            if dynastic_cycle_stepdown_warning:
                observed_engine_warnings.append(f"{name}: {line.strip()}")
            elif attributed or (
                duplicate and any(token in context for token in PROJECT_TOKENS)
            ):
                blocking.append(f"{name}: {line.strip()}")
    return (
        list(dict.fromkeys(line for line in blocking if line.strip())),
        list(
            dict.fromkeys(
                line for line in observed_engine_warnings if line.strip()
            )
        ),
    )


def initialize_fixture(stream: MarkerStream, artifacts: Path) -> None:
    confirm = isolated.open_decision_detail(
        "开始361制实机验收",
        "切换至宋帝并开考",
        artifacts,
        "05_fixture_initialize",
    )
    acceptance.click_until_text_disappears(
        confirm,
        "切换至宋帝并开考",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    for marker in REQUIRED_FIXTURE_MARKERS[:13]:
        stream.wait(marker, 30)
    isolated.wait_for_gameplay_hud(artifacts)
    acceptance.ensure_game_paused(artifacts, "05_song_emperor")


def choose_direct_publication(
    stream: MarkerStream, artifacts: Path, recorder: PromoRecorder | None = None
) -> None:
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "决议", (0.52, 0.00, 0.99, 0.30), contains=True
    ) is not None:
        image.save(artifacts / "06_decisions_drawer_before_calibration.png")
        acceptance.pyautogui.press("escape")
        time.sleep(0.8)
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_calibration", require_progress=True
    )
    log("advanced the live date for the one-day production calibration event")
    settle_promo_interruptions(
        artifacts,
        "06_calibration_preemption",
        observation_s=20.0,
        stop_event_title="绩效校准会议",
    )
    acceptance.wait_for_ocr_text(
        "绩效校准会议",
        PROMO_EVENT_TITLE_REGION,
        60,
        artifacts,
        "06_calibration_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("calibration_event_visible")
        recorder.clean_hold("calibration", artifacts)
    option = acceptance.wait_for_ocr_text(
        "名单无误",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "06_calibration_direct_publication.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(option, "production calibration direct publication")
    stream.wait("ZG361: scoreboard published", 30)
    stream.wait("ZGA: TEST PASS scoreboard_header_and_rows", 30)
    stream.wait("ZGA: TEST PASS three_grade_counts", 30)
    stream.wait("ZGA: TEST DONE zg361", 30)
    stream.validate()


def close_native_decisions_panel(artifacts: Path, stem: str) -> str:
    """Close the native drawer and prove it is gone before seeking our HUD button."""

    def wait_until_closed(
        timeout_s: float, success_artifact: str, failure_artifact: str
    ) -> bool:
        deadline = time.monotonic() + timeout_s
        absent_hits = 0
        last_image = None
        while time.monotonic() < deadline:
            acceptance.focus_ck3()
            last_image = acceptance.ImageGrab.grab()
            visible = acceptance.find_ocr_text(
                last_image, "决议", DECISIONS_HEADER_REGION, contains=True
            )
            absent_hits = absent_hits + 1 if visible is None else 0
            if absent_hits >= 2:
                last_image.save(artifacts / success_artifact)
                return True
            time.sleep(acceptance.POLL_INTERVAL_S)
        if last_image is not None:
            last_image.save(artifacts / failure_artifact)
        return False

    acceptance.focus_ck3()
    width, height = acceptance.pyautogui.size()
    # An open decision-row tooltip can consume the first Escape while leaving
    # the right drawer untouched. Move away before exercising that close path.
    acceptance.pyautogui.moveTo(int(width * 0.50), int(height * 0.50), duration=0.2)
    time.sleep(0.5)
    acceptance.pyautogui.press("escape")
    if wait_until_closed(
        2.5,
        f"{stem}_closed_by_escape.png",
        f"{stem}_escape_left_drawer_open.png",
    ):
        return "escape"

    close_point = (
        int(width * DECISIONS_CLOSE_BUTTON[0]),
        int(height * DECISIONS_CLOSE_BUTTON[1]),
    )
    acceptance.deliberate_click(close_point, "native Decisions title-bar close button")
    if wait_until_closed(
        5.0,
        f"{stem}_closed_by_title_button.png",
        f"red_{stem}_drawer_still_open.png",
    ):
        return "title_bar_close"
    raise acceptance.RunnerError(
        "native Decisions drawer remained open after Escape and its title-bar close button"
    )


def wait_for_scoreboard_closed_with_toggle(
    artifacts: Path, stem: str, timeout_s: float = 8.0
) -> tuple[int, int]:
    """Prove the modal closed and its safe-lane HUD toggle became clickable again."""

    deadline = time.monotonic() + timeout_s
    stable_hits = 0
    last_image = None
    last_button = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        last_image = acceptance.ImageGrab.grab()
        title = acceptance.find_ocr_text(
            last_image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        )
        last_button = acceptance.find_ocr_text(
            last_image,
            "考核榜",
            SCOREBOARD_BUTTON_REGION,
            contains=True,
        )
        stable_hits = stable_hits + 1 if title is None and last_button else 0
        if stable_hits >= 2:
            last_image.save(artifacts / f"{stem}_closed.png")
            return last_button
        time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"timeout_{stem}_close.png")
    raise acceptance.RunnerError(
        f"{stem} did not close the scoreboard and restore its safe-lane toggle"
    )


def reopen_managed_scoreboard_for_audit(
    artifacts: Path, stem: str, button: tuple[int, int]
) -> None:
    """Reopen the board after one close probe and prove managed content returned."""

    acceptance.deliberate_click(button, f"reopen performance board after {stem}")
    acceptance.wait_for_ocr_text(
        "天朝官员考核榜",
        acceptance.FULL_SCREEN_REGION,
        12,
        artifacts,
        f"{stem}_title.png",
        contains=True,
        stable_hits=2,
    )
    acceptance.wait_for_ocr_tokens(
        ("所辖官员", "官员 / 官职", "点击任一官员"),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        stem,
    )


def select_representative_scoreboard_row(
    items: list[dict[str, object]], width: int, height: int
) -> tuple[dict[str, object], str] | None:
    """Select one visible real-character row, never a header or event option."""

    left, top, right, bottom = SCOREBOARD_ROW_NAME_REGION
    candidates: list[tuple[int, dict[str, object], str]] = []
    for item in items:
        text = re.sub(r"\s+", "", str(item.get("text", "")))
        center = item.get("center")
        bbox = item.get("bbox")
        if not isinstance(center, (list, tuple)) or len(center) != 2:
            continue
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        x_ratio = float(center[0]) / width
        y_ratio = float(center[1]) / height
        if not (left <= x_ratio <= right and top <= y_ratio <= bottom):
            continue
        if (float(bbox[2]) - float(bbox[0])) / width < 0.06:
            continue
        parts = re.split(r"[，,、]", text)
        if len(parts) < 2:
            continue
        personal_name = "".join(re.findall(r"[\u3400-\u9fff]", parts[-1]))
        if len(personal_name) < 2:
            continue
        candidates.append((int(center[1]), item, personal_name))
    if not candidates:
        return None
    _, item, personal_name = min(candidates, key=lambda candidate: candidate[0])
    return item, personal_name


def wait_for_representative_character_view(
    artifacts: Path,
    stem: str,
    source_row: dict[str, object],
    name_probe: str,
    timeout_s: float = 12.0,
) -> tuple[int, int]:
    """Prove a row click closed the board and opened that character's native view."""

    deadline = time.monotonic() + timeout_s
    stable_hits = 0
    last_image = None
    last_name = None
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        last_image = acceptance.ImageGrab.grab()
        board_title = acceptance.find_ocr_text(
            last_image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        )
        last_name = acceptance.find_ocr_text(
            last_image,
            name_probe,
            CHARACTER_WINDOW_NAME_REGION,
            contains=True,
        )
        stable_hits = stable_hits + 1 if board_title is None and last_name else 0
        if stable_hits >= 2:
            last_image.save(artifacts / f"{stem}_character_open.png")
            write_json(
                artifacts / f"{stem}_character_open.json",
                {
                    "schema_version": 1,
                    "source_row_text": source_row["text"],
                    "source_row_center": source_row["center"],
                    "verification_name_probe": name_probe,
                    "character_name_center": list(last_name),
                    "scoreboard_closed": True,
                    "native_character_view_open": True,
                },
            )
            return last_name
        time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"timeout_{stem}_character_open.png")
    raise acceptance.RunnerError(
        "representative scoreboard row did not close the board and open its character"
    )


def close_representative_character_view(
    artifacts: Path, stem: str, name_probe: str
) -> dict[str, object]:
    """Restore a clean map through the native character title-bar close control."""

    width, height = acceptance.pyautogui.size()
    close_point = (
        int(width * CHARACTER_WINDOW_CLOSE_BUTTON[0]),
        int(height * CHARACTER_WINDOW_CLOSE_BUTTON[1]),
    )
    for attempt in range(1, 3):
        acceptance.focus_ck3()
        acceptance.deliberate_click(
            close_point, "native character title-bar close button"
        )
        deadline = time.monotonic() + 3.0
        absent_hits = 0
        last_image = None
        while time.monotonic() < deadline:
            last_image = acceptance.ImageGrab.grab()
            visible = acceptance.find_ocr_text(
                last_image,
                name_probe,
                CHARACTER_WINDOW_NAME_REGION,
                contains=True,
            )
            absent_hits = absent_hits + 1 if visible is None else 0
            if absent_hits >= 2:
                last_image.save(artifacts / f"{stem}_character_closed.png")
                return {
                    "method": "title_bar_close",
                    "attempts": attempt,
                    "point_px": list(close_point),
                    "point_normalized": list(CHARACTER_WINDOW_CLOSE_BUTTON),
                }
            time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / f"red_{stem}_character_still_open.png")
    raise acceptance.RunnerError(
        "representative row opened a character view that could not be closed"
    )


def audit_scoreboard_controls(artifacts: Path) -> dict[str, object]:
    """Live-click representative custom controls without claiming 160 row clicks."""

    # A queued product event can cover the modal even while its title and tabs
    # remain OCR-visible underneath.  The recovery classifier is deliberately
    # conservative and leaves a clean board untouched.
    settle_promo_interruptions(
        artifacts, "08_gui_audit_preflight", observation_s=1.0
    )
    acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "所辖官员", "点击任一官员"),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "08_gui_audit_ready",
    )
    width, height = acceptance.pyautogui.size()

    title_close_point = (
        int(width * SCOREBOARD_TITLE_CLOSE_BUTTON[0]),
        int(height * SCOREBOARD_TITLE_CLOSE_BUTTON[1]),
    )
    acceptance.deliberate_click(
        title_close_point, "performance-board title-bar close button"
    )
    title_toggle = wait_for_scoreboard_closed_with_toggle(
        artifacts, "08_gui_audit_title_button"
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_title_button_reopen", title_toggle
    )

    backdrop_point = (
        int(width * SCOREBOARD_BACKDROP_POINT[0]),
        int(height * SCOREBOARD_BACKDROP_POINT[1]),
    )
    acceptance.deliberate_click(backdrop_point, "performance-board modal backdrop")
    backdrop_toggle = wait_for_scoreboard_closed_with_toggle(
        artifacts, "08_gui_audit_backdrop"
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_backdrop_reopen", backdrop_toggle
    )

    row_items = acceptance.capture_ocr_bundle(
        artifacts, "08_gui_audit_row_source", acceptance.FULL_SCREEN_REGION
    )
    selected = select_representative_scoreboard_row(row_items, width, height)
    if selected is None:
        raise acceptance.RunnerError(
            "no visible real-character scoreboard row satisfied the representative audit"
        )
    source_row, personal_name = selected
    # Use the final two CJK characters as the cross-font OCR probe.  The row
    # and native character header render the same UI name at different sizes;
    # the leading glyph is the one most often recognized differently.
    name_probe = personal_name[-2:]
    row_center = tuple(int(value) for value in source_row["center"])
    acceptance.deliberate_click(
        row_center, f"representative generated scoreboard row: {source_row['text']!r}"
    )
    character_name_center = wait_for_representative_character_view(
        artifacts,
        "08_gui_audit_row_link",
        source_row,
        name_probe,
    )
    cleanup = close_representative_character_view(
        artifacts, "08_gui_audit_row_link", name_probe
    )
    row_reopen_button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        10,
        artifacts,
        "08_gui_audit_row_link_toggle_restored.png",
        contains=True,
        stable_hits=2,
    )
    reopen_managed_scoreboard_for_audit(
        artifacts, "08_gui_audit_row_link_reopen", row_reopen_button
    )

    return {
        "scope": "representative_generated_controls",
        "title_bar_close": {
            "clicked": True,
            "scoreboard_closed": True,
            "scoreboard_reopened": True,
            "point_px": list(title_close_point),
            "point_normalized": list(SCOREBOARD_TITLE_CLOSE_BUTTON),
            "closed_artifact": "08_gui_audit_title_button_closed.png",
            "reopened_artifact": "08_gui_audit_title_button_reopen.png",
        },
        "modal_backdrop": {
            "clicked": True,
            "scoreboard_closed": True,
            "scoreboard_reopened": True,
            "point_px": list(backdrop_point),
            "point_normalized": list(SCOREBOARD_BACKDROP_POINT),
            "closed_artifact": "08_gui_audit_backdrop_closed.png",
            "reopened_artifact": "08_gui_audit_backdrop_reopen.png",
        },
        "row_link": {
            "clicked": True,
            "scoreboard_closed": True,
            "native_character_view_opened": True,
            "scoreboard_reopened_after_character_cleanup": True,
            "source_text": source_row["text"],
            "source_center_px": list(row_center),
            "source_personal_name_ocr": personal_name,
            "verification_name_probe": name_probe,
            "character_name_center_px": list(character_name_center),
            "artifact": "08_gui_audit_row_link_character_open.png",
            "reopened_artifact": "08_gui_audit_row_link_reopen.png",
            "cleanup": cleanup,
        },
        "row_link_coverage": {
            "generated_total": SCOREBOARD_GENERATED_ROW_LINKS,
            "live_clicked": 1,
            "not_individually_clicked": SCOREBOARD_GENERATED_ROW_LINKS - 1,
            "claim": "one representative click over a shared generated row structure",
        },
    }


def capture_scoreboard_gui(
    artifacts: Path, recorder: PromoRecorder | None = None
) -> dict[str, object]:
    # Settlement schedules the summary one game-day after calibration. Dismiss it
    # before opening the board so a late event cannot cover the GUI evidence.
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    result_title = acceptance.find_ocr_text(
        image, "你主持的考核", PROMO_EVENT_TITLE_REGION, contains=True
    )
    if result_title is None:
        acceptance.set_speed_five_and_unpause(
            artifacts, "zg361_result_summary", require_progress=False
        )
        settle_promo_interruptions(
            artifacts,
            "07_result_summary_preemption",
            observation_s=30.0,
            stop_event_title="你主持的考核",
        )
    acceptance.wait_for_ocr_text(
        "你主持的考核",
        PROMO_EVENT_TITLE_REGION,
        15,
        artifacts,
        "07_result_summary.png",
        contains=True,
        stable_hits=1,
    )
    result_option = acceptance.wait_for_ocr_text(
        "知道了",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "07_result_summary_option.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(result_option, "production review result summary")
    time.sleep(0.8)

    # Deliberately hold the native Decisions drawer open and prove that the
    # additive HUD toggle is suppressed.  The old layout rendered the 180x44
    # button on top of this drawer, hiding decision content and stealing input.
    isolated.ensure_decisions_panel(artifacts, "07_scoreboard_overlay_gate")
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "决议", DECISIONS_HEADER_REGION, contains=True
    ) is None:
        image.save(artifacts / "timeout_07_scoreboard_right_panel_gate.png")
        raise acceptance.RunnerError(
            "native Decisions drawer was not open for scoreboard overlay gate"
        )
    if acceptance.find_ocr_text(
        image, "考核榜", acceptance.FULL_SCREEN_REGION, contains=False
    ) is not None:
        image.save(artifacts / "red_07_scoreboard_overlays_right_panel.png")
        raise acceptance.RunnerError(
            "performance-board HUD toggle overlaps a native right-side panel"
        )
    image.save(artifacts / "07_scoreboard_hidden_by_right_panel.png")
    right_panel_close_method = close_native_decisions_panel(
        artifacts, "07_scoreboard_right_panel"
    )
    button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        20,
        artifacts,
        "07_scoreboard_button.png",
        contains=True,
        stable_hits=1,
    )
    screen_width, screen_height = acceptance.pyautogui.size()
    button_center_normalized = [
        round(button[0] / screen_width, 4),
        round(button[1] / screen_height, 4),
    ]
    acceptance.deliberate_click(button, "production performance-board button")
    acceptance.wait_for_ocr_text(
        "天朝官员考核榜",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "08_scoreboard_title.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.ImageGrab.grab().save(artifacts / "08_scoreboard_panel_raw.png")
    rendered_text = acceptance.wait_for_ocr_tokens(
        (
            "天朝官员考核榜",
            "所辖官员",
            "制度驾驶舱",
            "点击任一官员",
        ),
        ("zg361_scoreboard", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "08_scoreboard_panel",
    )
    cockpit_artifact = None
    if recorder:
        recorder.mark("managed_scoreboard_visible")
        recorder.clean_hold("managed_scoreboard", artifacts)
        cockpit = acceptance.wait_for_ocr_text(
            "制度驾驶舱",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_scoreboard_cockpit_tab.png",
            stable_hits=1,
        )
        acceptance.deliberate_click(cockpit, "production policy-cockpit tab")
        # The 361 reference batch can schedule ordinary product events on the
        # next game day. One may surface over the board between the tab click
        # and OCR (for example "野狗与小白兔"). First prove the clean cockpit;
        # only if that fails do we invoke the conservative event recovery and
        # retry. This prevents cockpit prose from being mistaken for an event.
        cockpit_tokens = ("361 制度账本", "证据质量", "组织信任", "预算压力")
        try:
            acceptance.wait_for_ocr_tokens(
                cockpit_tokens,
                ("zg361_", "localize", "error"),
                acceptance.FULL_SCREEN_REGION,
                6,
                artifacts,
                "08_scoreboard_cockpit",
            )
            cockpit_artifact = "08_scoreboard_cockpit.png"
        except acceptance.RunnerError:
            settle_promo_interruptions(
                artifacts,
                "08_scoreboard_cockpit_recovery",
                observation_s=1.5,
            )
            acceptance.wait_for_ocr_tokens(
                cockpit_tokens,
                ("zg361_", "localize", "error"),
                acceptance.FULL_SCREEN_REGION,
                20,
                artifacts,
                "08_scoreboard_cockpit_recovered",
            )
            cockpit_artifact = "08_scoreboard_cockpit_recovered.png"
        recorder.mark("policy_cockpit_visible")
        recorder.clean_hold("policy_cockpit", artifacts, 3.0)
        managed = acceptance.wait_for_ocr_text(
            "所辖官员",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_scoreboard_managed_tab_return.png",
            stable_hits=1,
        )
        acceptance.deliberate_click(managed, "return to managed scoreboard tab")
        recorder.hold(1.0)
    representative_control_audit = audit_scoreboard_controls(artifacts)
    if recorder:
        recorder.mark("representative_scoreboard_controls_audited")
    return {
        "button_ocr": True,
        "right_panel_suppression_ocr": True,
        "managed_panel_ocr": True,
        "right_panel_suppression_artifact": "07_scoreboard_hidden_by_right_panel.png",
        "right_panel_close_method": right_panel_close_method,
        "button_artifact": "07_scoreboard_button.png",
        "button_center_px": list(button),
        "button_center_normalized": button_center_normalized,
        "button_expected_region": list(SCOREBOARD_BUTTON_REGION),
        "panel_artifact": "08_scoreboard_panel.png",
        "panel_ocr_artifact": "08_scoreboard_panel_ocr.json",
        "normalized_ocr": rendered_text,
        "cockpit_artifact": cockpit_artifact,
        "representative_control_audit": representative_control_audit,
    }


def close_scoreboard_panel(artifacts: Path, stem: str) -> None:
    acceptance.focus_ck3()
    acceptance.pyautogui.press("escape")
    time.sleep(0.8)
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "天朝官员考核榜", acceptance.FULL_SCREEN_REGION, contains=True
    ) is None:
        return
    image.save(artifacts / f"{stem}_scoreboard_after_escape.png")
    width, height = acceptance.pyautogui.size()
    acceptance.deliberate_click(
        (int(width * 0.05), int(height * 0.50)),
        "scoreboard modal backdrop close",
    )
    deadline = time.time() + 6
    while time.time() < deadline:
        image = acceptance.ImageGrab.grab()
        if acceptance.find_ocr_text(
            image,
            "天朝官员考核榜",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        ) is None:
            image.save(artifacts / f"{stem}_scoreboard_closed.png")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    raise acceptance.RunnerError("scoreboard modal did not close")


def pause_after_jingcha_host_click(
    stream: MarkerStream,
    artifacts: Path,
    mandate_day: int,
) -> dict[str, object]:
    """Stop the restored speed-five clock before the delayed switch can race."""

    # The mandate event interrupted a running speed-five timeline. Closing its
    # host option restores that running state, so send the pause key before any
    # planner OCR or transition wait can consume the fixture's two-day margin.
    acceptance.pyautogui.press("space")
    acceptance.ensure_game_paused(artifacts, "09_jingcha_host_immediate")
    paused_image = acceptance.ImageGrab.grab()
    paused_image.save(artifacts / "09_jingcha_host_immediate_pause_verified.png")
    paused_date = acceptance.read_hud_game_date(paused_image)
    if paused_date is None:
        raise acceptance.RunnerError(
            "Jingcha host pause was visible but its HUD date was unreadable"
        )
    paused_day = paused_date[0]
    due_day = mandate_day + JINGCHA_PERSONAL_SWITCH_DELAY_DAYS
    stream.pump()
    personal_switch_marker_count = stream.count(PERSONAL_SWITCH_SCHEDULED_MARKER)
    evidence = {
        "schema_version": 1,
        "result": "GREEN",
        "mandate_day_ordinal": mandate_day,
        "personal_switch_due_day_ordinal": due_day,
        "paused_day_ordinal": paused_day,
        "date_before_due": paused_day < due_day,
        "personal_switch_marker_count": personal_switch_marker_count,
    }
    if personal_switch_marker_count != 0 or paused_day >= due_day:
        evidence["result"] = "RED"
    write_json(artifacts / "09_jingcha_host_immediate_pause_gate.json", evidence)
    if personal_switch_marker_count != 0:
        raise acceptance.RunnerError(
            "personal-result switch raced the immediate Jingcha host pause"
        )
    if paused_day >= due_day:
        raise acceptance.RunnerError(
            "Jingcha host pause reached or crossed the delayed personal-switch due date: "
            f"paused={paused_day}, due={due_day}"
        )
    return evidence


def capture_jingcha_planner(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
) -> dict[str, object]:
    close_scoreboard_panel(artifacts, "09_jingcha")
    stream.wait("ZGA: TEST PASS clean_jingcha_dispatch_scheduled", 30)
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_clean_jingcha_dispatch", require_progress=True
    )
    stream.wait("ZGA: TEST PASS jingcha_mandate_issued", 30)
    stream.wait("ZGA: TEST PASS clean_jingcha_dispatched", 30)
    if stream.count("ZGA: TEST PASS jingcha_mandate_issued") != 1:
        raise acceptance.RunnerError(
            "Jingcha mandate marker must occur exactly once"
        )
    jingcha_interruptions = settle_promo_interruptions(
        artifacts,
        "09_jingcha_mandate_preemption",
        observation_s=20.0,
        stop_event_title="京察之期",
    )
    acceptance.wait_for_ocr_text(
        "京察之期",
        PROMO_EVENT_TITLE_REGION,
        20,
        artifacts,
        "09_jingcha_mandate_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("jingcha_mandate_visible")
        recorder.clean_hold("jingcha_mandate", artifacts)
    host_option = acceptance.wait_for_ocr_text(
        "依例举办京察",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "09_jingcha_host_option.png",
        stable_hits=1,
    )
    mandate_date = acceptance.read_hud_game_date()
    if mandate_date is None:
        raise acceptance.RunnerError(
            "Jingcha mandate HUD date is unreadable before accepting the host option"
        )
    mandate_day = mandate_date[0]
    acceptance.deliberate_click(host_option, "production host Jingcha option")
    host_pause_evidence = pause_after_jingcha_host_click(
        stream, artifacts, mandate_day
    )
    plan_button = acceptance.wait_for_ocr_text(
        "规划京察大计",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "09_jingcha_activity_detail.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(plan_button, "production plan Jingcha activity button")
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("京察大计", "选择京察举办地"),
        ("activity_zg361", "zg361_jingcha_phase", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "09_jingcha_planner",
    )
    if recorder:
        recorder.mark("free_jingcha_planner_visible")
        recorder.clean_hold("free_jingcha_planner", artifacts, 3.0)
    exit_planner = acceptance.wait_for_ocr_text(
        "退出活动规划",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "09_jingcha_exit_planner.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(exit_planner, "native exit activity planning button")
    acceptance.wait_for_ocr_text(
        "放弃京察大计规划",
        acceptance.FULL_SCREEN_REGION,
        10,
        artifacts,
        "09_jingcha_exit_confirmation.png",
        stable_hits=1,
    )
    exit_confirmation = acceptance.wait_for_ocr_text(
        "确认",
        acceptance.FULL_SCREEN_REGION,
        10,
        artifacts,
        "09_jingcha_exit_confirm_button.png",
        stable_hits=1,
    )
    acceptance.click_until_text_disappears(
        exit_confirmation,
        "放弃京察大计规划",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    isolated.wait_for_gameplay_hud(artifacts)
    return {
        "real_mandate_event_path": True,
        "clean_dispatch_scheduled_marker_count": stream.count(
            "ZGA: TEST PASS clean_jingcha_dispatch_scheduled"
        ),
        "clean_dispatch_marker_count": stream.count(
            "ZGA: TEST PASS clean_jingcha_dispatched"
        ),
        "mandate_marker_count": stream.count("ZGA: TEST PASS jingcha_mandate_issued"),
        "planner_opened": True,
        "custom_activity_title_ocr": True,
        "custom_destination_prompt_ocr": True,
        "unrelated_vanilla_activity_catalog_allowed": True,
        "planner_artifact": "09_jingcha_planner.png",
        "planner_ocr_artifact": "09_jingcha_planner_ocr.json",
        "host_pause_gate": host_pause_evidence,
        "preempting_product_events_dismissed": jingcha_interruptions,
        "normalized_ocr": rendered_text,
    }


def capture_superior_assigned_result(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
) -> dict[str, object]:
    # The external fixture schedules only the player-character switch. The
    # former player then becomes the real AI superior and invokes the product
    # review, grade, snapshot and result-event chain.
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_personal_switch", require_progress=True
    )
    stream.wait("ZGA: TEST PASS personal_result_switch_scheduled", 30)
    stream.wait(HISTORICAL_TARGET_DATA_MARKER_PREFIX, 30)
    stream.wait(HISTORICAL_TARGET_PASS_MARKER, 30)
    reviewed_history_id = resolved_historical_personal_result_target(stream)
    if stream.count(HISTORICAL_TARGET_PASS_MARKER) != 1:
        raise acceptance.RunnerError(
            "historical personal-result target PASS marker must occur exactly once"
        )
    if recorder:
        recorder.resolve_reviewed_subject(reviewed_history_id)
    stream.wait(
        "ZGA: TEST PASS personal_result_target_projected_bottom_two", 30
    )
    stream.wait(
        "ZGA: TEST PASS jingcha_refusal_superior_opinion_and_kpi_minus_50", 30
    )
    stream.wait("ZGA: TEST PASS superior_assigned_player_grade", 30)
    stream.wait(
        "ZGA: TEST PASS refusal_reason_consumed_once_by_original_superior", 30
    )
    stream.wait("ZGA: TEST PASS clean_policy_chain_scheduled", 30)
    if stream.count("ZGA: TEST PASS superior_assigned_player_grade") != 1:
        raise acceptance.RunnerError(
            "superior-assigned player grade marker must occur exactly once"
        )
    superior_interruptions = settle_promo_interruptions(
        artifacts,
        "10_superior_result_preemption",
        observation_s=20.0,
        stop_event_title="上司考定",
    )
    acceptance.wait_for_ocr_text(
        "上司考定",
        PROMO_EVENT_TITLE_REGION,
        30,
        artifacts,
        "10_superior_result_title.png",
        contains=True,
        stable_hits=1,
    )
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("上司考定", "你的绩效", "KPI", "同组位次"),
        ("zg361_", "topscope", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "10_superior_result",
    )
    grades = tuple(
        grade for grade in ("3.75", "3.5", "3.25") if grade in rendered_text
    )
    if len(grades) != 1:
        raise acceptance.RunnerError(
            f"personal result must render exactly one grade; OCR={rendered_text}"
        )
    if grades[0] != "3.25":
        raise acceptance.RunnerError(
            "the refusal-reason probe must reach the real 3.25 result branch; "
            f"OCR rendered {grades[0]}"
        )
    if recorder:
        recorder.mark("superior_assigned_325_visible")
        recorder.clean_hold("superior_assigned_325", artifacts, 3.5)
    return {
        "real_superior_review_path": True,
        "reviewed_official_history_id": reviewed_history_id,
        "historical_target_data_marker_count": stream.count(
            HISTORICAL_TARGET_DATA_MARKER_PREFIX
        ),
        "historical_target_pass_marker_count": stream.count(
            HISTORICAL_TARGET_PASS_MARKER
        ),
        "projected_bottom_two_marker_count": stream.count(
            "ZGA: TEST PASS personal_result_target_projected_bottom_two"
        ),
        "clean_policy_chain_scheduled_marker_count": stream.count(
            "ZGA: TEST PASS clean_policy_chain_scheduled"
        ),
        "preempting_product_events_dismissed": superior_interruptions,
        "rendered_grade": grades[0],
        "title_artifact": "10_superior_result_title.png",
        "panel_artifact": "10_superior_result.png",
        "panel_ocr_artifact": "10_superior_result_ocr.json",
        "normalized_ocr": rendered_text,
    }


def capture_received_scoreboard(
    artifacts: Path, recorder: PromoRecorder
) -> dict[str, object]:
    # The manager-facing result summary (zg361.1) has a passive "知道了"
    # close button.  The real subordinate-facing 3.25 result (zg361.4) instead
    # requires one of four responses.  Choose the side-effect-minimal acceptance
    # branch so the modal closes without opening an appeal or another event.
    result_option = acceptance.wait_for_ocr_text(
        "认命",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "11_superior_result_accept_option.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(result_option, "accept real 3.25 result")
    deadline = time.time() + 8
    last_image = None
    while time.time() < deadline:
        last_image = acceptance.ImageGrab.grab()
        if acceptance.find_ocr_text(
            last_image, "上司考定", acceptance.FULL_SCREEN_REGION, contains=True
        ) is None:
            last_image.save(artifacts / "11_superior_result_accepted.png")
            break
        time.sleep(acceptance.POLL_INTERVAL_S)
    else:
        if last_image is not None:
            last_image.save(artifacts / "timeout_11_superior_result_accept.png")
        raise acceptance.RunnerError("real 3.25 result response was not accepted")
    isolated.wait_for_gameplay_hud(artifacts)
    # The result event resumes the speed that was active before it appeared.
    # Pause immediately so unrelated court events cannot grow over the
    # scoreboard while the promo recorder holds a clean shot.
    acceptance.ensure_game_paused(artifacts, "11_received_result")
    settle_promo_interruptions(artifacts, "11_received_before_board")
    button = acceptance.wait_for_ocr_text(
        "考核榜",
        SCOREBOARD_BUTTON_REGION,
        20,
        artifacts,
        "11_received_scoreboard_button.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(button, "open received performance board")
    # A native event can already be queued while the result event is closing.
    # Observe again after the board opens so a late event is dismissed while
    # the intended board remains underneath it.
    settle_promo_interruptions(
        artifacts,
        "11_received_after_board_open",
        observation_s=2.5,
    )
    rendered_text = acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "本人所属考核单元", "3.25"),
        ("zg361_", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "11_received_scoreboard",
    )
    recorder.mark("received_scoreboard_with_325_visible")
    recorder.clean_hold("received_scoreboard_with_325", artifacts, 3.0)
    # This historical official has a received scoreboard but does not inherit
    # the emperor's mechanism ledger. Exercise the distinct received-tab button
    # in-place (an intentional idempotent click) without assuming the system tab
    # is available on this character.
    received_tab = acceptance.wait_for_ocr_text(
        "本人所属考核单元",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "11_received_tab_button.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(
        received_tab, "received performance-board tab blocker audit"
    )
    acceptance.wait_for_ocr_tokens(
        ("天朝官员考核榜", "本人所属考核单元", "3.25"),
        ("zg361_", "localize", "error"),
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "11_received_tab_reopened",
    )
    settle_promo_interruptions(artifacts, "11_received_before_close")
    close_scoreboard_panel(artifacts, "11_received")
    settle_promo_interruptions(artifacts, "11_received_after_close")
    acceptance.ensure_game_paused(artifacts, "11_received_policy_setup")
    return {
        "received_panel_artifact": "11_received_scoreboard.png",
        "received_tab_clicked_live": True,
        "received_tab_idempotent_reopen_live": True,
        "received_tab_reopened_artifact": "11_received_tab_reopened.png",
        "normalized_ocr": rendered_text,
    }


def promo_event_modal_evidence(
    items: list[dict[str, object]], width: int, height: int
) -> bool:
    """Require both a title and narrative body before treating UI as an event.

    The performance board itself has lower rows in the same lane as classic
    event options.  Requiring a wide narrative line in the event body keeps the
    generic option ranker from ever clicking an ordinary board row.
    """
    title = any(
        # CK3 character-event titles occupy the left half of the classic
        # modal. The centered performance-board and cockpit headings must not
        # satisfy this test even though they also have long explanatory text.
        PROMO_EVENT_TITLE_REGION[0]
        <= item["center"][0] / width
        < PROMO_EVENT_TITLE_REGION[2]
        and PROMO_EVENT_TITLE_REGION[1]
        <= item["center"][1] / height
        <= PROMO_EVENT_TITLE_REGION[3]
        and (item["bbox"][2] - item["bbox"][0]) / width >= 0.055
        for item in items
    )
    narrative = any(
        0.20 <= item["center"][0] / width <= 0.76
        and 0.27 <= item["center"][1] / height <= 0.58
        and (item["bbox"][2] - item["bbox"][0]) / width >= 0.10
        for item in items
    )
    return title and narrative


def promo_event_title_evidence(
    items: list[dict[str, object]],
    width: int,
    height: int,
    expected_title: str,
) -> bool:
    """Prove the expected event title is visibly on top, not in pause text."""

    expected = _normalize_promo_visible_text(expected_title)
    return bool(expected) and any(
        PROMO_EVENT_TITLE_REGION[0]
        <= item["center"][0] / width
        <= PROMO_EVENT_TITLE_REGION[2]
        and PROMO_EVENT_TITLE_REGION[1]
        <= item["center"][1] / height
        <= PROMO_EVENT_TITLE_REGION[3]
        and expected
        in _normalize_promo_visible_text(str(item.get("text", "")))
        for item in items
    )


def promo_preferred_product_event_option(
    items: list[dict[str, object]],
    width: int,
    height: int,
) -> tuple[str | None, dict[str, object] | None]:
    """Select an explicitly non-destructive option for a known product event."""

    for event_title, option_text in PROMO_PREFERRED_PRODUCT_EVENT_OPTIONS:
        if not promo_event_title_evidence(items, width, height, event_title):
            continue
        expected = _normalize_promo_visible_text(option_text)
        matches = [
            item
            for item in items
            if 0.18 <= item["center"][0] / width <= 0.75
            and 0.55 <= item["center"][1] / height <= 0.85
            and expected
            in _normalize_promo_visible_text(str(item.get("text", "")))
        ]
        if len(matches) != 1:
            return event_title, None
        return event_title, matches[0]
    return None, None


def promo_product_event_overlay_evidence(
    label: str,
    items: list[dict[str, object]],
    width: int,
    height: int,
) -> bool:
    """Reject event-shaped UI over the otherwise clean native planner span."""

    return label == "free_jingcha_planner" and promo_event_modal_evidence(
        items, width, height
    )


def _write_promo_interruption_decision(
    artifacts: Path,
    stem: str,
    *,
    status: str,
    kind: str | None,
    selected: dict[str, object] | None,
) -> None:
    write_json(
        artifacts / f"{stem}_decision.json",
        {
            "schema_version": 1,
            "scope": "promo_fixture_only",
            "status": status,
            "recovery_kind": kind,
            "selected_text": selected.get("text") if selected else None,
            "selected_center": selected.get("center") if selected else None,
            "allow_succession": False,
        },
    )


def settle_promo_interruptions(
    artifacts: Path,
    stem: str,
    *,
    observation_s: float = PROMO_INTERRUPTION_DEFAULT_OBSERVE_S,
    max_dismissals: int = PROMO_INTERRUPTION_MAX_DISMISSALS,
    stop_event_title: str | None = None,
) -> list[dict[str, object]]:
    """Conservatively settle bounded native events in the promo fixture only.

    Every actual or rejected recovery gets a full screenshot, OCR JSON,
    annotated candidate image, and decision sidecar.  Succession is always
    blocked.  Event-like UI without a strongly classified option is an
    immediate RED; non-event UI is merely observed and never clicked.
    """
    if max_dismissals < 1:
        raise ValueError("max_dismissals must be positive")
    deadline = time.monotonic() + max(0.0, observation_s)
    dismissed: list[dict[str, object]] = []
    while True:
        acceptance.focus_ck3()
        image = acceptance.ImageGrab.grab()
        items = acceptance.ocr_box_results(
            image, acceptance.FULL_SCREEN_REGION
        )
        width, height = image.size
        if stop_event_title and promo_event_title_evidence(
            items, width, height, stop_event_title
        ):
            image.save(artifacts / f"{stem}_target_event_visible.png")
            return dismissed

        preferred_event, preferred_selected = promo_preferred_product_event_option(
            items, width, height
        )
        lower, selected = acceptance.select_stall_recovery(
            items, image, allow_succession=False
        )
        if preferred_event is not None:
            if preferred_selected is None:
                diagnostic = f"{stem}_known_event_safe_option_missing"
                acceptance.mark_recovery_items(items, lower, None)
                acceptance.write_recovery_bundle(
                    image, items, artifacts, diagnostic
                )
                _write_promo_interruption_decision(
                    artifacts,
                    diagnostic,
                    status="blocked_known_event_safe_option_missing",
                    kind=preferred_event,
                    selected=None,
                )
                raise acceptance.RunnerError(
                    "known promo product event lacks its non-destructive option: "
                    f"{preferred_event}"
                )
            selected = preferred_selected
        succession_lower: list[dict[str, object]] = []
        succession = None
        if selected is None:
            succession_lower, succession = acceptance.select_stall_recovery(
                items, image, allow_succession=True
            )
        if (
            succession is not None
            and succession.get("layout_fallback") == "succession_continue"
        ):
            diagnostic = f"{stem}_interruption_blocked_succession"
            acceptance.mark_recovery_items(
                items, succession_lower, None
            )
            acceptance.write_recovery_bundle(
                image, items, artifacts, diagnostic
            )
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_succession",
                kind="succession_continue",
                selected=None,
            )
            raise acceptance.RunnerError(
                "promo interruption is succession; automatic continuation is forbidden"
            )

        if not promo_event_modal_evidence(items, width, height):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return dismissed
            time.sleep(min(acceptance.POLL_INTERVAL_S, remaining))
            continue

        kind = (
            acceptance.quick_recovery_kind(items, selected, width, height)
            if selected is not None
            else None
        )
        ordinal = len(dismissed) + 1
        diagnostic = f"{stem}_interruption_{ordinal:02d}"
        acceptance.mark_recovery_items(items, lower, selected)
        acceptance.write_recovery_bundle(image, items, artifacts, diagnostic)
        if selected is None or kind is None:
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_unknown_modal",
                kind=kind,
                selected=selected,
            )
            raise acceptance.RunnerError(
                "promo interruption looks like an event but has no safe option; "
                f"inspect {diagnostic}.png"
            )
        if len(dismissed) >= max_dismissals:
            _write_promo_interruption_decision(
                artifacts,
                diagnostic,
                status="blocked_dismissal_limit",
                kind=kind,
                selected=selected,
            )
            raise acceptance.RunnerError(
                f"promo interruption exceeded {max_dismissals} bounded dismissals"
            )

        _write_promo_interruption_decision(
            artifacts,
            diagnostic,
            status="selected_safe_event_option",
            kind=kind,
            selected=selected,
        )
        acceptance.deliberate_click(
            tuple(selected["center"]),
            f"promo fixture interruption {kind}: {selected['text']!r}",
        )
        selected_text = selected["text"]
        selected_center = selected["center"]
        close_deadline = time.monotonic() + 8
        while time.monotonic() < close_deadline:
            time.sleep(acceptance.POLL_INTERVAL_S)
            after = acceptance.ImageGrab.grab()
            after_items = acceptance.ocr_box_results(
                after, acceptance.FULL_SCREEN_REGION
            )
            still_visible = any(
                item["text"] == selected_text
                and abs(item["center"][0] - selected_center[0]) <= 30
                and abs(item["center"][1] - selected_center[1]) <= 20
                for item in after_items
            )
            if not still_visible:
                after.save(artifacts / f"{diagnostic}_dismissed.png")
                dismissed.append(
                    {
                        "kind": kind,
                        "selected_text": selected_text,
                        "selected_center": selected_center,
                        "diagnostic_stem": diagnostic,
                    }
                )
                acceptance.ensure_game_paused(
                    artifacts, f"{diagnostic}_dismissed"
                )
                deadline = time.monotonic() + max(0.0, observation_s)
                break
        else:
            after.save(artifacts / f"timeout_{diagnostic}.png")
            raise acceptance.RunnerError(
                f"promo interruption option did not disappear: {diagnostic}"
            )


def capture_policy_cards(
    stream: MarkerStream,
    artifacts: Path, recorder: PromoRecorder
) -> list[dict[str, object]]:
    captured: list[dict[str, object]] = []
    for mechanism_id, _decision_title, event_title, option_text in PROMO_POLICY_CARDS:
        stem = f"12_policy_{mechanism_id:03d}"
        settle_promo_interruptions(artifacts, f"{stem}_preflight")
        acceptance.ensure_game_paused(artifacts, f"{stem}_preflight")
        acceptance.set_speed_five_and_unpause(
            artifacts,
            f"zg361_clean_policy_{mechanism_id:03d}",
            require_progress=True,
        )
        dispatch_marker = (
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        stream.wait(dispatch_marker, 30)
        settle_promo_interruptions(
            artifacts,
            f"{stem}_preemption",
            observation_s=20.0,
            stop_event_title=event_title,
        )
        acceptance.wait_for_ocr_text(
            event_title,
            PROMO_EVENT_TITLE_REGION,
            20,
            artifacts,
            f"{stem}_event.png",
            contains=True,
            stable_hits=1,
        )
        recorder.mark(f"policy_card_{mechanism_id:03d}_visible")
        recorder.clean_hold(
            f"policy_card_{mechanism_id:03d}", artifacts, 2.5
        )
        option = acceptance.wait_for_ocr_text(
            option_text,
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            f"{stem}_option.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.deliberate_click(option, f"close policy card {mechanism_id:03d}")
        isolated.wait_for_gameplay_hud(artifacts)
        acceptance.ensure_game_paused(artifacts, f"{stem}_closed")
        captured.append(
            {
                "mechanism_id": mechanism_id,
                "event_artifact": f"{stem}_event.png",
                "dispatch_marker": dispatch_marker,
                "clean_span_id": f"policy_card_{mechanism_id:03d}",
            }
        )
    acceptance.set_speed_five_and_unpause(
        artifacts, "zg361_clean_policy_chain_completion", require_progress=True
    )
    stream.wait("ZGA: TEST PASS clean_policy_chain_completed", 30)
    acceptance.ensure_game_paused(artifacts, "12_policy_chain_completed")
    policy_markers = {
        f"{mechanism_id:03d}": stream.count(
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        for mechanism_id, *_ in PROMO_POLICY_CARDS
    }
    all_six_count = stream.count(
        "ZGA: TEST PASS clean_policy_chain_all_six_dispatched"
    )
    completion_count = stream.count("ZGA: TEST PASS clean_policy_chain_completed")
    if any(count != 1 for count in policy_markers.values()):
        raise acceptance.RunnerError(
            f"clean policy dispatch markers must each occur once: {policy_markers}"
        )
    if all_six_count != 1 or completion_count != 1:
        raise acceptance.RunnerError(
            "clean policy persistence markers must each occur once: "
            f"all_six={all_six_count}, completion={completion_count}"
        )
    return captured


def run_scenario(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
) -> dict[str, object]:
    initialize_fixture(stream, artifacts)
    if recorder:
        # The one visible fixture decision is allowed only before recording.
        # Close its native drawer and prove a clean HUD before FFmpeg starts;
        # subsequent fixture coordination is hidden and time-delayed.
        close_native_decisions_panel(artifacts, "05_promo_pre_record")
        assert_promo_frame_clean(
            artifacts,
            "05_promo_pre_record_clean_hud",
            label="pre_record_hud",
            phase="pre_record",
        )
        recorder.start()
        recorder.hold(2.0)
    choose_direct_publication(stream, artifacts, recorder)
    gui_evidence = capture_scoreboard_gui(artifacts, recorder)
    jingcha_evidence = capture_jingcha_planner(stream, artifacts, recorder)
    personal_result_evidence = capture_superior_assigned_result(
        stream, artifacts, recorder
    )
    received_evidence = None
    policy_cards: list[dict[str, object]] = []
    if recorder:
        received_evidence = capture_received_scoreboard(artifacts, recorder)
        policy_cards = capture_policy_cards(stream, artifacts, recorder)
        recorder.mark("all_requested_product_screens_captured")
        recorder.hold(2.0)
    counts = stream.counts()
    constructor_counts = fixture_constructor_counts()
    policy_dispatch_counts = {
        f"{mechanism_id:03d}": stream.count(
            f"ZGA: TEST PASS clean_policy_{mechanism_id:03d}_dispatched"
        )
        for mechanism_id, *_ in PROMO_POLICY_CARDS
    }
    reviewed_history_id = str(
        personal_result_evidence["reviewed_official_history_id"]
    )
    return {
        "standard_lobby_start": True,
        "player_history_id": EXPECTED_PLAYER_HISTORY_ID,
        "reviewed_official_history_id": reviewed_history_id,
        "real_character_provenance": (
            recorder.real_character_provenance
            if recorder
            else promo_real_character_provenance(reviewed_history_id)
        ),
        "fixture_constructor_counts": constructor_counts,
        "historical_subjects_manufactured_by_fixture": bool(
            any(constructor_counts.values())
        ),
        "test_decisions_visible_inside_clean_spans": 0 if recorder else None,
        "native_decisions_drawer_visible_inside_clean_spans": 0 if recorder else None,
        "real_character_runtime_attestation": {
            "song_emperor_exact_build_marker_count": stream.count(
                "ZGA: TEST PASS exact_build_song_emperor"
            ),
            "song_emperor_player_switch_marker_count": stream.count(
                "ZGA: TEST PASS switched_to_song_emperor"
            ),
            "reviewed_official_history_id": reviewed_history_id,
            "historical_target_data_marker_count": stream.count(
                HISTORICAL_TARGET_DATA_MARKER_PREFIX
            ),
            "historical_target_pass_marker_count": stream.count(
                HISTORICAL_TARGET_PASS_MARKER
            ),
            "projected_bottom_two_marker_count": stream.count(
                "ZGA: TEST PASS personal_result_target_projected_bottom_two"
            ),
            "resolved_subject_superior_grade_marker_count": stream.count(
                "ZGA: TEST PASS superior_assigned_player_grade"
            ),
        },
        "song_emperor_celestial": True,
        "song_emperor_independent_sample": True,
        "review_liege_minimum_tier": "duchy",
        "independence_required_for_review_entry": False,
        "non_independent_celestial_liege_entry": True,
        "direct_governor_cohort_at_least_three": True,
        "newcomer_first_review_ranked_and_protected_from_325": True,
        "calibration_c_all_newcomer_noop": True,
        "calibration_c_mixed_newcomer_atomic_swap": True,
        "pending_and_settled_review_idempotence": True,
        "grade_325_fixed_penalty_receipts_and_appeal_refund": True,
        "salary_penalty_contract": "one-year -25%; appeal stops future reduction; elapsed salary is not backdated",
        "real_review_effect_invocations_minimum": 2,
        "mechanism_batch": {
            "fixture_cases_passed": sum(
                "ZGA: MECHANISM CASE PASS" in line for line in stream.lines
            ),
            "product_choice_effects_applied": sum(
                "ZG361M: CASE" in line and "APPLIED" in line
                for line in stream.lines
            ),
            "portfolio_ledger_verified": bool(
                stream.count("ZGA: MECHANISM LEDGER PASS")
            ),
            "portfolio_idempotence_verified": bool(
                stream.count("ZGA: MECHANISM IDEMPOTENCE PASS")
            ),
        },
        "calibration_choice": "zg361.10.a direct publication",
        "managed_scoreboard_counts_from_row_markers": counts,
        "ai_non_independent_full_review": bool(
            stream.count("ZGA: TEST PASS ai_non_independent_full_review")
        ),
        "ai_non_independent_probe_unavailable": bool(
            stream.count("ZGA: TEST INFO ai_non_independent_review_candidate_unavailable")
        ),
        "ai_small_cohort_neutral_settlement": bool(
            stream.count("ZGA: TEST PASS ai_small_cohort_neutral_settlement")
        ),
        "ai_small_cohort_probe_unavailable": bool(
            stream.count("ZGA: TEST INFO ai_small_cohort_candidate_unavailable")
        ),
        "scoreboard_gui": gui_evidence,
        "jingcha_planner": jingcha_evidence,
        "jingcha_refusal": {
            "superior_opinion_modifier": True,
            "next_review_kpi_malus": -50,
            "consumed_by_original_superior_once": True,
        },
        "superior_assigned_player_result": personal_result_evidence,
        "promo_received_scoreboard": received_evidence,
        "promo_policy_cards": policy_cards,
        "promo_policy_chain": {
            "dispatch_marker_counts": policy_dispatch_counts,
            "all_six_dispatched_marker_count": stream.count(
                "ZGA: TEST PASS clean_policy_chain_all_six_dispatched"
            ),
            "completion_marker_count": stream.count(
                "ZGA: TEST PASS clean_policy_chain_completed"
            ),
            "persisted_choices_verified": bool(
                recorder
                and stream.count("ZGA: TEST PASS clean_policy_chain_completed") == 1
            ),
        },
    }


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if not logs.is_dir():
        return
    for path in sorted(item for item in logs.iterdir() if item.is_file()):
        shutil.copy2(path, artifacts / f"final_{path.name}")


def run_cell(
    artifacts: Path,
    userdir: Path,
    keep_userdir: bool,
    promo_capture: bool = False,
    runtime_source: Path = SOURCE,
    runtime_identity: dict[str, object] | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    userdir.mkdir(parents=True)
    runtime_source = Path(runtime_source).resolve()
    runtime_identity = dict(runtime_identity or {})
    source_before = isolated.tree_snapshot(SOURCE)
    runtime_source_before = isolated.tree_snapshot(runtime_source)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = bootstrap_userdir(userdir, runtime_source)
    process = None
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    diagnostics: list[str] = []
    observed_engine_warnings: list[str] = []
    mount_order: list[str] = []
    game_version = isolated.installed_game_version()
    executable_before = isolated.sha256_file(acceptance.CK3_EXE)
    executable_after = None
    runtime_after: dict[str, str] = {}
    runtime_unchanged = False
    source_unchanged = False
    runtime_source_unchanged = False
    stream = MarkerStream(userdir / "logs" / "debug.log")
    pid_path = artifacts / "ck3.pid"
    watchdog_pid = None
    recorder = PromoRecorder(artifacts / "promo") if promo_capture else None
    recorder_evidence: dict[str, object] = {}
    try:
        if executable_before != EXPECTED_EXE_SHA256:
            raise acceptance.RunnerError(
                f"CK3 executable SHA-256 drifted before launch: {executable_before}"
            )
        watchdog_pid = acceptance.start_process_watchdog(pid_path)
        process = acceptance.launch_ck3_process(False)
        pid_path.write_text(str(process.pid), encoding="ascii")
        log(f"launched tracked CK3 PID {process.pid}")
        acceptance.wait_for_ocr_text(
            "新游戏",
            acceptance.MAIN_MENU_REGION,
            BOOT_TIMEOUT_S,
            artifacts,
            "01_main_menu_parser_ready.png",
            stable_hits=1,
        )
        mount_order = verify_runtime_load_order(userdir, bootstrap)
        new_diagnostics, new_warnings = project_diagnostics(
            userdir, artifacts, "02_main_menu"
        )
        diagnostics.extend(new_diagnostics)
        observed_engine_warnings.extend(new_warnings)
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        isolated.dismiss_external_main_menu_popup(artifacts)
        acceptance.navigate_lobby(artifacts)
        isolated.wait_for_gameplay_hud(artifacts)
        acceptance.ensure_game_paused(artifacts, "04_standard_1066_start")
        evidence = run_scenario(stream, artifacts, recorder)
        new_diagnostics, new_warnings = project_diagnostics(
            userdir, artifacts, "10_runtime"
        )
        diagnostics.extend(new_diagnostics)
        observed_engine_warnings.extend(new_warnings)
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        if process.poll() is not None:
            raise acceptance.RunnerError(
                f"CK3 PID {process.pid} exited before controlled shutdown"
            )
        result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"FATAL {error}")
        if isinstance(error, Exception) and not isinstance(error, acceptance.RunnerError):
            traceback.print_exc()
        try:
            acceptance.focus_ck3()
            acceptance.ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
    finally:
        if recorder is not None and recorder.process is not None:
            try:
                recorder_evidence = recorder.stop()
            except Exception as error:
                result = "RED"
                reason = f"promo recorder stop failed: {error}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason
        if process is not None:
            try:
                acceptance.stop_ck3_process(
                    process, pid_path, require_running=result == "GREEN"
                )
            except Exception as error:
                result = "RED"
                reason = f"controlled stop failed: {error}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            if result == "GREEN":
                stream.validate(final=True)
            else:
                stream.pump(final=True)
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            version_after = isolated.installed_game_version()
            executable_after = isolated.sha256_file(acceptance.CK3_EXE)
            if (
                game_version != EXPECTED_GAME_VERSION
                or version_after != EXPECTED_GAME_VERSION
                or executable_before != EXPECTED_EXE_SHA256
                or executable_after != EXPECTED_EXE_SHA256
            ):
                raise acceptance.RunnerError(
                    "fixed CK3 1.19.0.6 executable contract changed during acceptance"
                )
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            new_diagnostics, new_warnings = project_diagnostics(
                userdir, artifacts, "11_shutdown"
            )
            diagnostics.extend(new_diagnostics)
            observed_engine_warnings.extend(new_warnings)
            copy_logs(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            runtime_unchanged = True
            for key, target in bootstrap["targets"].items():
                snapshot = isolated.tree_snapshot(target)
                runtime_after[key] = isolated.snapshot_digest(snapshot)
                if snapshot != bootstrap["tree_snapshots"][key]:
                    runtime_unchanged = False
            source_unchanged = isolated.tree_snapshot(SOURCE) == source_before
            runtime_source_unchanged = (
                isolated.tree_snapshot(runtime_source) == runtime_source_before
            )
            if not runtime_unchanged or not source_unchanged or not runtime_source_unchanged:
                raise acceptance.RunnerError("CK3 rewrote a runtime or source tree")
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason

    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(userdir)
            userdir_removed = not userdir.exists()
            if not userdir_removed:
                raise OSError(f"userdir still exists: {userdir}")
        except Exception as error:
            result = "RED"
            reason = f"userdir cleanup failed: {error}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
    elif userdir.exists():
        log(f"retained userdir at {userdir}")

    report = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "game_version": game_version,
        "expected_ck3_executable_sha256": EXPECTED_EXE_SHA256,
        "ck3_executable_before_sha256": executable_before,
        "ck3_executable_after_sha256": executable_after,
        "debug_mode": False,
        "isolated_userdir": True,
        "enabled_mods": bootstrap["enabled_mods"],
        "verified_mount_order": mount_order,
        "product_runtime_manifest": bootstrap["manifest"],
        "runtime_tree_before_sha256": bootstrap["tree_sha256"],
        "runtime_tree_after_sha256": runtime_after,
        "runtime_trees_unchanged": runtime_unchanged,
        "source_tree_unchanged": source_unchanged,
        "runtime_source_tree_unchanged": runtime_source_unchanged,
        **runtime_identity,
        "fixture_markers": stream.lines,
        "project_diagnostics": list(dict.fromkeys(diagnostics)),
        "observed_nonblocking_engine_warnings": list(
            dict.fromkeys(observed_engine_warnings)
        ),
        "scenario_evidence": evidence,
        "promo_capture": recorder_evidence,
        "isolated_userdir_path": str(userdir),
        "userdir_removed_after_run": userdir_removed,
        "process_watchdog_pid": watchdog_pid,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": (
                f"{acceptance.pyautogui.size().width}x"
                f"{acceptance.pyautogui.size().height}"
            ),
        },
    }
    write_json(artifacts / "report.json", report)
    return report


def main(
    artifacts_dir: str | None = None,
    keep_userdir: bool = True,
    preflight_only: bool = False,
    promo_capture: bool = False,
    workshop_cache_source: str | None = None,
    workshop_manifest: str | None = None,
) -> int:
    runtime_source = (
        Path(workshop_cache_source).expanduser().resolve()
        if workshop_cache_source
        else SOURCE.resolve()
    )
    manifest_path = (
        Path(workshop_manifest).expanduser().resolve()
        if workshop_manifest
        else None
    )
    runtime_identity = preflight(runtime_source, manifest_path)
    if preflight_only:
        print("ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
        if not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                f"artifact parent does not exist: {artifacts.parent}"
            )
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        artifacts = RUNS_ROOT / f"zga_{stamp}_{uuid.uuid4().hex[:8]}"
    userdir = artifacts.with_name(artifacts.name + "_userdir")
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe((artifacts, userdir), steam_root, workshop_roots)
    protected_before = isolated.protected_snapshot(steam_root)
    artifacts.mkdir()
    report = run_cell(
        artifacts / "cell",
        userdir,
        keep_userdir,
        promo_capture=promo_capture,
        runtime_source=runtime_source,
        runtime_identity=runtime_identity,
    )
    result = report["result"]
    error_reason = report["error_reason"]
    protected_unchanged = False
    try:
        isolated.verify_protected_storage(
            protected_before,
            steam_root,
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
        )
        protected_unchanged = True
    except BaseException as error:
        result = "RED"
        reason = str(error) or type(error).__name__
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": (
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" and protected_unchanged else 0
        ),
    }
    write_json(artifacts / "report.json", matrix)
    write_evidence_index(artifacts, matrix)
    print("\n===== ZHONGGUO 361 ACCEPTANCE =====")
    print(f"cell                    {report['result']}")
    print(
        "protected storage       "
        + ("UNCHANGED" if protected_unchanged else "UNPROVEN")
    )
    print(f"artifacts               {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument(
        "--discard-userdir",
        action="store_true",
        help="delete the isolated userdir after GREEN; default preserves all process material",
    )
    parser.add_argument("--preflight", action="store_true", help="do not launch CK3")
    parser.add_argument(
        "--promo-capture",
        action="store_true",
        help="record an append-only post-loading gameplay take and extra product UI",
    )
    parser.add_argument(
        "--workshop-cache-source",
        help="verified fresh CK3 Workshop cache leaf used instead of the development source",
    )
    parser.add_argument(
        "--workshop-manifest",
        help="formal ID-bearing release manifest used to verify --workshop-cache-source",
    )
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                artifacts_dir=arguments.artifacts_dir,
                keep_userdir=not arguments.discard_userdir,
                preflight_only=arguments.preflight,
                promo_capture=arguments.promo_capture,
                workshop_cache_source=arguments.workshop_cache_source,
                workshop_manifest=arguments.workshop_manifest,
            )
        )
    except acceptance.RunnerError as error:
        print(f"ZHONGGUO 361 ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
