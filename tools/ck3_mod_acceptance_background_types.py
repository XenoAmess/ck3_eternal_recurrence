"""Validated JSON boundary shared by the new background refusal protocol."""
from __future__ import annotations
import math,os,re,subprocess
import ast
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final, Literal, TypeAlias, TypedDict, Protocol, runtime_checkable
from types import ModuleType
from pathlib import Path

JsonValue: TypeAlias = None | bool | int | float | str | list['JsonValue'] | dict[str,'JsonValue']
JsonObject: TypeAlias = dict[str,JsonValue]

class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str

CONTROL_QUEUE_MODULE_ORDER_V1: Final[tuple[str, ...]] = (
    'ck3_mod_acceptance_keeper',
    'ck3_mod_acceptance_background_types',
    'steam_offline_state_contract',
    'steam_offline_native_profiles',
    'steam_offline_native_provider_v1',
    'steam_offline_state_probe',
    'ck3_live_run_id',
    'ck3_mod_acceptance_fresh_machine_bootstrap',
    'ck3_mod_acceptance_steam_gate',
    'ck3_mod_acceptance_launcher',
    'ck3_mod_acceptance_queue',
)


class ControlQueueBindingV1(TypedDict):
    """Python objects for one private binding; never a persisted JSON receipt."""
    refs: dict[str, FilePin]
    module: ModuleType
    modules: dict[str, ModuleType]


class ProcessGeneration(TypedDict):
    pid: int
    birth_filetime: str

class PreviousRefusalClosure(TypedDict):
    mode: Literal['previous-shared-background-supervisor-admission-refused']
    actual_process_inventory: JsonObject
    failure_cleanup: JsonObject

def json_value(value: object) -> JsonValue:
    if value is None or type(value) in (str,bool,int):
        if value is None or isinstance(value,(str,bool,int)):return value
    if type(value) is float and isinstance(value,float) and math.isfinite(value):return value
    if isinstance(value,list):return [json_value(item) for item in value]
    if isinstance(value,dict):
        out: JsonObject={}
        for key,item in value.items():
            if not isinstance(key,str):raise ValueError('JSON object key must be string')
            out[key]=json_value(item)
        return out
    raise ValueError('Value is outside the finite JSON type domain')

def json_object(value: object) -> JsonObject:
    result=json_value(value)
    if not isinstance(result,dict):raise ValueError('JSON metadata object required')
    return result

def file_pin(value: object) -> FilePin:
    row=json_object(value)
    path,size,digest=row.get('path'),row.get('bytes'),row.get('sha256')
    if not isinstance(path,str) or not path or type(size) is not int or not isinstance(size,int) or size<0:
        raise ValueError('Exact file path/byte-count required')
    if not isinstance(digest,str) or re.fullmatch('[0-9a-f]{64}',digest) is None:
        raise ValueError('Exact file SHA256 required')
    return FilePin(path=path,bytes=size,sha256=digest)

def keyed_file_pin(key: object, value: object) -> FilePin:
    if not isinstance(key, str) or not key or chr(0) in key or not Path(key).is_absolute():
        raise ValueError('Absolute selected file key required')
    row = json_object(value)
    if set(row) not in ({'bytes', 'sha256'}, {'path', 'bytes', 'sha256'}):
        raise ValueError('Exact keyed file pin fields required')
    if 'path' in row:
        declared = row['path']
        if not isinstance(declared, str) or declared != key:
            raise ValueError('Declared file path differs from selected key')
        return file_pin(row)
    return file_pin({**row, 'path': key})


def previous_refusal(value: object) -> PreviousRefusalClosure:
    row=json_object(value)
    if row.get('mode')!='previous-shared-background-supervisor-admission-refused':raise ValueError('Refusal closure mode')
    inventory=json_object(row.get('actual_process_inventory'))
    cleanup=json_object(row.get('failure_cleanup'))
    if inventory.get('blockers')!=[]:raise ValueError('Unresolved process inventory')
    file_pin(cleanup.get('close'))
    evidence=json_object(cleanup.get('original_evidence'))
    for item in evidence.values():file_pin(item)
    if (cleanup.get('administrative_resource_admission_only') is not True
            or cleanup.get('typed_normal_exit_proven') is not False
            or cleanup.get('original_host_exit_code') is not None
            or cleanup.get('original_ck3_exit_code') is not None):
        raise ValueError('Administrative refusal cannot invent normal/game exit')
    for name in ('host_started','native_session_started','game_started','normal_close_qualified','business_pass'):
        if cleanup.get(name) is not False:raise ValueError('Refusal cannot invent host/business credit')
    return PreviousRefusalClosure(mode='previous-shared-background-supervisor-admission-refused',
        actual_process_inventory=inventory,failure_cleanup=cleanup)

def text_field(row: JsonObject, key: str) -> str:
    value=row.get(key)
    if not isinstance(value,str) or not value:raise ValueError('Nonempty string required: '+key)
    return value

def object_field(row: JsonObject, key: str) -> JsonObject:
    return json_object(row.get(key))


CONTINUOUS14_PASSIVE_STORY_TYPES_V1: Final[tuple[str, ...]] = (
    'xfma_observer',
    'xfma_spot_e1_observer',
    'xfma_spot_e2_observer',
    'xfma_spot_e3_observer',
    'xfma_derivatives_e1_observer',
    'xfma_derivatives_e2_observer',
    'xfma_lifecycle_e1_observer',
    'xfma_lifecycle_e2_observer',
    'xfma_inheritance_e1_observer',
    'xfma_inheritance_e2_observer',
    'xfma_cold_reload_e1_observer',
    'xfma_cold_reload_e2_observer',
    'xfma_news_crisis_e1_observer',
    'xfma_news_crisis_e2_observer',
    'xfma_ai_capacity_e1_observer',
    'xfma_ai_capacity_e2_observer',
    'xfma_market_evolution_e1_observer',
    'xfma_market_evolution_e2_observer',
    'xfma_market_evolution_e3_observer',
    'xfma_market_evolution_e4_observer',
    'xfma_market_evolution_e5_observer',
    'xfma_delisting_gui_e1_observer',
    'xfma_delisting_gui_e2_observer',
    'xfma_market_evolution_day_record',
    'xfma_market_evolution_coin_record',
    'xfma_ai_capacity_day_record',
)


