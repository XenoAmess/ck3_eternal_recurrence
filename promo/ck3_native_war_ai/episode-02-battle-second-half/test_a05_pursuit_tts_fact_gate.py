"""A05 pursuit audio binds the new native controls and independent parity receipt."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import unittest

from render_selected_narration import identity, validate_a05_pursuit_facts


ROOT = Path(__file__).resolve().parent
FACTS = ROOT / "cards" / "e2-02-03-a05-pursuit-facts-20260928.json"
DRAFT = ROOT / "narration-script-draft.md"


class A05PursuitTTSFactGateTest(unittest.TestCase):
    def test_exact_pursuit_receipt_and_wrong_digest(self):
        args = Namespace(a05_pursuit_facts=FACTS, draft=DRAFT,
                         expected_a05_pursuit_facts_sha256=identity(FACTS)["sha256"])
        checked = validate_a05_pursuit_facts(args)
        self.assertIn("GREEN", checked["verifier_stdout"])
        args.expected_a05_pursuit_facts_sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "exact checked-in"):
            validate_a05_pursuit_facts(args)


if __name__ == "__main__":
    unittest.main()
