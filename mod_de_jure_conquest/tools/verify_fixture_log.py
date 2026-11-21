"""Verify existing fixture logs, including three fresh tiers; never launch or sign off."""

from __future__ import annotations

import argparse
import codecs
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
from typing import Literal, NotRequired, Sequence, TypedDict, cast

from gen_acceptance_fixture import BEGIN_MARKER, CLAIMS_EXCLUDED, DONE_MARKER, GUI_BASE_VALUES, GUI_REFERENCES, GUI_RELOAD_VALUES, GUI_STANDALONE_SCHEMA, GUI_STANDALONE_VALUES, GUI_STANDALONE_REFERENCES, GUI_STANDALONE_BASE_VALUES, GUI_STANDALONE_RELOAD_VALUES, OUTCOMES, TIERS, Tier, expected_markers, reviewed_tier
from gen_acceptance_fixture import GUI_PHYSICAL_SCHEMA, GUI_PHYSICAL_SETUP_VALUES, GUI_PHYSICAL_AFTER_VALUES, GUI_PHYSICAL_AFTER_REFS
from inspect_ck3_save_character_scope import _anonymous_records
from inspect_ck3_save_player_topology import SaveInputIdentity, _numeric_records, _player_records, _save_input_identity, _save_text
from extract_auto_upgrade_buildings import parse_clausewitz, tokenize_clausewitz

BOUNDARY = "Log markers only; fresh scene/runtime/EXE, actual date/paused window, error.log, protected-storage and normal exit require separate evidence. No GUI/payment/SaveLoad/full-product qualification."


@dataclass(frozen=True)
class ParsedContract:
    tier: Tier
    layer: str
    markers: tuple[str, ...]
    claims_excluded: tuple[str, ...]
    target_context_hygiene: bool


class SingleReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: str
    player_history_id: int
    tier: Tier
    expected_pass_count: int
    observed_pass_count: int
    observed_marker_counts: dict[str, int]
    diagnostic_readbacks: dict[str, list[bool]]
    diagnostic_boundary: str
    target_context_hygiene: bool
    errors: list[str]
    log: str
    log_sha256: str
    contract: str
    contract_sha256: str
    claims_excluded: list[str]
    boundary: str


class AggregateReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: str
    player_history_id: int
    expected_pass_count: int
    observed_pass_count: int
    observed_marker_counts: dict[str, int]
    errors: list[str]
    source_runs: list[SingleReport]
    claims_excluded: list[str]
    boundary: str


class InvalidReport(TypedDict):
    result: Literal["RED"]
    layer: Literal["fixture-input-rejected"]
    errors: list[str]
    boundary: str


def string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    result = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field} must be a list of strings")
        result.append(item)
    return result


def parse_contract(raw: bytes) -> ParsedContract:
    value: object = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture contract must be a JSON object")
    schema = value.get("schema")
    if schema not in ("djc.external-acceptance.v1", "djc.external-acceptance.v2"):
        raise ValueError("unsupported fixture contract schema")
    player = value.get("player_history_id")
    if type(player) is not int or player != 1128:
        raise ValueError("fixture player_history_id must be integer 1128")
    tier = reviewed_tier(value.get("tier", "all"))
    if schema == "djc.external-acceptance.v1" and tier != "all":
        raise ValueError("legacy v1 contract must retain the full all-tier marker set")
    markers = string_list(value.get("markers"), "markers")
    if markers != expected_markers(tier):
        raise ValueError("contract markers must match the exact original ordered tier predicates")
    exclusions = string_list(value.get("claims_excluded"), "claims_excluded")
    if not set(CLAIMS_EXCLUDED[:7]).issubset(exclusions):
        raise ValueError("contract must preserve original uncovered business obligations")
    if value.get("layer") != "scripted-war-production-CB" or value.get("requires_done_marker") != DONE_MARKER:
        raise ValueError("fixture layer or required DONE marker differs from the production-CB contract")
    if schema == "djc.external-acceptance.v2":
        bound = value.get("max_natural_days")
        nominal = value.get("nominal_completion_natural_day")
        expected_bound, expected_nominal = (48, 46) if tier == "all" else (18, 16)
        if type(bound) is not int or bound != expected_bound or type(nominal) is not int or nominal != expected_nominal:
            raise ValueError("fixture natural-day schedule differs from the reviewed tier bound")
        if value.get("fresh_start_date") != "1066.9.15":
            raise ValueError("fixture must start on the actual reviewed 1066.9.15 bookmark")
        latest = "1066.11.2" if tier == "all" else "1066.10.3"
        for field, expected in (("latest_date", latest), ("completion_event", "djct.800"), ("failure_event", "djct.900"), ("watchdog_event", "djct.901"), ("live", "NOT_RUN")):
            if value.get(field) != expected:
                raise ValueError(f"fixture {field} differs from the reviewed preparation contract")
        if type(value.get("pause_boundary")) is not str or type(value.get("fixture_isolation")) is not str:
            raise ValueError("fixture preparation and pause boundaries must be explicit strings")
    hygiene = "event_target_context" in value
    if hygiene and (schema != "djc.external-acceptance.v2"
            or value.get("event_target_context") != "CLEAR-INHERITED-TARGET-BEFORE-NATIVE"
            or value.get("eligibility_failure_probe") != "READONLY-STATE-AND-ON-FAILURE"):
        raise ValueError("fixture event_target_context must declare the reviewed optional clear and diagnosis")
    if ("eligibility_failure_probe" in value
            and value.get("eligibility_failure_probe") != "READONLY-STATE-AND-ON-FAILURE"):
        raise ValueError("fixture eligibility_failure_probe differs from the reviewed readback contract")
    return ParsedContract(tier, "scripted-war-production-CB", tuple(markers), tuple(exclusions), hygiene)


def verify(log: Path, contract: Path) -> SingleReport:
    data = log.read_bytes()
    raw_contract = contract.read_bytes()
    value = data.decode("utf-8-sig", errors="replace")
    definition = parse_contract(raw_contract)
    passes = Counter(re.findall(r"DJCT: TEST PASS ([A-Za-z0-9_]+)", value))
    failures = re.findall(r"DJCT: TEST FAIL ([A-Za-z0-9_]+)", value)
    errors = []
    if failures:
        errors.append("failure markers: " + ", ".join(failures))
    for marker in definition.markers:
        if passes[marker] != 1:
            errors.append(f"expected one PASS {marker}, observed {passes[marker]}")
    for marker in sorted(passes.keys() - set(definition.markers)):
        errors.append(f"unexpected PASS marker {marker}")
    if value.count(BEGIN_MARKER) != 1:
        errors.append("fixture BEGIN count differs from one")
    if value.count(DONE_MARKER) != 1:
        errors.append("fixture DONE count differs from one")
    if "DJCT: TEST STOP" in value:
        errors.append("fixture stopped at a known failure window")
    diagnostics: dict[str, list[bool]] = {}
    for label, truth in re.findall(r"DJCT: PROBE ([A-Za-z0-9_]+) (TRUE|FALSE)\b", value):
        diagnostics.setdefault(label, []).append(truth == "TRUE")
    if definition.target_context_hygiene:
        stages = [f"{name}_{outcome}" for name, *_ in TIERS
                  if definition.tier == "all" or definition.tier == name
                  for outcome in OUTCOMES]
        for stage in stages:
            for suffix, expected in (
                ("context_identity_before_clear", True), ("context_identity_after_clear", True),
                ("context_target_exists_after_clear", False), ("context_native_after_clear", True),
                ("context_identity_after_native_query", True),
            ):
                if diagnostics.get(f"{stage}_{suffix}") != [expected]:
                    errors.append(f"expected one {stage}_{suffix}={expected} readback")
            if len(diagnostics.get(stage + "_context_native_before_clear", [])) != 1:
                errors.append(f"expected one {stage}_context_native_before_clear readback")
    return {
        "result": "RED" if errors else "GREEN", "layer": definition.layer,
        "player_history_id": 1128, "tier": definition.tier,
        "expected_pass_count": len(definition.markers), "observed_pass_count": sum(passes.values()),
        "observed_marker_counts": dict(sorted(passes.items())), "errors": errors,
        "diagnostic_readbacks": diagnostics,
        "diagnostic_boundary": "Probe booleans are not original PASS credit or a proved unique cause. Optional target-only evaluated-context clear is explicit in the contract; actual incoming scope IDs/types and dates remain in the bound raw log.",
        "target_context_hygiene": definition.target_context_hygiene,
        "log": str(log.resolve()), "log_sha256": hashlib.sha256(data).hexdigest(),
        "contract": str(contract.resolve()), "contract_sha256": hashlib.sha256(raw_contract).hexdigest(),
        "claims_excluded": list(definition.claims_excluded), "boundary": BOUNDARY,
    }


