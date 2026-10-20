"""Canonical owner responses; raw-wire validation belongs before the SDK adapter."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Literal, TypeAlias, TypeGuard, TypedDict

JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = dict[str, JsonValue]


class OwnerSuccessPrefixV1(TypedDict):
    started_at_utc: str
    ended_at_utc: str
    elapsed_seconds: float
    request: JsonObject


class OwnerSuccessRowV1(OwnerSuccessPrefixV1):
    result: JsonObject
    mcp_result_projection_json_utf8_bytes: int


class OwnerClientUnknownRowV1(OwnerSuccessPrefixV1):
    client_error: str
    replay_allowed: Literal[False]


def _json_domain(value: object, active: set[int]) -> bool:
    if value is None or type(value) in (bool, int, str):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) not in (list, dict):
        return False
    identity = id(value)
    if identity in active:
        return False
    active.add(identity)
    try:
        if isinstance(value, list):
            return all(_json_domain(item, active) for item in value)
        if isinstance(value, dict):
            return all(type(key) is str and _json_domain(item, active)
                       for key, item in value.items())
        return False
    finally:
        active.remove(identity)


def _is_json_object(value: object) -> TypeGuard[JsonObject]:
    return type(value) is dict and _json_domain(value, set())


def require_json_object_v1(value: object) -> JsonObject:
    if not _is_json_object(value):
        raise ValueError("expected an ordinary finite JSON object")
    return value


@dataclass(frozen=True)
class CanonicalCompleteToolResultV1:
    meta: JsonObject | None
    content: list[JsonObject]
    structured_content: JsonValue
    is_error: bool
    result_type: Literal["complete"] = "complete"


@dataclass(frozen=True)
class ToolSuccessV1:
    row: JsonObject
    result: CanonicalCompleteToolResultV1
    kind: Literal["tool_success"] = "tool_success"


@dataclass(frozen=True)
class ToolFailureV1:
    row: JsonObject
    result: CanonicalCompleteToolResultV1
    kind: Literal["tool_failure"] = "tool_failure"


@dataclass(frozen=True)
class ClientUnknownV1:
    row: JsonObject
    client_error: str
    replay_allowed: Literal[False] = False
    kind: Literal["client_unknown"] = "client_unknown"


OwnerOutcomeV1: TypeAlias = ToolSuccessV1 | ToolFailureV1 | ClientUnknownV1
_FIELDS = frozenset({"meta", "content", "structured_content", "is_error", "result_type"})


def _canonical_tool_result(value: JsonValue) -> CanonicalCompleteToolResultV1:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("canonical MCP2 model dump fields required")
    meta = value["meta"]
    if meta is not None and not isinstance(meta, dict):
        raise ValueError("canonical meta must be an object or null")
    content = value["content"]
    if not isinstance(content, list):
        raise ValueError("canonical content must be an array")
    blocks: list[JsonObject] = []
    for block in content:
        if not isinstance(block, dict):
            raise ValueError("canonical content block must be an object")
        blocks.append(block)
    flag = value["is_error"]
    if type(flag) is not bool:
        raise ValueError("canonical is_error must be a boolean")
    if type(value["result_type"]) is not str or value["result_type"] != "complete":
        raise ValueError("non-complete MCP result retained; no retry")
    return CanonicalCompleteToolResultV1(
        meta=meta, content=blocks, structured_content=value["structured_content"], is_error=flag,
    )


def parse_canonical_tool_result_v1(value: object) -> CanonicalCompleteToolResultV1:
    return _canonical_tool_result(require_json_object_v1(value))


def parse_owner_response_v1(value: object) -> OwnerOutcomeV1:
    """Read returned results and explicit client-unknown rows, including projections."""
    row = require_json_object_v1(value)
    if "error" in row:
        raise ValueError("owner response has no top-level error field")
    if "client_error" in row:
        error = row["client_error"]
        if type(error) is not str or not error:
            raise ValueError("client_error must be a nonempty string")
        if row.get("replay_allowed") is not False or "result" in row:
            raise ValueError("client unknown requires no result and forbids replay")
        return ClientUnknownV1(row=row, client_error=error)
    if "result" not in row:
        raise ValueError("owner response lacks its canonical result")
    result = _canonical_tool_result(row["result"])
    if result.is_error:
        return ToolFailureV1(row=row, result=result)
    return ToolSuccessV1(row=row, result=result)


def decode_canonical_owner_response_v1(value: object) -> JsonObject:
    """Decode only after the original receipt was persisted; never resubmit."""
    outcome = parse_owner_response_v1(value)
    if isinstance(outcome, ClientUnknownV1):
        raise RuntimeError("client outcome unknown; original request must not be resent")
    if isinstance(outcome, ToolFailureV1):
        raise RuntimeError("SDK error; original result retained; no automatic retry")
    body = outcome.result.structured_content
    if isinstance(body, dict):
        return body
    for block in outcome.result.content:
        text = block.get("text")
        if block.get("type") != "text" or not isinstance(text, str):
            continue
        try:
            decoded: object = json.loads(text)
            return require_json_object_v1(decoded)
        except ValueError:
            continue
    raise ValueError("SDK returned no actual decoded object")
