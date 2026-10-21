"""Regressions for R2's real empty-slot diagnostics; these are not live PASS.

The shared scanner inspects production output. It neither interprets CK3 nor
initializes a fixture with the postcondition that the live case must establish.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import ClassVar
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ck3_text_projection import Block, blocks, masked
import living_artifacts_content as content


class ContentGenerationTests(unittest.TestCase):
    source: ClassVar[str]
    definitions: ClassVar[tuple[Block, ...]]
    direct: ClassVar[dict[int, str]]
    parents: ClassVar[dict[int, int]]
    children: ClassVar[dict[int, list[Block]]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = content.render_content_effects()
        cls.definitions = tuple(blocks(cls.source))
        mask = masked(cls.source)
        children: dict[int, list[Block]] = {}
        cls.parents = {}
        stack: list[Block] = []
        for block in cls.definitions:
            while stack and block.start >= stack[-1].end:
                stack.pop()
            if stack:
                children.setdefault(stack[-1].start, []).append(block)
                cls.parents[block.start] = stack[-1].start
            stack.append(block)
        cls.children = children
        cls.direct = {}
        for block in cls.definitions:
            value = list(mask[block.opening + 1:block.end - 1])
            offset = block.opening + 1
            for child in children.get(block.start, []):
                value[child.start - offset:child.end - offset] = " " * (child.end - child.start)
            cls.direct[block.start] = "".join(value)

    def assert_lazy_presence(self, block: Block, required: tuple[str, ...]) -> None:
        # The read must be the BODY of trigger_if. Presence in its child limit
        # is the boundary; textual order in the same eager block is insufficient.
        self.assertEqual(block.key, "trigger_if")
        guards = [child for child in self.children.get(block.start, []) if child.key == "limit"]
        self.assertEqual(len(guards), 1)
        for field in required:
            self.assertRegex(self.direct[guards[0].start], rf"has_variable\s*=\s*{field}\b")
        parent = self.parents[block.start]
        siblings = self.children[parent]
        index = siblings.index(block)
        self.assertLess(index + 1, len(siblings))
        fallback = siblings[index + 1]
        self.assertEqual(fallback.key, "trigger_else")
        self.assertRegex(self.direct[fallback.start], r"always\s*=\s*no\b")

    def test_all_slot_comparisons_have_parent_child_lazy_id_and_rank_guards(self) -> None:
        # R2 failed on an absent curse ID before it could even read the rank.
        # Check every generated LHS, including target ORs and mutation weights.
        reads = 0
        for block in self.definitions:
            direct = self.direct[block.start]
            for match in re.finditer(r"var:(xalw_(?:affix|curse)(?:_rank)?_[1-6])\s*(?:=|>|<)", direct):
                field = match.group(1)
                stem, slot = field.removesuffix("_" + field.rsplit("_", 1)[1]).replace("_rank", ""), field.rsplit("_", 1)[1]
                self.assert_lazy_presence(block, (f"{stem}_{slot}", f"{stem}_rank_{slot}"))
                reads += 1
        self.assertGreater(reads, 100)

    def test_refresh_and_selectors_do_not_initialize_empty_slots(self) -> None:
        # Empty is distinct from a new ID/rank zero; no content callback owns
        # slot creation. Only the actual core growth transaction may create it.
        for block in self.definitions:
            if block.key in ("set_variable", "change_variable"):
                self.assertNotRegex(self.direct[block.start], r"name\s*=\s*xalw_(?:affix|curse)(?:_rank)?_[1-6]\b")

    def test_first_prima_month_and_mutation_lazily_guard_optional_calendar_state(self) -> None:
        for block in self.definitions:
            direct = self.direct[block.start]
            for field in ("xalw_content_prima_last_month", "xalw_content_prima_streak"):
                for match in re.finditer(rf"var:{field}\s*(?:>=|=|>)", direct):
                    self.assert_lazy_presence(block, (field,))
        self.assertNotRegex(self.source, r"var:[\w:]+\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*=")

    def test_same_level_presence_is_rejected_as_a_lazy_boundary(self) -> None:
        # The old R2 patch passed a textual-order test. This negative checks the
        # actual guard contract so that same-level rewriting cannot regress it.
        fake = Block("limit", 0, 7, 13)
        with self.assertRaises(AssertionError):
            self.assert_lazy_presence(fake, ("xalw_curse_1", "xalw_curse_rank_1"))

    def test_no_presence_guard_shares_an_eager_block_with_its_read(self) -> None:
        for block in self.definitions:
            direct = self.direct[block.start]
            fields = re.findall(r"has_variable\s*=\s*(\w+)", direct)
            for field in fields:
                self.assertNotRegex(direct, rf"var:{field}\b", (block.key, field))

    def test_optional_projection_fields_use_lazy_branches(self) -> None:
        fields = ("xalw_content_ink_slot", "xalw_content_prima_slot", "xalw_content_echo_power")
        projection_names = {
            "xalw_content_refresh_artifact_effect", "xalw_content_on_equip_effect",
            "xalw_content_on_owner_changed_effect",
        }
        by_start = {block.start: block for block in self.definitions}
        for block in self.definitions:
            top = block
            while top.start in self.parents:
                top = by_start[self.parents[top.start]]
            if top.key not in projection_names:
                continue
            direct = self.direct[block.start]
            for field in fields:
                if re.search(rf"var:{field}\s*(?:=|>=|<=|>|<)", direct):
                    self.assert_lazy_presence(block, (field,))


if __name__ == "__main__":
    unittest.main()
