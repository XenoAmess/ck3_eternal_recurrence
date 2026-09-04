"""Fixed promotion-source progress observer and exact review action v1."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_PROMOTION_SOURCE_PROGRESS_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-promotion-source-progress-v1"
)
QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY: Final = (
    "game.contract.zhongguo-promotion-source-progress-v1-fail-closed"
)
QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP: Final = (
    "query-zhongguo-promotion-source-progress-v1"
)
QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP_PREFIX: Final = (
    f"{QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP}-"
)
ACTIVATE_REVIEW_NOW_V1_CAPABILITY: Final = (
    "game.command.activate-zhongguo-review-now-v1"
)
ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY: Final = (
    "game.contract.zhongguo-review-now-action-v1-fail-closed"
)
ACTIVATE_REVIEW_NOW_V1_STEP: Final = "activate-zhongguo-review-now-v1"
PROGRESS_WIDGETS: Final = (
    "zg361_promotion_source_bridge_window",
    "zg361_promotion_source_review_now_action",
    "zg361_promotion_source_b1_active",
    "zg361_promotion_source_central_active",
    "zg361_promotion_source_pp_active",
)
_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")


@dataclass(frozen=True)
class PromotionSourceProgressQueryV1:
    owner_character_id: int
    request_nonce: str


@dataclass(frozen=True)
class ReviewNowActionRequestV1:
    request_nonce: str
    expected_revision: int
    expected_native_revision: int
    expected_connection_generation: int
    expected_player_character_id: int


def _positive(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonce(value: object) -> str:
    if not isinstance(value, str) or _NONCE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a bounded ASCII token")
    return value


def query_promotion_source_progress_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_promotion_source_progress_v1_step(
    step: object,
) -> PromotionSourceProgressQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(QUERY_PROMOTION_SOURCE_PROGRESS_V1_STEP_PREFIX)
    parts = suffix.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0] or not parts[1] or len(parts[1]) % 2:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        if nonce.encode("ascii").hex() != parts[1]:
            return None
        return PromotionSourceProgressQueryV1(
            _positive(owner, "owner_character_id"), _nonce(nonce)
        )
    except (UnicodeDecodeError, ValueError):
        return None


def build_review_now_action_v1_request(
    *, request_nonce: object, expected_revision: object,
    expected_native_revision: object, expected_connection_generation: object,
    expected_player_character_id: object,
) -> ReviewNowActionRequestV1:
    return ReviewNowActionRequestV1(
        request_nonce=_nonce(request_nonce),
        expected_revision=_positive(expected_revision, "expected_revision"),
        expected_native_revision=_positive(
            expected_native_revision, "expected_native_revision"
        ),
        expected_connection_generation=_positive(
            expected_connection_generation, "expected_connection_generation"
        ),
        expected_player_character_id=_positive(
            expected_player_character_id, "expected_player_character_id"
        ),
    )


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed(value: object, name: str, kind: type) -> dict[str, object]:
    field = _exact(value, {"status", "value", "unavailable_reason"}, name)
    if field["status"] == "available":
        raw = field["value"]
        if field["unavailable_reason"] is not None or isinstance(raw, bool) != (
            kind is bool
        ) or not isinstance(raw, kind):
            raise ValueError(f"{name} has an invalid available value")
    elif field["status"] == "unavailable":
        if field["value"] is not None or not isinstance(
            field["unavailable_reason"], str
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    else:
        raise ValueError(f"{name} has invalid status")
    return dict(field)


def normalize_native_promotion_source_progress_v1(
    value: object, *, expected_query: PromotionSourceProgressQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    frame = _exact(
        value,
        {"schema_version", "status", "capability", "source_backend_id",
         "request_nonce", "snapshot_revision", "date_raw", "paused",
         "player_character_id", "widgets", "readiness",
         "unavailable_reason"},
        "promotion_source_progress",
    )
    if (
        frame["schema_version"] != 1
        or frame["capability"] != QUERY_PROMOTION_SOURCE_PROGRESS_V1_CAPABILITY
        or frame["source_backend_id"]
        != "ck3-1.19.0.6-native-zhongguo-promotion-source-progress-v1"
        or frame["request_nonce"] != expected_query.request_nonce
        or frame["snapshot_revision"] != expected_snapshot_revision
        or frame["date_raw"] != expected_date_raw
        or frame["paused"] is not True
        or frame["player_character_id"] != expected_player_character_id
        or expected_query.owner_character_id != expected_player_character_id
    ):
        raise ValueError("paused played-owner binding or provenance changed")
    widgets = frame["widgets"]
    if not isinstance(widgets, list) or len(widgets) != len(PROGRESS_WIDGETS):
        raise ValueError("fixed widget set changed")
    normalized_widgets = []
    for expected, raw in zip(PROGRESS_WIDGETS, widgets, strict=True):
        widget = _exact(
            raw,
            {"stable_identity", "runtime_name", "instance_pointer",
             "vtable_pointer", "exists", "effective_visible", "enabled"},
            f"widget[{expected}]",
        )
        if widget["stable_identity"] != expected or widget["runtime_name"] != expected:
            raise ValueError("fixed widget identity changed")
        normalized_widgets.append({
            **widget,
            "instance_pointer": _typed(widget["instance_pointer"], "instance_pointer", str),
            "vtable_pointer": _typed(widget["vtable_pointer"], "vtable_pointer", str),
            "exists": _typed(widget["exists"], "exists", bool),
            "effective_visible": _typed(
                widget["effective_visible"], "effective_visible", bool
            ),
            "enabled": _typed(widget["enabled"], "enabled", bool),
        })
    readiness = _exact(
        frame["readiness"],
        {"player_binding_ready", "gui_root_ready", "exact_widget_set_ready",
         "same_frame_ready", "query_ready", "production_live_ready"},
        "readiness",
    )
    if any(not isinstance(item, bool) for item in readiness.values()):
        raise ValueError("readiness must be boolean")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid status")
    if frame["status"] == "unavailable" and not isinstance(
        frame["unavailable_reason"], str
    ):
        raise ValueError("typed unavailability lacks reason")
    return {**frame, "widgets": normalized_widgets, "readiness": dict(readiness)}


def widget_visible(progress: dict[str, object], index: int) -> bool:
    widgets = progress.get("widgets")
    if not isinstance(widgets, list) or not 0 <= index < len(widgets):
        return False
    widget = widgets[index]
    field = widget.get("effective_visible") if isinstance(widget, dict) else None
    return isinstance(field, dict) and field.get("status") == "available" and (
        field.get("value") is True
    )


def verify_review_now_independent_postcondition_v1(
    *, action_result: dict[str, object], before_query_sequence: int,
    after_result: dict[str, object], expected_connection_generation: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    if (
        action_result.get("status") != "acknowledged_verification_pending"
        or action_result.get("accepted") is not True
        or action_result.get("production_capability_advertised") is not False
    ):
        raise ValueError("review-now transport did not return a pending ACK")
    after_sequence = _positive(after_result.get("query_sequence"), "query_sequence")
    binding = after_result.get("binding")
    progress = after_result.get("zhongguo_promotion_source_progress")
    if (
        after_sequence <= before_query_sequence
        or not isinstance(binding, dict)
        or binding.get("connection_generation") != expected_connection_generation
        or binding.get("player_character_id") != expected_player_character_id
        or not isinstance(progress, dict)
        or not widget_visible(progress, 2)
        or widget_visible(progress, 1)
    ):
        raise ValueError("independent paused progress query did not prove B1 entry")
    return {
        "status": "verified",
        "proof": "played_owner_b1_active_on_independent_paused_progress_query",
        "action_ack_used_as_state_evidence": False,
        "before_query_sequence": before_query_sequence,
        "after_query_sequence": after_sequence,
    }
