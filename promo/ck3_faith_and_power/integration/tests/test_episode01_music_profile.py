"""Pure contracts: no media, system fonts, FFmpeg, provider or machine paths."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]  # Repository integration/ directory.
sys.path.insert(0, str(ROOT / 'src'))
from faith_power_promo import full_episode as common
from xar_promo.render import plan_concat


class Episode01MusicProfileTests(unittest.TestCase):
    def test_legacy_budget_and_quality_defaults_are_unchanged(self):
        budget = common.peak_budget()
        self.assertEqual(budget['max_seconds'], 1860)
        self.assertEqual(budget['segments'], 168)
        self.assertEqual(budget['peak_new_bytes'], 2_783_466_160)
        self.assertEqual((budget['video_maxrate_bps'], budget['video_bufsize_bits'],
                          budget['audio_bitrate_bps']), (3_000_000, 3_000_000, 192_000))
        self.assertEqual((budget['geometry'], budget['crf'], budget['preset']),
                         ([2560, 1440, 30], 21, 'veryfast'))
        self.assertEqual(budget['media_CAS_copies'], 0)

    def test_immutable_extended_profile_and_bounded_clock(self):
        profile = common.PADDING_PROFILE
        self.assertEqual(profile.id, 'episode01-2101s-1440p30-v1')
        self.assertEqual(common.peak_budget(2101, 168, profile=profile)['peak_new_bytes'],
                         3_080_293_810)
        self.assertGreater(common.peak_budget(2101, 168, profile=profile)['peak_new_bytes'],
                           3_079_062_160)  # This upper bound is not a blanket grant.
        self.assertEqual(common.peak_budget(63008 / 30, 115, profile=profile)['peak_new_bytes'],
                         2_977_034_353)  # Original float/ceil formula is conservative by3 bytes.
        with self.assertRaises(FrozenInstanceError):
            profile.max_seconds = 2400
        for seconds, segments, selected in [(1860 + 1 / 30, 168, common.DEFAULT_PROFILE),
                                             (2101 + 1 / 30, 168, profile),
                                             (2101, 169, profile)]:
            with self.subTest(seconds=seconds, segments=segments):
                with self.assertRaises(ValueError):
                    common.peak_budget(seconds, segments, profile=selected)
        with self.assertRaises(ValueError):
            common.peak_budget(2101)  # The explicit padding profile is required.

    def test_pinned_profile_accepts_only_the_fixed_quality_contract(self):
        with tempfile.TemporaryDirectory(prefix='faith-music-profile-') as name:
            path = Path(name) / 'profile.json'

            def load(value):
                path.write_text(json.dumps(value), encoding='utf-8')
                return common.render_profile({'render_profile': common.pin(path)},
                                             common.Inputs({}).bound)

            expected = common.PADDING_PROFILE.to_mapping()
            self.assertEqual(load(expected), common.PADDING_PROFILE)
            changes = {'max_seconds': 2102, 'max_segments': 169,
                       'video_maxrate_bps': 2_000_000, 'video_bufsize_bits': 2_000_000,
                       'audio_bitrate_bps': 128_000, 'geometry': [1920, 1080, 30],
                       'crf': 28, 'preset': 'ultrafast'}
            for key, value in changes.items():
                with self.subTest(field=key):
                    with self.assertRaises(ValueError):
                        load({**expected, key: value})

    def test_actual_audio_planner_drives_one_video_copy_and_aac_concat(self):
        plan = plan_concat(ffmpeg='ffmpeg-not-executed',
                           segment_paths=[Path('unit-a.mp4'), Path('unit-b.mp4')],
                           concat_path=Path('unit.ffconcat'),
                           partial_output=Path('unit.partial.mp4'),
                           final_output=Path('unit.final.mp4'),
                           audit_directory=Path('unit-audit'))
        music = {'file': {'path': str(Path('unit-theme.wav'))}}
        mixed, audio = common.theme_concat(plan, music, 2101, 999_999_999)
        self.assertEqual(len(mixed.commands), 1)
        argv = mixed.commands[0].spec.argv
        self.assertEqual(argv[argv.index('-c:v') + 1], 'copy')
        self.assertEqual(argv[argv.index('-c:a') + 1], 'aac')
        self.assertEqual(argv[argv.index('-b:a') + 1], '192k')
        self.assertEqual(argv[argv.index('-ar') + 1], '48000')
        self.assertEqual(argv[argv.index('-ac') + 1], '2')
        self.assertEqual(argv.count('-i'), 2)
        self.assertEqual(argv[argv.index('-stream_loop') + 1], '-1')
        self.assertEqual(argv[argv.index('-fs') + 1], '999999999')
        self.assertEqual(argv[argv.index('-filter_complex') + 1], audio.filtergraph)
        self.assertEqual(audio.spec.stems[0].gain_db, 0)
        self.assertEqual(audio.spec.stems[1].gain_db, -17)
        self.assertEqual((audio.spec.stems[1].fade_in_seconds,
                          audio.spec.stems[1].fade_out_seconds), (2, 8))
        self.assertFalse(audio.spec.normalize)
        self.assertTrue(all(not stem.duck_windows for stem in audio.spec.stems))
        self.assertEqual(float(re.search(r'volume=([-+0-9.]+)dB',
                                         audio.filtergraph).group(1)), -17)
        self.assertIn('normalize=0', audio.filtergraph)
        self.assertNotIn('sidechain', audio.filtergraph)
        self.assertNotIn('loudnorm', audio.filtergraph)
        self.assertEqual(audio.filtergraph.count('[faith_theme_mix]'), 1)
        self.assertEqual(argv.count('[faith_theme_mix]'), 1)
        self.assertEqual(mixed.partial_output, plan.partial_output)
        self.assertEqual(mixed.generated_files, plan.generated_files)

    def test_residual_music_positive_absent_and_doubled(self):
        import numpy as np
        rng = np.random.default_rng(49)
        dry = rng.normal(0, .02, 4096)
        music = rng.normal(0, .005, 4096)
        noise = rng.normal(0, .00002, 4096)
        positive = common.music_window_metrics(dry + music + noise, dry, music)
        self.assertTrue(positive['passed'])
        self.assertFalse(common.music_window_metrics(dry, dry, music)['passed'])
        self.assertFalse(common.music_window_metrics(dry + 2 * music, dry, music)['passed'])

    def test_one_fixed_sample_lag_can_be_held_for_another_window(self):
        import numpy as np
        rng = np.random.default_rng(50)
        pad, lag = 320, 17
        signal = rng.normal(0, .02, 4096)
        actual = np.zeros(len(signal) + 2 * pad)
        actual[pad + lag:pad + lag + len(signal)] = signal
        calibrated = common.fixed_music_lag(actual, signal, pad)
        self.assertEqual(calibrated, lag)
        dry = rng.normal(0, .02, 4096)
        music = rng.normal(0, .005, 4096)
        another = np.zeros(len(dry) + 2 * pad)
        another[pad + lag:pad + lag + len(dry)] = dry + music
        self.assertTrue(common.music_window_metrics(
            another[pad + calibrated:pad + calibrated + len(dry)], dry, music)['passed'])

    @staticmethod
    def graphic(root, kind='diagram'):
        image = {'path': str(root / 'not-an-actual-image.png'),
                 'bytes': 0, 'sha256': '0' * 64}
        text = 'RULE DIAGRAM · NOT GAMEPLAY' if kind == 'diagram' else 'OBSERVED STATE · NOT GAMEPLAY'
        receipt = root / 'synthetic-render-receipt.json'
        schema = ('ck3-faith-power-result-source-diagram-v1' if kind == 'diagram'
                  else 'ck3-faith-power-native-readback-card-v1')
        receipt.write_text(json.dumps({'fixture_only_not_actual_media_evidence': True,
                                       'schema': schema, 'image': image,
                                       'permanent_disclosure': text}), encoding='utf-8')
        return {'kind': kind, 'image': image, 'disclosure': text, 'duration_seconds': 3,
                'burned_in_disclosure': {'source_class': kind, 'text': text,
                                        'render_receipt': common.pin(receipt)}}

    def test_only_exact_graphic_receipt_can_suppress_a_disclosure(self):
        with tempfile.TemporaryDirectory(prefix='faith-burned-label-') as name:
            root = Path(name)
            bound = common.Inputs({}).bound
            for kind in ['diagram', 'native-readback']:
                with self.subTest(kind=kind):
                    self.assertTrue(common.validate_burned_in_disclosure(
                        self.graphic(root, kind), bound))
            part = self.graphic(root)
            for field, value in [('kind', 'raw'), ('disclosure', 'Different label'),
                                 ('image', {**part['image'], 'sha256': '1' * 64})]:
                with self.subTest(changed=field):
                    with self.assertRaises(ValueError):
                        common.validate_burned_in_disclosure({**part, field: value}, bound)
            mismatched = deepcopy(part)
            mismatched['burned_in_disclosure']['source_class'] = 'native-readback'
            with self.assertRaises(ValueError):
                common.validate_burned_in_disclosure(mismatched, bound)
            self.assertFalse(common.validate_burned_in_disclosure(
                {'kind': 'raw', 'disclosure': 'GAMEPLAY'}, bound))

    def test_ass_omits_only_the_receipt_bound_duplicate_label(self):
        with tempfile.TemporaryDirectory(prefix='faith-ass-label-') as name:
            part = self.graphic(Path(name))
            self.assertTrue(common.validate_burned_in_disclosure(part, common.Inputs({}).bound))
            row = {'id': 'unit', 'zh': '规则。', 'en': 'Rule.',
                   'duration_seconds': 3, 'speech_duration_seconds': 2,
                   'visual_parts': [part]}
            face = SimpleNamespace(getlength=lambda text: len(text) * 10)
            with patch.object(common.ImageFont, 'truetype', return_value=face):
                burned = common.subtitle(row, Path('unused-font.ttf'), 'Unit Font')
                plain = deepcopy(row)
                plain['visual_parts'][0].pop('burned_in_disclosure')
                default = common.subtitle(plain, Path('unused-font.ttf'), 'Unit Font')
            self.assertNotIn(part['disclosure'], burned)
            self.assertEqual(default.count(part['disclosure']), 1)


if __name__ == '__main__':
    unittest.main()
