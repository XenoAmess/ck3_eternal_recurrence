"""New GUI-composition pure contracts; synthetic JSON and no media/fonts/tools."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HELPER = None


class GuiCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if HELPER is None:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
            from faith_power_promo import gui_composition
            cls.gui = gui_composition
        else:
            cls.gui = HELPER

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='gui-composition-pure-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bound_calls = []

    def pin_json(self, name, value):
        path = self.root / name
        data = json.dumps(value).encode()
        path.write_bytes(data)
        return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def binary_pin(self, name='original.png'):
        # Deliberately absent: metadata-only must not open this fixture binary.
        return {'path': str(self.root / name), 'bytes': 1234, 'sha256': 'a' * 64}

    def bound(self, value):
        self.bound_calls.append(value['path'])
        return Path(value['path'])

    def scene(self, template='A', duration=8):
        return {'kind': 'gui-composition', 'machine_id': 'fixture-machine', 'scene_id': 'same-window',
                'template': template, 'duration_seconds': duration, 'disclosure': self.gui.DISCLOSURE,
                'layers': [], 'annotations': []}

    def still(self, role='primary_GUI', template='A', duration=8, identity='left'):
        image = self.binary_pin(identity + '.png')
        capture = self.pin_json(identity + '-capture.json', {'fixture_only': True,
                    'machine_id': 'fixture-machine', 'image': image})
        receipt = self.pin_json(identity + '-still.json', {'fixture_only': True,
                    'schema': 'ck3-faith-power-original-gui-still-v1',
                    'machine_id': 'fixture-machine', 'image': image, 'source_geometry': [1920, 1080],
                    'source_identity': {'id': identity, 'kind': 'gameplay-screenshot',
                                        'observed_at_utc': 'fixture-time', 'context': 'fixture inventory'},
                    'capture_checks': [{'file': capture, 'json_pointer': '/image', 'equals': image}]})
        return {'id': identity, 'kind': 'game-still', 'role': role, 'image': image,
                'still_receipt': receipt, 'crop_rect': [100, 100, 800, 600],
                'canvas_rect': deepcopy(self.gui.SLOTS[template][role]),
                'display_interval_seconds': [0, duration], 'display_label': '原版实机静帧',
                'object_name': 'Original inventory item', 'required_context': ['Name', 'Item tier'],
                'object_context': 'Inventory; original item identity retained'}

    def raw(self, role='primary_GUI', template='A', duration=8, identity='raw'):
        raw = self.binary_pin('original.mp4')
        audit = self.pin_json('audit.json', {'fixture_only': True, 'machine_id': 'fixture-machine',
                    'raw': raw, 'full_decode_exit_code': 0, 'capture_was_aborted': False,
                    'pts': {'last_pts': 100}, 'video': {'width': 1920, 'height': 1080}})
        index = self.pin_json('index.json', {'fixture_only': True})
        pts = self.pin_json('frame-pts.stdout', {'frames': [{'best_effort_timestamp_time': str(i / 30)} for i in range(3001)]})
        return {'id': identity, 'role': role, 'kind': 'raw', 'raw': raw,
                'raw_audit': audit, 'source_index': index, 'source_frame_pts': pts,
                'geometry_evidence': {'file': audit, 'json_pointer': '/video'},
                'raw_start_seconds': 10, 'crop_rect': [100, 100, 800, 600],
                'canvas_rect': deepcopy(self.gui.SLOTS[template][role]),
                'display_interval_seconds': [0, duration], 'display_label': '原版实机片段',
                'object_name': 'Original inventory item', 'required_context': ['Name', 'Item tier'],
                'object_context': 'Actual selected inventory interval'}

    def test_empty_assets_are_gaps_and_readback_cannot_fill_original_gui_slot(self):
        scene = self.scene()
        self.assertFalse(self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)['content_ready'])
        layer = self.still()
        layer['image'] = None
        scene['layers'] = [layer]
        result = self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)
        self.assertFalse(result['content_ready'])
        self.assertTrue(any('asset unbound' in gap for gap in result['gaps']))
        self.assertEqual(self.bound_calls, [])
        layer['kind'] = 'native-readback'
        with self.assertRaises(ValueError):
            self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)
        self._check_notes_use_ass_and_do_not_require_new_png_or_system_font()

    def test_real_still_lineage_crop_bounds_and_metadata_do_not_open_binary(self):
        scene = self.scene()
        scene['layers'] = [self.still()]
        with patch.object(self.gui.Image, 'open', side_effect=AssertionError('binary opened during metadata')):
            result = self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)
        self.assertTrue(result['content_ready'])
        self.assertFalse(result['layers'][0]['source_geometry_checked_from_binary'])
        # Slots are available bounds: a narrow object-bearing GUI need not fill them.
        narrow = deepcopy(scene)
        narrow['layers'][0]['canvas_rect'] = [120, 120, 680, 900]
        self.assertTrue(self.gui.inspect(narrow, self.bound, 'fixture-machine', metadata_only=True)['content_ready'])
        narrow['layers'][0]['canvas_rect'] = [60, 120, 680, 900]
        with self.assertRaises(ValueError):
            self.gui.inspect(narrow, self.bound, 'fixture-machine', metadata_only=True)
        self.assertTrue(result['pixel_legibility_review_pending'])
        for rect in ([0, 0, 0, 1], [0, 0, True, 5], [0, 0, float('nan'), 5],
                     [0, 0, float('inf'), 5], [1900, 0, 100, 100]):
            with self.subTest(rect=rect):
                changed = deepcopy(scene)
                changed['layers'][0]['crop_rect'] = rect
                with self.assertRaises(ValueError):
                    self.gui.inspect(changed, self.bound, 'fixture-machine', metadata_only=True)
        header = SimpleNamespace(format='PNG', size=(1920, 1080),
                                 __enter__=lambda value: value, __exit__=lambda *args: None)
        # A context manager double, not a real PNG or header operation.
        class Header:
            format, size = 'PNG', (1920, 1080)
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch.object(self.gui.Image, 'open', return_value=Header()) as opened:
            self.assertTrue(self.gui.inspect(scene, self.bound, 'fixture-machine')['content_ready'])
        opened.assert_called_once()
        changed = deepcopy(scene)
        changed['layers'][0]['still_receipt'] = self.pin_json('bad-receipt.json',
                    {'schema': 'ck3-faith-power-native-readback-card-v1', 'machine_id': 'fixture-machine'})
        with self.assertRaises(ValueError):
            self.gui.inspect(changed, self.bound, 'fixture-machine', metadata_only=True)

    def test_raw_bounds_and_two_projection_insets_are_not_full_frame_raw(self):
        scene = self.scene()
        scene['layers'] = [self.raw()]
        result = self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)
        self.assertTrue(result['content_ready'])
        self.assertEqual(result['layers'][0]['selected_source_frame_indices_exclusive'], [300, 540])
        # Other provenance callers retain the strict .json default.
        with self.assertRaises(ValueError):
            self.gui._json(scene['layers'][0]['source_frame_pts'], self.bound)
        changed = deepcopy(scene)
        changed['layers'][0]['raw_start_seconds'] = 99
        with self.assertRaises(ValueError):
            self.gui.inspect(changed, self.bound, 'fixture-machine', metadata_only=True)
        inset = deepcopy(scene['layers'][0])
        inset.update(id='detail', role='detail_inset', canvas_rect=self.gui.SLOTS['A']['detail_inset'])
        scene['layers'].append(inset)
        report = self.gui.coverage([{'id': 'one', 'duration_seconds': 8, 'visual_parts': [scene]}])
        self.assertEqual(report['derived_composition_seconds'], 8)
        self.assertEqual(report['full_frame_raw_seconds_from_compositions'], 0)
        self.assertEqual(len(report['entries'][0]['embedded_layers']), 2)
        self.assertEqual(report['embedded_raw_layer_display_seconds'], 16)
        self.assertEqual(report['embedded_raw_visible_final_time_union_seconds'], 8)
        self.assertEqual(report['embedded_raw_unique_source_PTS_seconds'], 8)
        with self.assertRaises(ValueError):
            self.gui.coverage([{'id': 'one', 'duration_seconds': 8, 'visual_parts': [scene]},
                               {'id': 'two', 'duration_seconds': 8, 'visual_parts': [deepcopy(scene)]}])
        self._check_template_filter_uses_original_inputs_and_aspect_preserving_overlay()

    def test_cross_cue_scene_reuses_source_and_preserves_raw_time_continuity(self):
        scene = self.scene(duration=12)
        scene['layers'] = [self.raw(duration=12)]
        first = self.gui.slice_scene(scene, 0, 4)
        second = self.gui.slice_scene(scene, 4, 12)
        self.assertEqual(first['layers'][0]['raw'], second['layers'][0]['raw'])
        self.assertEqual(second['layers'][0]['raw_start_seconds'], 14)
        rows = [{'id': 'one', 'duration_seconds': 4, 'visual_parts': [first]},
                {'id': 'two', 'duration_seconds': 8, 'visual_parts': [second]}]
        report = self.gui.coverage(rows)
        self.assertEqual(report['derived_composition_seconds'], 12)
        self.assertEqual(report['entries'][1]['embedded_layers'][0]['authored_final_interval_seconds'], [4, 12])
        mapped = self.gui.actual_map_layers(second, 4.021354, 120)
        self.assertEqual(mapped[0]['actual_final_frame_indices_exclusive'], [120, 360])
        self.assertAlmostEqual(mapped[0]['actual_final_end_pts_exclusive'], 12.021354)
        wrong = deepcopy(rows)
        wrong[1]['visual_parts'][0]['layers'][0]['raw_start_seconds'] += 1
        with self.assertRaises(ValueError):
            self.gui.coverage(wrong)

    def _check_template_filter_uses_original_inputs_and_aspect_preserving_overlay(self):
        scene = self.scene(template='B')
        scene['layers'] = [self.still('left_GUI', 'B'), self.still('right_GUI', 'B', identity='right')]
        with patch.object(self.gui, 'inspect', return_value={'gaps': []}):
            argv, filters, next_input = self.gui.filters(scene, self.bound, 3, 'v2')
        self.assertEqual(argv.count('-i'), 2)
        self.assertEqual(next_input, 5)
        graph = ';'.join(filters)
        self.assertIn('[3:v]', graph)
        self.assertIn('[4:v]', graph)
        self.assertIn('force_original_aspect_ratio=decrease', graph)
        self.assertIn('crop=800:600:100:100', graph)
        self.assertIn('overlay=x=1312:y=120:eof_action=pass:repeatlast=0', graph)
        self.assertIn('[v2]', graph)
        self.assertNotIn('loop=', graph)
        self.assertNotIn('scale=2560:1440', graph)

    def _check_notes_use_ass_and_do_not_require_new_png_or_system_font(self):
        scene = self.scene(template='C')
        scene['layers'] = [self.still('GUI_anchor', 'C')]
        rule = self.pin_json('rule.json', {'value': 4})
        scene['annotations'] = [{'id': 'condition', 'text': '先看当前条件，再比较效果。',
                    'canvas_rect': [1200, 150, 1200, 110], 'display_interval_seconds': [2, 8],
                    'claim_ids': ['claim-rule'], 'source_refs': [{'file': rule, 'json_pointer': '/value'}]}]
        self.assertTrue(self.gui.inspect(scene, self.bound, 'fixture-machine', metadata_only=True)['content_ready'])
        face = SimpleNamespace(getlength=lambda text: len(text) * 20)
        tracks, cues = [], []
        with patch.object(self.gui.ImageFont, 'truetype', return_value=face):
            self.gui.ass(scene, 4, Path('never-opened-font'), 'Fixture Font', tracks, cues, prefix='cue.part0')
        self.assertEqual(len(tracks), 2)
        self.assertEqual((float(cues[0].start_seconds), float(cues[0].end_seconds)), (6, 12))
        self.assertEqual(tracks[0].style.alignment, 7)
        self.assertEqual(tracks[0].style.margin_left, 1200)
        self.assertLess(tracks[0].style.margin_vertical + 110, 1120)


if __name__ == '__main__':
    unittest.main()
