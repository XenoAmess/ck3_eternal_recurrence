"""Default-off speed-two, one-day watch of the published wartime roster.

Native29 observes these regular CUnits at the daily callback, then pauses.
This is neither a contact-free forecast nor a complete physical army scan.
Events and owner changes are SDK publication boundaries, not native intra-day
watches. Enabling this software candidate requires separate live admission.
"""

from dataclasses import dataclass

from .battle_reader_watch_v1 import CLOCK_CAPABILITIES
from .version_identity import CK3_12004, require_exact_native_build


SCOPE = "war_daily_watch_v1"
SPEED = 2
MAX_ARMIES = 64
STATE_CODES = {"regular": 1, "moving": 7, "retreating": 6, "sieging": 3}


def _positive(value):
    return type(value) is int and 0 < value <= 2**31 - 1


def _connection(snapshot):
    diagnostic = snapshot.get("diagnostics")
    if not isinstance(diagnostic, dict) or diagnostic.get("connected") is not True:
        return None
    hello = diagnostic.get("hello")
    if not isinstance(hello, dict) or hello.get("ck3_build_match") is not True:
        return None
    try:
        build = require_exact_native_build(
            hello.get("expected_ck3_version", hello.get("game_version")),
            hello.get("expected_ck3_sha256", hello.get("executable_sha256")))
    except ValueError:
        return None
    if build != CK3_12004:
        return None
    pair = (diagnostic.get("bridge_pid"), diagnostic.get("connection_generation"))
    return pair if all(_positive(value) for value in pair) else None


def _owner(snapshot):
    if not isinstance(snapshot, dict):
        return None
    actor = snapshot.get("played_character")
    connection = _connection(snapshot)
    episode = snapshot.get("episode_run_id")
    if (connection is None or not isinstance(actor, dict)
            or actor.get("alive") is not True or not _positive(actor.get("character_id"))
            or type(snapshot.get("episode_character_id")) is not int
            or snapshot["episode_character_id"] != actor["character_id"]
            or not isinstance(episode, str) or not episode):
        return None
    return (*connection, episode, actor["character_id"], snapshot.get("local_player_id"))


def _mandatory(snapshot):
    if snapshot.get("one_life_terminal") is not False or snapshot.get("one_life_terminal_reason") is not None:
        return "terminal"
    if snapshot.get("active_event") is not None:
        return "active_event"
    if snapshot.get("pending_character_interaction") is not None:
        return "pending_interaction"
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    if (not isinstance(hint, dict) or hint.get("status") != "absent"
            or hint.get("owner_verified") is not True):
        return "exclusive_modal_or_unknown"
    if snapshot.get("map_ready") is not True:
        return "map_unavailable"
    return None


def _roster(snapshot):
    """All published own/allied/enemy regular IDs, with no exclusions/cap trim."""
    players, wars = snapshot.get("player_armies"), snapshot.get("active_wars")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, dict) else None
    if not isinstance(players, list) or not players or not isinstance(wars, list) or not wars:
        return None
    rows, war_ids, side_ids = {}, [], {"allied": set(), "enemy": set()}

    def add(values, side, *, owned=False):
        if not isinstance(values, list):
            return False
        seen = set()
        for army in values:
            if not isinstance(army, dict):
                return False
            army_id = army.get("army_id")
            # Unknown, embarked/gathering, and active combat require their own
            # existing contracts. Retreat and siege are actual observed states.
            fingerprint = (army.get("owner_character_id"), army.get("current_province_id"),
                army.get("move_target_province_id"), army.get("in_combat"), army.get("retreating"))
            state = army.get("army_state")
            if (not _positive(army_id) or army_id in seen
                    or not _positive(fingerprint[0]) or not _positive(fingerprint[1])
                    or "move_target_province_id" not in army
                    or fingerprint[2] is not None and not _positive(fingerprint[2])
                    or fingerprint[3] is not False or type(fingerprint[4]) is not bool
                    or type(state) is not str or state not in STATE_CODES
                    or "army_state_code" in army and (type(army["army_state_code"]) is not int
                        or army["army_state_code"] != STATE_CODES[state])
                    or (state == "retreating") != fingerprint[4]
                    or type(army.get("controllable")) is not bool
                    or owned and (army["controllable"] is not True or fingerprint[0] != actor)
                    or army_id in rows and rows[army_id] != fingerprint):
                return False
            seen.add(army_id)
            rows[army_id] = fingerprint
            side_ids[side].add(army_id)
        return True

    if not add(players, "allied", owned=True):
        return None
    for war in wars:
        war_id = war.get("war_id") if isinstance(war, dict) else None
        if not _positive(war_id) or war_id in war_ids:
            return None
        war_ids.append(war_id)
        if not add(war.get("allied_armies"), "allied") or not add(war.get("enemy_armies"), "enemy"):
            return None
    if side_ids["allied"] & side_ids["enemy"] or not 0 < len(rows) <= MAX_ARMIES:
        return None
    return tuple(sorted(war_ids)), tuple(sorted(rows.items()))


