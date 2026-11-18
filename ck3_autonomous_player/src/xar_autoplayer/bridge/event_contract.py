"""Backend-neutral contract for one currently actionable CK3 event."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, TypedDict

from .version_identity import CK3_1210, FlorinFullSource, florin_full_source, require_exact_native_build


EVENT_OPTION_STEP_PREFIX = "select-event-option-"

FLORIN_EVENT_QUERY_STEP = "query-current-event-options-v1"
FLORIN_EVENT_QUERY_CAPABILITY = "game.query.current-event-options.v1"
FLORIN_EVENT_BACKEND = "ck3-1.21.0-native-headless-main-thread"


@dataclass(frozen=True)
class FlorinEventSource:
    snapshot_id: str
    public_revision: int
    native_revision: int
    event_instance_id: int
    date_raw: int
    game_pid: int
    connection_generation: int
    full_source: FlorinFullSource


class FlorinEventOption(TypedDict):
    native_option_index: int
    enabled: bool


class FlorinEventResult(TypedDict):
    status: str
    accepted: bool
    effect_attempted: bool
    options: list[FlorinEventOption]


class FlorinPublicOption(TypedDict):
    native_option_index: int
    option_number: int
    enabled: bool


class FlorinPublicEventOptions(TypedDict):
    schema: Literal["ck3-florin-current-event-options-v1"]
    read_only: Literal[True]
    available: bool
    status: str
    snapshot_id: str
    public_revision: str
    native_revision: str
    event_instance_id: int
    game_pid: int
    connection_generation: str
    date_raw: int
    played_character_id: int
    scope_sha256: str
    options: list[FlorinPublicOption]
    event_definition_observed: Literal[False]
    saved_scopes_observed: Literal[False]
    effect_indicators_observed: Literal[False]
    native_result_json: str
    business_acceptance_credit: Literal[False]


def project_florin_event_options(raw: object, source: FlorinEventSource) -> FlorinPublicEventOptions:
    """Explicit limited public variant; it never impersonates the old event scope/effect context."""
    import json
    result = normalize_florin_event_result(raw, source, FLORIN_EVENT_QUERY_STEP, None)
    return {"schema": "ck3-florin-current-event-options-v1", "read_only": True,
            "available": result["accepted"], "status": result["status"],
            "snapshot_id": source.snapshot_id, "public_revision": str(source.public_revision),
            "native_revision": str(source.native_revision), "event_instance_id": source.event_instance_id,
            "game_pid": source.game_pid, "connection_generation": str(source.connection_generation),
            "date_raw": source.date_raw, "played_character_id": source.full_source.played_character_id,
            "scope_sha256": source.full_source.scope_sha256,
            "options": [{"native_option_index": row["native_option_index"], "option_number": row["native_option_index"] + 1,
                         "enabled": row["enabled"]} for row in result["options"]],
            "event_definition_observed": False, "saved_scopes_observed": False, "effect_indicators_observed": False,
            "native_result_json": json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False),
            "business_acceptance_credit": False}


def is_florin_event_snapshot(snapshot: object) -> bool:
    if not isinstance(snapshot, dict):
        return False
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    return isinstance(hello, dict) and hello.get("expected_ck3_version") == "1.21.0"


def florin_event_source(snapshot: object, event_instance_id: int, expected_revision: int | None) -> FlorinEventSource:
    full = florin_full_source(snapshot, expected_revision)
    if not isinstance(snapshot, dict):
        raise ValueError("actual Florin event Full snapshot required")
    event = snapshot.get("active_event")
    if (not isinstance(event, dict) or type(event.get("instance_id")) is not int
            or type(event_instance_id) is not int or event_instance_id <= 0 or event_instance_id > 2**31 - 1
            or event.get("instance_id") != event_instance_id):
        raise ValueError("event control requires the actual positive current event instance")
    return FlorinEventSource(full.snapshot_id, full.public_revision, full.native_revision, event_instance_id,
                             full.date_raw, full.game_pid, full.connection_generation, full)


def florin_event_fields(source: FlorinEventSource, deadline_unix_ms: int) -> dict[str, object]:
    if type(deadline_unix_ms) is not int or not 1 <= deadline_unix_ms <= 2**63 - 1:
        raise ValueError("positive finite event deadline required")
    return {"event_option_control": {
        "schema": "ck3_1210_event_option_control_v1", "game_version": CK3_1210.game_version,
        "executable_sha256": CK3_1210.executable_sha256, "adapter_id": "ck3-1.21.0-msvc-x64",
        "backend": FLORIN_EVENT_BACKEND, "snapshot_id": source.snapshot_id,
        "native_revision": source.native_revision, "deadline_unix_ms": deadline_unix_ms,
    }, "arguments": {"event_instance_id": source.event_instance_id}}


def normalize_florin_event_result(raw: object, source: FlorinEventSource, step: str, native_index: int | None) -> FlorinEventResult:
    fields = {"schema", "game_version", "executable_sha256", "adapter_id", "backend", "step", "accepted", "status",
              "native_revision", "event_instance_id", "native_option_index", "application_main_observed",
              "full_snapshot_before_verified", "effect_attempted", "options", "unavailable_reason"}
    if not isinstance(raw, dict) or set(raw) not in (fields, fields | {"backend_id"}):
        raise ValueError("closed Florin event result fields required")
    query = step == FLORIN_EVENT_QUERY_STEP
    if ((query and native_index is not None)
            or (not query and (type(native_index) is not int or not 0 <= native_index < 512
                               or step != event_option_step(native_index + 1)))):
        raise ValueError("event result requires the exact query or authored option step")
    if (raw.get("schema") != "ck3_1210_event_option_control_result_v1"
            or require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256")) != CK3_1210
            or raw.get("adapter_id") != "ck3-1.21.0-msvc-x64" or raw.get("backend") != FLORIN_EVENT_BACKEND
            or raw.get("step") != step or type(raw.get("native_revision")) is not int
            or raw.get("native_revision") != source.native_revision or type(raw.get("event_instance_id")) is not int
            or raw.get("event_instance_id") != source.event_instance_id
            or (query and raw.get("native_option_index") is not None)
            or (not query and (type(raw.get("native_option_index")) is not int or raw.get("native_option_index") != native_index))):
        raise ValueError("Florin event result changed exact producer/Full/event/index")
    status = raw.get("status")
    if status not in {"available", "submitted", "unavailable", "expired", "stale_full_snapshot", "no_active_event",
                      "event_mismatch", "option_missing", "option_disabled", "rejected", "indeterminate"}:
        raise ValueError("unknown Florin event status")
    for name in ("accepted", "application_main_observed", "full_snapshot_before_verified", "effect_attempted"):
        if type(raw.get(name)) is not bool:
            raise ValueError("exact Florin event result boolean required")
    if raw["accepted"] != (status == ("available" if query else "submitted")) or (status == "submitted" if query else status == "available"):
        raise ValueError("Florin event query/select result role mismatch")
    options = raw.get("options")
    if not isinstance(options, list) or len(options) > 512:
        raise ValueError("bounded Florin options required")
    normalized: list[FlorinEventOption] = []
    seen: set[int] = set()
    for option in options:
        if (not isinstance(option, dict) or set(option) != {"native_option_index", "enabled"}
                or type(option.get("native_option_index")) is not int or not 0 <= option["native_option_index"] < 512
                or option["native_option_index"] in seen or type(option.get("enabled")) is not bool):
            raise ValueError("invalid or repeated authored Florin event option")
        seen.add(option["native_option_index"])
        normalized.append({"native_option_index": option["native_option_index"], "enabled": option["enabled"]})
    reason = raw.get("unavailable_reason")
    if reason is not None and (not isinstance(reason, str) or not reason or len(reason) > 4096):
        raise ValueError("bounded nullable Florin event reason required")
    if raw["accepted"]:
        if (raw["application_main_observed"] is not True or raw["full_snapshot_before_verified"] is not True
                or raw["effect_attempted"] == query or reason is not None
                or (not query and not any(row["native_option_index"] == native_index and row["enabled"] for row in normalized))):
            raise ValueError("accepted Florin event lacks actual Full/Main/enabled evidence")
    elif normalized:
        raise ValueError("rejected Florin event cannot grant option observation")
    return {"status": status, "accepted": raw["accepted"], "effect_attempted": raw["effect_attempted"], "options": normalized}


def event_option_step(option_number: int) -> str:
    """Return the semantic step for a 1-based native-authored option number.

    ``option_number = native_option_index + 1``, independent of rendered
    order. For visible native indices ``(0, 2)``, use numbers ``(1, 3)``.
    """
    _positive_integer(option_number, "option_number")
    return f"{EVENT_OPTION_STEP_PREFIX}{option_number}"


def parse_event_option_step(step: object) -> int | None:
    """Parse a select-event step, returning its 1-based option number."""
    if not isinstance(step, str) or not step.startswith(EVENT_OPTION_STEP_PREFIX):
        return None
    suffix = step.removeprefix(EVENT_OPTION_STEP_PREFIX)
    if not suffix.isascii() or not suffix.isdigit():
        return None
    option_number = int(suffix)
    return option_number if option_number > 0 else None


def normalize_active_event(
    value: object,
    *,
    default_source: str,
) -> dict[str, object] | None:
    """Normalize native and OCR event shapes into one planner-facing object.

    ``option_number`` is deliberately 1-based because it is also the suffix in
    ``select-event-option-N`` and the existing OCR shortcut number.  ``index``
    remains the zero-based value consumed by ``CSelectEventOptionCommand``.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("active_event must be an object or null")

    instance_id = value.get("instance_id")
    if instance_id is not None:
        _non_negative_integer(instance_id, "active_event instance_id")

    title = value.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise ValueError("active_event title must be a non-empty string or null")

    source = value.get("source", default_source)
    if not isinstance(source, str) or not source:
        raise ValueError("active_event source must be a non-empty string")

    raw_options = value.get("options")
    if raw_options is not None and not isinstance(raw_options, list):
        raise ValueError("active_event options must be a list")
    normalized_by_number: dict[int, dict[str, object]] = {}
    for fallback_number, raw_option in enumerate(raw_options or (), start=1):
        if not isinstance(raw_option, dict):
            raise ValueError("active_event option must be an object")
        option_number = raw_option.get("option_number")
        if option_number is None:
            raw_index = raw_option.get("index")
            if raw_index is None:
                option_number = fallback_number
            else:
                _non_negative_integer(raw_index, "active_event option index")
                option_number = int(raw_index) + 1
        _positive_integer(option_number, "active_event option_number")
        option_number = int(option_number)
        raw_index = raw_option.get("index", option_number - 1)
        _non_negative_integer(raw_index, "active_event option index")
        if int(raw_index) != option_number - 1:
            raise ValueError("active_event option index and option_number disagree")
        if option_number in normalized_by_number:
            raise ValueError("active_event option numbers must be unique")

        label = raw_option.get("label", raw_option.get("visible_text"))
        if label is not None and not isinstance(label, str):
            raise ValueError("active_event option label must be a string or null")
        enabled = raw_option.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("active_event option enabled must be boolean")
        option: dict[str, object] = {
            "index": option_number - 1,
            "option_number": option_number,
            "label": label,
            "enabled": enabled,
        }
        score = raw_option.get("strategy_score")
        if score is not None:
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(
                    "active_event option strategy_score must be numeric or null"
                )
            option["strategy_score"] = score
        reasons = raw_option.get("strategy_reasons")
        if isinstance(reasons, list):
            option["strategy_reasons"] = [
                reason for reason in reasons if isinstance(reason, str)
            ]
        normalized_by_number[option_number] = option

    option_count = value.get("option_count")
    if option_count is None and raw_options is not None:
        option_count = len(normalized_by_number)
    if option_count is not None:
        _non_negative_integer(option_count, "active_event option_count")
        option_count = int(option_count)
        if normalized_by_number and max(normalized_by_number) > option_count:
            raise ValueError("active_event option exceeds option_count")
        for option_number in range(1, option_count + 1):
            normalized_by_number.setdefault(
                option_number,
                {
                    "index": option_number - 1,
                    "option_number": option_number,
                    "label": None,
                    "enabled": True,
                },
            )

    return {
        "source": source,
        "instance_id": instance_id,
        "option_count": option_count,
        "title": title,
        "options": [normalized_by_number[key] for key in sorted(normalized_by_number)],
    }


