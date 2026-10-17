"""Portable, no-media regressions for the value-v3 authoring boundary."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from faith_power_promo import full_episode as common
from faith_power_promo.formal_episode import FormalInputs, VALUE_V3_SCHEMA
from xar_promo.model import new_project_config


@contextmanager
def forbid_media_reads(*paths):
    """Catch builtins/io/pathlib/os opens; deactivate the audit hook on exit."""
    blocked = {os.path.normcase(str(path.resolve())) for path in paths}

    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            target = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
            if target in blocked:
                raise AssertionError('Metadata-only inspection opened fake media')

    sys.addaudithook(audit)
    try:
        yield
    finally:
        blocked.clear()


def native_project(rows):
    config = new_project_config('value-v3-unit', 'Unit', 'zh-CN',
                                ['zh-CN', 'en'], 'unit', 'portable').to_dict()
    config['chapters'] = [{
        'id': 'unit-chapter', 'type': 'unit', 'state': 'planned',
        'title': {'zh-CN': '测试', 'en': 'Test'}, 'artifact_ids': [],
        'cues': [{'id': row['id'], 'narration': {'zh-CN': row['zh']},
                  'subtitles': {'zh-CN': row['zh'], 'en': row['en']}}
                 for row in rows],
    }]
    return config


def small_metadata_fixture(root):
    """Intentionally unbuildable: no visuals and all live slots are null."""
    media = root / 'voice.fake.mp3'
    media.write_bytes(b'fake; never decoded or opened during inspection')
    declared = {'path': str(media), 'bytes': media.stat().st_size,
                'sha256': '0' * 64}  # Inherited digest must not be rehashed.

    def document(name, value):
        path = root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return common.pin(path)

    rows = []
    for index, (zh, en) in enumerate([('甲。', 'First.'), ('乙。', 'Second.')], 1):
        cid = f'V3-UNIT-{index:02d}'
        rows.append({'id': cid, 'zh': zh, 'en': en,
                     'claim_ids': ['RULE-' + cid], 'shot_ids': [],
                     'audio': deepcopy(declared),
                     'provider_request': document(cid + '.request.json',
                                                  {'request': {'text': zh}}),
                     'speech_duration_seconds': 1.0,
                     'duration_seconds': common.cue_duration(1.0),
                     'visual_parts': None})
    slots = {'after018': None, 'after068': None, 'after083': None}
    voices = {'schema': 'faith-power-value-v3-voice-authoring-catalog-v2',
              'machine_id': 'synthetic-unit-fixture',
              'voice_authoring_projection': True,
              'projection_is_original_TTS_freeze': False,
              'cue_count': 2, 'cues': rows, 'new_live_result_voice_slots': slots}
    evidence = {'schema': 'ck3-faith-power-value-v3-cue-evidence-v1',
                'machine_id': 'synthetic-unit-fixture', 'native_checks': [],
                'cues': [{'id': r['id'], 'claim_ids': r['claim_ids'],
                          'shot_ids': [], 'source_refs': []} for r in rows],
                'claims': [{'id': r['claim_ids'][0], 'kind': 'source-rule',
                            'source_refs': [], 'native_check_ids': [],
                            'requires_native_checks': False} for r in rows]}
    config = native_project(rows)
    doc = {'schema': VALUE_V3_SCHEMA, 'machine_id': 'synthetic-unit-fixture',
           'scope': 'episode01-P-relic-review-scene',
           'voice_authoring_catalog': document('voices.json', voices),
           'cue_evidence_catalog': document('evidence.json', evidence),
           'project_config': document('project.json', config),
           'cues': rows, 'sequence': [r['id'] for r in rows],
           'pending_result_slots': slots, 'result_voice_batches': []}
    return doc, media


class ValueV3FormalTests(unittest.TestCase):
    def test_metadata_only_stats_media_without_opening_or_hashing_it(self):
        with tempfile.TemporaryDirectory() as name:
            doc, media = small_metadata_fixture(Path(name))
            inputs = FormalInputs(doc, common, metadata_only=True)
            with forbid_media_reads(media):
                # A negative control proves the guard catches Path binary reads.
                with self.assertRaisesRegex(AssertionError, 'opened fake media'):
                    media.read_bytes()
                result = inputs.inspect()
                with self.assertRaisesRegex(ValueError, 'refuses binary'):
                    inputs.load(doc['cues'][0]['audio'])
            self.assertFalse(result['ready_to_build'])
            self.assertFalse(result['fullrender_admitted'])
            self.assertFalse(result['media_bytes_revalidated'])
            self.assertTrue(result['metadata_only'])
            self.assertEqual(len(result['media_stat_observations']), 1)
            self.assertEqual(result['media_stat_observations'][0]['observed_bytes'],
                             media.stat().st_size)
            self.assertTrue(any('formal visual parts unbound' in gap
                                for gap in result['gaps']))
            self.assertTrue(any('result still unbound' in gap
                                for gap in result['gaps']))

    def test_native_project_requires_selected_sequence_and_exact_bilingual_text(self):
        rows = [{'id': 'cue-a', 'zh': '甲。', 'en': 'First.'},
                {'id': 'cue-b', 'zh': '乙。', 'en': 'Second.'}]
        config = native_project(rows)
        self.assertIs(common.explicit_project_config(config, rows), config)
        changed = deepcopy(config)
        changed['chapters'][0]['cues'].reverse()
        with self.assertRaisesRegex(ValueError, 'exact selected cue sequence'):
            common.explicit_project_config(changed, rows)
        for field, locale in [('narration', 'zh-CN'), ('subtitles', 'zh-CN'),
                              ('subtitles', 'en')]:
            with self.subTest(field=field, locale=locale):
                changed = deepcopy(config)
                changed['chapters'][0]['cues'][0][field][locale] = 'Changed'
                with self.assertRaisesRegex(ValueError, 'narration/subtitles differ'):
                    common.explicit_project_config(changed, rows)

    def test_explicit_groups_preserve_the_original_english_space(self):
        row = self.grouped_row()
        self.assertIs(common.subtitle_groups(row), row['subtitle_groups'])
        for language in ('zh', 'en'):
            self.assertEqual(''.join(g[language] for g in row['subtitle_groups']),
                             row[language])
        self.assertTrue(row['subtitle_groups'][0]['en'].endswith(' '))

    @staticmethod
    def grouped_row():
        return {'id': 'cue-grouped', 'zh': '甲。乙。', 'en': 'First. Second.',
                'speech_duration_seconds': 2.0,
                'subtitle_groups': [
                    {'start_seconds': 0, 'end_seconds': 1,
                     'zh': '甲。', 'en': 'First. '},
                    {'start_seconds': 1, 'end_seconds': 2,
                     'zh': '乙。', 'en': 'Second.'}]}

    def test_groups_reject_changed_text_overlap_and_out_of_speech_end(self):
        mutations = [('zh', lambda r: r['subtitle_groups'][0].update(zh='丙。')),
                     ('en', lambda r: r['subtitle_groups'][0].update(en='Wrong. ')),
                     ('overlap', lambda r: r['subtitle_groups'][1].update(start_seconds=.5)),
                     ('out-of-speech', lambda r: r['subtitle_groups'][1].update(end_seconds=2.1))]
        for label, mutate in mutations:
            with self.subTest(boundary=label):
                row = self.grouped_row()
                mutate(row)
                with self.assertRaises(ValueError):
                    common.subtitle_groups(row)

    def test_default_ungrouped_ass_and_srt_keep_legacy_ids_text_and_times(self):
        row = {'id': 'cue-default', 'zh': '规则。', 'en': 'Rule.',
               'speech_duration_seconds': 2.0, 'subtitle_start_seconds': .5,
               'duration_seconds': common.cue_duration(2.0),
               'visual_parts': [{'kind': 'diagram', 'duration_seconds': common.cue_duration(2.0),
                                 'disclosure': 'Source only'}]}
        self.assertEqual(common.subtitle_groups(row),
                         [{'start_seconds': .5, 'end_seconds': 2.0,
                           'zh': row['zh'], 'en': row['en']}])
        # Deterministic metrics only: no system font or font bytes are loaded.
        face = SimpleNamespace(getlength=lambda text: len(text) * 10)
        with patch.object(common.ImageFont, 'truetype', return_value=face):
            ass = common.subtitle(row, Path('unused-unit-font.ttf'), 'Unit Font')
        events = {line.split(',', 9)[4]: line.split(',', 9)
                  for line in ass.splitlines() if line.startswith('Dialogue: ')}
        for language, text in [('zh', row['zh']), ('en', row['en'])]:
            event = events['cue-default.' + language]
            self.assertEqual(event[1:3], ['0:00:00.50', '0:00:02.00'])
            self.assertTrue(event[9].endswith(text))
        self.assertEqual(set(events), {'cue-default.zh', 'cue-default.en', 'cue-default.source0'})
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'subtitles'
            common.companion_text([row], [{'actual_final_first_pts': 10.0}], output)
            prefix = '1\n00:00:10,500 --> 00:00:12,000\n'
            self.assertEqual((output / 'episode01.zh.srt').read_text('utf-8'),
                             prefix + '规则。\n')
            self.assertEqual((output / 'episode01.en.srt').read_text('utf-8'),
                             prefix + 'Rule.\n')
            self.assertEqual((output / 'episode01.bilingual.srt').read_text('utf-8'),
                             prefix + '规则。\nRule.\n')


if __name__ == '__main__':
    unittest.main()
