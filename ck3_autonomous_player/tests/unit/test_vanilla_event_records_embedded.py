from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from xar_autoplayer.vanilla_events import (
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events import (
    records_embedded,
    records_embedded_a,
    records_embedded_b,
    records_embedded_c,
)
from xar_autoplayer.vanilla_events.records_embedded import (
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_embedded_a import (
    EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_embedded_b import (
    EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_embedded_c import (
    EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS,
)


WORKTREE_ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ENTRY = (
    WORKTREE_ROOT / "tools" / "zg361_phase2_promotion_source_production_entry.py"
)
def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


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
        self.assertEqual(
            ["EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS"],
            records_embedded_a.__all__,
        )
        self.assertEqual(
            ["EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS"],
            records_embedded_b.__all__,
        )
        self.assertEqual(
            [
                "EMBEDDED_C_VANILLA_OBSERVATIONS",
                "EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS",
            ],
            records_embedded_c.__all__,
        )

    def test_shards_preserve_order_content_and_canonical_bytes(self) -> None:
        shards = (
            EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS,
            EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS,
            EMBEDDED_C_VANILLA_TIMELINE_CONTRACTS,
        )
        self.assertEqual(tuple(map(len, shards)), (27, 26, 26))

        combined: dict[str, dict[str, object]] = {}
        for shard in shards:
            self.assertTrue(combined.keys().isdisjoint(shard))
            combined.update(shard)

        self.assertEqual(combined, EMBEDDED_VANILLA_TIMELINE_CONTRACTS)
        self.assertEqual(
            tuple(combined),
            tuple(EMBEDDED_VANILLA_TIMELINE_CONTRACTS),
        )
        for event_key, contract in combined.items():
            self.assertIs(
                contract,
                EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key],
            )
        self.assertEqual(
            _canonical_bytes(combined),
            _canonical_bytes(EMBEDDED_VANILLA_TIMELINE_CONTRACTS),
        )

    def test_aggregate_and_shards_retain_utf8_bom(self) -> None:
        modules = (
            records_embedded,
            records_embedded_a,
            records_embedded_b,
            records_embedded_c,
        )
        for module in modules:
            with self.subTest(module=module.__name__):
                self.assertTrue(
                    Path(module.__file__).read_bytes().startswith(b"\xef\xbb\xbf")
                )

    def test_embedded_inventory_is_campaign_neutral(self) -> None:
        self.assertEqual(len(EMBEDDED_VANILLA_TIMELINE_CONTRACTS), 79)
        self.assertFalse(
            any(
                key.startswith("zg361")
                for key in EMBEDDED_VANILLA_TIMELINE_CONTRACTS
            )
        )
        for event_key, contract in EMBEDDED_VANILLA_TIMELINE_CONTRACTS.items():
            with self.subTest(event=event_key):
                self.assertNotIn("date_raw", contract)
                self.assertNotIn("date_raw_range", contract)
                self.assertEqual(contract.get("root_character_id"), "$player")

    def test_production_literal_is_product_only_and_uses_shared_aggregate(
        self,
    ) -> None:
        tree = _production_tree()
        literal_keys = _production_literal_keys(tree)

        self.assertEqual(len(literal_keys), 24)
        self.assertEqual(len(set(literal_keys)), 24)
        self.assertEqual(
            [key for key in literal_keys if not key.startswith("zg361")],
            [
                "study_confucian_classics_outcome.1030",
                "childhood.2010",
                "coming_of_age.1002",
                "hostile_scheme_discovery.1001",
                "martial_authority_special.3000",
                "imperial_examination.7100",
                "tgp_dynastic_cycle.0082",
            ],
        )
        self.assertEqual(
            sum(key.startswith("zg361") for key in literal_keys), 17
        )
        self.assertEqual(_shared_aggregate_update_count(tree), 1)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 185)


if __name__ == "__main__":
    unittest.main()
