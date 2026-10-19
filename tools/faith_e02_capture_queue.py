"""Validate B1 presentation plans, then use the existing public once-only queue.

An allowlist is a capture scope, not native legality or proof of zero world
mutation. The registered MCP schema and native current candidate guards still
decide each request. Every presentation must have a later independent query in
the same plan; a query's actual availability/selection still needs review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

TYPES = frozenset({'site_of_wisdom', 'site_of_martyrs', 'site_of_miracles'})
CREATION_QUERY = 'ck3_query_player_holy_site_creation_context_v1'
CREATION_SELECTORS = frozenset({'ck3_open_holy_site_creation_window_v1',
    'ck3_select_holy_site_creation_type_v1', 'ck3_select_holy_site_creation_barony_v1',
    'ck3_set_holy_site_creation_artifact_selection_v1'})
REVISION_QUERIES = frozenset({CREATION_QUERY, 'ck3_query_campaign_root_context_v1',
    'ck3_query_player_religion_context_v1'})
STEP_KEYS = frozenset({'id', 'kind', 'tool', 'args', 'fresh_revision', 'continue_on_error', 'timeout'})


def require(value, message):
    if not value:
        raise ValueError(message)


def _ref(value):
    return type(value) is int and 0 <= value < 2**32 - 1


def _fields(args, required, optional=(), *, fresh_revision=False):
    required = set(required)
    permitted = required | set(optional)
    if fresh_revision is True and 'expected_revision' not in args:
        # The public queue/host binds the actual revision immediately before
        # dispatch. Do not insert a guessed value into this capture plan.
        required.discard('expected_revision')
    require(set(args) >= required and set(args) <= permitted,
            'B1 tool argument fields differ from its finite contract')
    if 'expected_revision' in args:
        require(type(args['expected_revision']) is int and args['expected_revision'] > 0,
                'B1 expected_revision must be an observed positive integer')


def _following(steps, index, tool, fields):
    require(index + 1 < len(steps), 'B1 presentation needs a later independent readback')
    following = steps[index + 1]
    require(following.get('tool') == tool and following.get('fresh_revision') is True
            and all(following.get('args', {}).get(k) == v for k, v in fields.items()),
            'B1 presentation must immediately precede the matching fresh independent query')


def validate(plan, report=None):
    require(type(plan) is dict and set(plan) == {'steps'} and type(plan['steps']) is list
            and 1 <= len(plan['steps']) <= 32, 'B1 needs an explicit bounded nonempty steps list')
    steps = plan['steps']
    ids = []
    for index, step in enumerate(steps):
        require(type(step) is dict and set(step) <= STEP_KEYS
                and step.get('kind', 'tool') == 'tool', 'B1 admits only finite tool plans, no lifecycle or day operation')
        require(isinstance(step.get('id'), str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', step['id']),
                'B1 needs unique portable explicit step IDs')
        ids.append(step['id'])
        args = step.get('args', {})
        require(type(args) is dict and step.get('continue_on_error') is True,
                'B1 uses actual args and retains the host after an unavailable UI query')
        require('fresh_revision' not in step or type(step['fresh_revision']) is bool,
                'B1 fresh_revision must be a boolean')
        if 'timeout' in step:
            require(type(step['timeout']) in (int, float) and 0 < step['timeout'] <= 300,
                    'B1 tool timeout exceeds its bounded command allocation')
        def fields(required, optional=()):
            _fields(args, required, optional, fresh_revision=step.get('fresh_revision', True))
        tool = step.get('tool')
        if tool == 'ck3_take_snapshot':
            fields((), {'include_native_command_history'})
            require(args.get('include_native_command_history', False) is False, 'B1 does not request command history')
        elif tool == 'ck3_get_capabilities':
            fields(())
        elif tool in REVISION_QUERIES:
            fields({'expected_revision'})
        elif tool == 'ck3_query_player_holy_site_v1':
            fields({'expected_revision'}, {'holy_site_id'})
            require(args.get('holy_site_id') is None or _ref(args['holy_site_id']), 'B1 requires an actual HolySite full ID')
        elif tool == 'ck3_query_ingame_ui_window_v1':
            fields({'expected_revision', 'window_kind'})
            require(args['window_kind'] in {'faith', 'holy_site', 'holy_site_creation'}, 'B1 window scope differs')
        elif tool in CREATION_SELECTORS:
            required_fields = {'expected_revision'}
            if tool == 'ck3_select_holy_site_creation_type_v1':
                required_fields.add('type_key')
            elif tool == 'ck3_select_holy_site_creation_barony_v1':
                required_fields.add('barony_title_id')
            elif tool == 'ck3_set_holy_site_creation_artifact_selection_v1':
                required_fields |= {'artifact_id', 'selected'}
            fields(required_fields)
            require('type_key' not in args or args['type_key'] in TYPES, 'Only B1 wisdom/martyrs/miracles type previews')
            for key in ('barony_title_id', 'artifact_id'):
                require(key not in args or _ref(args[key]), 'B1 selector requires an actual complete ID')
            require('selected' not in args or type(args['selected']) is bool, 'B1 desired selection must be explicit boolean')
            _following(steps, index, CREATION_QUERY, {})
        elif tool in {'ck3_open_faith_window_v1', 'ck3_open_holy_site_window_v1'}:
            key = 'faith_id' if tool == 'ck3_open_faith_window_v1' else 'holy_site_id'
            kind = 'faith' if key == 'faith_id' else 'holy_site'
            fields({'expected_revision', key})
            require(_ref(args[key]), 'B1 original page requires an actual full ID')
            _following(steps, index, 'ck3_query_ingame_ui_window_v1', {'window_kind': kind})
        elif tool == 'ck3_query_faith_power_ui_v1':
            fields({'expected_revision', 'window_kind', 'subject_id'}, {'presentation_tab', 'presentation_receipt'})
            require(args['window_kind'] in {'faith', 'tooltips'} and _ref(args['subject_id']), 'B1 finite presentation query scope differs')
            if args['window_kind'] == 'tooltips':
                require(args['subject_id'] == 0 and 'presentation_tab' not in args, 'Global tooltips uses subject0, no tab')
            else:
                require(args.get('presentation_tab', '') in {'', 'holy_sites'}, 'B1 only previews the original holy-sites tab')
            require('presentation_receipt' not in args or isinstance(args['presentation_receipt'], str)
                    and re.fullmatch(r'[0-9a-f]{32}', args['presentation_receipt']), 'B1 requires an actual presentation receipt')
        elif tool == 'ck3_present_faith_power_ui_v1':
            fields({'operation', 'expected_revision', 'window_kind', 'subject_id'},
                   {'presentation_tab', 'presentation_receipt'})
            require(_ref(args['subject_id']), 'B1 presentation subject must be an actual full ID')
            operation, kind = args['operation'], args['window_kind']
            if kind == 'faith':
                require(operation in {'select_presentation_tab', 'close_presentation_window'}
                        and (operation != 'select_presentation_tab' or args.get('presentation_tab') == 'holy_sites')
                        and 'presentation_receipt' not in args,
                        'B1 permits only faith holy-site tab or close; no draft/interaction/building action')
                _following(steps, index, 'ck3_query_faith_power_ui_v1', {'window_kind': 'faith', 'subject_id': args['subject_id']})
            else:
                require(kind == 'tooltips' and operation == 'close_tooltips' and args['subject_id'] == 0
                        and 'presentation_tab' not in args and isinstance(args.get('presentation_receipt'), str)
                        and re.fullmatch(r'[0-9a-f]{32}', args['presentation_receipt']),
                        'B1 global tooltip close requires its independent original query receipt')
                _following(steps, index, 'ck3_query_faith_power_ui_v1',
                           {'window_kind': 'tooltips', 'subject_id': 0, 'presentation_receipt': args['presentation_receipt']})
        else:
            raise ValueError('B1 rejects world confirmation, events, saves, days or an unlisted tool: ' + str(tool))
    require(len(ids) == len(set(ids)), 'Duplicate B1 step ID; never replay')
    return {'schema': 'faith-engine-e02-b1-capture-policy-v1', 'capture_policy_validated': True,
            'steps': len(steps), 'submitted': False, 'native_legality_or_readback_success_inferred': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--live', type=Path)
    parser.add_argument('--queue-name')
    args = parser.parse_args(argv)
    result = validate(json.loads(args.plan.read_bytes()))
    if args.queue_name:
        require(args.live is not None, 'B1 dispatch needs its actual public allocated live directory')
        entry = Path(__file__).resolve().with_name('ck3_mod_acceptance_queue_control.py')
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(entry), '--live', str(args.live),
                               '--plan', str(args.plan), '--name', args.queue_name], check=False).returncode
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
