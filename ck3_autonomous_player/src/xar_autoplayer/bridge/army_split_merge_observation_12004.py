"""Read-only split/merge observations for E04 and ordinary Army consumers.

Inputs are already normalized native DTOs. These helpers never submit commands,
repair a cohort, infer a physical soldier write, or award live qualification.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _integer(value: object, name: str) -> int:
    _need(type(value) is int, name + " must retain an integer")
    return value


def classify_regiment_observation(
    strength: Mapping[str, object], data: Mapping[str, object] | None,
) -> dict[str, object]:
    """Separate ArRg cached 1/1 from associated persistent DATA and its predicate.

    A true native predicate identifies the source Character override branch.
    It does not identify a knight/commander or prove this record's birth.
    """
    identity = _integer(strength.get("army_regiment_id"), "army_regiment_id")
    current = _integer(strength.get("current_soldiers"), "current_soldiers")
    maximum = _integer(strength.get("maximum_soldiers"), "maximum_soldiers")
    _need(strength.get("scale") == 1, "ArRg soldiers must retain scale 1")
    _need(current >= 0 and maximum >= 0, "ArRg cache is not available")
    predicate = None
    count = None
    complete = False
    if data is not None:
        _need(data.get("army_regiment_id") == identity, "DATA belongs to another full ArRg ID")
        predicate = data.get("native_loss_writer_skipped")
        _need(predicate is None or type(predicate) is bool, "Character predicate must be bool or null")
        count = data.get("native_data_record_count")
        _need(count is None or type(count) is int and count >= 0, "DATA count is invalid")
        records = data.get("records")
        complete = (data.get("status") == "available" and data.get("ready") is True
                    and type(records) is list and count == len(records))
    one_one = current == maximum == 1
    kind = ("character_override_1_1" if predicate is True and one_one else
            "character_predicate_without_1_1_cache" if predicate is True else
            "noncharacter_DATA" if predicate is False and complete and count else
            "noncharacter_empty_DATA" if predicate is False and complete else
            "unclassified_1_1" if one_one else "unclassified")
    return {"army_regiment_id": identity, "kind": kind,
            "current_soldiers": current, "maximum_soldiers": maximum,
            "native_loss_writer_skipped": predicate,
            "DATA_complete": complete, "native_data_record_count": count,
            "physical_soldier_write_observed": False,
            "birth_producer_observed": False, "player_troop_class": None}


def read_bound_native_army_resolution(row, *, army_id):
    def need(v,m):
        if not v:raise ValueError(m)
    need(isinstance(row,dict) and type(army_id) is int and type(row.get('army_id')) is int and row['army_id']==army_id,'normalized Army row belongs to another public CUnit')
    need(row.get('status')=='available','normalized Army row unavailable')
    native=row.get('native_carmy_id');need(type(native) is int and -(2**31)<=native<2**31 and native!=-1,'actual native CArmy FullID unavailable')
    r=row.get('native_army_resolution_v1');keys={'status','ready','branch','raw_reference','reference_index','storage_capacity','entry_full_id'}
    need(isinstance(r,dict) and set(r)==keys,'typed native resolution schema absent')
    need(r['status']=='available' and r['ready'] is True and r['branch']=='resolved','typed native resolution not available/resolved')
    need(all(type(r[k]) is int and -(2**31)<=r[k]<2**31 for k in ('raw_reference','reference_index','storage_capacity','entry_full_id')),'typed native resolution integer inputs unavailable')
    need(r['raw_reference']==r['entry_full_id']==native,'typed CArmy reference/full generation does not match actual row')
    need(0<=r['reference_index']<r['storage_capacity'],'typed native resolution entry outside current storage')
    return {'army_id':army_id,'native_carmy_id':native,'native_army_resolution_v1':dict(r)}


def _roster(frame: Mapping[str, object]) -> dict[int, Mapping[str, object]]:
    rows = frame.get("player_armies")
    _need(isinstance(rows, list), "complete player roster is required")
    result = {}
    for row in rows:
        _need(isinstance(row, Mapping), "player roster row is invalid")
        identity = _integer(row.get("army_id"), "public CUnit FullID")
        _need(identity not in result, "duplicate public CUnit FullID")
        result[identity] = row
    return result


def _fresh_pair(before: Mapping[str, object], after: Mapping[str, object]) -> None:
    for frame in (before, after):
        _need(frame.get("paused") is True and frame.get("map_ready") is True,
              "independent paused ready frames are required")
        _need(isinstance(frame.get("snapshot_id"), str) and bool(frame["snapshot_id"]),
              "snapshot identity is missing")
    _need(before["snapshot_id"] != after["snapshot_id"], "post-frame is not independently fresh")
    for field in ("revision", "native_revision"):
        _need(_integer(after.get(field), field) > _integer(before.get(field), field),
              "post-frame revision must advance")
    _need(before.get("episode_run_id") and before.get("episode_run_id") == after.get("episode_run_id"),
          "episode changed or is unknown")
    _need(_integer(before.get("date_raw"), "date_raw") == after.get("date_raw"),
          "same-date microexperiment advanced time")
    for field in ("bridge_pid", "connection_generation"):
        first = before.get("diagnostics", {}).get(field)
        second = after.get("diagnostics", {}).get(field)
        _need(type(first) is int and first > 0 and first == second,
              "process/connection identity changed or is unknown")
    first = before.get("played_character", {})
    second = after.get("played_character", {})
    _need(first.get("alive") is True and second.get("alive") is True
          and type(first.get("character_id")) is int
          and first["character_id"] == second.get("character_id"),
          "played Character changed or is unknown")


def identify_split_sibling(
    before: Mapping[str, object], after: Mapping[str, object], *,
    source_army_id: int, pre_strengths: Mapping[str, object],
    post_strengths: Mapping[str, object],
) -> dict[str, object]:
    """Identify a fresh sibling from exact set difference, then typed CArmy map.

    No ACK or supplied sibling ID is accepted as identity evidence. A missing
    postcondition raises without recommending resubmission of an unknown action.
    """
    _integer(source_army_id, "source public CUnit FullID")
    _fresh_pair(before, after)
    old, new = _roster(before), _roster(after)
    _need(source_army_id in old and source_army_id in new, "original source did not survive")
    added = set(new) - set(old)
    _need(len(added) == 1 and set(old) <= set(new), "split roster is not exactly old plus one sibling")
    sibling = next(iter(added))
    original = old[source_army_id]
    actor = before["played_character"]["character_id"]
    _need(original.get("controllable") is True and original.get("owner_character_id") == actor
          and type(original.get("current_province_id")) is int,
          "source owner/province/control input is unavailable")
    for identity in (source_army_id, sibling):
        row = new[identity]
        _need(row.get("controllable") is True and row.get("owner_character_id") == actor
              and row.get("current_province_id") == original.get("current_province_id"),
              "split owner/province/control postcondition differs")
    def mapping(packet, frame):
        _need(packet.get("accepted") is True
              and packet.get("queried_snapshot_id") == frame["snapshot_id"]
              and packet.get("queried_revision") == frame["revision"]
              and packet.get("queried_native_revision") == frame["native_revision"],
              "CArmy map is not bound to its own independent frame")
        mapped = {}
        for row in packet.get("army_strengths", []):
            identity = row.get("army_id")
            _need(identity not in mapped, "duplicate strengths CUnit FullID")
            mapped[identity] = row
        return mapped
    old_mapped, mapped = mapping(pre_strengths, before), mapping(post_strengths, after)
    result = {}
    for identity in (source_army_id, sibling):
        row = mapped.get(identity, {})
        _need(row.get("status") == "available", "split CArmy map unavailable")
        result[identity] = _integer(row.get("native_carmy_id"), "native CArmy FullID")
        _need(result[identity] != -1, "native CArmy FullID is the invalid sentinel")
    old_source = old_mapped.get(source_army_id, {})
    _need(old_source.get("status") == "available"
          and old_source.get("native_carmy_id") == result[source_army_id],
          "original native CArmy generation did not survive")
    _need(len(set(result.values())) == 2, "split children resolve to the same CArmy")
    return {"source_army_id": source_army_id, "sibling_army_id": sibling,
            "native_carmy_ids": result, "identity_verified": True,
            "cohort_conservation_verified": False, "commander_verified": False}


def _cohort(armies: Sequence[Mapping[str, object]]) -> tuple[dict, dict]:
    strengths, records = {}, {}
    for army in armies:
        _need(army.get("status") == "available", "Army strength row unavailable")
        rows = army.get("regiment_strengths")
        data = army.get("regiment_replenishment_records_v1")
        _need(isinstance(rows, list) and len(rows) == army.get("regiment_count"),
              "complete ArRg strength roster is required")
        _need(isinstance(data, list), "complete DATA row collection is required")
        data_map = {}
        for row in data:
            identity = row.get("army_regiment_id")
            _need(identity not in data_map, "duplicate DATA ArRg FullID")
            _need(row.get("status") == "available" and row.get("ready") is True
                  and type(row.get("records")) is list
                  and row.get("native_data_record_count") == len(row["records"]),
                  "partial DATA must not be filled with zero")
            data_map[identity] = row
        local_current = local_maximum = 0
        for row in rows:
            identity = _integer(row.get("army_regiment_id"), "ArRg FullID")
            _need(identity not in strengths and identity in data_map, "ArRg duplicate or DATA identity missing")
            classification = classify_regiment_observation(row, data_map[identity])
            local_current += classification["current_soldiers"]
            local_maximum += classification["maximum_soldiers"]
            strengths[identity] = row
            records[identity] = data_map[identity]
        _need(set(data_map) == {row["army_regiment_id"] for row in rows}, "DATA contains extra ArRg IDs")
        _need((local_current, local_maximum) == (army.get("current_soldiers"), army.get("maximum_soldiers")),
              "ArRg strength sum differs from the actual Army cache")
    return strengths, records


def compare_split_merge_cohorts(
    before_armies: Sequence[Mapping[str, object]],
    after_armies: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Compare original cohort and whole strategy Army without dropping extras.

    Caller binds these DTOs to their respective frames/lifecycle. This comparison
    cannot identify the cause or physical instruction of a cache difference.
    """
    old, old_data = _cohort(before_armies)
    new, new_data = _cohort(after_armies)
    added, missing = sorted(set(new)-set(old)), sorted(set(old)-set(new))
    changed = sorted(i for i in set(old) & set(new) if old[i] != new[i])
    data_changed = sorted(i for i in set(old_data) & set(new_data)
                          if old_data[i]["records"] != new_data[i]["records"])
    predicate_changed = sorted(i for i in set(old_data) & set(new_data)
                               if old_data[i].get("native_loss_writer_skipped")
                               != new_data[i].get("native_loss_writer_skipped"))
    def totals(rows):
        return [sum(r[k] for r in rows) for k in ("current_soldiers", "maximum_soldiers")]
    original_survivors = [new[i] for i in old if i in new]
    return {"original_ids": sorted(old), "added_ids": added, "missing_ids": missing,
            "changed_original_strength_ids": changed, "changed_original_DATA_ids": data_changed,
            "changed_original_character_predicate_ids": predicate_changed,
            "original_before_current_max": totals(old.values()),
            "original_after_current_max": totals(original_survivors),
            "whole_after_current_max": totals(new.values()),
            "added_regiments": [classify_regiment_observation(new[i], new_data[i]) for i in added],
            "frozen_exact_cohort_pass": not (added or missing or changed or data_changed or predicate_changed),
            "actual_physical_refill": None, "birth_producer_observed": False}


