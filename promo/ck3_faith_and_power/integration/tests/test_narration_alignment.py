"""Regressions from actual Edge SentenceBoundary punctuation omissions."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from faith_power_promo.narration_alignment import (
    decode_sentence_matches, encode_sentence_matches, reconcile_sentence_texts,
    BoundaryRecord, boundary_fields, checked_file_pin, parse_boundary_record,
    parse_file_pin, parse_raw_boundaries, subtitle_units,
    validate_wire_text,
)


class SentenceBoundaryTextTests(unittest.TestCase):
    def test_actual_leading_quote_omission_is_explicit(self) -> None:
        result = reconcile_sentence_texts(
            ('“当地仪式”也不等于不许远行。', '收费方式也一样。'),
            ('当地仪式”也不等于不许远行。', '收费方式也一样。'))
        self.assertEqual(result[0].status, 'LEADING_OPEN_QUOTE_OMITTED')
        self.assertEqual(result[0].reported_text, '当地仪式”也不等于不许远行。')
        self.assertEqual(result[1].status, 'EXACT')

    def test_interior_quote_omission_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Unrecognized'):
            reconcile_sentence_texts(('这里的“朝圣者”仍保留。',), ('这里的朝圣者”仍保留。',))

    def test_word_number_and_other_punctuation_changes_are_rejected(self) -> None:
        for source, reported in [('增加十分。', '增加二十分。'), ('“朝觐”仍可用。', '朝圣”仍可用。'),
                ('“朝觐”仍可用。', '朝觐仍可用。'), ('数字为80。', '数字为100。'), ('文字相同。', '文字 相同。')]:
            with self.subTest(source=source, reported=reported), self.assertRaises(ValueError):
                reconcile_sentence_texts((source,), (reported,))

    def test_sentence_count_change_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, 'counts must match'):
            reconcile_sentence_texts(('第一句。', '第二句。'), ('第一句。第二句。',))

    def test_json_array_roundtrip_preserves_status_and_original_text(self) -> None:
        original = reconcile_sentence_texts(('“热忱”的传教例子尤其值得看。',), ('热忱”的传教例子尤其值得看。',))
        decoded: object = json.loads(json.dumps(encode_sentence_matches(original), ensure_ascii=False))
        self.assertEqual(decode_sentence_matches(decoded), original)

    def test_persisted_wrong_missing_null_bool_and_float_fields_reject(self) -> None:
        valid = {'sequence': 1, 'source_text': '原文。', 'reported_text': '原文。', 'status': 'EXACT'}
        for key, value in [('sequence', True), ('sequence', 1.0), ('sequence', None),
                ('source_text', None), ('status', 'LEADING_OPEN_QUOTE_OMITTED')]:
            invalid = dict(valid)
            invalid[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                decode_sentence_matches([invalid])
        missing = dict(valid)
        del missing['reported_text']
        with self.assertRaises(ValueError):
            decode_sentence_matches([missing])
        with self.assertRaises(ValueError):
            decode_sentence_matches(None)


class SameStreamContractTests(unittest.TestCase):
    def test_actual_escaped_chunk_limit_and_incompatible_text_reject(self) -> None:
        self.assertEqual(validate_wire_text('“第一句。”'), '“第一句。”')
        for text in (None, '', ' ', '\x00', '&' * 820):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_wire_text(text)

    def fixture(self, root: Path) -> tuple[BoundaryRecord, Path]:
        audio, request, raw, source = (root / name for name in ('a.mp3', 'request.json', 'raw.jsonl', 'source.py'))
        audio.write_bytes(b'fixture audio, not decodable MP3')
        request.write_text(json.dumps({'machine_id': 'fixture-machine', 'observed_at_utc': '2026-10-22T00:00:00Z',
            'evidence_source': 'synthetic fixture invocation', 'provider': {'provider_id': 'edge-tts', 'tool_version': '7.3.1'},
            'cue_id': 'cue01', 'request': {'text': '第一句。第二句。', 'voice': 'fixture', 'rate': '+0%', 'pitch': '+0Hz',
            'volume': '+0%', 'audio_format': 'mp3', 'cache_salt': ''}}), encoding='utf-8')
        source.write_text('# fixture source', encoding='utf-8')
        raw.write_text(json.dumps({'type': 'SentenceBoundary', 'offset': 0, 'duration': 20000000,
                                   'text': '第一句。'}) + '\n' + json.dumps({'type': 'SentenceBoundary',
                                   'offset': 10000000, 'duration': 20000000, 'text': '第二句。'}) + '\n', encoding='utf-8')
        record: BoundaryRecord = {'schema': 'faith-power-same-stream-boundaries-v1', 'machine_id': 'fixture-machine',
            'observed_at_utc': '2026-10-22T00:00:00Z', 'cue_id': 'cue01', 'request': checked_file_pin(request),
            'audio': checked_file_pin(audio), 'raw_metadata': checked_file_pin(raw), 'communicate_source': checked_file_pin(source),
            'timebase': '1/10000000', 'status': 'complete', 'stream_complete': True, 'stream_error': None,
            'actual_wire_calls': 1, 'events': parse_raw_boundaries(raw)}
        envelope = root / 'boundaries.json'
        envelope.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        return record, envelope

    def test_persisted_record_real_pins_and_actual_subtitle_consumer(self) -> None:
        from faith_power_promo.full_episode import subtitle_groups
        with tempfile.TemporaryDirectory() as directory:
            record, envelope = self.fixture(Path(directory))
            self.assertEqual(parse_boundary_record(json.loads(envelope.read_text('utf-8'))), record)
            units = subtitle_units([{'id': 'a', 'zh': '第一句。', 'en': 'First. '},
                                    {'id': 'b', 'zh': '第二句。', 'en': 'Second.'}], '第一句。第二句。', 'First. Second.')
            fields = boundary_fields(checked_file_pin(envelope), machine_id='fixture-machine', cue_id='cue01',
                audio=record['audio'], request=record['request'], units=units, speech_seconds=2.5)
            self.assertEqual([group['end_seconds'] for group in fields['subtitle_groups']], [1.0, 2.5])
            # This is the actual shared ASS/SRT consumer, not a test compositor.
            row = {'zh': '第一句。第二句。', 'en': 'First. Second.', 'speech_duration_seconds': 2.5, **fields}
            self.assertEqual(subtitle_groups(json.loads(json.dumps(row))), fields['subtitle_groups'])

    def test_contract_rejects_missing_wrong_null_bool_float_and_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record, _ = self.fixture(Path(directory))
            for key, value in [('actual_wire_calls', True), ('actual_wire_calls', 1.0),
                    ('stream_complete', 1), ('status', None), ('events', None), ('audio', None),
                    ('stream_error', 'hidden error'), ('schema', 'wrong'), ('timebase', '1/1000')]:
                broken: dict[str, object] = dict(record)
                broken[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    parse_boundary_record(broken)
            for key in record:
                missing: dict[str, object] = dict(record)
                del missing[key]
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    parse_boundary_record(missing)
            extra: dict[str, object] = {**record, 'provider_request': record['request']}
            with self.assertRaises(ValueError):
                parse_boundary_record(extra)
            audio = record['audio']
            assert audio is not None
            Path(audio['path']).write_bytes(b'tampered audio')
            with self.assertRaisesRegex(ValueError, 'changed'):
                parse_boundary_record(record)

    def test_raw_duplicate_keys_tick_types_formats_and_large_exact_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.jsonl'
            for line in ['{"type":"SentenceBoundary","offset":0,"offset":1,"duration":1,"text":"a"}',
                    '{"type":"SentenceBoundary","offset":true,"duration":1,"text":"a"}',
                    '{"type":"SentenceBoundary","offset":0,"duration":1.0,"text":"a"}',
                    '{"type":"SentenceBoundary","offset":-1,"duration":1,"text":"a"}',
                    '{"type":"WordBoundary","offset":0,"duration":1,"text":"a"}', '{}']:
                path.write_text(line, encoding='utf-8')
                with self.subTest(line=line), self.assertRaises(ValueError):
                    parse_raw_boundaries(path)
            path.write_text('{"type":"SentenceBoundary","offset":9007199254740993,"duration":1,"text":"a"}', encoding='utf-8')
            events = parse_raw_boundaries(path)
            self.assertEqual(json.loads(json.dumps(events))[0]['offset_ticks'], '9007199254740993')
            record, envelope = self.fixture(Path(directory))
            bad: dict[str, object] = dict(record)
            for ticks in ['00', '+1', '1.0', '18446744073709551616', 1, True, None]:
                bad['events'] = [{**record['events'][0], 'offset_ticks': ticks}]
                with self.subTest(ticks=ticks), self.assertRaises(ValueError):
                    parse_boundary_record(bad)
            for pin_size in [True, 1.0, None]:
                with self.assertRaises(ValueError):
                    parse_file_pin({**checked_file_pin(envelope), 'bytes': pin_size})

    def test_units_are_exact_and_failure_missing_null_empty_remain_distinct(self) -> None:
        for value in [None, [], [{'id': 'x', 'zh': 'a'}], [{'id': True, 'zh': 'a', 'en': 'b'}],
                      [{'id': 'x', 'zh': 'edited', 'en': 'b'}]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                subtitle_units(value, 'a', 'b')
        with tempfile.TemporaryDirectory() as directory:
            record, _ = self.fixture(Path(directory))
            failed: dict[str, object] = {**record, 'status': 'failed', 'stream_complete': False,
                'stream_error': 'actual partial failure', 'audio': None, 'raw_metadata': None,
                'actual_wire_calls': 0, 'events': []}
            self.assertIsNone(parse_boundary_record(json.loads(json.dumps(failed)))['raw_metadata'])
            del failed['raw_metadata']
            with self.assertRaises(ValueError):
                parse_boundary_record(failed)


if __name__ == '__main__':
    unittest.main()
