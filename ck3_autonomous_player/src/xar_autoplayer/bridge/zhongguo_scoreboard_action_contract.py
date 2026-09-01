"""Allowlisted ZhongGuo scoreboard named-widget action contract.

This module is deliberately independent from the shared native driver and MCP
facade.  It freezes the request, admission, ACK, and independent post-query
rules needed to wire those layers later.  An ACK proves only that one exact
allowlisted runtime instance was dispatched; it never proves the GUI changed.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY: Final = (
    "game.command.activate-zhongguo-scoreboard-v1"
)
ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP: Final = (
    "activate-zhongguo-scoreboard-v1"
)
ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY: Final = (
    "game.contract.zhongguo-scoreboard-action-v1-fail-closed"
)
ZHONGGUO_SCOREBOARD_ACTION_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_SCOREBOARD_ACTION_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_SCOREBOARD_ACTION_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1"
)
ZHONGGUO_SCOREBOARD_ACTION_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-scoreboard-action-v1"
)
ZHONGGUO_SCOREBOARD_ACTION_V1_ALLOWLIST_ID: Final = (
    "zg361-scoreboard-named-widget-action-v1"
)

ACTION_KEYS: Final = frozenset(
    {
        "open",
        "switch-managed",
        "switch-received",
        "switch-system",
        "close",
        "reopen",
    }
)
_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_POINTER_RE: Final = re.compile(r"0x[0-9A-F]+\Z")
_PROVIDER_SESSION_RE: Final = re.compile(r"[0-9A-F]{32}\Z")
_FINGERPRINT_RE: Final = re.compile(r"[0-9A-F]{64}\Z")

_WINDOW = "zg361_scoreboard_window"
_MODAL = "zg361_scoreboard_modal"
_ENTRY_TARGETS: Final = {
    "managed": "zg361_scoreboard_entry_managed",
    "received": "zg361_scoreboard_entry_received",
    "system": "zg361_scoreboard_entry_system",
}
_TAB_TARGETS: Final = {
    "managed": "zg361_scoreboard_tab_managed",
    "received": "zg361_scoreboard_tab_received",
    "system": "zg361_scoreboard_tab_system",
}
_PAGE_WITNESSES: Final = {
    "managed": "zg361_scoreboard_page_managed",
    "received": "zg361_scoreboard_page_received",
    "system": "zg361_scoreboard_page_system",
}
_CLOSE_TARGET = "zg361_scoreboard_header_close"
_FIXED_WIDGETS: Final = frozenset(
    {
        "zg361_open_scoreboard",
        _WINDOW,
        _MODAL,
        "zg361_scoreboard_panel",
        *_ENTRY_TARGETS.values(),
        *_TAB_TARGETS.values(),
        *_PAGE_WITNESSES.values(),
        "zg361_scoreboard_modal_backdrop_close",
        _CLOSE_TARGET,
    }
)
_ACK_KEYS: Final = {
    "schema_version",
    "status",
    "accepted",
    "capability",
    "step",
    "request_nonce",
    "action",
    "source",
    "target",
    "expected_postcondition",
    "native_handled",
    "postcondition_verified",
    "provenance",
}
_SOURCE_KEYS: Final = {
    "revision",
    "native_revision",
    "connection_generation",
    "date_raw",
    "player_character_id",
    "provider_session_id",
    "observation_sequence",
    "observed_state_revision",
    "tree_fingerprint_v1",
    "semantic_fingerprint_v1",
    "window_instance_pointer",
}
_TARGET_KEYS: Final = {
    "stable_identity",
    "runtime_name",
    "instance_pointer",
    "vtable_pointer",
}
_POST_KEYS: Final = {
    "requires_independent_query",
    "minimum_observation_sequence",
    "minimum_observed_state_revision",
    "expected_provider_session_id",
    "expected_tree_fingerprint_v1",
    "modal_effective_visible",
    "active_tab",
    "list_view_required",
    "expected_window_instance_pointer",
}
_NATIVE_RESULT_KEYS: Final = {
    "step",
    "accepted",
    "status",
    "request_nonce",
    "action",
    "action_sequence",
    "snapshot_revision",
    "rejection_reason",
    "action_ack",
    "production_capability_advertised",
    "backend_id",
}
_PROVENANCE: Final = {
    "game_version": ZHONGGUO_SCOREBOARD_ACTION_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_SCOREBOARD_ACTION_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_SCOREBOARD_ACTION_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_SCOREBOARD_ACTION_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_SCOREBOARD_ACTION_V1_ALLOWLIST_ID,
    "contract_stage": "exact_dispatch_ack_provider_revision_live_unverified",
}


class ScoreboardActionRejected(ValueError):
    """Typed fail-closed action admission error."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class ZhongguoScoreboardActionRequestV1:
    request_nonce: str
    action: str
    expected_revision: int
    expected_native_revision: int
    expected_connection_generation: int
    expected_player_character_id: int
    expected_provider_session_id: str
    expected_observation_sequence: int
    expected_observed_state_revision: int
    expected_tree_fingerprint_v1: str
    expected_semantic_fingerprint_v1: str
    expected_window_instance_pointer: str
    expected_target_instance_pointer: str
    expected_target_vtable_pointer: str