CONTINUOUS14_CONTRACT_V1: Final[JsonObject] = {
    'schema': 'ck3-continuous14-diagnostic-contract-v2', 'days': 14, 'raw_hours': 336,
    'speed': 1, 'timeout_seconds': 240, 'maximum_polls': 480, 'poll_interval_seconds': 0.25,
    'maximum_full_bytes': 4 * 1024 * 1024, 'maximum_status_bytes': 65536, 'physical_saves': 2,
    'running_observation': 'native_date_sentinel_status_only', 'financial_daily_coverage_verified': False,
    'business_pass': False, 'performance_pass': False, 'product_release_pass': False,
}


def continuous14_contract_matches_v1(value: object) -> bool:
    """JSON domain equality, including bool/int/float distinctions at public boundaries."""
    try:
        return (type(value) is dict and json.dumps(value, sort_keys=True, allow_nan=False)
                == json.dumps(CONTINUOUS14_CONTRACT_V1, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError):
        return False


def continuous14_owner_v1(before: object, capabilities: object) -> JsonObject:
    """Live transport ownership only. This is not a running world/Full observation."""
    from xar_autoplayer.bridge.version_identity import florin_full_source
    baseline, caps = json_object(before), json_object(capabilities)
    source = florin_full_source(baseline, None)
    origin = object_field(baseline, 'diagnostics')
    owner = object_field(caps, 'diagnostics')
    advertised = caps.get('bridge_capabilities')
    if not isinstance(advertised, list) or any(type(name) is not str for name in advertised):
        raise ValueError('Continuous14 actual status capabilities must be explicit names')
    hello, initial_hello = object_field(owner, 'hello'), object_field(origin, 'hello')
    identity = ('pid', 'connection_generation', 'expected_ck3_version', 'expected_ck3_sha256',
                'game_adapter_id', 'ck3_build_match')
    if (owner.get('connected') is not True or type(owner.get('bridge_pid')) is not int
            or owner.get('bridge_pid') != source.game_pid
            or type(owner.get('connection_generation')) is not int
            or owner.get('connection_generation') != source.connection_generation
            or not isinstance(owner.get('pipe_name'), str) or not owner['pipe_name']
            or owner.get('pipe_name') != origin.get('pipe_name')
            or any(type(hello.get(key)) is not type(initial_hello.get(key))
                or hello.get(key) != initial_hello.get(key) for key in identity)
            or hello.get('connection_generation') != source.connection_generation
            or 'game.command.research-query-tactical-daily-sentinel-v1'
                not in advertised):
        raise ValueError('Continuous14 live status transport crossed its original PID/pipe/connection/HELLO')
    return {'bridge_capabilities': advertised, 'diagnostics': {'connected': owner['connected'],
        'bridge_pid': owner['bridge_pid'], 'connection_generation': owner['connection_generation'],
        'pipe_name': owner['pipe_name'], 'hello': hello}}


def continuous14_status_sample_v1(before: object, value: object, arm: object, previous_day: int,
                                   capabilities_before: object, capabilities_after: object) -> JsonObject | None:
    """One actual native slot read. No Full, actor/resource read, or financial-day inference."""
    from xar_autoplayer.bridge.version_identity import florin_full_source
    from xar_autoplayer.bridge.native_driver import (
        _normalize_tactical_daily_sentinel_status, _validate_tactical_daily_sentinel_stop)
    source = florin_full_source(before, None)
    owner_before = continuous14_owner_v1(before, capabilities_before)
    owner_after = continuous14_owner_v1(before, capabilities_after)
    actual = json_object(_normalize_tactical_daily_sentinel_status(value))
    armed = json_object(_normalize_tactical_daily_sentinel_status(arm))
    if type(previous_day) is not int or not 0 <= previous_day <= 14:
        raise ValueError('Continuous14 previous sample is not an exact bounded native day')
    count = actual.get('completed_daily_ticks')
    if type(count) is not int or not 0 <= count <= 14 or count not in (previous_day, previous_day + 1):
        raise ValueError('Continuous14 native status sample missing or rewound; no interpolation')
    if count < 14:
        expected = dict(armed)
        expected.update(last_observed_date_raw=source.date_raw + 24 * count, completed_daily_ticks=count)
        if actual != expected:
            raise ValueError('Continuous14 native status generation/date/flags changed or paused early')
    else:
        _validate_tactical_daily_sentinel_stop(dict(actual), arm_status=dict(armed),
            starting_date_raw=source.date_raw, target_date_raw=source.date_raw + 336,
            ending_date_raw=source.date_raw + 336, elapsed_days=14, speed=1,
            mode='terminal_or_sentinel', watch_army_ids=())
        if actual.get('trigger_reasons') != ['date_deadline'] or actual.get('intermediate_pause_count') != 0:
            raise ValueError('Continuous14 terminal was not the sole original native deadline pause')
    if len(json.dumps(actual, allow_nan=False).encode('utf-8')) > 65536:
        raise ValueError('Continuous14 actual status exceeds its finite 64KiB budget')
    if count == previous_day:
        return None  # Actual duplicate/zero read stays in wire; never becomes a missing sample.
    return {'day': count, 'status': actual, 'owner_before': owner_before, 'owner_after': owner_after}


def continuous14_endpoint_v1(before: object, after: object, arm: object, status: object) -> None:
    """Only the actual fresh paused endpoint can prove current world/date/actor identity."""
    from xar_autoplayer.bridge.version_identity import florin_full_source
    from xar_autoplayer.bridge.native_driver import (
        _normalize_tactical_daily_sentinel_status, _validate_tactical_daily_sentinel_stop)
    first, last = json_object(before), json_object(after)
    initial, ending = florin_full_source(first, None), florin_full_source(last, None)
    if ((ending.game_pid, ending.connection_generation, ending.played_character_id, ending.scope_sha256)
            != (initial.game_pid, initial.connection_generation, initial.played_character_id, initial.scope_sha256)
            or ending.date_raw != initial.date_raw + 336
            or ending.native_revision <= initial.native_revision or ending.public_revision <= initial.public_revision
            or last.get('local_player_id') != first.get('local_player_id')
            or type(last.get('speed')) is not int or last.get('speed') != 1):
        raise ValueError('Continuous14 fresh paused endpoint changed its original world/actor/date/speed')
    actual, armed = _normalize_tactical_daily_sentinel_status(status), _normalize_tactical_daily_sentinel_status(arm)
    _validate_tactical_daily_sentinel_stop(actual, arm_status=armed,
        starting_date_raw=initial.date_raw, target_date_raw=initial.date_raw + 336,
        ending_date_raw=ending.date_raw, elapsed_days=14, speed=1,
        mode='terminal_or_sentinel', watch_army_ids=())
    if actual.get('trigger_reasons') != ['date_deadline'] or actual.get('intermediate_pause_count') != 0:
        raise ValueError('Continuous14 fresh endpoint lacks its original sole native deadline')


FUTURES_NATURAL14_CASE_V1: Final = 'futures-natural-liquidity14'
FUTURES_NATURAL14_SCOPE_V1: Final = 'natural_futures_short_reduce_observed_cells_only'
FUTURES_NATURAL14_CONTRACT_V1: Final[JsonObject] = {
    'schema': 'ck3-futures-natural-liquidity14-contract-v1',
    'physical_save_maximum': 3, 'physical_save_max_bytes': 268435456,
    'prebusiness_baseline_saves': 1, 'continuous_interval_endpoint_saves': 2,
    'days': 14, 'short_lots': 1, 'short_leverage': 2, 'reduce_lots': 1,
    'reduce_position_id': 150, 'reduce_side': 'long', 'submitted_side': 'SELL',
    'cells': ['short', 'reduce'], 'cell_statuses': ['OBSERVED', 'NOT_OBSERVED'],
    'observer_arm': False, 'actor_change': False, 'financial_clock_credit': False,
    'force_counterparty_or_funds': False, 'derivatives_acceptance_credit': False,
}
FUTURES_NATURAL14_PHASES_V1: Final[list[JsonObject]] = [
    {'id': 'bind-natural-futures-baseline', 'at_day': 0, 'requirements': [
        'actual_latest_physical_source_and_new_same_date_baseline_complete_graph_bound',
        'actual_actor_primary_wallet_old_long150_contract_oracle_and_payment_presence_pinned',
        'actual_no_synthetic_funds_ai_override_observer_or_historical_replay',
        'actual_minimized_non_topmost_no_foreground_activation_for_entire_run']},
    {'id': 'retain-two-normal-sell-orders', 'at_day': 0, 'requirements': [
        'actual_new_short2x1_and_old_long150_reduce1_use_normal_fresh_gui_identities',
        'actual_order_ids_same_contract_sell_sides_own_wallet_reservations_and_fees_reconciled',
        'actual_second_physical_save_audit_raw_whole_retains_both_outcomes_without_forced_pending',
        'actual_missing_permission_or_reservation_recorded_without_replay_or_synthetic_success']},
    {'id': 'reconcile-natural-futures-terminal', 'at_day': 14, 'requirements': [
        'actual_single_original_arm_resume_and_fourteen_same_owner_native_status_samples',
        'actual_third_physical_save_audit_raw_whole_and_all_three_original_archives_pinned',
        'actual_short_and_reduce_cells_use_real_order_position_collateral_fee_counterparty_evidence',
        'actual_absent_fills_remain_not_observed_and_dates_alone_do_not_prove_trade_causality',
        'actual_no_financial_daily_performance_full_derivatives_or_whole_product_credit']},
]


def futures_natural14_contract_matches_v1(product: object, case: object, value: object) -> bool:
    if not isinstance(value, dict):
        return False
    config = value
    contract = config.get('futures_natural_liquidity14_contract')
    if not isinstance(contract, dict):
        return False
    integers = ('physical_save_maximum', 'physical_save_max_bytes', 'prebusiness_baseline_saves',
                'continuous_interval_endpoint_saves', 'days', 'short_lots', 'short_leverage',
                'reduce_lots', 'reduce_position_id')
    flags = ('observer_arm', 'actor_change', 'financial_clock_credit',
             'force_counterparty_or_funds', 'derivatives_acceptance_credit')
    phases = config.get('gui_phases')
    return (product == 'financial-markets' and case == FUTURES_NATURAL14_CASE_V1
        and config.get('product') == product and config.get('case_id') == case
        and config.get('schema') == 'ck3-mod-acceptance-product-case-v1'
        and config.get('execution_purpose') == 'product_acceptance'
        and config.get('clock_purpose') == 'continuous14_diagnostic'
        and config.get('acceptance_scope') == FUTURES_NATURAL14_SCOPE_V1
        and config.get('startup_mode') == 'saved_campaign'
        and config.get('product_loading', 'present') == 'present'
        and type(config.get('maximum_natural_days')) is int and config.get('maximum_natural_days') == 14
        and config.get('allow_actor_change') is False
        and config.get('pending_interaction_policy') == 'stop_at_boundary'
        and config.get('business_contract_applicable') is True
        and config.get('whole_product_release_pass') is False
        and continuous14_contract_matches_v1(config.get('continuous14_contract'))
        and contract == FUTURES_NATURAL14_CONTRACT_V1
        and all(type(contract.get(k)) is int for k in integers)
        and all(contract.get(k) is False for k in flags)
        and config.get('passive_story_types') == list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
        and isinstance(phases, list) and phases == FUTURES_NATURAL14_PHASES_V1
        and all(isinstance(p, dict) and type(p.get('at_day')) is int for p in phases)
        and not any(k in config for k in ('fixture_source', 'fixture_emitter', 'marker_inventory',
                                        'futures_gui_transactions_contract', 'redemption_gui_contract')))


def continuous14_case_scope_matches_v1(product: object, case: object, config: object) -> bool:
    if futures_natural14_contract_matches_v1(product, case, config):
        return True
    return (isinstance(config, dict) and product == 'financial-markets'
        and case == 'clock-cadence-continuous14' and config.get('maximum_natural_days') == 14
        and config.get('allow_actor_change', False) is False
        and config.get('acceptance_scope') == 'clock_cadence_diagnostic_only'
        and continuous14_contract_matches_v1(config.get('continuous14_contract')))


@dataclass(frozen=True)
class ProductAcceptancePurposeV1:
    machine_id: str
    run_id: str
    product: str
    case: str
    state_dir: Path
    bridge_pipe: str
    maximum_natural_days: int
    allow_actor_change: bool = False
    clock_purpose: Literal['one_day_acceptance', 'continuous14_diagnostic'] = 'one_day_acceptance'

    def __post_init__(self) -> None:
        if type(self.allow_actor_change) is not bool:
            raise ValueError('Exact product-purpose actor-observation boolean required')
        if self.clock_purpose not in ('one_day_acceptance', 'continuous14_diagnostic'):
            raise ValueError('Unknown product clock purpose')
        if self.clock_purpose == 'continuous14_diagnostic' and (
                self.product != 'financial-markets' or self.case not in ('clock-cadence-continuous14', FUTURES_NATURAL14_CASE_V1)
                or self.maximum_natural_days != 14 or self.allow_actor_change):
            raise ValueError('Continuous14 purpose requires its exact independent diagnostic case')


def _purpose_original(reference: object) -> tuple[FilePin, JsonObject]:
    pin = file_pin(reference)
    if set(json_object(reference)) != {'path', 'bytes', 'sha256'} or pin['bytes'] > 8 * 1024 * 1024:
        raise ValueError('Bounded exact product-purpose original required')
    path = Path(pin['path'])
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('Product-purpose original must be an absolute ordinary file')
    raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('Product-purpose original changed: ' + str(path))
    return pin, json_object(json.loads(raw))


def product_acceptance_purpose_v1(value: object, *, purpose_path: Path,
                                  host_path: Path, state_dir: Path,
                                  bridge_pipe: str) -> ProductAcceptancePurposeV1:
    """One Root-reviewed public prepared case; never an R05 progress admission."""
    row = json_object(value)
    if (set(row) != {'schema', 'purpose', 'machine_id', 'reviewed_context'}
            or row.get('schema') != 'ck3-product-acceptance-purpose-v1'
            or row.get('purpose') != 'product_acceptance'):
        raise ValueError('Explicit product acceptance purpose required')
    context_pin, context = _purpose_original(row['reviewed_context'])
    frozen_pin, frozen = _purpose_original(context.get('frozen_argv'))
    prepared_pin, prepared = _purpose_original(context.get('prepared_case'))
    _, contract = _purpose_original(prepared.get('contract'))
    run_root = purpose_path.resolve().parent
    run_id = text_field(context, 'run_id')
    machine_id = text_field(object_field(frozen, 'identity_allocation'), 'machine_id')
    product, case = text_field(context, 'product'), text_field(context, 'case')
    argv = strings_field(frozen, 'argv')

    def option(flag: str) -> str:
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise ValueError('Product-purpose frozen argv requires exactly one ' + flag)
        return argv[argv.index(flag) + 1]

    if (row.get('machine_id') != machine_id
            or context.get('schema') != 'ck3-mod-acceptance-run-context-v1'
            or context.get('reviewer') != '/root' or 'operator_delegation' in context
            or Path(context_pin['path']).resolve().parent != run_root
            or run_id != run_root.name or Path(text_field(context, 'run_dir')).resolve() != run_root
            or Path(frozen_pin['path']).resolve() != run_root / 'frozen-argv.json'
            or frozen.get('run_id') != run_id or frozen.get('mod_key') != product or frozen.get('cell') != case
            or prepared.get('schema') != 'ck3-mod-acceptance-prepared-case-v1'
            or prepared.get('product') != product or prepared.get('case') != case
            or context.get('case_inputs') != prepared.get('case_inputs')
            or frozen.get('runtime_manifest') != prepared.get('runtime_manifest')
            or contract.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or contract.get('product') != product or contract.get('case_id') != case
            or contract.get('execution_purpose') != 'product_acceptance'
            or len(argv) < 5 or Path(argv[4]).resolve() != host_path.resolve()
            or Path(option('--product-acceptance-purpose')).resolve() != purpose_path.resolve()
            or Path(option('--state-dir')).resolve() != state_dir.resolve()
            or Path(text_field(frozen, 'state_dir')).resolve() != state_dir.resolve()
            or option('--bridge-pipe') != bridge_pipe
            or Path(option('--output')).resolve() != run_root / 'native-report.json'):
        raise ValueError('Product-purpose crossed Root review, prepared case or original host/run/state/pipe')
    # The prepared object is pinned by both the reviewed context and the
    # allocator's original ready context, rather than selected by filename.
    ready = json_object(json.loads((run_root / 'ready-context.json').read_bytes()))
    if (ready.get('run_id') != run_id or ready.get('prepared_case') != prepared_pin
            or ready.get('frozen_argv') != frozen_pin):
        raise ValueError('Product-purpose differs from original allocated ready context')
    maximum = contract.get('maximum_natural_days')
    if type(maximum) is not int or not isinstance(maximum, int) or not 0 <= maximum <= 400:
        raise ValueError('Original product-purpose natural-day budget must be an integer from 0 through 400')
    allow_actor_change = contract.get('allow_actor_change', False)
    if type(allow_actor_change) is not bool or not isinstance(allow_actor_change, bool):
        raise ValueError('Exact original case allow_actor_change boolean required')
    clock_purpose = contract.get('clock_purpose', 'one_day_acceptance')
    if clock_purpose not in ('one_day_acceptance', 'continuous14_diagnostic'):
        raise ValueError('Unknown pinned product clock purpose')
    if (clock_purpose == 'continuous14_diagnostic') != (
            product == 'financial-markets' and case in ('clock-cadence-continuous14', FUTURES_NATURAL14_CASE_V1)):
        raise ValueError('Continuous14 purpose cannot be borrowed by another case')
    if clock_purpose == 'continuous14_diagnostic' and (
            maximum != 14 or allow_actor_change or not continuous14_case_scope_matches_v1(product, case, contract)):
        raise ValueError('Pinned continuous14 diagnostic bounds differ')
    admitted_clock_purpose: Literal['one_day_acceptance', 'continuous14_diagnostic'] = (
        'continuous14_diagnostic' if clock_purpose == 'continuous14_diagnostic' else 'one_day_acceptance')
    return ProductAcceptancePurposeV1(machine_id, run_id, product, case, state_dir.resolve(), bridge_pipe,
        maximum, allow_actor_change, admitted_clock_purpose)


def write_product_acceptance_purpose_v1(purpose_path: Path, reviewed_context: Path, *,
                                        host_path: Path, state_dir: Path,
                                        bridge_pipe: str) -> ProductAcceptancePurposeV1:
    raw = reviewed_context.read_bytes()
    context = json_object(json.loads(raw))
    _, frozen = _purpose_original(context.get('frozen_argv'))
    row: JsonObject = {'schema': 'ck3-product-acceptance-purpose-v1', 'purpose': 'product_acceptance',
        'machine_id': text_field(object_field(frozen, 'identity_allocation'), 'machine_id'),
        'reviewed_context': {'path': str(reviewed_context.resolve()), 'bytes': len(raw),
                             'sha256': hashlib.sha256(raw).hexdigest()}}
    purpose = product_acceptance_purpose_v1(row, purpose_path=purpose_path,
        host_path=host_path, state_dir=state_dir, bridge_pipe=bridge_pipe)
    with purpose_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return purpose


@dataclass
class ProductAcceptanceClockV1:
    purpose: ProductAcceptancePurposeV1
    start_date_raw: int | None = None
    actor: int | None = None
    bridge_pid: int | None = None
    generation: int | None = None
    last_date_raw: int | None = None
    continuous14_claimed: bool = False

    def observe(self, value: object) -> None:
        row = json_object(value)
        if row.get('map_ready') is not True or row.get('paused') is not True:
            return
        diagnostics = object_field(row, 'diagnostics')

        def positive(item: object) -> int:
            if type(item) is not int or not isinstance(item, int) or item <= 0:
                raise ValueError('Product-purpose clock requires an actual paused native map integer identity')
            return item

        date = positive(row.get('date_raw'))
        pid, generation = positive(diagnostics.get('bridge_pid')), positive(diagnostics.get('connection_generation'))
        if diagnostics.get('pipe_name') != self.purpose.bridge_pipe:
            raise ValueError('Product-purpose native pipe differs')
        # Loading can publish a ready map before the player object. Only that
        # explicit initial null waits; it cannot bind or advance this clock.
        if self.start_date_raw is None and 'played_character' in row and row['played_character'] is None:
            return
        actor = positive(object_field(row, 'played_character').get('character_id'))
        if self.start_date_raw is None:
            self.start_date_raw, self.actor, self.bridge_pid, self.generation = date, actor, pid, generation
        elif ((pid, generation) != (self.bridge_pid, self.generation)
                or actor != self.actor and not self.purpose.allow_actor_change):
            raise ValueError('Product-purpose native actor/process/generation changed')
        if self.last_date_raw is not None and date < self.last_date_raw:
            raise ValueError('Product-purpose actual native date rewound')
        # This records an observation only. Native action and independent
        # succession/head proofs remain the responsibility of their consumers.
        self.actor = actor
        self.last_date_raw = date

    def deadline(self, starting: object, target_date_raw: int, *, r05_scope_bound: bool) -> JsonObject:
        if self.purpose.clock_purpose != 'one_day_acceptance':
            raise ValueError('Continuous14 diagnostics cannot use the ordinary one-day route')
        if type(r05_scope_bound) is not bool:
            raise ValueError('Explicit R05 scope-presence boolean required')
        if r05_scope_bound:
            raise ValueError('Product acceptance and an R05 progress scope cannot share clock authority')
        self.observe(starting)
        row = json_object(starting)
        current = row.get('date_raw')
        start = self.start_date_raw
        if (start is None or type(current) is not int or not isinstance(current, int)
                or row.get('paused') is not True or row.get('map_ready') is not True
                or type(target_date_raw) is not int or current < start or (current - start) % 24
                or target_date_raw != current + 24):
            raise ValueError('Product acceptance permits only an original actual paused one-day request')
        endpoint = start + self.purpose.maximum_natural_days * 24
        if current >= endpoint:
            raise ValueError('Original product-acceptance natural-day budget exhausted')
        return {'schema': 'ck3-product-acceptance-clock-v1', 'run_id': self.purpose.run_id,
            'starting_date_raw': current, 'requested_target_date_raw': target_date_raw,
            'target_date_raw': target_date_raw, 'endpoint_date_raw': endpoint,
            'boundary_date_raw': endpoint, 'status': 'advance', 'policy_choices_changed': False}

    def continuous14_deadline(self, starting: object, target_date_raw: int, *, r05_scope_bound: bool) -> JsonObject:
        """Once, current+336, for the exact pinned diagnostic; never an AUTO admission."""
        if self.purpose.clock_purpose != 'continuous14_diagnostic' or r05_scope_bound is not False:
            raise ValueError('Continuous14 requires its independent purpose without an R05 scope')
        self.observe(starting)
        row = json_object(starting)
        current = row.get('date_raw')
        if (self.continuous14_claimed or type(current) is not int or current != self.start_date_raw
                or row.get('paused') is not True or row.get('map_ready') is not True
                or type(target_date_raw) is not int or target_date_raw != current + 336 or target_date_raw >= 2**31):
            raise ValueError('Continuous14 permits one original paused current+336 window only')
        self.continuous14_claimed = True
        return {'schema': 'ck3-product-continuous14-clock-v1', 'run_id': self.purpose.run_id,
            'clock_purpose': 'continuous14_diagnostic', 'starting_date_raw': current,
            'target_date_raw': target_date_raw, 'requested_days': 14, 'policy_choices_changed': False,
            'business_pass': False, 'performance_pass': False, 'product_release_pass': False}

def strings_field(row: JsonObject, key: str) -> list[str]:
    value=row.get(key)
    if not isinstance(value,list) or not value:raise ValueError('Nonempty string list required: '+key)
    result: list[str]=[]
    for item in value:
        if not isinstance(item,str) or not item:raise ValueError('String list required: '+key)
        result.append(item)
    return result

def environment(value: object) -> dict[str,str]:
    row=json_object(value)
    result: dict[str,str]={}
    for key,item in row.items():
        if not isinstance(item,str):raise ValueError('Environment string required')
        result[key]=item
    return result

def process_handle(process: 'subprocess.Popen[bytes]') -> int:
    # The original retained Popen handle, never a reopened PID handle.
    value=getattr(process,'_handle',None)
    if not isinstance(value,int) or isinstance(value,bool) or value<=0:
        raise ValueError('Original Windows Popen handle unavailable')
    return value


# Shared wire logging metadata. Missing legacy codec is interpreted only by
# the report/manifest reader; explicit null and unknown values never default.
WireEvidenceCodec: TypeAlias = Literal["plain", "gzip-members"]
WireEvidenceKind: TypeAlias = Literal["native-wire", "mcp-wire", "mcp-calls"]


class WireFileIdentity(TypedDict):
    provider: Literal["win32-file-id-info", "posix-fstat"]
    device: str
    inode: str


class WireEvidenceCommit(TypedDict):
    schema: Literal["ck3-wire-evidence-commit-v1"]
    wire_evidence_codec: Literal["gzip-members"]
    path: str
    stream_id: str
    file_identity: WireFileIdentity
    completed_physical_offset: str
    logical_bytes: str
    record_count: int
    last_member_physical_begin: str
    last_member_sha256: str


class WireEvidenceSource(TypedDict):
    path: str
    wire_evidence_codec: WireEvidenceCodec
    commit: WireEvidenceCommit | None


def wire_evidence_codec(value: object) -> WireEvidenceCodec:
    if type(value) is str and value == "plain":
        return "plain"
    if type(value) is str and value == "gzip-members":
        return "gzip-members"
    raise ValueError("wire_evidence_codec must be plain or gzip-members")


def wire_evidence_path(report_path: Path, kind: WireEvidenceKind,
                       codec: WireEvidenceCodec) -> Path:
    if kind not in ("native-wire", "mcp-wire", "mcp-calls"):
        raise ValueError("Unknown wire evidence kind")
    selected = wire_evidence_codec(codec)
    return report_path.with_suffix("." + kind + ".jsonl" +
                                   (".gz" if selected == "gzip-members" else ""))


def _wire_decimal(value: object, bits: int, *, positive: bool = False) -> str:
    if (not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None or
            int(value) >= 1 << bits or positive and int(value) == 0):
        raise ValueError("Canonical bounded wire decimal required")
    return value


def wire_file_identity_value(value: object) -> WireFileIdentity:
    row = json_object(value)
    if set(row) != {"provider", "device", "inode"}:
        raise ValueError("Exact wire file identity fields required")
    provider = row["provider"]
    device = _wire_decimal(row["device"], 64)
    inode = _wire_decimal(row["inode"], 128, positive=True)
    if provider == "win32-file-id-info":
        return WireFileIdentity(provider="win32-file-id-info", device=device, inode=inode)
    if provider == "posix-fstat":
        return WireFileIdentity(provider="posix-fstat", device=device, inode=inode)
    raise ValueError("Unknown wire file identity provider")


@runtime_checkable
class _WireFileIdentityReader(Protocol):
    def file_identity(self, handle: int, *, allow_empty: bool = False) -> object: ...


def wire_file_identity(fd: int) -> WireFileIdentity:
    """Borrow the caller's open file; never close its fd or native handle."""
    if type(fd) is not int or fd < 0:
        raise ValueError("Actual held wire fd required")
    if os.name == "nt":
        import importlib
        import msvcrt
        module = importlib.import_module(
            "xar_autoplayer.bridge.native_loaded_provider_windows_v1")
        factory: object = getattr(module, "_Win32ReadsV1", None)
        if not callable(factory):
            raise ValueError("Shared native file identity provider unavailable")
        reader: object = factory()
        if not isinstance(reader, _WireFileIdentityReader):
            raise ValueError("Shared native file identity method unavailable")
        result = reader.file_identity(msvcrt.get_osfhandle(fd), allow_empty=True)
        if not isinstance(result, tuple) or len(result) != 3:
            raise ValueError("Native file identity tuple unavailable")
        volume, identity, size = result
        if (type(volume) is not int or not isinstance(volume, int) or not 0 <= volume < 1 << 64 or
                not isinstance(identity, bytes) or len(identity) != 16 or not any(identity) or
                type(size) is not int or not isinstance(size, int) or size < 0):
            raise ValueError("Native FileIdInfo/GetFileSizeEx result invalid")
        return WireFileIdentity(provider="win32-file-id-info", device=str(volume),
                                inode=str(int.from_bytes(identity, "little")))
    observed = os.fstat(fd)
    return wire_file_identity_value({"provider": "posix-fstat",
        "device": str(observed.st_dev), "inode": str(observed.st_ino)})


def wire_evidence_commit(value: object) -> WireEvidenceCommit:
    row = json_object(value)
    if set(row) != {"schema", "wire_evidence_codec", "path", "stream_id", "file_identity",
            "completed_physical_offset", "logical_bytes", "record_count",
            "last_member_physical_begin", "last_member_sha256"}:
        raise ValueError("Exact wire commit fields required")
    if (row["schema"] != "ck3-wire-evidence-commit-v1" or
            wire_evidence_codec(row["wire_evidence_codec"]) != "gzip-members"):
        raise ValueError("Wire commit schema/codec differs")
    path, stream_id, digest, count = (row["path"], row["stream_id"],
                                    row["last_member_sha256"], row["record_count"])
    if not isinstance(path, str) or not path or "\0" in path or not Path(path).is_absolute():
        raise ValueError("Absolute committed wire path required")
    if not isinstance(stream_id, str) or re.fullmatch("[0-9a-f]{32}", stream_id) is None:
        raise ValueError("Wire stream identity required")
    if not isinstance(digest, str) or re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise ValueError("Wire member SHA256 required")
    if not isinstance(count, int) or isinstance(count, bool) or not 0 < count < 1 << 53:
        raise ValueError("Safe positive wire record count required")
    end = _wire_decimal(row["completed_physical_offset"], 64, positive=True)
    logical = _wire_decimal(row["logical_bytes"], 64, positive=True)
    begin = _wire_decimal(row["last_member_physical_begin"], 64)
    if int(begin) >= int(end):
        raise ValueError("Completed member physical range invalid")
    return WireEvidenceCommit(schema="ck3-wire-evidence-commit-v1",
        wire_evidence_codec="gzip-members", path=path, stream_id=stream_id,
        file_identity=wire_file_identity_value(row["file_identity"]),
        completed_physical_offset=end, logical_bytes=logical, record_count=count,
        last_member_physical_begin=begin, last_member_sha256=digest)


def wire_evidence_source(report: object, report_path: Path,
                         declared_codec: WireEvidenceCodec) -> WireEvidenceSource:
    row = json_object(report)
    codec = wire_evidence_codec(row["wire_evidence_codec"]) if "wire_evidence_codec" in row else "plain"
    if codec != wire_evidence_codec(declared_codec):
        raise ValueError("Report wire codec differs from selected manifest")
    path = row.get("native_wire")
    if (not isinstance(path, str) or not path or "\0" in path or not Path(path).is_absolute() or
            Path(path).resolve().parent != report_path.resolve().parent):
        raise ValueError("Actual native wire must belong to allocated report directory")
    native_commit: WireEvidenceCommit | None = None
    if codec == "gzip-members":
        commits = json_object(row.get("wire_evidence_commits"))
        if set(commits) != {"native-wire", "mcp-wire", "mcp-calls"}:
            raise ValueError("All three wire commit roles required")
        for kind, field in (("native-wire", "native_wire"),
                            ("mcp-wire", "mcp_wire"), ("mcp-calls", "mcp_calls")):
            value = commits[kind]
            if value is None:
                if kind == "native-wire":
                    raise ValueError("Native wire has no completed published member")
                continue
            parsed = wire_evidence_commit(value)
            role_path = row.get(field)
            if not isinstance(role_path, str) or Path(parsed["path"]).resolve() != Path(role_path).resolve():
                raise ValueError("Committed wire role path differs from actual report")
            if kind == "native-wire":
                native_commit = parsed
    elif "wire_evidence_commits" in row:
        commits = json_object(row["wire_evidence_commits"])
        if set(commits) != {"native-wire", "mcp-wire", "mcp-calls"} or any(v is not None for v in commits.values()):
            raise ValueError("Plain report cannot claim gzip commits")
    return WireEvidenceSource(path=path, wire_evidence_codec=codec, commit=native_commit)


RUNNING_DATE_BASE_HOST_SHA256: Final = '776fc23d6a0d7913df96e1799ae25b5021db99b76fb943802171bac6f85c808f'
RUNNING_DATE_SUPPORT_FILENAME: Final = 'campaign_running_date_publication_v1.py'
RUNNING_DATE_SUPPORT_RELATIVE: Final = 'ck3_autonomous_player/src/xar_autoplayer/bridge/' + RUNNING_DATE_SUPPORT_FILENAME
RUNNING_DATE_PROJECTION_SCHEMA: Final = 'ck3-shared-host-running-date-support-v1'
MENU_FACTORY_PROJECTION_SCHEMA: Final = 'ck3-shared-host-running-date-support-v2'
MENU_FACTORY_SOURCE_RELATIVE: Final = 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


def _host_support_pin(value: object) -> FilePin:
    row = json_object(value)
    if set(row) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Exact host-support file pin fields required')
    result = file_pin(row)
    path = Path(result['path'])
    if not path.is_absolute() or path.is_symlink():
        raise ValueError('Absolute ordinary host-support file required')
    return result


def checked_host_support_pin(value: object) -> FilePin:
    result = _host_support_pin(value)
    raw = Path(result['path']).read_bytes()
    if len(raw) != result['bytes'] or hashlib.sha256(raw).hexdigest() != result['sha256']:
        raise ValueError('Host-support exact file bytes changed: ' + result['path'])
    return result


def _running_date_function(raw: bytes) -> bytes:
    tree = ast.parse(raw.decode('utf-8-sig'))
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name == '_campaign_pending_running_date']
    if len(found) != 1 or found[0].end_lineno is None:
        raise ValueError('Exactly one reviewed running-date host definition required')
    node = found[0]
    return b''.join(raw.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])