def aggregate(inputs: Sequence[tuple[Path, Path]]) -> AggregateReport:
    if len(inputs) != 3 or len({log.resolve() for log, _ in inputs}) != 3 or len({contract.resolve() for _, contract in inputs}) != 3:
        raise ValueError("aggregation requires three distinct log/contract pairs from three fresh tier runs")
    reports = [verify(log, contract) for log, contract in inputs]
    if {report["tier"] for report in reports} != {"duchy", "kingdom", "empire"}:
        raise ValueError("aggregation requires exactly one duchy, one kingdom and one empire contract")
    errors = [f"{report['tier']}: {message}" for report in reports for message in report["errors"]]
    counts: Counter[str] = Counter()
    for report in reports:
        counts.update(report["observed_marker_counts"])
    for marker in expected_markers():
        if counts[marker] != 1:
            errors.append(f"aggregate expected one PASS {marker}, observed {counts[marker]}")
    if set(counts) != set(expected_markers()):
        errors.append("aggregate marker identity set differs from all original 72 predicates")
    return {
        "result": "RED" if errors else "GREEN", "layer": "scripted-war-production-CB-three-fresh-tiers",
        "player_history_id": 1128, "expected_pass_count": 72, "observed_pass_count": sum(counts.values()),
        "observed_marker_counts": dict(sorted(counts.items())), "errors": errors, "source_runs": reports,
        "claims_excluded": sorted({item for report in reports for item in report["claims_excluded"]}), "boundary": BOUNDARY,
    }


@dataclass(frozen=True)
class SavedAtom:
    kind: str
    identity: int


@dataclass(frozen=True)
class SavedPoint:
    source: SaveInputIdentity
    player_id: int
    atoms: dict[str, SavedAtom]
    physical_date: str | None = None

    def value(self, key: str) -> int:
        atom = self.atoms[key]
        if atom.kind != "value":
            raise ValueError(f"{key} must be a physical saved value, found {atom.kind}")
        return atom.identity


class ArtifactEvidence(TypedDict):
    kind: str
    path: str
    sha256: str


class InitialSourcePin(TypedDict):
    path: str
    bytes: int
    sha256: str
    file_id: str
    mtime_ns: str


class GuiSaveReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: Literal["physical-saved-GUI-observer-data-only"]
    machine_id: str
    tier: Tier
    player_saved_id: str
    fixed_point_codec: str
    before_save: SaveInputIdentity
    after_reload_save: SaveInputIdentity
    gui_evidence_path: str
    gui_evidence_sha256: str
    gui_artifacts: list[ArtifactEvidence]
    companion_contract_sha256: str
    money_raw_decimal_strings: dict[str, str]
    persisted_references: dict[str, dict[str, str]]
    load_method: str
    errors: list[str]
    boundary: str
    source_mode: NotRequired[Literal["standalone-ordinary-only"]]
    initial_source_save: NotRequired[InitialSourcePin]
    physical_dates: NotRequired[dict[str, str]]


def required_string(value: object, field: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field} must be a nonempty string")
    return value


def preview_raw(value: object, field: str) -> int:
    text = required_string(value, field)
    if re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,5})?", text) is None:
        raise ValueError(f"{field} must be a nonnegative plain decimal string with at most five decimal places")
    try:
        amount = Decimal(text) * 100000
    except InvalidOperation as error:
        raise ValueError(f"invalid {field}") from error
    if amount != amount.to_integral_value() or amount > 2**63 - 1:
        raise ValueError(f"{field} exceeds the reviewed saved fixed-point domain")
    return int(amount)


def physical_native_zip(path: Path) -> bool:
    """Only the physical-only mode accepts actual native flat text as well.

    The observed Save header is SAV0100 plus sixteen hex characters. Do not
    reinterpret a decoded surrogate/plain arbitrary JSON as the physical Save.
    Full strict UTF8/EOF/NUL validation precedes the existing plaintext readers.
    """
    with path.open("rb") as stream:
        prefix = stream.read(128)
    if prefix.startswith(b"PK\x03\x04"):
        return True
    if re.match(br"SAV0100[0-9a-fA-F]{16}\r?\nmeta_data\s*=\s*\{", prefix) is None:
        raise ValueError("physical-only native input must be ZIP plaintext or observed SAV0100+16hex native flat text")
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            if "\x00" in decoder.decode(chunk):
                raise ValueError("native flat Save contains binary NUL data")
        decoder.decode(b"", final=True)
    return False


