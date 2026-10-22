"""Regressions from actual Edge SentenceBoundary punctuation omissions."""
from __future__ import annotations

import json
import unittest

from faith_power_promo.narration_alignment import (
    decode_sentence_matches, encode_sentence_matches, reconcile_sentence_texts,
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


if __name__ == '__main__':
    unittest.main()
