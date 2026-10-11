"""Strict current4 child education focus transport through existing private steps."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, StepPostconditionError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12004

SCHEMA = "child-education-focus-private-12004-v1"
QUERY_STEP = "private-query-child-education-focus-v1"
SUBMIT_STEP = "private-select-child-education-focus-v1"
RECEIPT_STEP = "private-query-child-education-focus-receipt-v1"
EDUCATION_KEYS = frozenset({
    "education_diplomacy", "education_martial", "education_stewardship",
    "education_intrigue", "education_learning",
})
_FRAME_KEYS = frozenset({
    "snapshot_id", "episode_run_id", "native_revision", "date_raw",
    "controller_full_id", "paused",
})
_SUBMISSION_KEYS = frozenset({
    "status", "unavailable_reason", "action_request_id", "accepted",
    "child_full_id", "requested_focus_key", "pre_frame",
})


def _object(value: object, keys: frozenset[str], name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"{name} must have the exact native fields")
    return value


def _integer(value: object, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} is outside its source integer range")
    return value


def _full_id(value: object, name: str) -> int:
    return _integer(value, 1, 0xFFFFFFFE, name)


def _text(value: object, name: str, *, empty: bool = False) -> str:
    if type(value) is not str or len(value) > 4096 or (not empty and not value):
        raise ValueError(f"{name} must preserve its native string")
    return value


def _reason(value: object) -> None:
    if value is not None:
        _text(value, "unavailable_reason", empty=True)


def _key(value: object) -> str:
    if type(value) is not str or value not in EDUCATION_KEYS:
        raise ValueError("target_key must be an exact education source key")
    return value


def _frame(value: object) -> dict[str, object]:
    source = _object(value, _FRAME_KEYS, "source_frame")
    revision = _integer(source["native_revision"], 1, 0xFFFFFFFFFFFFFFFF, "native_revision")
    if source["snapshot_id"] != f"native:{revision}" or source["paused"] is not True:
        raise ValueError("native child-focus frame identity is invalid")
    _text(source["episode_run_id"], "episode_run_id")
    _integer(source["date_raw"], 0, 0x7FFFFFFF, "date_raw")
    _full_id(source["controller_full_id"], "controller_full_id")
    return deepcopy(dict(source))


def _focus(value: object) -> None:
    source = _object(value, frozenset({
        "available", "unavailable_reason", "presence", "key",
    }), "current_focus")
    if type(source["available"]) is not bool:
        raise ValueError("current_focus availability is untyped")
    _reason(source["unavailable_reason"])
    if source["key"] is not None:
        _text(source["key"], "current_focus.key")
    if source["available"]:
        if source["presence"] not in {"present", "absent"}:
            raise ValueError("available current_focus presence is untyped")
        if ((source["presence"] == "present") != (source["key"] is not None)):
            raise ValueError("current_focus presence and key disagree")
    elif source["presence"] != "" or source["key"] is not None:
        raise ValueError("unavailable current_focus was promoted to a value")


def _submission(value: object) -> Mapping[str, object]:
    source = _object(value, _SUBMISSION_KEYS, "submission")
    if source["status"] not in {
        "submitted_verification_pending", "rejected_before_submit", "submit_unknown",
    } or type(source["accepted"]) is not bool:
        raise ValueError("child-focus submission status is untyped")
    if source["status"] == "submitted_verification_pending" and source["accepted"] is not True:
        raise ValueError("pending submission lacks native queue acceptance")
    if source["status"] == "rejected_before_submit" and source["accepted"] is not False:
        raise ValueError("rejected submission claims acceptance")
    _reason(source["unavailable_reason"])
    _text(source["action_request_id"], "action_request_id")
    _full_id(source["child_full_id"], "child_full_id")
    _key(source["requested_focus_key"])
    _frame(source["pre_frame"])
    return source


def parse_child_education_focus_private_v1(
    response: object, *, expected_request_id: str, kind: str,
    expected_frame: Mapping[str, object], child_full_id: int, target_key: str,
    expected_submission: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Preserve the closed native DTO; false, unavailable and pending stay distinct."""
    if not isinstance(response, Mapping) or (
        response.get("type") != "command_result"
        or response.get("protocol_version") != 1
        or type(response.get("protocol_version")) is not int
        or response.get("request_id") != expected_request_id
        or response.get("ok") is not True
    ):
        detail = {key: response.get(key) for key in (
            "error", "reason", "status", "execution_code",
        ) if isinstance(response, Mapping) and key in response}
        raise BridgeUnavailableError(f"native child-focus command failed: {detail}")
    _text(expected_request_id, "expected_request_id")
    _full_id(child_full_id, "child_full_id")
    _key(target_key)
    wanted = _frame(expected_frame)
    base = frozenset({"schema", "kind"})
    if kind == "query":
        keys = base | frozenset({
            "status", "unavailable_reason", "source_frame", "child_full_id",
            "target_key", "native_legal", "current_focus",
        })
    elif kind == "submit":
        keys = base | _SUBMISSION_KEYS
    elif kind == "receipt":
        keys = base | frozenset({
            "status", "unavailable_reason", "observed_applied",
            "submission", "post_observation",
        })
    else:
        raise ValueError("unsupported child-focus result kind")
    result = _object(response.get("result"), keys, "child-focus result")
    if result["schema"] != SCHEMA or result["kind"] != kind:
        raise ValueError("native child-focus schema/kind mismatch")
    _reason(result["unavailable_reason"])
    if kind == "query":
        _full_id(result["child_full_id"], "query.child_full_id")
        _key(result["target_key"])
        if (result["status"] not in {"available", "unavailable"}
                or result["child_full_id"] != child_full_id
                or result["target_key"] != target_key
                or _frame(result["source_frame"]) != wanted):
            raise ValueError("child-focus query binding mismatch")
        if (result["native_legal"] is not None
                and type(result["native_legal"]) is not bool):
            raise ValueError("native child-focus legality is untyped")
        if result["status"] == "available" and type(result["native_legal"]) is not bool:
            raise ValueError("available query lacks an observed native legality")
        _focus(result["current_focus"])
    elif kind == "submit":
        submission = _submission({key: result[key] for key in _SUBMISSION_KEYS})
        if (submission["child_full_id"] != child_full_id
                or submission["requested_focus_key"] != target_key
                or submission["action_request_id"] != expected_request_id
                or _frame(submission["pre_frame"]) != wanted):
            raise ValueError("child-focus submit binding mismatch")
    else:
        if (result["status"] not in {
            "observed_applied", "verification_pending", "unavailable",
        } or type(result["observed_applied"]) is not bool):
            raise ValueError("child-focus receipt status is untyped")
        if result["observed_applied"] is not (result["status"] == "observed_applied"):
            raise ValueError("child-focus receipt status and observation disagree")
        submission = _submission(result["submission"])
        if not isinstance(expected_submission, Mapping) or any(
            submission[key] != expected_submission.get(key) for key in (
                "action_request_id", "child_full_id", "requested_focus_key", "pre_frame",
            )
        ):
            raise ValueError("receipt does not belong to the submitted child/action/frame")
        if submission["child_full_id"] != child_full_id or submission["requested_focus_key"] != target_key:
            raise ValueError("receipt child/key binding mismatch")
        post = result["post_observation"]
        if post is not None:
            post = _object(post, frozenset({
                "action_request_id", "independently_published_after_submission",
                "source_frame", "child_full_id", "current_focus",
            }), "post_observation")
            _full_id(post["child_full_id"], "post_observation.child_full_id")
            if (post["action_request_id"] != submission["action_request_id"]
                    or post["child_full_id"] != child_full_id
                    or type(post["independently_published_after_submission"]) is not bool
                    or _frame(post["source_frame"]) != wanted):
                raise ValueError("receipt post observation binding mismatch")
            _focus(post["current_focus"])
        if result["observed_applied"]:
            pre = _frame(submission["pre_frame"])
            if (submission["accepted"] is not True or post is None
                    or post["independently_published_after_submission"] is not True
                    or wanted["native_revision"] <= pre["native_revision"]
                    or wanted["snapshot_id"] == pre["snapshot_id"]
                    or any(wanted[key] != pre[key] for key in (
                        "episode_run_id", "controller_full_id",
                    ))
                    or post["current_focus"]["available"] is not True
                    or post["current_focus"]["presence"] != "present"
                    or post["current_focus"]["key"] != target_key):
                raise ValueError("observed_applied lacks the independent same-child postcondition")
    return deepcopy(dict(result))


