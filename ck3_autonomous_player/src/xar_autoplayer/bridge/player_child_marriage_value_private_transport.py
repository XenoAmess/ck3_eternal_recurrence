"""One specified player's child and one native-final marriage value read."""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .marriage_matchmaking_private_transport import _require_same_paused_frame


STEP = "query-player-child-marriage-value-v1-private"
SCHEMA = "xar.ck3.player-child-marriage-value.v1"


def _native_fertility_input_valid(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    extension = value.get("extension_present")
    evaluated = value.get("native_gate_evaluated")
    allows = value.get("native_gate_allows")
    raw = value.get("effective_raw")
    return (
        value.get("source") == "native_marriage_fertility_input"
        and type(extension) is bool
        and type(evaluated) is bool
        and type(raw) is int
        and evaluated is extension
        and (type(allows) is bool if evaluated else allows is None)
        and (raw == 0 if allows is not True else True)
    )


def query_player_child_marriage_value_private_v1(
    driver: object, *, legality: dict[str, object], candidate_character_id: int,
    request_matrilineal_option: bool = False,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Recheck a specified child and candidate on one paused native revision."""
    if getattr(driver, "allow_private_player_child_marriage_subject_query", False) is not True:
        raise UnsupportedStepError("private player-child marriage value query is disabled")
    before = driver.take_snapshot()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    subject_id = legality.get("subject_character_id") if isinstance(legality, dict) else None
    rows = legality.get("native_legal_candidates") if isinstance(legality, dict) else None
    if (
        not isinstance(legality, dict)
        or legality.get("schema") != "xar.ck3.player-child-marriage-subject.v1"
        or legality.get("status") != "available"
        or legality.get("player_child_verified") is not True
        or legality.get("read_only") is not True
        or legality.get("advertised") is not False
        or legality.get("exact_ck3_build") != "1.19.0.6"
        or legality.get("played_character_id") != played_id
        or legality.get("native_revision") != before.get("native_revision")
        or type(legality.get("query_sequence")) is not int
        or legality["query_sequence"] <= 0
        or type(subject_id) is not int or subject_id <= 0
        or type(candidate_character_id) is not int
        or not 0 < candidate_character_id < 2**31
        or not isinstance(rows, list)
        or len([row for row in rows if isinstance(row, dict) and
                row.get("candidate_character_id") == candidate_character_id]) != 1
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict) or played.get("alive") is not True
        or type(played_id) is not int or played_id <= 0
    ):
        raise BridgeUnavailableError("child marriage value lacks same-frame final legality")
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if type(request_matrilineal_option) is not bool:
        raise ValueError("request_matrilineal_option must be bool")
    request_id = "family-child-value-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "legality_query_sequence": legality["query_sequence"],
        "subject_character_id": subject_id,
        "candidate_character_id": candidate_character_id,
        "request_matrilineal_option": request_matrilineal_option,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("child marriage value query timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "child marriage value query RED: " + str(frame.get("error") or "unknown"))
    result = frame.get("result")
    _require_same_paused_frame(driver.take_snapshot(), before,
                               before["native_revision"], played_id)
    if (
        not isinstance(result, dict) or result.get("step") != STEP
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("native_revision") != before["native_revision"]
        or result.get("legality_query_sequence") != legality["query_sequence"]
        or result.get("status") not in {"available", "unavailable"}
        or not isinstance(result.get("rows"), list)
        or len(result["rows"]) != 1
    ):
        raise BridgeUnavailableError("child marriage value response changed")
    row = result["rows"][0]
    source = next(item for item in rows if isinstance(item, dict) and
                  item.get("candidate_character_id") == candidate_character_id)
    if (
        not isinstance(row, dict)
        or row.get("actor_character_id") != played_id
        or row.get("heir_character_id") != subject_id
        or row.get("candidate_character_id") != candidate_character_id
        or row.get("recipient_character_id") !=
            source.get("recipient_matchmaker_character_id")
        or row.get("status") != result["status"]
        or (request_matrilineal_option and
            row.get("requested_matrilineal_option") is not True)
    ):
        raise BridgeUnavailableError("child marriage value five-role identity changed")
    if result["status"] == "available":
        first = row.get("heir_sex_selector_raw")
        second = row.get("candidate_sex_selector_raw")
        selected = row.get("matrilineal_option_selected")
        effective = row.get("effective_matrilineal_if_accepted")
        pairs = row.get("possible_alliance_pairs")
        candidate_betrothed = row.get("candidate_betrothed_character_id")
        candidate_primary = row.get("candidate_primary_spouse_character_id")
        candidate_spouses = row.get("candidate_spouse_character_ids")
        if (
            row.get("failure") != "none"
            or row.get("projection_failure") != "none"
            or row.get("outcome_failure") != "none"
            or row.get("predicted_outcome_if_accepted") not in {"marriage", "betrothal"}
            or type(first) is not int or first not in {0, 1}
            or type(second) is not int or second not in {0, 1}
            or type(selected) is not bool or type(effective) is not bool
            or effective is not (bool(first) if first == second else selected)
            or row.get("heir_dynasty_id") != legality.get("dynasty_id")
            or row.get("heir_house_id") != legality.get("house_id")
            or type(row.get("candidate_dynasty_id")) is not int
            or not _native_fertility_input_valid(
                row.get("heir_native_fertility"))
            or not _native_fertility_input_valid(
                row.get("candidate_native_fertility"))
            or any(value is not None and
                   (type(value) is not int or value <= 0)
                   for value in (candidate_betrothed, candidate_primary))
            or not isinstance(candidate_spouses, list)
            or any(type(value) is not int or value <= 0
                   for value in candidate_spouses)
            or (candidate_primary is not None and
                candidate_primary not in candidate_spouses)
            or not isinstance(pairs, list) or len(pairs) > 3
            or any(not isinstance(pair, dict) or
                   any(type(pair.get(key)) is not bool for key in
                       ("already_allied", "both_have_realm_data",
                        "would_attempt_if_accepted"))
                    for pair in pairs)
            or (request_matrilineal_option and (
                row.get("selected_option_readback") is not True
                or selected is not True
                or row.get("final_legality_sampled") is not True
                or row.get("complete_can_send") is not True
                or type(row.get("recipient_ai_accept_raw")) is not int
                or row["recipient_ai_accept_raw"] <= 0
                or type(row.get("recipient_answer_status_raw")) is not int
                or row["recipient_answer_status_raw"] not in {0, 1}
            ))
        ):
            raise BridgeUnavailableError("child marriage value native fields malformed")
    return {
        "schema": SCHEMA, "exact_ck3_build": "1.19.0.6",
        "read_only": True, "advertised": False,
        "native_revision": before["native_revision"],
        "legality_query_sequence": legality["query_sequence"],
        "played_character_id": played_id, "subject_character_id": subject_id,
        "candidate_character_id": candidate_character_id,
        "request_matrilineal_option": request_matrilineal_option,
        "status": result["status"], "row": row,
    }
