"""Two default-only stock Confirmation previews; ACKs never prove visibility."""
from __future__ import annotations

KEYS = {
    'clerical_puppet': 'make_clerical_puppet_interaction',
    'external_clerical_puppet': 'make_external_clerical_puppet_interaction',
}
OPTION_KEYS = ('hook', 'skill_support', 'piety_support', 'dread_support',
               'friendly_support', 'lunacy_support')
OPERATIONS = {'query', 'open_clerical_preview', 'close_clerical_preview'}


def validate_request(operation, subject_id, fields):
    if (operation not in OPERATIONS or type(subject_id) is not int
            or not 0 < subject_id < 2**32 - 1
            or fields['presentation_target'] not in KEYS
            or fields['presentation_index'] is not None
            or fields['presentation_tab'] is not None
            or (operation != 'query' and fields['presentation_receipt'] is None)):
        raise ValueError('clerical preview requires a full recipient, one finite target and its query receipt for an action')


def _context(c, *, key, actor, recipient):
    expected = {'interaction_key', 'definition_hash', 'actor_id', 'recipient_id',
        'effective_actor_id', 'interface_kind', 'needs_confirmation',
        'declared_option_count', 'selected_option_count', 'roles', 'options'}
    if not isinstance(c, dict) or set(c) != expected:
        raise ValueError('clerical native context shape unavailable')
    if (c['interaction_key'] != key or c['actor_id'] != actor
            or c['recipient_id'] != recipient or c['effective_actor_id'] != actor
            or c['needs_confirmation'] is not True
            or any(type(c[n]) is not int for n in ('definition_hash', 'actor_id',
                'recipient_id', 'effective_actor_id', 'interface_kind',
                'declared_option_count', 'selected_option_count'))
            or not 0 <= c['definition_hash'] < 2**32
            or not 0 < c['actor_id'] < 2**32-1 or not 0 < c['recipient_id'] < 2**32-1
            or c['interface_kind'] != 0 or c['declared_option_count'] != 6
            or c['selected_option_count'] != 0):
        raise ValueError('clerical context lost exact roles, kind, confirmation or default options')
    roles = c['roles']
    if (not isinstance(roles, list) or len(roles) != 6
            or any(x is not None and (type(x) is not int or not 0 <= x < 2**32-1) for x in roles)
            or roles[0] != actor or roles[1] != recipient or roles[5] != actor):
        raise ValueError('clerical context full native roles differ')
    options = c['options']
    if not isinstance(options, list) or len(options) != 6:
        raise ValueError('clerical context lacks six actual native options')
    ids = set()
    for name, item in zip(OPTION_KEYS, options, strict=True):
        if (not isinstance(item, dict) or set(item) != {'key', 'flag_id', 'bank_value', 'selected'}
                or item['key'] != name or type(item['flag_id']) is not int
                or not 0 <= item['flag_id'] < 2**32-1 or item['flag_id'] in ids
                or type(item['bank_value']) is not int or item['bank_value'] != 0
                or item['selected'] is not False):
            raise ValueError('clerical option key/flag/default native bank mismatch')
        ids.add(item['flag_id'])


def normalize(value, leaf, *, operation, kind, subject_id, actor_id, target, receipt):
    c = leaf.get('clerical_preview')
    if kind != 'clerical_interaction':
        if c is not None:
            raise ValueError('unsolicited clerical preview on another window')
        return
    if c is None and not leaf['available']:
        return  # Preserve an actual earlier owner/source admission failure.
    fields = {'available', 'root_bound', 'window_visible', 'phase', 'default_context',
              'window_context', 'command_submitted', 'options_mutated', 'business_outcome_observed'}
    if not isinstance(c, dict) or set(c) != fields:
        raise ValueError('missing finite clerical preview observation')
    if (any(type(c[n]) is not bool for n in ('available', 'root_bound', 'command_submitted',
                'options_mutated', 'business_outcome_observed'))
            or c['available'] != leaf['available']
            or any(c[n] for n in ('command_submitted', 'options_mutated', 'business_outcome_observed'))):
        raise ValueError('clerical preview cannot claim commands, option mutation or business outcomes')
    for sample in (c['default_context'], c['window_context']):
        if sample is not None:
            _context(sample, key=KEYS[target], actor=actor_id, recipient=subject_id)
    if not leaf['available']:
        return
    if (not c['root_bound'] or not value['window_exists'] or c['default_context'] is None
            or leaf['receipt_id'] is None or (receipt is not None and leaf['receipt_id'] != receipt)):
        raise ValueError('clerical preview lacks initialized original root/default context/query receipt')
    if operation == 'query':
        visible = c['window_visible']
        if (type(visible) is not bool or visible != value['effective_visible']
                or leaf['post_window_visible'] != visible
                or leaf['observation_owner_epoch'] is None):
            raise ValueError('clerical query lacks independent actual root visibility')
        if visible:
            if (c['phase'] != 'visible_observed' or not leaf['source_bound']
                    or not leaf['preview_observed'] or c['window_context'] != c['default_context']):
                raise ValueError('clerical visible query lacks matching installed full context/default options')
        elif (c['phase'] not in {'default_observed', 'hidden_observed'}
                or leaf['source_bound'] or leaf['preview_observed']):
            raise ValueError('clerical hidden query cannot claim a visible bound preview')
        if c['phase'] == 'hidden_observed' and (receipt is None or leaf['action_owner_epoch'] is None):
            raise ValueError('clerical hidden postcondition lacks original close receipt')
        if leaf['action_owner_epoch'] is not None and leaf['observation_owner_epoch'] <= leaf['action_owner_epoch']:
            raise ValueError('clerical postcondition must be a later independent owner query')
    else:
        phase = 'open_pending' if operation == 'open_clerical_preview' else 'close_pending'
        if (c['phase'] != phase or c['window_visible'] is not None
                or c['window_context'] is not None or leaf['post_window_visible'] is not None
                or leaf['observation_owner_epoch'] is not None or leaf['action_owner_epoch'] is None
                or leaf['preview_observed']):
            raise ValueError('clerical UI ACK cannot claim an actual completed preview/hidden result')
