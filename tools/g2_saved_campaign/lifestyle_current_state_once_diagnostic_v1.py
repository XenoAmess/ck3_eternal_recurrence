"""One explicit App-owned LIFE2 read; no new connection or gameplay submission."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import copy
import json
from pathlib import Path


TOOL_NAME = "ck3_query_player_lifestyle_current_state_once_diagnostic_v1"


def _frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    return {
        **{key: snapshot.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "paused", "map_ready",
        )},
        "player_character_id": actor.get("character_id") if isinstance(actor, Mapping) else None,
        "actor_alive": actor.get("alive") if isinstance(actor, Mapping) else None,
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None,
        "hello_pid": hello.get("pid") if isinstance(hello, Mapping) else None,
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None,
    }


def install_once_diag(
    server: object, driver: object, *, evidence_path: str | Path,
    expected_owner_frame: Mapping[str, object], machine_id: str,
):
    """The warm factory owns physical Game/birth/DLL qualification.

    It passes its actual ``create_server(driver, ...)`` argument here, never a
    Queue surrogate. This helper checks that owner's current paused frame and
    invokes its existing current-state reader exactly once. An attempted read
    is consumed even on failure, and the original method result is retained.
    """
    expected = copy.deepcopy(dict(expected_owner_frame))
    required = ("bridge_pid", "player_character_id", "date_raw", "min_native_revision")
    if (not isinstance(machine_id, str) or not machine_id
            or any(type(expected.get(key)) is not int or expected[key] <= 0 for key in required)
            or not isinstance(expected.get("episode_run_id"), str)
            or not expected["episode_run_id"].startswith(f"native-{expected['player_character_id']}-")):
        raise ValueError("one LIFE2 diagnostic requires the factory's exact owner/frame binding")
    target = Path(evidence_path)
    started = target.with_name(target.name + ".started.json")
    if target.exists() or started.exists():
        raise ValueError("one LIFE2 diagnostic path was already reserved")
    used = False

    @server.tool()
    def ck3_query_player_lifestyle_current_state_once_diagnostic_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        nonlocal used
        if used:
            raise RuntimeError("one LIFE2 diagnostic was already attempted; never retry")
        used = True
        record: dict[str, object] = {
            "schema": "xar.app-owned-lifestyle-current-state-once-diagnostic.v1",
            "machine_id": machine_id,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "expected_owner_frame": expected,
            "expected_revision": expected_revision,
            "method": "NativeDriver.query_player_lifestyle_current_state_private_v1",
            "gameplay_action_submitted": False,
            "raw_native_command_result": "not_observed; original Driver method return retained",
        }
        # Reserve before querying so a new App cannot silently retry this path.
        with started.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
        try:
            before = _frame(driver.take_internal_semantic_snapshot())
            record["before"] = before
            native = before.get("native_revision")
            if (type(expected_revision) is not int or expected_revision <= 0
                    or before.get("revision") != expected_revision
                    or type(native) is not int or native < expected["min_native_revision"]
                    or before.get("snapshot_id") != f"native:{native}"
                    or before.get("paused") is not True or before.get("map_ready") is not True
                    or before.get("actor_alive") is not True
                    or any(before.get(key) != expected[key] for key in (
                        "bridge_pid", "player_character_id", "date_raw", "episode_run_id"))
                    or before.get("hello_pid") != expected["bridge_pid"]
                    or getattr(driver, "_session_bridge_pid", None) != expected["bridge_pid"]
                    or getattr(driver, "allow_private_lifestyle_formal_trial", False) is not True):
                raise ValueError("one LIFE2 diagnostic current paused owner/frame did not bind")
            reader = getattr(driver, "query_player_lifestyle_current_state_private_v1", None)
            if not callable(reader):
                raise ValueError("existing LIFE2 current-state method is unavailable")
            record["query_attempted"] = True
            record["original_method_return"] = copy.deepcopy(
                reader(expected_revision=expected_revision)
            )
            after = _frame(driver.take_internal_semantic_snapshot())
            record["after"] = after
            record["same_frame"] = after == before
            record["status"] = "observed" if after == before else "frame_changed"
        except Exception as error:
            record["status"] = "diagnostic_failed"
            record["exception_type"] = type(error).__name__
            record["exception"] = str(error)
        record["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        with target.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
        return record

    return ck3_query_player_lifestyle_current_state_once_diagnostic_v1
