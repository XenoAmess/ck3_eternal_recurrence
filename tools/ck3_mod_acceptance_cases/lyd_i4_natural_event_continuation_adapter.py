"""Continue partial existing-cooldown observation through one reviewed vanilla event.

All simulation uses the public CaseClient. Unknown policy holds the same process
at its original deadline; no event, advance or failed action is replayed.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import stat
import sys

from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as natural
from ck3_mod_acceptance_cases import lyd_i4_natural_event_context_adapter as discovery

require = natural.require
CASE = 'i4-natural-expiry-event-continuation'
RESULT = CASE + '-result'
TOOL = discovery.TOOL
SELECT = 'ck3_select_event_option'


def contract():
    return natural.base.read_json(Path(__file__).with_name('lyd_i4_natural_event_continuation.json'))


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == CASE and data == contract(),
            'Exact independent event-continuation case required')
    require(data['maximum_natural_days'] == 366 and data['maximum_registered_event_choices'] == 1 and
            data['registered_event_definitions'] == ['bookmark.1070'] and data['school_choice_actions'] == 0,
            'Only one reviewed bookmark continuation; natural cap/school choices unchanged')


def prepare_case(context):
    validate_contract(context)
    inherited = {**context, 'case': natural.contract()['case_id'], 'case_contract': natural.contract()}
    prepared = natural.prepare_case(inherited)
    return {**prepared, 'continuation_case': CASE, 'inherited_preparation_case': inherited['case'],
            'business_pass': False}


def _pin_python(path):
    path = Path(path).resolve()
    info = path.stat(follow_symlinks=False)
    require(path.suffix == '.py' and stat.S_ISREG(info.st_mode) and
            not path.is_symlink() and not info.st_file_attributes & 1024,
            'Reviewed shared Python source must be regular')
    raw = path.read_bytes()
    require(len(raw) == info.st_size, 'Shared Python source changed while read')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class ReviewedPolicy:
    """Private namespace explicitly rooted in reviewed MAIN, optionally a ROOT overlay."""

    def __init__(self, context):
        self.base = (Path(context['repo_root']) / 'ck3_autonomous_player/src/xar_autoplayer').resolve()
        self.overlay = None
        self.expected = []
        self.module = None
        self.serial = 0

    def reload(self, binding=None):
        self.module = None
        if binding is not None:
            require(set(binding) == {'root', 'files'} and isinstance(binding['files'], list) and
                    binding['files'], 'ROOT reload needs its exact reviewed overlay source refs')
            root = Path(binding['root']).resolve()
            require(root.is_dir() and (root / 'vanilla_events').is_dir(), 'Reviewed policy-root layout missing')
            for ref in binding['files']:
                require(set(ref) == {'path', 'bytes', 'sha256'} and
                        Path(ref['path']).resolve().is_relative_to(root) and
                        _pin_python(ref['path']) == {**ref, 'path': str(Path(ref['path']).resolve())},
                        'ROOT reviewed overlay source changed')
            self.overlay, self.expected = root, list(binding['files'])
        require(sys.dont_write_bytecode, 'Public policy import requires the original -B entry')
        # Do not consume installed xar_autoplayer or the selected frozen host package.
        # Relative imports use only these explicit roots; MAIN is the declared
        # source of unchanged modules when a small reviewed overlay is selected.
        self.serial += 1
        prefix = '_lyd_i4_reviewed_policy_' + str(id(self)) + '_' + str(self.serial)
        roots = ([self.overlay] if self.overlay is not None else []) + [self.base]
        for name, paths in ((prefix, roots), (prefix + '.vanilla_events', [p / 'vanilla_events' for p in roots])):
            # An actual source loader also preserves importlib.resources access
            # to MAIN's unchanged packaged event source index. Do not execute
            # __init__ exports or import an installed canonical package.
            original = paths[-1] / '__init__.py'
            spec = importlib.util.spec_from_file_location(name, original,
                submodule_search_locations=[str(p) for p in paths])
            require(spec is not None and spec.loader is not None, 'Reviewed package source loader unavailable')
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
        importlib.invalidate_caches()
        self.prefix, self.roots = prefix, roots
        self.module = importlib.import_module(prefix + '.vanilla_events.policy')
        require(Path(self.module.__file__).resolve().is_relative_to(roots[0]) or
                Path(self.module.__file__).resolve().is_relative_to(self.base),
                'Shared policy import escaped reviewed roots')

    def recommend(self, typed, frame, context):
        if self.module is None:
            self.reload()
        active = frame['active_event']
        result = self.module.recommend_registered_vanilla_event_option_v1(
            typed, played_character_id=frame['played_character']['character_id'],
            snapshot_option_count=active['option_count'], ck3_build=context['shared_game']['version'],
            played_character=frame['played_character'])
        # Record actually imported source files, not an inventory of the source tree.
        paths = sorted({Path(module.__file__).resolve() for name, module in tuple(sys.modules.items())
                        if name.startswith(self.prefix + '.') and getattr(module, '__file__', None)})
        require(all(any(path.is_relative_to(root) for root in self.roots) for path in paths),
                'Shared relative module escaped reviewed source roots')
        pins = [_pin_python(path) for path in paths]
        loaded = {row['path']: row for row in pins}
        require(all(loaded.get(str(Path(ref['path']).resolve())) ==
                    {**ref, 'path': str(Path(ref['path']).resolve())} for ref in self.expected),
                'Reviewed overlay was not actually consumed')
        return result, {'base_MAIN_policy_root': str(self.base),
                        'reviewed_overlay_root': str(self.overlay) if self.overlay else None,
                        'actual_imported_sources': pins, 'installed_or_Csr_policy_import_used': False}


def event_query(client, before, name):
    """Fresh typed query; leave unavailable policy/presentation intact for ROOT review."""
    from ck3_mod_acceptance import pin
    frame = client.snapshot(require_event_free=False)
    discovery.same_event_frame(client, before, frame, fresh=True)
    instance = frame['active_event']['instance_id']
    rows = client.execute_plan([{'id': name, 'tool': TOOL, 'fresh_revision': False,
        'args': {'event_instance_id': instance, 'expected_revision': frame['revision']}}], name)
    require(len(rows) == 1 and rows[0].get('id') == name and rows[0].get('ok') is True and
            not rows[0].get('error'), 'Original typed query failed; no replay')
    row = rows[0]
    discovery.same_event_frame(client, frame, row['after_snapshot'])
    result = row['result']
    return {'frame': frame, 'after_frame': row['after_snapshot'], 'original_result': result,
            'typed_context': result.get('current_event_window_context'),
            'original_result_ref': pin(client.output / (name + '.actual-results.json'))}


def qualified_context(packet, context):
    frame, result, typed = packet['frame'], packet['original_result'], packet['typed_context']
    active = frame['active_event']
    actor = frame['played_character']['character_id']
    require(result.get('accepted') is True and result.get('scope') == 'exact-current-event-window' and
            result.get('status') == 'available' and result.get('current_event_window_context_ready') is True and
            result.get('queried_revision') == frame['revision'] and
            result.get('queried_native_revision') == frame['native_revision'] and
            result.get('queried_snapshot_id') == frame['snapshot_id'] and
            isinstance(typed, dict) and typed.get('schema') == 'current-event-window-context-v1' and
            typed.get('status') == 'available' and typed.get('current_event_instance_id') == active['instance_id'] and
            typed.get('date_raw') == frame['date_raw'] and typed.get('snapshot_revision') == frame['native_revision'],
            'Fresh typed identity/presentation contract unavailable')
    root = typed.get('root_scope', {})
    require(root.get('status') == 'available' and
            root.get('typed_identity', {}).get('character_id') == actor and
            type(active.get('option_count')) is int and active['option_count'] == 3 and
            typed.get('event_definition_key') == 'bookmark.1070' and
            typed.get('provenance', {}).get('backend_id') == 'ck3-1.20.0.4-native-event-window-v1' and
            context['shared_game']['version'] == '1.20.0.4',
            'Only the reviewed actual-player .4 bookmark shape can continue')
    options = typed.get('options')
    require(isinstance(options, list) and len(options) == active['option_count'] and
            [row.get('native_option_index') for row in options] == [0, 1, 2] and
            [row.get('rendered_index') for row in options] == [0, 1, 2] and
            all(row.get('shown') is True and row.get('enabled') is True for row in options),
            'Exact real option presentation changed')
    native = active.get('options')
    require(isinstance(native, list) and
            [(row.get('index'), row.get('option_number'), row.get('enabled')) for row in native] ==
            [(0, 1, True), (1, 2, True), (2, 3, True)], 'Actual snapshot option mapping differs')
    return typed


def qualified_recommendation(value, context):
    game = context['shared_game']
    require(value.get('schema') == 'xar.ck3.vanilla-event-registry-choice' and
            value.get('status') == 'recommended' and value.get('source') == 'shared_vanilla_event_registry' and
            value.get('event_definition_key') == 'bookmark.1070' and value.get('ck3_build') == game['version'] and
            str(value.get('ck3_exe_sha256', '')).lower() == game['exe_sha256'].lower() and
            value.get('selected_native_option_index') == 2 and value.get('selected_option_number') == 3 and
            value.get('selected_rendered_index') == 2 and value.get('semantic_decision_ready') is False and
            value.get('semantic_optimal') is False and value.get('native_ai_equivalent') is False and
            isinstance(value.get('checks'), dict) and value['checks'] and
            all(check is True for check in value['checks'].values()) and value.get('failed_checks') == [],
            'Reviewed shared recommendation unavailable; never infer semantic readiness')


def after_choice(client, before, row, name):
    require(row.get('id') == name and row.get('ok') is True and not row.get('error'),
            'Original sole option submission failed; never retry')
    result = row['result']
    require(result.get('accepted') is True and result.get('event_instance_id') == before['active_event']['instance_id'] and
            result.get('option_index') == 2 and result.get('option_number') == 3,
            'Sole option ACK differs; never retry')
    after = client.validate_frame(row['after_snapshot'], require_event_free=False)
    require(natural.frame_identity(before) == natural.frame_identity(after) and
            type(after.get('native_revision')) is int and after['native_revision'] >= before['native_revision'] and
            type(after.get('revision')) is int and after['revision'] >= before['revision'],
            'Option after-snapshot crossed original paused owner/date')
    require((after.get('active_event') or {}).get('instance_id') != before['active_event']['instance_id'],
            'Original event not gone in actual after-snapshot; submitted choice is never replayed')
    return after


def handle_event(context, client, data, frame, ordinal, choices, policy, *, elapsed):
    from ck3_mod_acceptance import pin
    attempt, reload_error = 0, None
    instance = frame['active_event']['instance_id']
    prefix = 'i4-event-' + str(ordinal).zfill(4) + '-instance-' + str(instance)
    while True:
        attempt += 1
        name = prefix + '-review-' + str(attempt).zfill(4)
        packet = event_query(client, frame, name)
        frame = packet['after_frame']
        recommendation, binding, blocked = None, None, None
        try:
            require(reload_error is None, reload_error or 'Shared policy reload incomplete')
            typed = qualified_context(packet, context)
            require(choices < data['maximum_registered_event_choices'], 'Already consumed the sole reviewed event choice')
            recommendation, binding = policy.recommend(typed, packet['frame'], context)
            qualified_recommendation(recommendation, context)
        except (ValueError, ImportError, OSError, KeyError, TypeError, SyntaxError) as error:
            blocked = type(error).__name__ + ': ' + str(error)
        if blocked is None:
            before = packet['after_frame']
            action_name = prefix + '-select-third-once'
            client.checkpoint(action_name + '-intent', {'event': packet, 'recommendation': recommendation,
                'shared_policy_source': binding, 'actual_instance': before['active_event']['instance_id'],
                'choice_submitted': False, 'army_material_credit': False})
            # All guards precede this one mutation; no fallback or selection retry.
            rows = client.execute_plan([{'id': action_name, 'tool': SELECT, 'fresh_revision': False,
                'args': {'event_instance_id': before['active_event']['instance_id'], 'option_number': 3,
                         'expected_revision': before['revision']}}], action_name)
            require(len(rows) == 1, 'Incomplete sole option result; never retry')
            after = after_choice(client, before, rows[0], action_name)
            choice = {'event': packet, 'recommendation': recommendation, 'shared_policy_source': binding,
                'selection_step_id': action_name, 'actual_after_snapshot': after,
                'original_selection_result_ref': pin(client.output / (action_name + '.actual-results.json')),
                'old_instance_gone': True, 'event_choice_actions': 1, 'army_material_credit': False,
                'semantic_decision_ready': False}
            client.checkpoint(action_name + '-observed', choice)
            return after, choice, False
        # This Python contract gap is held inside run_case, before public finally
        # can close the process. Keep original hold/deadline and queue ownership.
        answer = client.root_checkpoint(name + '-policy-gap', {
            'status': 'PAUSED_EVENT_POLICY_GAP', 'event': packet, 'reason': blocked,
            'recommendation': recommendation, 'shared_policy_source': binding,
            'elapsed_natural_hours': elapsed, 'request_ordinal': ordinal,
            'event_choice_actions': choices, 'school_choice_actions': 0,
            'allowed_operator_actions': ['abort', 'reevaluate'],
            'reevaluate_is_fresh_readonly_query_and_reviewed_Python_reload_only': True,
            'advance_or_choice_replay_allowed': False, 'business_pass': False})
        require(answer.get('action') in ('abort', 'reevaluate'), 'Explicit ROOT abort or reevaluate required')
        if answer['action'] == 'abort':
            return frame, {'event': packet, 'policy_gap': blocked, 'operator_abort': True,
                           'event_choice_actions': 0}, True
        # Explicit ROOT response optionally binds a small overlay of reviewed
        # shared Python modules. It never changes the frozen MAIN/host/native.
        try:
            policy.reload(answer.get('reviewed_policy_binding'))
            reload_error = None
        except (ValueError, ImportError, OSError, KeyError, TypeError, SyntaxError) as error:
            reload_error = type(error).__name__ + ': ' + str(error)
            client.checkpoint(name + '-reload-error', {'error': type(error).__name__ + ': ' + str(error),
                'business_pass': False, 'choice_submitted': False})
            # Next iteration is a new read-only query; no original action replay.


def reopen_school(client, data, frame, ordinal):
    prefix = 'i4-event-return-school-' + str(ordinal).zfill(4)
    _, opened = natural._call(client, prefix + '-open', 'ck3_open_ingame_decisions_v1',
        {'expected_revision': frame['revision']}, frame)
    selected, _ = natural._call(client, prefix + '-select-detail', 'ck3_select_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': opened['revision']}, opened)
    proof = natural.observe_decision(client, data, ordinal)
    natural.validate_selected(selected, opened, proof, data['decision_key'])
    return proof


def boundary_interval(client, row, before, initial, elapsed, maximum):
    elapsed, frame = discovery.validate_boundary(client, row, before, initial, elapsed, maximum)
    value = row['result']
    require(not value['requested_interval_complete'] or value['elapsed_hours'] >= 24,
            'Complete event interval cannot claim fewer than 24 actual hours')
    return elapsed, frame


def observe_existing(context, client, data, initial, before, policy):
    elapsed, intervals, events, choices, ordinal = 0, [], [], 0, 0
    maximum = data['maximum_natural_days']
    while elapsed + 24 <= maximum * 24:
        ordinal += 1
        require(ordinal <= maximum + data['maximum_registered_event_choices'],
                'Bounded actual requests exhausted; no zero-hour replay loop')
        row = client.advance_day(days=1, timeout=data['one_day_timeout'], allow_event_boundary=True)
        boundary = row['result'].get('event_boundary') is not None
        if boundary:
            elapsed, frame = boundary_interval(client, row, before, initial, elapsed, maximum)
            interval = {'step_id': row['id'], 'request_ordinal': ordinal, 'elapsed_hours': row['result']['elapsed_hours'],
                'date_raw': frame['date_raw'], 'interval_kind': 'event_boundary',
                'requested_interval_complete': row['result']['requested_interval_complete']}
            intervals.append(interval)  # Preserve this actual time before policy hold.
            while frame.get('active_event') is not None:
                frame, event, aborted = handle_event(context, client, data, frame, ordinal,
                    choices, policy, elapsed=elapsed)
                events.append(event)
                if aborted:
                    return {'status': 'PARTIAL_POLICY_GAP_PRESERVED', 'natural_intervals': intervals,
                        'events': events, 'event_choice_actions': choices, 'elapsed_natural_hours': elapsed,
                        'last_frame': frame, 'final_decision': None}
                choices += 1
            proof = reopen_school(client, data, frame, ordinal)
        else:
            elapsed = natural.validate_day(row, before, initial, elapsed, maximum)
            proof = natural.observe_decision(client, data, ordinal,
                front_frame=natural.day_observation_frame(client, row))
            intervals.append({'step_id': row['id'], 'request_ordinal': ordinal, 'elapsed_hours': row['result']['elapsed_hours'],
                'date_raw': proof['frame']['date_raw'], 'interval_kind': 'complete_natural_day',
                'requested_interval_complete': True})
        require(natural.frame_identity(proof['frame'])[:3] == natural.frame_identity(initial)[:3] and
                proof['frame']['date_raw'] - initial['date_raw'] == elapsed,
                'School re-observation crossed actual contiguous natural duration')
        intervals[-1]['confirm_enabled'] = proof['confirm_enabled']
        before = proof['frame']
        if proof['confirm_enabled']:
            return {'status': 'PARTIAL_EXISTING_COOLDOWN_OBSERVED', 'natural_intervals': intervals,
                'events': events, 'event_choice_actions': choices, 'elapsed_natural_hours': elapsed,
                'last_frame': before, 'final_decision': proof}
    return {'status': 'NATURAL_DURATION_CAP_WITHOUT_EXPIRY', 'natural_intervals': intervals,
        'events': events, 'event_choice_actions': choices, 'elapsed_natural_hours': elapsed,
        'last_frame': before, 'final_decision': None}


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    seed = {k: context['saved_campaign'][k] for k in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')}
    origin = natural.validate_origin(natural.base._checked_json(context['case_inputs']['origin_metadata']), seed, data)
    client.retain_process()
    initial = client.snapshot()
    require(initial['played_character']['character_id'] == seed['player_id'] and initial['date_raw'] == seed['date_raw'],
            'Initial original0240 identity/date differs')
    first = reopen_school(client, data, initial, 0)
    require(first['confirm_enabled'] is False, 'Initially enabled school cannot qualify existing flag disappearance')
    saved, after_save = natural._call(client, 'i4-continuation-initial-save-once', 'ck3_save_checkpoint',
        {'expected_revision': first['frame']['revision']}, first['frame'])
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original initial SAVE unavailable')
    initial_saved = natural.read_saved(context, saved['checkpoint'], initial['date_raw'], data, True)
    client.checkpoint('i4-continuation-origin', {'initial_saved': initial_saved, 'origin': origin,
        'initial_frame': initial, 'initial_decision': first, 'existing_cooldown_only': True})
    observed = observe_existing(context, client, data, initial, after_save, ReviewedPolicy(context))
    final, saved_facts = observed['final_decision'], None
    if final is not None:
        saved, _ = natural._call(client, 'i4-continuation-final-save-once', 'ck3_save_checkpoint',
            {'expected_revision': final['frame']['revision']}, final['frame'])
        require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original final SAVE unavailable')
        saved_facts = natural.read_saved(context, saved['checkpoint'], final['frame']['date_raw'], data, False)
    facts = {'schema': 'ck3-mod-acceptance-i4-existing-cooldown-event-continuation-v1',
        'run_id': context['run_id'], 'product': context['product'], 'case': context['case'],
        'scope': data['scope'], **observed, 'initial_saved': initial_saved, 'saved': saved_facts,
        'case_contract_qualified': final is not None, 'gui_contract_qualified': final is not None,
        'business_contract_applicable': True, 'business_pass': final is not None, 'product_release_pass': False,
        'initial_confirm_enabled': False, 'school_choice_actions': 0, 'army_material_credit': False,
        'semantic_decision_ready': False, 'normal_close_pending': True,
        'fresh_full_365_cycle': None, 'exact_expiry_date': None, 'cold_reload': None,
        'formal_I3b': None, 'C3': None, 'I4_complete': None}
    client.checkpoint(RESULT, facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / (RESULT + '.json')
    if not path.is_file():
        return {'status': 'NOT_RUN_OR_PRESERVED_FAILURE', 'business_pass': False,
                'business_contract_applicable': True, 'product_release_pass': False}
    facts = natural.base.read_json(path)
    data = context['case_contract']
    require(all(facts[k] == context[k] for k in ('run_id', 'product', 'case')) and
            facts['school_choice_actions'] == 0 and 0 <= facts['event_choice_actions'] <= 1 and
            facts['army_material_credit'] is False and facts['semantic_decision_ready'] is False and
            facts['product_release_pass'] is False and all(facts[k] is None for k in
                ('fresh_full_365_cycle', 'exact_expiry_date', 'cold_reload', 'formal_I3b', 'C3', 'I4_complete')),
            'Partial continuation crossed case or unsupported credit')
    prior, total = data['saved_campaign']['date_raw'], 0
    intervals = facts['natural_intervals']
    require(isinstance(intervals, list) and len({row['step_id'] for row in intervals}) == len(intervals),
            'Distinct original natural requests required')
    for ordinal, interval in enumerate(intervals, 1):
        hours = interval['elapsed_hours']
        require(interval['request_ordinal'] == ordinal and type(hours) is int and
                (24 <= hours < 48 if interval['interval_kind'] == 'complete_natural_day' else 0 <= hours < 48) and
                interval['date_raw'] == prior + hours, 'Contiguous actual elapsed interval required')
        prior, total = interval['date_raw'], total + hours
    require(total == facts['elapsed_natural_hours'] and total <= 24 * data['maximum_natural_days'],
            'Actual natural duration exceeded original cap')
    require(len(intervals) <= data['maximum_natural_days'] + data['maximum_registered_event_choices'] and
            all(row.get('confirm_enabled') is False for row in intervals[:-1]),
            'Observation continued past enabled school or original bounded requests')
    choices = [event for event in facts['events'] if event.get('event_choice_actions') == 1]
    require(len(choices) == facts['event_choice_actions'] and
            all(event['old_instance_gone'] is True and event['army_material_credit'] is False and
                event['event']['typed_context']['event_definition_key'] == 'bookmark.1070' and
                event['recommendation']['selected_native_option_index'] == 2 and
                event['recommendation']['selected_option_number'] == 3 for event in choices),
            'Original sole reviewed event choice evidence differs')
    for event in choices:
        packet = event['event']
        original = natural.base._checked_json(packet['original_result_ref'])
        require(len(original['rows']) == 1 and original['rows'][0]['result'] == packet['original_result'],
                'Original typed event result differs')
        qualified_context(packet, context)
        qualified_recommendation(event['recommendation'], context)
        selected = natural.base._checked_json(event['original_selection_result_ref'])
        require(len(selected['rows']) == 1, 'Original sole option result required')
        from ck3_mod_acceptance_client import CaseClient
        class VerifiedFrame:
            validate_frame = CaseClient.validate_frame
            manifest = {'game': context['shared_game']}
            _binding = None
        reader = VerifiedFrame()
        discovery.same_event_frame(reader, packet['frame'], packet['after_frame'])
        observed = after_choice(reader, packet['after_frame'], selected['rows'][0], event['selection_step_id'])
        require(observed == event['actual_after_snapshot'], 'Original selected after-snapshot differs')
    if facts['business_pass']:
        require(facts['status'] == 'PARTIAL_EXISTING_COOLDOWN_OBSERVED' and
                facts['initial_saved']['school_cooldown_present'] is True and facts['initial_saved']['headless'] is True and
                facts['initial_saved']['save_body_reads'] == 1 and facts['initial_saved']['baseline_body_reads'] == 0 and
                facts['saved']['school_cooldown_present'] is False and facts['saved']['headless'] is True and
                facts['saved']['save_body_reads'] == 1 and facts['saved']['baseline_body_reads'] == 0 and
                facts['final_decision']['confirm_enabled'] is True and
                Path(facts['initial_saved']['preserved_checkpoint']['path']).resolve() !=
                Path(facts['saved']['checkpoint']['path']).resolve(),
                'Fresh initial/final saved flag/headless evidence incomplete')
    else:
        require(facts['status'] in ('PARTIAL_POLICY_GAP_PRESERVED', 'NATURAL_DURATION_CAP_WITHOUT_EXPIRY') and
                facts['saved'] is None and facts['final_decision'] is None,
                'Unfinished continuation gained expiry credit')
    return {**facts, 'verification_scope': data['scope'] + '; shared normal close independently required'}
