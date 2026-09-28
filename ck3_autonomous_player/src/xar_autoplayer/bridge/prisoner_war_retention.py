"""Source-bound, read-only war retention projection for player prisoners.

The caller must supply a complete native participant/succession scan before a
negative PoW result is possible.  No CK3 command or release is issued here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


_FRAME_FIELDS = (
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "played_character_id",
    "episode_run_id",
)


def _positive_id(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value < 2**31:
        raise ValueError(f"{name} must be a positive full native ID")
    return value


def _optional_id(value: object, name: str) -> int | None:
    return None if value is None else _positive_id(value, name)


def _ids(value: object, name: str) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array or unavailable")
    ids = [_positive_id(item, name) for item in value]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name} contains duplicate full IDs")
    return ids


def _same_frame(
    first: Mapping[str, object], second: Mapping[str, object]
) -> bool:
    return all(first.get(field) is not None and first.get(field) == second.get(field)
               for field in _FRAME_FIELDS)


def normalize_war_prisoner_release_pairs_v1(
    raw: Mapping[str, object], *, expected_step: str,
    expected_war_id: int, expected_snapshot_revision: object,
    expected_date_raw: object,
) -> dict[str, object]:
    """Fail closed on a native generic PoW source scan and its frame binding."""
    if (raw.get("step") != expected_step or raw.get("accepted") is not True
            or raw.get("status") != "available" or raw.get("read_only") is not True
            or raw.get("backend_id") != "native-headless"):
        raise ValueError("native query envelope is not an available read-only result")
    revision = raw.get("snapshot_revision")
    if (type(revision) is not int or revision <= 0
            or revision != expected_snapshot_revision):
        raise ValueError("native query revision differs from the paused frame")
    sequence = raw.get("query_sequence")
    if type(sequence) is not int or sequence <= 0:
        raise ValueError("native query sequence is invalid")
    value = raw.get("war_prisoner_release_pairs_v1")
    if not isinstance(value, Mapping):
        raise ValueError("native prisoner release observation is missing")
    if value.get("war_id") != expected_war_id or value.get("date_raw") != expected_date_raw:
        raise ValueError("native prisoner release identity or date differs")
    cb_index = value.get("active_casus_belli_database_index")
    cb_key = value.get("active_casus_belli_key")
    if (type(cb_index) is not int or cb_index < 0
            or not isinstance(cb_key, str) or not cb_key):
        raise ValueError("native prisoner release CB identity is unavailable")
    attacker = _positive_id(value.get("primary_attacker_character_id"), "primary attacker")
    defender = _positive_id(value.get("primary_defender_character_id"), "primary defender")
    attackers = _ids(value.get("attacker_participant_ids"), "attacker participants")
    defenders = _ids(value.get("defender_participant_ids"), "defender participants")
    attacker_candidates = _ids(value.get("attacker_release_candidate_ids"), "attacker candidates")
    defender_candidates = _ids(value.get("defender_release_candidate_ids"), "defender candidates")
    if (value.get("same_frame_stable") is not True
            or value.get("full_participant_scan") is not True
            or value.get("primary_and_first_three_successors_scanned") is not True
            or attackers is None or defenders is None
            or attacker_candidates is None or defender_candidates is None
            or attacker not in attackers or defender not in defenders
            or attacker_candidates[:1] != [attacker]
            or defender_candidates[:1] != [defender]
            or len(attacker_candidates) > 4 or len(defender_candidates) > 4
            or set(attackers) & set(defenders)):
        raise ValueError("native participant/successor scan is incomplete")
    pairs = value.get("release_pairs")
    if not isinstance(pairs, list):
        raise ValueError("native release pairs are unavailable")
    seen: set[tuple[int, int]] = set()
    for pair in pairs:
        if not isinstance(pair, Mapping):
            raise ValueError("native release pair is malformed")
        jailer = _positive_id(pair.get("jailer_character_id"), "jailer")
        prisoner = _positive_id(pair.get("prisoner_character_id"), "prisoner")
        if (jailer, prisoner) in seen or not (
            (jailer in attackers and prisoner in defender_candidates)
            or (jailer in defenders and prisoner in attacker_candidates)
        ):
            raise ValueError("native release pair contradicts the complete scan")
        seen.add((jailer, prisoner))
        if not isinstance(pair.get("reason"), str):
            raise ValueError("native release reason is malformed")
    return dict(value)


def project_prisoner_war_retention(
    *,
    war: Mapping[str, object],
    prisoners: Sequence[Mapping[str, object]],
    exit_options: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Join one paused war to full-ID custody rows without inventing absences.

    ``war`` may leave producer fields null until the generic native PoW reader
    supplies them.  Completed list scans must set both explicit scan flags;
    empty lists alone never prove an empty release set.  ``exit_options`` is a
    separate native feasibility read, not evidence that an exit occurred.
    """
    frame = war.get("frame")
    if not isinstance(frame, Mapping) or not all(frame.get(k) is not None for k in _FRAME_FIELDS):
        raise ValueError("war frame is incomplete")
    war_id = _positive_id(war.get("war_id"), "war_id")
    cb_key = war.get("cb_key")
    if cb_key is not None and (not isinstance(cb_key, str) or not cb_key):
        raise ValueError("cb_key must be a nonempty string or unavailable")

    attacker = _optional_id(war.get("primary_attacker_character_id"), "primary attacker")
    defender = _optional_id(war.get("primary_defender_character_id"), "primary defender")
    attacker_house = _optional_id(war.get("primary_attacker_house_id"), "attacker house")
    attackers = _ids(war.get("attacker_participant_ids"), "attacker participants")
    defenders = _ids(war.get("defender_participant_ids"), "defender participants")
    attacker_candidates = _ids(war.get("attacker_release_candidate_ids"), "attacker release candidates")
    defender_candidates = _ids(war.get("defender_release_candidate_ids"), "defender release candidates")
    complete = (war.get("full_participant_scan") is True
                and war.get("primary_and_first_three_successors_scanned") is True
                and all(value is not None for value in (
                    attacker, defender, attackers, defenders,
                    attacker_candidates, defender_candidates,
                )))
    if complete:
        assert attackers is not None and defenders is not None
        assert attacker_candidates is not None and defender_candidates is not None
        if (attacker not in attackers or defender not in defenders
                or attacker_candidates[0:1] != [attacker]
                or defender_candidates[0:1] != [defender]
                or len(attacker_candidates) > 4 or len(defender_candidates) > 4
                or set(attackers) & set(defenders)):
            raise ValueError("native war participant or primary-succession scan is inconsistent")

    reachable: bool | None = None
    if exit_options is not None:
        option_frame = exit_options.get("frame")
        if not isinstance(option_frame, Mapping) or not _same_frame(frame, option_frame):
            raise ValueError("war exit options do not match the paused war frame")
        if exit_options.get("war_id") != war_id or exit_options.get("cb_key") != cb_key:
            raise ValueError("war exit options identity differs from war reader")
        options = exit_options.get("options")
        if not isinstance(options, Mapping) or set(options) != {"surrender", "white_peace", "victory"}:
            raise ValueError("war exit option availability is incomplete")
        if not all(type(value) is bool for value in options.values()):
            raise ValueError("war exit option availability must be boolean")
        reachable = any(options.values())

    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for prisoner in prisoners:
        row_frame = prisoner.get("frame")
        if not isinstance(row_frame, Mapping) or not _same_frame(frame, row_frame):
            raise ValueError("prisoner collection does not match the paused war frame")
        prisoner_id = _positive_id(prisoner.get("character_id"), "prisoner")
        if prisoner_id in seen:
            raise ValueError("prisoner collection contains duplicate full IDs")
        seen.add(prisoner_id)
        jailer_id = _optional_id(prisoner.get("jailer_character_id"), "jailer")
        house_id = _optional_id(prisoner.get("house_id"), "prisoner house")
        house_observable = prisoner.get("house_observable")
        if type(house_observable) is not bool:
            raise ValueError("prisoner House observability must be explicit")
        custody_status = prisoner.get("custody_status")
        if custody_status not in {"held_by_jailer", "unavailable"}:
            raise ValueError("custody status must be explicit")
        pow_side: str | None = None
        if cb_key == "fp3_free_house_member_cb":
            # Stock surrender / white peace / victory interactions skip
            # release_prisoners_of_war_effect for this CB.
            pow_status = "not_applicable_cb"
        elif not complete or custody_status != "held_by_jailer" or jailer_id is None:
            pow_status = "unavailable"
        elif jailer_id in defenders and prisoner_id in attacker_candidates:
            pow_status, pow_side = "matched_pair", "defender_jailer"
        elif jailer_id in attackers and prisoner_id in defender_candidates:
            pow_status, pow_side = "matched_pair", "attacker_jailer"
        else:
            pow_status = "not_in_pairs"

        if cb_key is None:
            fp3_status = "unavailable"
        elif cb_key != "fp3_free_house_member_cb":
            fp3_status = "not_applicable_cb"
        elif not house_observable:
            fp3_status = "unavailable"
        elif house_id is None:
            fp3_status = "not_applicable_no_house"
        elif (not complete or attacker is None or defender is None or attacker_house is None
              or attackers is None or defenders is None or jailer_id is None
              or custody_status != "held_by_jailer"):
            fp3_status = "unavailable"
        elif (jailer_id in defenders and attacker in attackers
              and defender in defenders and house_id == attacker_house):
            fp3_status = "matched_house"
        else:
            fp3_status = "not_matched"

        if pow_status == "matched_pair" or fp3_status == "matched_house":
            commitment = "present"
        elif pow_status == "unavailable" or fp3_status == "unavailable":
            commitment = "unavailable"
        else:
            commitment = "not_from_these_two_rules"
        rows.append({
            "prisoner_character_id": prisoner_id,
            "jailer_character_id": jailer_id,
            "prisoner_house_id": house_id,
            "generic_pow_pair_status": pow_status,
            "generic_pow_pair_side": pow_side,
            "generic_pow_exit_attainable_now": reachable if pow_status == "matched_pair" else None,
            "fp3_house_member_status": fp3_status,
            "fp3_prestige_effect": (
                {"attacker": "major_prestige_gain", "defender": "major_prestige_loss",
                 "actual_amount": None}
                if fp3_status == "matched_house" else None
            ),
            "pending_war_retention_commitment": commitment,
        })
    return {
        "schema": "xar.ck3.prisoner-war-retention-source-join.v1",
        "frame": dict(frame),
        "war_id": war_id,
        "cb_key": cb_key,
        "generic_pow_source_scan_complete": complete,
        "war_exit_option_available_now": reachable,
        "prisoners": rows,
        "read_only": True,
    }
