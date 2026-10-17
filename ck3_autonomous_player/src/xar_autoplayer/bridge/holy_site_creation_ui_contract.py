"""Four exact4 selectors; native selection postconditions never imply creation."""
from __future__ import annotations

from collections.abc import Mapping

from .player_holy_site_creation_context_private_transport import normalize_player_holy_site_creation_context_v1
from .player_holy_site_private_transport import _ref

KIND = "holy_site_creation"
PERMISSION = "allow_private_player_holy_site_creation_ui"
OPERATIONS = frozenset({"open_holy_site_creation", "select_holy_site_creation_type",
    "select_holy_site_creation_barony", "set_holy_site_creation_artifact_selection"})


def validate_creation_ui_fields(operation: str, kind: str, subject_id: int, *,
        type_key: str | None, selected: bool | None) -> None:
    if kind != KIND:
        if type_key is not None or selected is not None:
            raise ValueError("creation selector fields belong only to the fixed creation UI routes")
        return
    if operation not in OPERATIONS | {"query"}:
        raise ValueError("unsupported holy-site creation selector operation")
    _ref(subject_id, "creation UI subject_id", nullable=False)
    if operation in {"query", "open_holy_site_creation", "select_holy_site_creation_type"} and subject_id != 0:
        raise ValueError("this creation operation uses the current player faith, with no selected subject")
    if operation == "select_holy_site_creation_type":
        if not isinstance(type_key, str) or not 1 <= len(type_key.encode("utf-8")) <= 160 or "\0" in type_key:
            raise ValueError("creation type key must preserve its exact 1..160 UTF-8 bytes")
    elif type_key is not None:
        raise ValueError("only the fixed type selector accepts a type key")
    if operation == "set_holy_site_creation_artifact_selection":
        if type(selected) is not bool:
            raise ValueError("creation artifact selection requires an explicit actual bool")
    elif selected is not None:
        raise ValueError("only the fixed artifact selector accepts selected")


def _bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"creation UI boolean is missing: {name}")
    return value


def validate_creation_ui_result(value: Mapping[str, object], *, operation: str, subject_id: int,
        type_key: str | None, selected: bool | None, snapshot: Mapping[str, object] | None) -> None:
    validate_creation_ui_fields(operation, KIND, subject_id, type_key=type_key, selected=selected)
    if not isinstance(snapshot, Mapping):
        raise ValueError("creation UI result requires its actual current public snapshot")
    ui = value.get("holy_site_creation_ui")
    if not isinstance(ui, dict) or set(ui) != {"operation", "type_key", "selected", "requested_object_id",
            "postcondition_observed", "selection_verified", "create_dispatched", "context"}:
        raise ValueError("creation UI result lost its exact selector/context shape")
    if (ui["operation"] != operation or ui["type_key"] != type_key
            or type(ui["selected"]) is not type(selected) or ui["selected"] != selected
            or type(ui["requested_object_id"]) is not int or ui["requested_object_id"] != subject_id):
        raise ValueError("creation UI selector echo differs from the submitted fixed operation")
    post = _bool(ui["postcondition_observed"], "postcondition_observed")
    verified = _bool(ui["selection_verified"], "selection_verified")
    if ui["create_dispatched"] is not False:
        raise ValueError("creation UI selectors cannot dispatch a creation command")
    attempted = _bool(value.get("native_dispatch_attempted"), "native_dispatch_attempted")
    dispatched = _bool(value.get("dispatch_invoked"), "dispatch_invoked")
    pending = _bool(value.get("verification_pending"), "verification_pending")
    available = _bool(value.get("available"), "available")
    if dispatched and not attempted:
        raise ValueError("creation UI invocation lacks an observed native attempt")
    context = ui["context"]
    if context is not None:
        normalize_player_holy_site_creation_context_v1(context, snapshot=snapshot)
        if context["capture_epoch"] != value.get("pump_epoch"):
            raise ValueError("creation UI context belongs to another admitted owner epoch")
        if value["subject_id_available"] and value["current_subject_id"] != context["player_faith_id"]:
            raise ValueError("creation UI window is not bound to its observed current faith")
    elif post or verified or available:
        raise ValueError("creation UI has no captured context for its claimed postcondition")
    if verified:
        if not post or not context["available"] or not context["selection_available"]:
            raise ValueError("creation UI selected-state claim has no complete independent observation")
        if operation == "open_holy_site_creation":
            wanted = context["player_faith_matches"] is True
        elif operation == "select_holy_site_creation_type":
            wanted = context["selected_type_key"] == type_key
        elif operation == "select_holy_site_creation_barony":
            wanted = context["selected_barony_title_id"] == subject_id
        elif operation == "set_holy_site_creation_artifact_selection":
            wanted = (subject_id in context["selected_artifact_ids"]) is selected
        else:
            wanted = False
        if not wanted or value["effective_visible"] is not True:
            raise ValueError("creation UI postcondition does not show the requested selected state")
    if operation == "query":
        if attempted or dispatched or pending or post or verified:
            raise ValueError("creation UI query cannot claim a selector invocation or action postcondition")
    elif available:
        if (value["status"] not in {"ui_selection_verified", "already_selected_verified"}
                or pending or not post or not verified):
            raise ValueError("available creation UI needs the actual selected-state postcondition")
        if value["status"] == "ui_selection_verified" and (not attempted or not dispatched):
            raise ValueError("new verified creation selection lacks an actual invocation")
    else:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("unavailable creation UI requires its actual diagnostic")
        expected = "verification_pending" if attempted else "unavailable"
        if value.get("status") != expected or pending is not attempted:
            raise ValueError("creation UI unknown attempt must retain verification_pending, not success")
    if attempted:
        if (value["application_owner_thread_verified"] is not True
                or value["gui_owner_binding_verified"] is not True
                or not value["gui_context_address"] or not value["gui_owner_address"]
                or not value["thread_id"] or not value["pump_epoch"]):
            raise ValueError("creation selector attempt lacks the actual native owner binding")
        modal = value.get("modal_admission")
        if (not isinstance(modal, dict) or modal.get("attempted") is not True
                or modal.get("header_read") is not True or modal.get("receivers_verified") is not True
                or type(modal.get("effective_visible_count")) is not int or modal["effective_visible_count"] != 0
                or modal.get("effective_hidden_mask") != 8
                or modal.get("policy") != "refuse_any_effective_visible_receiver"):
            raise ValueError("creation selector invocation lacks native modal admission")
