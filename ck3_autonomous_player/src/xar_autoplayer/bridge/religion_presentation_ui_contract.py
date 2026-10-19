"""Finite exact .4 presentation selectors; no widget/path/RVA inputs.

Original GUI dispatch remains in the owning-thread provider. An action ACK and
the later native observation are separate; neither claims rendered pixels.
"""
from __future__ import annotations

import re
import hashlib
from typing import Literal
from .clerical_preview_ui_contract import KEYS as CLERICAL_KEYS, validate_request as validate_clerical_request, normalize as normalize_clerical_result

PresentationWindowKind = Literal["faith", "holding", "personal_beliefs", "rite_creation", "clerical_interaction"]
PresentationTarget = Literal["faith_core_tenet", "faith_doctrine", "personal_tenet",
    "rite_core_tenet_choice", "rite_core_tenet_slot", "holding_building", "holding_building_preview", "holding_construct_conditions", "clerical_puppet", "external_clerical_puppet"]
PresentationTab = Literal["", "beliefs", "holy_sites", "tenets", "doctrines"]
PresentationOperation = Literal["query", "open_holding", "open_personal_beliefs",
    "select_presentation_tab", "open_rite_core_picker", "hover_presentation_tooltip",
    "leave_presentation_tooltip", "show_building_details", "open_building_track", "close_presentation_window", "open_clerical_preview", "close_clerical_preview"]

WINDOW_ROOTS = {"faith": "faith_window", "holding": "holding_view",
    "personal_beliefs": "window_personal_beliefs", "rite_creation": "rite_creation_window", "clerical_interaction": "character_interaction_confirmation_window"}
TARGET_KIND = {"faith_core_tenet": "faith", "faith_doctrine": "faith",
    "personal_tenet": "personal_beliefs", "rite_core_tenet_choice": "rite_creation", "rite_core_tenet_slot": "rite_creation",
    "holding_building": "holding", "holding_building_preview": "holding",
    "holding_construct_conditions": "holding", **{key: "clerical_interaction" for key in CLERICAL_KEYS}}
RESPONSE_TARGET_KIND = {**TARGET_KIND, "rite_core_tenet_slot": "rite_creation"}
TABS = {"faith": {"beliefs", "holy_sites"}, "personal_beliefs": {"tenets", "doctrines"}}
NEW_OPERATIONS = {"open_holding", "open_personal_beliefs", "select_presentation_tab",
    "open_rite_core_picker", "hover_presentation_tooltip", "leave_presentation_tooltip",
    "show_building_details", "open_building_track", "close_presentation_window", "open_clerical_preview", "close_clerical_preview"}
_RECEIPT = re.compile(r"[0-9a-f]{32}\Z")


def requested(operation: str, kind: str, *, presentation_target=None,
        presentation_index=None, presentation_tab=None, presentation_receipt=None) -> bool:
    return (operation in NEW_OPERATIONS or kind in {"holding", "personal_beliefs", "rite_creation", "clerical_interaction"}
        or any(value is not None for value in (presentation_target, presentation_index,
            presentation_tab, presentation_receipt)))


