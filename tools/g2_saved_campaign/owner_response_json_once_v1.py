"""Encode the full MCP result once while retaining the owner's exact row JSON."""
from __future__ import annotations

import json


def json_utf8(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def prepare_success_response_row_v1(*, started_at_utc: str, ended_at_utc: str,
                                    elapsed_seconds: float, request: dict,
                                    result: dict) -> tuple[dict, bytes]:
    """Return the original row object plus exactly its existing compact UTF-8.

    The full result is neither pruned nor normalized.  The original output-model
    dump and downstream decoded/check_after functions remain the caller's work.
    A text/JSON encoding error propagates to the caller's existing unknown-outcome
    path, never to an RPC retry.  No file or backend operation occurs here.
    """
    encoded_result = json_utf8(result)
    prefix = {"started_at_utc": started_at_utc, "ended_at_utc": ended_at_utc,
              "elapsed_seconds": elapsed_seconds, "request": request}
    count = len(encoded_result)
    row = {**prefix, "result": result, "mcp_result_projection_json_utf8_bytes": count}
    encoded_row = b"".join((json_utf8(prefix)[:-1], b',"result":', encoded_result,
                           b',"mcp_result_projection_json_utf8_bytes":',
                           str(count).encode("ascii"), b"}"))
    return row, encoded_row
