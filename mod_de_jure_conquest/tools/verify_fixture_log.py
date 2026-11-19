"""Verify existing fixture logs, including three fresh tiers; never launch or sign off."""

from __future__ import annotations

import argparse
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
from typing import Literal, Sequence, TypedDict

from gen_acceptance_fixture import BEGIN_MARKER, CLAIMS_EXCLUDED, DONE_MARKER, GUI_BASE_VALUES, GUI_REFERENCES, GUI_RELOAD_VALUES, TIERS, Tier, expected_markers, reviewed_tier
from inspect_ck3_save_character_scope import _anonymous_records
from inspect_ck3_save_player_topology import SaveInputIdentity, _numeric_records, _player_records, _save_input_identity, _save_text

BOUNDARY = "Log markers only; fresh scene/runtime/EXE, actual date/paused window, error.log, protected-storage and normal exit require separate evidence. No GUI/payment/SaveLoad/full-product qualification."


@dataclass(frozen=True)
class ParsedContract:
    tier: Tier
    layer: str
    markers: tuple[str, ...]
    claims_excluded: tuple[str, ...]


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
    return ParsedContract(tier, "scripted-war-production-CB", tuple(markers), tuple(exclusions))


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
    return {
        "result": "RED" if errors else "GREEN", "layer": definition.layer,
        "player_history_id": 1128, "tier": definition.tier,
        "expected_pass_count": len(definition.markers), "observed_pass_count": sum(passes.values()),
        "observed_marker_counts": dict(sorted(passes.items())), "errors": errors,
        "diagnostic_readbacks": diagnostics,
        "diagnostic_boundary": "Read-only probe booleans only, not original PASS credit or a proved unique cause. Actual scope IDs/date remain in the bound raw log.",
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

    def value(self, key: str) -> int:
        atom = self.atoms[key]
        if atom.kind != "value":
            raise ValueError(f"{key} must be a physical saved value, found {atom.kind}")
        return atom.identity


class ArtifactEvidence(TypedDict):
    kind: str
    path: str
    sha256: str


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


def read_saved_point(path: Path, phase: int, tier_value: int) -> SavedPoint:
    try:
        source = _save_input_identity(path, native_zip=True)
        played, current = _player_records(path, native_zip=True)
        if len(current) != 1 or not any(row.get("character_id") == current[0] for row in played):
            raise ValueError("physical save needs one current played character and its actual played-character record")
        version: str | None = None
        with _save_text(path, native_zip=True) as stream:
            for line in stream:
                match = re.fullmatch(r'\s*version="([^"\n]+)"\s*', line)
                if match:
                    version = match.group(1)
                    break
        if version != "1.21.0.3":
            raise ValueError("physical save version is not reviewed 1.21.0.3")
        root_block: str | None = None
        for level, identity, block in _numeric_records(path, native_zip=True):
            if level == 1 and identity == current[0] and "alive_data={" in block:
                root_block = block
                break
        if root_block is None:
            raise ValueError("actual current player living record is missing")
        atoms: dict[str, SavedAtom] = {}
        for block in _anonymous_records(root_block):
            names = re.findall(r'^\s*flag="(djcg_[^"]+)"$', block, re.MULTILINE)
            if not names:
                continue
            if len(names) != 1 or names[0] in atoms:
                raise ValueError("duplicate or ambiguous GUI observer saved variable")
            kinds = re.findall(r'^\s*type=([A-Za-z0-9_]+)$', block, re.MULTILINE)
            identities = re.findall(r'^\s*identity=(-?(?:0|[1-9][0-9]*))$', block, re.MULTILINE)
            if len(kinds) != 1 or len(identities) != 1 or abs(int(identities[0])) > 2**63 - 1:
                raise ValueError("saved observer atom must have one typed signed64 decimal identity")
            atoms[names[0]] = SavedAtom(kinds[0], int(identities[0]))
        expected = (*GUI_BASE_VALUES, *GUI_REFERENCES, *(GUI_RELOAD_VALUES if phase == 3 else ()))
        if not set(expected).issubset(atoms):
            raise ValueError("physical save lacks required observer values or references")
        result = SavedPoint(source, current[0], atoms)
        for key in (*GUI_BASE_VALUES, *(GUI_RELOAD_VALUES if phase == 3 else ())):
            result.value(key)
        if result.value("djcg_phase") != phase * 100000 or result.value("djcg_tier") != tier_value * 100000:
            raise ValueError("physical save phase/tier differs from the actual observer contract")
        for key in GUI_REFERENCES:
            if atoms[key].kind == "value" or atoms[key].identity <= 0:
                raise ValueError("physical saved object references must retain typed positive identities")
        if atoms["djcg_primary"].kind != "char" or atoms["djcg_secondary"].kind != "char" or len({current[0], atoms["djcg_primary"].identity, atoms["djcg_secondary"].identity}) != 3:
            raise ValueError("physical player/primary/secondary character identities are not distinct")
        if _save_input_identity(path, native_zip=True) != source:
            raise ValueError("physical saved source changed during observation")
        return result
    except zipfile.BadZipFile as error:
        raise ValueError(f"physical save ZIP/CRC invalid: {error}") from error


def verify_gui_saves(before: Path, after: Path, evidence: Path, contract: Path) -> GuiSaveReport:
    if before.resolve() == after.resolve():
        raise ValueError("two distinct physical Save files are required")
    raw_contract = contract.read_bytes()
    definition: object = json.loads(raw_contract)
    if not isinstance(definition, dict) or definition.get("schema") != "djc.gui-ordinary-save.v1":
        raise ValueError("GUI companion contract schema differs")
    tier = reviewed_tier(definition.get("tier"))
    if tier == "all":
        raise ValueError("GUI companion must bind one completed tier")
    tier_index, tier_row = next((index, row) for index, row in enumerate(TIERS) if row[0] == tier)
    if type(definition.get("player_history_id")) is not int or definition.get("player_history_id") != 1128 or type(definition.get("tier_value")) is not int or definition.get("tier_value") != tier_index + 1:
        raise ValueError("GUI companion actor/tier identity differs")
    if definition.get("goal") != tier_row[1] or definition.get("casus_belli") != tier + "_de_jure_greatwar":
        raise ValueError("GUI companion goal or CB differs")
    for field, expected in (("base_value_variables", GUI_BASE_VALUES), ("reload_value_variables", GUI_RELOAD_VALUES), ("reference_variables", GUI_REFERENCES)):
        if string_list(definition.get(field), field) != list(expected):
            raise ValueError("GUI companion saved-variable contract differs")
    if any(definition.get(key) is not True for key in ("ordinary_gui_required", "same_completed_matrix_world_required", "same_paused_date_required")):
        raise ValueError("GUI companion must retain ordinary same-world paused GUI obligations")
    for key, expected_number in (("max_extra_natural_days", 0), ("save_before_reload_phase", 2), ("save_after_reload_phase", 3)):
        if type(definition.get(key)) is not int or definition.get(key) != expected_number:
            raise ValueError("GUI companion day/phase contract differs")
    if definition.get("native_qualification") != "NOT_GRANTED" or definition.get("live") != "NOT_RUN":
        raise ValueError("GUI companion metadata cannot grant Native or live qualification")
    raw_evidence = evidence.read_bytes()
    value: object = json.loads(raw_evidence)
    if not isinstance(value, dict) or value.get("schema") != "djc.gui-physical-save-evidence.v1":
        raise ValueError("actual GUI evidence schema differs")
    if value.get("machine_id") != "desktop-3fevhd2-1c74096080" or value.get("game_version") != "1.21.0.3" or type(value.get("game_build")) is not int or value.get("game_build") != 26785313 or value.get("exe_sha256") != "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28" or value.get("tier") != tier:
        raise ValueError("actual GUI source machine/build/EXE/tier identity differs")
    if value.get("ordinary_gui_declaration") is not True or value.get("same_completed_matrix_world") is not True or value.get("paused_same_date") is not True:
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
    if method == "cold_process_load":
        required_kinds.add("process_lifecycle")
    if {row["kind"] for row in artifacts} != required_kinds or len(artifacts) != len(required_kinds):
        raise ValueError("one exact artifact for each real GUI action/state is required")
    first = read_saved_point(before, 2, tier_index + 1)
    second = read_saved_point(after, 3, tier_index + 1)
    if value.get("loaded_save_sha256") != first.source["sha256"]:
        raise ValueError("actual Load record must bind the exact first physical saved bytes")
    if first.player_id != second.player_id:
        raise ValueError("physical saved player identity changed")
    errors = []
    for key in (*GUI_BASE_VALUES[1:], *GUI_REFERENCES):
        if first.atoms[key] != second.atoms[key]:
            errors.append(f"saved observer value/reference changed across actual load: {key}")
    for name in ("gold", "prestige", "piety"):
        if first.value("djcg_after_" + name) != second.value("djcg_reload_" + name):
            errors.append(f"actual reloaded {name} differs from saved after-GUI value")
    if first.value("djcg_date") != second.value("djcg_reload_date"):
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
    if _save_input_identity(before, native_zip=True) != first.source or _save_input_identity(after, native_zip=True) != second.source or evidence.read_bytes() != raw_evidence or contract.read_bytes() != raw_contract:
        raise ValueError("actual source input changed during GUI/save verification")
    return {
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
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report already exists; use a fresh output")
    result: SingleReport | AggregateReport | InvalidReport | GuiSaveReport
    try:
        gui_inputs = (args.gui_save_before, args.gui_save_after, args.gui_evidence, args.gui_contract)
        if any(path is not None for path in gui_inputs):
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
