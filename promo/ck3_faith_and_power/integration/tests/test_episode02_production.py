"""No-media checks of episode two through the existing formal and concat consumers."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from faith_power_promo import full_episode as common
from faith_power_promo.formal_episode import FormalInputs
from test_value_v3_formal import small_metadata_fixture, forbid_media_reads


class Episode02ProductionTests(unittest.TestCase):
    def test_episode02_inspection_keeps_source_and_pending_result_guards(self):
        for scope in ('episode02-formal-review', 'episode02-review-segment'):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as name:
                doc, media = small_metadata_fixture(Path(name))
                doc.update(scope=scope, excluded_cues=[])
                with forbid_media_reads(media):
                    result = FormalInputs(doc, common, metadata_only=True).inspect()
                self.assertEqual(result['scope'], scope)
                self.assertEqual(len(result['rows']), 2)
                self.assertFalse(result['ready_to_build'])
                self.assertFalse(result['fullrender_admitted'])
                self.assertTrue(any('result still unbound' in gap for gap in result['gaps']))
                changed = deepcopy(doc)
                changed['cues'][0]['zh'] = 'Changed source text'
                with self.assertRaisesRegex(ValueError, 'Selected measured source field changed'):
                    FormalInputs(changed, common, metadata_only=True).inspect()

    def test_formal_episode02_requires_reasoned_inventory_exclusions(self):
        with tempfile.TemporaryDirectory() as name:
            doc, _ = small_metadata_fixture(Path(name))
            doc.update(scope='episode02-formal-review', excluded_cues=[])
            doc['cues'] = doc['cues'][:1]
            doc['sequence'] = [doc['cues'][0]['id']]
            with self.assertRaisesRegex(ValueError, 'reasoned exclusions'):
                FormalInputs(doc, common, metadata_only=True).inspect()

    def test_episode02_companions_have_correct_names_and_measured_pts(self):
        row = {'id': 'E02-C01', 'zh': '规则。', 'en': 'Rule.',
               'speech_duration_seconds': 2.0}
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / 'text'
            outputs = common.companion_text([row], [{'actual_final_first_pts': 10.125}],
                                            root, scope='episode02-formal-review')
            self.assertEqual({path.name for path in outputs}, {
                'episode02.zh.srt', 'episode02.en.srt',
                'episode02.bilingual.srt', 'episode02-script.md'})
            self.assertEqual((root / 'episode02.bilingual.srt').read_text('utf-8'),
                             '1\n00:00:10,125 --> 00:00:12,125\n规则。\nRule.\n')
            self.assertIn('00:00:10,125  规则。', (root / 'episode02-script.md').read_text('utf-8'))

    def test_real_public_concat_planner_uses_each_episode_output(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for prefix, scope in (('episode01', 'episode01-formal-review'),
                                  ('episode02', 'episode02-formal-review'),
                                  ('episode02', 'episode02-review-segment')):
                with self.subTest(scope=scope):
                    plan = common.review_concat_plan('ffmpeg', [root / 'cue.mp4'],
                                                     root, root / 'audit', scope)
                    self.assertEqual(plan.final_output, root / (prefix + '-review.mp4'))
                    self.assertEqual(plan.partial_output, root / (prefix + '-review.partial.mp4'))
                    self.assertEqual(plan.generated_files[0].path, root / (prefix + '.ffconcat'))
                    self.assertEqual(Path(plan.commands[0].spec.argv[-1]), plan.partial_output)
                    self.assertFalse(plan.final_output.exists())
                    self.assertFalse(plan.generated_files[0].path.exists())

    def test_actual_pinned_profile_covers_34_minutes_without_quality_change(self):
        reference = common.pin(ROOT / 'profiles/episode02-2040s-1440p30-v1.json')
        profile = common.render_profile({'render_profile': reference},
                                        lambda pin: Path(pin['path']))
        budget = common.peak_budget(2040, 110, profile=profile)
        self.assertEqual(budget['geometry'], [2560, 1440, 30])
        self.assertEqual(budget['video_maxrate_bps'], 3_000_000)
        self.assertEqual(budget['media_CAS_copies'], 0)
        with self.assertRaises(ValueError):
            common.peak_budget(2040 + 1 / 30, 110, profile=profile)
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'changed-profile.json'
            changed = json.loads(Path(reference['path']).read_text('utf-8'))
            changed['crf'] = 22
            path.write_text(json.dumps(changed), 'utf-8')
            with self.assertRaisesRegex(ValueError, 'Unknown immutable render profile'):
                common.render_profile({'render_profile': common.pin(path)},
                                      lambda pin: Path(pin['path']))

    def test_unknown_scope_refuses_before_creating_output(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'must-not-exist'
            with self.assertRaisesRegex(ValueError, 'Unknown episode production scope'):
                common.companion_text([], [], output, scope='episode03-formal-review')
            with self.assertRaisesRegex(ValueError, 'Unknown episode production scope'):
                common.build(SimpleNamespace(output=output), {'scope': '../../episode02'},
                             {'ready_to_build': True}, None, {})
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