def request_fields(operation: str, kind: str, subject_id: int, *, presentation_target=None,
        presentation_index=None, presentation_tab=None, presentation_receipt=None) -> dict:
    """Zero Faith/Rite references remain valid. Province/Character IDs are positive."""
    values = {"presentation_target": presentation_target, "presentation_index": presentation_index,
        "presentation_tab": presentation_tab, "presentation_receipt": presentation_receipt}
    if not requested(operation, kind, **values):
        return {}
    if kind not in WINDOW_ROOTS or operation not in NEW_OPERATIONS | {"query"}:
        raise ValueError("unsupported finite presentation operation/window")
    if type(subject_id) is not int or not 0 <= subject_id < 2**32 - 1:
        raise ValueError("presentation subject must preserve its full uint32 reference")
    if operation != "query" and kind in {"holding", "personal_beliefs"} and subject_id == 0:
        raise ValueError("holding ProvinceID and personal CharacterID must be positive")
    if kind == "holding" and subject_id > 2**31 - 1:
        raise ValueError("holding subject must be an actual positive int32 Province map index")
    if presentation_target is not None and (type(presentation_target) is not str
            or presentation_target not in {"", *TARGET_KIND}):
        raise ValueError("unsupported finite presentation target")
    if presentation_index is not None and (type(presentation_index) is not int
            or not 0 <= presentation_index < 128):
        raise ValueError("presentation index exceeds the finite 128-row census budget; provider checks its actual container")
    if presentation_tab is not None and (type(presentation_tab) is not str
            or presentation_tab not in {"", "beliefs", "holy_sites", "tenets", "doctrines"}):
        raise ValueError("unsupported finite presentation tab")
    if presentation_receipt is not None and (type(presentation_receipt) is not str
            or _RECEIPT.fullmatch(presentation_receipt) is None):
        raise ValueError("presentation receipt must be 32 lower-case hex characters")
    target = presentation_target or ""
    tab = presentation_tab or ""
    if target and TARGET_KIND[target] != kind:
        raise ValueError("presentation target belongs to another typed window")
    if target and kind in {"holding", "personal_beliefs"} and subject_id == 0:
        raise ValueError("tooltip observation requires its actual ProvinceID or CharacterID")
    if tab and tab not in TABS.get(kind, set()):
        raise ValueError("presentation tab belongs to another typed window")
    if kind == "clerical_interaction":
        validate_clerical_request(operation, subject_id, values)
        return {key: value for key, value in values.items() if value is not None}
    if operation in {"open_clerical_preview", "close_clerical_preview"}:
        raise ValueError("clerical preview operations require their finite typed window")
    if operation == "query":
        if target:
            if presentation_index is None or presentation_receipt is None or tab:
                raise ValueError("tooltip readback requires exact target/index/receipt")
        elif presentation_index is not None or presentation_receipt is not None:
            raise ValueError("ordinary window observation has no tooltip index/receipt")
    elif operation in {"hover_presentation_tooltip", "leave_presentation_tooltip"}:
        if not target or presentation_index is None or tab:
            raise ValueError("tooltip action requires exact target/index")
        if (operation == "hover_presentation_tooltip") != (presentation_receipt is None):
            raise ValueError("only leave consumes the original tooltip receipt")
    elif operation == "select_presentation_tab":
        if not tab or target or presentation_index is not None or presentation_receipt is not None:
            raise ValueError("tab selection accepts only its original finite tab")
    elif operation == "open_rite_core_picker":
        if kind != "rite_creation" or presentation_index is None or target or tab or presentation_receipt is not None:
            raise ValueError("core picker requires source RiteID and current visible core-row census index")
    elif operation == "open_building_track":
        if kind != "holding" or target != "holding_building" or presentation_index is None or tab or presentation_receipt is not None:
            raise ValueError("opening a building track requires the current original installed-building row; no preview, tab, or tooltip receipt")
    elif operation == "show_building_details":
        if kind != "holding" or target != "holding_building_preview" or presentation_index is None or tab or presentation_receipt is not None:
            raise ValueError("ShowDetails requires an original potential-building preview; installed-slot clicks are not admitted")
    elif operation == "close_presentation_window":
        if kind != "personal_beliefs" or any(v is not None for v in values.values()):
            raise ValueError("closing admits only the current player personal beliefs window, without selector fields")
    else:
        expected = {"open_holding": "holding", "open_personal_beliefs": "personal_beliefs"}[operation]
        if kind != expected or any(v is not None for v in values.values()):
            raise ValueError("opening accepts only its typed subject")
    return {key: value for key, value in values.items() if value is not None}


def tooltip_query(operation: str, *, presentation_target=None, presentation_receipt=None, **_) -> bool:
    return (operation == "query" and bool(presentation_target) and presentation_target not in CLERICAL_KEYS
            and presentation_receipt is not None)


