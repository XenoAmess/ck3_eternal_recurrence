"""Summarize superseded market history after a complete fresh observation.

The latest full market and every command row/envelope remain. A summary is not
an archive: an older selected source body may be omitted too. Selected decisions
and pending-hire ledgers retain their own facts and use fresh employer readback.
"""
from __future__ import annotations

import copy
import hashlib
import json

from ..m5_observed_opportunity_selector import observed_frame
from .player_mercenary_context import (
    STEP, normalize_player_mercenary_context_v1,
    player_mercenary_context_frame_binding,
)

SUMMARY_SCHEMA = "xar.market-history-observation-summary.v1"


def _summary(result: dict[str, object], raw: dict[str, object]) -> dict[str, object]:
    rows = raw.get("rows")
    if not isinstance(rows, list):
        raise ValueError("old market body has no factual row collection")
    digest = hashlib.sha256()
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    for piece in encoder.iterencode(raw):
        encoded = piece.encode("utf-8")
        digest.update(encoded)
        size += len(encoded)
    frame = result.get("mercenary_query_source_frame_v1")
    # Keep original facts; never infer an old receipt's frame from today's state.
    source_frame = ({key: copy.deepcopy(frame[key]) for key in (
        "played_character_id", "native_revision", "date_raw", "snapshot_id",
        "revision", "episode_run_id") if key in frame}
        if isinstance(frame, dict) else None)
    value = {
        "schema": SUMMARY_SCHEMA, "original_schema": raw.get("schema"),
        "original_query_sequence": result["query_sequence"],
        "source_frame": source_frame, "snapshot_revision": result.get("snapshot_revision"),
        "date_raw": result.get("date_raw"), "row_count": len(rows),
        "canonical_sha256": digest.hexdigest(), "canonical_json_bytes": size,
        "canonical_json_encoding": "utf-8;ensure_ascii=false;sort_keys=true;compact;allow_nan=false",
        "full_body_retained_in_driver_history": False,
        "full_body_reconstructible_from_summary": False, "immutable_archive": False,
        "original_receipt_lookup": {
            "step": STEP, "query_sequence": result["query_sequence"],
            "source_frame": copy.deepcopy(source_frame), "receipt_path_known": False,
        },
    }
    for key in ("game_version", "executable_sha256", "actor_character_id", "capture_epoch",
                "read_only", "available", "unavailable_reason", "native_hire_mode"):
        if key in raw:
            value[key] = copy.deepcopy(raw[key])
    if "connection_generation" in result:
        value["original_receipt_lookup"]["connection_generation"] = copy.deepcopy(
            result["connection_generation"])
    return value


def compact_superseded_market_history_v1(
    history: list[dict[str, object]], *, result: dict[str, object],
    before: dict[str, object], after: dict[str, object],
) -> int:
    """Mutate old body fields under the caller's history lock; return changed rows.

    The complete new result must already be recorded. Validation/encoding errors
    leave every old body intact. The caller invalidates its incremental history
    JSON cache and marks state dirty if rows changed. This function performs no
    I/O and never alters the result returned to the API caller.
    """
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or result.get("step") != STEP or result.get("accepted") is not True
            or result.get("status") != "completed" or result.get("read_only") is not True
            or type(result.get("query_sequence")) is not int or result["query_sequence"] <= 0
            or result.get("snapshot_revision") != before.get("native_revision")
            or result.get("date_raw") != before.get("date_raw")):
        return 0
    normalized = normalize_player_mercenary_context_v1(
        result.get("player_mercenary_context"), snapshot=before)
    if normalized.get("available") is not True:
        return 0
    frame = observed_frame(before)
    if (player_mercenary_context_frame_binding(after)
            != player_mercenary_context_frame_binding(before)
            or observed_frame(after) != frame
            or result.get("mercenary_query_source_frame_v1") != frame):
        return 0
    normalize_player_mercenary_context_v1(normalized, snapshot=after)
    if not history:
        return 0
    latest = history[-1]
    latest_result = latest.get("result")
    if (latest.get("command") != STEP or latest.get("ok") is not True
            or not isinstance(latest_result, dict)
            or latest_result.get("query_sequence") != result["query_sequence"]
            or latest_result.get("player_mercenary_context") != result["player_mercenary_context"]):
        return 0
    changes = []
    for row in history[:-1]:
        old = row.get("result")
        if row.get("command") != STEP or row.get("ok") is not True or not isinstance(old, dict):
            continue
        raw = old.get("player_mercenary_context")
        if (old.get("accepted") is not True or old.get("read_only") is not True
                or old.get("status") != "completed" or type(old.get("query_sequence")) is not int
                or old["query_sequence"] <= 0 or not isinstance(raw, dict)
                or raw.get("schema") == SUMMARY_SCHEMA
                or not str(raw.get("schema", "")).endswith("_player_mercenary_context_v1")):
            continue
        # Construct all summaries before changing interior rows; failures keep full history.
        changes.append((old, _summary(old, raw)))
    for old, summary in changes:
        old["player_mercenary_context"] = summary
    return len(changes)
