"""Regress the R38 unheld-title continuation failure using real diagnostic ASTs."""
from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch
import sys

import build_factory_diagnostic as builder
import validate_factory_diagnostic as validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from extract_auto_upgrade_buildings import Block, parse_clausewitz


class FactoryDiagnosticHeirProbeTests(unittest.TestCase):
    def setUp(self):
        mod = ROOT / 'mod_li_yu_dao'
        factory = (mod / 'common/scripted_effects/lyd_c3_head_factory.txt').read_text(encoding='utf-8-sig')
        commit = (mod / 'common/scripted_effects/lyd_i3b_commit_effects.txt').read_text(encoding='utf-8-sig')
        self.inputs = (factory, commit, '礼与道')
        self.original = builder.generate(*self.inputs)
        self.probe = builder.generate(*self.inputs, heir_log_probe=True, stop_after_holder=True)

    def one(self, block, key):
        rows = [entry.value for entry in block.entries if entry.key == key]
        self.assertEqual(len(rows), 1, key)
        return rows[0]

    def node(self, value):
        if isinstance(value, Block):
            return tuple((entry.key, entry.operator, self.node(entry.value)) for entry in value.entries)
        return value

    def test_removing_four_scope_logs_restores_complete_atomic_transaction(self):
        relative = 'common/scripted_effects/lyd_i3b_commit_effects.txt'
        original, probe = (parse_clausewitz(files[relative]) for files in (self.original, self.probe))
        old_d2 = self.one(original, 'lyd_factory_diag_d2_effect')
        new_d2 = self.one(probe, 'lyd_factory_diag_d2_effect')
        filtered = Block(tuple(row for row in new_d2.entries if row.key not in ('debug_log', 'every_in_list')))
        self.assertEqual(self.node(filtered), self.node(old_d2))
        self.assertEqual(
            self.node(Block(tuple(row for row in probe.entries if row.key != 'lyd_factory_diag_d2_effect'))),
            self.node(Block(tuple(row for row in original.entries if row.key != 'lyd_factory_diag_d2_effect'))))
        logs = [row.value for row in new_d2.entries if row.key == 'debug_log']
        self.assertEqual(logs, [f'"LYD_D2B_HEIR_PROBE_{stage}_{edge}"'
            for stage in ('BEFORE_CREATE', 'AFTER_CREATE', 'AFTER_HOLDER', 'AFTER_RESOLVE')
            for edge in ('BEGIN', 'END')])
        lists = [row.value for row in new_d2.entries if row.key == 'every_in_list']
        self.assertEqual(len(lists), 4)
        for block in lists:
            self.assertEqual([row.key for row in block.entries],
                             ['variable', 'debug_log', 'debug_log_scopes', 'every_title_heir'])
            self.assertEqual(self.one(block, 'variable'), 'lyd_i3b_political_titles')
            heirs = self.one(block, 'every_title_heir')
            self.assertEqual([row.key for row in heirs.entries], ['debug_log', 'debug_log_scopes'])
            self.assertEqual(self.one(block, 'debug_log_scopes'), 'yes')
            self.assertEqual(self.one(heirs, 'debug_log_scopes'), 'yes')

    def test_holder_terminal_preserves_guards_and_removes_D3_continuation(self):
        relative = 'events/lyd_factory_operation_diagnostic.txt'
        old, new = (parse_clausewitz(files[relative]) for files in (self.original, self.probe))
        old_event, new_event = self.one(old, 'lyd_factory_diag.2'), self.one(new, 'lyd_factory_diag.2')
        old_option, new_option = self.one(old_event, 'option'), self.one(new_event, 'option')
        self.assertEqual([row.key for row in new_option.entries], ['name', 'trigger'])
        self.assertEqual(self.one(new_option, 'name'), 'lyd_factory_diag_stop')
        self.assertEqual(self.node(self.one(new_option, 'trigger')), self.node(self.one(old_option, 'trigger')))
        self.assertIsInstance(self.one(old_option, 'hidden_effect'), Block)
        for before, after, excluded in ((old_event, new_event, 'option'), (old, new, 'lyd_factory_diag.2')):
            self.assertEqual(self.node(Block(tuple(row for row in before.entries if row.key != excluded))),
                             self.node(Block(tuple(row for row in after.entries if row.key != excluded))))
        for language in ('english', 'simp_chinese'):
            path = f'localization/{language}/lyd_factory_operation_diagnostic_l_{language}.yml'
            self.assertTrue(self.probe[path].startswith(self.original[path]))
            self.assertEqual(self.probe[path].count(' lyd_factory_diag_stop:0 '), 1)

    def test_invalid_modes_cannot_create_a_partial_holder_probe(self):
        for flags in ({'stop_after_holder': True}, {'control': 'transaction-only', 'heir_log_probe': True},
                      {'heir_log_probe': 1}, {'stop_after_holder': 1}):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                builder.generate(*self.inputs, **flags)


class FactoryDiagnosticControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.overlay = Path(self.temp.name) / 'overlay'
        self.overlay.mkdir()
        mod = ROOT / 'mod_li_yu_dao'
        self.factory = (mod / 'common/scripted_effects/lyd_c3_head_factory.txt').read_text(encoding='utf-8-sig')
        self.commit = (mod / 'common/scripted_effects/lyd_i3b_commit_effects.txt').read_text(encoding='utf-8-sig')

    def materialize(self, control):
        files = builder.generate(self.factory, self.commit, '礼与道', control)
        for name, text in files.items():
            path = self.overlay / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8-sig', newline='\n')

    def validate(self, control):
        output = Path(self.temp.name) / 'validation.json'
        argv = ['validate', '--source-root', str(ROOT), '--overlay', str(self.overlay),
                '--output', str(output), '--control', control]
        with patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
            validator.main()
        return json.loads(output.read_bytes())

    def replace_once(self, relative, old, new):
        path = self.overlay / relative
        text = path.read_text(encoding='utf-8-sig')
        self.assertEqual(text.count(old), 1)
        path.write_text(text.replace(old, new, 1), encoding='utf-8-sig', newline='\n')

    def test_full_diagnostic_retains_inverse_production_ast_contract(self):
        self.materialize('full')
        result = self.validate('full')
        self.assertTrue(all(row['passed'] for row in result['checks']))

    def test_empty_transaction_control_admits_unheld_title_and_stops(self):
        self.materialize('transaction-only')
        result = self.validate('transaction-only')
        self.assertTrue(all(row['passed'] for row in result['checks']))

    def test_r38_held_title_guard_is_rejected(self):
        self.materialize('transaction-only')
        path = self.overlay / 'events/lyd_factory_operation_diagnostic.txt'
        text = path.read_text(encoding='utf-8-sig')
        start = text.index('lyd_factory_diag.2 = {')
        end = text.index('lyd_factory_diag.3 = {', start)
        event = text[start:end]
        self.assertEqual(event.count('lyd_factory_diag_unheld_title_trigger'), 2)
        # R38 used the same wrong held-title condition on both display and
        # option. Equality of those guards alone cannot detect this failure.
        event = event.replace('lyd_factory_diag_unheld_title_trigger', 'lyd_factory_diag_title_trigger')
        path.write_text(text[:start] + event + text[end:], encoding='utf-8-sig', newline='\n')
        with self.assertRaisesRegex(ValueError, 'D2_terminal_requires_unheld_title_and_completion_marker'):
            self.validate('transaction-only')

    def test_completion_marker_before_resolve_is_rejected(self):
        self.materialize('transaction-only')
        marker = '    set_variable = { name = lyd_factory_diag_empty_transaction_completed value = 1 }\n'
        resolve = '    resolve_title_and_vassal_change = scope:lyd_c3_head_change\n'
        self.replace_once('common/scripted_effects/lyd_i3b_commit_effects.txt', resolve + marker, marker + resolve)
        with self.assertRaisesRegex(ValueError, 'D2b_empty_transaction_marker_after_resolve_before_event'):
            self.validate('transaction-only')

    def test_terminal_cannot_continue_to_head_assignment(self):
        self.materialize('transaction-only')
        self.replace_once('events/lyd_factory_operation_diagnostic.txt',
                          'var:lyd_factory_diag_empty_transaction_completed = 1\n        }\n    }',
                          'var:lyd_factory_diag_empty_transaction_completed = 1\n        }\n'
                          '        hidden_effect = { lyd_factory_diag_d3_effect = yes }\n    }')
        with self.assertRaisesRegex(ValueError, 'D2_terminal_option_has_only_name_and_trigger'):
            self.validate('transaction-only')


if __name__ == '__main__':
    unittest.main()
