"""Keep a completed native market AUTO's full result in structured content."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .player_mercenary_context import STEP

if TYPE_CHECKING:
    from mcp.types import CallToolResult


def build_mercenary_query_auto_turn_mcp_result(
    payload: dict[str, object],
) -> dict[str, object] | CallToolResult:
    """Shape only successful native readonly market observations.

    No market normalizer, cost/identity conversion, selection or hire occurs.
    The existing registered tool output model still validates the full payload.
    Direct tools, unavailable collections, errors and other AUTO results retain
    their existing conversion.
    """
    plan, result = payload.get("plan"), payload.get("result")
    if (payload.get("status") != "executed" or payload.get("selected_step") != STEP
            or not isinstance(plan, dict) or plan.get("selected_step") != STEP
            or not isinstance(result, dict) or result.get("step") != STEP
            or result.get("backend_id") != "native-headless"
            or result.get("accepted") is not True or result.get("status") != "completed"
            or result.get("read_only") is not True):
        return payload
    market = result.get("player_mercenary_context")
    if (not isinstance(market, dict) or market.get("available") is not True
            or market.get("read_only") is not True or not isinstance(market.get("rows"), list)):
        return payload

    from mcp.types import CallToolResult, TextContent

    summary = {
        "schema": "xar.mercenary-query-auto-mcp-summary.v1",
        "full_result_location": "structuredContent", "text_contains_full_result": False,
        "status": payload["status"], "selected_step": STEP,
        "query_status": result["status"], "query_sequence": result.get("query_sequence"),
        "snapshot_revision": result.get("snapshot_revision"), "date_raw": result.get("date_raw"),
        "actor_character_id": market.get("actor_character_id"),
        "capture_epoch": market.get("capture_epoch"), "company_row_count": len(market["rows"]),
        "market_available": True, "read_only": True,
    }
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(
            summary, ensure_ascii=False, separators=(",", ":")))],
        structured_content=payload, is_error=False,
    )
