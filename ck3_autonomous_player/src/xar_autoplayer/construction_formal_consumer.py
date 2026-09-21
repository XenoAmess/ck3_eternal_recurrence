"""One controlled feudal construction action and its durable confirmation.

This is not a public capability.  A lost native reply is an unresolved action,
not permission to build again after a cold start.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import write_json_atomic
from .lifestyle_formal_consumer import ROOT_QUERY_STEP, same_frame_feudal_peace_scope


SUBMIT_STEP = "private-submit-player-construction-v1"
RECEIPT_STEP = "private-query-player-construction-receipt-v1"
_LEDGER = "construction-formal-pending-v1.json"


def read_construction_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.exists():
        return {"schema": "xar.ck3.construction_formal_pending_v1", "pending": None,
                "applied": None}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict)
            or record.get("schema") != "xar.ck3.construction_formal_pending_v1"
            or not all(key in record for key in ("pending", "applied"))
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "applied"))):
        raise ValueError("construction pending ledger shape is unknown")
    return record


def write_construction_ledger(state_dir: Path, record: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(record))


def plan_construction_private(
    driver: object, planned: dict[str, object], snapshot: Mapping[str, object],
    history: list[dict[str, object]], available_steps: set[str],
) -> dict[str, object]:
    plan = planned.get("plan")
    if not isinstance(plan, dict) or plan.get("selected_step") != "life-advance":
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        return {**planned, "plan": {**plan, "selected_step": None,
                                    "reason": "construction trial lacks durable state_dir"}}
    ledger = read_construction_ledger(state_dir)
    episode = snapshot.get("episode_run_id")
    pending = ledger["pending"]
    if isinstance(pending, dict):
        if pending.get("episode_run_id") != episode:
            return {**planned, "plan": {**plan, "selected_step": None,
                                        "reason": "unresolved construction belongs to another episode"}}
        from .bridge.domain_construction_private_transport_v1 import _identity

        pid, creation = _identity(driver)
        cold_process = (pid, creation) != (
            pending.get("source_bridge_pid"),
            pending.get("source_bridge_creation_date"),
        )
        if (cold_process or (type(snapshot.get("native_revision")) is int
                             and snapshot["native_revision"] > pending.get("pre_native_revision", 0))):
            return {**planned, "plan": {**plan,
                "phase": "construction_pending_receipt",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(pending),
                "reason": "query independent paused construction state before another action"}}
        return {**planned, "plan": {**plan,
            "construction_pending_action": dict(pending),
            "reason": "advance to independent native frame; never resubmit pending construction"}}
    applied = ledger["applied"]
    if isinstance(applied, dict) and applied.get("episode_run_id") == episode:
        from .bridge.domain_construction_private_transport_v1 import _identity

        if _identity(driver) != (applied.get("post_bridge_pid"),
                                 applied.get("post_bridge_creation_date")):
            return {**planned, "plan": {**plan,
                "phase": "construction_cold_applied_requery",
                "selected_step": RECEIPT_STEP,
                "construction_pending_action": dict(applied),
                "reason": "cold restore may load an earlier checkpoint; verify construction before using ledger"}}
        return {**planned, "plan": {**plan,
            "construction_receipt_consumed": dict(applied)}}
    scope = same_frame_feudal_peace_scope(snapshot, history)
    if scope["status"] == "root_query_needed":
        if ROOT_QUERY_STEP not in available_steps:
            return {**planned, "plan": {**plan, "selected_step": None,
                "reason": "construction trial needs same-frame public feudal root query"}}
        return {**planned, "plan": {**plan, "selected_step": ROOT_QUERY_STEP,
            "phase": "construction_feudal_scope_query"}}
    if scope["status"] != "admitted":
        return planned
    from .bridge.domain_construction_private_transport_v1 import query_construction_private

    query = query_construction_private(driver, expected_revision=int(planned["revision"]))
    if query.get("status") == "no_legal_budgeted_building":
        return {**planned, "plan": {**plan, "construction_private_query": query}}
    if query.get("status") != "selected":
        return {**planned, "plan": {**plan, "selected_step": None,
            "construction_private_query": query,
            "reason": "private construction source unavailable; preserve RED"}}
    return {**planned, "plan": {**plan,
        "phase": "construction_typed_submit", "selected_step": SUBMIT_STEP,
        "construction_private_query": query,
        "reason": "submit one native-legal budgeted construction"}}
