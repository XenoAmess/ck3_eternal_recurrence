"""Shape the Army query MCP result without repeating its full JSON as text."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from .army_strengths_manager_shared_wire import pack_army_strengths_manager_inputs

if TYPE_CHECKING:
    from mcp.types import CallToolResult


_SUMMARY_ARMY_FIELDS = (
    "status",
    "army_id",
    "native_carmy_id",
    "regiment_count",
    "current_soldiers",
    "maximum_soldiers",
    "ai_base_power_raw",
    "ai_base_power_scale",
    "current_supply_raw",
    "current_supply_scale",
    "current_attrition_fraction_raw",
    "current_attrition_fraction_scale",
    "unavailable_reason",
)


def _army_strengths_summary(payload: dict[str, object]) -> dict[str, object]:
    source = payload.get("source")
    rows = cast(list[dict[str, object]], payload["army_strengths"])
    return {
        "accepted": payload.get("accepted"),
        "status": payload.get("status"),
        "query_sequence": payload.get("query_sequence"),
        "source": {
            "revision": (
                source.get("revision")
                if isinstance(source, dict)
                else payload.get("queried_revision")
            ),
            "native_revision": (
                source.get("native_revision")
                if isinstance(source, dict)
                else payload.get("queried_native_revision")
            ),
        },
        "army_ids": (
            payload["army_ids"]
            if "army_ids" in payload
            else [row.get("army_id") for row in rows]
        ),
        "armies": [
            {field: row.get(field) for field in _SUMMARY_ARMY_FIELDS}
            for row in rows
        ],
        "result_location": "structuredContent",
    }


def build_army_strengths_mcp_result(payload: dict[str, object]) -> CallToolResult:
    """Keep the complete Service result in structured content and summarize text.

    MCP imports stay lazy so baseline installs do not require the optional SDK.
    The caller supplies the complete Army result from a direct query or step.
    """
    from mcp.types import CallToolResult, TextContent

    summary = _army_strengths_summary(payload)
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
            )
        ],
        structured_content=pack_army_strengths_manager_inputs(payload),
    )


def build_army_auto_turn_mcp_result(payload: dict[str, object]) -> CallToolResult:
    """Preserve the original Army auto-turn packet with a compact text summary."""
    from mcp.types import CallToolResult, TextContent

    plan = cast(dict[str, object], payload["plan"])
    result = cast(dict[str, object], payload["result"])
    summary = {
        "status": payload.get("status"),
        "selected_step": payload.get("selected_step"),
        "plan": {key: plan.get(key) for key in ("selected_step", "phase")},
        "result": _army_strengths_summary(result),
        "result_location": "structuredContent",
    }
    return CallToolResult(
        content=[TextContent(
            type="text", text=json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
        )],
        structured_content={
            **payload,
            "result": pack_army_strengths_manager_inputs(result),
        },
    )
