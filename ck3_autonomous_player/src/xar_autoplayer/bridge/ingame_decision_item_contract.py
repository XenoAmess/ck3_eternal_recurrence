"""Read actual exact .3 decision model identity without projecting UI action qualification."""
from .ingame_decisions_open_contract import result_build

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
    result_build(raw)
    if (not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-decision-item-v1"
            or raw.get("step") != STEP or raw.get("read_only") is not True
            or type(raw.get("available")) is not bool):
        raise ValueError("malformed exact .3/.4 keyed decision observation")
    if raw.get("row_widget_datacontext_verified") is not False or raw.get("action_qualified") is not False:
        raise ValueError("model observation cannot qualify a widget action")
    # Available terms must describe this outer model's actual selected,
    # visible, complete detail for the same full player ID. An unavailable
    # component remains compatible with unselected/hidden list observations.
    selected_terms = raw.get("selected_terms")
    if isinstance(selected_terms, dict) and selected_terms.get("available") is True:
        if raw["available"] is not True:
            raise ValueError("available selected terms require an available outer model")
        for proof in ("detail_definition_matches_target", "detail_tree_complete",
                      "detail_root_visible", "detail_actor_binding_verified"):
            if raw.get(proof) is not True:
                raise ValueError(f"available selected terms lack outer selected-detail proof: {proof}")
        actor = raw.get("detail_actor_reference_key")
        if type(actor) is not int or actor != binding["played_character_id"]:
            raise ValueError("available selected terms changed outer detail actor")
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
    if "selected_terms" in raw:
        if raw.get("game_version") != "1.20.0.4":
            raise ValueError("selected terms must not cross native builds")
        normalize_selected_decision_terms_v1(raw["selected_terms"], binding, requested_key)
    return dict(raw)


