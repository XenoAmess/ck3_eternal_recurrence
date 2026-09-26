"""Default-OFF, unadvertised paused five-candidate alliance projection.

The native result describes only pairs that the exact-build marriage effect
would consider if the recipient accepted. It is not an alliance receipt,
ranking, utility, or permission to submit a marriage.
"""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError


STEP = "query-first-heir-candidate-alliance-projection-v1-private"
SCHEMA = "xar.ck3.first-heir-candidate-alliance-projection.v1"


def query_first_heir_candidate_alliance_projection_private_v1(
    driver: object, *, legality: dict[str, object],
    candidate_character_ids: list[int], timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Project exactly five distinct IDs from one current final-legal read."""
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if (
        not isinstance(legality, dict)
        or legality.get("schema") !=
           "xar.ck3.observed-first-heir-marriage-legality.v1"
        or legality.get("status") != "available"
        or type(legality.get("native_revision")) is not int
        or legality["native_revision"] <= 0
        or type(legality.get("query_sequence")) is not int
        or legality["query_sequence"] <= 0
        or type(legality.get("observed_first_heir_character_id")) is not int
        or legality["observed_first_heir_character_id"] <= 0
    ):
        raise BridgeUnavailableError("current final-legal first-heir read required")
    if (
        not isinstance(candidate_character_ids, list)
        or len(candidate_character_ids) != 5
        or any(type(value) is not int or not 0 < value < 2**31
               for value in candidate_character_ids)
        or len(set(candidate_character_ids)) != 5
    ):
        raise ValueError("exactly five distinct positive CharacterIDs required")
    legal = legality.get("native_legal_candidates")
    if not isinstance(legal, list):
        raise BridgeUnavailableError("native final-legal candidate rows absent")
    legal_ids = [row.get("candidate_character_id")
                 for row in legal if isinstance(row, dict)]
    if any(legal_ids.count(value) != 1 for value in candidate_character_ids):
        raise BridgeUnavailableError("requested candidate was not uniquely final-legal")

    before = driver.take_snapshot()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        before.get("native_revision") != legality["native_revision"]
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or type(played_id) is not int or played_id <= 0
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError("marriage projection requires same paused frame")
    if any(
        row.get("played_character_id") != played_id or
        row.get("subject_character_id") !=
        legality["observed_first_heir_character_id"]
        for row in legal if isinstance(row, dict) and
        row.get("candidate_character_id") in candidate_character_ids
    ):
        raise BridgeUnavailableError("legal candidate role identity changed")

    request_id = "m5-alliance-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": legality["native_revision"],
        "legality_query_sequence": legality["query_sequence"],
        **{f"candidate_id_{index}": value
           for index, value in enumerate(candidate_character_ids)},
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("marriage projection command_result timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "marriage projection private query RED: " +
            str(frame.get("error") or "unknown"))
    result = frame.get("result")
    if (
        not isinstance(result, dict) or result.get("step") != STEP
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("native_revision") != legality["native_revision"]
        or result.get("legality_query_sequence") != legality["query_sequence"]
        or result.get("status") not in {"available", "unavailable"}
    ):
        raise BridgeUnavailableError("marriage projection native envelope malformed")
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != 5:
        raise BridgeUnavailableError("marriage projection requires five native rows")
    observed_unavailable = False
    for index, row in enumerate(rows):
        if (
            not isinstance(row, dict)
            or row.get("actor_character_id") != played_id
            or row.get("heir_character_id") !=
               legality["observed_first_heir_character_id"]
            or row.get("candidate_character_id") !=
               candidate_character_ids[index]
            or type(row.get("recipient_character_id")) is not int
            or row["recipient_character_id"] <= 0
            or row.get("status") not in {"available", "unavailable"}
            or not isinstance(row.get("failure"), str)
            or not isinstance(row.get("projection_failure"), str)
            or not isinstance(row.get("outcome_failure"), str)
        ):
            raise BridgeUnavailableError("marriage projection row identity malformed")
        pairs = row.get("possible_alliance_pairs")
        if not isinstance(pairs, list) or len(pairs) > 3:
            raise BridgeUnavailableError("marriage projection pair bounds malformed")
        if row["status"] == "unavailable":
            observed_unavailable = True
            if (row["failure"] == "none" or
                row.get("matrilineal_option_selected") is not None or pairs or
                row.get("predicted_outcome_if_accepted") is not None or
                (row["failure"] == "outcome_unavailable" and
                 row["outcome_failure"] == "none")):
                raise BridgeUnavailableError("unavailable projection claims a value")
            continue
        if (row["failure"] != "none" or
            row["projection_failure"] != "none" or
            row["outcome_failure"] != "none" or
            row.get("predicted_outcome_if_accepted") not in
                {"marriage", "betrothal"} or
            type(row.get("matrilineal_option_selected")) is not bool):
            raise BridgeUnavailableError("available projection lost native option")
        for pair in pairs:
            if (
                not isinstance(pair, dict)
                or type(pair.get("first_character_id")) is not int
                or type(pair.get("second_character_id")) is not int
                or pair["first_character_id"] <= 0
                or pair["second_character_id"] <= 0
                or pair["first_character_id"] == pair["second_character_id"]
                or type(pair.get("already_allied")) is not bool
                or type(pair.get("both_have_realm_data")) is not bool
                or type(pair.get("would_attempt_if_accepted")) is not bool
                or pair["would_attempt_if_accepted"] is not (
                    not pair["already_allied"] and
                    pair["both_have_realm_data"])
            ):
                raise BridgeUnavailableError("marriage projection pair malformed")
    if (result["status"] == "available") is observed_unavailable:
        raise BridgeUnavailableError("marriage projection aggregate status disagrees")

    after = driver.take_snapshot()
    after_played = after.get("played_character")
    if (
        after.get("native_revision") != before["native_revision"]
        or after.get("date_raw") != before["date_raw"]
        or after.get("paused") is not True
        or after.get("map_ready") is not True
        or not isinstance(after_played, dict)
        or after_played.get("character_id") != played_id
        or after_played.get("alive") is not True
    ):
        raise BridgeUnavailableError("marriage projection frame changed before consumption")
    return {
        "schema": SCHEMA, "schema_version": 1,
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "status": result["status"],
        "native_revision": legality["native_revision"],
        "legality_query_sequence": legality["query_sequence"],
        "rows": rows,
    }