def read_bound_current_commander(
    packet: Mapping[str, object], frame: Mapping[str, object], *,
    army_id: int, native_carmy_id: int,
) -> int | None:
    """Read the actual assigned commander from its independent typed query.

    Candidate quality, movement preview context and proposed assignment do not
    supply this identity. Query failure stays unavailable instead of becoming 0.
    """
    _need(packet.get("accepted") is True and packet.get("read_only") is True,
          "typed commander query is unavailable")
    _need(packet.get("queried_snapshot_id") == frame.get("snapshot_id")
          and packet.get("queried_revision") == frame.get("revision")
          and packet.get("queried_native_revision") == frame.get("native_revision"),
          "commander query is not bound to its own frame")
    value = packet.get("army_commander_candidates", {})
    _need(value.get("army_id") == army_id and value.get("native_carmy_id") == native_carmy_id
          and value.get("date_raw") == frame.get("date_raw")
          and value.get("snapshot_revision") == frame.get("native_revision"),
          "commander receiver/date/full-generation map differs")
    current = value.get("current_commander", {})
    if current.get("status") == "absent":
        _need(current.get("character_id") is None, "absent commander has an invented ID")
        return None
    _need(current.get("status") == "available", "assigned commander identity unavailable")
    identity = _integer(current.get("character_id"), "actual assigned commander FullID")
    _need(identity != -1, "assigned commander FullID is the invalid sentinel")
    return identity