def project_running_date_host(base: bytes, helper: FilePin, menu_factory: FilePin | None = None) -> bytes:
    """Replace one approved definition; every other byte round-trips exactly."""
    helper = _host_support_pin(helper)
    if hashlib.sha256(base).hexdigest() != RUNNING_DATE_BASE_HOST_SHA256:
        raise ValueError('Unsupported original shared host SHA256')
    original = _running_date_function(base)
    text = '''def _campaign_pending_running_date(source: dict[str, object], snapshot: dict[str, object],
                                   error: RuntimeError) -> dict[str, object]:
    """Observe the canonical typed support; never admit an unqualified frame."""
    import hashlib
    import importlib.util
    import sys
    from pathlib import Path
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class Pending(Protocol):
        def to_host_binding(self) -> dict[str, object]: ...

    @runtime_checkable
    class Support(Protocol):
        def pending_running_date_v1(self, source: object, snapshot: object, error: object) -> Pending: ...

    path = Path(__HELPER_PATH__)
    raw = path.read_bytes()
    if path.is_symlink() or len(raw) != __HELPER_BYTES__ or hashlib.sha256(raw).hexdigest() != __HELPER_SHA__:
        raise RuntimeError('Shared running-date support bytes differ from the frozen projection')
    spec = importlib.util.spec_from_file_location('_ck3_shared_running_date_support_v1', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('Exact shared running-date support loader unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not isinstance(module, Support):
        raise RuntimeError('Canonical running-date support API differs')
    return module.pending_running_date_v1(source, snapshot, error).to_host_binding()
'''
    replacement = (text.replace('__HELPER_BYTES__', str(helper['bytes']))
                   .replace('__HELPER_SHA__', repr(helper['sha256']))
                   .replace('__HELPER_PATH__', repr(helper['path'])))
    newline = '\r\n' if b'\r\n' in base else '\n'
    projected = replacement.replace('\n', newline).encode('utf-8')
    if base.count(original) != 1:
        raise ValueError('Ambiguous original shared host definition')
    output = base.replace(original, projected, 1)
    ast.parse(output.decode('utf-8-sig'))
    if output.count(projected) != 1 or output.replace(projected, original, 1) != base:
        raise ValueError('Host-support projection cannot restore the exact original host')
    if menu_factory is not None:
        reference = checked_host_support_pin(menu_factory)
        source = Path(reference['path'])
        if not source.as_posix().endswith('/' + MENU_FACTORY_SOURCE_RELATIVE):
            raise ValueError('Canonical public menu factory source path differs')
        source_tree = ast.parse(source.read_bytes())
        functions = [node for node in source_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_server']
        imports = [node for node in functions[0].body if isinstance(node, ast.ImportFrom)
                   and node.module == 'xar_autoplayer.bridge.mcp_server'
                   and [(alias.name, alias.asname) for alias in node.names] == [('create_server', None)]] if len(functions) == 1 else []
        if len(imports) != 1:
            raise ValueError('Canonical public native server lacks its exact stock factory import')
        old_import = ('    from registration_mcp import create_server' + newline).encode()
        stock_import = ast.get_source_segment(source.read_text(encoding='utf-8-sig'), imports[0])
        if stock_import != 'from xar_autoplayer.bridge.mcp_server import create_server':
            raise ValueError('Canonical public stock factory statement differs')
        replacement_import = ("    if getattr(args, 'frontend_mod_load_observation', False):" + newline
                              + '        ' + stock_import + newline + '    else:' + newline
                              + '        from registration_mcp import create_server' + newline).encode()
        if output.count(old_import) != 1:
            raise ValueError('Exactly one original campaign factory import required')
        output = output.replace(old_import, replacement_import, 1)
        if output.replace(replacement_import, old_import, 1).replace(projected, original, 1) != base:
            raise ValueError('Menu factory projection cannot restore exact original host')
        ast.parse(output.decode('utf-8-sig'))
    return output


@dataclass(frozen=True)
class HostRunningDateProjectionV1:
    machine_id: str
    source_commit: str
    source_git_blob: str
    observed_at_utc: str
    base_host: FilePin
    canonical_helper: FilePin
    helper: FilePin
    projected_host: FilePin
    producer: FilePin
    projector: FilePin
    canonical_menu_factory: FilePin | None = None

    @classmethod
    def parse(cls, value: object) -> HostRunningDateProjectionV1:
        row = json_object(value)
        pins = ('base_host', 'canonical_helper', 'helper', 'projected_host', 'producer', 'projector')
        menu = row.get('schema') == MENU_FACTORY_PROJECTION_SCHEMA
        extra = {'canonical_menu_factory'} if menu else set()
        if set(row) != {'schema', 'machine_id', 'source_commit', 'source_git_blob', 'observed_at_utc', *pins, *extra}:
            raise ValueError('Exact shared host-support projection fields required')
        if row['schema'] not in (RUNNING_DATE_PROJECTION_SCHEMA, MENU_FACTORY_PROJECTION_SCHEMA):
            raise ValueError('Unsupported shared host-support projection schema')
        machine, commit, blob = row['machine_id'], row['source_commit'], row['source_git_blob']
        if type(machine) is not str or not isinstance(machine, str) or not machine or '\0' in machine:
            raise ValueError('Explicit host-support machine identity required')
        for digest in (commit, blob):
            if type(digest) is not str or not isinstance(digest, str) or re.fullmatch('[0-9a-f]{40}', digest) is None:
                raise ValueError('Exact committed host-support source identity required')
        if not isinstance(commit, str) or not isinstance(blob, str):
            raise ValueError('Host-support source identity must be strings')
        observed = row['observed_at_utc']
        if (not isinstance(observed, str) or re.fullmatch(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)', observed) is None):
            raise ValueError('Strict actual UTC host-support observation time required')
        instant = datetime.fromisoformat(observed.replace('Z', '+00:00'))
        if instant > datetime.now(timezone.utc):
            raise ValueError('Host-support observation cannot be in the future')
        return cls(machine, commit, blob, observed,
                   base_host=_host_support_pin(row['base_host']), canonical_helper=_host_support_pin(row['canonical_helper']),
                   helper=_host_support_pin(row['helper']), projected_host=_host_support_pin(row['projected_host']),
                   producer=_host_support_pin(row['producer']), projector=_host_support_pin(row['projector']),
                   canonical_menu_factory=_host_support_pin(row['canonical_menu_factory']) if menu else None)

    def to_json(self) -> JsonObject:
        row: JsonObject = {'schema': MENU_FACTORY_PROJECTION_SCHEMA if self.canonical_menu_factory is not None else RUNNING_DATE_PROJECTION_SCHEMA, 'machine_id': self.machine_id,
                           'source_commit': self.source_commit, 'source_git_blob': self.source_git_blob,
                           'observed_at_utc': self.observed_at_utc}
        for key, value in (('base_host', self.base_host), ('canonical_helper', self.canonical_helper),
                           ('helper', self.helper), ('projected_host', self.projected_host),
                           ('producer', self.producer), ('projector', self.projector)):
            row[key] = json_object(value)
        if self.canonical_menu_factory is not None:
            row['canonical_menu_factory'] = json_object(self.canonical_menu_factory)
        return row


def validate_host_running_date_projection(reference: object, host: Path, machine_id: object) -> list[FilePin]:
    """Validate metadata before host selection and return its full freeze closure."""
    receipt = checked_host_support_pin(reference)
    row = HostRunningDateProjectionV1.parse(json.loads(Path(receipt['path']).read_bytes()))
    if type(machine_id) is not str or row.machine_id != machine_id:
        raise ValueError('Host-support projection crossed the actual machine')
    refs = [row.base_host, row.canonical_helper, row.helper, row.projected_host, row.producer, row.projector]
    if row.canonical_menu_factory is not None:
        refs.append(row.canonical_menu_factory)
    for ref in refs:
        checked_host_support_pin(ref)
    if Path(row.projected_host['path']).resolve() != host.resolve():
        raise ValueError('Selected host differs from shared support projection')
    if Path(row.helper['path']).resolve() != host.resolve().with_name(RUNNING_DATE_SUPPORT_FILENAME):
        raise ValueError('Shared support import route must be the exact host sibling')
    if not Path(row.canonical_helper['path']).as_posix().endswith('/' + RUNNING_DATE_SUPPORT_RELATIVE):
        raise ValueError('Canonical host helper source path differs')
    if Path(row.helper['path']).read_bytes() != Path(row.canonical_helper['path']).read_bytes():
        raise ValueError('Host support is not a byte-exact canonical source snapshot')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != row.projector['sha256']:
        raise ValueError('Loaded host projector differs from declared canonical source')
    expected = project_running_date_host(Path(row.base_host['path']).read_bytes(), row.helper, row.canonical_menu_factory)
    if host.read_bytes() != expected:
        raise ValueError('Shared host changes exceed the exact supported definition projection')
    return [receipt, *refs]
