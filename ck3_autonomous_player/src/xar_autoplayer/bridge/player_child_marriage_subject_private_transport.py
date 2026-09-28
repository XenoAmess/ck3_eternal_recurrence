"""Private exact-build read of one specified player child and marriage authority."""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .marriage_matchmaking_private_transport import _require_same_paused_frame


STEP = "query-player-child-marriage-subject-v1-private"
SCHEMA = "xar.ck3.player-child-marriage-subject.v1"


def query_player_child_marriage_subject_private_v1(
    driver: object, *, expected_native_revision: int,
    subject_character_id: int, timeout_seconds: float = 360.0,
    diagnose_family_arrays: bool = False,
) -> dict[str, object]:
    if getattr(driver, "allow_private_player_child_marriage_subject_query", False) is not True:
        raise UnsupportedStepError("private player-child marriage query is disabled")
    before = driver.take_snapshot()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        type(expected_native_revision) is not int
        or expected_native_revision <= 0
        or before.get("native_revision") != expected_native_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or type(played_id) is not int or played_id <= 0
        or type(before.get("revision")) is not int
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError("player-child marriage query needs a paused living-player map frame")
    if type(subject_character_id) is not int or not 0 < subject_character_id < 2**31:
        raise ValueError("subject_character_id must be a positive native CharacterID")
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if type(diagnose_family_arrays) is not bool:
        raise ValueError("diagnose_family_arrays must be bool")
    request_id = "family-child-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": expected_native_revision,
        "subject_character_id": subject_character_id,
        "diagnose_family_arrays": diagnose_family_arrays,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("player-child marriage query timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "player-child marriage query RED: " + str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    _require_same_paused_frame(
        driver.take_snapshot(), before, expected_native_revision, played_id
    )
    if (
        not isinstance(result, dict)
        or result.get("step") != STEP
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("subject_source") != "specified_player_child"
        or result.get("native_revision") != expected_native_revision
        or result.get("subject_character_id") != subject_character_id
        or type(result.get("query_sequence")) is not int
        or result["query_sequence"] <= 0
    ):
        raise BridgeUnavailableError("player-child marriage response identity changed")
    base = {
        "schema": SCHEMA, "schema_version": 1,
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "native_revision": expected_native_revision,
        "played_character_id": played_id,
        "subject_character_id": subject_character_id,
        "query_sequence": result["query_sequence"],
    }
    probe = result.get("family_array_diagnostic")
    if diagnose_family_arrays:
        if (
            not isinstance(probe, dict)
            or probe.get("available") is not True
            or probe.get("played_character_id") != played_id
            or type(probe.get("spouse_readable")) is not bool
            or type(probe.get("primary_spouse_character_id")) is not int
            or not isinstance(probe.get("slots"), list)
            or len(probe["slots"]) != 6
            or any(not isinstance(slot, dict) for slot in probe["slots"])
            or [slot.get("offset") for slot in probe["slots"]]
            != [0x20, 0x30, 0x40, 0x50, 0x60, 0x70]
        ):
            raise BridgeUnavailableError("player family array diagnostic malformed")
        for slot in probe["slots"]:
            samples = slot.get("samples")
            if (
                any(type(slot.get(key)) is not bool for key in (
                    "header_readable", "data_pointer_present",
                    "native_int_array_shape", "sample_readable"))
                or type(slot.get("capacity")) is not int
                or type(slot.get("count")) is not int
                or not isinstance(samples, list) or len(samples) > 16
                or any(not isinstance(sample, dict)
                       or type(sample.get("character_id")) is not int
                       or type(sample.get("generation_valid")) is not bool
                       for sample in samples)
            ):
                raise BridgeUnavailableError("player family array slot malformed")
        base["family_array_diagnostic"] = probe
    elif probe is not None:
        raise BridgeUnavailableError("unsolicited player family array diagnostic")
    if result.get("status") == "unavailable":
        reason = result.get("unavailable_reason")
        if (
            not isinstance(reason, str) or not reason
            or result.get("player_child_verified") is not False
            or result.get("family_candidates") != []
        ):
            raise BridgeUnavailableError("unavailable player-child marriage read malformed")
        return {**base, "status": "unavailable", "unavailable_reason": reason}
    if result.get("status") != "available":
        raise BridgeUnavailableError("player-child marriage status invalid")
    betrothed = result.get("betrothed_character_id")
    primary_spouse = result.get("primary_spouse_character_id")
    spouses = result.get("spouse_character_ids")
    age = result.get("adult_measure_raw")
    house = result.get("house_id")
    dynasty = result.get("dynasty_id")
    employer = result.get("employer_character_id")
    rows = result.get("family_candidates")
    diagnostics = result.get("arrange_marriage_diagnostics")
    if (
        result.get("unavailable_reason") is not None
        or result.get("player_child_verified") is not True
        or result.get("bilateral_verified") is not True
        or type(age) is not int or not -2**15 <= age < 2**15
        or result.get("adult_threshold_raw") != 16
        or result.get("adult") is not (age >= 16)
        or (house is not None and (type(house) is not int or house < 0))
        or (dynasty is not None and (type(dynasty) is not int or dynasty < 0))
        or (employer is not None and (type(employer) is not int or employer <= 0))
        or any(value is not None and (type(value) is not int or value <= 0)
               for value in (betrothed, primary_spouse))
        or not isinstance(spouses, list)
        or any(type(value) is not int or value <= 0 for value in spouses)
        or len(set(spouses)) != len(spouses)
        or (betrothed is not None and
            (betrothed == primary_spouse or betrothed in spouses))
        or not isinstance(rows, list)
        or not isinstance(diagnostics, dict)
        or type(diagnostics.get("slots_scanned")) is not int
        or diagnostics.get("slots_scanned") != diagnostics.get("storage_capacity")
    ):
        raise BridgeUnavailableError("available player-child marriage read malformed")
    seen: set[int] = set()
    legal_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise BridgeUnavailableError("player-child marriage candidate malformed")
        candidate_id = row.get("candidate_character_id")
        answer = row.get("recipient_answer_status_raw")
        if (
            type(candidate_id) is not int or candidate_id <= 0
            or candidate_id in seen
            or row.get("played_character_id") != played_id
            or row.get("subject_character_id") != subject_character_id
            or type(row.get("recipient_matchmaker_character_id")) is not int
            or row["recipient_matchmaker_character_id"] <= 0
            or row.get("complete_can_send") is not True
            or type(row.get("recipient_ai_accept_raw")) is not int
            or type(answer) is not int or answer not in {0, 1, 2}
            or row.get("recipient_answer_allows_send") is not (answer != 2)
        ):
            raise BridgeUnavailableError("player-child marriage legality row malformed")
        seen.add(candidate_id)
        if answer != 2:
            legal_rows.append(row)
    return {
        **base, "status": "available", "unavailable_reason": None,
        "player_child_verified": True, "adult_measure_raw": age,
        "adult_threshold_raw": 16, "adult": age >= 16,
        "house_id": house, "dynasty_id": dynasty,
        "employer_character_id": employer,
        "betrothed_character_id": betrothed,
        "primary_spouse_character_id": primary_spouse,
        "spouse_character_ids": spouses,
        "bilateral_verified": True,
        "candidates": rows, "native_legal_candidates": legal_rows,
        "diagnostics": diagnostics,
        "family_subject_role_mismatches": result.get("family_subject_role_mismatches"),
    }
