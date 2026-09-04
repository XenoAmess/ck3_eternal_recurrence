"""Static tests for the B3 mutually exclusive trigger-body bisect builder."""

from __future__ import annotations

import hashlib
import unittest

import prepare_zg361_b3_trigger_body_bisect as bisect


BOM = b"\xef\xbb\xbf"
CANDIDATE_REAL = "\n".join(
    (
        f"{bisect.CANDIDATE_READY} = {{",
        *bisect.FALSE_STUB_TERMS[bisect.CANDIDATE_READY],
        "    always = yes",
        "}",
    )
)
EXACT_REAL = "\n".join(
    (
        f"{bisect.FROZEN_MANAGER_EXACT} = {{",
        f"    {bisect.CANDIDATE_READY} = {{",
        "        EXPECTED_OWNER = $EXPECTED_OWNER$",
        "        EXPECTED_P2C_CYCLE = $EXPECTED_P2C_CYCLE$",
        "        EXPECTED_P2C_CASE = $EXPECTED_P2C_CASE$",
        "    }",
        *bisect.FALSE_STUB_TERMS[bisect.FROZEN_MANAGER_EXACT],
        "    always = yes",
        "}",
    )
)
BASE = BOM + (
    "# GENERATED FILE — test\n\n" + CANDIDATE_REAL + "\n\n" + EXACT_REAL + "\n"
).encode("utf-8")


class TriggerBodyBisectTests(unittest.TestCase):
    def test_v1_keeps_candidate_real_and_stubs_exact(self) -> None:
        original = bisect.parsed_blocks(BASE)
        rendered = bisect.render_variant(
            BASE,
            real=bisect.CANDIDATE_READY,
            stub=bisect.FROZEN_MANAGER_EXACT,
        )
        parsed = bisect.parsed_blocks(rendered)
        self.assertTrue(rendered.startswith(BOM))
        self.assertIn(b"# GENERATED FILE", rendered)
        self.assertEqual(original[bisect.CANDIDATE_READY], parsed[bisect.CANDIDATE_READY])
        self.assertEqual(
            bisect.false_stub(bisect.FROZEN_MANAGER_EXACT),
            parsed[bisect.FROZEN_MANAGER_EXACT],
        )
        self.assertEqual(
            bisect.EXPECTED_ABI[bisect.FROZEN_MANAGER_EXACT],
            bisect.placeholder_set(parsed[bisect.FROZEN_MANAGER_EXACT]),
        )
        self.assertEqual(
            bisect.EXPECTED_PROVIDER_PLACEHOLDERS,
            bisect.placeholder_set(rendered),
        )

    def test_v2_keeps_exact_call_pointing_to_candidate_stub(self) -> None:
        original = bisect.parsed_blocks(BASE)
        rendered = bisect.render_variant(
            BASE,
            real=bisect.FROZEN_MANAGER_EXACT,
            stub=bisect.CANDIDATE_READY,
        )
        parsed = bisect.parsed_blocks(rendered)
        self.assertEqual(original[bisect.FROZEN_MANAGER_EXACT], parsed[bisect.FROZEN_MANAGER_EXACT])
        self.assertEqual(
            bisect.false_stub(bisect.CANDIDATE_READY),
            parsed[bisect.CANDIDATE_READY],
        )
        self.assertIn(
            "zg361_p2c_m360_candidate_ready_trigger = {",
            parsed[bisect.FROZEN_MANAGER_EXACT],
        )
        self.assertEqual(
            bisect.EXPECTED_ABI[bisect.CANDIDATE_READY],
            bisect.placeholder_set(parsed[bisect.CANDIDATE_READY]),
        )
        self.assertEqual(
            bisect.EXPECTED_PROVIDER_PLACEHOLDERS,
            bisect.placeholder_set(rendered),
        )

    def test_old_zero_placeholder_false_stub_is_materially_abi_invalid(self) -> None:
        old = f"{bisect.CANDIDATE_READY} = {{\n    always = no\n}}"
        self.assertEqual(frozenset(), bisect.placeholder_set(old))
        self.assertNotEqual(
            bisect.EXPECTED_ABI[bisect.CANDIDATE_READY],
            bisect.placeholder_set(old),
        )

    def test_tree_delta_reports_only_changed_provider(self) -> None:
        unchanged = {"bytes": 3, "sha256": hashlib.sha256(b"old").hexdigest()}
        before = {
            "descriptor.mod": unchanged,
            bisect.TRIGGER_RELATIVE: {
                "bytes": 4,
                "sha256": hashlib.sha256(b"real").hexdigest(),
            },
        }
        after = {
            "descriptor.mod": unchanged,
            bisect.TRIGGER_RELATIVE: {
                "bytes": 4,
                "sha256": hashlib.sha256(b"stub").hexdigest(),
            },
        }
        self.assertEqual(
            [bisect.TRIGGER_RELATIVE],
            [row["path"] for row in bisect.tree_delta(before, after)],
        )


if __name__ == "__main__":
    unittest.main()
