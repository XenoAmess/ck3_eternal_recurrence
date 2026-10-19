"""Storage qualification for complete native campaign deadlines, not policy.

The two frames already exist in the life-advance call. No observation, cache,
serialization, file access, or gameplay operation is performed here.
"""
from .version_identity import CK3_12004, require_exact_native_build

OWNER_SCHEMA = "xar.ck3.driver-wal-multiday-owner/v1"
OWNER_KEY = "driver_state_wal_multiday_owner_v1"
_OWNER_KEYS = (
    "actor_id", "episode_character_id", "episode_run_id", "local_player_id",
    "bridge_pid", "connection_generation", "game_version", "executable_sha256",
)
_ENDPOINT_KEYS = frozenset((*_OWNER_KEYS, "revision", "native_revision",
                            "snapshot_id", "date_raw", "alive", "paused", "map_ready"))


def _positive(value):
    return type(value) is int and 0 < value <= 2**63 - 1


def _endpoint_from_frame(frame):
    if (type(frame) is not dict or frame.get("backend_id") != "native-headless"
            or frame.get("source") != "injected-dll-named-pipe"
            or frame.get("paused") is not True or frame.get("map_ready") is not True):
        return None
    actor, diagnostic = frame.get("played_character"), frame.get("diagnostics")
    if (type(actor) is not dict or actor.get("alive") is not True
            or type(diagnostic) is not dict or diagnostic.get("connected") is not True):
        return None
    hello = diagnostic.get("hello")
    if type(hello) is not dict or hello.get("ck3_build_match") is not True:
        return None
    try:
        build = require_exact_native_build(
            hello.get("expected_ck3_version", hello.get("game_version")),
            hello.get("expected_ck3_sha256", hello.get("executable_sha256")))
    except ValueError:
        return None
    if build != CK3_12004:
        return None
    result = {
        "actor_id": actor.get("character_id"),
        "episode_character_id": frame.get("episode_character_id"),
        "episode_run_id": frame.get("episode_run_id"),
        "local_player_id": frame.get("local_player_id"),
        "bridge_pid": diagnostic.get("bridge_pid"),
        "connection_generation": diagnostic.get("connection_generation"),
        "game_version": build.game_version,
        "executable_sha256": build.executable_sha256,
        "revision": frame.get("revision"), "native_revision": frame.get("native_revision"),
        "snapshot_id": frame.get("snapshot_id"), "date_raw": frame.get("date_raw"),
        "alive": True, "paused": True, "map_ready": True,
    }
    return result if _valid_endpoint(result) else None


def _valid_endpoint(value):
    return bool(type(value) is dict and set(value) == _ENDPOINT_KEYS
        and all(_positive(value.get(key)) for key in (
            "actor_id", "episode_character_id", "local_player_id", "bridge_pid",
            "connection_generation", "revision", "native_revision", "date_raw"))
        and value["actor_id"] == value["episode_character_id"]
        and type(value["episode_run_id"]) is str and bool(value["episode_run_id"])
        and value["snapshot_id"] == f"native:{value['native_revision']}"
        and value["game_version"] == CK3_12004.game_version
        and value["executable_sha256"] == CK3_12004.executable_sha256
        and value["alive"] is True and value["paused"] is True and value["map_ready"] is True)


def _same_owner(before, after):
    return all(before[key] == after[key] for key in _OWNER_KEYS)


def owner_proof_v1(starting, current):
    """Capture only typed scalar provenance from existing starting/current frames."""
    before, after = _endpoint_from_frame(starting), _endpoint_from_frame(current)
    if (before is None or after is None or not _same_owner(before, after)
            or after["date_raw"] <= before["date_raw"]
            or after["revision"] < before["revision"]
            or after["native_revision"] <= before["native_revision"]):
        return None
    return {"schema": OWNER_SCHEMA, "source": "existing_native_timeline_frames",
            "starting": before, "ending": after}


def _int_equal(value, expected):
    return type(value) is int and value == expected


