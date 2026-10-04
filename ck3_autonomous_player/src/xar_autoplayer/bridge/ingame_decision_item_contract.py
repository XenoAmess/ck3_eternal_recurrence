"""Read actual exact .3 decision model identity without projecting UI action qualification."""
from .ingame_decisions_open_contract import EXE_SHA256

STEP = "query-ingame-decision-item-v1"
CAPABILITY = "game.command.query-ingame-decision-item-v1"


def validate_decision_key(key: object) -> str:
    if not isinstance(key, str) or not key or len(key) > 192 or not all(
        "a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9" or c == "_" for c in key
    ):
        raise ValueError("invalid semantic decision key")
    return key


def normalize_decision_item(raw: object, binding: dict[str, object], requested_key: str) -> dict[str, object]:
    validate_decision_key(requested_key)
    if (not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-decision-item-v1"
            or raw.get("step") != STEP or raw.get("read_only") is not True
            or raw.get("game_version") != "1.20.0.3"
            or str(raw.get("executable_sha256", "")).lower() != EXE_SHA256
            or type(raw.get("available")) is not bool):
        raise ValueError("malformed exact .3 keyed decision observation")
    if raw.get("row_widget_datacontext_verified") is not False or raw.get("action_qualified") is not False:
        raise ValueError("model observation cannot qualify a widget action")
    if not raw["available"]:
        if not isinstance(raw.get("unavailable_reason"), str) or not raw["unavailable_reason"]:
            raise ValueError("unavailable keyed model lacks reason")
        return dict(raw)
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
        value = raw.get(key)
        if type(value) is not int or value != binding[key]:
            raise ValueError(f"keyed model changed {key}")
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
                "decisions_tree_complete", "decisions_root_visible", "row_owner_verified"):
        if raw.get(key) is not True:
            raise ValueError(f"keyed model proof unavailable: {key}")
    for key, bound in (("group_count", 64), ("row_count", 2048)):
        if type(raw.get(key)) is not int or not 0 <= raw[key] <= bound:
            raise ValueError(f"keyed model has invalid {key}")
    if type(raw.get("matching_row_count")) is not int or raw["matching_row_count"] != 1:
        raise ValueError("requested actual model row is not unique")
    if raw.get("decision_key") != requested_key:
        raise ValueError("actual model definition key does not match request")
    if type(raw.get("row_context_reference_key")) is not int or not 0 <= raw["row_context_reference_key"] <= 0xFFFFFFFF:
        raise ValueError("invalid observed context reference key")
    for key in ("row_scope_reference_available", "detail_tree_complete", "detail_root_visible",
                "detail_definition_available", "detail_definition_matches_target"):
        if type(raw.get(key)) is not bool:
            raise ValueError(f"keyed model lacks actual {key}")
    current = raw.get("detail_decision_key")
    if raw["detail_definition_available"]:
        validate_decision_key(current)
    elif current != "":
        raise ValueError("absent detail definition contains a key")
    if raw["detail_definition_matches_target"] != (raw["detail_definition_available"] and current == requested_key):
        raise ValueError("actual selected definition comparison is inconsistent")
    if raw["detail_root_visible"] and not raw["detail_tree_complete"]:
        raise ValueError("actual visible detail root census is incomplete")
    return dict(raw)