def source_identity(path: Path) -> tuple[int, int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def flat_living_player_block(path: Path, player: int) -> str | None:
    """Current native flat writer has column-zero living records.

    Match the real living/<player> path by lexical depth, not indentation or an
    unrelated numeric object with the same ID. The shared date reader already
    uses this strings/comments-aware structural scanner.
    """
    structural, quoted_end = re.compile(r'[{}"#]'), re.compile(r'["\\]')
    living_key = re.compile(r'\s*living\s*=\s*\{\s*$')
    record_key = re.compile(r'\s*' + str(player) + r'\s*=\s*\{\s*$')
    depth, quoted, living, tables = 0, False, False, 0
    captured: list[str] | None = None
    found: str | None = None
    with _save_text(path, native_zip=False) as stream:
        for line in stream:
            if not quoted and depth == 0 and living_key.fullmatch(line.rstrip('\r\n')):
                tables += 1
                if tables != 1:raise ValueError("duplicate physical living root table")
                living = True
            elif living and not quoted and depth == 1 and record_key.fullmatch(line.rstrip('\r\n')):
                if found is not None:raise ValueError("duplicate physical living player record")
                captured = []
            if captured is not None:captured.append(line)
            index = 0
            while index < len(line):
                token = (quoted_end if quoted else structural).search(line, index)
                if token is None:break
                char, index = token.group(), token.end()
                if quoted:
                    if char == '\\':index += 1
                    else:quoted = False
                elif char == '#':break
                elif char == '"':quoted = True
                else:
                    depth += 1 if char == '{' else -1
                    if depth < 0:raise ValueError("physical native braces differ")
            if captured is not None and depth == 1:
                found, captured = "".join(captured), None
            if living and depth == 0:living = False
    if depth != 0 or quoted or captured is not None:
        raise ValueError("unterminated physical native living input")
    return found


def flat_selected_atoms(record: str, player: int) -> dict[str, SavedAtom]:
    """Use the existing tokenizer on one bounded living actor only.

    Native variable list items use space-indented anonymous braces and bare flag
    tokens. Scope lookup is alive_data/variables/data, never regex over another
    actor's or an unrelated object's flags. No full-save decoder is introduced.
    """
    def end_of_block(tokens: list[str], opening: int) -> int:
        depth = 0
        for index in range(opening, len(tokens)):
            if tokens[index] == "{":depth += 1
            elif tokens[index] == "}":
                depth -= 1
                if depth == 0:return index
        raise ValueError("unterminated selected native actor block")

    def direct_fields(tokens: list[str]) -> dict[str, list[str | list[str]]]:
        result: dict[str, list[str | list[str]]] = {}
        index = 0
        while index < len(tokens):
            if index + 2 >= len(tokens) or tokens[index + 1] != "=":
                raise ValueError("selected native actor field is not a direct assignment")
            key, index = tokens[index], index + 2
            if tokens[index] == "{":
                end = end_of_block(tokens, index)
                value: str | list[str] = tokens[index + 1:end]
                index = end + 1
            else:
                value = tokens[index]
                index += 1
            result.setdefault(key, []).append(value)
        return result

    def one_block(tokens: list[str], key: str) -> list[str]:
        rows = direct_fields(tokens).get(key)
        if rows is None or len(rows) != 1 or not isinstance(rows[0], list):
            raise ValueError("native actor requires one exact " + key + " block")
        return rows[0]

    tokens = one_block(tokenize_clausewitz(record), str(player))
    for name in ("alive_data", "variables", "data"):
        tokens = one_block(tokens, name)
    selected = {*GUI_PHYSICAL_SETUP_VALUES, *GUI_STANDALONE_REFERENCES,
                *GUI_PHYSICAL_AFTER_VALUES, *GUI_PHYSICAL_AFTER_REFS,
                "djcg_date", "djcg_setup_date", "djcg_reload_date"}
    atoms: dict[str, SavedAtom] = {}
    index = 0
    while index < len(tokens):
        if tokens[index] != "{":raise ValueError("native variable collection needs anonymous records")
        end = end_of_block(tokens, index)
        fields = direct_fields(tokens[index + 1:end])
        index = end + 1
        flags = fields.get("flag")
        if flags is None or len(flags) != 1 or not isinstance(flags[0], str):
            raise ValueError("native variable record needs one scalar flag")
        name = flags[0]
        if name.startswith('"'):
            decoded: object = json.loads(name)
            if not isinstance(decoded, str):raise ValueError("native flag must be a string")
            name = decoded
        if name == "djcg_failed":raise ValueError("physical observer explicitly failed")
        if name not in selected:continue  # Empty once flags are not value0 atoms.
        if name in atoms:raise ValueError("duplicate selected native variable")
        data = fields.get("data")
        if data is None or len(data) != 1 or not isinstance(data[0], list):
            raise ValueError("selected native variable needs one typed data block")
        parsed = parse_clausewitz(" ".join(data[0]))
        pairs = {entry.key: entry.value for entry in parsed.entries}
        if (len(parsed.entries) != 2 or set(pairs) != {"type", "identity"}
                or any(entry.operator != "=" for entry in parsed.entries)
                or not isinstance(pairs["type"], str) or not isinstance(pairs["identity"], str)
                or re.fullmatch(r"[A-Za-z0-9_]+", pairs["type"]) is None
                or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", pairs["identity"]) is None
                or abs(int(pairs["identity"])) > 2**63 - 1):
            raise ValueError("selected native variable needs exact type/signed64 identity")
        atoms[name] = SavedAtom(pairs["type"], int(pairs["identity"]))
    return atoms


def read_saved_point(path: Path, phase: int, tier_value: int, *, standalone: bool = False, physical_stage: Literal["s0", "s1"] | None = None) -> SavedPoint:
    try:
        identity_before = source_identity(path) if physical_stage is not None else None
        native_zip = physical_native_zip(path) if physical_stage is not None else True
        source = _save_input_identity(path, native_zip=native_zip)
        played, current = _player_records(path, native_zip=native_zip)
        if len(current) != 1 or not any(row.get("character_id") == current[0] for row in played):
            raise ValueError("physical save needs one current played character and its actual played-character record")
        version: str | None = None
        with _save_text(path, native_zip=native_zip) as stream:
            for line in stream:
                match = re.fullmatch(r'\s*version="([^"\n]+)"\s*', line)
                if match:
                    version = match.group(1)
                    break
        if version != "1.21.0.3":
            raise ValueError("physical save version is not reviewed 1.21.0.3")
        root_block: str | None = None
        if physical_stage is not None and not native_zip:
            root_block = flat_living_player_block(path, current[0])
        else:
            for level, identity, block in _numeric_records(path, native_zip=native_zip):
                if level == 1 and identity == current[0] and "alive_data={" in block:
                    root_block = block
                    break
        if root_block is None or re.search(r'\balive_data\s*=\s*\{', root_block) is None:
            raise ValueError("actual current player living record is missing")
        atoms: dict[str, SavedAtom] = flat_selected_atoms(root_block, current[0]) if physical_stage is not None and not native_zip else {}
        for block in (() if physical_stage is not None and not native_zip else _anonymous_records(root_block)):
            names = re.findall(r'^\s*flag="(djcg_[^"]+)"$', block, re.MULTILINE)
            if not names:
                continue
            if physical_stage is not None:
                if "djcg_failed" in names:raise ValueError("physical observer explicitly failed")
                selected = {*GUI_PHYSICAL_SETUP_VALUES, *GUI_STANDALONE_REFERENCES,
                            *GUI_PHYSICAL_AFTER_VALUES, *GUI_PHYSICAL_AFTER_REFS,
                            "djcg_date", "djcg_setup_date", "djcg_reload_date"}
                if not any(name in selected for name in names):
                    # Actual once/capture character flags have empty data. They
                    # are not selected typed variables and are never coerced0.
                    continue
            if len(names) != 1 or names[0] in atoms:
                raise ValueError("duplicate or ambiguous GUI observer saved variable")
            kinds = re.findall(r'^\s*type=([A-Za-z0-9_]+)$', block, re.MULTILINE)
            identities = re.findall(r'^\s*identity=(-?(?:0|[1-9][0-9]*))$', block, re.MULTILINE)
            if len(kinds) != 1 or len(identities) != 1 or abs(int(identities[0])) > 2**63 - 1:
                raise ValueError("saved observer atom must have one typed signed64 decimal identity")
            atoms[names[0]] = SavedAtom(kinds[0], int(identities[0]))
        if physical_stage is not None:
            result = SavedPoint(source, current[0], atoms, physical_saved_date(path, native_zip=native_zip))
            validate_physical_point(result, physical_stage)
            if _save_input_identity(path, native_zip=native_zip) != source or source_identity(path) != identity_before:
                raise ValueError("physical source changed during observation")
            return result
        base_values = GUI_STANDALONE_BASE_VALUES if standalone else GUI_BASE_VALUES
        reload_values = GUI_STANDALONE_RELOAD_VALUES if standalone else GUI_RELOAD_VALUES
        expected = (*base_values, *GUI_REFERENCES, *(reload_values if phase == 3 else ()), *(GUI_STANDALONE_VALUES if standalone else ()), *(GUI_STANDALONE_REFERENCES if standalone else ()))
        if not set(expected).issubset(atoms):
            raise ValueError("physical save lacks required observer values or references")
        result = SavedPoint(source, current[0], atoms, physical_saved_date(path) if standalone else None)
        for key in (*base_values, *(reload_values if phase == 3 else ())):
            result.value(key)
        if result.value("djcg_phase") != phase * 100000 or result.value("djcg_tier") != tier_value * 100000:
            raise ValueError("physical save phase/tier differs from the actual observer contract")
        for key in GUI_REFERENCES:
            if atoms[key].kind == "value" or atoms[key].identity <= 0:
                raise ValueError("physical saved object references must retain typed positive identities")
        if atoms["djcg_primary"].kind != "char" or atoms["djcg_secondary"].kind != "char" or len({current[0], atoms["djcg_primary"].identity, atoms["djcg_secondary"].identity}) != 3:
            raise ValueError("physical player/primary/secondary character identities are not distinct")
        if standalone:
            for key in GUI_STANDALONE_VALUES:
                result.value(key)
            if (result.value("djcg_standalone") != 100000
                    or result.value("djcg_setup_prestige") != result.value("djcg_before_prestige")
                    or result.value("djcg_setup_piety") != result.value("djcg_before_piety")):
                raise ValueError("standalone saved setup/mode differs from actual business before snapshot")
            if {"djcg_setup_date", "djcg_date", "djcg_reload_date"} & atoms.keys():
                raise ValueError("standalone v2 must use actual physical dates, not obsolete script date variables")
            if atoms["djcg_goal"].kind != "lt" or atoms["djcg_war"].kind != "war":
                raise ValueError("standalone saved goal/war must retain actual lt/war types")
            for key in GUI_STANDALONE_REFERENCES:
                expected_kind = "char" if key.endswith(("primary", "secondary")) else "lt"
                if atoms[key].kind != expected_kind or atoms[key].identity <= 0:
                    raise ValueError("standalone setup reference types/identities differ")
            if any(atoms["djcg_setup_" + key] != atoms["djcg_" + key] for key in ("goal", "primary", "secondary")):
                raise ValueError("standalone actual goal/participants differ from S0 setup references")
            if len({atoms[key].identity for key in GUI_STANDALONE_REFERENCES[:3]}) != 3:
                raise ValueError("standalone ducal goal and two county IDs must be distinct")
        if _save_input_identity(path, native_zip=True) != source:
            raise ValueError("physical saved source changed during observation")
        return result
    except zipfile.BadZipFile as error:
        raise ValueError(f"physical save ZIP/CRC invalid: {error}") from error


def physical_saved_date(path: Path, *, native_zip: bool = True) -> str:
    """Read the unique root date, respecting strings/comments, without extraction."""
    structural = re.compile(r'[{}"#]')
    quoted_end = re.compile(r'["\\]')
    date_pattern = re.compile(r'\s*date\s*=\s*(?:"([0-9]+\.[0-9]+\.[0-9]+)"|([0-9]+\.[0-9]+\.[0-9]+))\s*(?:#.*)?$')
    depth, quoted = 0, False
    dates: list[str] = []
    with _save_text(path, native_zip=native_zip) as stream:
        for line in stream:
            if depth == 0 and not quoted:
                match = date_pattern.fullmatch(line.rstrip('\r\n'))
                if match:
                    dates.append(match.group(1) or match.group(2))
            index = 0
            while index < len(line):
                token = (quoted_end if quoted else structural).search(line, index)
                if token is None:
                    break
                char = token.group()
                index = token.end()
                if quoted:
                    if char == '\\':index += 1
                    else:quoted = False
                elif char == '#':break
                elif char == '"':quoted = True
                else:
                    depth += 1 if char == '{' else -1
                    if depth < 0:raise ValueError("physical Save root braces differ")
    if depth != 0 or quoted or dates != ["1066.9.15"]:
        raise ValueError("standalone requires exactly one actual physical root date1066.9.15")
    return dates[0]


def verify_gui_saves(before: Path, after: Path, evidence: Path, contract: Path) -> GuiSaveReport:
    if before.resolve() == after.resolve():
        raise ValueError("two distinct physical Save files are required")
    raw_contract = contract.read_bytes()
    definition: object = json.loads(raw_contract)
    if not isinstance(definition, dict) or definition.get("schema") not in ("djc.gui-ordinary-save.v1", GUI_STANDALONE_SCHEMA):
        raise ValueError("GUI companion contract schema differs")
    standalone = definition.get("schema") == GUI_STANDALONE_SCHEMA
    tier = reviewed_tier(definition.get("tier"))
    if tier == "all":
        raise ValueError("GUI companion must bind one completed tier")
    tier_index, tier_row = next((index, row) for index, row in enumerate(TIERS) if row[0] == tier)
    if type(definition.get("player_history_id")) is not int or definition.get("player_history_id") != 1128 or type(definition.get("tier_value")) is not int or definition.get("tier_value") != tier_index + 1:
        raise ValueError("GUI companion actor/tier identity differs")
    if definition.get("goal") != tier_row[1] or definition.get("casus_belli") != tier + "_de_jure_greatwar":
        raise ValueError("GUI companion goal or CB differs")
    base_values = GUI_STANDALONE_BASE_VALUES if standalone else GUI_BASE_VALUES
    reload_values = GUI_STANDALONE_RELOAD_VALUES if standalone else GUI_RELOAD_VALUES
    for field, expected in (("base_value_variables", base_values), ("reload_value_variables", reload_values), ("reference_variables", GUI_REFERENCES)):
        if string_list(definition.get(field), field) != list(expected):
            raise ValueError("GUI companion saved-variable contract differs")
    if standalone:
        if (tier != "duchy" or definition.get("same_completed_matrix_world_required") is not False
                or definition.get("matrix_pass_credit") is not False
                or any(definition.get(key) is not True for key in ("ordinary_gui_required", "same_paused_date_required", "standalone_setup_required", "initial_source_save_required"))
                or definition.get("fresh_start_date") != "1066.9.15" or definition.get("setup_event") != "djcg.1"
                or definition.get("fixture_context_clear") != "target-only-before-native"
                or definition.get("physical_calendar_required") != "literal15-and-both-physical-save-root-dates"
                or type(definition.get("saved_entry_bridge")) is not bool
                or string_list(definition.get("standalone_value_variables"), "standalone_value_variables") != list(GUI_STANDALONE_VALUES)
                or string_list(definition.get("standalone_reference_variables"), "standalone_reference_variables") != list(GUI_STANDALONE_REFERENCES)):
            raise ValueError("standalone source setup contract differs; it cannot claim a completed matrix")
        resources = definition.get("setup_resources")
        if (not isinstance(resources, dict) or set(resources) != {"prestige", "piety", "prestige_level"}
                or any(type(resources.get(key)) is not int or resources[key] != expected
                       for key, expected in (("prestige", 100000), ("piety", 100000), ("prestige_level", 5)))):
            raise ValueError("standalone explicit resource preparation contract differs")
    elif any(definition.get(key) is not True for key in ("ordinary_gui_required", "same_completed_matrix_world_required", "same_paused_date_required")):
        raise ValueError("GUI companion must retain ordinary same-world paused GUI obligations")
    for key, expected_number in (("max_extra_natural_days", 0), ("save_before_reload_phase", 2), ("save_after_reload_phase", 3)):
        if type(definition.get(key)) is not int or definition.get(key) != expected_number:
            raise ValueError("GUI companion day/phase contract differs")
    if definition.get("native_qualification") != "NOT_GRANTED" or definition.get("live") != "NOT_RUN":
        raise ValueError("GUI companion metadata cannot grant Native or live qualification")
    raw_evidence = evidence.read_bytes()
    value: object = json.loads(raw_evidence)
    evidence_schema = "djc.gui-standalone-physical-save-evidence.v2" if standalone else "djc.gui-physical-save-evidence.v1"
    if not isinstance(value, dict) or value.get("schema") != evidence_schema:
        raise ValueError("actual GUI evidence schema differs")
    if value.get("machine_id") != "desktop-3fevhd2-1c74096080" or value.get("game_version") != "1.21.0.3" or type(value.get("game_build")) is not int or value.get("game_build") != 26785313 or value.get("exe_sha256") != "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28" or value.get("tier") != tier:
        raise ValueError("actual GUI source machine/build/EXE/tier identity differs")
    if standalone:
        if (value.get("ordinary_gui_declaration") is not True or value.get("same_completed_matrix_world") is not False
                or value.get("fresh_source_setup_world") is not True or value.get("setup_action_actual") is not True
                or value.get("paused_same_date") is not True):
            raise ValueError("standalone ordinary GUI, actual source/setup and paused same-date evidence are mandatory")
    elif value.get("ordinary_gui_declaration") is not True or value.get("same_completed_matrix_world") is not True or value.get("paused_same_date") is not True:
        raise ValueError("actual ordinary GUI, same-world and paused same-date records are mandatory")
    method = required_string(value.get("load_method"), "load_method")
    if method not in ("gui_load_same_process", "cold_process_load"):
        raise ValueError("unsupported actual Load method")
    pids = [required_string(value.get(key), key) for key in ("process_before", "process_after")]
    if any(re.fullmatch(r"[1-9][0-9]*", pid) is None for pid in pids) or ((pids[0] == pids[1]) != (method == "gui_load_same_process")):
        raise ValueError("Load method must retain actual equal or distinct process identities")
    rows = value.get("artifacts")
    if not isinstance(rows, list):
        raise ValueError("actual GUI artifact list is required")
    artifacts: list[ArtifactEvidence] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"kind", "path", "sha256"}:
            raise ValueError("GUI artifact requires exact kind/path/SHA fields")
        kind = required_string(row["kind"], "artifact kind")
        path = Path(required_string(row["path"], "artifact path"))
        expected_digest = required_string(row["sha256"], "artifact SHA")
        if not path.is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", expected_digest) or hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest:
            raise ValueError("actual GUI artifact path/bytes/SHA mismatch")
        artifacts.append(ArtifactEvidence(kind=kind, path=str(path), sha256=expected_digest))
    required_kinds = {"preview", "declare_action", "load_action", "reloaded_state"}
    if standalone:
        required_kinds.add("setup_action")
    if method == "cold_process_load":
        required_kinds.add("process_lifecycle")
    if {row["kind"] for row in artifacts} != required_kinds or len(artifacts) != len(required_kinds):
        raise ValueError("one exact artifact for each real GUI action/state is required")
    initial_pin: InitialSourcePin | None = None
    initial_path: Path | None = None
    if standalone:
        if (before.stat().st_dev, before.stat().st_ino) == (after.stat().st_dev, after.stat().st_ino):
            raise ValueError("standalone physical Save points must not be the same file/hardlink")
        raw_pin = value.get("initial_source_save")
        if not isinstance(raw_pin, dict) or set(raw_pin) != {"path", "bytes", "sha256", "file_id", "mtime_ns"}:
            raise ValueError("standalone initial physical source requires exact path/bytes/SHA/FileID/mtime")
        initial_path = Path(required_string(raw_pin["path"], "initial source path"))
        if not initial_path.is_absolute() or type(raw_pin["bytes"]) is not int or raw_pin["bytes"] <= 0:
            raise ValueError("standalone initial source path/bytes differ")
        for key, pattern in (("sha256", r"[0-9a-f]{64}"), ("file_id", r"[1-9][0-9]*"), ("mtime_ns", r"[1-9][0-9]*")):
            if re.fullmatch(pattern, required_string(raw_pin[key], key)) is None:
                raise ValueError("standalone initial source identity is not canonical")
        initial_pin = InitialSourcePin(path=str(initial_path), bytes=raw_pin["bytes"], sha256=raw_pin["sha256"], file_id=raw_pin["file_id"], mtime_ns=raw_pin["mtime_ns"])
        check_initial_source(initial_path, initial_pin, before, after)
    first = read_saved_point(before, 2, tier_index + 1, standalone=standalone)
    second = read_saved_point(after, 3, tier_index + 1, standalone=standalone)
    if value.get("loaded_save_sha256") != first.source["sha256"]:
        raise ValueError("actual Load record must bind the exact first physical saved bytes")
    if first.player_id != second.player_id:
        raise ValueError("physical saved player identity changed")
    errors = []
    for key in (*base_values[1:], *GUI_REFERENCES, *(GUI_STANDALONE_VALUES if standalone else ()), *(GUI_STANDALONE_REFERENCES if standalone else ())):
        if first.atoms[key] != second.atoms[key]:
            errors.append(f"saved observer value/reference changed across actual load: {key}")
    for name in ("gold", "prestige", "piety"):
        if first.value("djcg_after_" + name) != second.value("djcg_reload_" + name):
            errors.append(f"actual reloaded {name} differs from saved after-GUI value")
    if standalone:
        if first.physical_date != second.physical_date or first.physical_date != "1066.9.15":
            errors.append("actual physical Save root dates differ from the zero-day contract")
    elif first.value("djcg_date") != second.value("djcg_reload_date"):
        errors.append("actual reload date differs from saved GUI date")
    same, peace = first.value("djcg_same_faith"), first.value("djcg_peace_of_god")
    extra = first.value("djcg_expected_extra_piety")
    if same not in (0, 100000) or peace not in (0, 100000) or extra != (100 * 100000 if same and peace else 0):
        errors.append("observed Peace-of-God predicates/medium100 extra piety differ from reviewed stock")
    prestige_preview = preview_raw(value.get("preview_prestige"), "preview_prestige")
    piety_preview = preview_raw(value.get("preview_piety"), "preview_piety")
    prestige_delta = first.value("djcg_before_prestige") - first.value("djcg_after_prestige")
    piety_delta = first.value("djcg_before_piety") - first.value("djcg_after_piety")
    if prestige_delta != prestige_preview:
        errors.append("actual total prestige debit differs from recorded ordinary GUI preview")
    if piety_delta != piety_preview + extra:
        errors.append("actual total piety debit differs from GUI CB preview plus observed conditional stock extra")
    if standalone and first.value("djcg_before_gold") != first.value("djcg_after_gold"):
        errors.append("standalone actual gold changed although the selected production CB has no gold cost")
    if _save_input_identity(before, native_zip=True) != first.source or _save_input_identity(after, native_zip=True) != second.source or evidence.read_bytes() != raw_evidence or contract.read_bytes() != raw_contract:
        raise ValueError("actual source input changed during GUI/save verification")
    if standalone and initial_path is not None and initial_pin is not None:
        check_initial_source(initial_path, initial_pin, before, after)
    report: GuiSaveReport = {
        "result": "RED" if errors else "GREEN", "layer": "physical-saved-GUI-observer-data-only",
        "machine_id": "desktop-3fevhd2-1c74096080", "tier": tier, "player_saved_id": str(first.player_id),
        "fixed_point_codec": "physical CK3 saved type=value identity / 100000; not a Native memory/resource ABI",
        "before_save": first.source, "after_reload_save": second.source,
        "gui_evidence_path": str(evidence.resolve()), "gui_evidence_sha256": hashlib.sha256(raw_evidence).hexdigest(),
        "gui_artifacts": artifacts, "companion_contract_sha256": hashlib.sha256(raw_contract).hexdigest(),
        "money_raw_decimal_strings": {"prestige_preview": str(prestige_preview), "piety_preview": str(piety_preview), "conditional_extra_piety": str(extra), "actual_total_prestige_debit": str(prestige_delta), "actual_total_piety_debit": str(piety_delta), "before_prestige": str(first.value("djcg_before_prestige")), "after_prestige": str(first.value("djcg_after_prestige")), "before_piety": str(first.value("djcg_before_piety")), "after_piety": str(first.value("djcg_after_piety"))},
        "persisted_references": {key: {"kind": first.atoms[key].kind, "raw_identity": str(first.atoms[key].identity)} for key in GUI_REFERENCES},
        "load_method": method, "errors": errors,
        "boundary": "Physical ZIP+CRC and exact persistent observer data/GUI-source hashes only. Actual ordinary UI/Load/paused/date/process lifecycle authenticity comes from the supplied operator evidence; phase3 or two files alone cannot prove Load. No Native ABI, full-product, peace, concurrency or general Save compatibility qualification.",
    }
    if standalone and initial_pin is not None:
        report["source_mode"] = "standalone-ordinary-only"
        report["initial_source_save"] = initial_pin
        report["persisted_references"].update({key: {"kind": first.atoms[key].kind, "raw_identity": str(first.atoms[key].identity)} for key in GUI_STANDALONE_REFERENCES})
        report["physical_dates"] = {"before_reload": first.physical_date or "", "after_reload": second.physical_date or ""}
        report["money_raw_decimal_strings"].update(
            before_gold=str(first.value("djcg_before_gold")), after_gold=str(first.value("djcg_after_gold")),
            actual_total_gold_debit=str(first.value("djcg_before_gold") - first.value("djcg_after_gold")))
        report["boundary"] += " Standalone setup has no completed-matrix credit; initial physical source pin and actual setup action are bound operator evidence, not an independent decoded initial-world proof."
    return report


