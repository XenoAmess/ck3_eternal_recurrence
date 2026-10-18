"""Keep complete combat-query AUTO results in structured content only."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .combat_contract import parse_query_combat_simulation_inputs_step
from .combat_phase_contract import parse_query_combat_simulation_inputs_v3_step

if TYPE_CHECKING:
    from mcp.types import CallToolResult


def build_combat_query_auto_turn_mcp_result(
    payload: dict[str, object],
) -> dict[str, object] | CallToolResult:
    """Shape only a successful V2/V3 query's AUTO envelope, not model inputs.

    The tool keeps its existing output annotation/schema. MCP's explicit-result
    conversion still validates structured content against that output model.
    Text consumers receive a summary and must use structured content for data.
    """
    plan, result = payload.get("plan"), payload.get("result")
    step = payload.get("selected_step")
    if (payload.get("status") != "executed" or not isinstance(step, str)
            or not isinstance(plan, dict) or plan.get("selected_step") != step
            or not isinstance(result, dict) or result.get("step") != step
            or result.get("accepted") is not True
            or not isinstance(result.get("combat_simulation_inputs"), dict)):
        return payload
    if parse_query_combat_simulation_inputs_step(step) is not None:
        version, statuses = 2, {"available", "partial"}
    elif parse_query_combat_simulation_inputs_v3_step(step) is not None:
        version, statuses = 3, {"available", "unavailable"}
    else:
        return payload
    if result.get("status") not in statuses:
        return payload

    from mcp.types import CallToolResult, TextContent

    summary = {
        "schema": "xar.combat-query-auto-mcp-summary.v1",
        "full_result_location": "structuredContent", "text_contains_full_result": False,
        "status": payload["status"], "selected_step": step, "query_version": version,
        "query_status": result["status"], "query_sequence": result.get("query_sequence"),
        **{key: result.get(key) for key in (
            "queried_snapshot_id", "queried_revision", "queried_native_revision")},
    }
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(
            summary, ensure_ascii=False, separators=(",", ":")))],
        structured_content=payload, is_error=False,
    )
