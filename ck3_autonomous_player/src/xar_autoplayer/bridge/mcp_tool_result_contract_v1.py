"""Check completion tags before decoding a retained MCP result body."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal


def require_complete_tool_result(value: Mapping[str, object]) -> Literal["complete"]:
    """Legacy omission is allowed; every explicit alias must be complete.

    SDK-error checks remain the caller's job. No body is normalized or retried.
    """
    for key in ("result_type", "resultType"):
        if key in value:
            kind = value[key]
            if type(kind) is not str or kind != "complete":
                raise ValueError("non-complete MCP result retained; no retry")
    return "complete"
