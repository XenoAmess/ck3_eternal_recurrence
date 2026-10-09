"""Regress the R38 unheld-title continuation failure using real diagnostic ASTs."""
from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch

import build_factory_diagnostic as builder
import validate_factory_diagnostic as validator

ROOT = Path(__file__).resolve().parents[2]


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
        self.replace_once('events/lyd_factory_operation_diagnostic.txt',
                          'STAGE = 2 }\n        lyd_factory_diag_unheld_title_trigger = yes',
                          'STAGE = 2 }\n        lyd_factory_diag_title_trigger = yes')
        with self.assertRaisesRegex(ValueError, 'D2_terminal_display_option_guards_equal'):
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
