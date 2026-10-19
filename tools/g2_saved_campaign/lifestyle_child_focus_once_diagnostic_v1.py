"""Conditional second read through the existing App-owned child-focus method."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path

from lifestyle_current_state_once_diagnostic_v1 import _frame


TOOL_NAME = "ck3_query_current_player_education_focus_once_diagnostic_v1"
LIFE2_ERRORS = frozenset({
    "native_lifestyle_current_state_current_lifestyle_getter_failed",
    "native_lifestyle_current_state_current_lifestyle_key_read_failed",
})


def install_child_focus_once_diag(
    server: object, driver: object, *, evidence_path: str | Path,
    lifestyle_diagnostic_path: str | Path, machine_id: str,
):
    """Register now; execution requires the first read's exact same-frame failure.

    The runtime owner separately qualifies the existing Native26 handler/DLL.
    The target education key requests only a native validator; the returned
    current-focus fact is independent and no command is copied or submitted.
    """
    target, prior_path = Path(evidence_path), Path(lifestyle_diagnostic_path)
    started = target.with_name(target.name + ".started.json")
    if target.exists() or started.exists():
        raise ValueError("one child-focus diagnostic path was already reserved")
    used = False

    @server.tool()
    def ck3_query_current_player_education_focus_once_diagnostic_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        nonlocal used
        if used:
            raise RuntimeError("one child-focus diagnostic was already attempted; never retry")
        used = True
        record: dict[str, object] = {
            "schema": "xar.app-owned-child-focus-once-diagnostic.v1",
            "machine_id": machine_id,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "method": "NativeDriver.query_child_education_focus_private_v1",
            "prior_lifestyle_diagnostic_path": str(prior_path),
            "expected_revision": expected_revision,
            "gameplay_action_submitted": False,
        }
        with started.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
        try:
            prior = json.loads(prior_path.read_text(encoding="utf-8-sig"))
            error = prior.get("original_method_return", {}).get("native_error")
            before = _frame(driver.take_internal_semantic_snapshot())
            record["before"] = before
            record["prior_native_error"] = error
            if (prior.get("schema") != "xar.app-owned-lifestyle-current-state-once-diagnostic.v1"
                    or prior.get("machine_id") != machine_id
                    or prior.get("method") != "NativeDriver.query_player_lifestyle_current_state_private_v1"
                    or prior.get("status") != "observed" or prior.get("same_frame") is not True
                    or prior.get("query_attempted") is not True
                    or error not in LIFE2_ERRORS
                    or prior.get("before") != prior.get("after")
                    or before != prior.get("after")
                    or type(expected_revision) is not int or expected_revision <= 0
                    or before.get("revision") != expected_revision
                    or before.get("paused") is not True or before.get("map_ready") is not True
                    or before.get("actor_alive") is not True
                    or getattr(driver, "_session_bridge_pid", None) != before.get("bridge_pid")
                    or before.get("hello_pid") != before.get("bridge_pid")
                    or getattr(driver, "allow_private_lifestyle_formal_trial", False) is not True):
                raise ValueError("child-focus diagnostic lacks the exact preceding same-frame LIFE2 failure")
            record["query_attempted"] = True
            record["original_method_return"] = copy.deepcopy(
                driver.query_child_education_focus_private_v1(
                    child_full_id=before["player_character_id"],
                    target_key="education_stewardship", expected_revision=expected_revision,
                )
            )
            after = _frame(driver.take_internal_semantic_snapshot())
            record["after"] = after
            record["same_frame"] = after == before
            record["status"] = "observed" if after == before else "frame_changed"
        except Exception as error:
            record["status"] = "diagnostic_failed"
            record["exception_type"] = type(error).__name__
            record["exception"] = str(error)
        record["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        with target.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
        return record

    return ck3_query_current_player_education_focus_once_diagnostic_v1