def normalize_selected_decision_terms_v1(value: object, binding: dict[str, object],
                                         requested_key: str) -> dict[str, object]:
    """Exact .4 empty or fixed create_hof stock-default terms; no action credit."""
    if (not isinstance(value, dict)
            or value.get("schema") != "ck3-selected-decision-terms-v1"
            or value.get("read_only") is not True
            or value.get("action_ready") is not False
            or value.get("decision_confirm_invoked") is not False
            or value.get("context_adapter") not in {
                "actual_empty_named_parameters_only", "actual_create_hof_stock_default_parameter_only"}
            or value.get("decision_key") != requested_key
            or type(value.get("available")) is not bool
            or value.get("game_version") != "1.20.0.4"
            or not isinstance(value.get("executable_sha256"), str)
            or value["executable_sha256"].lower()
            != "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"):
        raise ValueError("malformed selected decision terms")
    for key in ("played_character_id", "date_raw"):
        if type(value.get(key)) is not int or value[key] != binding[key]:
            raise ValueError(f"selected decision terms changed {key}")
    if type(value.get("capture_epoch")) is not int or value["capture_epoch"] < 0:
        raise ValueError("selected decision terms lacks an actual capture epoch")
    if not value["available"]:
        if (value["context_adapter"] != "actual_empty_named_parameters_only"
                or value.get("stock_default_parameter") is not None):
            raise ValueError("unavailable selected terms cannot claim a verified stock parameter")
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("unavailable selected decision terms lacks reason")
        if (value.get("context_verified") is not False
                or any(value.get(k) is not False for k in (
                    "requirements_bypass_observed", "ordinary_legality_observed", "confirm_tooltip_available",
                    "requirements_description_available", "cost_description_available",
                    "resource_quote_available", "cooldown_observed"))
                or any(value.get(k) is not None for k in (
                    "can_confirm", "requirements_bypass_raw", "ordinary_can_confirm", "confirm_tooltip",
                    "requirements_description", "cost_description", "resource_quote", "cooldown"))):
            raise ValueError("unavailable selected terms must not invent observed values")
        return dict(value)
    if (value.get("capture_epoch") <= 0 or value.get("context_verified") is not True
            or not selected_parameter_context_verified_v1(value, requested_key)
            or type(value.get("can_confirm")) is not bool):
        raise ValueError("selected decision context is unqualified")
    for key in ("requirements_bypass_observed", "ordinary_legality_observed",
                "confirm_tooltip_available", "requirements_description_available",
                "cost_description_available", "resource_quote_available", "cooldown_observed"):
        if type(value.get(key)) is not bool:
            raise ValueError(f"selected terms lacks actual boolean {key}")
    bypass = value["requirements_bypass_observed"]
    raw = value.get("requirements_bypass_raw")
    if (bypass and (type(raw) is not int or not 0 <= raw <= 255)) or (not bypass and raw is not None):
        raise ValueError("selected terms lost bypass availability")
    ordinary = bypass and raw == 0
    if value["ordinary_legality_observed"] is not ordinary:
        raise ValueError("selected terms invented ordinary legality")
    if value.get("ordinary_can_confirm") is not (value["can_confirm"] if ordinary else None):
        raise ValueError("selected terms ordinary gate differs from native")
    for key in ("confirm_tooltip", "requirements_description", "cost_description"):
        observed = value[key + "_available"]
        if (observed and not isinstance(value.get(key), str)) or (not observed and value.get(key) is not None):
            raise ValueError(f"selected terms lost {key} availability")
    quote = value.get("resource_quote")
    if value["resource_quote_available"]:
        if (not isinstance(quote, dict) or set(quote) != {"raw_scale", "resource_vector_raw", "native_affordable"}
                or type(quote["raw_scale"]) is not int or quote["raw_scale"] != 100000 or type(quote["native_affordable"]) is not bool
                or not isinstance(quote["resource_vector_raw"], list)
                or len(quote["resource_vector_raw"]) != 10
                or any(type(n) is not int or not -(1 << 63) <= n < (1 << 63) for n in quote["resource_vector_raw"])):
            raise ValueError("selected terms malformed native resource quote")
    elif quote is not None:
        raise ValueError("unavailable selected quote must stay null")
    clock = value.get("cooldown")
    if value["cooldown_observed"]:
        if (not isinstance(clock, dict)
                or set(clock) != {"present", "current_counter_raw", "expiry_raw", "active", "counter_unit"}
                or type(clock["present"]) is not bool or type(clock["active"]) is not bool
                or type(clock["current_counter_raw"]) is not int
                or not -(1 << 31) <= clock["current_counter_raw"] < (1 << 31)
                or clock["counter_unit"] != "native_decision_clock_counter"):
            raise ValueError("selected terms malformed native cooldown")
        if clock["present"]:
            if (type(clock["expiry_raw"]) is not int or not -(1 << 31) <= clock["expiry_raw"] < (1 << 31)
                    or clock["active"] != (clock["current_counter_raw"] < clock["expiry_raw"])):
                raise ValueError("selected cooldown expiry differs")
        elif clock["expiry_raw"] is not None or clock["active"] is not False:
            raise ValueError("absent selected cooldown invented expiry or active state")
    elif clock is not None:
        raise ValueError("unobserved selected cooldown must stay null")
    return dict(value)


def selected_parameter_context_verified_v1(value: dict[str, object], requested_key: str) -> bool:
    """Fixed wire identity only; the native reader proves the actual source row."""
    count = value.get("named_parameter_count")
    if type(count) is not int:
        return False
    parameter = value.get("stock_default_parameter")
    if value.get("context_adapter") == "actual_empty_named_parameters_only":
        return count == 0 and parameter is None
    if (value.get("context_adapter") != "actual_create_hof_stock_default_parameter_only"
            or requested_key != "create_hof_decision" or count != 1
            or not isinstance(parameter, dict) or set(parameter) != {
                "token_source", "canonical_token", "key", "scope_kind", "scope_flags", "scope_payload", "no_custom_controller"}):
        return False
    return (parameter["token_source"] == "stock_detail_default_token_slot_0x5D4C0D8"
            and type(parameter["canonical_token"]) is int and 0 <= parameter["canonical_token"] <= 0xFFFFFFFF
            and type(parameter["key"]) is int and parameter["key"] == parameter["canonical_token"]
            and type(parameter["scope_kind"]) is int and parameter["scope_kind"] == 4
            and type(parameter["scope_flags"]) is int and parameter["scope_flags"] == 0
            and type(parameter["scope_payload"]) is int and parameter["scope_payload"] == 0xFFFFFFFF
            and parameter["no_custom_controller"] is True)
