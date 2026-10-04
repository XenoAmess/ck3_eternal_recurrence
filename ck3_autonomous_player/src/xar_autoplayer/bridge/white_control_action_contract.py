"""One fixed White age+1 action; actual business and rendered text remain separate."""
from __future__ import annotations
from copy import deepcopy
import re
from .white_player_business_variables_contract import VARIABLE_KEYS, business_binding
from .white_rendered_text_contract import TEXT_NAMES, PROOFS as TEXT_PROOFS

STEP = "click-white-control-v1"
CAPABILITY = "game.command.click-white-control-v1"
SCHEMA = "ck3-native-white-control-action-v1"
AGE_TEXT = "ervc_cc_age_value_text"
AGE_VARIABLE = "ervc_cc_age"
PROOFS = ("source_abi_pins_verified", "receiver_qualified", "gui_owner_binding_verified",
          "frame_verified", "dispatch_attempted", "dispatch_invoked", "native_after_read")

def validate_action(control: object, expected_before_age: object, intent_id: object) -> None:
    if control != "age_plus_1" or not isinstance(control, str):
        raise ValueError("only fixed White age_plus_1 is admitted")
    if type(expected_before_age) is not int or not 0 <= expected_before_age < 120:
        raise ValueError("expected_before_age must be an integer in 0..119")
    if not isinstance(intent_id, str) or re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", intent_id) is None:
        raise ValueError("intent_id must contain 1..64 ASCII letters/digits/_.:-")

def normalize_action_ack(raw: object, binding: dict[str, object], age: int) -> dict[str, object]:
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA or raw.get("step") != STEP or raw.get("control") != "age_plus_1":
        raise ValueError("wrong native White action ACK")
    if raw.get("backend_id", "native-headless") != "native-headless":
        raise ValueError("White action requires native backend")
    if raw.get("read_only") is not False or raw.get("selected_down_available") is not False or raw.get("postcondition_verified") is not False:
        raise ValueError("native ACK cannot grant independent postcondition/down credit")
    if raw.get("available") is not True or any(raw.get(key) is not True for key in PROOFS):
        raise ValueError("White action lacks actual once-dispatch/receiver/frame proof")
    if type(raw.get("native_handled")) is not bool or raw.get("unavailable_reason") != "":
        raise ValueError("White action ACK lacks actual native handling diagnostic")
    for key in ("game_pid", "native_revision", "connection_generation", "played_character_id", "date_raw"):
        if type(raw.get(key)) is not int or raw[key] != binding[key]:
            raise ValueError("White action crossed " + key)
    if type(raw.get("expected_before_age")) is not int or raw["expected_before_age"] != age:
        raise ValueError("White action ACK changed its expected age")
    path = raw.get("target_child_path")
    if (not isinstance(path, str) or not path.startswith("0/") or len(path.split("/")) > 64
            or any(not n.isascii() or not n.isdecimal() or int(n) > 2048 for n in path.split("/"))):
        raise ValueError("White action receiver path is outside actual inner modal")
    return deepcopy(raw)

def actual_values(business: object, text: object, binding: dict[str, object]) -> tuple[dict[str, int], str]:
    if not isinstance(business, dict) or not isinstance(text, dict):
        raise ValueError("White action needs separate actual business/text observations")
    for result in (business, text):
        if result.get("available") is not True or result.get("read_only") is not True:
            raise ValueError("actual White observation is unavailable")
        for key in ("game_pid", "native_revision", "connection_generation", "played_character_id", "date_raw", "episode_run_id"):
            if result.get(key) != binding[key]:
                raise ValueError("White observation crossed " + key)
    if business.get("schema") != "ck3-native-white-player-business-variables-v1" or business.get("all_eight_numeric_integers") is not True:
        raise ValueError("White action requires eight actual numeric business values")
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified", "player_scope_verified", "stable_two_pass_values"):
        if business.get(key) is not True:
            raise ValueError("White business lacks " + key)
    fields = business.get("fields")
    if not isinstance(fields, dict) or set(fields) != set(VARIABLE_KEYS):
        raise ValueError("White action requires exact eight variable keys")
    values = {}
    for key in VARIABLE_KEYS:
        field = fields[key]
        if (not isinstance(field, dict) or field.get("present") is not True or type(field.get("actual_kind")) is not int or field["actual_kind"] != 1
                or type(field.get("integer_value")) is not int or type(field.get("fixed_raw")) is not int
                or field["fixed_raw"] != field["integer_value"] * 100000 or field.get("actual_payload") != field["fixed_raw"]):
            raise ValueError("White action lacks actual Q100000 integer " + key)
        values[key] = field["integer_value"]
    if (text.get("schema") != "ck3-native-white-rendered-text-v1" or text.get("rendered_text_available") is not True
            or text.get("selected_down_available") is not False or any(text.get(key) is not True for key in TEXT_PROOFS)
            or text.get("text_source") != "actual_CPdxGuiTextbox_GetText_390"):
        raise ValueError("White action lacks actual visible rendered text proof")
    texts = text.get("fields")
    if not isinstance(texts, dict) or set(texts) != set(TEXT_NAMES):
        raise ValueError("White action lacks nine fixed actual text fields")
    age = texts[AGE_TEXT]
    if not isinstance(age, dict) or age.get("effective_visible") is not True or not isinstance(age.get("text_utf8"), str):
        raise ValueError("White action lacks actual visible age text")
    return values, age["text_utf8"]