def _enabled(driver: object) -> None:
    if getattr(driver, "allow_private_lifestyle_formal_trial", False) is not True:
        raise UnsupportedStepError("private child education focus route is disabled")


def _read(driver: object) -> dict[str, object]:
    return private_g2_query_snapshot_v1(driver, include_native_command_history=False)


def _context(snapshot: Mapping[str, object], expected_revision: int) -> dict[str, object]:
    _integer(expected_revision, 1, 0xFFFFFFFFFFFFFFFF, "expected_revision")
    _integer(snapshot.get("revision"), 1, 0xFFFFFFFFFFFFFFFF, "snapshot.revision")
    build = private_native_build_identity(snapshot)
    played = snapshot.get("played_character")
    if (build != CK3_12004 or snapshot.get("revision") != expected_revision
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, Mapping) or played.get("alive") is not True):
        raise BridgeUnavailableError("child-focus requires the original current4 paused controller frame")
    controller = _integer(played.get("character_id"), -0x80000000, 0xFFFFFFFE,
                          "played_character.character_id") & 0xFFFFFFFF
    frame = _frame({
        "snapshot_id": snapshot.get("snapshot_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"), "controller_full_id": controller,
        "paused": snapshot.get("paused"),
    })
    return {**frame, "public_revision": expected_revision,
            "exact_ck3_build": build.game_version, "exe_sha256": build.executable_sha256}


