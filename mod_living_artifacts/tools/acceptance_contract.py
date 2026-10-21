"""Closed data boundaries for the staged Living Artifacts live case."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Literal, Protocol, TypeAlias, TypedDict, runtime_checkable

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]
Object: TypeAlias = dict[str, Json]
Status: TypeAlias = Literal["NOT_RUN", "PASS", "FAIL", "BLOCKED"]
SAFE = 2**53 - 1
RESULT_NAME = "living-artifacts-core-result.json"
OBSERVATION_PREFIX = "XALW_SAMPLE_V1;"
INPUT_PREFIX = "XALW_INPUT_V1;"


class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str


class CheckResult(TypedDict):
    case_id: str
    status: Status
    evidence_scope: Literal["fixture_live"]
    reason: str | None
    evidence: list[Pin]
    observed: Object


@runtime_checkable
class CasePort(Protocol):
    output: Path
    state: Path
    manifest: object
    frozen: object
    operator_reviewer: str

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object: ...
    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None,
                     reserve: int = 90) -> object: ...
    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> object: ...
    def guard(self, reserve: int = 90) -> object: ...
    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes: ...
    def checkpoint(self, name: str, value: object) -> object: ...
    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object: ...


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError(f"{label}: string keys required")
        result[key] = item
    return result


def field(value: object, key: str) -> object:
    row = mapping(value, "container")
    require(key in row, f"Missing required field: {key}")
    return row[key]


def integer(value: object, label: str, low: int = 0, high: int = SAFE) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label}: strict bounded integer required; bool/float rejected")
    return value


def text(value: object, label: str) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise ValueError(f"{label}: nonempty string required")
    return value


def array(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label}: JSON array required")
    return list(value)


def decimal_id(value: object, label: str, *, allow_zero: bool = False) -> str:
    result = text(value, label)
    require(re.fullmatch(r"0|[1-9][0-9]*", result) is not None, f"{label}: canonical decimal string required")
    require((0 if allow_zero else 1) <= int(result) <= 2**64 - 1, f"{label}: ID range exceeded")
    return result


def native_id(value: object, label: str, *, allow_zero: bool = False) -> int:
    return integer(value, label, 0 if allow_zero else 1, 2**32 - 2)


def exact_getter_integer(value: str, label: str, low: int = 0, high: int = SAFE) -> int:
    # The observer requests all five fixed-point decimal places. Grouped digits
    # are accepted only in canonical groups; nonzero fractions are rejected.
    require(re.fullmatch(r"-?(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)\.[0-9]{5}", value) is not None,
            f"{label}: exact five-place getter value required")
    try:
        number = Decimal(value.replace(",", ""))
    except InvalidOperation as error:
        raise ValueError(f"{label}: invalid getter number") from error
    require(number.is_finite() and number == number.to_integral_value(), f"{label}: noninteger getter rejected")
    result = int(number)
    require(low <= result <= high, f"{label}: getter range exceeded")
    return result


def json_value(value: object) -> Json:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is int:
        require(-SAFE <= value <= SAFE, "JSON integer exceeds safe range; preserve a canonical decimal string")
        return value
    if type(value) is float:
        require(math.isfinite(value), "Nonfinite JSON value rejected")
        return value
    if type(value) is list or type(value) is tuple:
        return [json_value(item) for item in value]
    row = mapping(value, "JSON")
    return {key: json_value(item) for key, item in row.items()}


def object_value(value: object) -> Object:
    return {key: json_value(item) for key, item in mapping(value, "JSON object").items()}


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read(path: Path) -> Object:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique)
    return object_value(value)


def pin(path: Path) -> Pin:
    path = path.resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_once(path: Path, value: object) -> Pin:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(json_value(value), stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return pin(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Frame:
    revision: int
    native_revision: int
    date_raw: int
    player_id: int
    pid: int
    generation_decimal: str

    @classmethod
    def parse(cls, value: object, *, run_id: str, machine_id: str, manifest: object) -> Frame:
        row = mapping(value, "native frame")
        for key, expected in {"paused": True, "map_ready": True, "source": "injected-dll-named-pipe",
                              "backend_id": "native-headless", "episode_projection": "native_campaign"}.items():
            require(type(row.get(key)) is type(expected) and row[key] == expected, f"Native frame guard: {key}")
        require(field(manifest, "machine_id") == machine_id, "Selected runtime belongs to another machine")
        actor = field(row, "played_character")
        require(field(actor, "alive") is True and field(actor, "source") == "native", "Actual alive native actor required")
        diagnostics = field(row, "diagnostics")
        hello = field(diagnostics, "hello")
        game = field(manifest, "game")
        binding = field(row, "managed_campaign_run_binding")
        require(field(binding, "run_id") == run_id and field(binding, "bridge_pipe") == field(diagnostics, "pipe_name"),
                "Actual public run/pipe binding differs")
        pid = integer(field(diagnostics, "bridge_pid"), "native PID", 1, 2**32 - 1)
        generation = integer(field(diagnostics, "connection_generation"), "native generation", 1)
        require(integer(field(hello, "pid"), "hello PID", 1, 2**32 - 1) == pid and
                integer(field(hello, "connection_generation"), "hello generation", 1) == generation and
                field(hello, "ck3_build_match") is True and field(hello, "expected_ck3_version") == field(game, "version") and
                text(field(hello, "expected_ck3_sha256"), "EXE SHA").lower() == text(field(game, "exe_sha256"), "selected EXE SHA").lower(),
                "Native hello differs from selected exact runtime")
        return cls(integer(field(row, "revision"), "public revision", 1), integer(field(row, "native_revision"), "native revision", 1),
                   integer(field(row, "date_raw"), "native date"), native_id(field(actor, "character_id"), "native actor"), pid, str(generation))


@dataclass(frozen=True)
class ArtifactSample:
    sequence: int
    owner_id: str
    artifact_id: str
    equipped: bool
    game_day: int
    month: int
    level: int
    xp: int
    pending: int
    growth_sequence: int
    last_month: int
    resonance: int
    durability_decimal: str

    @classmethod
    def parse(cls, line: str) -> ArtifactSample:
        require(OBSERVATION_PREFIX in line, "Actual observer prefix missing")
        body = line[line.index(OBSERVATION_PREFIX) + len(OBSERVATION_PREFIX):].strip()
        pairs = body.split(";")
        values: dict[str, str] = {}
        for pair in pairs:
            key, separator, value = pair.partition("=")
            require(bool(separator) and key not in values, "Malformed or duplicate observer field")
            values[key] = value
        require(set(values) == {"seq", "owner", "artifact", "equipped", "game_day", "month", "level", "xp", "pending", "growth", "last_month", "resonance", "durability"},
                "Observer field contract differs")
        require(values["equipped"] in ("0", "1"), "Actual equipped predicate is not binary")
        durability = values["durability"]
        require(re.fullmatch(r"-?[0-9]+\.[0-9]{5}", durability) is not None, "Durability getter must preserve five decimals")
        return cls(exact_getter_integer(values["seq"], "sequence"), decimal_id(values["owner"], "owner"),
                   decimal_id(values["artifact"], "artifact", allow_zero=True), values["equipped"] == "1",
                   exact_getter_integer(values["game_day"], "game day"), exact_getter_integer(values["month"], "month"),
                   exact_getter_integer(values["level"], "level", 1), exact_getter_integer(values["xp"], "xp"),
                   exact_getter_integer(values["pending"], "pending"), exact_getter_integer(values["growth"], "growth"),
                   exact_getter_integer(values["last_month"], "last month"), exact_getter_integer(values["resonance"], "resonance", 0, 100), durability)

    def to_json(self) -> Object:
        return {"sequence": self.sequence, "owner_id": self.owner_id, "artifact_id": self.artifact_id, "equipped": self.equipped,
                "game_day": self.game_day, "month": self.month, "level": self.level, "xp": self.xp, "pending": self.pending,
                "growth_sequence": self.growth_sequence, "last_month": self.last_month, "resonance": self.resonance,
                "durability_decimal": self.durability_decimal}
