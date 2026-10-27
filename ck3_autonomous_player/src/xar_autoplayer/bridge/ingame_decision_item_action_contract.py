"""Native navigation attempts, once-only Confirm, and actual postconditions."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

from .ingame_decisions_open_contract import result_build
from .ingame_decision_item_contract import normalize_decision_item, validate_decision_key

SELECT_STEP = 'select-ingame-decision-item-v1'
SELECT_CAPABILITY = 'game.command.select-ingame-decision-item-v1'
CONFIRM_STEP = 'confirm-ingame-decision-item-v1'
CONFIRM_CAPABILITY = 'game.command.confirm-ingame-decision-item-v1'


class DecisionNavigationFilePin(TypedDict):
    path: str
    bytes: int
    sha256: str


class DecisionNavigationPredecessor(TypedDict):
    request_id: str
    claim: DecisionNavigationFilePin
    verified: DecisionNavigationFilePin


class DecisionNavigationIdentity(TypedDict):
    game_pid: int
    actor_id: int
    episode_run_id: str | None
    decision_key: str
    action: Literal['select']
    public_revision: int
    navigation_predecessor: NotRequired[DecisionNavigationPredecessor]


@dataclass(frozen=True)
class DecisionNavigationClaim:
    identity: DecisionNavigationIdentity
    path: Path
    repeated: bool


class VisibleDecisionNavigationResult(TypedDict):
    schema: Literal['ck3-ingame-decision-item-action-v1']
    step: Literal['select-ingame-decision-item-v1']
    action: Literal['select']
    decision_key: str
    game_version: str
    executable_sha256: str
    native_revision: int
    connection_generation: int
    game_pid: int
    played_character_id: int
    date_raw: int
    read_only: Literal[True]
    completion_source: Literal['observed_already_visible']
    dispatch_invoked: Literal[False]
    native_call_completed: Literal[False]
    before_already_selected: Literal[True]
    selected_after_verified: Literal[True]
    postcondition_verified: Literal[True]
    verification_pending: Literal[False]
    status: Literal['verified_selected_detail']
    later_actual_observation: dict[str, object]
    native_ack: None
    action_request_id: None
    action_claim_path: None
    episode_run_id: str | None
    queried_revision: int
    uses_mouse: Literal[False]
    uses_keyboard: Literal[False]
    uses_ocr: Literal[False]


def _navigation_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError('decision navigation evidence must be a JSON object')
    return {key: item for key, item in value.items()}


def _navigation_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError('decision navigation evidence lacks a string identity')
    return value


def _navigation_integer(value: object, *, positive: bool = False) -> int:
    if type(value) is not int or (positive and value <= 0):
        raise ValueError('decision navigation evidence has an invalid integer')
    return value


def _navigation_episode(value: object) -> str | None:
    return None if value is None else _navigation_text(value)


def _navigation_file_pin(value: object) -> DecisionNavigationFilePin:
    raw = _navigation_object(value)
    if set(raw) != {'path', 'bytes', 'sha256'}:
        raise ValueError('decision navigation FilePin fields differ')
    path = _navigation_text(raw['path'])
    size = _navigation_integer(raw['bytes'], positive=True)
    sha256 = _navigation_text(raw['sha256'])
    if (not Path(path).is_absolute() or len(sha256) != 64
            or any(char not in '0123456789abcdef' for char in sha256)):
        raise ValueError('decision navigation FilePin identity is invalid')
    return {'path': path, 'bytes': size, 'sha256': sha256}


def parse_decision_navigation_identity(value: object) -> DecisionNavigationIdentity:
    raw = _navigation_object(value)
    fields = {'game_pid', 'actor_id', 'episode_run_id', 'decision_key', 'action', 'public_revision'}
    if set(raw) not in (fields, fields | {'navigation_predecessor'}) or raw['action'] != 'select':
        raise ValueError('decision navigation identity fields differ')
    identity: DecisionNavigationIdentity = {
        'game_pid': _navigation_integer(raw['game_pid'], positive=True),
        'actor_id': _navigation_integer(raw['actor_id'], positive=True),
        'episode_run_id': _navigation_episode(raw['episode_run_id']),
        'decision_key': validate_decision_key(raw['decision_key']), 'action': 'select',
        'public_revision': _navigation_integer(raw['public_revision'], positive=True),
    }
    if 'navigation_predecessor' in raw:
        predecessor = _navigation_object(raw['navigation_predecessor'])
        if set(predecessor) != {'request_id', 'claim', 'verified'}:
            raise ValueError('decision navigation predecessor fields differ')
        identity['navigation_predecessor'] = {
            'request_id': _navigation_text(predecessor['request_id']),
            'claim': _navigation_file_pin(predecessor['claim']),
            'verified': _navigation_file_pin(predecessor['verified']),
        }
    return identity


def _navigation_record(path: Path) -> tuple[dict[str, object], DecisionNavigationFilePin]:
    # Claims and their verified results are small, immutable local evidence.
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('decision navigation evidence exceeds its read bound')
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError('decision navigation evidence exceeds its read bound')
    value: object = json.loads(raw)
    return _navigation_object(value), {
        'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
    }


def _navigation_claim_path(directory: Path, identity: DecisionNavigationIdentity) -> Path:
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode('utf-8')).hexdigest()
    return directory / f'{key}.claim.json'


def _verified_navigation_predecessor(
    claim: Path, identity: DecisionNavigationIdentity,
) -> DecisionNavigationPredecessor:
    value, claim_pin = _navigation_record(claim)
    request_id = _navigation_text(value.get('request_id'))
    key = validate_decision_key(identity.get('decision_key'))
    binding = _navigation_object(value.get('binding'))
    for field in ('native_revision', 'connection_generation', 'game_pid', 'played_character_id'):
        _navigation_integer(binding.get(field), positive=True)
    _navigation_integer(binding.get('date_raw'))
    previous_identity = parse_decision_navigation_identity(value.get('action_identity'))
    _navigation_episode(binding.get('episode_run_id'))
    if (set(value) != {'schema', 'request_id', 'binding', 'action_identity', 'decision_key',
                       'action', 'expected_window_kind', 'status'}
            or set(binding) != {'native_revision', 'connection_generation', 'game_pid',
                                'played_character_id', 'date_raw', 'episode_run_id'}
            or value.get('schema') != 'ck3-ingame-decision-item-once-claim-v1'
            or value.get('status') != 'claimed_result_unknown_no_retry'
            or value.get('action') != 'select' or value.get('decision_key') != key
            or value.get('expected_window_kind') is not None
            or previous_identity != identity
            or _navigation_claim_path(claim.parent, previous_identity) != claim
            or previous_identity.get('game_pid') != binding['game_pid']
            or previous_identity.get('actor_id') != binding['played_character_id']
            or previous_identity.get('episode_run_id') != binding.get('episode_run_id')):
        raise ValueError('decision navigation predecessor identity differs; no retry')
    verified, verified_pin = _navigation_record(claim.with_suffix('.verified.json'))
    result = _navigation_object(verified.get('result'))
    if (set(verified) != {'schema', 'request_id', 'result'}
            or verified.get('schema') != 'ck3-ingame-decision-action-independent-verification-v1'
            or verified.get('request_id') != request_id
            or result.get('schema') != 'ck3-ingame-decision-item-action-v1'
            or result.get('step') != SELECT_STEP or result.get('action') != 'select'
            or result.get('decision_key') != key
            or result.get('status') != 'verified_selected_detail'
            or result.get('postcondition_verified') is not True
            or result.get('verification_pending') is not False
            or result.get('action_request_id') != request_id
            or result.get('action_claim_path') != str(claim)
            or result.get('episode_run_id') != binding.get('episode_run_id')
            or _navigation_integer(result.get('queried_revision'), positive=True)
                != previous_identity['public_revision']):
        raise ValueError('decision navigation predecessor lacks verified completion; no retry')
    native = normalize_decision_action(result.get('native_ack'), binding, key, 'select')
    later = _navigation_object(result.get('later_actual_observation'))
    if (not actual_selected_detail(later, binding, key)
            or native.get('game_version') != later.get('game_version')
            or _navigation_text(native.get('executable_sha256')).lower()
                != _navigation_text(later.get('executable_sha256')).lower()):
        raise ValueError('decision navigation predecessor lacks actual visible detail; no retry')
    return {'request_id': request_id, 'claim': claim_pin, 'verified': verified_pin}


def select_navigation_claim(directory: Path, identity: object) -> DecisionNavigationClaim:
    """Choose one append-only slot before observing the new navigation prestate.

    Simultaneous callers choose the same successor and compete on the existing
    exclusive claim create. An unknown predecessor never creates a new slot.
    """
    base = parse_decision_navigation_identity(identity)
    if 'navigation_predecessor' in base:
        raise ValueError('caller cannot supply a decision navigation predecessor')
    candidate: DecisionNavigationIdentity = {**base}
    claim = _navigation_claim_path(directory, candidate)
    seen: set[Path] = set()
    repeated = False
    while claim.exists():
        if claim in seen:
            raise ValueError('decision navigation predecessor cycle; no retry')
        seen.add(claim)
        predecessor = _verified_navigation_predecessor(claim, candidate)
        candidate = {**base, 'navigation_predecessor': predecessor}
        claim = _navigation_claim_path(directory, candidate)
        repeated = True
    return DecisionNavigationClaim(candidate, claim, repeated)


def require_closed_null_decision_navigation(
    raw: object, binding: dict[str, object], decision_key: str,
) -> None:
    result = normalize_decision_item(raw, binding, decision_key)
    if (result.get('available') is not True or result.get('detail_tree_complete') is not True
            or result.get('detail_root_visible') is not False
            or result.get('detail_definition_available') is not False
            or result.get('detail_definition_matches_target') is not False
            or result.get('detail_decision_key') != ''):
        raise ValueError('new select navigation requires an actual closed/null detail')


def visible_decision_navigation_result(
    raw: object, binding: dict[str, object], decision_key: str, revision: int,
) -> VisibleDecisionNavigationResult:
    """SDK completion from a fresh reader; never a fabricated native action ACK."""
    result = normalize_decision_item(raw, binding, decision_key)
    if not actual_selected_detail(result, binding, decision_key):
        raise ValueError('idempotent select lacks actual visible selected detail')
    if 'episode_run_id' not in binding:
        raise ValueError('idempotent select lacks an explicit episode identity')
    return {
        'schema': 'ck3-ingame-decision-item-action-v1', 'step': 'select-ingame-decision-item-v1', 'action': 'select',
        'decision_key': decision_key, 'game_version': _navigation_text(result.get('game_version')),
        'executable_sha256': _navigation_text(result.get('executable_sha256')),
        'native_revision': _navigation_integer(binding.get('native_revision'), positive=True),
        'connection_generation': _navigation_integer(binding.get('connection_generation'), positive=True),
        'game_pid': _navigation_integer(binding.get('game_pid'), positive=True),
        'played_character_id': _navigation_integer(binding.get('played_character_id'), positive=True),
        'date_raw': _navigation_integer(binding.get('date_raw')),
        'read_only': True, 'completion_source': 'observed_already_visible',
        'dispatch_invoked': False, 'native_call_completed': False, 'before_already_selected': True,
        'selected_after_verified': True, 'postcondition_verified': True, 'verification_pending': False,
        'status': 'verified_selected_detail', 'later_actual_observation': result,
        'native_ack': None, 'action_request_id': None, 'action_claim_path': None,
        'episode_run_id': _navigation_episode(binding['episode_run_id']),
        'queried_revision': _navigation_integer(revision, positive=True),
        'uses_mouse': False, 'uses_keyboard': False, 'uses_ocr': False,
    }


def normalize_decision_action(raw: object, binding: dict[str, object], decision_key: str, action: str) -> dict[str, object]:
    build = result_build(raw)
    step = SELECT_STEP if action == 'select' else CONFIRM_STEP if action == 'confirm' else None
    if (step is None or not isinstance(raw, dict) or raw.get('schema') != 'ck3-ingame-decision-item-action-v1'
            or raw.get('step') != step or raw.get('action') != action or raw.get('decision_key') != decision_key):
        raise ValueError('malformed exact .3/.4 decision action acknowledgement')
    for key in ('native_revision', 'connection_generation', 'game_pid', 'played_character_id', 'date_raw'):
        if type(raw.get(key)) is not int or raw[key] != binding[key]:
            raise ValueError(f'decision action changed {key}')
    for key in ('owner_thread_verified', 'source_abi_pins_verified', 'action_abi_pins_verified',
                'receiver_qualified', 'gui_owner_binding_verified', 'frame_verified'):
        if raw.get(key) is not True:
            raise ValueError(f'decision action lacks actual {key}')
    before = normalize_decision_item(raw.get('before_actual_model'), binding, decision_key)
    if result_build(before) != build:
        raise ValueError('decision action and before model builds differ')
    if before.get('available') is not True:
        raise ValueError('decision action lacks actual before model qualification')
    for key in ('dispatch_invoked', 'native_call_completed', 'before_already_selected', 'native_handled',
                'native_after_read', 'selected_after_verified', 'inner_modal_visible', 'inner_modal_tree_complete',
                'postcondition_verified', 'verification_pending', 'detail_actor_binding_verified', 'no_blocking_modal_verified'):
        if type(raw.get(key)) is not bool:
            raise ValueError(f'decision action lacks actual boolean {key}')
    if raw.get('unavailable_reason') or raw.get('status') not in ('observed_postcondition', 'acknowledged_verification_pending'):
        raise ValueError('native decision action rejected or completion is unknown; no retry')
    if action == 'select':
        if raw['no_blocking_modal_verified'] is not True:
            raise ValueError('source OnSelect is blocked by a modal')
        if raw['before_already_selected']:
            if raw['dispatch_invoked'] or raw['native_call_completed']:
                raise ValueError('already-selected source handler must not toggle Hide')
            if before.get('detail_definition_matches_target') is not True:
                raise ValueError('already-selected acknowledgement lacks actual definition identity')
        elif not raw['dispatch_invoked'] or not raw['native_call_completed']:
            raise ValueError('source OnSelect invocation did not complete; no retry')
    else:
        if (not raw['dispatch_invoked'] or raw['before_already_selected']
                or raw['detail_actor_binding_verified'] is not True
                or before.get('detail_root_visible') is not True
                or before.get('detail_tree_complete') is not True
                or before.get('detail_definition_matches_target') is not True
                or before.get('detail_actor_binding_verified') is not True
                or type(before.get('detail_actor_reference_key')) is not int
                or before['detail_actor_reference_key'] != binding['played_character_id']):
            raise ValueError('fixed Confirm lacks actual selected detail/actor/dispatch proof')
    return dict(raw)


def actual_selected_detail(raw: object, binding: dict[str, object], decision_key: str) -> bool:
    result = normalize_decision_item(raw, binding, decision_key)
    return (result.get('available') is True and result.get('detail_root_visible') is True
            and result.get('detail_tree_complete') is True and result.get('detail_definition_matches_target') is True
            and result.get('detail_actor_binding_verified') is True
            and type(result.get('detail_actor_reference_key')) is int
            and result['detail_actor_reference_key'] == binding['played_character_id'])


def actual_inner_modal_tree(raw: object, window_kind: str) -> bool:
    # Outer transparent root visibility alone does not prove a panel open.
    if (window_kind != 'vivhite_courtier' or not isinstance(raw, dict)
            or raw.get('schema') != 'ck3-native-gui-window-tree-inspection-v1'
            or raw.get('window_kind') != window_kind or raw.get('read_only') is not True
            or raw.get('scope_root_name') != 'ervc_courtier_creator_window'
            or raw.get('root_available') is not True or raw.get('truncated') is not False):
        return False
    rows = raw.get('widgets')
    if (not isinstance(rows, list) or type(raw.get('widget_count')) is not int
            or raw['widget_count'] != len(rows) or not 1 <= len(rows) <= 2048):
        return False
    roots = [r for r in rows if isinstance(r, dict) and r.get('child_path') == '']
    modals = [r for r in rows if isinstance(r, dict) and r.get('runtime_name') == 'ervc_courtier_creator_modal']
    return (len(roots) == 1 and roots[0].get('runtime_name') == 'ervc_courtier_creator_window'
            and roots[0].get('effective_visible') is True and roots[0].get('child_count') == 1
            and len(modals) == 1 and modals[0].get('child_path') == '0'
            and modals[0].get('effective_visible') is True)
