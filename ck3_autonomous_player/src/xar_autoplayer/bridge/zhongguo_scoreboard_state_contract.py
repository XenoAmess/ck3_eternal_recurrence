"""Fixed-name, read-only ZhongGuo scoreboard state and player ACL contract.

The caller supplies only a nonce. Widget names and character-variable keys are
provider-owned allowlists. Fifteen fixed runtime instances expose their stable
identity, instance/vtable pointer and visibility for a later paused action
probe. The v1 query intentionally reports focus, enabled, rect, scroll and
every action as typed unavailable until their exact-build ABI and paused live
evidence exist.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-scoreboard-state-v1"
)
QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP: Final = (
    "query-zhongguo-scoreboard-state-v1"
)
QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP}-"
)
ZHONGGUO_SCOREBOARD_STATE_KIND_V1: Final = (
    "zhongguo.scoreboard.named-state-acl"
)
ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-scoreboard-state-v1"
)
ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-scoreboard-state-v1"
)
ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID: Final = (
    "zg361-scoreboard-fixed-widget-acl-v1"
)
ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_POINTER_RE: Final = re.compile(r"0x[0-9A-F]+\Z")
_WIDGET_IDENTITIES: Final = (
    ("zg361_open_scoreboard", "zg361_scoreboard_toggle"),
    ("zg361_scoreboard_window", "zg361_scoreboard_window"),
    ("zg361_scoreboard_modal", "zg361_scoreboard_modal"),
    ("zg361_scoreboard_panel", "zg361_scoreboard_panel"),
    ("zg361_scoreboard_entry_managed", "zg361_scoreboard_entry_managed"),
    ("zg361_scoreboard_entry_received", "zg361_scoreboard_entry_received"),
    ("zg361_scoreboard_entry_system", "zg361_scoreboard_entry_system"),
    ("zg361_scoreboard_tab_managed", "zg361_scoreboard_tab_managed"),
    ("zg361_scoreboard_tab_received", "zg361_scoreboard_tab_received"),
    ("zg361_scoreboard_tab_system", "zg361_scoreboard_tab_system"),
    ("zg361_scoreboard_page_managed", "zg361_scoreboard_page_managed"),
    ("zg361_scoreboard_page_received", "zg361_scoreboard_page_received"),
    ("zg361_scoreboard_page_system", "zg361_scoreboard_page_system"),
    (
        "zg361_scoreboard_modal_backdrop_close",
        "zg361_scoreboard_modal_backdrop_close",
    ),
    ("zg361_scoreboard_header_close", "zg361_scoreboard_header_close"),
)
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_TYPED_REASONS: Final = {
    "snapshot_unavailable",
    "widget_not_instantiated",
    "named_clickable_child_not_stable",
    "enabled_state_abi_not_frozen",
    "focus_owner_abi_not_frozen",
    "modal_blocking_abi_not_frozen",
    "screen_rect_abi_not_frozen",
    "scroll_area_extent_abi_not_frozen",
    "surface_not_available",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "read_only_provider_action_not_exposed",
    "state_projection_unavailable",
}
_TOP_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "gui_root_unavailable",
    "state_projection_unavailable",
    "widget_state_unavailable",
    "widget_not_instantiated",
    "acl_inconsistent",
    "state_changed",
    "internal_error",
}
_WIDGET_KEYS: Final = {
    "stable_identity",
    "runtime_name",
    "instance_pointer",
    "vtable_pointer",
    "exists",
    "local_visible",
    "effective_visible",
    "enabled",
    "focused",
    "modal_blocking",
    "screen_x",
    "screen_y",
    "screen_width",
    "screen_height",
    "scroll_min",
    "scroll_max",
    "scroll_value",
}
_MANAGED_KEYS: Final = {
    "surface_available",
    "current_player_can_assess_others",
    "owner_character_id",
    "first_subject_character_id",
}
_RECEIVED_KEYS: Final = {
    "surface_available",
    "current_player_is_subject",
    "first_row_character_id",
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "result_case_serial",
    "b1_case_serial",
    "disclosure_acl_mode",
    "disclosure_policy_available",
    "disclosure_policy_id",
    "disclosure_self_mode",
    "disclosure_team_mode",
    "disclosure_evaluator_identity_mode",
    "disclosure_blackbox_risk",
}
_READINESS_KEYS: Final = {
    "player_binding_ready",
    "gui_root_ready",
    "entry_window_state_ready",
    "acl_ready",
    "same_frame_ready",
    "state_acl_query_ready",
    "full_widget_gate_ready",
    "production_live_ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_SCOREBOARD_STATE_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_SCOREBOARD_STATE_V1_ALLOWLIST_ID,
    "gui_global_slot_rva": "0x576CC68",
    "find_top_level_widget_rva": "0x36D0B20",
    "widget_hidden_flags_offset": "0xD0",
    "widget_parent_offset": "0xE8",
    "widget_children_offset": "0xF0",
    "widget_name_offset": "0x1B8",
    "query_scope": "fixed_scoreboard_instances_and_player_frozen_acl",
    "contract_stage": "static_exact_build_live_unverified",
}
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "case_kind",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "widgets",
    "acl",
    "actions",
    "readiness",
    "unavailable_reason",
    "provenance",
}


@dataclass(frozen=True, slots=True)
class ZhongguoScoreboardStateQueryV1:
    request_nonce: str


def _exact(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} has unexpected fields")
    return value


def _integer(value: object, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} is out of range")
    return value


def _typed(
    value: object,
    label: str,
    *,
    kind: str,
) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, label)
    status = field["status"]
    raw = field["value"]
    reason = field["unavailable_reason"]
    if status == "available":
        if reason is not None:
            raise ValueError(f"{label} available value has a reason")
        if kind == "bool":
            if not isinstance(raw, bool):
                raise ValueError(f"{label} must contain a boolean")
        elif kind == "int":
            _integer(raw, label, -(2**63), 2**63 - 1)
        elif kind == "pointer":
            if not isinstance(raw, str) or _POINTER_RE.fullmatch(raw) is None:
                raise ValueError(
                    f"{label} must contain an uppercase hex pointer"
                )
        else:  # pragma: no cover - internal invariant
            raise AssertionError(kind)
    elif status == "unavailable":
        if raw is not None or reason not in _TYPED_REASONS:
            raise ValueError(f"{label} malformed unavailable value")
    else:
        raise ValueError(f"{label} has an invalid status")
    return dict(field)


def query_zhongguo_scoreboard_state_v1_step(request_nonce: str) -> str:
    if not isinstance(request_nonce, str) or _NONCE_RE.fullmatch(
        request_nonce
    ) is None:
        raise ValueError("request_nonce is invalid")
    return f"{QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX}{request_nonce}"


def parse_query_zhongguo_scoreboard_state_v1_step(
    step: object,
) -> ZhongguoScoreboardStateQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX
    ):
        return None
    nonce = step[len(QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP_PREFIX) :]
    if _NONCE_RE.fullmatch(nonce) is None:
        return None
    return ZhongguoScoreboardStateQueryV1(nonce)


def normalize_native_zhongguo_scoreboard_state_v1(
    value: object,
    *,
    expected_query: ZhongguoScoreboardStateQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    frame = _exact(value, _FRAME_KEYS, "scoreboard_state")
    if frame["schema_version"] != 1:
        raise ValueError("scoreboard_state schema_version is not 1")
    if frame["case_kind"] != ZHONGGUO_SCOREBOARD_STATE_KIND_V1:
        raise ValueError("scoreboard_state case kind drifted")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("scoreboard_state nonce mismatch")
    if frame["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("scoreboard_state native revision mismatch")
    if frame["date_raw"] != expected_date_raw or frame["paused"] is not True:
        raise ValueError("scoreboard_state is not bound to the paused date")
    if frame["player_character_id"] != expected_player_character_id:
        raise ValueError("scoreboard_state player mismatch")
    status = frame["status"]
    if status not in {"available", "unavailable"}:
        raise ValueError("scoreboard_state status is invalid")
    reason = frame["unavailable_reason"]
    if (status == "available" and reason is not None) or (
        status == "unavailable" and reason not in _TOP_REASONS
    ):
        raise ValueError("scoreboard_state top-level reason is invalid")

    widgets = frame["widgets"]
    if not isinstance(widgets, list) or len(widgets) != len(
        _WIDGET_IDENTITIES
    ):
        raise ValueError("scoreboard_state widgets are incomplete")
    normalized_widgets: list[dict[str, object]] = []
    for index, expected in enumerate(_WIDGET_IDENTITIES):
        widget = _exact(widgets[index], _WIDGET_KEYS, f"widget[{index}]")
        if (widget["stable_identity"], widget["runtime_name"]) != expected:
            raise ValueError(f"widget[{index}] identity drifted")
        normalized = {
            "stable_identity": widget["stable_identity"],
            "runtime_name": widget["runtime_name"],
            "instance_pointer": _typed(
                widget["instance_pointer"],
                f"widget[{index}].instance_pointer",
                kind="pointer",
            ),
            "vtable_pointer": _typed(
                widget["vtable_pointer"],
                f"widget[{index}].vtable_pointer",
                kind="pointer",
            ),
        }
        for key in (
            "exists",
            "local_visible",
            "effective_visible",
            "enabled",
            "focused",
            "modal_blocking",
        ):
            normalized[key] = _typed(widget[key], f"widget[{index}].{key}", kind="bool")
        for key in (
            "screen_x",
            "screen_y",
            "screen_width",
            "screen_height",
            "scroll_min",
            "scroll_max",
            "scroll_value",
        ):
            normalized[key] = _typed(widget[key], f"widget[{index}].{key}", kind="int")
        normalized_widgets.append(normalized)
        if status == "available" and (
            normalized["instance_pointer"]["status"] != "available"
            or normalized["vtable_pointer"]["status"] != "available"
        ):
            raise ValueError(f"widget[{index}] lacks paused probe pointers")

    acl = _exact(frame["acl"], {"managed", "received_self"}, "acl")
    managed = _exact(acl["managed"], _MANAGED_KEYS, "acl.managed")
    received = _exact(
        acl["received_self"], _RECEIVED_KEYS, "acl.received_self"
    )
    for key in ("surface_available", "current_player_can_assess_others"):
        if not isinstance(managed[key], bool):
            raise ValueError(f"acl.managed.{key} must be boolean")
    normalized_managed = {
        **managed,
        "owner_character_id": _typed(
            managed["owner_character_id"],
            "acl.managed.owner_character_id",
            kind="int",
        ),
        "first_subject_character_id": _typed(
            managed["first_subject_character_id"],
            "acl.managed.first_subject_character_id",
            kind="int",
        ),
    }
    for key in ("surface_available", "current_player_is_subject"):
        if not isinstance(received[key], bool):
            raise ValueError(f"acl.received_self.{key} must be boolean")
    normalized_received = dict(received)
    for key in _RECEIVED_KEYS - {
        "surface_available",
        "current_player_is_subject",
    }:
        normalized_received[key] = _typed(
            received[key], f"acl.received_self.{key}", kind="int"
        )
    if status == "available":
        if managed["current_player_can_assess_others"] is not managed[
            "surface_available"
        ]:
            raise ValueError("managed ACL is not surface-derived")
        if received["current_player_is_subject"] is not received[
            "surface_available"
        ]:
            raise ValueError("received-self ACL is not player-bound")

    actions = _exact(frame["actions"], {"activate", "close", "reopen"}, "actions")
    normalized_actions = {
        key: _typed(actions[key], f"actions.{key}", kind="bool")
        for key in ("activate", "close", "reopen")
    }
    for key, action in normalized_actions.items():
        if action["status"] != "unavailable" or action[
            "unavailable_reason"
        ] != "read_only_provider_action_not_exposed":
            raise ValueError(f"actions.{key} falsely advertises a write")

    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(readiness[key], bool) for key in _READINESS_KEYS):
        raise ValueError("scoreboard_state readiness must be boolean")
    if readiness["full_widget_gate_ready"] or readiness[
        "production_live_ready"
    ]:
        raise ValueError("static v1 must not claim full/live readiness")
    if status == "available" and not readiness["state_acl_query_ready"]:
        raise ValueError("available scoreboard_state lacks minimal readiness")

    provenance = _exact(
        frame["provenance"], set(_PROVENANCE_VALUES), "provenance"
    )
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("scoreboard_state provenance drifted")
    return {
        **frame,
        "widgets": normalized_widgets,
        "acl": {
            "managed": normalized_managed,
            "received_self": normalized_received,
        },
        "actions": normalized_actions,
        "readiness": dict(readiness),
        "provenance": dict(provenance),
    }
