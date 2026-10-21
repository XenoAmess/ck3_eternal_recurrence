"""Real candidate parsing through raw-YML normalization and token validation."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translate_localization_minimax import (
    TranslationError, assert_protected_tokens, extract_candidate,
    normalize_raw_ck3_newline_escapes,
)


class NewlineBoundaryTests(unittest.TestCase):
    def test_json_decoded_line_break_returns_to_raw_ck3_domain(self) -> None:
        source = {"entry": "First\\n[scope:item.GetName]\\n#!"}
        envelope = json.dumps({"entry": "Premier\n[scope:item.GetName]\n#!"})
        candidate = extract_candidate(envelope, ("entry",))
        normalized = normalize_raw_ck3_newline_escapes(source, candidate)
        assert_protected_tokens(source, normalized)
        self.assertEqual(normalized["entry"], "Premier\\n[scope:item.GetName]\\n#!")

    def test_already_raw_escape_is_not_encoded_twice(self) -> None:
        source = {"entry": "First\\nLast"}
        self.assertEqual(normalize_raw_ck3_newline_escapes(source, source), source)

    def test_counts_and_other_tokens_still_reject_changes(self) -> None:
        source = {"entry": "First\\n[scope:item.GetName]\\nLast"}
        for value in ("Premier\n[scope:item.GetName]", "Premier\n[scope:item.GetName]\n\nFin", "Premier\n[scope:other.GetName]\nFin"):
            with self.subTest(value=value), self.assertRaises(TranslationError):
                assert_protected_tokens(source, normalize_raw_ck3_newline_escapes(source, {"entry": value}))

    def test_unrequested_or_literal_backslash_line_break_is_rejected(self) -> None:
        for source in ({"entry": "Single line"}, {"entry": r"Literal \\n text"}):
            with self.subTest(source=source), self.assertRaises(TranslationError):
                normalize_raw_ck3_newline_escapes(source, {"entry": "New\nline"})


if __name__ == "__main__":
    unittest.main()
