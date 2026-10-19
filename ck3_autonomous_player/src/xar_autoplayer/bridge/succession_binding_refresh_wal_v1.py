"""Narrow, caller-owned proof for an unchanged estate's source-frame refresh.

No observations or writes. The original WAL owner holds its write/state locks
when consuming a proof. Missing provenance is ineligible, never inferred.
"""
from dataclasses import dataclass
import json

from .succession_transition_contract import normalize_succession_expectation_v1
from .version_identity import CK3_12004, require_exact_native_build

_REFRESH = frozenset(("snapshot_id", "revision", "native_revision", "date_raw"))
_BINDING = _REFRESH | {"episode_run_id", "episode_character_id"}
_OWNER = ("actor", "episode_actor", "episode", "local_player", "pid", "connection", "pipe", "build")


def _json(value):
    def valid(v):
        if type(v) in (str, int, float, bool, type(None)):
            return True
        if type(v) is list:
            return all(valid(x) for x in v)
        return type(v) is dict and all(type(k) is str and valid(x) for k, x in v.items())
    if not valid(value):
        raise ValueError("noncanonical JSON type")
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _positive(value):
    return type(value) is int and 0 < value <= 2**63 - 1


def _build(hello):
    if type(hello) is not dict or hello.get("ck3_build_match") is not True:
        return None
    try:
        build = require_exact_native_build(
            hello.get("expected_ck3_version", hello.get("game_version")),
            hello.get("expected_ck3_sha256", hello.get("executable_sha256")))
    except ValueError:
        return None
    return (build.game_version, build.executable_sha256) if build == CK3_12004 else None


