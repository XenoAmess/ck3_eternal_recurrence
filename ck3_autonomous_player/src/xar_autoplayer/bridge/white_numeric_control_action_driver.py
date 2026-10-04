"""One fixed skill+1 callback and independent actual business/text/price observations."""
import hashlib
import json
import os
import time
import uuid
from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .white_numeric_control_action_contract import (
    STEP, CAPABILITY, CONTROLS, PRICE_TEXT, GOLD_TEXT, business_binding,
    validate_numeric_action, normalize_numeric_ack, numeric_values,
)

def click_white_numeric_control(driver, control, expected_before_value, expected_before_price_text, intent_id, *, expected_revision=None):
    from .native_driver import _same_paused_native_frame, _validate_revision
    validate_numeric_action(control, expected_before_value, expected_before_price_text, intent_id)
    if expected_revision is not None:
        _validate_revision(expected_revision, "expected_revision")
        if expected_revision >= 2**64: raise ValueError("expected_revision must fit uint64")
    if CAPABILITY not in set(driver.capabilities().get("bridge_capabilities", [])):
        raise UnsupportedStepError("native DLL lacks six fixed White skill+1 controls")
    starting = driver.take_snapshot()
    try:
        binding = business_binding(starting); revision = starting["revision"]
        _validate_revision(revision, "snapshot revision")
        if revision >= 2**64: raise ValueError("snapshot revision must fit uint64")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    if expected_revision is not None and expected_revision != revision:
        raise PreSubmissionRevisionMismatchError("White skill action public revision changed")
    identity = {"game_pid": binding["game_pid"], "actor_id": binding["played_character_id"],
                "episode_run_id": binding["episode_run_id"], "intent_id": intent_id}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    directory = driver._native_driver_state_path().parent / "white-control-actions"
    claim = directory / (key + ".claim.json")
    if claim.exists(): raise BridgeUnavailableError("White action intent already claimed; no retry")
    before_business = driver.query_white_player_business_variables_v1(expected_revision=revision)
    before_text = driver.query_white_rendered_text_v1(expected_revision=revision)
    variable, widget_text = CONTROLS[control]
    try:
        before_values, before_strings = numeric_values(before_business, before_text, binding)
        fresh = driver.take_snapshot()
        if (business_binding(fresh) != binding or not _same_paused_native_frame(starting, fresh)
                or before_values[variable] != expected_before_value or before_strings[widget_text] != str(expected_before_value)
                or before_strings[PRICE_TEXT] != expected_before_price_text):
            raise ValueError("White skill/price actual before or frame changed")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    request_id = "white-numeric-" + uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=True)
    claim_data = {"schema": "ck3-white-control-once-claim-v1", "identity": identity, "binding": binding,
                  "request_id": request_id, "control": control, "expected_before_value": expected_before_value,
                  "expected_before_price_text": expected_before_price_text,
                  "before_business": before_business, "before_rendered_text": before_text,
                  "status": "claimed_result_unknown_no_retry"}
    try:
        with claim.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(claim_data, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    except FileExistsError as error:
        raise BridgeUnavailableError("White action intent already claimed; no retry") from error
    raw = None; result = None
    def preserve(ok, error=""):
        receipt = {"schema": "ck3-white-numeric-once-result-v1", "ok": ok, "request_id": request_id,
                   "claim_path": str(claim), "raw": raw, "result": result, "error": error}
        with (directory / (key + ".result.json")).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(receipt, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    try:
        raw = driver._execute_primitive_step(STEP, expected_revision=revision, required_capability=CAPABILITY,
            protocol_request_id=request_id, request_fields={"control": control, "expected_before_value": expected_before_value,
                "expected_before_price_text": expected_before_price_text,
                "expected_player_character_id": binding["played_character_id"], "expected_game_pid": binding["game_pid"],
                "expected_connection_generation": binding["connection_generation"]})
        result = normalize_numeric_ack(raw, binding, control, expected_before_value)
        deadline = time.monotonic() + 5.0
        while True:
            current = driver.take_snapshot()
            if business_binding(current) != binding or not _same_paused_native_frame(starting, current):
                raise ValueError("White numeric independent after crossed frame")
            after_business = driver.query_white_player_business_variables_v1(expected_revision=current["revision"])
            after_text = driver.query_white_rendered_text_v1(expected_revision=current["revision"])
            after_values, after_strings = numeric_values(after_business, after_text, binding)
            ending = driver.take_snapshot()
            if business_binding(ending) != binding or not _same_paused_native_frame(starting, ending):
                raise ValueError("White numeric independent after crossed frame")
            other_same = all(after_values[key] == value for key, value in before_values.items() if key != variable)
            other_text_same = all(after_strings[key] == value for key, value in before_strings.items() if key not in (widget_text, PRICE_TEXT))
            if (after_values[variable] == expected_before_value + 1 and after_strings[widget_text] == str(expected_before_value + 1)
                    and other_same and other_text_same):
                result.update({"postcondition_verified": True, "independent_business_after_verified": True,
                    "independent_rendered_text_after_verified": True, "actual_price_before_after_bound": True,
                    "actual_price_before": before_strings[PRICE_TEXT], "actual_price_after": after_strings[PRICE_TEXT],
                    "price_formula_verified": False, "before_business": before_business, "before_rendered_text": before_text,
                    "later_actual_business": after_business, "later_actual_rendered_text": after_text,
                    "intent_id": intent_id, "action_claim_path": str(claim), "episode_run_id": binding["episode_run_id"],
                    "queried_revision": revision, "full_gui_acceptance_credit": False,
                    "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False})
                break
            if not other_same or not other_text_same or after_values[variable] not in (expected_before_value, expected_before_value + 1):
                raise ValueError("White numeric actual after changed unrelated configuration/text/gold")
            if time.monotonic() >= deadline:
                raise ValueError("White numeric ACK lacks later actual skill+1 text/business; no retry")
            time.sleep(0.05)
        preserve(True)
    except Exception as error:
        preserve(False, f"{type(error).__name__}: {error}")
        driver._record_command(STEP, ok=False, result={"raw": raw, "action_claim_path": str(claim)}, error=str(error))
        if isinstance(error, ValueError): raise BridgeUnavailableError(str(error)) from error
        raise
    driver._record_command(STEP, ok=True, result=result)
    return result