def eligible_bounded_multiday_delta_v1(step, result, *, expected_owner):
    """Do not authorize gameplay, retries, early stops, or a changed owner.

    The caller still validates every uncommitted row, the unchanged history
    prefix, all scalar state, base identity, chain, byte caps and barriers.
    This predicate only admits one fully verified campaign-date-clock row.
    """
    if step != "life-advance" or type(result) is not dict or result.get("step") != step:
        return False
    start, end, days = (result.get("starting_date_raw"), result.get("ending_date_raw"),
                        result.get("elapsed_days"))
    if (not _positive(start) or not _positive(end) or type(days) is not int
            or not 1 <= days <= 45 or end != start + 24 * days
            or not _int_equal(result.get("requested_horizon_days"), days)
            or result.get("paused") is not True
            or result.get("progress_status") != "postcondition"
            or result.get("final_screen") != "map_hud"
            or result.get("active_event") is not None
            or result.get("pending_character_interaction") is not None
            or result.get("event_resolution") is not None
            or result.get("ordinary_events") not in (None, [])):
        return False
    speed = result.get("timeline_speed")
    if type(speed) is not int or not 1 <= speed <= 5:
        return False
    proof = result.get(OWNER_KEY)
    if (type(proof) is not dict or set(proof) != {"schema", "source", "starting", "ending"}
            or proof.get("schema") != OWNER_SCHEMA
            or proof.get("source") != "existing_native_timeline_frames"):
        return False
    before, after = proof.get("starting"), proof.get("ending")
    if (not _valid_endpoint(before) or not _valid_endpoint(after)
            or not _same_owner(before, after)
            or before["date_raw"] != start or after["date_raw"] != end
            or after["revision"] < before["revision"]
            or after["native_revision"] <= before["native_revision"]
            or type(expected_owner) is not tuple or len(expected_owner) != 3
            or not _positive(expected_owner[0]) or not _positive(expected_owner[1])
            or type(expected_owner[2]) is not str or not expected_owner[2]
            or expected_owner != (after["bridge_pid"], after["episode_character_id"],
                                   after["episode_run_id"])):
        return False
    deadline = result.get("campaign_deadline_v1")
    clock = result.get("campaign_deadline_native_clock_v1")
    if (type(deadline) is not dict or not _int_equal(deadline.get("target_date_raw"), end)
            or type(clock) is not dict
            or clock.get("schema") != "xar.ck3.campaign-native-date-clock/v1"
            or clock.get("scope") != "campaign_date_deadline"
            or clock.get("exact_one_day_qualification_claimed") is not False
            or "early_boundary_cancel" not in clock or clock["early_boundary_cancel"] is not None
            or not _int_equal(clock.get("starting_date_raw"), start)
            or not _int_equal(clock.get("target_date_raw"), end)):
        return False
    armed, stopped = clock.get("armed"), clock.get("stopped")
    if (type(armed) is not dict or type(stopped) is not dict
            or not _positive(armed.get("generation"))
            or armed.get("state") != "armed" or stopped.get("state") != "triggered"
            or not _int_equal(stopped.get("generation"), armed["generation"])):
        return False
    for status in (armed, stopped):
        if (status.get("mode") != "terminal_or_sentinel"
                or not _int_equal(status.get("speed"), speed)
                or not _int_equal(status.get("starting_date_raw"), start)
                or not _int_equal(status.get("target_date_raw"), end)
                or not _int_equal(status.get("army_count"), 0)
                or not _int_equal(status.get("combat_count"), 0)
                or status.get("terminal_observed") is not False
                or status.get("abnormal") is not False):
            return False
    return bool(_int_equal(armed.get("completed_daily_ticks"), 0)
        and _int_equal(armed.get("last_observed_date_raw"), start)
        and _int_equal(stopped.get("last_observed_date_raw"), end)
        and _int_equal(stopped.get("trigger_date_raw"), end)
        and _int_equal(stopped.get("completed_daily_ticks"), days)
        and _int_equal(stopped.get("signed_date_delta_from_target_raw"), 0)
        and _int_equal(stopped.get("overshoot_days"), 0)
        and _int_equal(stopped.get("intermediate_pause_count"), 0)
        and stopped.get("trigger_reasons") == ["date_deadline"]
        and _int_equal(stopped.get("trigger_flags"), 1)
        and stopped.get("pause_wrapper_called") is True
        and stopped.get("pause_observed") is True)