def check_initial_source(path: Path, expected: InitialSourcePin, before: Path, after: Path) -> None:
    stat_before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    stat_after = path.stat()
    actual = (stat_after.st_size, digest, str(stat_after.st_ino), str(stat_after.st_mtime_ns))
    if (stat_before.st_size, stat_before.st_ino, stat_before.st_mtime_ns) != (stat_after.st_size, stat_after.st_ino, stat_after.st_mtime_ns) or actual != (expected["bytes"], expected["sha256"], expected["file_id"], expected["mtime_ns"]):
        raise ValueError("standalone initial source bytes/identity changed")
    if any((stat_after.st_dev, stat_after.st_ino) == (p.stat().st_dev, p.stat().st_ino) for p in (before, after)):
        raise ValueError("standalone initial source cannot be either resulting Save/hardlink")


def validate_physical_point(point: SavedPoint, stage: Literal["s0", "s1"]) -> None:
    """Read bounded actual observer fields; phase numbers never grant credit here."""
    values = (*GUI_PHYSICAL_SETUP_VALUES, *(GUI_PHYSICAL_AFTER_VALUES if stage == "s1" else ()))
    refs = (*GUI_STANDALONE_REFERENCES, *(GUI_PHYSICAL_AFTER_REFS if stage == "s1" else ()))
    if not set((*values, *refs)).issubset(point.atoms):
        raise ValueError("physical S0/S1 lacks real setup/war/resource observations; phase alone is insufficient")
    for key in values:
        point.value(key)
    for key in ("djcg_standalone", "djcg_tier", "djcg_physical"):
        if point.value(key) != 100000:
            raise ValueError("physical observer requires exact standalone ducal mode")
    if {"djcg_date", "djcg_setup_date", "djcg_reload_date"} & point.atoms.keys():
        raise ValueError("physical observer must use real Save dates, not obsolete script date variables")
    for key in refs:
        kind = "war" if key == "djcg_war" else "char" if key.endswith(("primary", "secondary", "attacker")) else "lt"
        if point.atoms[key].kind != kind or point.atoms[key].identity <= 0:
            raise ValueError("physical war/participant/title reference type or identity differs")
    if len({point.player_id, point.atoms["djcg_setup_primary"].identity, point.atoms["djcg_setup_secondary"].identity}) != 3:
        raise ValueError("physical actual actor and two defenders must be distinct")
    if len({point.atoms[k].identity for k in GUI_STANDALONE_REFERENCES[:3]}) != 3:
        raise ValueError("physical goal and county title identities must be distinct")
    same, peace = point.value("djcg_same_faith"), point.value("djcg_peace_of_god")
    if same not in (0, 100000) or peace not in (0, 100000) or point.value("djcg_expected_extra_piety") != (10000000 if same and peace else 0):
        raise ValueError("physical observed Peace-of-God predicates/conditional extra differ")
    if stage == "s0":
        if {"djcg_war", "djcg_physical_captured"} & point.atoms.keys():
            raise ValueError("S0 baseline already contains a captured war")
    else:
        if point.value("djcg_physical_captured") != 100000 or point.value("djcg_war_count") != 100000:
            raise ValueError("S1 needs exactly one actual matched war")
        if point.atoms["djcg_actual_attacker"] != SavedAtom("char", point.player_id):
            raise ValueError("actual war primary attacker differs from actual player")
        for key in ("goal", "primary", "secondary"):
            if point.atoms["djcg_actual_" + key] != point.atoms["djcg_setup_" + key]:
                raise ValueError("actual war goal/defender differs from S0 setup")


