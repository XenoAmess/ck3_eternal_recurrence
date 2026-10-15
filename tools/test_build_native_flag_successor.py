"""Exact predecessor-object inheritance; no compiler, game or desktop contact."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_native_flag_successor import inherit_successor, pin


class SuccessorInheritanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'; self.source.mkdir()
        self.base = self.root / 'baseline'; self.base.mkdir()
        self.groups = {'runtime': [{'file': str(self.source / 'a.cpp'), 'output': 'a.obj'}], 'bridge': []}
        for name in ('a.cpp', 'new.cpp'):
            (self.source / name).write_text('existing provider', encoding='utf-8')
        for name in ('bridge.dll', 'runtime.lib', 'a.obj', 'new.obj'):
            (self.base / name).write_bytes(name.encode())
        self.report = dict(schema='ck3-native-flag-successor-v1', baseline_build_dir=str(self.base),
            source_dir=str(self.source), flags=['EXISTING_FLAG'], status='failed',
            archive={'exit_code': 0}, link={'exit_code': 0},
            baseline_dll=pin(self.base / 'bridge.dll'), baseline_archive=pin(self.base / 'runtime.lib'),
            compiled=[dict(target='runtime', original_output=name + '.obj', exit_code=0,
                source=pin(self.source / (name + '.cpp')), object=pin(self.base / (name + '.obj')),
                argv=['cl', '/DEXISTING_FLAG=1', str(self.source / (name + '.cpp'))])
                for name in ('a', 'new')])
        self.path = self.root / 'prior.json'

    def load(self):
        self.path.write_text(json.dumps(self.report), encoding='utf-8')
        return inherit_successor({'baseline_successor_report': str(self.path)}, self.base,
                                 self.source, self.groups)

    def test_successful_link_retains_failed_fixture_status_and_exact_objects(self):
        result = self.load()
        self.assertEqual(result['flags'], ['EXISTING_FLAG'])
        self.assertEqual(result['report']['original_status'], 'failed')
        self.assertEqual(set(result['objects']), {'a.obj', 'new.obj'})
        self.assertEqual(len(self.groups['runtime']), 2)
        self.assertEqual(self.groups['runtime'][1]['inherited_argv'], self.report['compiled'][1]['argv'])
        self.assertEqual(json.loads(self.path.read_text()), self.report)

    def test_tampered_source_and_object_rejected(self):
        for part in ('source', 'object'):
            with self.subTest(part=part):
                expected = copy.deepcopy(self.report)
                self.report['compiled'][0][part]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'pinned input changed'):
                    self.load()
                self.report = expected

    def test_failed_link_wrong_source_duplicate_and_wrong_target_rejected(self):
        for field in ('link', 'source', 'duplicate', 'target'):
            original = copy.deepcopy(self.report)
            if field == 'link': self.report['link']['exit_code'] = 1
            elif field == 'source': self.report['source_dir'] = str(self.base)
            elif field == 'duplicate': self.report['compiled'].append(self.report['compiled'][0])
            else: self.report['compiled'][0]['target'] = 'other'
            with self.subTest(field=field), self.assertRaises(ValueError): self.load()
            self.report = original

    def test_optional_overlay_defaults_empty(self):
        self.assertEqual(inherit_successor({}, self.base, self.source, self.groups),
                         {'flags': [], 'objects': {}, 'report': None})


if __name__ == '__main__': unittest.main()
