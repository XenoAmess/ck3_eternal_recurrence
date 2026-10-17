def classify_first_heir_preread_readonly_v1(row):
    """Only the named Native first-heir PRE-read guard, never a during-read failure."""
    import re
    if not isinstance(row, dict):
        return None
    request, result = row.get("request"), row.get("result")
    if (not isinstance(request, dict) or request.get("tool") != "ck3_auto_turn"
            or request.get("arguments") != {} or type(request.get("sequence")) is not int
            or request["sequence"] <= 0 or row.get("client_error") is not None
            or not isinstance(result, dict) or result.get("is_error") is not True
            or result.get("result_type") != "complete"
            or result.get("structured_content") is not None):
        return None
    content = result.get("content")
    if (not isinstance(content, list) or len(content) != 1
            or not isinstance(content[0], dict) or content[0].get("type") != "text"):
        return None
    text = content[0].get("text")
    prefix = ("Error executing tool ck3_auto_turn: current heir relationship query RED: "
              "current first-heir relationship frame changed; pre_read_guard=")
    if not isinstance(text, str) or not text.startswith(prefix) or len(text) > 16384:
        return None
    parts = text[len(prefix):].split("; ")
    if len(parts) not in (5, 6) or parts[-1] != "complex_field_values=presence_or_count_only":
        return None
    guard = parts[0]
    guards = {"previous_snapshot_missing": False, "snapshot_read_failed": False,
              "snapshot_not_equal": True, "not_paused": True, "map_not_ready": True,
              "played_character_missing": True, "played_character_not_alive": True}
    if guard not in guards or parts[1] != "snapshot_read_completed=" + str(guards[guard]).lower():
        return None
    names = ("date_raw", "speed", "paused", "player_id", "map_ready", "has_played_character",
             "played_character_id", "played_character_alive", "played_character_stress_points",
             "played_character_event_trait_membership_present", "played_character_gold_raw",
             "played_character_gold_scale", "played_character_prestige_raw", "played_character_prestige_scale",
             "played_character_piety_raw", "played_character_piety_scale", "played_character_betrothed_id",
             "played_character_primary_spouse_id", "played_character_spouse_ids_count", "has_active_event",
             "active_event_instance_id", "active_event_option_count", "has_pending_character_interaction",
             "pending_character_interaction_id", "pending_sender_character_id", "pending_auto_accept_notification",
             "active_wars_count", "player_armies_count", "has_one_life_settlement")
    differences = ("date_raw", "speed", "paused", "player_id", "map_ready", "has_played_character",
             "played_character_id", "played_character_alive", "played_character_stress_points",
             "played_character_event_trait_membership", "played_character_gold", "played_character_prestige",
             "played_character_piety", "played_character_betrothed_id", "played_character_primary_spouse_id",
             "played_character_spouse_ids", "has_active_event", "active_event_instance_id", "active_event_option_count",
             "has_pending_character_interaction", "pending_character_interaction_id", "pending_sender_character_id",
             "pending_auto_accept_notification", "active_wars", "player_armies", "has_one_life_settlement",
             "one_life_settlement")
    def scalars(value):
        items = value.split(",")
        if len(items) != len(names): return None
        parsed = {}
        for name, item in zip(names, items):
            pair = item.split(":")
            if len(pair) != 2 or pair[0] != name or re.fullmatch(r"-?(0|[1-9][0-9]*)", pair[1]) is None:
                return None
            number = int(pair[1])
            if not -(2**63) <= number < 2**64: return None
            parsed[name] = number
        return parsed
    offset = 2
    differing = []
    if guard == "snapshot_not_equal":
        if len(parts) != 6 or not parts[2].startswith("differing_fields="): return None
        differing = parts[2][len("differing_fields="):].split(",")
        if (not differing or len(differing) != len(set(differing))
                or any(name not in differences for name in differing)
                or differing != sorted(differing, key=differences.index)):
            return None
        offset = 3
    elif len(parts) != 5:
        return None
    if not parts[offset].startswith("cached=") or not parts[offset+1].startswith("observed="):
        return None
    cached, observed = parts[offset][7:], parts[offset+1][9:]
    if guard == "previous_snapshot_missing":
        if cached != "unknown" or observed != "unknown": return None
    elif guard == "snapshot_read_failed":
        if scalars(cached) is None or observed != "unknown": return None
    else:
        before, after = scalars(cached), scalars(observed)
        if before is None or after is None: return None
        if guard != "snapshot_not_equal":
            field = {"not_paused":"paused", "map_not_ready":"map_ready",
                     "played_character_missing":"has_played_character",
                     "played_character_not_alive":"played_character_alive"}[guard]
            if before != after or after[field] != 0: return None
    return {"classification":"first_heir_native_pre_read_guard_rejected",
            "read_only_precondition":True, "business_submission":False,
            "native_step":"query-current-first-heir-relationship-v1-private",
            "native_stage":"first_heir_relationship_pre_read_guard",
            "pre_read_guard":guard, "snapshot_read_completed":guards[guard],
            "differing_fields":differing, "relationship_query_executor_started":False,
            "original_action_replay_allowed":False}
