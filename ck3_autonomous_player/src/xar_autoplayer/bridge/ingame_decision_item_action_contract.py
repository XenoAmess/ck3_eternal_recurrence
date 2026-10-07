"""Once-only native source OnSelect/Confirm intent and independent actual postconditions."""
from .ingame_decisions_open_contract import result_build
from .ingame_decision_item_contract import normalize_decision_item

SELECT_STEP = 'select-ingame-decision-item-v1'
SELECT_CAPABILITY = 'game.command.select-ingame-decision-item-v1'
CONFIRM_STEP = 'confirm-ingame-decision-item-v1'
CONFIRM_CAPABILITY = 'game.command.confirm-ingame-decision-item-v1'


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
