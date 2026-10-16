"""Pure scope check for an exact-day contact route's starting war frame.

The caller independently validates Game/actor/frame binding, the complete
Native route horizon, one-day clock stop, and paused postcondition. This
check grants no action, war outcome, or material credit.
"""

_MAX_PUBLIC_ARMY_ID = 2**31 - 1


def observe_route_contact_exact_day_war_scope_v1(
    *, before, after, planned_wars, selected_hostile_ids,
    subject_army_id, start_date_raw, end_date_raw,
):
    """Require every observed non-retreating enemy in the selected set.

    Native's explicit `retreating is True` excludes an army from current
    contact. Missing/unknown retreat data stays in scope. A war may end or
    begin during the native-stopped day; ending rows are validated but never
    substituted for the frozen starting contact scope.
    """
    def require(ok, message):
        if not ok:
            raise ValueError("route-contact exact-day war scope: " + message)

    require(type(start_date_raw) is int and type(end_date_raw) is int
            and end_date_raw == start_date_raw + 24, "exact one-day dates")
    require(type(subject_army_id) is int and 0 <= subject_army_id <= _MAX_PUBLIC_ARMY_ID,
            "subject public CUnit ID")
    require(isinstance(selected_hostile_ids, (list, tuple))
            and 0 < len(selected_hostile_ids) <= 64
            and all(type(value) is int and 0 <= value <= _MAX_PUBLIC_ARMY_ID
                    for value in selected_hostile_ids)
            and list(selected_hostile_ids) == sorted(set(selected_hostile_ids))
            and subject_army_id not in selected_hostile_ids,
            "selected hostile IDs")
    require(isinstance(planned_wars, list) and 0 < len(planned_wars) <= 64
            and all(isinstance(war, dict) and type(war.get("war_id")) is int
                    and war["war_id"] > 0 for war in planned_wars),
            "planned active wars")
    planned_ids = [war["war_id"] for war in planned_wars]
    require(len(set(planned_ids)) == len(planned_ids), "duplicate planned war")

    def observed(progress, expected_date_raw, *, starting):
        require(isinstance(progress, dict)
                and progress.get("date_raw") == expected_date_raw
                and isinstance(progress.get("wars"), list)
                and len(progress["wars"]) <= 64
                and (not starting or bool(progress["wars"])),
                "observed war watch/date")
        wars, players, current_hostiles, retreating = set(), set(), set(), set()
        for war in progress["wars"]:
            require(isinstance(war, dict) and type(war.get("war_id")) is int
                    and war["war_id"] > 0 and war["war_id"] not in wars,
                    "observed war identity")
            wars.add(war["war_id"])
            for key in ("player_armies", "enemy_armies"):
                rows = war.get(key)
                require(isinstance(rows, list) and len(rows) <= 4096,
                        "complete war-side roster")
                for row in rows:
                    require(isinstance(row, dict) and type(row.get("army_id")) is int
                            and 0 <= row["army_id"] <= _MAX_PUBLIC_ARMY_ID,
                            "public CUnit ID")
                    if key == "player_armies":
                        players.add(row["army_id"])
                    elif row.get("retreating") is True:
                        retreating.add(row["army_id"])
                    else:
                        current_hostiles.add(row["army_id"])
        return wars, players, current_hostiles, retreating

    old_wars, old_players, old_hostiles, old_retreating = observed(
        before, start_date_raw, starting=True)
    new_wars, _, _, _ = observed(after, end_date_raw, starting=False)
    require(subject_army_id in old_players, "subject absent from original player scope")
    require(set(planned_ids) == old_wars, "selected war IDs differ from original scope")
    require(set(selected_hostile_ids) == old_hostiles,
            "selected hostile IDs differ from complete non-retreating scope")
    return {
        "status": "observed_starting_scope",
        "starting_war_ids": sorted(old_wars),
        "ending_war_ids": sorted(new_wars),
        "selected_hostile_ids": list(selected_hostile_ids),
        "excluded_observed_retreating_ids": sorted(old_retreating - old_hostiles),
        "war_scope_transition_observed": old_wars != new_wars,
        "action_credit": False,
        "war_outcome_credit": False,
        "material_credit": False,
    }
