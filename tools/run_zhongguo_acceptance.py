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
import uuid
from pathlib import Path

import run_acceptance as acceptance
import build_mod_zhongguo_style_release as release
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_zhongguo_style"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
# CK3 writes into its -userdir. Keep both the evidence bundle and complete
# writable profile durable but outside the repository/protected real profile.
RUNS_ROOT = ROOT.parent / f"{ROOT.name}_process_assets" / "zg361" / "runs"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
EXPECTED_PLAYER_HISTORY_ID = "han_8052"
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
        payload = {
            "schema": 1,
            "started_at_utc": self.started_at_utc,
            "exclude_ck3_loading": True,
            "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
            "raw_path": str(self.raw_path),
            "raw_bytes": self.raw_path.stat().st_size,
            "raw_sha256": isolated.sha256_file(self.raw_path),
            "ffmpeg_log": str(self.log_path),
            "marks": self.marks,
        }
        write_json(self.timeline_path, payload)
        self.process = None
        return payload


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


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
        "personal_result_target_selected_from_prior_tail",
        "order_by = var:zg361_rank",
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
        for marker in REQUIRED_FIXTURE_MARKERS:
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
    acceptance.wait_for_ocr_text(
        "绩效校准会议",
        acceptance.FULL_SCREEN_REGION,
        60,
        artifacts,
        "06_calibration_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("calibration_event_visible")
        recorder.hold()
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


def capture_scoreboard_gui(
    artifacts: Path, recorder: PromoRecorder | None = None
) -> dict[str, object]:
    # Settlement schedules the summary one game-day after calibration. Dismiss it
    # before opening the board so a late event cannot cover the GUI evidence.
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    result_option = acceptance.find_ocr_text(
        image, "知道了", acceptance.FULL_SCREEN_REGION, contains=True
    )
    if result_option is None:
        acceptance.set_speed_five_and_unpause(
            artifacts, "zg361_result_summary", require_progress=False
        )
        result_option = acceptance.wait_for_ocr_text(
            "知道了",
            acceptance.FULL_SCREEN_REGION,
            30,
            artifacts,
            "07_result_summary.png",
            contains=True,
            stable_hits=1,
        )
    else:
        image.save(artifacts / "07_result_summary.png")
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
        recorder.hold()
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
        # next game day.  One may surface over the board between the tab click
        # and OCR (for example "野狗与小白兔").  Resolve only a positively
        # identified native event, then prove the cockpit underneath; never
        # treat an overlaid modal as a missing or broken tab.
        settle_promo_interruptions(
            artifacts,
            "08_scoreboard_cockpit",
            observation_s=3.5,
        )
        acceptance.wait_for_ocr_tokens(
            ("361 制度账本", "证据质量", "组织信任", "预算压力"),
            ("zg361_", "localize", "error"),
            acceptance.FULL_SCREEN_REGION,
            20,
            artifacts,
            "08_scoreboard_cockpit",
        )
        cockpit_artifact = "08_scoreboard_cockpit.png"
        recorder.mark("policy_cockpit_visible")
        recorder.hold(3.0)
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


def capture_jingcha_planner(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
) -> dict[str, object]:
    close_scoreboard_panel(artifacts, "09_jingcha")
    confirm = isolated.open_decision_detail(
        "验收免费京察规划器",
        "发出京察召集令",
        artifacts,
        "09_jingcha_mandate",
    )
    acceptance.click_until_text_disappears(
        confirm,
        "发出京察召集令",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    stream.wait("ZGA: TEST PASS jingcha_mandate_issued", 30)
    if stream.count("ZGA: TEST PASS jingcha_mandate_issued") != 1:
        raise acceptance.RunnerError(
            "Jingcha mandate marker must occur exactly once"
        )
    acceptance.wait_for_ocr_text(
        "京察之期",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "09_jingcha_mandate_event.png",
        contains=True,
        stable_hits=1,
    )
    if recorder:
        recorder.mark("jingcha_mandate_visible")
        recorder.hold()
    host_option = acceptance.wait_for_ocr_text(
        "依例举办京察",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        "09_jingcha_host_option.png",
        stable_hits=1,
    )
    acceptance.deliberate_click(host_option, "production host Jingcha option")
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
        recorder.hold(3.0)
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
        "planner_opened": True,
        "custom_activity_title_ocr": True,
        "custom_destination_prompt_ocr": True,
        "unrelated_vanilla_activity_catalog_allowed": True,
        "planner_artifact": "09_jingcha_planner.png",
        "planner_ocr_artifact": "09_jingcha_planner_ocr.json",
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
    stream.wait(
        "ZGA: TEST PASS personal_result_target_selected_from_prior_tail", 30
    )
    stream.wait(
        "ZGA: TEST PASS jingcha_refusal_superior_opinion_and_kpi_minus_50", 30
    )
    stream.wait("ZGA: TEST PASS superior_assigned_player_grade", 30)
    stream.wait(
        "ZGA: TEST PASS refusal_reason_consumed_once_by_original_superior", 30
    )
    if stream.count("ZGA: TEST PASS superior_assigned_player_grade") != 1:
        raise acceptance.RunnerError(
            "superior-assigned player grade marker must occur exactly once"
        )
    acceptance.wait_for_ocr_text(
        "上司考定",
        acceptance.FULL_SCREEN_REGION,
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
        recorder.hold(3.5)
    return {
        "real_superior_review_path": True,
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
    recorder.hold(3.0)
    settle_promo_interruptions(artifacts, "11_received_before_close")
    close_scoreboard_panel(artifacts, "11_received")
    settle_promo_interruptions(artifacts, "11_received_after_close")
    acceptance.ensure_game_paused(artifacts, "11_received_policy_setup")
    return {
        "received_panel_artifact": "11_received_scoreboard.png",
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
        0.18 <= item["center"][0] / width <= 0.76
        and 0.10 <= item["center"][1] / height <= 0.36
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

        lower, selected = acceptance.select_stall_recovery(
            items, image, allow_succession=False
        )
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
    artifacts: Path, recorder: PromoRecorder
) -> list[dict[str, object]]:
    captured: list[dict[str, object]] = []
    for mechanism_id, decision_title, event_title, option_text in PROMO_POLICY_CARDS:
        stem = f"12_policy_{mechanism_id:03d}"
        settle_promo_interruptions(artifacts, f"{stem}_preflight")
        acceptance.ensure_game_paused(artifacts, f"{stem}_preflight")
        confirm = isolated.open_decision_detail(
            decision_title,
            "打开此卡",
            artifacts,
            stem,
        )
        acceptance.click_until_text_disappears(
            confirm,
            "打开此卡",
            acceptance.FULL_SCREEN_REGION,
            artifacts,
            attempts=2,
        )
        acceptance.wait_for_ocr_text(
            event_title,
            acceptance.FULL_SCREEN_REGION,
            20,
            artifacts,
            f"{stem}_event.png",
            contains=True,
            stable_hits=1,
        )
        recorder.mark(f"policy_card_{mechanism_id:03d}_visible")
        recorder.hold(2.5)
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
            }
        )
    return captured


def run_scenario(
    stream: MarkerStream,
    artifacts: Path,
    recorder: PromoRecorder | None = None,
) -> dict[str, object]:
    initialize_fixture(stream, artifacts)
    if recorder:
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
        policy_cards = capture_policy_cards(artifacts, recorder)
        recorder.mark("all_requested_product_screens_captured")
        recorder.hold(2.0)
    counts = stream.counts()
    return {
        "standard_lobby_start": True,
        "player_history_id": EXPECTED_PLAYER_HISTORY_ID,
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