def _frame(snapshot):
    if (type(snapshot) is not dict or snapshot.get("backend_id") != "native-headless"
            or snapshot.get("source") != "injected-dll-named-pipe"
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return None
    actor, d = snapshot.get("played_character"), snapshot.get("diagnostics")
    if (type(actor) is not dict or actor.get("alive") is not True
            or type(d) is not dict or d.get("connected") is not True):
        return None
    out = dict(actor=actor.get("character_id"), episode_actor=snapshot.get("episode_character_id"),
               episode=snapshot.get("episode_run_id"), local_player=snapshot.get("local_player_id"),
               pid=d.get("bridge_pid"), connection=d.get("connection_generation"), pipe=d.get("pipe_name"),
               build=_build(d.get("hello")),
               snapshot_id=snapshot.get("snapshot_id"), revision=snapshot.get("revision"),
               native_revision=snapshot.get("native_revision"), date_raw=snapshot.get("date_raw"))
    if (not all(_positive(out[k]) for k in ("actor", "episode_actor", "local_player", "pid", "connection",
                                           "revision", "native_revision"))
            or out["actor"] != out["episode_actor"] or type(out["episode"]) is not str or not out["episode"]
            or type(out["pipe"]) is not str or not out["pipe"]
            or out["build"] is None or type(out["date_raw"]) is not int or out["date_raw"] < 0
            or out["snapshot_id"] != "native:" + str(out["native_revision"])):
        return None
    return out


def _publication_matches(driver, frame):
    """Read only existing protocol-cache scalars under its original condition."""
    state = driver.state
    with state._condition:
        native, hello = state._semantic_snapshot, state._hello
        if type(native) is not dict or type(hello) is not dict:
            return False
        actor = native.get("played_character")
        return (state._connected is True and type(actor) is dict and actor.get("alive") is True
                and all(_positive(v) for v in (state._public_revision, native.get("revision"),
                        state._connection_generation, hello.get("pid"), actor.get("character_id"),
                        native.get("local_player_id"), driver._session_bridge_pid, driver._episode_character_id))
                and type(native.get("date_raw")) is int and type(native.get("snapshot_id")) is str
                and driver.pipe_name == state.pipe_name == frame["pipe"]
                and state._public_revision == frame["revision"]
                and native.get("revision") == frame["native_revision"]
                and native.get("snapshot_id") == frame["snapshot_id"]
                and native.get("date_raw") == frame["date_raw"] and native.get("paused") is True
                and native.get("map_ready") is True and native.get("active_event") is None
                and native.get("pending_character_interaction") is None
                and actor.get("character_id") == frame["actor"]
                and native.get("local_player_id") == frame["local_player"]
                and state._connection_generation == frame["connection"]
                and hello.get("pid") == frame["pid"] and _build(hello) == frame["build"]
                and driver._session_bridge_pid == frame["pid"]
                and driver._episode_character_id == frame["episode_actor"]
                and driver._episode_run_id == frame["episode"])


def _expectation(fields):
    value = fields["succession_expectation"]
    if _json(normalize_succession_expectation_v1(value)) != _json(value):
        raise ValueError("expectation is not canonical")
    if set(value["binding"]) != _BINDING:
        raise ValueError("unknown binding shape")
    return value


def _business(fields):
    value = _expectation(fields)
    # Only these four leaves are excluded; every other key/type/order survives.
    binding = {k: v for k, v in value["binding"].items() if k not in _REFRESH}
    return _json({**fields, "succession_expectation": {**value, "binding": binding}})


@dataclass(frozen=True)
class _Anchor:
    instance: int
    frame: dict
    fields: bytes
    generation: int
    committed: int


@dataclass
class _Proof:
    instance: int
    anchor: _Anchor
    before: bytes
    after: bytes
    frame: dict
    generation: int
    used: bool = False


def begin_refresh(driver, snapshot, before, after):
    """Called inside the original state lock; rejection leaves full persistence."""
    try:
        anchor = getattr(driver, "_succession_binding_wal_anchor_v1", None)
        frame = _frame(snapshot)
        if (type(anchor) is not _Anchor or anchor.instance != id(driver) or frame is None
                or not all(anchor.frame[k] == frame[k] for k in _OWNER)
                or anchor.generation != driver._driver_state_wal_barrier_generation
                or anchor.committed > driver._driver_state_wal_committed_rows
                or anchor.fields != _json(before) or _business(before) != _business(after)
                or not _publication_matches(driver, frame)):
            return None
        old, new = _expectation(before)["binding"], _expectation(after)["binding"]
        if (old["snapshot_id"] != "native:" + str(old["native_revision"])
                or any(new[k] < old[k] for k in ("revision", "native_revision", "date_raw"))
                or not any(new[k] != old[k] for k in _REFRESH)
                or any(new[k] != frame[k] for k in _REFRESH)
                or new["episode_run_id"] != frame["episode"]
                or new["episode_character_id"] != frame["actor"]):
            return None
        return _Proof(id(driver), anchor, _json(before), _json(after), frame,
                      driver._driver_state_wal_barrier_generation)
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def consume_refresh(driver, proof, prior, fields, rows, readonly):
    """One-shot alternate to scalar equality; caller holds write and state locks."""
    if type(proof) is not _Proof or proof.used:
        return False
    proof.used = True
    try:
        return (proof.instance == id(driver)
                and getattr(driver, "_succession_binding_wal_anchor_v1", None) is proof.anchor
                and proof.generation == driver._driver_state_wal_barrier_generation
                and driver._driver_state_dirty is False
                and driver._driver_state_wal_barrier_required is False
                and proof.before == _json(prior) and proof.after == _json(fields)
                and proof.after == _json(driver._driver_state_wal_scalar_fields_locked_v1())
                and _business(prior) == _business(fields)
                and bool(rows) and all(type(r) is dict and r.get("ok") is True
                                       and readonly(r.get("command")) for r in rows)
                and _publication_matches(driver, proof.frame))
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def finish_refresh(driver, snapshot, fields, generation):
    """Establish a new anchor only after this retain's successful original write."""
    driver._succession_binding_wal_anchor_v1 = None
    try:
        frame = _frame(snapshot)
        if (not getattr(driver, "allow_driver_state_wal_v1", False) or driver.state_dir is None
                or frame is None or driver._driver_state_dirty or driver._driver_state_error is not None
                or driver._succession_reconciliation is not None
                or driver._driver_state_wal_barrier_required
                or driver._driver_state_wal_barrier_generation not in (generation, generation + 1)
                or type(driver._driver_state_wal_document) is not dict
                or driver._driver_state_wal_committed_rows != len(driver._command_history)
                or _json(driver._driver_state_wal_scalar_fields_locked_v1()) != _json(fields)
                or not _publication_matches(driver, frame)):
            return
        _expectation(fields)
        driver._succession_binding_wal_anchor_v1 = _Anchor(
            id(driver), frame, _json(fields), driver._driver_state_wal_barrier_generation,
            driver._driver_state_wal_committed_rows)
    except (AttributeError, KeyError, TypeError, ValueError):
        return
