"""Bounded read-only projection of an actual, successfully melted CK3 checkpoint.

This reads saved state. Current process/owner/equipment authority remains native.
The token/block grammar follows the repository's bounded_save_parser; only the
selected character and artifact records are parsed, never the whole save AST.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Iterator, TypeAlias

from acceptance_contract import Object, decimal_id, native_id, pin, require
from living_artifacts_core import render_fixture_localization
from living_artifacts_model import LIVING_NAME_PREFIX

Value: TypeAlias = str | tuple["Entry", ...]
TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}="]+')


@dataclass(frozen=True)
class Entry:
    key: str | None
    value: Value


def parse_block(body: str) -> tuple[Entry, ...]:
    tokens: list[str] = []
    ending = 0
    for match in TOKEN.finditer(body):
        require(not body[ending:match.start()].strip(), "Unparsed/unterminated quoted save token")
        tokens.append(match.group(0))
        ending = match.end()
    require(not body[ending:].strip(), "Unparsed trailing save token")
    position = 0

    def value() -> Value:
        nonlocal position
        require(position < len(tokens), "Truncated selected save block")
        token = tokens[position]
        position += 1
        if token != "{":
            require(token not in ("}", "="), "Unexpected selected save block token")
            return token
        entries: list[Entry] = []
        while position < len(tokens) and tokens[position] != "}":
            key: str | None = None
            if position + 1 < len(tokens) and tokens[position + 1] == "=":
                key = tokens[position]
                position += 2
            entries.append(Entry(key, value()))
        require(position < len(tokens), "Unterminated selected save block")
        position += 1
        return tuple(entries)

    parsed = value()
    require(position == len(tokens) and isinstance(parsed, tuple), "Selected save block was not consumed exactly")
    if not isinstance(parsed, tuple):
        raise ValueError("Selected save block must be structured")
    return parsed


def one(entries: tuple[Entry, ...], key: str, *, required: bool = True) -> Value | None:
    values = [entry.value for entry in entries if entry.key == key]
    require(len(values) <= 1 and (not required or len(values) == 1), "Nonunique/missing saved field: " + key)
    return values[0] if values else None


def structured(value: Value | None, label: str) -> tuple[Entry, ...]:
    require(isinstance(value, tuple), "Saved structured block required: " + label)
    if not isinstance(value, tuple):
        raise ValueError(label)
    return value


def scalar(value: Value | None, label: str) -> str:
    require(type(value) is str, "Saved scalar required: " + label)
    if not isinstance(value, str):
        raise ValueError(label)
    if value.startswith('"'):
        require(value.endswith('"'), "Unterminated saved scalar")
        # Keep save escaping lossless; selected names/flags have no escapes.
        require("\\" not in value[1:-1], "Escaped selected scalar requires an explicit decoder")
        return value[1:-1]
    return value


def records(path: Path, section: tuple[str, ...]) -> Iterator[tuple[str, str]]:
    """Read canonical Rakaly indentation, validating each selected record AST."""
    active: list[str] = []
    current: str | None = None
    captured: list[str] = []
    captured_bytes = 0
    record_depth = len(section)
    with path.open("r", encoding="utf-8", errors="strict") as stream:
        for line in stream:
            if current is not None:
                captured.append(line)
                captured_bytes += len(line)
                require(captured_bytes < 4 * 1024 * 1024, "Selected checkpoint record exceeds bound")
                if line.strip() == "}" and line.startswith("\t" * record_depth) and not line.startswith("\t" * (record_depth + 1)):
                    body = "".join(captured)
                    yield current, body
                    current, captured, captured_bytes = None, [], 0
                continue
            match = re.fullmatch(r"(\t*)([A-Za-z_0-9]+)=\{\s*\n?", line)
            if match is not None:
                depth = len(match.group(1))
                name = match.group(2)
                if depth == record_depth and tuple(active[:record_depth]) == section and name.isdecimal():
                    current, captured, captured_bytes = name, [line], len(line)
                elif depth < record_depth:
                    active[depth:] = [name]
            elif line.strip() == "}":
                depth = len(line) - len(line.lstrip("\t"))
                if depth < record_depth:
                    del active[depth:]
    require(current is None, "Truncated selected checkpoint record")


@dataclass(frozen=True)
class SavedVariable:
    kind: str | None
    raw_identity: str | None
    flag: str | None

    def integer_value(self, name: str) -> int:
        require(self.kind == "value" and self.flag is None, "Saved numeric variable required: " + name)
        # CK3's serializer omits an identity equal to zero in a typed value.
        raw = int(self.raw_identity) if self.raw_identity is not None else 0
        require(raw % 100000 == 0, "Fractional saved value rejected: " + name)
        return raw // 100000

    def artifact_reference(self, name: str) -> str:
        require(self.kind == "artifact" and self.raw_identity is not None and self.flag is None, "Saved artifact reference required: " + name)
        return decimal_id(self.raw_identity, name, allow_zero=True)

    def to_json(self) -> Object:
        return {"type": self.kind, "raw_identity_decimal": self.raw_identity, "flag": self.flag}


def variables(entries: tuple[Entry, ...]) -> dict[str, SavedVariable]:
    scope = one(entries, "variables", required=False)
    if scope is None:
        return {}
    data = structured(one(structured(scope, "variables"), "data"), "variables.data")
    result: dict[str, SavedVariable] = {}
    for entry in data:
        require(entry.key is None, "Expected anonymous saved variable record")
        record = structured(entry.value, "variable")
        name = scalar(one(record, "flag"), "variable name")
        if not name.startswith("xalw_"):
            continue
        require(name not in result, "Duplicate selected saved variable: " + name)
        value = structured(one(record, "data"), "variable data")
        kind = one(value, "type", required=False)
        identity = one(value, "identity", required=False)
        flag = one(value, "flag", required=False)
        raw = scalar(identity, "variable identity") if identity is not None else None
        require(raw is None or re.fullmatch(r"-?(0|[1-9][0-9]*)", raw) is not None, "Saved identity must be canonical signed decimal")
        result[name] = SavedVariable(scalar(kind, "variable type") if kind is not None else None, raw,
                                    scalar(flag, "variable flag") if flag is not None else None)
    return result


@dataclass(frozen=True)
class SavedArtifact:
    artifact_id: str
    owner_id: str
    name: str
    rarity: str
    artifact_type: str
    durability_decimal: str
    variables: dict[str, SavedVariable]

    @classmethod
    def parse(cls, reference: str, block: str) -> SavedArtifact:
        entries = parse_block(block[block.index("{"):])
        durability = scalar(one(entries, "durability"), "durability")
        try:
            amount = Decimal(durability)
        except InvalidOperation as error:
            raise ValueError("Saved durability is not decimal") from error
        require(amount.is_finite() and amount >= 0 and amount * 100000 == (amount * 100000).to_integral_value(), "Saved durability exceeds Q100000 precision")
        return cls(decimal_id(reference, "saved artifact", allow_zero=True), decimal_id(scalar(one(entries, "owner"), "owner"), "saved owner"),
                   scalar(one(entries, "name"), "name"), scalar(one(entries, "rarity"), "rarity"), scalar(one(entries, "type"), "artifact type"),
                   format(amount, ".5f"), variables(entries))

    def to_json(self) -> Object:
        return {"artifact_id": self.artifact_id, "owner_id": self.owner_id, "name": self.name, "rarity": self.rarity,
                "artifact_type": self.artifact_type, "durability_decimal": self.durability_decimal,
                "variables": {key: value.to_json() for key, value in self.variables.items()}}


@dataclass(frozen=True)
class SavedInputs:
    player_id: str
    target_id: str
    date_literal: str
    player_variables: dict[str, SavedVariable]
    artifacts: tuple[SavedArtifact, ...]

    def to_json(self) -> Object:
        return {"authority": "actual-checkpoint-saved-state-auxiliary", "current_native_artifact_variable_query": False,
                "player_id": self.player_id, "target_id": self.target_id, "saved_date": self.date_literal,
                "player_variables": {key: value.to_json() for key, value in self.player_variables.items()},
                "artifacts": [item.to_json() for item in self.artifacts]}


def inspect_inputs(melted: Path, *, player_id: int) -> SavedInputs:
    actor = str(native_id(player_id, "selected actual player"))
    player = [body for identity, body in records(melted, ("living",)) if identity == actor]
    require(len(player) == 1, "Exactly one actual living player record required")
    player_entries = parse_block(player[0][player[0].index("{"):])
    alive = structured(one(player_entries, "alive_data"), "living player alive data")
    player_variables = variables(alive)
    require("xalw_fixture_target" in player_variables, "Actual player has no saved fixture target reference")
    target_id = player_variables["xalw_fixture_target"].artifact_reference("xalw_fixture_target")
    selected: list[SavedArtifact] = []
    localizations = (render_fixture_localization("english"), render_fixture_localization("simp_chinese"))
    role_names = {role: frozenset((LIVING_NAME_PREFIX if role == "target" else "") + entries["xalw_test_living_name" if role == "target" else f"xalw_test_material_{role}_name"]
                                 for entries in localizations)
                  for role in ("target", "common", "masterwork", "famed", "illustrious")}
    wanted = set().union(*role_names.values())
    for identity, body in records(melted, ("artifacts", "artifacts")):
        if not any('name="' + name + '"' in body for name in wanted) and identity != target_id:
            continue
        item = SavedArtifact.parse(identity, body)
        if item.owner_id == actor:
            selected.append(item)
    require(len(selected) == 5 and len({item.artifact_id for item in selected}) == 5 and
            all(sum(item.name in names for item in selected) == 1 for names in role_names.values()),
            "Actual saved player must own five distinct named fixture inputs")
    target = [item for item in selected if item.artifact_id == target_id]
    require(len(target) == 1 and target[0].name in role_names["target"], "Saved target variable and actual named artifact disagree")
    for role in ("common", "masterwork", "famed", "illustrious"):
        require(all(item.rarity == role for item in selected if item.name in role_names[role]), "Actual saved material rarity differs from its named input role")
    dates: list[str] = []
    with melted.open(encoding="utf-8", errors="strict") as stream:
        for line in stream:
            if line.startswith("date="):
                dates.append(line.strip().removeprefix("date="))
    require(len(dates) == 1 and re.fullmatch(r"[1-9][0-9]*\.(?:[1-9]|1[0-2])\.(?:[1-9]|[12][0-9]|3[01])", dates[0]) is not None,
            "Exactly one actual saved calendar date required")
    return SavedInputs(actor, target_id, dates[0], player_variables, tuple(selected))