def choose_event_option_number(active_event: object) -> int | None:
    """Choose the best enabled option, preferring score then visual order."""
    if not isinstance(active_event, dict):
        return None
    options = active_event.get("options")
    if not isinstance(options, list):
        return None
    ranked: list[tuple[float, int]] = []
    for option in options:
        if not isinstance(option, dict) or option.get("enabled") is not True:
            continue
        option_number = option.get("option_number")
        if (
            isinstance(option_number, bool)
            or not isinstance(option_number, int)
            or option_number <= 0
        ):
            continue
        score = option.get("strategy_score", 0)
        numeric_score = (
            float(score)
            if not isinstance(score, bool) and isinstance(score, (int, float))
            else 0.0
        )
        ranked.append((numeric_score, option_number))
    if not ranked:
        return None
    _score, option_number = max(ranked, key=lambda row: (row[0], -row[1]))
    return option_number


def action_step_set(capabilities: object) -> set[str]:
    """Extract exact semantic action names from a driver capability object."""
    raw_steps = (
        capabilities.get("action_steps") if isinstance(capabilities, dict) else None
    )
    if not isinstance(raw_steps, Iterable) or isinstance(raw_steps, (str, bytes)):
        return set()
    return {step for step in raw_steps if isinstance(step, str) and step}


def _positive_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _non_negative_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
