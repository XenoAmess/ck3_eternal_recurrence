"""Fail-closed decision used by the next H3937 screen operator.

Callers must independently bind each input to the exact attempt and nonce.
This function never changes a task-bus lease or removes an unsafe marker.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def assess_screen_release(
    *,
    child_started: bool,
    child_exited: bool,
    target_processes_gone: bool,
    child_completion: Mapping[str, Any] | None,
    outer_report: Mapping[str, Any] | None,
    outer_report_sha256: str | None,
    pre_native_launch_proven: bool,
    unsafe_marker_absent: bool,
    nonce_bound_watchdog_scans: Sequence[Sequence[Mapping[str, Any]]] | None,
    watchdog_scan_error: str | None,
    unique_owned_screen_lease: bool,
) -> dict[str, object]:
    """Return reasons before any `status --state done` command is attempted."""
    failures: list[str] = []
    if type(child_started) is not bool:
        failures.append("one-shot child-started proof malformed")
    if child_exited is not True:
        failures.append("one-shot child exit unproven")
    if target_processes_gone is not True:
        failures.append("CK3/recorder/injector inventory not empty or unavailable")
    if child_started is True:
        if not isinstance(child_completion, Mapping) or not isinstance(outer_report, Mapping):
            failures.append("exact child completion or outer report unavailable")
        else:
            bound_sha = str(child_completion.get("outer_report_sha256", ""))
            if not outer_report_sha256 or bound_sha.upper() != outer_report_sha256.upper():
                failures.append("outer report digest differs from child completion")
            if child_completion.get("outer_cleanup_proven") is not True:
                failures.append("child native cleanup not proven")
            if outer_report.get("outer_session_cleanup_verified") is not True:
                failures.append("outer native session cleanup not proven")
            cleanup = outer_report.get("cleanup")
            if not isinstance(cleanup, Mapping) or cleanup.get("cleanup_proven") is not True:
                failures.append("native cleanup evidence incomplete")
    elif child_started is False and pre_native_launch_proven is not True:
        failures.append("no-child pre-native phase not proven")
    if unsafe_marker_absent is not True:
        failures.append("unsafe marker present or unreadable")
    if watchdog_scan_error is not None:
        failures.append("nonce-bound watchdog inventory unavailable")
    if (
        type(nonce_bound_watchdog_scans) is not list
        or len(nonce_bound_watchdog_scans) != 2
        or any(type(scan) is not list for scan in nonce_bound_watchdog_scans)
    ):
        failures.append("two nonce-bound watchdog scans unavailable")
    elif any(scan for scan in nonce_bound_watchdog_scans):
        failures.append("nonce-bound watchdog child remains")
    if unique_owned_screen_lease is not True:
        failures.append("exact unique screen lease not proven")
    return {
        "schema": "xar.h3937-screen-release-decision.v1",
        "may_release": not failures,
        "failures": failures,
        "watchdog_scan_count": (
            len(nonce_bound_watchdog_scans)
            if nonce_bound_watchdog_scans is not None else 0
        ),
    }
