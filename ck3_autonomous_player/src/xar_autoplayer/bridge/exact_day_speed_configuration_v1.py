"""Avoid a same-frame no-op speed command; leave the native day stop intact."""
from __future__ import annotations

from .driver import BridgeUnavailableError
from .version_identity import CK3_12004, require_exact_native_build


def _binding(snapshot):
    if type(snapshot) is not dict:
        return None
    actor = snapshot.get("played_character")
    diagnostic = snapshot.get("diagnostics")
    if (not isinstance(actor, dict) or actor.get("alive") is not True
            or not isinstance(diagnostic, dict) or diagnostic.get("connected") is not True
            or snapshot.get("backend_id") != "native-headless"
            or snapshot.get("source") != "injected-dll-named-pipe"
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True):
        return None
    values = (snapshot.get("revision"), snapshot.get("native_revision"),
              snapshot.get("date_raw"), actor.get("character_id"),
              snapshot.get("episode_character_id"), snapshot.get("local_player_id"),
              diagnostic.get("bridge_pid"), diagnostic.get("connection_generation"))
    if (any(type(value) is not int or value <= 0 for value in values)
            or values[3] != values[4]
            or snapshot.get("snapshot_id") != f"native:{values[1]}"
            or not isinstance(snapshot.get("episode_run_id"), str)
            or not snapshot["episode_run_id"]):
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
    return (*values, snapshot["snapshot_id"], snapshot["episode_run_id"], build)


def prepare_exact_day_speed_v1(driver, starting, *, speed, actions):
    """Use only a revalidated complete local frame; no stored/cross-call cache.

    A changed speed is a real boundary, never an instruction to set it back.
    Missing/foreign/stale bindings retain the original setter/rejection path.
    Native Arm must still validate its independently observed actual speed.
    """
    binding = _binding(starting)
    if (binding is not None and type(speed) is int and 1 <= speed <= 5
            and type(starting.get("speed")) is int and starting["speed"] == speed):
        fresh = driver.take_internal_semantic_snapshot()
        if (not isinstance(fresh, dict) or type(fresh.get("speed")) is not int
                or fresh["speed"] != speed):
            raise BridgeUnavailableError("exact-day clock observed a changed or unavailable speed; no resume")
        if _binding(fresh) == binding:
            return fresh
    speed_step = f"set-speed-{speed}"
    speed_result = driver._execute_composite_primitive(speed_step, starting)
    actions.append({"step": speed_step, "result": speed_result})
    current = driver._wait_for_life_advance_snapshot(
        driver.take_internal_semantic_snapshot(),
        lambda snapshot: snapshot.get("speed") == speed,
        timeout_seconds=driver.command_timeout_seconds,
    )
    if current.get("speed") != speed:
        raise BridgeUnavailableError("exact-day clock did not observe its speed")
    return current
