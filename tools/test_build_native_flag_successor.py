"""Exact predecessor-object inheritance; no compiler, game or desktop contact."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_native_flag_successor import (inherit_successor, pin, materialize_source_overlay,
    parse_ninja_dependencies, select_changed_objects, remap_source_arguments)


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

    def test_grandparent_objects_survive_and_descendant_replacements_win(self):
        ancestor = self.root / 'ancestor.json'
        ancestor.write_text(json.dumps(self.report), encoding='utf-8')
        replacement = self.root / 'replacement.obj'; replacement.write_bytes(b'new object')
        self.report['predecessor'] = pin(ancestor)
        self.report['compiled'] = [copy.deepcopy(self.report['compiled'][0])]
        self.report['compiled'][0]['object'] = pin(replacement)
        result = self.load()
        self.assertEqual(result['objects'], {'a.obj': replacement, 'new.obj': self.base / 'new.obj'})
        self.report['predecessor']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'report chain pin changed'):
            self.load()

    def test_overlaid_predecessor_maps_source_identity_back_to_original(self):
        overlay = self.root / 'previous-source'; overlay.mkdir()
        for name in ('a.cpp', 'new.cpp'):
            (overlay / name).write_text('previous overlay', encoding='utf-8')
        self.report['effective_source_dir'] = str(overlay)
        for row in self.report['compiled']:
            row['source'] = pin(overlay / Path(row['source']['path']).name)
        result = self.load()
        self.assertEqual(result['effective_source_dir'], overlay)
        self.assertEqual(self.groups['runtime'][0]['file'], str(self.source / 'a.cpp'))


class SourceOverlayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.source = self.root / 'original'; self.source.mkdir()
        self.base = self.root / 'baseline'; self.base.mkdir()
        self.output = self.root / 'successor-source'

    def write(self, name, text):
        path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8'); return path

    def test_exact_overlay_isolated_and_bad_pin_or_traversal_refused(self):
        original = self.write('include/layout.hpp', 'old layout')
        update = self.root / 'update.hpp'; update.write_text('new layout', encoding='utf-8')
        config = {'baseline_build_dir': str(self.base), 'source_overlay': {'output_dir': str(self.output),
            'files': [{'relative_path': 'include/layout.hpp', 'source': pin(update)}]}}
        bad = copy.deepcopy(config); bad['source_overlay']['files'][0]['source']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Pinned overlay input changed'):
            materialize_source_overlay(bad, self.source, {})
        bad = copy.deepcopy(config); bad['source_overlay']['files'][0]['relative_path'] = '../escape.hpp'
        with self.assertRaisesRegex(ValueError, 'escapes source'):
            materialize_source_overlay(bad, self.source, {})
        actual, record = materialize_source_overlay(config, self.source, {})
        self.assertEqual(original.read_text(), 'old layout')
        self.assertEqual((actual / 'include/layout.hpp').read_text(), 'new layout')
        self.assertEqual(record['files'][0]['source'], pin(update))
        with self.assertRaises(FileExistsError):
            materialize_source_overlay(config, self.source, {})

    def test_real_deps_and_new_include_closure_cover_both_production_targets(self):
        header = self.write('include/layout.hpp', 'struct Layout { int a; };')
        self.write('include/wrapper.hpp', '#include <layout.hpp>\n')
        direct = self.write('direct.cpp', '#include "wrapper.hpp"\n')
        macro = self.write('macro.cpp', '#include SELECTED_LAYOUT_HEADER\n')
        untouched = self.write('untouched.cpp', 'int unrelated;\n')
        deps = parse_ninja_dependencies('macro.obj: #deps 1, deps mtime 1 (VALID)\n    ' +
            str(header) + '\n\nstale.obj: #deps 1, deps mtime 1 (STALE)\n    ' + str(header) + '\n', self.base)
        self.assertNotIn('stale.obj', deps)
        groups = {'runtime': [{'file': str(direct), 'output': 'direct.obj'}], 'bridge': [
            {'file': str(macro), 'output': 'macro.obj'}, {'file': str(untouched), 'output': 'untouched.obj'}]}
        changed, records = select_changed_objects(groups, self.source, self.source, [],
                                                   {'include/layout.hpp'}, deps)
        self.assertEqual({row['output'] for _, row in changed}, {'direct.obj', 'macro.obj'})
        self.assertEqual({row['target'] for row in records}, {'runtime', 'bridge'})
        self.assertEqual(records[1]['actual_original_dependencies'], [str(header)])

    def test_compile_paths_move_to_overlay_but_baseline_outputs_do_not(self):
        argv = ['cl', '-I' + str(self.source / 'include'), str(self.source / 'direct.cpp'),
                '/Fo' + str(self.base / 'direct.obj')]
        moved = remap_source_arguments(argv, {self.source}, self.output)
        self.assertEqual(moved[1], '-I' + (self.output / 'include').as_posix())
        self.assertEqual(moved[2], (self.output / 'direct.cpp').as_posix())
        self.assertEqual(moved[3], '/Fo' + (self.base / 'direct.obj').as_posix())


if __name__ == '__main__': unittest.main()