def _native_frame(context: Mapping[str, object]) -> dict[str, object]:
    return {key: context[key] for key in _FRAME_KEYS}


def _request(context: Mapping[str, object], child: int, key: str) -> dict[str, object]:
    return {
        "expected_snapshot_id": context["snapshot_id"],
        "expected_revision": context["native_revision"],
        "expected_date_raw": context["date_raw"],
        "expected_player_character_id": context["controller_full_id"],
        "episode_run_id": context["episode_run_id"],
        "child_full_id": child, "target_key": key,
    }


def _exchange(driver: object, step: str, request_id: str,
              payload: Mapping[str, object]) -> object:
    driver.endpoint.send({
        **dict(payload), "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
    })
    return driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)


def _metadata(result: Mapping[str, object], context: Mapping[str, object],
              request_id: str) -> dict[str, object]:
    return {**deepcopy(dict(result)), "request_id": request_id,
            "source_public_revision": context["public_revision"],
            "source_context": deepcopy(dict(context))}


def query_child_education_focus_private_v1(
    driver: object, *, child_full_id: int, target_key: str, expected_revision: int,
) -> dict[str, object]:
    _enabled(driver)
    child, key = _full_id(child_full_id, "child_full_id"), _key(target_key)
    before = _context(_read(driver), expected_revision)
    request_id = "child-focus-query-" + uuid.uuid4().hex
    response = _exchange(driver, QUERY_STEP, request_id, _request(before, child, key))
    after = _context(_read(driver), expected_revision)
    if before != after:
        raise BridgeUnavailableError("child-focus query crossed its original paused frame")
    result = parse_child_education_focus_private_v1(
        response, expected_request_id=request_id, kind="query",
        expected_frame=_native_frame(before), child_full_id=child, target_key=key,
    )
    return _metadata(result, before, request_id)