def validated_call_fields(operation: str, kind: str, subject_id: int, **fields) -> dict:
    """Public presentation wrapper cannot become a route for unrelated UI ops."""
    if kind not in WINDOW_ROOTS or operation not in NEW_OPERATIONS | {"query"}:
        raise ValueError("this wrapper admits only the finite presentation operation/window table")
    if operation == "query" and all(value is None for value in fields.values()):
        fields["presentation_tab"] = ""  # Explicit presence marker, also for valid Faith0.
    return request_fields(operation, kind, subject_id, **fields)


def normalize_presentation_result(value: dict, *, operation: str, kind: str, subject_id: int,
        actor_id: int, presentation_target=None, presentation_index=None,
        presentation_tab=None, presentation_receipt=None) -> None:
    fields = dict(presentation_target=presentation_target, presentation_index=presentation_index,
        presentation_tab=presentation_tab, presentation_receipt=presentation_receipt)
    active = requested(operation, kind, **fields)
    leaf = value.get("presentation_ui")
    if not active:
        if leaf is not None:
            raise ValueError("unsolicited presentation observation on a legacy request")
        return
    request_fields(operation, kind, subject_id, **fields)
    if not isinstance(leaf, dict) or leaf.get("schema") != "ck3-presentation-ui-v1":
        raise ValueError("finite presentation native leaf is unavailable; old generic window output is insufficient")
    flags = ("requested", "available", "source_bound", "tab_observed", "picker_observed",
        "preview_observed", "hover_source_matches", "tooltip_stack_observed", "tooltip_root_visible",
        "leave_observed", "cache_complete", "rendered_pixels_observed")
    for key in flags:
        if type(leaf.get(key)) is not bool:
            raise ValueError("missing native presentation flag: " + key)
    if leaf["requested"] is not True or leaf["rendered_pixels_observed"] is not False:
        raise ValueError("presentation native observation cannot grant rendered pixel proof")
    if leaf["available"] != value["available"] or leaf.get("status") != value.get("status"):
        raise ValueError("presentation leaf/envelope availability or status differs")
    reason = leaf.get("unavailable_reason")
    if leaf["available"]:
        if reason is not None:
            raise ValueError("available presentation has an unavailable reason")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("unavailable presentation needs its actual reason")
    for key in ("subject_id", "target_index", "receipt_id", "active_tab", "target_kind",
            "action_owner_epoch", "observation_owner_epoch", "post_window_visible",
            "tooltip_active_count", "tooltip_top_locked", "cache_texts", "targets"):
        if key not in leaf:
            raise ValueError("missing nullable presentation observation: " + key)
    for key in ("subject_id", "target_index"):
        n = leaf[key]
        if n is not None and (type(n) is not int or not 0 <= n < 2**32
                or (key == "subject_id" and n == 2**32 - 1)
                or (key == "target_index" and n >= 128)):
            raise ValueError("presentation observed uint32 reference/index is invalid")
    if leaf["subject_id"] is not None and kind in {"holding", "personal_beliefs"} and leaf["subject_id"] == 0:
        raise ValueError("observed Province/Character subject zero is invalid")
    if kind == "holding" and leaf["subject_id"] is not None and leaf["subject_id"] > 2**31 - 1:
        raise ValueError("observed Province map index exceeds its actual int32 domain")
    for key in ("action_owner_epoch", "observation_owner_epoch"):
        n = leaf[key]
        if n is not None and (type(n) is not int or not 0 < n < 2**64):
            raise ValueError("presentation owner epoch is invalid")
    for key, maximum in (("tooltip_active_count", 32), ("tooltip_top_locked", 255)):
        n = leaf[key]
        if n is not None and (type(n) is not int or not 0 <= n <= maximum):
            raise ValueError("presentation native tooltip stack observation is invalid")
    visible = leaf["post_window_visible"]
    if visible is not None and (type(visible) is not bool or visible != value["effective_visible"]):
        raise ValueError("presentation actual window visibility differs")
    if leaf["active_tab"] is not None and leaf["active_tab"] not in TABS.get(kind, set()):
        raise ValueError("presentation observed tab belongs to another window")
    if leaf["tab_observed"] != (leaf["active_tab"] is not None):
        raise ValueError("presentation tab availability must not infer an unknown tab")
    if leaf["target_kind"] is not None and RESPONSE_TARGET_KIND.get(leaf["target_kind"]) != kind:
        raise ValueError("presentation observed target belongs to another window")
    receipt = leaf["receipt_id"]
    if receipt is not None and (type(receipt) is not str or _RECEIPT.fullmatch(receipt) is None):
        raise ValueError("presentation native receipt is invalid")
    if leaf["source_bound"]:
        if not value["subject_id_available"] or leaf["subject_id"] != value["current_subject_id"]:
            raise ValueError("presentation source is not bound to the actual typed window subject")
        if subject_id != 0 or operation != "query" or presentation_target:
            if leaf["subject_id"] != subject_id:
                raise ValueError("presentation source differs from the requested full subject")
        if kind == "personal_beliefs" and leaf["subject_id"] != actor_id:
            raise ValueError("personal beliefs source is not the current player")
    if presentation_target and leaf["source_bound"]:
        if leaf["target_kind"] != presentation_target or leaf["target_index"] != presentation_index:
            raise ValueError("presentation source differs from the exact target container row")
    if not value["window_exists"] and leaf["available"]:
        if operation != "query" and not value["dispatch_invoked"]:
            raise ValueError("absent presentation window is neither independently observed nor opening")
        if leaf["source_bound"] or leaf["post_window_visible"] is not False:
            raise ValueError("absent window cannot grant a bound visible source")
    if operation != "query" and leaf["available"]:
        if not value["dispatch_invoked"] or not value["native_dispatch_attempted"] or not value["verification_pending"]:
            raise ValueError("presentation action ACK lacks the actual original dispatch")
        if operation not in {"open_holding", "open_personal_beliefs", "open_clerical_preview"} and not leaf["source_bound"]:
            raise ValueError("presentation action lacks its actual source-bound window")
        if operation in {"open_rite_core_picker", "show_building_details", "open_building_track"}:
            expected_kind = {"open_rite_core_picker": "rite_core_tenet_slot",
                "show_building_details": "holding_building_preview", "open_building_track": "holding_building"}[operation]
            if leaf["target_kind"] != expected_kind or leaf["target_index"] != presentation_index:
                raise ValueError("presentation ACK lost the current original GUI container row identity")
    if operation in {"close_presentation_window", "close_clerical_preview"} and leaf["available"]:
        if leaf["post_window_visible"] is not None or leaf["action_owner_epoch"] is None:
            raise ValueError("close ACK must retain unknown postvisibility until an independent window query")
    if operation == "hover_presentation_tooltip" and leaf["available"]:
        if receipt is None or leaf["action_owner_epoch"] is None or not leaf["source_bound"]:
            raise ValueError("tooltip hover ACK lacks a minted source-bound receipt")
    if operation == "leave_presentation_tooltip" and leaf["available"]:
        if receipt is None or leaf["action_owner_epoch"] is None or not leaf["source_bound"]:
            raise ValueError("tooltip leave ACK lacks its newly minted source-bound receipt")
    if tooltip_query(operation, **fields) and leaf["available"]:
        first, later = leaf["action_owner_epoch"], leaf["observation_owner_epoch"]
        if (receipt != presentation_receipt or first is None or later is None or later <= first
                or not leaf["source_bound"] or not leaf["tooltip_stack_observed"]):
            raise ValueError("tooltip query lacks an independent later receipt/source/stack observation")
        if not leaf["leave_observed"] and (not leaf["hover_source_matches"] or not leaf["tooltip_root_visible"]
                or leaf["tooltip_active_count"] is None or leaf["tooltip_active_count"] < 1
                or leaf["tooltip_top_locked"] != 0):
            raise ValueError("tooltip observation lacks its currently bound visible unlocked source")
        if leaf["leave_observed"] and leaf["hover_source_matches"]:
            raise ValueError("tooltip leave cannot also claim an active matching hover")
    normalize_clerical_result(value, leaf, operation=operation, kind=kind, subject_id=subject_id,
        actor_id=actor_id, target=presentation_target, receipt=presentation_receipt)
    normalize_holding_tracks_result(leaf, kind)
    texts, targets = leaf["cache_texts"], leaf["targets"]
    if not isinstance(texts, list) or len(texts) > 64:
        raise ValueError("presentation cache text count exceeds its finite bound")
    total = 0
    for item in texts:
        if (not isinstance(item, dict) or set(item) != {"runtime_name", "text", "sha256"}
                or type(item["runtime_name"]) is not str or type(item["text"]) is not str):
            raise ValueError("presentation native cache entry is malformed")
        raw = item["text"].encode("utf-8"); total += len(raw)
        if len(raw) > 16384 or total > 262144 or item["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("presentation native cache exceeds bounds or differs from its exact UTF-8 SHA")
    if not isinstance(targets, list) or len(targets) > 128:
        raise ValueError("presentation target enumeration exceeds its finite bound")
    seen = set()
    for item in targets:
        if (not isinstance(item, dict) or set(item) != {"index", "kind", "runtime_name", "definition_key",
                "label", "effective_visible", "enabled"} or type(item["index"]) is not int
                or not 0 <= item["index"] < 128 or RESPONSE_TARGET_KIND.get(item["kind"]) != kind
                or type(item["runtime_name"]) is not str or type(item["effective_visible"]) is not bool
                or type(item["enabled"]) is not bool
                or any(item[k] is not None and type(item[k]) is not str for k in ("definition_key", "label"))):
            raise ValueError("presentation actual target row is malformed")
        identity = (item["kind"], item["index"])
        if identity in seen:
            raise ValueError("presentation target container identity is not unique")
        seen.add(identity)


def normalize_holding_tracks_result(leaf: dict, kind: str) -> None:
    """Optional successor observation; missing/null remains unknown for a01."""
    tracks = leaf.get("holding_tracks")
    if tracks is None:
        return
    keys = {"available", "unavailable_reason", "owner_bound", "window_exists", "root_exists",
        "effective_visible", "selection_category_id", "selection_mode", "selection_action_raw", "selected_building_key"}
    if kind != "holding" or not isinstance(tracks, dict) or set(tracks) != keys:
        raise ValueError("holding tracks optional observation is malformed or belongs to another window")
    if type(tracks["available"]) is not bool or type(tracks["owner_bound"]) is not bool:
        raise ValueError("holding tracks native availability/owner binding flags are missing")
    reason = tracks["unavailable_reason"]
    if (tracks["available"] and reason is not None) or (not tracks["available"] and (type(reason) is not str or not reason)):
        raise ValueError("holding tracks availability needs its actual unavailable reason")
    for field in ("window_exists", "root_exists", "effective_visible"):
        if tracks[field] is not None and type(tracks[field]) is not bool:
            raise ValueError("holding tracks visibility is neither observed bool nor unknown")
    for field in ("selection_category_id", "selection_mode", "selection_action_raw"):
        if tracks[field] is not None and (type(tracks[field]) is not int or not -(2**31) <= tracks[field] < 2**31):
            raise ValueError("holding tracks selected native raw int32 is invalid")
    key = tracks["selected_building_key"]
    if key is not None and (type(key) is not str or not key or len(key.encode("utf-8")) > 1024 or "\x00" in key):
        raise ValueError("holding tracks selected building key is malformed")
    if (tracks["owner_bound"] or tracks["root_exists"] is True) and tracks["window_exists"] is not True:
        raise ValueError("holding tracks owner/root cannot be bound without its actual window")
    if tracks["effective_visible"] is True and (not tracks["owner_bound"] or tracks["root_exists"] is not True
            or leaf["source_bound"] is not True or leaf["post_window_visible"] is not True):
        raise ValueError("holding tracks visible state lacks the owned source and visible main holding")
