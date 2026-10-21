"""Pure background foreground policy; no window, file or game operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias
from uuid import UUID

JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = dict[str, JsonValue]


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _integer(value: object, minimum: int = 0, maximum: int = (1 << 53)-1) -> int:
    if type(value) is not int:
        raise ValueError("exact integer")
    _need(minimum <= value <= maximum, "integer range")
    return value


def _text(value: object) -> str:
    if type(value) is not str:
        raise ValueError("exact text")
    _need(0 < len(value) <= 32768, "bounded text")
    return value


def _record(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or not isinstance(value, dict):
        raise ValueError("object")
    row: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str or not isinstance(key, str):
            raise ValueError("text key")
        row[key] = item
    _need(set(row) == fields, "exact foreground fields")
    return row


def _rows(value: object) -> list[object]:
    if type(value) is not list or not isinstance(value, list):
        raise ValueError("array")
    return list(value)


LaunchForegroundClassV1: TypeAlias = Literal[
 "FOREGROUND_UNCHANGED", "NON_GAME_USER_FOREGROUND", "OWNED_GAME_FOREGROUND",
 "OWNED_AUXILIARY_FOREGROUND", "UNKNOWN_FOREGROUND_OWNER", "USER_DESKTOP_CHANGED"]

@dataclass(frozen=True, slots=True)
class LaunchForegroundObservationV1:
 foreground_before: int
 foreground_after: int
 foreground_after_pid: int | None
 desktop_before: str
 desktop_after: str
 game_pid: int
 owned_auxiliary_pids: tuple[int, ...]

 def __post_init__(self) -> None:
  _integer(self.foreground_before)
  _integer(self.foreground_after)
  _integer(self.game_pid, 1, 2**32-1)
  if self.foreground_after_pid is not None:
   _integer(self.foreground_after_pid, 1, 2**32-1)
   _need(self.foreground_after > 0, "an owned PID requires an actual window handle")
  for value in (self.desktop_before, self.desktop_after):
   _need(str(UUID(_text(value))) == value, "canonical observed desktop UUID")
  _need(type(self.owned_auxiliary_pids) is tuple and len(self.owned_auxiliary_pids) <= 8,
   "bounded owned auxiliary process tuple")
  for pid in self.owned_auxiliary_pids:
   _integer(pid, 1, 2**32-1)
  _need(len(set(self.owned_auxiliary_pids)) == len(self.owned_auxiliary_pids)
   and self.game_pid not in self.owned_auxiliary_pids, "distinct actual owned auxiliary processes")

 @property
 def classification(self) -> LaunchForegroundClassV1:
  if self.desktop_after != self.desktop_before:
   return "USER_DESKTOP_CHANGED"
  if self.foreground_after_pid == self.game_pid:
   return "OWNED_GAME_FOREGROUND"
  if self.foreground_after_pid in self.owned_auxiliary_pids:
   return "OWNED_AUXILIARY_FOREGROUND"
  if self.foreground_after_pid is None:
   return "UNKNOWN_FOREGROUND_OWNER"
  if self.foreground_unchanged:
   return "FOREGROUND_UNCHANGED"
  return "NON_GAME_USER_FOREGROUND"

 @property
 def foreground_unchanged(self) -> bool:
  return self.foreground_before == self.foreground_after

 @property
 def permitted(self) -> bool:
  return self.classification in ("FOREGROUND_UNCHANGED", "NON_GAME_USER_FOREGROUND")

 def to_wire(self) -> JsonObject:
  return {"foreground_before": self.foreground_before, "foreground_after": self.foreground_after,
   "foreground_after_pid": self.foreground_after_pid, "desktop_before": self.desktop_before,
   "desktop_after": self.desktop_after, "game_pid": self.game_pid,
   "owned_auxiliary_pids": list(self.owned_auxiliary_pids),
   "classification": self.classification, "foreground_unchanged": self.foreground_unchanged}

def classify_current_saved_launch_foreground_v1(value: object) -> LaunchForegroundObservationV1:
 """Classify an observed window owner; never activate, restore or move a window."""
 row = _record(value, {"foreground_before", "foreground_after", "foreground_after_pid",
  "desktop_before", "desktop_after", "game_pid", "owned_auxiliary_pids"})
 pid = row["foreground_after_pid"]
 return LaunchForegroundObservationV1(_integer(row["foreground_before"]), _integer(row["foreground_after"]),
  None if pid is None else _integer(pid, 1, 2**32-1), _text(row["desktop_before"]), _text(row["desktop_after"]),
  _integer(row["game_pid"], 1, 2**32-1), tuple(_integer(item, 1, 2**32-1) for item in _rows(row["owned_auxiliary_pids"])))

def parse_current_saved_launch_foreground_v1(value: object) -> LaunchForegroundObservationV1:
 row = _record(value, {"foreground_before", "foreground_after", "foreground_after_pid",
  "desktop_before", "desktop_after", "game_pid", "owned_auxiliary_pids", "classification", "foreground_unchanged"})
 result = classify_current_saved_launch_foreground_v1({key: item for key, item in row.items()
  if key not in ("classification", "foreground_unchanged")})
 _need(_text(row["classification"]) == result.classification
  and row["foreground_unchanged"] is result.foreground_unchanged, "derived foreground facts must be authentic")
 return result


