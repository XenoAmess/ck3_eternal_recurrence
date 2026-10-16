"""Keep an incomplete battle read distinct from a usable battle-control frame."""
import copy

SCHEMA = "xar.battle-control-readonly-unavailable.v1"
NATIVE_ERROR = "application-main typed query failed or its snapshot changed"
FAILURE = {"executor_enter": True, "executor_exception": {"code": 0, "image": "none", "rva": None},
    "executor_finish": True, "executor_typed_result": False, "final_equal": None, "final_read": None,
    "frame_stable": True, "query_type": "battle_control", "stage": "typed_result", "typed_result": False,
    "wait_completed": True, "wait_result": "completed"}
FRAME_KEYS = ("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id",
              "episode_run_id", "bridge_pid", "connection_generation", "paused", "map_ready")
CLOCK_CAPABILITIES = frozenset({"game.command.research-arm-tactical-daily-sentinel-v1-N",
    "game.command.research-query-tactical-daily-sentinel-v1", "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"})


def exact(a, b):
    if type(a) is not type(b): return False
    if isinstance(b, dict): return a.keys() == b.keys() and all(exact(a[k], v) for k, v in b.items())
    if isinstance(b, list): return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def _frame(snapshot):
    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    if not isinstance(played, dict) or played.get("alive") is not True or not isinstance(diagnostics, dict): return None
    frame = {k: snapshot.get(k) for k in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready")}
    frame.update(actor_character_id=played.get("character_id"), bridge_pid=diagnostics.get("bridge_pid"),
                 connection_generation=diagnostics.get("connection_generation"))
    if (any(type(frame[k]) is not int or frame[k] <= 0 for k in
            ("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation"))
            or not isinstance(frame["episode_run_id"], str) or not frame["episode_run_id"]
            or frame["snapshot_id"] != "native:" + str(frame["native_revision"])
            or frame["paused"] is not True or frame["map_ready"] is not True
            or snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None
            or snapshot.get("one_life_terminal") is not False): return None
    return frame


def _scope(snapshot, subject):
    frame = _frame(snapshot)
    armies, wars = snapshot.get("player_armies"), snapshot.get("active_wars")
    if frame is None or not isinstance(armies, list) or not isinstance(wars, list) or not wars: return None
    own = [a for a in armies if isinstance(a, dict) and a.get("army_id") == subject]
    if (len(own) != 1 or own[0].get("controllable") is not True or own[0].get("in_combat") is not True
            or own[0].get("retreating") is not False or own[0].get("owner_character_id") != frame["actor_character_id"]
            or type(own[0].get("current_province_id")) is not int or own[0]["current_province_id"] <= 0): return None
    province = own[0]["current_province_id"]
    war_ids, participants = [], {subject}
    all_rows = list(armies)
    for war in wars:
        if not isinstance(war, dict) or type(war.get("war_id")) is not int or war["war_id"] <= 0 or war["war_id"] in war_ids: return None
        war_ids.append(war["war_id"])
        for side in ("allied_armies", "enemy_armies"):
            rows = war.get(side)
            if not isinstance(rows, list): return None
            all_rows.extend(rows)
    for army in all_rows:
        if not isinstance(army, dict): return None
        if army.get("current_province_id") == province and army.get("in_combat") is True:
            aid = army.get("army_id")
            if type(aid) is not int or not 0 <= aid <= 2**31 - 1: return None
            participants.add(aid)
    return {"subject_army_id": subject, "province_id": province,
        **{k: frame[k] for k in ("actor_character_id", "episode_run_id", "bridge_pid", "connection_generation")},
        "active_war_ids": sorted(war_ids), "observed_combat_army_ids": sorted(participants)}


def terminal_failure(error, step, native_revision):
    from .battle_control_contract import parse_query_battle_control_snapshot_v1_step
    request, result = getattr(error, "native_request_frame", None), getattr(error, "native_command_result_frame", None)
    rid = getattr(error, "native_request_id", None)
    return bool(parse_query_battle_control_snapshot_v1_step(step) is not None
        and isinstance(rid, str) and rid and isinstance(request, dict) and isinstance(result, dict)
        and exact(request, {"type": "execute_step", "protocol_version": 1, "request_id": rid,
                           "step": step, "expected_revision": native_revision})
        and exact(result, {"type": "command_result", "protocol_version": 1, "request_id": rid,
            "ok": False, "error": NATIVE_ERROR, "typed_query_failure_v1": FAILURE}))


def observe_unavailable(error, step, starting, current):
    from .battle_control_contract import parse_query_battle_control_snapshot_v1_step
    subject = parse_query_battle_control_snapshot_v1_step(step)
    first, final = _frame(starting), _frame(current)
    scope = _scope(starting, subject)
    if (first is None or scope is None or not exact(first, final) or not exact(scope, _scope(current, subject))
            or not terminal_failure(error, step, first["native_revision"])): return None
    result = {"schema": SCHEMA, "step": step, "accepted": False, "status": "unavailable",
        "read_only": True, "business_submission": False, "replay_allowed": False,
        "backend_id": "native-headless", "battle_control_snapshot": None,
        "diagnostic_reason": "native_battle_control_typed_read_failed",
        "prediction_ready": False, "retreat_authorized": False, "scope_key": scope,
        "source_frame": first, "same_frame_readback": final,
        "native_request": copy.deepcopy(error.native_request_frame),
        "native_command_result": copy.deepcopy(error.native_command_result_frame)}
    validate_unavailable(result)
    return result


def validate_unavailable(result, *, planning_source=None):
    from .battle_control_contract import parse_query_battle_control_snapshot_v1_step
    if not isinstance(result, dict) or set(result) != {"schema", "step", "accepted", "status", "read_only",
        "business_submission", "replay_allowed", "backend_id", "battle_control_snapshot", "diagnostic_reason",
        "prediction_ready", "retreat_authorized", "scope_key", "source_frame", "same_frame_readback",
        "native_request", "native_command_result"}: raise ValueError("battle unavailable shape differs")
    subject = parse_query_battle_control_snapshot_v1_step(result["step"])
    source, scope = result["source_frame"], result["scope_key"]
    if (result["schema"] != SCHEMA or subject is None or result["accepted"] is not False
            or result["status"] != "unavailable" or result["read_only"] is not True
            or result["business_submission"] is not False or result["replay_allowed"] is not False
            or result["backend_id"] != "native-headless" or result["battle_control_snapshot"] is not None
            or result["diagnostic_reason"] != "native_battle_control_typed_read_failed"
            or result["prediction_ready"] is not False or result["retreat_authorized"] is not False
            or not isinstance(source, dict) or set(source) != set(FRAME_KEYS)
            or not exact(source, result["same_frame_readback"])
            or any(type(source[k]) is not int or source[k] <= 0 for k in
                ("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation"))
            or source["snapshot_id"] != "native:" + str(source["native_revision"])
            or not isinstance(source["episode_run_id"], str) or not source["episode_run_id"]
            or source["paused"] is not True or source["map_ready"] is not True
            or not isinstance(scope, dict) or set(scope) != {"subject_army_id", "province_id", "actor_character_id",
                "episode_run_id", "bridge_pid", "connection_generation", "active_war_ids", "observed_combat_army_ids"}
            or scope["subject_army_id"] != subject or type(scope["province_id"]) is not int or scope["province_id"] <= 0
            or any(not exact(scope[k], source[k]) for k in ("actor_character_id", "episode_run_id", "bridge_pid", "connection_generation"))):
        raise ValueError("battle unavailable source/scope differs")
    for key in ("active_war_ids", "observed_combat_army_ids"):
        ids = scope[key]
        minimum = 1 if key == "active_war_ids" else 0
        if (not isinstance(ids, list) or not ids or any(type(v) is not int or not minimum <= v <= 2**31 - 1 for v in ids)
                or ids != sorted(set(ids))): raise ValueError("battle unavailable scope IDs malformed")
    if subject not in scope["observed_combat_army_ids"]: raise ValueError("battle unavailable subject absent")
    class Evidence: pass
    error = Evidence()
    error.native_request_frame, error.native_command_result_frame = result["native_request"], result["native_command_result"]
    error.native_request_id = error.native_request_frame.get("request_id") if isinstance(error.native_request_frame, dict) else None
    if not terminal_failure(error, result["step"], source["native_revision"]): raise ValueError("battle unavailable original terminal read differs")
    if planning_source is not None:
        if not isinstance(planning_source, dict) or any(not exact(planning_source.get(k), source[k]) for k in FRAME_KEYS if k not in {"paused", "map_ready"}):
            raise ValueError("battle unavailable public planning frame differs")
    return result


def _progress_key(progress, scope):
    if not isinstance(progress, dict) or not isinstance(progress.get("wars"), list): return False
    ids, participants, subject_seen = [], set(), False
    for war in progress["wars"]:
        if not isinstance(war, dict): return False
        ids.append(war.get("war_id"))
        for side in ("player_armies", "enemy_armies"):
            rows = war.get(side)
            if not isinstance(rows, list): return False
            for army in rows:
                if not isinstance(army, dict): return False
                if army.get("army_id") == scope["subject_army_id"]:
                    subject_seen = army.get("in_combat") is True and army.get("current_province_id") == scope["province_id"]
                    if not subject_seen: return False
                if army.get("in_combat") is True and army.get("current_province_id") == scope["province_id"]:
                    participants.add(army.get("army_id"))
    return subject_seen and sorted(ids) == scope["active_war_ids"] and sorted(participants) == scope["observed_combat_army_ids"]


def _continuous_watch(rows, start_index, start_date, end_date, key, query_step, command, result):
    cursor = start_date
    for row in rows[start_index + 1:]:
        step, dto = command(row), result(row)
        if step == query_step and row.get("ok") is True: return False
        if not isinstance(step, str) or not step.startswith("life-advance"): continue
        if (row.get("ok") is not True or step != "life-advance-one-day" or not isinstance(dto, dict)
                or dto.get("starting_date_raw") != cursor or type(dto.get("ending_date_raw")) is not int
                or dto["ending_date_raw"] not in (cursor, cursor + 24)
                or not _progress_key(dto.get("war_progress_before"), key)
                or not _progress_key(dto.get("war_progress_after"), key)): return False
        cursor = dto["ending_date_raw"]
    return cursor == end_date


def select_watch(snapshot, rows, *, command, result):
    frame = _frame(snapshot)
    if frame is None: return None
    active = sorted(a["army_id"] for a in snapshot.get("player_armies", []) if isinstance(a, dict)
                    and a.get("controllable") is True and a.get("in_combat") is True and type(a.get("army_id")) is int)
    for subject in active:
        key = _scope(snapshot, subject)
        failures = []
        for index, row in enumerate(rows):
            dto = result(row)
            if not isinstance(dto, dict) or dto.get("schema") != SCHEMA: continue
            try: validate_unavailable(dto)
            except (TypeError, ValueError): continue
            if row.get("ok") is False and exact(dto["scope_key"], key): failures.append((index, dto))
        if not failures: continue
        last_index, last = failures[-1]
        cursor = last["source_frame"]["date_raw"]
        if cursor > frame["date_raw"] or not _continuous_watch(rows, last_index, cursor, frame["date_raw"], key, last["step"], command, result): continue
        dates = sorted({dto["source_frame"]["date_raw"] for _, dto in failures})
        cooldown = len(dates) >= 2 and dates[-1] - dates[-2] == 24
        if cooldown:
            previous_index, previous = next((i, d) for i, d in reversed(failures) if d["source_frame"]["date_raw"] == dates[-2])
            cooldown = _continuous_watch(rows, previous_index, dates[-2], frame["date_raw"], key, last["step"], command, result)
        until = dates[-1] + 30 * 24 if cooldown else dates[-1] + 24
        if frame["date_raw"] >= until: continue
        return {"status": "reader_unavailable_hands_off", "subject_army_id": subject,
            "scope_key": copy.deepcopy(key), "original_failure": copy.deepcopy(last),
            "cooldown_active": cooldown, "next_query_date_raw": until,
            "observed_date_raw": frame["date_raw"], "prediction_ready": False, "retreat_authorized": False}
    return None
