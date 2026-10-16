"""Durable independent cooldowns for six optional ordinary checks."""
from __future__ import annotations

import json
import os
from pathlib import Path
import uuid

DOMAINS = ("ransom", "council", "lifestyle", "construction", "crown", "feast")
RAW_PER_DAY = 24
COOLDOWN_RAW = 30 * RAW_PER_DAY
PATH_NAME = "optional-check-cadence-v1.json"


def _empty(episode: str) -> dict:
    return {"schema": "xar.optional-check-cadence.v1", "episode_run_id": episode,
            "domains": {name: {"consecutive_no_action": 0, "next_due_date_raw": None,
                               "last_check_frame": None, "last_actual_action_frame": None}
                        for name in DOMAINS}}


def _load(state_dir: Path, episode: str) -> dict:
    path = state_dir / PATH_NAME
    if not path.exists():
        return _empty(episode)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "xar.optional-check-cadence.v1":
        raise ValueError("optional check cadence state has unknown schema")
    if value.get("episode_run_id") != episode:
        return _empty(episode)
    rows = value.get("domains")
    if not isinstance(rows, dict) or set(rows) != set(DOMAINS):
        raise ValueError("optional check cadence domains are incomplete")
    for name in DOMAINS:
        row = rows[name]
        if (not isinstance(row, dict)
                or type(row.get("consecutive_no_action")) is not int
                or not 0 <= row["consecutive_no_action"] <= 2
                or (row.get("next_due_date_raw") is not None
                    and type(row["next_due_date_raw"]) is not int)):
            raise ValueError("optional check cadence domain is invalid: " + name)
    return value


def _write(state_dir: Path, value: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / PATH_NAME
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def frame(snapshot: dict) -> tuple[str, int, int] | None:
    episode = snapshot.get("episode_run_id")
    date_raw = snapshot.get("date_raw")
    revision = snapshot.get("native_revision")
    if (snapshot.get("paused") is not True or not isinstance(episode, str)
            or not episode or type(date_raw) is not int or date_raw < 0
            or type(revision) is not int or revision < 0):
        return None
    return episode, date_raw, revision


def deferred(state_dir: Path, domain: str, current: tuple[str, int, int]) -> dict | None:
    if domain not in DOMAINS:
        raise ValueError("unknown optional check domain")
    row = _load(state_dir, current[0])["domains"][domain]
    due = row["next_due_date_raw"]
    if due is None or current[1] >= due:
        return None
    technical = row.get("technical_defer")
    if isinstance(technical, dict):
        return {"status": "technical_read_unavailable_deferred",
                "consecutive_no_action": row["consecutive_no_action"],
                "next_due_date_raw": due, "technical_defer": dict(technical),
                "remaining_game_days": (due - current[1] + RAW_PER_DAY - 1) // RAW_PER_DAY}
    return {"status": "cooldown_after_three_no_action_checks",
            "consecutive_no_action": 0, "next_due_date_raw": due,
            "remaining_game_days": (due - current[1] + RAW_PER_DAY - 1) // RAW_PER_DAY}


def action_recorded(state_dir: Path, domain: str,
                    current: tuple[str, int, int]) -> bool:
    if domain not in DOMAINS:
        raise ValueError("unknown optional check domain")
    return _load(state_dir, current[0])["domains"][domain]["last_actual_action_frame"] == list(current[1:])


def requalify_lifestyle_frontier_once(
    state_dir: Path, current: tuple[str, int, int], *,
    native_catalogue: str,
) -> bool:
    """Invalidate only the old lifestyle negative result after a native upgrade.

    This does not count an action or a check.  Call only after the current
    bridge has advertised the specified native catalogue capability.
    """
    if not isinstance(native_catalogue, str) or not native_catalogue:
        raise ValueError("lifestyle catalogue capability is required")
    value = _load(state_dir, current[0])
    row = value["domains"]["lifestyle"]
    if row.get("native_catalogue") == native_catalogue:
        return False
    row.update(consecutive_no_action=0, next_due_date_raw=None,
               last_check_frame=None, native_catalogue=native_catalogue)
    row.pop("technical_defer", None)
    _write(state_dir, value)
    return True


def record(state_dir: Path, domain: str, current: tuple[str, int, int], *,
           actual_action: bool) -> dict:
    if domain not in DOMAINS:
        raise ValueError("unknown optional check domain")
    value = _load(state_dir, current[0])
    row = value["domains"][domain]
    marker = list(current[1:])
    if actual_action:
        if row["last_actual_action_frame"] == marker:
            return dict(row)
        row.pop("technical_defer", None)
        row.update(consecutive_no_action=0, next_due_date_raw=None,
                   last_actual_action_frame=marker)
    else:
        if row["last_check_frame"] == marker:
            return dict(row)
        due = row["next_due_date_raw"]
        if due is not None and current[1] < due:
            raise ValueError("optional check recorded inside its cooldown")
        row.pop("technical_defer", None)
        row["last_check_frame"] = marker
        row["next_due_date_raw"] = None
        misses = row["consecutive_no_action"] + 1
        if misses == 3:
            row["consecutive_no_action"] = 0
            row["next_due_date_raw"] = current[1] + COOLDOWN_RAW
        else:
            row["consecutive_no_action"] = misses
    _write(state_dir, value)
    return dict(row)


def defer_council_technical_read(state_dir: Path, current: tuple[str, int, int], *,
                               evidence_path: str) -> dict:
    """Delay one failed council read without counting an operation or no-op."""
    if not isinstance(evidence_path, str) or not evidence_path:
        raise ValueError("council technical defer requires captured evidence")
    value = _load(state_dir, current[0])
    row = value["domains"]["council"]
    marker = list(current[1:])
    previous = row.get("technical_defer")
    if (isinstance(previous, dict) and previous.get("frame") == marker
            and type(row.get("next_due_date_raw")) is int
            and row["next_due_date_raw"] > current[1]):
        return dict(row)
    due = row.get("next_due_date_raw")
    row["next_due_date_raw"] = max(current[1] + COOLDOWN_RAW,
                                   due if type(due) is int else current[1])
    # Service's ordinary result observer sees the attempted frame once; this
    # marker suppresses its no-op increment without changing either counter.
    row["last_check_frame"] = marker
    row["technical_defer"] = {"status": "read_unavailable", "frame": marker,
                              "evidence_path": evidence_path,
                              "business_submission": False,
                              "no_action_counter_incremented": False}
    _write(state_dir, value)
    return dict(row)
