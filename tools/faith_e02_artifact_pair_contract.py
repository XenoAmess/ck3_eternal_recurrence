"""Typed boundaries for two separately allocated C2 artifact experiments."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Literal, Protocol, TypeAlias, TypedDict, runtime_checkable

Json: TypeAlias = None | bool | int | float | str | list['Json'] | dict[str, 'Json']
Object: TypeAlias = dict[str, Json]
Arm: TypeAlias = Literal['personal', 'enshrine']
SAFE = 2**53 - 1
SAVE_SHA = '7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e'
SAVE_BYTES = 50210503
PLAYER = 15893
DATE = 51394920
RECIPIENTS = (15893, 10322)
ARTIFACT = 267
SITE = 26
EXE = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
PREVIOUS_PENDING_SHA = '0254962a7caed4186f5875cb534d85b47b4df604aae2a2f6a6722686daa296a6'
PREVIOUS_WORLD_SHA = 'c546d242d490a4c0ee85726e7f0e5c684d279c6561a6b77af57fff40d6df9b37'
CASE_PREFIX = 'faith-engine-e02-artifact-pair-'


class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str


class Knight(TypedDict):
    character_id: int
    rite_id: int
    faith_id: int
    raw_decimal: str
    original_breakdown: str
    raw_scale: int
    cache_generation_time_known: Literal[False]
    site_attribution_observed: Literal[False]


class Wallet(TypedDict):
    gold_raw_decimal: str
    prestige_raw_decimal: str
    piety_raw_decimal: str
    raw_scale: int


class Item(TypedDict):
    artifact_id: int
    personally_owned: bool
    equipped: bool
    equipped_slot_index: int | None
    effective_slot_index: int | None
    replacing_artifact_id: int | None
    can_equip: bool | None
    can_unequip: bool | None


class Quote(TypedDict):
    artifact_id: int
    holy_site_id: int
    effective_slot_index: int
    replacing_artifact_id: int | None
    preview_sha256: str
    original_effect_description: str
    original_disabled_tooltip: str


@dataclass(frozen=True)
class Frame:
    revision: int
    native_revision: int
    date: int
    player: int
    pid: int
    generation: int
    run_id: str


@dataclass(frozen=True)
class Draft:
    type_key: str
    artifact_id: int
    first_barony_id: int
    second_barony_id: int


@dataclass(frozen=True)
class Contract:
    arm: Arm
    pair_id: str
    machine_id: str
    save_path: str
    pair_root: Path
    prior_pending: Pin
    prior_result: Pin
    native_dll: Pin
    native_qualification: Pin
    dependencies: tuple[Pin, ...]
    draft: Draft | None
    max_calls: int


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
    def guard(self, reserve: int = 90) -> object: ...
    def remaining(self) -> float: ...
    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object: ...


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + ': object required')
    result: dict[str, object] = {}
    for key, item in value.items():
        require(type(key) is str, label + ': string keys required')
        result[str(key)] = item
    return result


def field(value: object, key: str) -> object:
    row = mapping(value, 'container')
    require(key in row, 'Missing required field: ' + key)
    return row[key]


def integer(value: object, label: str, low: int = 0, high: int = SAFE) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(label + ': exact bounded integer required, bool/float forbidden')
    return value


def boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(label + ': exact boolean required')
    return value


def text(value: object, label: str, *, empty: bool = False) -> str:
    if type(value) is not str or (not empty and not value) or '\0' in value:
        raise ValueError(label + ': actual string required')
    return value


def sha(value: object) -> str:
    result = text(value, 'SHA256')
    require(re.fullmatch('[0-9a-f]{64}', result) is not None, 'Canonical lowercase SHA256 required')
    return result


def array(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise ValueError(label + ': JSON array required, no tuple alias')
    return list(value)


def json_value(value: object) -> Json:
    if value is None or type(value) in (str, bool, int):
        if value is None or isinstance(value, (str, bool, int)):
            return value
    if type(value) is float:
        require(math.isfinite(value), 'Nonfinite JSON number forbidden')
        return value
    if type(value) is list:
        return [json_value(item) for item in value]
    row = mapping(value, 'JSON value')
    return {key: json_value(item) for key, item in row.items()}


def object_value(value: object) -> Object:
    row = mapping(value, 'JSON object')
    return {key: json_value(item) for key, item in row.items()}


def encode(value: object) -> bytes:
    def safe(item: Json) -> None:
        if type(item) is int:
            require(-SAFE <= item <= SAFE, 'JSON output integer exceeds JS safe range; use named canonical decimal field')
        elif isinstance(item, list):
            for child in item: safe(child)
        elif isinstance(item, dict):
            for child in item.values(): safe(child)
    safe(json_value(value))
    return (json.dumps(json_value(value), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def read(path: Path) -> Object:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in pairs:
            require(key not in out, 'Duplicate JSON key: ' + key)
            out[key] = value
        return out
    raw: object = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique)
    return object_value(raw)


def digest(value: object) -> str:
    return hashlib.sha256(encode(value).rstrip(b'\n')).hexdigest()


def pin(path: Path) -> Pin:
    path = path.resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def parse_pin(value: object, *, verify: bool = True) -> Pin:
    row = mapping(value, 'file pin')
    require(set(row) == {'path', 'bytes', 'sha256'}, 'Exact pin fields required')
    result: Pin = {'path': text(row['path'], 'pin path'), 'bytes': integer(row['bytes'], 'pin bytes'),
                   'sha256': sha(row['sha256'])}
    path = Path(result['path'])
    require(path.is_absolute() and not path.is_symlink(), 'Absolute regular pinned file required')
    if verify:
        require(path.is_file() and pin(path) == result, 'Pinned file identity changed: ' + str(path))
    return result


def write_once(path: Path, value: object) -> Pin:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encode(value))
        stream.flush()
        import os
        os.fsync(stream.fileno())
    return pin(path)


def nullable_id(value: object, label: str) -> int | None:
    return None if value is None else integer(value, label, 0, 2**32-2)


def frame(value: object, run_id: str) -> Frame:
    row = mapping(value, 'actual snapshot')
    for key, expected in {'paused': True, 'map_ready': True, 'backend_id': 'native-headless',
                          'source': 'injected-dll-named-pipe', 'episode_projection': 'native_campaign'}.items():
        require(type(row.get(key)) is type(expected) and row.get(key) == expected, 'Actual snapshot admission: ' + key)
    require(field(row, 'active_event') is None and field(row, 'pending_character_interaction') is None,
            'Native interruption must be handled before controlled artifact actions')
    played = mapping(field(row, 'played_character'), 'played actor')
    require(field(played, 'alive') is True and field(played, 'source') == 'native', 'Actual living player required')
    diagnostic = mapping(field(row, 'diagnostics'), 'actual diagnostics')
    hello = mapping(field(diagnostic, 'hello'), 'actual hello')
    managed = mapping(field(row, 'managed_campaign_run_binding'), 'allocated managed run')
    require(field(managed, 'run_id') == run_id and field(diagnostic, 'pipe_name') == field(managed, 'bridge_pipe'),
            'The real allocated run/pipe, not an invented retry nonce, must own this scene')
    sha(field(managed, 'frozen_argv_sha256'))
    pid = integer(field(diagnostic, 'bridge_pid'), 'actual PID', 1, 2**31-1)
    gen = integer(field(diagnostic, 'connection_generation'), 'actual generation', 1)
    require(integer(field(hello, 'pid'), 'hello PID', 1) == pid and
            integer(field(hello, 'connection_generation'), 'hello generation', 1) == gen and
            field(hello, 'ck3_build_match') is True and field(hello, 'expected_ck3_version') == '1.20.0.4' and
            text(field(hello, 'expected_ck3_sha256'), 'EXE').lower() == EXE, 'Actual exact4 owner hello differs')
    return Frame(integer(field(row, 'revision'), 'public revision', 1),
                 integer(field(row, 'native_revision'), 'native revision', 1),
                 integer(field(row, 'date_raw'), 'actual date', 0, 2**31-1),
                 integer(field(played, 'character_id'), 'played fullID', 1, 2**32-2), pid, gen, run_id)


def knight(value: object, owner: Frame, target: int) -> Knight:
    row = mapping(value, 'current KnightEffectiveness')
    for key in ('available', 'read_only', 'two_pass_stable', 'own_actor_context_verified'):
        require(field(row, key) is True, 'Actual backed KnightEffectiveness unavailable: ' + key)
    require(field(row, 'schema') == 'ck3_12004_character_knight_effectiveness_v1' and
            field(row, 'callback_provenance') == 'exact4_native' and field(row, 'game_version') == '1.20.0.4' and
            text(field(row, 'executable_sha256'), 'EXE').lower() == EXE, 'KnightEffectiveness provenance differs')
    require(integer(field(row, 'snapshot_revision'), 'native revision', 1) == owner.native_revision and
            integer(field(row, 'date_raw'), 'native date') == owner.date and
            integer(field(row, 'played_character_id'), 'native played actor') == owner.player and
            integer(field(row, 'character_id'), 'target fullID') == target, 'KnightEffectiveness crossed actor/frame')
    for key in ('modifier_cache_refreshed', 'cache_generation_time_known', 'site_attribution_observed',
                'gameplay_command_submitted', 'raw_pointer_fields_persisted'):
        require(field(row, key) is False, 'No invented refresh, attribution or mutation: ' + key)
    require(field(row, 'selected_site_contribution_raw') is None and field(row, 'script_cache_rng_effects') == 'unknown',
            'Source attribution remains unknown')
    require(integer(field(row, 'raw_scale'), 'raw scale') == 100000, 'Native raw scale changed')
    raw = integer(field(row, 'knight_effectiveness_raw'), 'signed native Knight raw', -(2**63), 2**63-1)
    original = text(field(row, 'actual_knight_effectiveness_breakdown'), 'native original text', empty=True)
    require(len(original.encode('utf-8')) <= 32768, 'Native text is not the complete bounded original')
    return {'character_id': target, 'rite_id': integer(field(row, 'rite_id'), 'actual Rite', 0, 2**32-2),
            'faith_id': integer(field(row, 'faith_id'), 'actual Faith', 0, 2**32-2),
            'raw_decimal': str(raw), 'original_breakdown': original, 'raw_scale': 100000,
            'cache_generation_time_known': False, 'site_attribution_observed': False}


def wallet(value: object) -> Wallet:
    row = mapping(value, 'wallet frame')
    results: list[str] = []
    for name in ('gold', 'prestige', 'piety'):
        item = mapping(field(row, 'played_character_' + name), name)
        require(integer(field(item, 'scale'), 'wallet scale') == 100000, 'Wallet scale differs')
        results.append(str(integer(field(item, 'raw'), 'wallet signed raw', -(2**63), 2**63-1)))
    return {'gold_raw_decimal': results[0], 'prestige_raw_decimal': results[1],
            'piety_raw_decimal': results[2], 'raw_scale': 100000}


def item(value: object, owner: Frame) -> Item:
    row = mapping(value, 'personal item')
    require(field(row, 'available') is True and field(row, 'read_only') is True and
            field(row, 'loaded_source_pins_verified') is True, 'Actual personal item unavailable')
    require(integer(field(row, 'requested_artifact_id'), 'requested item') == ARTIFACT and
            integer(field(row, 'played_character_id'), 'item player') == owner.player and
            integer(field(row, 'date_raw'), 'item date') == owner.date, 'Personal item crossed scene')
    owned = boolean(field(row, 'personally_owned'), 'owned')
    require(owned and field(row, 'inventory_artifact') is True, 'The artifact must remain personally owned')
    equip = boolean(field(row, 'equipped'), 'equipped')
    return {'artifact_id': ARTIFACT, 'personally_owned': owned, 'equipped': equip,
            'equipped_slot_index': nullable_id(field(row, 'equipped_slot_index'), 'equipped slot'),
            'effective_slot_index': nullable_id(field(row, 'effective_slot_index'), 'effective slot'),
            'replacing_artifact_id': nullable_id(field(row, 'replacing_artifact_id'), 'replacing artifact'),
            'can_equip': None if field(row, 'can_equip_in_effective_slot') is None else boolean(row['can_equip_in_effective_slot'], 'can equip'),
            'can_unequip': None if field(row, 'can_unequip') is None else boolean(row['can_unequip'], 'can unequip')}


def parse_contract(value: object) -> Contract:
    row = mapping(value, 'paired artifact contract')
    keys = {'schema', 'product', 'case', 'arm', 'pair_id', 'machine_id', 'saved_input', 'pair_evidence_root',
            'artifact_id', 'holy_site_id', 'recipient_ids', 'metric', 'native_cohort', 'previous_enshrine',
            'draft', 'dependencies', 'max_public_calls', 'profile'}
    require(set(row) == keys, 'Exact pair contract fields required; missing/null are not aliases')
    arm_value = field(row, 'arm')
    require(arm_value in ('personal', 'enshrine') and type(arm_value) is str, 'Named arm required')
    arm: Arm = 'personal' if arm_value == 'personal' else 'enshrine'
    require(row['schema'] == 'faith-e02-artifact-pair-case-v1' and row['product'] == 'faith-engine' and
            row['case'] == CASE_PREFIX + arm + '-v1', 'Public product/case identity differs')
    pair_id = text(row['pair_id'], 'pair ID')
    require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,79}', pair_id) is not None, 'Portable pair identity required')
    saved = mapping(row['saved_input'], 'same C2 mother')
    require(set(saved) == {'save', 'bytes', 'sha256', 'player_id', 'date_raw'}, 'Exact original saved input required')
    require(integer(saved['bytes'], 'save bytes') == SAVE_BYTES and sha(saved['sha256']) == SAVE_SHA and
            integer(saved['player_id'], 'saved player') == PLAYER and integer(saved['date_raw'], 'saved date') == DATE,
            'Both arms must restore the exact original C2 mother')
    require(integer(row['artifact_id'], 'artifact fullID') == ARTIFACT and
            integer(row['holy_site_id'], 'site fullID') == SITE and row['metric'] == 'knight_effectiveness_raw',
            'Finite artifact/site/named Knight metric only')
    ids = [integer(x, 'recipient fullID', 1, 2**32-2) for x in array(row['recipient_ids'], 'recipients')]
    require(ids == list(RECIPIENTS), 'Same two explicit actual recipients required in both arms')
    profile = mapping(row['profile'], 'vanilla profile')
    require(set(profile) == {'enabled_mods', 'product_files'} and
            array(profile['enabled_mods'], 'enabled mods') == [] and array(profile['product_files'], 'product files') == [],
            'Independent original vanilla experiments only')
    history = mapping(row['previous_enshrine'], 'retained B14 known-world result')
    require(set(history) == {'pending', 'world_result'}, 'Do not omit retained 267 history to rotate a ledger')
    prior_pending, prior_result = parse_pin(history['pending']), parse_pin(history['world_result'])
    require(prior_pending['bytes'] == 1866 and prior_pending['sha256'] == PREVIOUS_PENDING_SHA and
            prior_result['bytes'] == 5338507 and prior_result['sha256'] == PREVIOUS_WORLD_SHA,
            'Bind the exact protected original B14 pending and independently known world result, not substituted history')
    cohort = mapping(row['native_cohort'], 'native cohort')
    require(set(cohort) == {'dll', 'qualification'}, 'Public qualified native cohort required')
    draft = None
    if row['draft'] is not None:
        d = mapping(row['draft'], 'optional A2 draft')
        require(arm == 'personal' and set(d) == {'type_key', 'artifact_id', 'barony_ids'}, 'A2 prelude belongs only to the personal arm')
        baronies = [integer(x, 'actual barony fullID', 0, 2**32-2) for x in array(d['barony_ids'], 'two baronies')]
        require(len(baronies) == 2 and baronies[0] != baronies[1], 'Two distinct exact candidate baronies required')
        draft = Draft(text(d['type_key'], 'native type key'), integer(d['artifact_id'], 'draft artifact', 0, 2**32-2),
                      baronies[0], baronies[1])
    return Contract(arm, pair_id, text(row['machine_id'], 'actual machine'), text(saved['save'], 'mother path'),
                    Path(text(row['pair_evidence_root'], 'stable pair evidence root')), prior_pending,
                    prior_result, parse_pin(cohort['dll']), parse_pin(cohort['qualification']),
                    tuple(parse_pin(x) for x in array(row['dependencies'], 'source dependencies')), draft,
                    integer(row['max_public_calls'], 'finite call cap', 32, 96))
