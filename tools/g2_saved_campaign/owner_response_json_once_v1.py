"""Encode the full MCP result once while retaining the owner's exact row JSON."""
from __future__ import annotations

import json

from owner_response_contract_v1 import JsonObject, OwnerSuccessPrefixV1, OwnerSuccessRowV1
from owner_response_contract_v1 import JsonValue as JsonValue
from owner_response_contract_v1 import (
    decode_canonical_owner_response_v1 as decode_canonical_owner_response_v1,
)


def json_utf8(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def prepare_success_response_row_v1(*, started_at_utc: str, ended_at_utc: str,
                                    elapsed_seconds: float, request: JsonObject,
                                    result: JsonObject) -> tuple[OwnerSuccessRowV1, bytes]:
    """Encode a returned RPC result, including SDK errors, without interpreting it.

    The full result is neither pruned nor normalized. The original model dump
    and downstream decoded/check_after functions remain the caller's work.
    Encoding errors propagate to the existing unknown-outcome path, never to
    an RPC retry. No file or backend operation occurs here.
    """
    encoded_result = json_utf8(result)
    prefix: OwnerSuccessPrefixV1 = {
        "started_at_utc": started_at_utc, "ended_at_utc": ended_at_utc,
        "elapsed_seconds": elapsed_seconds, "request": request,
    }
    count = len(encoded_result)
    row: OwnerSuccessRowV1 = {
        **prefix, "result": result, "mcp_result_projection_json_utf8_bytes": count,
    }
    encoded_row = b"".join((json_utf8(prefix)[:-1], b',"result":', encoded_result,
                           b',"mcp_result_projection_json_utf8_bytes":',
                           str(count).encode("ascii"), b"}"))
    return row, encoded_row
