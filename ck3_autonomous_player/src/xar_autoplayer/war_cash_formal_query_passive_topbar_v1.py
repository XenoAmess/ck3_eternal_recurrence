"""Opt-in, append-only topbar diagnostic during a formal selected query.

This module never turns a GUI cache or a query into a cash quote.  The
research sampler uses only PROCESS_QUERY_LIMITED_INFORMATION and
PROCESS_VM_READ and limits each of its two reads to 64 KiB.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

from .m5_observed_opportunity_selector import observed_frame


SCHEMA = "xar.ck3.war-cash-formal-query-passive-topbar.v1"
MAX_READ = 64 * 1024
SAMPLE_NAME = "passive-topbar-raw.json"
RECEIPT_NAME = "passive-topbar-diagnostic.json"
FRAME_KEYS = frozenset({
    "played_character_id", "native_revision", "date_raw",
    "snapshot_id", "revision", "episode_run_id",
})


def _sha256(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdefABCDEF" for char in value))


def _same_frame(candidate: object, other: object) -> bool:
    if not isinstance(candidate, dict) or not isinstance(other, dict):
        return False
    if (candidate.get("status") != "same_paused_query_postcheck_passed"
            or other.get("status") != "same_paused_query_postcheck_passed"):
        return False
    a = candidate.get("source_frame_after")
    b = other.get("source_frame_after")
    try:
        if (set(a) != FRAME_KEYS or set(b) != FRAME_KEYS
                or observed_frame(a) != a or observed_frame(b) != b
                or a != b):
            return False
    except (TypeError, ValueError, KeyError):
        return False
    return (
        candidate.get("source_frame_before") == a == b
        and other.get("source_frame_before") == b
        and type(candidate.get("process_pid")) is int
        and candidate["process_pid"] > 0
        and candidate.get("process_pid") == other.get("process_pid")
        and type(candidate.get("process_created_filetime")) is int
        and candidate["process_created_filetime"] > 0
        and candidate.get("process_created_filetime")
        == other.get("process_created_filetime")
        and type(candidate.get("treasury_after_raw")) is int
        and candidate.get("treasury_after_raw")
        == other.get("treasury_after_raw")
        and _sha256(candidate.get("loaded_game_exe_sha256"))
        and candidate.get("loaded_game_exe_sha256")
        == other.get("loaded_game_exe_sha256")
    )


def _bounded_sample(sample: object, candidate: dict[str, object]) -> bool:
    if not isinstance(sample, dict):
        return False
    diagnostic = sample.get("diagnostic")
    if not isinstance(diagnostic, dict):
        return False
    first, second = diagnostic.get("first"), diagnostic.get("second")
    if not isinstance(first, dict) or not isinstance(second, dict):
        return False
    first_size = first.get("target_memory_bytes_read")
    second_size = second.get("target_memory_bytes_read")
    return (
        sample.get("status") == "stable_supplied_bytes_diagnostic_only"
        and diagnostic.get("status") == sample.get("status")
        and type(sample.get("sampler_exit_code")) is int
        and sample["sampler_exit_code"] == 0
        and type(sample.get("pid")) is int
        and sample["pid"] == candidate.get("process_pid")
        and type(sample.get("process_created_filetime")) is int
        and sample["process_created_filetime"]
        == candidate.get("process_created_filetime")
        and sample.get("process_exe_sha256")
        == candidate.get("loaded_game_exe_sha256")
        and _sha256(sample.get("process_exe_sha256"))
        and type(first_size) is int and 0 < first_size <= MAX_READ
        and type(second_size) is int and 0 < second_size <= MAX_READ
        and type(diagnostic.get("total_target_memory_bytes_read")) is int
        and diagnostic["total_target_memory_bytes_read"]
        == first_size + second_size
        and diagnostic.get("formal_cash_eligible") is False
        and sample.get("formal_cash_eligible") is False
        and sample.get("game_code_called") is False
        and sample.get("game_memory_written") is False
        and sample.get("same_native_frame_before_after_proven_by_this_tool")
        is False
    )


def _attempt_anchor(sample: object, attempt_dir: Path) -> bool:
    if not isinstance(sample, dict):
        return False
    intent = attempt_dir / "intent.json"
    try:
        digest = hashlib.sha256(intent.read_bytes()).hexdigest().upper()
        source = Path(sample.get("session_receipt", ""))
        return (source.resolve(strict=True) == intent.resolve(strict=True)
                and sample.get("session_receipt_sha256") == digest)
    except (OSError, TypeError, ValueError):
        return False


def sample_read_only_topbar(pid: int, attempt_dir: Path) -> dict[str, object]:
    """Run the pinned research sampler in a bounded child, preserving output."""
    script = (Path(__file__).resolve().parents[2] / "native_bridge" /
              "research" / "war_cash_topbar_bounded_sample.py")
    output = attempt_dir / SAMPLE_NAME
    if output.exists():
        raise FileExistsError("passive raw sample already exists in this attempt")
    command = [sys.executable, str(script), "--pid", str(pid),
               "--session-receipt", str(attempt_dir / "intent.json"),
               "--output", str(output)]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False,
    )
    if not output.is_file():
        raise RuntimeError(
            f"read-only sampler produced no receipt (exit {completed.returncode})"
        )
    raw = output.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("read-only sampler receipt exceeds 1 MiB")
    # The raw file is an append-only child artifact.  A nonzero exit is
    # expected when the sampler itself reports RED.
    sample = json.loads(raw)
    if not isinstance(sample, dict):
        raise ValueError("read-only sampler receipt is not an object")
    sample["sampler_exit_code"] = completed.returncode
    sample["raw_receipt_path"] = str(output)
    sample["raw_receipt_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    return sample


def capture_formal_query_passive_topbar(
    *,
    attempt_dir: Path,
    candidate: dict[str, object] | None,
    postcheck: Callable[[], dict[str, object]],
    sampler: Callable[[int, Path], dict[str, object]] = sample_read_only_topbar,
) -> tuple[dict[str, object], dict[str, object] | None]:
    """Write a RED diagnostic and return the post-sample formal check.

    Sampler and postcheck errors are evidence failures, never gameplay errors.
    The caller may invalidate its original formal receipt if postcheck fails.
    """
    missing: list[str] = []
    sample: dict[str, object] | None = None
    post: dict[str, object] | None = None
    if (not isinstance(candidate, dict)
            or candidate.get("status") != "same_paused_query_postcheck_passed"):
        missing.append("formal_selected_query_candidate_unavailable")
    elif not _same_frame(candidate, candidate):
        missing.append("candidate_frame_or_pid_incomplete")
    else:
        try:
            sample = sampler(candidate["process_pid"], attempt_dir)
        except Exception as error:
            missing.append(f"passive_read_failed:{type(error).__name__}")
        if not _bounded_sample(sample, candidate):
            missing.append("read_only_pid_or_64k_budget_or_cache_diagnostic_unproven")
        if not _attempt_anchor(sample, attempt_dir):
            missing.append("passive_sample_not_bound_to_attempt_intent")
        try:
            post = postcheck()
        except Exception as error:
            missing.append(f"post_sample_frame_check_failed:{type(error).__name__}")
        if not _same_frame(candidate, post):
            missing.append("post_sample_same_pid_or_six_field_frame_unproven")

    receipt: dict[str, object] = {
        "schema": SCHEMA,
        "status": "RED_diagnostic_only",
        "missing_reasons": missing or [
            "gui_cache_natural_refresh_and_military_cash_composition_unproven"
        ],
        "sample_status": sample.get("status") if isinstance(sample, dict) else None,
        "sample": sample,
        "candidate_frame": (
            candidate.get("source_frame_after")
            if isinstance(candidate, dict) else None
        ),
        "post_sample_frame": (
            post.get("source_frame_after") if isinstance(post, dict) else None
        ),
        "post_sample_formal_query_check_passed": _same_frame(candidate, post),
        "gameplay_submit_by_this_diagnostic": False,
        "formal_cash_eligible": False,
        "pending_war_cash_raw": None,
        "immediate_war_action_cost_raw": None,
        "future_war_cost_upper_raw": None,
        "future_risk_budget_raw": None,
        "minimum_war_gold_reserve_raw": None,
        "horizon_days": None,
        "future_war_cost_assumptions": None,
    }
    path = attempt_dir / RECEIPT_NAME
    try:
        payload = json.dumps(receipt, sort_keys=True, indent=2,
                             ensure_ascii=False).encode("utf-8")
        with path.open("xb") as stream:
            stream.write(payload)
    except Exception as error:
        return ({
            "status": "RED_observer_receipt_write_failed",
            "missing_reasons": [f"append_only_receipt_failed:{type(error).__name__}"],
            "post_sample_formal_query_check_passed": _same_frame(candidate, post),
            "formal_cash_eligible": False,
        }, post)
    summary = {
        "status": receipt["status"], "path": str(path),
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
        "missing_reasons": receipt["missing_reasons"],
        "post_sample_formal_query_check_passed": (
            receipt["post_sample_formal_query_check_passed"]
        ),
        "formal_cash_eligible": False,
    }
    return summary, post


def formal_candidate_after_passive_topbar(
    candidate: dict[str, object] | None,
    summary: dict[str, object] | None,
) -> dict[str, object]:
    """Keep a formal query receipt only after an appended post-sample check."""
    if (
        isinstance(candidate, dict)
        and candidate.get("status") == "same_paused_query_postcheck_passed"
        and isinstance(summary, dict)
        and summary.get("status") == "RED_diagnostic_only"
        and summary.get("post_sample_formal_query_check_passed") is True
        and isinstance(summary.get("path"), str)
        and summary["path"]
        and _sha256(summary.get("sha256"))
    ):
        return candidate
    return {
        "status": "blocked_after_passive_sample",
        "missing_reasons": [
            "append_only_post_sample_same_pid_six_field_check_unproven"
        ],
        "formal_cash_receipt_eligible": False,
        "immediate_war_action_cost_raw": None,
    }