def _uint64(value: object, label: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    minimum = 1 if positive else 0
    if not minimum <= value <= 2**64 - 1:
        raise ValueError(f"{label} is out of range")
    return value


def _character_id(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if not 1 <= value <= 2**31 - 1:
        raise ValueError(f"{label} is out of range")
    return value


def _pointer(value: object, label: str) -> str:
    if not isinstance(value, str) or _POINTER_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an uppercase hexadecimal pointer")
    return value


def _provider_session_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _PROVIDER_SESSION_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be 32 uppercase hexadecimal digits")
    return value


def _fingerprint(value: object, label: str) -> str:
    if not isinstance(value, str) or _FINGERPRINT_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be 64 uppercase hexadecimal digits")
    return value


def build_zhongguo_scoreboard_action_v1_request(
    *,
    request_nonce: str,
    action: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_player_character_id: int,
    expected_provider_session_id: str,
    expected_observation_sequence: int,
    expected_observed_state_revision: int,
    expected_tree_fingerprint_v1: str,
    expected_semantic_fingerprint_v1: str,
    expected_window_instance_pointer: str,
    expected_target_instance_pointer: str,
    expected_target_vtable_pointer: str,
) -> ZhongguoScoreboardActionRequestV1:
    if not isinstance(request_nonce, str) or _NONCE_RE.fullmatch(
        request_nonce
    ) is None:
        raise ValueError("request_nonce is invalid")
    if action not in ACTION_KEYS:
        raise ValueError("action is not allowlisted")
    return ZhongguoScoreboardActionRequestV1(
        request_nonce=request_nonce,
        action=action,
        expected_revision=_uint64(expected_revision, "expected_revision"),
        expected_native_revision=_uint64(
            expected_native_revision,
            "expected_native_revision",
            positive=True,
        ),
        expected_connection_generation=_uint64(
            expected_connection_generation,
            "expected_connection_generation",
            positive=True,
        ),
        expected_player_character_id=_character_id(
            expected_player_character_id,
            "expected_player_character_id",
        ),
        expected_provider_session_id=_provider_session_id(
            expected_provider_session_id,
            "expected_provider_session_id",
        ),
        expected_observation_sequence=_uint64(
            expected_observation_sequence,
            "expected_observation_sequence",
            positive=True,
        ),
        expected_observed_state_revision=_uint64(
            expected_observed_state_revision,
            "expected_observed_state_revision",
            positive=True,
        ),
        expected_tree_fingerprint_v1=_fingerprint(
            expected_tree_fingerprint_v1,
            "expected_tree_fingerprint_v1",
        ),
        expected_semantic_fingerprint_v1=_fingerprint(
            expected_semantic_fingerprint_v1,
            "expected_semantic_fingerprint_v1",
        ),
        expected_window_instance_pointer=_pointer(
            expected_window_instance_pointer,
            "expected_window_instance_pointer",
        ),
        expected_target_instance_pointer=_pointer(
            expected_target_instance_pointer,
            "expected_target_instance_pointer",
        ),
        expected_target_vtable_pointer=_pointer(
            expected_target_vtable_pointer,
            "expected_target_vtable_pointer",
        ),
    )


def _typed_bool(widget: dict[str, object], key: str, reason: str) -> bool:
    value = widget.get(key)
    if not isinstance(value, dict):
        raise ScoreboardActionRejected(f"{reason}_unavailable")
    if value.get("status") != "available" or not isinstance(
        value.get("value"), bool
    ):
        raise ScoreboardActionRejected(f"{reason}_unavailable")
    return bool(value["value"])


def _typed_pointer(widget: dict[str, object], key: str, reason: str) -> str:
    value = widget.get(key)
    if not isinstance(value, dict) or value.get("status") != "available":
        raise ScoreboardActionRejected(f"{reason}_unavailable")
    try:
        return _pointer(value.get("value"), reason)
    except ValueError as error:
        raise ScoreboardActionRejected(f"{reason}_unavailable") from error


def _widgets_by_identity(source_state: dict[str, object]) -> dict[str, dict[str, object]]:
    raw = source_state.get("widgets")
    if not isinstance(raw, list) or len(raw) != len(_FIXED_WIDGETS):
        raise ScoreboardActionRejected("fixed_widget_projection_incomplete")
    result: dict[str, dict[str, object]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ScoreboardActionRejected("fixed_widget_projection_incomplete")
        identity = item.get("stable_identity")
        runtime_name = item.get("runtime_name")
        if (
            not isinstance(identity, str)
            or identity not in _FIXED_WIDGETS
            or identity in result
            or runtime_name != identity
            and not (
                identity == "zg361_open_scoreboard"
                and runtime_name == "zg361_scoreboard_toggle"
            )
        ):
            raise ScoreboardActionRejected("fixed_widget_identity_mismatch")
        result[identity] = item
    if set(result) != _FIXED_WIDGETS:
        raise ScoreboardActionRejected("fixed_widget_projection_incomplete")
    return result


def _usable_target(
    widget: dict[str, object],
    *,
    expected_instance_pointer: str,
    expected_vtable_pointer: str,
) -> tuple[str, str]:
    if not _typed_bool(widget, "exists", "target_exists"):
        raise ScoreboardActionRejected("target_not_instantiated")
    if not _typed_bool(widget, "effective_visible", "target_visibility"):
        raise ScoreboardActionRejected("target_not_visible")
    if not _typed_bool(widget, "enabled", "target_enabled"):
        raise ScoreboardActionRejected("target_disabled")
    instance = _typed_pointer(widget, "instance_pointer", "target_instance")
    vtable = _typed_pointer(widget, "vtable_pointer", "target_vtable")
    if instance != expected_instance_pointer:
        raise ScoreboardActionRejected("target_instance_mismatch")
    if vtable != expected_vtable_pointer:
        raise ScoreboardActionRejected("target_vtable_mismatch")
    return instance, vtable


def plan_zhongguo_scoreboard_action_v1(
    request: ZhongguoScoreboardActionRequestV1,
    *,
    source_state: dict[str, object],
    observed_revision: int,
    observed_connection_generation: int,
) -> dict[str, object]:
    """Admit one action and return an executor plan, never a success ACK."""

    if source_state.get("status") != "available" or source_state.get(
        "paused"
    ) is not True:
        raise ScoreboardActionRejected("source_state_unavailable")
    if (
        request.expected_observation_sequence == 2**64 - 1
        or request.expected_observed_state_revision == 2**64 - 1
    ):
        raise ScoreboardActionRejected("revision_overflow")
    if observed_revision != request.expected_revision:
        raise ScoreboardActionRejected("revision_mismatch")
    if (
        source_state.get("snapshot_revision")
        != request.expected_native_revision
    ):
        raise ScoreboardActionRejected("native_revision_mismatch")
    if observed_connection_generation != request.expected_connection_generation:
        raise ScoreboardActionRejected("connection_generation_mismatch")
    if (
        source_state.get("player_character_id")
        != request.expected_player_character_id
    ):
        raise ScoreboardActionRejected("player_binding_mismatch")
    if source_state.get("provider_session_id") != (
        request.expected_provider_session_id
    ):
        raise ScoreboardActionRejected("provider_session_mismatch")
    if source_state.get("observation_sequence") != (
        request.expected_observation_sequence
    ):
        raise ScoreboardActionRejected("observation_sequence_mismatch")
    if source_state.get("observed_state_revision") != (
        request.expected_observed_state_revision
    ):
        raise ScoreboardActionRejected("observed_state_revision_mismatch")
    if source_state.get("tree_fingerprint_v1") != (
        request.expected_tree_fingerprint_v1
    ):
        raise ScoreboardActionRejected("tree_fingerprint_mismatch")
    if source_state.get("semantic_fingerprint_v1") != (
        request.expected_semantic_fingerprint_v1
    ):
        raise ScoreboardActionRejected("semantic_fingerprint_mismatch")
    readiness = source_state.get("readiness")
    if not isinstance(readiness, dict) or any(
        readiness.get(key) is not True
        for key in (
            "player_binding_ready",
            "gui_root_ready",
            "entry_window_state_ready",
            "acl_ready",
            "same_frame_ready",
            "state_acl_query_ready",
        )
    ):
        raise ScoreboardActionRejected("player_or_same_frame_not_ready")

    widgets = _widgets_by_identity(source_state)
    window = widgets[_WINDOW]
    if not _typed_bool(window, "exists", "window_exists"):
        raise ScoreboardActionRejected("window_not_instantiated")
    window_instance = _typed_pointer(
        window, "instance_pointer", "window_instance"
    )
    if window_instance != request.expected_window_instance_pointer:
        raise ScoreboardActionRejected("window_instance_mismatch")
    modal_visible = _typed_bool(
        widgets[_MODAL], "effective_visible", "modal_visibility"
    )

    active_tab: str | None
    if request.action == "reopen":
        raise ScoreboardActionRejected("reopen_requires_two_phase_sequence")
    if request.action == "open":
        if modal_visible:
            raise ScoreboardActionRejected("scoreboard_already_open")
        visible_entries: list[tuple[str, str]] = []
        for tab, identity in _ENTRY_TARGETS.items():
            try:
                visible = _typed_bool(
                    widgets[identity], "effective_visible", "target_visibility"
                )
            except ScoreboardActionRejected:
                visible = False
            if visible:
                visible_entries.append((tab, identity))
        if len(visible_entries) != 1:
            raise ScoreboardActionRejected("entry_target_not_unique")
        active_tab, target_identity = visible_entries[0]
    elif request.action.startswith("switch-"):
        if not modal_visible:
            raise ScoreboardActionRejected("scoreboard_not_open")
        active_tab = request.action.removeprefix("switch-")
        target_identity = _TAB_TARGETS[active_tab]
        acl = source_state.get("acl")
        if not isinstance(acl, dict):
            raise ScoreboardActionRejected("acl_unavailable")
        if active_tab == "managed":
            managed = acl.get("managed")
            if not isinstance(managed, dict) or managed.get(
                "current_player_can_assess_others"
            ) is not True:
                raise ScoreboardActionRejected("managed_acl_denied")
        if active_tab == "received":
            received = acl.get("received_self")
            if not isinstance(received, dict) or received.get(
                "surface_available"
            ) is not True:
                raise ScoreboardActionRejected("received_acl_denied")
        if _typed_bool(
            widgets[_PAGE_WITNESSES[active_tab]],
            "effective_visible",
            "active_page_visibility",
        ):
            raise ScoreboardActionRejected("action_noop")
    else:
        if not modal_visible:
            raise ScoreboardActionRejected("scoreboard_not_open")
        active_tab = None
        target_identity = _CLOSE_TARGET

    target = widgets[target_identity]
    instance, vtable = _usable_target(
        target,
        expected_instance_pointer=request.expected_target_instance_pointer,
        expected_vtable_pointer=request.expected_target_vtable_pointer,
    )
    runtime_name = target.get("runtime_name")
    if runtime_name != target_identity:
        raise ScoreboardActionRejected("target_runtime_identity_mismatch")
    date_raw = source_state.get("date_raw")
    if isinstance(date_raw, bool) or not isinstance(date_raw, int):
        raise ScoreboardActionRejected("source_date_unavailable")
    return {
        "request": request,
        "source": {
            "revision": observed_revision,
            "native_revision": request.expected_native_revision,
            "connection_generation": observed_connection_generation,
            "date_raw": date_raw,
            "player_character_id": request.expected_player_character_id,
            "provider_session_id": request.expected_provider_session_id,
            "observation_sequence": request.expected_observation_sequence,
            "observed_state_revision": (
                request.expected_observed_state_revision
            ),
            "tree_fingerprint_v1": request.expected_tree_fingerprint_v1,
            "semantic_fingerprint_v1": (
                request.expected_semantic_fingerprint_v1
            ),
            "window_instance_pointer": window_instance,
        },
        "target": {
            "stable_identity": target_identity,
            "runtime_name": runtime_name,
            "instance_pointer": instance,
            "vtable_pointer": vtable,
        },
        "expected_postcondition": {
            "requires_independent_query": True,
            "minimum_observation_sequence": (
                request.expected_observation_sequence + 1
            ),
            "minimum_observed_state_revision": (
                request.expected_observed_state_revision + 1
            ),
            "expected_provider_session_id": (
                request.expected_provider_session_id
            ),
            "expected_tree_fingerprint_v1": (
                request.expected_tree_fingerprint_v1
            ),
            "modal_effective_visible": request.action != "close",
            "active_tab": active_tab,
            "list_view_required": request.action != "close",
            "expected_window_instance_pointer": window_instance,
        },
    }


def acknowledged_zhongguo_scoreboard_action_v1(
    plan: dict[str, object],
) -> dict[str, object]:
    """Create the ACK shape after an executor accepted the admitted plan."""

    request = plan.get("request")
    if not isinstance(request, ZhongguoScoreboardActionRequestV1):
        raise ValueError("action plan lacks its frozen request")
    return {
        "schema_version": 1,
        "status": "acknowledged_verification_pending",
        "accepted": True,
        "capability": ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
        "step": ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
        "request_nonce": request.request_nonce,
        "action": request.action,
        "source": dict(plan["source"]),
        "target": dict(plan["target"]),
        "expected_postcondition": dict(plan["expected_postcondition"]),
        "native_handled": False,
        "postcondition_verified": False,
        "provenance": dict(_PROVENANCE),
    }


def normalize_zhongguo_scoreboard_action_v1_ack(
    value: object,
    *,
    expected_request: ZhongguoScoreboardActionRequestV1,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _ACK_KEYS:
        raise ValueError("scoreboard action ACK has unexpected fields")
    if (
        value["schema_version"] != 1
        or value["status"] != "acknowledged_verification_pending"
        or value["accepted"] is not True
        or value["capability"] != ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY
        or value["step"] != ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP
        or value["request_nonce"] != expected_request.request_nonce
        or value["action"] != expected_request.action
        or not isinstance(value["native_handled"], bool)
        or value["postcondition_verified"] is not False
        or value["provenance"] != _PROVENANCE
    ):
        raise ValueError("scoreboard action ACK identity drifted")
    source = value["source"]
    target = value["target"]
    post = value["expected_postcondition"]
    if not isinstance(source, dict) or set(source) != _SOURCE_KEYS:
        raise ValueError("scoreboard action ACK source binding drifted")
    if not isinstance(target, dict) or set(target) != _TARGET_KEYS:
        raise ValueError("scoreboard action ACK target binding drifted")
    if not isinstance(post, dict) or set(post) != _POST_KEYS:
        raise ValueError("scoreboard action ACK postcondition drifted")
    if (
        source["revision"] != expected_request.expected_revision
        or source["native_revision"]
        != expected_request.expected_native_revision
        or source["connection_generation"]
        != expected_request.expected_connection_generation
        or source["player_character_id"]
        != expected_request.expected_player_character_id
        or source["provider_session_id"]
        != expected_request.expected_provider_session_id
        or source["observation_sequence"]
        != expected_request.expected_observation_sequence
        or source["observed_state_revision"]
        != expected_request.expected_observed_state_revision
        or source["tree_fingerprint_v1"]
        != expected_request.expected_tree_fingerprint_v1
        or source["semantic_fingerprint_v1"]
        != expected_request.expected_semantic_fingerprint_v1
        or source["window_instance_pointer"]
        != expected_request.expected_window_instance_pointer
        or target["instance_pointer"]
        != expected_request.expected_target_instance_pointer
        or target["vtable_pointer"]
        != expected_request.expected_target_vtable_pointer
    ):
        raise ValueError("scoreboard action ACK does not match its request")
    _pointer(source["window_instance_pointer"], "window_instance_pointer")
    _provider_session_id(source["provider_session_id"], "provider_session_id")
    _uint64(source["observation_sequence"], "observation_sequence", positive=True)
    _uint64(
        source["observed_state_revision"],
        "observed_state_revision",
        positive=True,
    )
    _fingerprint(source["tree_fingerprint_v1"], "tree_fingerprint_v1")
    _fingerprint(source["semantic_fingerprint_v1"], "semantic_fingerprint_v1")
    _pointer(target["instance_pointer"], "target.instance_pointer")
    _pointer(target["vtable_pointer"], "target.vtable_pointer")
    if expected_request.action.startswith("switch-"):
        expected_targets = {
            _TAB_TARGETS[expected_request.action.removeprefix("switch-")]
        }
    elif expected_request.action == "close":
        expected_targets = {_CLOSE_TARGET}
    else:
        expected_targets = set(_ENTRY_TARGETS.values())
    if (
        target["stable_identity"] not in expected_targets
        or target["runtime_name"] != target["stable_identity"]
        or post["requires_independent_query"] is not True
        or post["minimum_observation_sequence"]
        != source["observation_sequence"] + 1
        or post["minimum_observed_state_revision"]
        != source["observed_state_revision"] + 1
        or post["expected_provider_session_id"]
        != source["provider_session_id"]
        or post["expected_tree_fingerprint_v1"]
        != source["tree_fingerprint_v1"]
        or post["expected_window_instance_pointer"]
        != source["window_instance_pointer"]
        or not isinstance(post["list_view_required"], bool)
        or not isinstance(post["modal_effective_visible"], bool)
        or post["active_tab"] not in {None, "managed", "received", "system"}
    ):
        raise ValueError("scoreboard action ACK is internally inconsistent")
    expected_tab = None
    if expected_request.action.startswith("switch-"):
        expected_tab = expected_request.action.removeprefix("switch-")
    elif expected_request.action in {"open", "reopen"}:
        expected_tab = next(
            tab
            for tab, identity in _ENTRY_TARGETS.items()
            if identity == target["stable_identity"]
        )
    if post["active_tab"] != expected_tab:
        raise ValueError("scoreboard action ACK active tab drifted")
    return {
        **value,
        "source": dict(source),
        "target": dict(target),
        "expected_postcondition": dict(post),
        "provenance": dict(value["provenance"]),
    }


def normalize_native_zhongguo_scoreboard_action_v1_result(
    value: object,
    *,
    expected_request: ZhongguoScoreboardActionRequestV1,
) -> dict[str, object]:
    """Validate one native transport result without promoting unavailable.

    The fail-closed transport capability is intentionally distinct from the
    production action capability.  Once the exact dispatcher is wired, that
    transport may return an ACK with ``production_capability_advertised=false``;
    the ACK proves submission only and remains unusable as gameplay success
    until a later provider-owned observation revision verifies postconditions.
    """

    if not isinstance(value, dict) or set(value) != _NATIVE_RESULT_KEYS:
        raise ValueError("scoreboard action native result has unexpected fields")
    if (
        value["step"] != ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP
        or value["request_nonce"] != expected_request.request_nonce
        or value["action"] != expected_request.action
    ):
        raise ValueError("scoreboard action native result binding drifted")
    action_sequence = _uint64(
        value["action_sequence"], "action_sequence", positive=True
    )
    snapshot_revision = _uint64(
        value["snapshot_revision"], "snapshot_revision", positive=True
    )
    backend_id = value["backend_id"]
    if not isinstance(backend_id, str) or not backend_id:
        raise ValueError("scoreboard action native result lacks backend_id")
    advertised = value["production_capability_advertised"]
    if not isinstance(advertised, bool):
        raise ValueError("scoreboard action production capability flag is invalid")
    if value["accepted"] is False:
        reason = value["rejection_reason"]
        if (
            value["status"] != "unavailable"
            or not isinstance(reason, str)
            or not reason
            or value["action_ack"] is not None
            or advertised
        ):
            raise ValueError("scoreboard action unavailable result is inconsistent")
        ack = None
    elif value["accepted"] is True:
        if (
            value["status"] != "acknowledged_verification_pending"
            or value["rejection_reason"] is not None
        ):
            raise ValueError("scoreboard action ACK is inconsistent")
        ack = normalize_zhongguo_scoreboard_action_v1_ack(
            value["action_ack"], expected_request=expected_request
        )
    else:
        raise ValueError("scoreboard action accepted flag is invalid")
    return {
        **value,
        "action_sequence": action_sequence,
        "snapshot_revision": snapshot_revision,
        "action_ack": ack,
    }


def verify_zhongguo_scoreboard_action_v1_postcondition(
    ack: dict[str, object],
    *,
    post_state: dict[str, object],
    observed_revision: int,
    observed_connection_generation: int,
) -> dict[str, object]:
    """Verify a later query; this is the only function that returns PASS."""

    source = ack.get("source")
    expected = ack.get("expected_postcondition")
    if not isinstance(source, dict) or not isinstance(expected, dict):
        raise ScoreboardActionRejected("ack_binding_unavailable")
    if post_state.get("status") != "available" or post_state.get(
        "paused"
    ) is not True:
        raise ScoreboardActionRejected("post_state_unavailable")
    if observed_revision != source["revision"]:
        raise ScoreboardActionRejected("post_revision_mismatch")
    native_revision = post_state.get("snapshot_revision")
    if (
        isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision != source["native_revision"]
    ):
        raise ScoreboardActionRejected("post_native_revision_mismatch")
    if observed_connection_generation != source["connection_generation"]:
        raise ScoreboardActionRejected("post_connection_generation_mismatch")
    if post_state.get("player_character_id") != source["player_character_id"]:
        raise ScoreboardActionRejected("post_player_binding_mismatch")
    if post_state.get("date_raw") != source["date_raw"]:
        raise ScoreboardActionRejected("post_date_mismatch")
    if post_state.get("provider_session_id") != (
        expected["expected_provider_session_id"]
    ):
        raise ScoreboardActionRejected("post_provider_session_mismatch")
    observation_sequence = post_state.get("observation_sequence")
    if (
        isinstance(observation_sequence, bool)
        or not isinstance(observation_sequence, int)
        or observation_sequence < expected["minimum_observation_sequence"]
    ):
        raise ScoreboardActionRejected("post_observation_sequence_not_advanced")
    observed_state_revision = post_state.get("observed_state_revision")
    if (
        isinstance(observed_state_revision, bool)
        or not isinstance(observed_state_revision, int)
        or observed_state_revision
        < expected["minimum_observed_state_revision"]
    ):
        raise ScoreboardActionRejected("post_observed_state_revision_not_advanced")
    if post_state.get("tree_fingerprint_v1") != (
        expected["expected_tree_fingerprint_v1"]
    ):
        raise ScoreboardActionRejected("post_tree_fingerprint_mismatch")
    semantic_fingerprint = post_state.get("semantic_fingerprint_v1")
    if semantic_fingerprint == source["semantic_fingerprint_v1"]:
        raise ScoreboardActionRejected("post_semantic_fingerprint_unchanged")
    try:
        _fingerprint(semantic_fingerprint, "post semantic_fingerprint_v1")
    except ValueError as error:
        raise ScoreboardActionRejected(
            "post_semantic_fingerprint_unavailable"
        ) from error
    post_query_nonce = post_state.get("request_nonce")
    if (
        not isinstance(post_query_nonce, str)
        or _NONCE_RE.fullmatch(post_query_nonce) is None
    ):
        raise ScoreboardActionRejected("post_query_nonce_unavailable")
    if post_query_nonce == ack.get("request_nonce"):
        raise ScoreboardActionRejected("post_query_nonce_not_independent")
    widgets = _widgets_by_identity(post_state)
    window_instance = _typed_pointer(
        widgets[_WINDOW], "instance_pointer", "post_window_instance"
    )
    if window_instance != expected["expected_window_instance_pointer"]:
        raise ScoreboardActionRejected("post_window_instance_mismatch")
    modal_visible = _typed_bool(
        widgets[_MODAL], "effective_visible", "post_modal_visibility"
    )
    if modal_visible is not expected["modal_effective_visible"]:
        raise ScoreboardActionRejected("post_modal_visibility_mismatch")
    visible_pages = []
    for tab, identity in _PAGE_WITNESSES.items():
        if _typed_bool(
            widgets[identity], "effective_visible", "post_page_visibility"
        ):
            visible_pages.append(tab)
    active_tab = expected["active_tab"]
    if active_tab is None:
        if visible_pages:
            raise ScoreboardActionRejected("closed_scoreboard_has_visible_page")
    elif visible_pages != [active_tab]:
        raise ScoreboardActionRejected("post_active_tab_mismatch")
    return {
        "schema_version": 1,
        "status": "verified",
        "action_request_nonce": ack["request_nonce"],
        "post_query_nonce": post_query_nonce,
        "source_revision": source["revision"],
        "post_revision": observed_revision,
        "source_native_revision": source["native_revision"],
        "post_native_revision": native_revision,
        "provider_session_id": source["provider_session_id"],
        "source_observation_sequence": source["observation_sequence"],
        "post_observation_sequence": observation_sequence,
        "source_observed_state_revision": source["observed_state_revision"],
        "post_observed_state_revision": observed_state_revision,
        "tree_fingerprint_v1": source["tree_fingerprint_v1"],
        "source_semantic_fingerprint_v1": source[
            "semantic_fingerprint_v1"
        ],
        "post_semantic_fingerprint_v1": semantic_fingerprint,
        "player_character_id": source["player_character_id"],
        "window_instance_pointer": window_instance,
        "modal_effective_visible": modal_visible,
        "active_tab": active_tab,
        "list_view_verified": bool(expected["list_view_required"]),
        "postcondition_verified": True,
    }
