"""Six literal skill+1 controls. Bind actual price strings without calculating a price."""
from copy import deepcopy
from .white_control_action_contract import PROOFS, SCHEMA, actual_values, business_binding, validate_action
from .white_rendered_text_contract import TEXT_NAMES

STEP = "click-white-numeric-control-v1"
CAPABILITY = "game.command.click-white-numeric-control-v1"
CONTROLS = {
    name + "_plus_1": ("ervc_cc_" + name, "ervc_cc_" + name + "_value_text")
    for name in ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")
}
PRICE_TEXT = "ervc_cc_price_value_text"
GOLD_TEXT = "ervc_cc_gold_value_text"

def validate_numeric_action(control, expected_before_value, expected_before_price_text, intent_id):
    if not isinstance(control, str) or control not in CONTROLS:
        raise ValueError("only six literal White skill_plus_1 controls are admitted")
    validate_action("age_plus_1", expected_before_value, intent_id)
    if expected_before_value >= 100:
        raise ValueError("expected_before_value must be an integer in 0..99")
    if not isinstance(expected_before_price_text, str) or not expected_before_price_text or "\0" in expected_before_price_text:
        raise ValueError("expected_before_price_text must be actual nonempty rendered text")
    if len(expected_before_price_text.encode("utf-8", "strict")) > 2048:
        raise ValueError("expected actual price text exceeds the fixed getter budget")

def normalize_numeric_ack(raw, binding, control, before):
    if (not isinstance(raw, dict) or raw.get("schema") != SCHEMA or raw.get("step") != STEP
            or raw.get("control") != control or raw.get("backend_id", "native-headless") != "native-headless"):
        raise ValueError("wrong fixed White numeric action ACK")
    if (raw.get("available") is not True or any(raw.get(key) is not True for key in PROOFS)
            or raw.get("before_price_bound") is not True or raw.get("read_only") is not False
            or raw.get("selected_down_available") is not False or raw.get("postcondition_verified") is not False):
        raise ValueError("numeric ACK lacks actual receiver/before-price/frame proof or invents post credit")
    if raw.get("unavailable_reason") != "" or type(raw.get("native_handled")) is not bool:
        raise ValueError("numeric native handling diagnostic is malformed")
    for key in ("game_pid", "native_revision", "connection_generation", "played_character_id", "date_raw"):
        if type(raw.get(key)) is not int or raw[key] != binding[key]:
            raise ValueError("numeric action crossed " + key)
    if type(raw.get("expected_before_value")) is not int or raw["expected_before_value"] != before:
        raise ValueError("numeric action expected before changed")
    path = raw.get("target_child_path")
    if (not isinstance(path, str) or not path.startswith("0/") or len(path.split("/")) > 64
            or any(not n.isascii() or not n.isdecimal() or int(n) > 2048 for n in path.split("/"))):
        raise ValueError("numeric receiver is outside actual inner modal")
    return deepcopy(raw)

def numeric_values(business, text, binding):
    values, _ = actual_values(business, text, binding)
    strings = {}
    for name in TEXT_NAMES:
        field = text["fields"][name]
        if (not isinstance(field, dict) or field.get("effective_visible") is not True
                or not isinstance(field.get("text_utf8"), str) or "\0" in field["text_utf8"]):
            raise ValueError("numeric action lacks actual visible text " + name)
        strings[name] = field["text_utf8"]
    if not strings[PRICE_TEXT] or not strings[GOLD_TEXT]:
        raise ValueError("numeric action requires actual price and gold strings")
    return values, strings
