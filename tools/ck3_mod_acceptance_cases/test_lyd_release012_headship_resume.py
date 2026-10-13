"""Inert saved-campaign gate tests; no CK3 launch or real R79 SAVE access."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ck3_mod_acceptance_cases import lyd_release012_headship_resume_adapter as resume
from ck3_mod_acceptance_prepare import CONFIG_NAMES, pin


class HeadshipResumeContract(unittest.TestCase):
    def test_scoped_native_protocol_does_not_change_first_start(self):
        bound = resume.scoped('load_base')()
        self.assertEqual(bound.CASE, resume.CASE)
        self.assertEqual(bound.RESULT, resume.RESULT)
        self.assertEqual(bound.review_cell.__globals__['CASE'], resume.CASE)
        self.assertEqual(resume.fresh.CASE, 'release012-headship-first')
        self.assertEqual(resume.fresh.RESULT, 'lyd-headship-first-result.json')
        self.assertEqual(resume.scoped('run_case').__globals__['CASE'], resume.CASE)

    def test_exact_seed_and_formal_product_only_projection(self):
        with tempfile.TemporaryDirectory(prefix='lyd-resume-inert-') as folder:
            root = Path(folder)
            save = root / 'seed.ck3'
            save.write_bytes(b'inert-save')
            seed = {'save': str(save), 'bytes': save.stat().st_size,
                'sha256': hashlib.sha256(save.read_bytes()).hexdigest(),
                'player_id': resume.SEED_PLAYER, 'date_raw': resume.SEED_DATE,
                'product_inventory': None}
            product = root / 'formal'
            product.mkdir()
            (product / 'descriptor.mod').write_text('name="inert"\n', encoding='utf-8')
            (product / 'content.txt').write_text('formal bytes\n', encoding='utf-8')
            rows = [
                {'path': p.name, 'size': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(product.iterdir())]
            manifest = root / 'formal-manifest.json'
            source_head = 'a' * 40
            manifest.write_text(json.dumps({'format_version': 1, 'git_sha': source_head,
                'mod_version': '0.1.2', 'product_id': 'mod_li_yu_dao', 'files': rows}), encoding='utf-8')
            plain = {}
            for index, name in enumerate(CONFIG_NAMES):
                path = root / 'plain' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(index), encoding='utf-8')
                plain[name] = pin(path)
            contract = json.loads(Path(resume.__file__).with_name(
                'lyd_release012_headship_resume.json').read_text(encoding='utf-8'))
            context = {'product': 'li-yu-dao', 'case': resume.CASE, 'case_contract': contract,
                'saved_campaign': seed, 'state_dir': str(root / 'new-state'),
                'output': str(root / 'output'), 'runtime_manifest': {'sha256': 'b' * 64},
                'case_inputs': {'product_dir': str(product), 'formal_release_manifest': pin(manifest),
                                'plain_configuration': plain}}
            (root / 'output').mkdir()
            with patch.multiple(resume, SEED_BYTES=seed['bytes'], SEED_SHA256=seed['sha256'],
                                PRODUCT_FILES=2, FORMAL_MANIFEST_SHA256=pin(manifest)['sha256'],
                                FORMAL_SOURCE_HEAD=source_head), \
                    patch.object(resume.fresh, 'storage_deadline', return_value=9999999999):
                self.assertEqual(resume.seed_identity(seed), save)
                prepared = resume.prepare_case(context)
                inventory = json.loads(Path(prepared['startup']['saved_campaign']['product_inventory']).read_text())
                self.assertEqual(inventory['enabled_mods'], ['mod/product.mod'])
                self.assertEqual(len(inventory['product_files']), 3)
                self.assertNotIn('_case_contract.json', [Path(row['path']).name for row in inventory['product_files']])
                self.assertEqual(prepared['startup']['saved_campaign']['sha256'], seed['sha256'])
                changed_seed = dict(seed, player_id=42)
                with self.assertRaises(ValueError):
                    resume.seed_identity(changed_seed)
                (product / 'content.txt').write_text('tampered\n', encoding='utf-8')
                changed = dict(context, state_dir=str(root / 'rejected-state'), output=str(root / 'output'))
                with self.assertRaisesRegex(ValueError, 'Formal product bytes differ'):
                    resume.prepare_case(changed)
                self.assertFalse(Path(changed['state_dir']).exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
