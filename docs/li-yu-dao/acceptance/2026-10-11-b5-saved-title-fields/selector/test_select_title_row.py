"""Synthetic framing/hash/output tests only; not an actual SAVE qualification."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('selector', Path(__file__).with_name('select_title_row.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def actual_frame(rows):
    return b'head={\n}\nlanded_titles={\n\tlanded_titles={\n' + rows + b'\t}\n}\ndynasties={\n}\n'


class SelectorTests(unittest.TestCase):
    def test_exact_nested_title_only_full_one_pass_hash(self):
        data = actual_frame(b'7={\n key="unselected"\n}\n18373={\n key="braces { }"\n}\n')
        class SmallReads(io.BytesIO):
            def read(self, n=-1):
                return super().read(min(n, 7))
        row, size, sha = m.scan(SmallReads(data), 18373)
        self.assertEqual((size, sha), (len(data), hashlib.sha256(data).hexdigest()))
        self.assertEqual(bytes(row.row), b'18373={\n key="braces { }"\n}\n')

    def test_same_numeric_id_outside_title_not_selected(self):
        data = b'18373={\n wrong=yes\n}\n' + actual_frame(b'18373={\n right=yes\n}\n')
        row, _, _ = m.scan(io.BytesIO(data), 18373)
        self.assertNotIn(b'wrong', row.row)

    def test_duplicate_and_truncated_actual_database_reject(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            m.scan(io.BytesIO(actual_frame(b'18373={\n}\n18373={\n}\n')), 18373)
        with self.assertRaises(ValueError):
            m.scan(io.BytesIO(actual_frame(b'18373={\n}\n')[:-20]), 18373)

    def test_overflow_discards_row_keeps_full_stream_authentication(self):
        data = actual_frame(b'18373={\n value="' + b'a' * 40000 + b'"\n}\n')
        row, size, sha = m.scan(io.BytesIO(data), 18373)
        self.assertTrue(row.row_overflow)
        self.assertEqual(row.row, b'')
        self.assertEqual((size, sha), (len(data), hashlib.sha256(data).hexdigest()))
        out = json.loads(m.render(row, {}, {}))
        self.assertEqual(out['status'], 'ROW_RETENTION_LIMIT_EXCEEDED')
        self.assertFalse(out['B5_pass'])

    def test_flat_layout_and_missing_target_fail_closed(self):
        for data in (b'landed_titles={\n18373={\n}\n}\ndynasties={\n}\n', actual_frame(b'7={\n}\n')):
            with self.assertRaises(ValueError):
                m.scan(io.BytesIO(data), 18373)


if __name__ == '__main__':
    unittest.main()
