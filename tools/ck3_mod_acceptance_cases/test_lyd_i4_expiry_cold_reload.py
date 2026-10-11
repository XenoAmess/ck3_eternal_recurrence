"""Eight inert source-contract regressions; no CK3, SDK or real SAVE input."""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

options = argparse.ArgumentParser(add_help=False)
options.add_argument('--repo-root', type=Path)
options.add_argument('--fixture-root', type=Path)
selected, remaining = options.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
REPO = selected.repo_root or next((parent for parent in Path(__file__).resolve().parents
    if (parent / 'tools/ck3_mod_acceptance.py').is_file()), None)
if REPO is None:
    raise ValueError('External candidate tests require explicit --repo-root')
REPO = REPO.resolve()
PACKAGE = (selected.fixture_root or Path(tempfile.gettempdir())).resolve()
sys.path.insert(0, str(REPO / 'tools'))
spec = importlib.util.spec_from_file_location('ck3_mod_acceptance_cases._i4_cold_candidate',
    Path(__file__).with_name('lyd_i4_expiry_cold_reload_adapter.py'))
cold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cold)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class ColdContract(unittest.TestCase):
    def setUp(self):
        # Temporary receipts are inert and scoped to this B-only test directory.
        self.temp = tempfile.TemporaryDirectory(prefix='inert-', dir=PACKAGE)
        self.root = Path(self.temp.name).resolve()
        if not self.root.is_relative_to(PACKAGE):
            raise RuntimeError('Temporary test root is outside the candidate package')
        self.addCleanup(self.temp.cleanup)
        self.original_contract = cold.natural.contract()
        self.run_id = 'inert-machine--li-yu-dao--R0056'
        self.run = self.root / self.run_id
        (self.run / 'case-output').mkdir(parents=True)
        self.seed = {'save': str(self.run / 'expiry-final.DO-NOT-READ'), 'bytes': 123456,
            'sha256': 'a' * 64, 'player_id': 31254,
            'date_raw': self.original_contract['saved_campaign']['date_raw'] + 24}
        self.close = {'normal_close_qualified': True, 'retained_handle': {'actual_retained_os0': True},
            'native_zero_proof': {'inert': True}, 'host_finished_at': 'inert',
            'managed_thread_finished': True, 'cleanup_ok': True, 'host_error': None,
            'root_normal_gui_review': {'inert': True}}
        self.original = {'schema': 'ck3-mod-acceptance-i4-existing-cooldown-result-v1',
            'run_id': self.run_id, 'product': 'li-yu-dao', 'case': 'i4-existing-school-cooldown',
            'scope': 'PARTIAL_EXISTING_COOLDOWN_OBSERVATION', 'case_contract_qualified': True,
            'gui_contract_qualified': True, 'business_contract_applicable': True, 'business_pass': True,
            'product_release_pass': False, 'initial_flag': {'initial_flag_present': True},
            'initial_confirm_enabled': False, 'final_confirm_enabled': True, 'school_choice_actions': 0,
            'initial_saved': {'school_cooldown_present': True, 'headless': True, 'save_body_reads': 1,
                'baseline_body_reads': 0, 'preserved_checkpoint': {'path': str(self.run / 'initial.DO-NOT-READ')}},
            'saved': {'school_cooldown_present': False, 'headless': True, 'save_body_reads': 1,
                'baseline_body_reads': 0, 'checkpoint': {'path': self.seed['save'], 'size': self.seed['bytes'],
                    'sha256': self.seed['sha256'], 'date_raw': self.seed['date_raw']}},
            'natural_intervals': [{'step_id': 'inert-day-1', 'elapsed_hours': 24,
                'date_raw': self.seed['date_raw'], 'confirm_enabled': True}],
            'elapsed_natural_hours': 24, 'elapsed_natural_days': 1, 'days_are_actual_simulation_duration': True,
            'normal_close_pending': True, 'cold_reload': None, **{key: None for key in cold.CREDIT_LIMITS}}
        self.runtime = {'path': str(self.root / 'manifest.NOT-OPENED'), 'bytes': 321, 'sha256': 'b' * 64}
        self.context = {'case_contract': cold.contract(), 'product': 'li-yu-dao', 'case': 'i4-expiry-cold-reload',
            'runtime_manifest': self.runtime, 'saved_campaign': deepcopy(self.seed)}
        self.publish()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        return pin(path)

    def publish(self, *, exit_code=0, argv_case='i4-existing-school-cooldown', run_id=None):
        original_path = self.run / 'case-output/i4-existing-school-cooldown-case-result.json'
        self.write(original_path, self.original)
        verified = cold.natural.verify_case({'case_contract': self.original_contract,
            'product': 'li-yu-dao', 'case': 'i4-existing-school-cooldown', 'run_id': self.run_id,
            'output': str(original_path.parent)})
        stdout = self.write(self.root / 'verify.stdout.json', {**verified, 'normal_close': self.close,
            'case_acceptance_pass': True, 'qualified_boundary_pass': True})
        prepared = self.write(self.root / 'prepared.json', {'schema': 'ck3-mod-acceptance-prepared-case-v1',
            'product': 'li-yu-dao', 'case': 'i4-existing-school-cooldown', 'runtime_manifest': self.runtime,
            'contract': pin(REPO / 'tools/ck3_mod_acceptance_cases/lyd_i4_natural_expiry.json'),
            'case_inputs': {}, 'startup': {'saved_campaign': self.original_contract['saved_campaign']}})
        frozen = self.write(self.root / 'frozen.json', {'run_id': self.run_id, 'runtime_manifest': self.runtime})
        run = self.write(self.root / 'run.json', {'schema': 'ck3-mod-acceptance-run-context-v1',
            'product': 'li-yu-dao', 'case': 'i4-existing-school-cooldown', 'run_id': run_id or self.run_id,
            'run_dir': str(self.run), 'prepared_case': prepared, 'frozen_argv': frozen})
        command = self.write(self.root / 'verify.command.json', {'exit_code': exit_code, 'stdout': stdout,
            'argv': ['inert-python', str(REPO / 'tools/ck3_mod_acceptance.py'), 'verify',
                '--product', 'li-yu-dao', '--case', argv_case,
                '--prepared-case', prepared['path'], '--run-context', run['path']]})
        self.context['case_inputs'] = {'expected_upstream_run_id': self.run_id,
            'natural_expiry_verified_origin': {'prepared_case': prepared, 'run_context': run,
                'public_verify_command': command}}

    def model(self, frame):
        value = {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True, 'available': True,
            'decision_key': 'lyd_change_school_decision', 'detail_decision_key': 'lyd_change_school_decision',
            'matching_row_count': 1, 'native_revision': frame['native_revision'], 'connection_generation': 1,
            'game_pid': 123, 'played_character_id': 31254, 'date_raw': self.seed['date_raw'],
            'detail_actor_reference_key': 31254}
        for key in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified', 'gui_owner_binding_verified',
                'decisions_tree_complete', 'decisions_root_visible', 'row_owner_verified', 'detail_tree_complete',
                'detail_root_visible', 'detail_definition_available', 'detail_definition_matches_target',
                'detail_actor_binding_verified'):
            value[key] = True
        return value

    def tree(self):
        rows = [('', 'decisiondetail_view', {'effective_visible': True}), ('0', 'footer', {'child_count': 7}),
            ('0/0', 'cost', {}), ('0/2', 'regular', {'child_count': 3}),
            ('0/2/2', 'cram_study_start_tutorial_highlight', {}),
            ('0/2/1', '', {'enabled': True, 'effective_visible': True}),
            ('0/3', 'custom', {'child_count': 2}), ('0/3/0', 'back', {}),
            ('0/3/1', '', {'enabled': False, 'effective_visible': False})]
        widgets = [{'child_path': path, 'runtime_name': name, **fields} for path, name, fields in rows]
        return {'schema': 'ck3-native-gui-window-tree-inspection-v1', 'window_kind': 'decision_detail',
            'scope_root_name': 'decisiondetail_view', 'read_only': True, 'accepted': True, 'status': 'available',
            'root_available': True, 'truncated': False, 'widgets': widgets, 'widget_count': len(widgets)}

    def saved_graphs(self):
        actor = {'character_id': 31254, 'rite_id': 169, 'landed_data': [],
            'variables': {'lyd_enabled': {'present': True}}}
        faith = {'id': 107, 'heads': {'religious_head': '4294967295', 'religious_head_title': None}, 'main_rite': '169'}
        rite = {'id': 169, 'faith': '107', 'heads': {'head_of_rite': '31254'}}
        return actor, faith, rite

    def cold_facts(self):
        data = {**cold.contract(), 'saved_campaign': self.seed}
        saved = cold.evaluate_cold_saved(None, *self.saved_graphs(), data)
        saved.update(checkpoint={'path': str(self.root / 'new-cold.DO-NOT-READ'), 'size': 54321,
            'sha256': 'c' * 64, 'date_raw': self.seed['date_raw']}, save_body_reads=1, baseline_body_reads=0,
            additional_checkpoint_copies=0)
        frame = {'diagnostics': {'bridge_pid': 123, 'connection_generation': 1}, 'played_character': {'character_id': 31254},
            'date_raw': self.seed['date_raw'], 'native_revision': 2, 'revision': 3, 'paused': True, 'active_event': None}
        return {'initial_frame': deepcopy(frame), 'decision': {'frame': frame, 'model_before': self.model(frame),
            'model_after': self.model(frame), 'detail_tree': self.tree(), 'confirm_enabled': True, 'decision_executed': False},
            'cold_saved': saved, 'natural_days': 0, 'school_choice_actions': 0, 'cold_SAVE_actions': 1,
            **{key: None for key in cold.CREDIT_LIMITS}, 'product_release_pass': False}

    def test_01_qualified_origin_and_reusable_run_binding_without_seed_read(self):
        from ck3_mod_acceptance import Selection
        selected = SimpleNamespace(adapter_path=Path(cold.__file__), locations={'repo_root': REPO})
        self.assertEqual(Selection.load_adapter(selected).contract(), cold.contract())
        original = Path.read_bytes
        def no_seed(path):
            if path.resolve() == Path(self.seed['save']).resolve():
                raise RuntimeError('Seed body must not be opened by adapter')
            return original(path)
        with patch.object(Path, 'read_bytes', no_seed):
            self.assertEqual(cold.upstream(self.context)['seed'], self.seed)
        # Permanent config is reusable; selection is explicit input, not hard R56.
        self.assertNotIn('expected_upstream_attempt_suffix', cold.contract())

    def test_02_missing_actual_refs_and_expected_run_reject(self):
        for mutate in ('prepared', 'expected'):
            context = deepcopy(self.context)
            if mutate == 'prepared': context['case_inputs']['natural_expiry_verified_origin']['prepared_case'] = None
            else: context['case_inputs']['expected_upstream_run_id'] = None
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): cold.upstream(context)

    def test_03_original_verify_failure_or_wrong_case_reject(self):
        for values in ({'exit_code': 2}, {'argv_case': 'i3b-formal-b5'}):
            self.publish(**values)
            with self.subTest(values=values), self.assertRaises(ValueError): cold.upstream(self.context)

    def test_04_same_manifest_and_selected_original_run_required(self):
        for kind in ('manifest', 'selected-run', 'run-vs-frozen'):
            self.publish()
            context = deepcopy(self.context)
            if kind == 'manifest': context['runtime_manifest']['sha256'] = 'd' * 64
            elif kind == 'selected-run': context['case_inputs']['expected_upstream_run_id'] = 'inert--R0055'
            else: self.publish(run_id='inert--R0055'); context = deepcopy(self.context)
            with self.subTest(kind=kind), self.assertRaises(ValueError): cold.upstream(context)

    def test_05_exact_expiry_final_save_not_initial_or_other_world(self):
        for key, value in (('save', str(self.root / 'initial.DO-NOT-READ')), ('sha256', 'd' * 64),
                ('date_raw', self.original_contract['saved_campaign']['date_raw']), ('bytes', 123455)):
            context = deepcopy(self.context); context['saved_campaign'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): cold.upstream(context)

    def test_06_normal_gui_os_native_close_required_not_failure_cleanup(self):
        for key, value in (('normal_close_qualified', False), ('native_zero_proof', None),
                ('host_error', 'preserved failure'), ('root_normal_gui_review', None),
                ('retained_handle', {'actual_retained_os0': False})):
            self.close[key] = value; self.publish()
            with self.subTest(key=key), self.assertRaises(ValueError): cold.upstream(self.context)
            self.close[key] = {'normal_close_qualified': True, 'native_zero_proof': {'inert': True},
                'host_error': None, 'root_normal_gui_review': {'inert': True},
                'retained_handle': {'actual_retained_os0': True}}[key]

    def test_07_cold_saved_hor_flag_faith_and_membership_are_explicit(self):
        data = {**cold.contract(), 'saved_campaign': self.seed}
        observed = cold.evaluate_cold_saved(None, *self.saved_graphs(), data)
        self.assertTrue(observed['head_of_rite_explicitly_observed'])
        for kind in ('hor', 'flag', 'faith', 'membership'):
            actor, faith, rite = self.saved_graphs()
            if kind == 'hor': rite['heads']['head_of_rite'] = '999'
            elif kind == 'flag': actor['variables']['lyd_school_cooldown'] = {'present': True}
            elif kind == 'faith': faith['main_rite'] = '170'
            else: actor['variables'] = {}
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                cold.evaluate_cold_saved(None, actor, faith, rite, data)

    def test_08_cold_enabled_frame_single_new_body_and_partial_credit(self):
        origin, data = cold.upstream(self.context), cold.contract()
        self.assertTrue(cold.assessment(self.cold_facts(), origin, data))
        for kind in ('disabled', 'wrong-frame', 'seed-reparse', 'extra-copy', 'full-cycle', 'action'):
            facts = self.cold_facts()
            if kind == 'disabled': facts['decision']['detail_tree']['widgets'][5]['enabled'] = False
            elif kind == 'wrong-frame': facts['decision']['frame']['date_raw'] += 1
            elif kind == 'seed-reparse': facts['cold_saved']['baseline_body_reads'] = 1
            elif kind == 'extra-copy': facts['cold_saved']['additional_checkpoint_copies'] = 1
            elif kind == 'full-cycle': facts['fresh_full_365_cycle'] = True
            else: facts['school_choice_actions'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError): cold.assessment(facts, origin, data)

    def test_09_existing_wrapper_uses_exact_execution_and_selected_context(self):
        self.assertEqual(cold.upstream(self.context)['seed'], self.seed)
        source = self.root / 'inert-source'
        env = {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1',
               'PYTHONPATH': str(source / 'tools')}
        self.runtime = self.write(self.root / 'manifest.json', {
            'schema': 'ck3-mod-acceptance-shared-runtime-v1',
            'entry_environment': {'PYTHONPATH_parts': [
                {'root_key': 'source_root', 'relative_path': 'tools'}]}})
        self.context.update(runtime_manifest=self.runtime, repo_root=str(REPO))
        runtime = self.root / 'runtime.local.json'
        python = Path(sys.executable).resolve()
        self.write(runtime, {'schema': 'ck3-mod-acceptance-runtime-v1',
            'manifest': self.runtime, 'paths': {'source_root': str(source)},
            'repo_root': str(REPO), 'python': str(python)})
        self.publish()
        bundle = self.context['case_inputs']['natural_expiry_verified_origin']
        run_path = Path(bundle['run_context']['path'])
        run = json.loads(run_path.read_bytes())
        frozen_path = Path(run['frozen_argv']['path'])
        frozen = json.loads(frozen_path.read_bytes())
        frozen.update(runtime_environment=env, source_root=str(source),
                      argv=[str(python), 'inert-host.NOT-EXECUTED'])
        run['frozen_argv'] = self.write(frozen_path, frozen)
        bundle['run_context'] = self.write(run_path, run)
        command_path = Path(bundle['public_verify_command']['path'])
        command = json.loads(command_path.read_bytes())
        entry = REPO / 'tools/ck3_mod_acceptance.py'
        public_args = ['verify', '--runtime', str(runtime), *command['argv'][3:]]
        wrapper = self.root / 'with_selected_environment.py'
        wrapper.write_bytes(b'inert wrapper; never executed')
        real_bytes = cold.command_bytes
        self.assertEqual(real_bytes(pin(wrapper)), wrapper.read_bytes())
        bad_sha = {**pin(wrapper), 'sha256': '0' * 64}
        with self.assertRaises(ValueError):
            real_bytes(bad_sha)
        fixed_source = {'path': str(wrapper), 'bytes': 2905,
            'sha256': '4e98c85d8aa9784b5b0f2958944affbb43ac489d0081b9c54e3fd0c99672a096'}
        def source_or_stdio(row):
            if row == fixed_source:
                return b''
            return real_bytes(row)
        def stderr(record):
            path = self.root / 'wrapper.stderr'
            path.write_text(json.dumps(record) + '\n', encoding='utf-8')
            return pin(path)
        marker = {'mode': 'EXECUTE_ONCE',
            'public_argv': [str(python), '-B', '-X', 'utf8', str(entry), *public_args],
            'cwd': str(REPO), 'selected_runtime_environment': env,
            'environment_applied_to_public_process': True,
            'queue_mode': 'Selected by CaseClient before each submission; no retry fallback',
            'business_acceptance': 'NOT_ASSESSED'}
        command.update(argv=[str(python), '-B', '-X', 'utf8', str(wrapper),
            '--entry', str(entry), '--execute', '--', *public_args],
            cwd=str(REPO), stderr=stderr(marker))
        bundle['public_verify_command'] = self.write(command_path, command)
        context = deepcopy(self.context)
        with patch.object(cold, 'command_bytes', side_effect=source_or_stdio):
            self.assertEqual(cold.upstream(context)['seed'], self.seed)
            for case in ('missing-execute', 'emit-only', 'wrong-entry', 'cross-context',
                         'environment', 'marker-argv', 'cwd', 'exit2'):
                value, record = deepcopy(command), deepcopy(marker)
                current = deepcopy(context)
                if case == 'missing-execute':
                    value['argv'].remove('--execute')
                elif case == 'emit-only':
                    record['mode'] = 'EMIT_ONLY'
                elif case == 'wrong-entry':
                    value['argv'][6] = str(self.root / 'other/ck3_mod_acceptance.py')
                elif case == 'cross-context':
                    other = str(self.root / 'other-context.json')
                    value['argv'][value['argv'].index('--run-context') + 1] = other
                    record['public_argv'][record['public_argv'].index('--run-context') + 1] = other
                elif case == 'environment':
                    record['selected_runtime_environment']['PYTHONPATH'] = 'other-source'
                elif case == 'marker-argv':
                    record['public_argv'][-1] = 'different-context'
                elif case == 'cwd':
                    record['cwd'] = str(self.root)
                else:
                    value['exit_code'] = 2
                value['stderr'] = stderr(record)
                current['case_inputs']['natural_expiry_verified_origin']['public_verify_command'] = self.write(command_path, value)
                with self.subTest(case=case), self.assertRaises(ValueError):
                    cold.upstream(current)


if __name__ == '__main__':
    unittest.main(verbosity=2)
