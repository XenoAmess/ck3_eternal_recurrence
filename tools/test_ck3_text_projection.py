import unittest

from ck3_text_projection import blocks, digest, named_block, project, recover


class TextProjectionTest(unittest.TestCase):
    def test_reversible_projection_preserves_native_controls(self):
        native = 'window = {\n a = { name = "cards" }\n onclick = "[Native.Action]"\n}\n'
        changes = [('a = { name = "cards" }', 'a = { name = "cards" wrap_count = 3 }')]
        result = project(native, digest(native), changes)
        self.assertIn('[Native.Action]', result)
        self.assertEqual(recover(result, digest(native), changes), native)

    def test_changed_source_and_changed_projection_are_rejected(self):
        native = 'x = { value = 3 }'
        changes = [('value = 3', 'value = 100')]
        with self.assertRaises(ValueError):
            project(native + '\nx = 1', digest(native), changes)
        with self.assertRaises(ValueError):
            recover('x = { value = 100 ignored = yes }', digest(native), changes)

    def test_ambiguous_anchor_is_rejected(self):
        native = 'x = { value = 3 value = 3 }'
        with self.assertRaises(ValueError):
            project(native, digest(native), [('value = 3', 'value = 100')])

    def test_scanner_ignores_quoted_and_commented_braces(self):
        source = 'x = { # }\n text = "{ \\" }"\n y = { name = "cards" }\n }'
        self.assertEqual([b.key for b in blocks(source)], ['x', 'y'])
        span = named_block(source, 'y', 'cards')
        self.assertEqual(source[span.start:span.end], 'y = { name = "cards" }')

    def test_unbalanced_and_unterminated_text_is_rejected(self):
        for source in ('x = {', 'x = }', 'x = "missing'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                blocks(source)

    def test_duplicate_named_block_is_rejected(self):
        with self.assertRaises(ValueError):
            named_block('x = { name = "cards" } x = { name = "cards" }', 'x', 'cards')

    def test_bom_and_line_endings_normalize(self):
        self.assertEqual(digest('\ufeffx = {\r\n}\r\n'), digest('x = {\n}\n'))


if __name__ == '__main__':
    unittest.main()
