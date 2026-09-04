#!/usr/bin/env python3
"""Unit tests for the B3 exact-trigger explicit-AND candidate freezer."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))

import prepare_zg361_b3_exact_and_wrapper_candidate as candidate


class ExactAndWrapperCandidateTests(unittest.TestCase):
    def test_wrapper_preserves_body_bytes_below_one_explicit_and(self) -> None:
        original = "\n".join(
            (
                f"{candidate.EXACT_TRIGGER} = {{",
                "    child_trigger = { EXPECTED = $EXPECTED_OWNER$ }",
                "    var:sample = $EXPECTED_P2C_CYCLE$",
                "}",
            )
        )
        wrapped = candidate.explicit_and_wrapper(original)
        self.assertEqual(wrapped.count("AND = {"), 1)
        self.assertEqual(
            wrapped,
            "\n".join(
                (
                    f"{candidate.EXACT_TRIGGER} = {{",
                    "    AND = {",
                    "        child_trigger = { EXPECTED = $EXPECTED_OWNER$ }",
                    "        var:sample = $EXPECTED_P2C_CYCLE$",
                    "    }",
                    "}",
                )
            ),
        )

    def test_wrapper_rejects_wrong_definition(self) -> None:
        with self.assertRaises(candidate.CandidateError):
            candidate.explicit_and_wrapper("wrong = {\n    always = yes\n}")


if __name__ == "__main__":
    unittest.main()