@dataclass(frozen=True)
class WarDailyWatchV1:
    owner: tuple
    date_raw: int
    revision: int
    native_revision: int
    roster: tuple

    @property
    def watch_army_ids(self):
        return tuple(army_id for army_id, _ in self.roster[1])

    def same_connection(self, snapshot):
        return isinstance(snapshot, dict) and _connection(snapshot) == self.owner[:2]

    def same_owner(self, snapshot):
        return _owner(snapshot) == self.owner

    def boundary(self, snapshot):
        if not self.same_connection(snapshot):
            return "connection_changed"
        if not self.same_owner(snapshot):
            return "actor_or_episode_changed"
        if (type(snapshot.get("revision")) is not int or snapshot["revision"] < self.revision
                or type(snapshot.get("native_revision")) is not int
                or snapshot["native_revision"] < self.native_revision
                or type(snapshot.get("date_raw")) is not int
                or snapshot["date_raw"] < self.date_raw):
            return "frame_unknown"
        return _mandatory(snapshot)

    def ready_to_arm(self, snapshot):
        return (self.boundary(snapshot) is None and snapshot.get("paused") is True
                and snapshot.get("date_raw") == self.date_raw
                and type(snapshot.get("speed")) is int and snapshot["speed"] == SPEED
                and _roster(snapshot) == self.roster)


def select_war_daily_watch_v1(snapshot, *, enabled, exact_one_day, result_step,
                            proof_kind, bridge_capabilities, action_steps, assault_in_progress):
    if (enabled is not True or exact_one_day is not True
            or result_step != "life-advance-one-day" or proof_kind is not None
            or assault_in_progress is not False or not isinstance(snapshot, dict)
            or snapshot.get("paused") is not True or _mandatory(snapshot) is not None
            or not CLOCK_CAPABILITIES <= bridge_capabilities
            or "game.state.pending-character-interaction" not in bridge_capabilities
            or not {"set-speed-2", "pause-map", "resume-map"} <= action_steps):
        return None
    owner, roster = _owner(snapshot), _roster(snapshot)
    if (owner is None or roster is None
            or any(not _positive(snapshot.get(key)) for key in ("date_raw", "revision", "native_revision"))
            or snapshot.get("snapshot_id") != f"native:{snapshot['native_revision']}"):
        return None
    return WarDailyWatchV1(owner, snapshot["date_raw"], snapshot["revision"],
                           snapshot["native_revision"], roster)


def unresolved_history_v1(rows):
    """A restored failure receipt also prohibits automatic candidate replay."""
    for row in rows:
        value = row.get("result") if isinstance(row, dict) else None
        if (isinstance(value, dict) and value.get("schema") == "xar.war-daily-watch-unresolved.v1"
                and value.get("never_replay") is True):
            return True
    return False


def resume_once_v1(driver, starting, context, actions):
    """One request only. An unknown ACK is never an authorization to replay."""
    from .native_driver import BridgeUnavailableError
    current = driver.take_internal_semantic_snapshot()
    if not context.ready_to_arm(current):
        raise BridgeUnavailableError("war daily watch owner/roster changed before resume")
    revision = current["revision"]
    result = driver._execute_primitive_step("resume-map", expected_revision=None,
        internal_semantic_snapshot=True)
    actions.append({"step": "resume-map", "result": result})
    current = driver.take_internal_semantic_snapshot()
    # Date alone is not a stop predicate: the Native147 race can publish the
    # target date while the post-daily native pause is still pending.
    def stopped_or_early_boundary(frame):
        boundary = context.boundary(frame)
        if boundary not in (None, "active_event", "pending_interaction", "exclusive_modal_or_unknown"):
            return True
        if (boundary is not None and type(frame.get("date_raw")) is int
                and frame["date_raw"] < context.date_raw + 24):
            return True
        return (frame.get("paused") is True and type(frame.get("revision")) is int
                and frame["revision"] > revision)
    return driver._wait_for_life_advance_snapshot(current, stopped_or_early_boundary,
        timeout_seconds=driver.life_advance_timeout_seconds)
