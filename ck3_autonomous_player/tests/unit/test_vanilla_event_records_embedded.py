from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.vanilla_events import (
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events import records_embedded
from xar_autoplayer.vanilla_events.records_embedded import (
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ENTRY = (
    WORKTREE_ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
)
# Updated when exact-build .5009/.1001 REDs replaced their legacy one-shot
# bindings with portable source-backed contracts.
EXPECTED_EMBEDDED_CANONICAL_SHA256 = (
    "F7D1F8DEE3D8B717486B2CF6261A78C49D2B34C9D404440FB7F3CD7D08C8F8DE"
)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _production_tree() -> ast.Module:
    return ast.parse(
        PRODUCTION_ENTRY.read_text(encoding="utf-8-sig"),
        filename=str(PRODUCTION_ENTRY),
    )


def _production_literal_keys(tree: ast.Module) -> tuple[str, ...]:
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "KNOWN_TIMELINE_INTERRUPTS"
    )
    if not isinstance(assignment.value, ast.Dict):
        raise AssertionError("production timeline interrupt literal is not a dict")
    return tuple(ast.literal_eval(key) for key in assignment.value.keys)


def _shared_aggregate_update_count(tree: ast.Module) -> int:
    count = 0
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "update"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "KNOWN_TIMELINE_INTERRUPTS"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "VANILLA_EVENT_TIMELINE_CONTRACTS"
        ):
            count += 1
    return count


class EmbeddedVanillaTimelineContractsTests(unittest.TestCase):
    def test_public_exports_are_exact(self) -> None:
        self.assertEqual(
            ["EMBEDDED_VANILLA_TIMELINE_CONTRACTS"],
            records_embedded.__all__,
        )
        self.assertIs(
            EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
            records_embedded.EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
        )

    def test_embedded_inventory_and_content_digest_are_frozen(self) -> None:
        self.assertEqual(len(EMBEDDED_VANILLA_TIMELINE_CONTRACTS), 79)
        self.assertFalse(
            any(
                key.startswith("zg361")
                for key in EMBEDDED_VANILLA_TIMELINE_CONTRACTS
            )
        )
        self.assertEqual(
            _canonical_sha256(EMBEDDED_VANILLA_TIMELINE_CONTRACTS),
            EXPECTED_EMBEDDED_CANONICAL_SHA256,
        )

    def test_production_literal_is_product_only_and_uses_shared_aggregate(
        self,
    ) -> None:
        tree = _production_tree()
        literal_keys = _production_literal_keys(tree)

        self.assertEqual(len(literal_keys), 17)
        self.assertEqual(len(set(literal_keys)), 17)
        self.assertTrue(all(key.startswith("zg361") for key in literal_keys))
        self.assertEqual(_shared_aggregate_update_count(tree), 1)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 164)


if __name__ == "__main__":
    unittest.main()
