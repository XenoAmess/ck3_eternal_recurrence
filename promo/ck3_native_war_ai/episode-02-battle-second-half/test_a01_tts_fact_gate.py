"""A01 reinforcement audio may bind only the checked-in native join receipt."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import unittest

from render_selected_narration import identity, validate_a01_facts


ROOT = Path(__file__).resolve().parent
FACTS = ROOT / "cards" / "e2-06-07-a01-join-facts-20260928-v2.json"
DRAFT = ROOT / "narration-script-draft.md"


class A01TTSFactGateTest(unittest.TestCase):
    def test_exact_join_receipt_and_wrong_digest(self):
        args = Namespace(a01_facts=FACTS, draft=DRAFT,
                         expected_a01_facts_sha256=identity(FACTS)["sha256"])
        checked = validate_a01_facts(args)
        self.assertIn("GREEN", checked["verifier_stdout"])
        args.expected_a01_facts_sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "exact checked-in"):
            validate_a01_facts(args)


if __name__ == "__main__":
    unittest.main()
