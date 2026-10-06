"""Shape the Army query MCP result without repeating its full JSON as text."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

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


def build_army_strengths_mcp_result(payload: dict[str, object]) -> CallToolResult:
    """Keep the complete Service result in structured content and summarize text.

    MCP imports stay lazy so baseline installs do not require the optional SDK.
    The caller supplies the complete result of Service.query_army_strengths.
    """
    from mcp.types import CallToolResult, TextContent

    source = cast(dict[str, object], payload["source"])
    rows = cast(list[dict[str, object]], payload["army_strengths"])
    summary = {
        "accepted": payload.get("accepted"),
        "status": payload.get("status"),
        "query_sequence": payload.get("query_sequence"),
        "source": {
            "revision": source.get("revision"),
            "native_revision": source.get("native_revision"),
        },
        "army_ids": payload["army_ids"],
        "armies": [
            {field: row.get(field) for field in _SUMMARY_ARMY_FIELDS}
            for row in rows
        ],
        "result_location": "structuredContent",
    }
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
            )
        ],
        structured_content=payload,
    )
