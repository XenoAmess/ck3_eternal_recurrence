"""Reviewed support-source compatibility only; no CK3 or business approval."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--support-repo', type=Path, default=Path(__file__).resolve().parents[1])
options, remaining = parser.parse_known_args()
HERE = Path(__file__).resolve().parent
CASES = HERE / 'ck3_mod_acceptance_cases'
sys.path.insert(0, str(options.support_repo / 'tools'))
from ck3_mod_acceptance_cases import xqol_followup_common as common
import ck3_mod_acceptance_prepare as prepare

ORIGINAL_PREPARE = {'bytes': 10984, 'sha256': '4dff30b3023d34cb2eb7923e52d81184da2cab4f301fc8a7c7b454277a003981'}
PREVIOUS_PREPARE = {'bytes': 12881, 'sha256': '4221d9bab91706ba0e6ba07a21b1944adf71f71e9cc4c1a54ce8c9117b3dbbab'}
REVIEW = json.loads((CASES / 'xqol_prepare_compatibility_review_v2.json').read_bytes())
CURRENT_PREPARE = REVIEW['after']
ORIGINAL_CONTRACTS = {'administrative_appointments': {'bytes': 2823, 'sha256': '803a6649952c323c3f07958b9635977c046deb544be16b723e5a1b45d0d4bccf'}, 'meritocratic_appointments': {'bytes': 6348, 'sha256': '3f7cda3eb863403e37abaa8165fb7aae23cafa585efaa757be785cfb1128ae7f'}, 'prison_payment': {'bytes': 4553, 'sha256': '4cd85a367af0b0fd7ebe4f4a404097c71b073de9a537402504a41b390f7f14ad'}, 'selfpaid_ransom': {'bytes': 3883, 'sha256': '956f01db9012c6704cc505e3a3ae68e31c08e23c4a78040220dfa41bc57c7862'}, 'pam_positive': {'bytes': 5128, 'sha256': '9f92e3f05df036be9b1624f20092988855ff3764b196c140a86693978ed81cbc'}, 'pam_negative': {'bytes': 4995, 'sha256': 'aea73ce9857339e729c6e16de5d43a13bb4cad75b64fffde8c84db626f4eea6b'}, 'liege_shared_ransom': {'bytes': 6620, 'sha256': 'cc69b83f6abd0e69821f0c91dc8a1e68388ec5b5338163c7dd24386d105ea169'}}
SUPPORT_KEY = '../ck3_mod_acceptance_prepare.py'

def context(name):
    contract = json.loads((CASES / ('xqol_' + name + '.json')).read_bytes())
    return {'case': name, 'case_contract': contract, 'case_spec': {'budgets': copy.deepcopy(contract['original_budgets'])}}

class ReviewedPrepareCompatibility(unittest.TestCase):
    def test_reviewed_optional_branches_restore_original_prefix_and_added_definition(self):
        raw = (options.support_repo / 'tools/ck3_mod_acceptance_prepare.py').read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (CURRENT_PREPARE['bytes'], CURRENT_PREPARE['sha256']))
        self.assertEqual({key: REVIEW['before'][key] for key in ('bytes', 'sha256')}, PREVIOUS_PREPARE)
        restored = raw.decode('utf-8')
        self.assertEqual(len(REVIEW['inverse_fragments']), 4)
        for fragment in REVIEW['inverse_fragments']:
            self.assertEqual(restored.count(fragment['reviewed_current']), 1)
            restored = restored.replace(fragment['reviewed_current'], fragment['old'], 1)
        raw = restored.encode('utf-8')
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (PREVIOUS_PREPARE['bytes'], PREVIOUS_PREPARE['sha256']))
        prefix = raw[:ORIGINAL_PREPARE['bytes']]
        self.assertEqual(hashlib.sha256(prefix).hexdigest(), ORIGINAL_PREPARE['sha256'])
        old = ast.parse(prefix)
        tail = ast.parse(raw[ORIGINAL_PREPARE['bytes']:])
        self.assertEqual(len(tail.body), 1)
        added = tail.body[0]
        self.assertIsInstance(added, ast.FunctionDef)
        self.assertEqual(added.name, 'finish_product_profile')
        self.assertNotIn(added.name, {getattr(node, 'name', None) for node in old.body})
        self.assertEqual(added.decorator_list, [])
        self.assertEqual(added.args.defaults, [])
        self.assertEqual([ast.dump(node) for node in added.args.kw_defaults], ['Constant(value=None)'])

    def test_original_product_fixture_keeps_exact_mount_order_and_v1_policy(self):
        for name in ORIGINAL_CONTRACTS:
            self.assertNotIn('frontend_scenario', context(name)['case_contract'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture, product = root / 'fixture', root / 'product'
            for directory in (fixture, product):
                directory.mkdir()
                (directory / 'descriptor.mod').write_text('name="test"\n', encoding='utf-8')
            output = root / 'output'
            output.mkdir()
            plain = {}
            for index, relative in enumerate(prepare.CONFIG_NAMES):
                source = root / ('plain-%d.txt' % index)
                source.write_text('plain %d\n' % index, encoding='utf-8')
                plain[relative] = prepare.pin(source)
            ctx = {'state_dir': str(root / 'state'), 'output': str(output),
                   'case_contract': {'post_start': {}, 'required_startup': [], 'forbidden_startup': []}}
            # Only engine identity I/O is fake; run the real materializer and finish.
            with patch.object(prepare, '_engine', return_value=(None, {'game_version': 'synthetic'})):
                result = prepare.materialize_fixture_profile(ctx, fixture, product, plain)
            profile = Path(result['profile'])
            self.assertEqual(json.loads((profile / 'dlc_load.json').read_bytes())['enabled_mods'],
                             ['mod/product.mod', 'mod/fixture.mod'])
            self.assertEqual((profile / 'mod-content/product/descriptor.mod').read_bytes(),
                             (product / 'descriptor.mod').read_bytes())
            policy = json.loads((output / 'frontend-fixture-start-policy.json').read_bytes())
            self.assertEqual((policy['schema'], policy['schema_version']),
                             ('ck3-frontend-fixture-start-policy-v1', 1))
            self.assertEqual(json.loads((output / 'profile-preparation.json').read_bytes())['provenance'],
                             {'kind': 'case-emitter-and-exact-formal-staging',
                              'fixture': str(fixture), 'product': str(product)})

    def test_all_seven_actual_support_contracts_validate(self):
        for name in ORIGINAL_CONTRACTS:
            with self.subTest(case=name):
                ctx = context(name)
                self.assertEqual(ctx['case_contract']['support_files'][SUPPORT_KEY], CURRENT_PREPARE)
                common.validate_contract(ctx)

    def test_only_reviewed_support_pin_changes_each_entire_contract(self):
        for name, expected in ORIGINAL_CONTRACTS.items():
            with self.subTest(case=name):
                restored = copy.deepcopy(context(name)['case_contract'])
                restored['support_files'][SUPPORT_KEY] = copy.deepcopy(ORIGINAL_PREPARE)
                raw = (json.dumps(restored, ensure_ascii=False, indent=2) + '\n').encode()
                self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (expected['bytes'], expected['sha256']))

    def test_wrong_helper_byte_count_or_digest_still_rejected(self):
        for name in ORIGINAL_CONTRACTS:
            for field, value in [('bytes', CURRENT_PREPARE['bytes'] - 1), ('sha256', '0' * 64)]:
                with self.subTest(case=name, field=field):
                    ctx = context(name)
                    ctx['case_contract']['support_files'][SUPPORT_KEY][field] = value
                    with self.assertRaisesRegex(ValueError, 'Original case support changed'):
                        common.validate_contract(ctx)

    def test_fixture_pin_and_original_budget_tamper_still_rejected(self):
        for name in ORIGINAL_CONTRACTS:
            with self.subTest(case=name, kind='fixture'):
                ctx = context(name)
                key = next(key for key in ctx['case_contract']['support_files'] if '/fixture/' in key)
                ctx['case_contract']['support_files'][key]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'Original case support changed'):
                    common.validate_contract(ctx)
            with self.subTest(case=name, kind='budget'):
                ctx = context(name)
                ctx['case_spec']['budgets']['hold_seconds'] += 1
                with self.assertRaisesRegex(ValueError, 'Original QOL wall-clock bounds changed'):
                    common.validate_contract(ctx)

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
