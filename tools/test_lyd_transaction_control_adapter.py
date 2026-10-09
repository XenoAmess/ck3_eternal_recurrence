"""Portable tests for the product control; no CK3, SDK, process or screen."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from ck3_mod_acceptance_cases import lyd_transaction_control_adapter as adapter
from ck3_mod_acceptance_prepare import CONFIG_NAMES, pin


def frame(instance=121, revision=2):
    return {'snapshot_id': 'native:' + str(revision - 1), 'revision': revision,
        'native_revision': revision - 1, 'date_raw': 53144712, 'paused': True, 'map_ready': True,
        'episode_projection': 'native_campaign', 'played_character': {'character_id': 31254},
        'active_event': {'instance_id': instance}, 'diagnostics': {'bridge_pid': 901, 'connection_generation': 1}}


def scope(kind, key, identity):
    return {'status': 'available', 'type_key': kind,
        'typed_identity': {'status': 'available', 'kind': kind, key: identity}}


def event_packet(actual, definition='lyd_factory_diag.20'):
    return {'status': 'available', 'queried_snapshot_id': actual['snapshot_id'],
        'queried_revision': actual['revision'], 'queried_native_revision': actual['native_revision'],
        'current_event_window_context': {'schema': 'current-event-window-context-v1', 'status': 'available',
            'snapshot_revision': actual['native_revision'], 'date_raw': actual['date_raw'],
            'current_event_instance_id': actual['active_event']['instance_id'], 'event_definition_key': definition,
            'window_match_count': 1, 'root_scope': scope('character', 'character_id', 31254),
            'saved_scopes': [{'name': 'lyd_i3b_actor', 'scope': scope('character', 'character_id', 31254)},
                {'name': 'new_title', 'scope': scope('landed_title', 'title_id', 18373)}],
            'readiness': {key: True for key in ('event_definition_identity_ready', 'root_scope_ready',
                                             'saved_scopes_ready', 'option_presentation_ready')},
            'options': [{'rendered_index': 0, 'native_option_index': 0, 'shown': True,
                         'enabled': True, 'fallback': False, 'cancel': False}]}}


def cache_packet(actual, data):
    return {'queried_snapshot_id': actual['snapshot_id'], 'queried_revision': actual['revision'],
        'queried_native_revision': actual['native_revision'], 'date_raw': actual['date_raw'],
        'game_pid': 901, 'connection_generation': 1, 'player_character_id': 31254,
        'native_result': {'actor_cached_succession': {'available': True, 'read_only': True,
            'roster_complete': True, 'native_count': 45, 'played_character_id': 31254,
            'played_character_full_id': 31254, 'date_raw': 53144712,
            'complete_cached_successor_ids': list(data['baseline_cached_succession'])}}}


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return pin(path)


def saved_fixture(directory, data, completed=1, title_holder=None, political_change=False):
    ids = ' '.join(str(value) for value in data['baseline_cached_succession'])
    actor = '31254={\nalive_data={ variables={ data={ { flag="' + data['completed_variable'] + '" data={ type=value identity=' + str(completed * 100000) + '} } } } }\nlanded_data={ succession={ ' + ids + ' } }\n}\n'
    titles = ''
    for title_id in data['political_title_ast_sha256']:
        titles += title_id + '={\nholder=31254\nheir={ 40526 40695 }\n}\n'
    new_title = '18373={\nname="empty_transaction_control"\n' + ('' if title_holder is None else 'holder=' + str(title_holder) + '\n') + '}\n'
    raw = ('living={\n' + actor + '}\ndead_unprunable={\n}\nlanded_titles={\n' + titles + new_title + '}\ndynasties={\n}\n').encode()
    reader = adapter._reader(TOOLS.parent)
    data = copy.deepcopy(data)
    for identity, entries in reader.title_database_records(raw.decode()):
        if str(identity) in data['political_title_ast_sha256']:
            data['political_title_ast_sha256'][str(identity)] = reader.ast_sha(entries)
    if political_change:
        raw = raw.replace(b'heir={ 40526 40695 }', b'heir={ 40526 39979 }', 1)
    path = directory / 'independent-checkpoint.ck3'
    path.write_bytes(raw)
    return data, {'path': str(path), 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
        'status': 'saved', 'date_raw': 53144712, 'episode_projection': 'native_campaign'}


class AdmissionTests(unittest.TestCase):
    def test_pure_saved_admission_uses_real_scope_name_and_no_action(self):
        data, actual = adapter.contract(), frame()
        packet = event_packet(actual)
        unchanged = copy.deepcopy(packet)
        result = adapter.admit_saved_startup_event({'state_dir': '/unused', 'expected': data['expected']}, actual, packet)
        self.assertEqual(set(result), set(data['expected']) | {'proof', 'business_pass'})
        self.assertEqual(result['proof']['new_title_id'], 18373)
        self.assertEqual(result['proof']['actions_submitted'], 0)
        self.assertIs(result['business_pass'], False)
        self.assertEqual(packet, unchanged)

    def test_malformed_or_crossed_typed_admission_fails(self):
        data, actual = adapter.contract(), frame()
        mutations = [
            lambda p: p.update(queried_revision=3),
            lambda p: p['current_event_window_context'].update(event_definition_key='lyd_factory_diag.2'),
            lambda p: p['current_event_window_context']['root_scope']['typed_identity'].update(character_id=65865),
            lambda p: p['current_event_window_context']['saved_scopes'][1].update(name='lyd_i3b_new_title'),
            lambda p: p['current_event_window_context']['saved_scopes'][1]['scope']['typed_identity'].update(title_id=18374),
            lambda p: p['current_event_window_context']['options'][0].update(enabled=False),
            lambda p: p['current_event_window_context']['options'][0].update(native_option_index=1),
            lambda p: p['current_event_window_context']['readiness'].update(root_scope_ready=False),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                packet = event_packet(actual)
                mutate(packet)
                with self.assertRaises(ValueError):
                    adapter.admit_saved_startup_event({'expected': data['expected']}, actual, packet)

    def test_cache_requires_complete_order_and_exact_frame(self):
        data, actual = adapter.contract(), frame()
        self.assertEqual(adapter.observe_cache(actual, cache_packet(actual, data), data), data['baseline_cached_succession'])
        for change in ('order', 'incomplete', 'generation'):
            packet = cache_packet(actual, data)
            if change == 'order':
                packet['native_result']['actor_cached_succession']['complete_cached_successor_ids'].reverse()
            elif change == 'incomplete':
                packet['native_result']['actor_cached_succession']['roster_complete'] = False
            else:
                packet['connection_generation'] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                adapter.observe_cache(actual, packet, data)


class PreparationTests(unittest.TestCase):
    def inputs(self, root):
        data = adapter.contract()
        product, overlay = root / 'production', root / 'overlay'
        product_rows, overlay_rows = [], []
        for name in ['descriptor.mod'] + ['common/p%02d.txt' % i for i in range(70)]:
            row = write(product / name, b'name="formal"\n' if name == 'descriptor.mod' else b'# formal\n')
            product_rows.append({**row, 'path': name})
        for name in ['descriptor.mod', 'common/effect.txt', 'common/trigger.txt', 'events/control.txt',
                     'localization/english/control.yml', 'localization/simp_chinese/control.yml']:
            row = write(overlay / name, b'name="control"\n' if name == 'descriptor.mod' else b'# control\n')
            overlay_rows.append({**row, 'path': name})
        data['overlay_files'] = overlay_rows
        inventory = root / 'product-inventory.json'
        inventory.write_text(json.dumps({'source_head': data['production_source_head'], 'files': product_rows}), encoding='utf-8')
        seed = write(root / 'seed.ck3', b'fixture seed never copied or parsed by adapter')
        data['saved_campaign']['bytes'], data['saved_campaign']['sha256'] = seed['bytes'], seed['sha256']
        configs = {name: write(root / 'plain' / name, b'' if 'presets' in name else b'fixture original settings') for name in CONFIG_NAMES}
        context = {'product': 'li-yu-dao', 'case': 'transaction-only-control', 'case_contract': data,
            'output': str(root / 'output'), 'state_dir': str(root / 'state'), 'case_inputs': {
                'product_dir': str(product), 'product_inventory': pin(inventory), 'overlay_dir': str(overlay),
                'plain_configuration': configs}, 'saved_campaign': {**data['saved_campaign'], 'save': seed['path']}}
        return context, data

    def test_two_mods_four_configs_complete_inventory_without_seed_or_registrar(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context, data = self.inputs(root)
            with patch.object(adapter, 'contract', return_value=data):
                prepared = adapter.prepare_case(context)
            self.assertEqual(len(prepared['files']), 84)
            inventory = adapter.read_json(prepared['startup']['saved_campaign']['product_inventory'])
            self.assertEqual(inventory['enabled_mods'], ['mod/product.mod', 'mod/transaction_control.mod'])
            self.assertEqual(len(inventory['product_files']), 79)
            self.assertEqual(set(inventory), {'schema', 'profile_path', 'enabled_mods', 'product_files'})
            self.assertTrue(all(Path(row['path']).read_bytes() is not None for row in inventory['product_files']))
            for directory in ('save games', 'logs', 'run'):
                self.assertFalse((root / 'state/profile' / directory).exists())
            self.assertEqual(Path(prepared['startup']['saved_campaign']['save']), root / 'seed.ck3')
            self.assertFalse((root / 'state/profile/seed.ck3').exists())
            self.assertNotIn('fixture_start_policy', prepared['startup'])
            hook = adapter.read_json(prepared['startup']['saved_campaign_startup_case_contract'])
            self.assertEqual(hook['handler']['function'], 'admit_saved_startup_event')
            self.assertEqual(hook['expected'], data['expected'])
            with patch.object(adapter, 'contract', return_value=data), self.assertRaises(ValueError):
                adapter.prepare_case(context)

    def test_missing_plain_configuration_or_changed_mod_is_not_prepared(self):
        for failure in ('configuration', 'changed-file'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                context, data = self.inputs(root)
                if failure == 'configuration':
                    del context['case_inputs']['plain_configuration']['presets.txt']
                else:
                    (root / 'overlay/events/control.txt').write_bytes(b'changed input')
                with patch.object(adapter, 'contract', return_value=data), self.assertRaises(ValueError):
                    adapter.prepare_case(context)


class SavedProofTests(unittest.TestCase):
    def test_independent_checkpoint_numeric_unheld_and_all_political_ast(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, checkpoint = saved_fixture(Path(temporary), adapter.contract())
            facts = adapter.read_saved_control(TOOLS.parent, checkpoint, data)
            self.assertIs(facts['saved_control_qualified'], True)
            self.assertEqual(facts['political_title_ast_sha256'], data['political_title_ast_sha256'])
            self.assertEqual(facts['save_body_reads'], 1)
            self.assertEqual(facts['baseline_body_reads'], 0)
            self.assertIs(facts['business_pass'], False)

    def test_completion_holder_or_full_ast_change_refuses_credit(self):
        for kwargs in ({'completed': 0}, {'title_holder': 31254}, {'political_change': True}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                data, checkpoint = saved_fixture(Path(temporary), adapter.contract(), **kwargs)
                with self.assertRaises(ValueError):
                    adapter.read_saved_control(TOOLS.parent, checkpoint, data)


class FakeClient:
    """The public API boundary only, with original queue rows kept in memory."""
    def __init__(self, root, data, checkpoint, *, bad_after=False, reject_select=False):
        self.output, self.data, self.saved = root / 'output', data, checkpoint
        self.output.mkdir()
        self.frames, self.calls, self.retained = [frame(), frame(777, 3)], [], False
        self.bad_after, self.reject_select = bad_after, reject_select

    def retain_process(self):
        self.retained = True

    def guard(self):
        pass

    def validate_frame(self, actual, require_event_free=True):
        assert require_event_free is False
        return actual

    def snapshot(self, require_event_free=True):
        assert require_event_free is False
        self.current = self.frames.pop(0)
        return self.current

    def execute_plan(self, steps, name, timeout=None):
        self.calls.extend(copy.deepcopy(steps))
        step = steps[0]
        assert step['fresh_revision'] is False and 0 < timeout <= 60
        tool = step['tool']
        if tool == 'ck3_query_current_event_window_context_v1':
            value = event_packet(self.current, 'lyd_factory_diag.20' if len(self.frames) else 'lyd_factory_diag.2')
        elif tool == 'ck3_query_actor_cached_succession_v1':
            value = cache_packet(self.current, self.data)
            if not self.frames and self.bad_after:
                value['native_result']['actor_cached_succession']['complete_cached_successor_ids'].reverse()
        elif tool == 'ck3_select_event_option':
            if self.reject_select:
                raise RuntimeError('original timeout remains unknown')
            value = {'accepted': True, 'event_instance_id': 121, 'option_number': 1, 'option_index': 0}
        elif tool == 'ck3_save_checkpoint':
            value = {'accepted': True, 'step': 'save-checkpoint', 'checkpoint': self.saved}
        elif tool == 'ck3_take_snapshot':
            value = self.snapshot(require_event_free=False)
        else:
            raise AssertionError('Undeclared public tool ' + tool)
        return [{'id': name, 'ok': True, 'result': value}]

    def checkpoint(self, name, value):
        path = self.output / (name + '.json')
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream)
        return path


class OnceFlowTests(unittest.TestCase):
    def run_fixture(self, root, **kwargs):
        data, checkpoint = saved_fixture(root, adapter.contract())
        client = FakeClient(root, data, checkpoint, **kwargs)
        context = {'repo_root': str(TOOLS.parent), 'state_dir': str(root / 'state'), 'output': str(client.output),
            'product': 'li-yu-dao', 'case': 'transaction-only-control', 'run_id': 'synthetic-run', 'case_contract': data}
        return context, client, data

    def test_complete_control_once_dynamic_terminal_and_saved_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, client, data = self.run_fixture(Path(temporary))
            with patch.object(adapter, 'contract', return_value=data):
                result = adapter.run_case(context, client)
                verified = adapter.verify_case(context)
            self.assertTrue(client.retained)
            self.assertTrue(result['transaction_control_pass'])
            self.assertEqual(result['terminal_event_instance_id'], 777)
            selections = [row for row in client.calls if row['tool'] == 'ck3_select_event_option']
            self.assertEqual(len(selections), 1)
            self.assertEqual(selections[0]['args'], {'option_number': 1, 'event_instance_id': 121, 'expected_revision': 2})
            self.assertEqual(len([row for row in client.calls if row['tool'] == 'ck3_save_checkpoint']), 1)
            self.assertIs(verified['business_pass'], False)
            self.assertIs(verified['product_release_pass'], False)

    def test_after_cache_change_or_unknown_selection_never_replays_or_passes(self):
        for kwargs in ({'bad_after': True}, {'reject_select': True}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                context, client, data = self.run_fixture(Path(temporary), **kwargs)
                with patch.object(adapter, 'contract', return_value=data), self.assertRaises((ValueError, RuntimeError)):
                    adapter.run_case(context, client)
                self.assertEqual(len([row for row in client.calls if row['tool'] == 'ck3_select_event_option']), 1)
                self.assertEqual(len([row for row in client.calls if row['tool'] == 'ck3_save_checkpoint']), 0)
                self.assertFalse((client.output / 'transaction-control-case-result.json').exists())

    def test_terminal_observation_allows_transient_empty_or_original_event_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, client, data = self.run_fixture(Path(temporary))
            empty = frame(121, 3)
            empty['active_event'] = None
            client.frames = [frame(), empty, frame(121, 3), frame(888, 3)]
            with patch.object(adapter, 'contract', return_value=data), patch.object(adapter.time, 'sleep'):
                result = adapter.run_case(context, client)
            self.assertEqual(result['terminal_event_instance_id'], 888)
            snapshots = [row for row in client.calls if row['tool'] == 'ck3_take_snapshot']
            self.assertEqual(len(snapshots), 3)
            self.assertEqual(len({row['id'] for row in snapshots}), 3)
            self.assertEqual(len([row for row in client.calls if row['tool'] == 'ck3_select_event_option']), 1)

    def test_terminal_deadline_keeps_unknown_without_selection_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, client, data = self.run_fixture(Path(temporary))
            client.frames = [frame(121, 3)]
            with patch.object(adapter.time, 'monotonic', side_effect=[0, 0, 0, 61, 61]), self.assertRaises(TimeoutError):
                adapter.observe_terminal(client, data)
            self.assertEqual(len(client.calls), 1)
            self.assertEqual(client.calls[0]['tool'], 'ck3_take_snapshot')


if __name__ == '__main__':
    unittest.main()