def physical_json(raw: bytes) -> dict[str, object]:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in rows:
            if key in result:
                raise ValueError("duplicate JSON field in actual physical evidence")
            result[key] = value
        return result
    value: object = json.loads(raw, object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError("actual evidence must be a direct object")
    return cast(dict[str, object], value)


@dataclass(frozen=True)
class PhysicalArtifact:
    path: Path
    raw: bytes
    stat: tuple[int, int, int, int]

    def recheck(self) -> None:
        now = self.path.stat()
        if (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns) != self.stat or self.path.read_bytes() != self.raw:
            raise ValueError("actual physical evidence bytes/identity changed during verification")


def physical_artifact(value: object, field: str) -> PhysicalArtifact:
    if not isinstance(value, dict) or set(value) != {"path", "bytes", "sha256", "file_id", "mtime_ns"}:
        raise ValueError(field + " requires full path/bytes/SHA/FileID/mtime Pin")
    path = Path(required_string(value.get("path"), field + " path"))
    if not path.is_absolute():
        raise ValueError(field + " path must be absolute")
    stat = path.stat()
    raw = path.read_bytes()
    if (type(value.get("bytes")) is not int or value["bytes"] != len(raw)
            or value.get("sha256") != hashlib.sha256(raw).hexdigest()
            or value.get("file_id") != str(stat.st_ino) or value.get("mtime_ns") != str(stat.st_mtime_ns)):
        raise ValueError(field + " actual bytes/identity Pin mismatch")
    result = PhysicalArtifact(path, raw, (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns))
    result.recheck()
    return result


def physical_object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(field + " must be a direct object")
    return cast(dict[str, object], value)


def verify_physical_saves(s0: Path, s1: Path, evidence: Path, contract: Path) -> dict[str, object]:
    """S0 -> real ordinary Native UI -> S1 -> fresh passive cold readback.

    No event/decision/console invocation, phase2/3, or second same-process Save.
    Observer snapshots are bounded real script predicates, not full War-table AST.
    """
    if s0.samefile(s1):
        raise ValueError("S0 and S1 must be distinct physical files, not a hardlink")
    source_identities = (source_identity(s0), source_identity(s1))
    raw_contract, raw_evidence = contract.read_bytes(), evidence.read_bytes()
    definition = physical_json(raw_contract)
    expected_contract: dict[str, object] = {
        "schema": GUI_PHYSICAL_SCHEMA, "tier": "duchy", "player_history_id": 1128,
        "goal": "d_capua", "casus_belli": "duchy_de_jure_greatwar",
        "setup_value_variables": list(GUI_PHYSICAL_SETUP_VALUES), "setup_reference_variables": list(GUI_STANDALONE_REFERENCES),
        "after_value_variables": list(GUI_PHYSICAL_AFTER_VALUES), "after_reference_variables": list(GUI_PHYSICAL_AFTER_REFS),
        "current_date": "1066.9.15", "maximum_natural_days": 0, "requires_phase_markers": False,
        "saved_entry_bridge": True, "passive_real_war_observer": True,
        "cold_match_marker": "DJCG: PHYSICAL READBACK MATCH war_goal_participants_resources",
        "matrix_pass_credit": False, "native_qualification": "NOT_GRANTED", "live": "NOT_RUN"}
    if definition != expected_contract:
        raise ValueError("physical-only contract differs; legacy phase requirements cannot be substituted")
    value = physical_json(raw_evidence)
    if (value.get("schema") != "djc.physical-ordinary-evidence.v1"
            or value.get("machine_id") != "desktop-3fevhd2-1c74096080"
            or value.get("game_version") != "1.21.0.3" or type(value.get("game_build")) is not int or value["game_build"] != 26785313
            or value.get("exe_sha256") != "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28"
            or value.get("ordinary_native_ui") is not True or value.get("cold_load_exact_s1") is not True):
        raise ValueError("actual physical evidence machine/build/channel identity differs")
    first = read_saved_point(s0, 0, 1, physical_stage="s0")
    second = read_saved_point(s1, 0, 1, physical_stage="s1")
    if first.player_id != second.player_id or any(first.atoms[key] != second.atoms[key] for key in (*GUI_PHYSICAL_SETUP_VALUES, *GUI_STANDALONE_REFERENCES)):
        raise ValueError("S1 actual actor/setup references or before balances differ from S0")
    if value.get("loaded_save_sha256") != second.source["sha256"]:
        raise ValueError("cold Load must bind exact S1 bytes, not S0/phase markers")
    processes = string_list(value.get("process_ids"), "process_ids")
    if len(processes) != 3 or len(set(processes)) != 3 or any(re.fullmatch(r"[1-9][0-9]*", p) is None for p in processes):
        raise ValueError("S0, ordinary-S1 and cold-read require three actual distinct process IDs")
    names = ("native_dispatch", "cold_core", "cold_log", "load_lifecycle", "setup_action", "observer_source", "initial_source_save")
    pins = {name: physical_artifact(value.get(name), name) for name in names}
    if any(pins["initial_source_save"].path.samefile(p) for p in (s0, s1)):
        raise ValueError("initial source cannot be the resulting S0/S1 or their hardlink")
    if value.get("observer_contract_sha256") != hashlib.sha256(raw_contract).hexdigest():
        raise ValueError("actual adopted observer contract Pin differs")
    dispatch, core = physical_json(pins["native_dispatch"].raw), physical_json(pins["cold_core"].raw)
    if (dispatch.get("schema") != "ck3.djc_declaration_ui.current267_result.v1"
            or dispatch.get("game_version") != "1.21.0.3"
            or dispatch.get("executable_sha256") != "859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28"
            or dispatch.get("adapter_id") != "ck3-1.21.0.3-26785313-msvc-x64"
            or dispatch.get("backend") != "ck3-1.21.0.3-native-application-main-djc-ui"
            or (dispatch.get("action"), dispatch.get("step"), dispatch.get("status")) not in (
                ("send_ui", "send-current-djc-declaration-ui-v1", "send_dispatched"),
                ("accept_warning", "accept-current-djc-declaration-warning-v1", "warning_dispatched"))
            or any(dispatch.get(k) is not True for k in ("source_available", "effect_attempted", "native_returned", "cleanup_known"))
            or any(dispatch.get(k) is not False for k in ("submitted", "war_created", "payment_confirmed", "physical_save_confirmed"))
            or any(k not in dispatch or dispatch[k] is not None for k in ("war_id", "total_debit", "unavailable_reason"))):
        raise ValueError("actual v23 Native dispatch original is missing/inconsistent; dispatch is not War/debit proof")
    source = physical_object(dispatch.get("source"), "Native source")
    selected = physical_object(source.get("selected"), "Native selected tuple")
    if (source.get("schema") != "ck3.djc_declaration_ui.current267_source.v1"
            or source.get("actor_id") != first.player_id
            or source.get("recipient_id") != first.atoms["djcg_setup_primary"].identity
            or source.get("target_character_id") != first.atoms["djcg_setup_primary"].identity
            or source.get("cb_key") != "duchy_de_jure_greatwar"
            or selected.get("cb_key") != "duchy_de_jure_greatwar"
            or selected.get("target_title_ids") != [first.atoms["djcg_setup_goal"].identity]
            or selected.get("source_row_enabled") is not True
            or type(selected.get("claimant_character_id")) is not int
            or not isinstance(selected.get("extra_configuration_ids"), list)
            or any(type(n) is not int or not -(2**31) <= n < 2**31 for n in cast(list[object], selected.get("extra_configuration_ids")))):
        raise ValueError("actual Native selected actor/recipient/CB/goal/configuration tuple differs")
    facts = physical_object(dispatch.get("facts_before"), "Native facts_before")
    for frame in (facts, core):
        if (any(frame.get(k) is not True for k in ("paused", "map_ready", "has_played_character", "played_character_alive"))
                or frame.get("played_character_id") != first.player_id or type(frame.get("date_raw")) is not int):
            raise ValueError("actual paused Core actor/date is missing or differs")
    if (core.get("schema") != "ck3_1210_core_frame_v1" or core.get("status") != "partial"
            or core.get("game_version") != "1.21.0.3"
            or core.get("executable_sha256") != "859F0D380098ADCB130EB9D453458222749FCDF6D46126AD0ED99D78F9A0AA28"
            or core.get("adapter_id") != "ck3-1.21.0.3-26785313-msvc-x64"
            or core.get("core_available") is not True or core.get("complete_snapshot") is not False
            or core.get("date_raw") != facts["date_raw"]
            or core.get("excluded_snapshot_families") != ["treasury", "domain", "military", "campaign"]):
        raise ValueError("fresh cold Core is unavailable/different-date; it never supplies War or money")
    log = pins["cold_log"].raw.decode("utf-8-sig")
    marker = cast(str, definition["cold_match_marker"])
    if log.count(marker) != 1 or "DJCG: PHYSICAL READBACK FAIL" in log or "DJCG: STOP" in log:
        raise ValueError("fresh cold log lacks one actual matching current-war/resource readback")
    setup_log = pins["setup_action"].raw.decode("utf-8-sig")
    if setup_log.count("DJCG: SETUP standalone_resources_before_business_observation") != 1 or "DJCG: OBSERVE FAIL" in setup_log:
        raise ValueError("S0 requires one actual guarded setup observation")
    # These are trusted operator-origin records, independently pinned. Neither a
    # marker nor copied file alone proves SAVE/Load/lifecycle or source adoption.
    if any(not pins[n].raw for n in ("load_lifecycle", "setup_action", "observer_source")):
        raise ValueError("actual setup/source/Load lifecycle records are required")
    lifecycle = physical_json(pins["load_lifecycle"].raw)
    if (lifecycle.get("schema") != "djc.physical-load-lifecycle.v1"
            or lifecycle.get("process_ids") != processes
            or lifecycle.get("loaded_save_sha256") != second.source["sha256"]
            or lifecycle.get("S0_sha256") != first.source["sha256"]
            or lifecycle.get("physical_S0_confirmed") is not True
            or lifecycle.get("physical_S1_confirmed") is not True
            or lifecycle.get("cold_loaded") is not True):
        raise ValueError("actual physical SAVE and exact cold Load/process lifecycle record differs")
    deltas = {n: first.value("djcg_setup_" + n) - second.value("djcg_after_" + n) for n in ("gold", "prestige", "piety")}
    errors = []
    if deltas["gold"] != 0 or any(deltas[n] < 0 for n in ("prestige", "piety")):
        errors.append("actual ordinary declaration gold changed or prestige/piety increased")
    if deltas["piety"] < first.value("djcg_expected_extra_piety"):
        errors.append("actual piety debit is below the observed conditional stock surcharge")
    # Preview is optional because current v23 does not supply price. No invented
    # 50/200/300 Native values: report this missing independent obligation.
    preview = value.get("preview")
    preview_verified = preview is not None
    if preview is not None:
        prices = physical_object(preview, "actual preview")
        preview_pin = physical_artifact(prices.get("artifact"), "preview")
        if deltas["prestige"] != preview_raw(prices.get("prestige"), "preview prestige") or deltas["piety"] != preview_raw(prices.get("piety"), "preview piety") + first.value("djcg_expected_extra_piety"):
            errors.append("actual total debit differs from supplied genuine preview plus conditional stock extra")
        preview_pin.recheck()
    for pin in pins.values():
        pin.recheck()
    if (_save_input_identity(s0, native_zip=first.source["format"] == "native_zip_plaintext") != first.source
            or _save_input_identity(s1, native_zip=second.source["format"] == "native_zip_plaintext") != second.source
            or source_identities != (source_identity(s0), source_identity(s1))
            or contract.read_bytes() != raw_contract or evidence.read_bytes() != raw_evidence):
        raise ValueError("actual source input changed during physical-only verification")
    return {"result": "RED" if errors else "GREEN", "layer": "bounded-physical-S0-S1-and-passive-cold-readback",
            "player_saved_id": str(first.player_id), "S0": first.source, "S1": second.source,
            "physical_dates": {"S0": first.physical_date, "S1": second.physical_date},
            "war_saved_id": str(second.atoms["djcg_war"].identity),
            "references": {k: {"kind": second.atoms[k].kind, "identity": str(second.atoms[k].identity)} for k in (*GUI_STANDALONE_REFERENCES, *GUI_PHYSICAL_AFTER_REFS)},
            "actual_total_debit_saved_raw": {k: str(v) for k, v in deltas.items()},
            "saved_fixed_point_divisor": "100000", "price_preview_comparison": "OBSERVED" if preview_verified else "NOT_RUN",
            "native_selected_tuple": selected, "contract_sha256": hashlib.sha256(raw_contract).hexdigest(),
            "evidence_sha256": hashlib.sha256(raw_evidence).hexdigest(), "errors": errors,
            "boundary": "Bounded real passive script war/goal/participant/resource snapshots in physical Saves plus fresh current-world readback; not an independent full War-table AST. Operator-origin exact source adoption, SAVE, native action and cold Load/lifecycle remain separately authenticated inputs. No phase2/3, marker-only Load proof, Core War/money inference, completed matrix, general Save, Native ABI or whole-product credit. Missing preview comparison remains NOT_RUN."}


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, action="append", default=[])
    parser.add_argument("--contract", type=Path, action="append", default=[])
    parser.add_argument("--aggregate", action="store_true", help="three ordered --log/--contract pairs; exact original 72-marker union")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--gui-save-before", type=Path)
    parser.add_argument("--gui-save-after", type=Path)
    parser.add_argument("--gui-evidence", type=Path)
    parser.add_argument("--gui-contract", type=Path)
    parser.add_argument("--physical-s0", type=Path)
    parser.add_argument("--physical-s1", type=Path)
    parser.add_argument("--physical-evidence", type=Path)
    parser.add_argument("--physical-contract", type=Path)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report already exists; use a fresh output")
    result: SingleReport | AggregateReport | InvalidReport | GuiSaveReport | dict[str, object]
    try:
        gui_inputs = (args.gui_save_before, args.gui_save_after, args.gui_evidence, args.gui_contract)
        physical_inputs = (args.physical_s0, args.physical_s1, args.physical_evidence, args.physical_contract)
        if any(path is not None for path in physical_inputs):
            if not all(path is not None for path in physical_inputs) or any(path is not None for path in gui_inputs) or args.log or args.contract or args.aggregate:
                raise ValueError("physical S0/S1 needs exactly four separate inputs and excludes legacy phase modes")
            result = verify_physical_saves(*physical_inputs)
        elif any(path is not None for path in gui_inputs):
            if not all(path is not None for path in gui_inputs) or args.log or args.contract or args.aggregate:
                raise ValueError("GUI physical-save mode needs exactly four GUI inputs and excludes log/aggregate modes")
            result = verify_gui_saves(*gui_inputs)
        elif len(args.log) != len(args.contract):
            raise ValueError("each log needs its own corresponding contract")
        elif args.aggregate:
            result = aggregate(list(zip(args.log, args.contract, strict=True)))
        elif len(args.log) == 1:
            result = verify(args.log[0], args.contract[0])
        else:
            raise ValueError("multiple logs require explicit --aggregate")
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        result = InvalidReport(result="RED", layer="fixture-input-rejected", errors=[str(error)], boundary=BOUNDARY)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