def submit_child_education_focus_private_v1(
    driver: object, *, query: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    _enabled(driver)
    before = _context(_read(driver), expected_revision)
    if not isinstance(query, Mapping) or query.get("source_context") != before:
        raise BridgeUnavailableError("child-focus query is stale or belongs to another controller/build")
    child, key = _full_id(query.get("child_full_id"), "child_full_id"), _key(query.get("target_key"))
    native_query = {field: query[field] for field in (
        "schema", "kind", "status", "unavailable_reason", "source_frame",
        "child_full_id", "target_key", "native_legal", "current_focus",
    )}
    parse_child_education_focus_private_v1(
        {"type": "command_result", "protocol_version": 1, "request_id": query.get("request_id"),
         "ok": True, "result": native_query},
        expected_request_id=query.get("request_id"), kind="query",
        expected_frame=_native_frame(before), child_full_id=child, target_key=key,
    )
    if query["status"] != "available" or query["native_legal"] is not True:
        raise BridgeUnavailableError("child-focus submit lacks an observed original native legal query")
    action_id = "child-focus-" + uuid.uuid4().hex
    intent = _metadata({
        "schema": SCHEMA, "kind": "submit", "status": "action_state_unknown",
        "unavailable_reason": None, "action_request_id": action_id, "accepted": None,
        "child_full_id": child, "requested_focus_key": key, "pre_frame": _native_frame(before),
        "native_command_submitted": None,
    }, before, action_id)
    driver._record_command(SUBMIT_STEP, ok=True, result=intent)
    if getattr(driver, "_driver_state_error", None) is not None:
        raise StepPostconditionError("child-focus intent was not durably recorded",
                                    selected_step=SUBMIT_STEP, step_result=intent)
    try:
        response = _exchange(driver, SUBMIT_STEP, action_id,
                             {**_request(before, child, key), "action_request_id": action_id})
        result = parse_child_education_focus_private_v1(
            response, expected_request_id=action_id, kind="submit",
            expected_frame=_native_frame(before), child_full_id=child, target_key=key,
        )
    except Exception as error:
        raise StepPostconditionError(
            f"child-focus submission state unknown: {type(error).__name__}",
            selected_step=SUBMIT_STEP, step_result=intent,
        ) from error
    pending = _metadata(result, before, action_id)
    pending["native_command_submitted"] = (
        True if result["accepted"] else False if result["status"] == "rejected_before_submit" else None
    )
    driver._record_command(SUBMIT_STEP, ok=True, result=pending)
    return pending


def query_child_education_focus_receipt_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    _enabled(driver)
    if (not isinstance(pending, Mapping) or pending.get("schema") != SCHEMA
            or pending.get("kind") != "submit" or pending.get("status") not in {
                "action_state_unknown", "submit_unknown", "submitted_verification_pending",
            }):
        raise ValueError("child-focus receipt requires the original unresolved submission")
    child = _full_id(pending.get("child_full_id"), "child_full_id")
    key, action_id = _key(pending.get("requested_focus_key")), _text(
        pending.get("action_request_id"), "action_request_id")
    pre = _frame(pending.get("pre_frame"))
    source = pending.get("source_context")
    if (not isinstance(source, Mapping) or _native_frame(source) != pre
            or source.get("exact_ck3_build") != CK3_12004.game_version
            or source.get("exe_sha256") != CK3_12004.executable_sha256):
        raise ValueError("child-focus receipt lost its exact accepted source binding")
    before = _context(_read(driver), expected_revision)
    if any(before[field] != pre[field] for field in ("episode_run_id", "controller_full_id")):
        raise BridgeUnavailableError("child-focus receipt belongs to another controller/episode")
    request_id = "child-focus-receipt-" + uuid.uuid4().hex
    response = _exchange(driver, RECEIPT_STEP, request_id,
                         {**_request(before, child, key), "action_request_id": action_id})
    after = _context(_read(driver), expected_revision)
    if before != after:
        raise BridgeUnavailableError("child-focus receipt crossed its published paused frame")
    result = parse_child_education_focus_private_v1(
        response, expected_request_id=request_id, kind="receipt",
        expected_frame=_native_frame(before), child_full_id=child, target_key=key,
        expected_submission=pending,
    )
    receipt = _metadata(result, before, request_id)
    receipt["action_request_id"] = action_id
    driver._record_command(RECEIPT_STEP, ok=True, result=receipt)
    return receipt
