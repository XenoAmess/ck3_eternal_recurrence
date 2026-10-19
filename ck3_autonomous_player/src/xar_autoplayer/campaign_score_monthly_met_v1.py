"""Fresh exact-month MET collection using the two existing readonly queries.

Call from the paired post-AUTO MET handler while it owns the paused runner.
No prior snapshot, planner input, cache, SAVE, file IO or retry is accepted.
The queries have separate Native mailbox captures, not one atomic capture.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from time import perf_counter

from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .campaign_score_cadence_v1 import ordinary_sample_candidate
from .campaign_score_existing_inputs_v1 import (
    _frame_reason, project_existing_month_inputs_v1,
)


def collect_monthly_met_candidate_v1(
    service, *, start_date: str, machine_id: str, campaign_anchor, months: int = 360,
):
    """Return (fresh semantic snapshot, optional narrow monthly candidate).

    The caller's existing queue must still pair the MET with its settled AUTO
    and persist the actual response/Game pins. Call once, before another action
    or advance. This function never enables a private permission or retries an
    uncertain query. Non-month frames cost one semantic read and zero queries.
    """
    read = service.driver.take_internal_semantic_snapshot
    snapshot = read()

    def candidate(frame):
        if frame.get("paused") is not True:
            return None
        return ordinary_sample_candidate(
            frame, start_date=start_date, machine_id=machine_id,
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
            campaign_anchor=campaign_anchor, months=months,
        )

    sample = candidate(snapshot)
    if sample is None:
        return snapshot, None

    # Reuse the service's established frame contract, including episode/PID/
    # connection generation. Never manufacture a binding for a retained DTO.
    source_frame = service._observed_planning_source_frame(snapshot)
    initial_frame_reason = _frame_reason(snapshot, source_frame)
    packets, source_frames, queries = {}, {}, {}
    current = snapshot
    semantic_reads = 1
    final_frame_observed = True
    stopped_reason = initial_frame_reason
    query_methods = (
        ("cash", getattr(service.driver, "query_war_cash_current_resources_private_v1", None)),
        ("realm", getattr(service, "query_campaign_root_context_v1", None)),
    )
    for kind, query in query_methods:
        if stopped_reason is not None:
            queries[kind] = {"status": "not_invoked", "reason": stopped_reason}
            continue
        if not callable(query):
            queries[kind] = {"status": "not_invoked", "reason": "existing_query_method_unavailable"}
            continue
        source_frames[kind] = deepcopy(source_frame)
        started = perf_counter()
        query_stop_reason = None
        try:
            packets[kind] = query(expected_revision=source_frame["revision"])
            queries[kind] = {"status": "returned"}
        except UnsupportedStepError as error:
            # Existing permission/capability refusal occurs before submission.
            queries[kind] = {"status": "unsupported", "reason": str(error)[:256]}
        except (BridgeUnavailableError, ValueError, TypeError, KeyError) as error:
            queries[kind] = {"status": "unavailable", "reason": str(error)[:256]}
            # A failed or unknown result may still own the client/mailbox.
            # Do not use a stable semantic cache to justify another submission.
            query_stop_reason = "earlier_readonly_query_unavailable:" + kind
        queries[kind]["elapsed_seconds"] = round(perf_counter() - started, 6)
        semantic_reads += 1
        try:
            current = read()
        except BridgeUnavailableError as error:
            final_frame_observed = False
            stopped_reason = "post_query_semantic_frame_unavailable:" + str(error)[:192]
            continue
        stopped_reason = _frame_reason(current, source_frame) or query_stop_reason

    # If the frame moved, retain only the final exact-slot ordinary observation.
    # The pure mapper rejects both old query packets against that actual frame.
    # If the final read failed, the initial frame remains an actual observation,
    # but neither optional query may be promoted without the closing check.
    sample = candidate(current)
    if sample is None:
        return current, None
    if not final_frame_observed:
        packets.clear()
    extra = project_existing_month_inputs_v1(
        current, cash_packet=packets.get("cash"),
        cash_source_frame=source_frames.get("cash"),
        campaign_root_result=packets.get("realm"),
        root_source_frame=source_frames.get("realm"),
    )
    sample["raw_metrics"].update(extra["raw_metrics"])
    sample["sources"].extend(extra["sources"])
    sample["existing_realm_diagnostics"] = extra["realm_diagnostics"]
    sample["existing_input_gaps"] = {
        **extra["input_gaps"],
        **{kind: row["reason"] for kind, row in queries.items() if row.get("reason")},
    }
    if not final_frame_observed:
        sample["existing_input_gaps"]["closing_frame"] = stopped_reason
    attempts = sum(row["status"] != "not_invoked" for row in queries.values())
    sample["monthly_collection"] = {
        "mode": "paused_readonly_bundle", "same_native_capture": False,
        "native_capture_epochs": {"cash": None, "realm": None},
        "capture_epoch_status": "not_exposed_by_existing_cash_and_root_interfaces",
        "source_frame": deepcopy(source_frame),
        "closing_frame": service._observed_planning_source_frame(current) if final_frame_observed else None,
        "closing_frame_verified": final_frame_observed and _frame_reason(current, source_frame) is None,
        "queries": queries, "readonly_query_invocations": attempts,
        "collector_semantic_reads": semantic_reads,
        "native_requests_at_most": attempts,
        "native_requests_observed": None,
        "new_SAVE_exports": 0, "retry_count": 0,
        "runtime_queue_pairing_and_response_pins_still_required": True,
    }
    # Existing wrappers may reject before sending. Their DTOs expose no send
    # counter, so do not inherit the pure cadence helper's zero-RPC assertion.
    sample["new_RPC_calls"] = 0 if attempts == 0 else None
    return current, sample
