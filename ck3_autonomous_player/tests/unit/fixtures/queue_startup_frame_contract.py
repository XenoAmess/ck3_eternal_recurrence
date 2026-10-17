"""Reviewed actual queue.frame excerpt; test contract, not a deployed queue."""

def frame(value, *, semantic=False, expected_lifecycle=None):
    actor = value.get("played_character") if semantic else None
    actor_id = actor.get("character_id") if isinstance(actor, dict) else value.get("actor_character_id")
    alive = actor.get("alive") if isinstance(actor, dict) else value.get("actor_alive")
    if (value.get("paused") is not True or value.get("map_ready") is not True
            or alive is not True or type(actor_id) is not int or actor_id <= 0
            or type(value.get("date_raw")) is not int
            or type(value.get("revision")) is not int or value["revision"] < 0
            or not isinstance(value.get("snapshot_id"), str) or not value["snapshot_id"]
            or not isinstance(value.get("episode_run_id"), str) or not value["episode_run_id"]):
        raise ValueError("actual paused living map/date/episode frame is unavailable")
    if semantic:
        from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1
        if (expected_lifecycle is None or value.get("one_life_terminal") is True
                or normalize_succession_lifecycle_binding_v1(value.get("succession_lifecycle")) != expected_lifecycle):
            raise ValueError("terminal or nonordinary semantic frame; stop rather than continue")
    return {"snapshot_id": value["snapshot_id"], "revision": value["revision"],
            "native_revision": value.get("native_revision"), "date_raw": value["date_raw"],
            "actor_character_id": actor_id, "episode_run_id": value["episode_run_id"]}
