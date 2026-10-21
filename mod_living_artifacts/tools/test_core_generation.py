"""Offline structural regressions for the native gameplay script producers.

These checks inspect the actual generated definition tree. They do not execute
CK3, establish a native ABI, prove material destruction, or qualify live play.
In particular, native artifact-modifier removal still needs an equip/unequip
business observation; this suite only prevents a stale character projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import re
import sys
from typing import ClassVar
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ck3_text_projection import Block, blocks, masked, normalize
import living_artifacts_core as core


@dataclass(frozen=True)
class Scalar:
    key: str
    operator: str
    value: str
    start: int


class Script:
    """Small structural view over the shared scanner, not a CK3 interpreter."""

    def __init__(self, text: str) -> None:
        self.text = normalize(text)
        self.mask = masked(self.text)
        self.blocks = tuple(blocks(self.text))

    def children(self, parent: Block) -> tuple[Block, ...]:
        inside = tuple(item for item in self.blocks if parent.opening < item.start < parent.end)
        return tuple(item for item in inside if not any(
            other.opening < item.start < other.end for other in inside
        ))

    def descendants(self, parent: Block, key: str) -> tuple[Block, ...]:
        return tuple(item for item in self.blocks if item.key == key and parent.opening < item.start < parent.end)

    def named(self, key: str) -> Block:
        found = tuple(item for item in self.blocks if item.key == key)
        if len(found) != 1:
            raise AssertionError(f"Expected one definition {key!r}; got {len(found)}")
        return found[0]

    def child(self, parent: Block, key: str) -> Block:
        found = tuple(item for item in self.children(parent) if item.key == key)
        if len(found) != 1:
            raise AssertionError(f"Expected one direct {key!r} child of {parent.key!r}; got {len(found)}")
        return found[0]

    def scalars(self, parent: Block) -> tuple[Scalar, ...]:
        content = list(self.mask[parent.opening + 1:parent.end - 1])
        offset = parent.opening + 1
        for child in self.children(parent):
            content[child.start - offset:child.end - offset] = " " * (child.end - child.start)
        return tuple(Scalar(match.group(1), match.group(2), match.group(3), offset + match.start())
                     for match in re.finditer(r"([\w:@.-]+)\s*(\?=|>=|<=|!=|=|>|<)\s*([^\s{}]+)", "".join(content)))

    def scalar(self, parent: Block, key: str) -> Scalar:
        found = tuple(item for item in self.scalars(parent) if item.key == key)
        if len(found) != 1:
            raise AssertionError(f"Expected one scalar {key!r} in {parent.key!r}; got {len(found)}")
        return found[0]

    def variable_actions(self, parent: Block, operation: str, variable: str) -> tuple[Block, ...]:
        return tuple(item for item in self.descendants(parent, operation)
                     if self.scalar(item, "name").value == variable)

    def ancestors(self, block: Block) -> tuple[Block, ...]:
        return tuple(item for item in self.blocks if item.opening < block.start < item.end)


class CoreGenerationTests(unittest.TestCase):
    effects: ClassVar[Script]
    events: ClassVar[Script]
    triggers: ClassVar[Script]
    values: ClassVar[Script]

    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = Script(core.render_core_effects())
        cls.events = Script(core.render_core_events())
        cls.triggers = Script(core.render_core_triggers())
        cls.values = Script(core.render_core_script_values())

    def test_feeding_xp_is_guarded_by_post_destruction_absence(self) -> None:
        script = self.effects
        feed = script.named("xalw_feed_material_effect")
        transaction = script.child(feed, "if")
        destruction = script.scalar(transaction, "destroy_artifact")
        self.assertEqual(destruction.value, "scope:xalw_material")
        changes = script.variable_actions(feed, "change_variable", "xalw_pending_xp")
        self.assertEqual(len(changes), 1)
        credit = changes[0]
        self.assertGreater(credit.start, destruction.start)
        guarded = tuple(parent for parent in script.ancestors(credit)
                        if parent.key == "if" and parent != transaction)
        self.assertEqual(len(guarded), 1)
        check = script.child(guarded[0], "limit")
        absent = script.child(check, "NOT")
        self.assertEqual(script.scalar(absent, "exists").value, "scope:xalw_material")
        self.assertEqual(script.scalar(credit, "add").value, "scope:xalw_feed_xp")

    def test_feeding_imprint_commits_in_same_success_branch_as_xp(self) -> None:
        script = self.effects
        feed = script.named("xalw_feed_material_effect")
        credit = script.variable_actions(feed, "change_variable", "xalw_pending_xp")[0]
        imprint = script.variable_actions(feed, "set_variable", "xalw_feeding_imprint")
        self.assertEqual(len(imprint), 1)
        self.assertEqual(script.ancestors(imprint[0]), script.ancestors(credit))
        self.assertEqual(script.scalar(imprint[0], "days").value, "90")

    def test_feeding_preview_and_producer_share_one_xp_value(self) -> None:
        script = self.effects
        feed = script.named("xalw_feed_material_effect")
        freezes = tuple(item for item in script.descendants(feed, "save_scope_value_as")
                        if script.scalar(item, "name").value == "xalw_feed_xp")
        self.assertEqual(len(freezes), 1)
        self.assertEqual(script.scalar(freezes[0], "value").value, "xalw_selected_feed_xp_value")
        localized = core.render_core_localization("simp_chinese")["xalw.11.desc"]
        self.assertIn("ScriptValue('xalw_selected_feed_xp_value')", localized)

    def test_four_native_rarity_inputs_have_exact_distinct_rewards(self) -> None:
        script = self.values
        source = script.named("xalw_feed_base_xp_value")
        rewards: dict[str, int] = {}
        for branch in script.children(source):
            condition = script.child(branch, "limit")
            rewards[script.scalar(condition, "rarity").value] = int(script.scalar(branch, "add").value)
        self.assertEqual(rewards, {"common": 80, "masterwork": 200, "famed": 500, "illustrious": 1200})
        selected = script.named("xalw_selected_feed_xp_value")
        self.assertEqual(script.scalar(selected, "floor").value, "yes")
        self.assertEqual(script.scalar(script.child(selected, "if"), "multiply").value, "1.25")

    def test_every_crossed_level_advances_sequence_inside_auto_loop(self) -> None:
        script = self.effects
        settle = script.named("xalw_settle_xp_effect")
        loop = script.descendants(settle, "while")
        self.assertEqual(len(loop), 1)
        condition = script.child(loop[0], "limit")
        comparison = script.scalar(condition, "var:xalw_xp_in_level")
        self.assertEqual((comparison.operator, comparison.value), (">=", "xalw_next_level_xp_value"))
        for variable in ("xalw_level", "xalw_growth_sequence"):
            increment = script.variable_actions(loop[0], "change_variable", variable)
            self.assertEqual(len(increment), 1)
            self.assertEqual(script.scalar(increment[0], "add").value, "1")
        expiry = tuple(item for item in script.descendants(loop[0], "trigger_event"))
        self.assertEqual(expiry, ())

    def test_low_and_high_level_growth_weights_are_specified_independently(self) -> None:
        script = self.effects
        loop = script.descendants(script.named("xalw_settle_xp_effect"), "while")[0]
        low_branch = script.child(loop, "if")
        high_branch = script.child(loop, "else")
        condition = script.scalar(script.child(low_branch, "limit"), "var:xalw_level")
        self.assertEqual((condition.operator, condition.value), ("<=", "10"))
        self.assertEqual(tuple(int(child.key) for child in script.children(script.child(low_branch, "random_list"))), (45, 25, 20, 10))
        self.assertEqual(tuple(int(child.key) for child in script.children(script.child(high_branch, "random_list"))), (25, 20, 30, 25))

    def test_full_curse_replacement_cannot_reset_or_randomize_rank(self) -> None:
        script = self.effects
        curse = script.named("xalw_grow_curse_effect")
        replacement = script.child(curse, "else")
        self.assertEqual(len(script.children(script.child(replacement, "random_list"))), 2)
        changed_names = tuple(script.scalar(item, "name").value for operation in ("set_variable", "change_variable")
                              for item in script.descendants(replacement, operation))
        self.assertEqual(set(changed_names), {"xalw_curse_1", "xalw_curse_2"})
        for branch in tuple(item for item in script.children(curse) if item.key in ("if", "else_if"))[:2]:
            full_rank_branch = script.child(branch, "else")
            self.assertEqual(tuple(item for item in script.descendants(full_rank_branch, "set_variable")
                                   if script.scalar(item, "name").value.startswith("xalw_curse_rank_")), ())

    def test_owner_calendar_dispatch_has_single_month_gate(self) -> None:
        script = self.events
        pulse = script.named("xalw.1")
        immediate = script.child(pulse, "immediate")
        dispatch = tuple(branch for branch in script.children(immediate)
                         if branch.key == "if" and any(item.key == "xalw_owner_monthly_effect" for item in script.scalars(branch)))
        self.assertEqual(len(dispatch), 1)
        month_check = script.scalar(script.child(dispatch[0], "limit"), "var:xalw_last_owner_month")
        self.assertEqual((month_check.operator, month_check.value), ("!=", "xalw_current_month_value"))
        timers = script.descendants(pulse, "trigger_event")
        self.assertEqual(len(timers), 1)
        self.assertEqual(script.scalar(timers[0], "days").value, "1")
        artifact = self.effects.named("xalw_artifact_monthly_effect")
        guard = self.effects.scalar(self.effects.child(self.effects.child(artifact, "if"), "limit"), "var:xalw_last_settled_month")
        self.assertEqual((guard.operator, guard.value), ("!=", "xalw_current_month_value"))

    def test_suppression_deadline_is_numeric_and_old_timer_is_bound(self) -> None:
        script = self.effects
        begin = script.named("xalw_begin_suppression_timer_effect")
        assignment = script.variable_actions(begin, "set_variable", "xalw_growth_suppressed_until")
        self.assertEqual(len(assignment), 1)
        deadline = script.child(assignment[0], "value")
        self.assertEqual(script.scalar(deadline, "value").value, "current_date")
        self.assertEqual(script.scalar(deadline, "add").value, "90")
        renew = self.triggers.named("xalw_can_renew_suppression_trigger")
        comparison = self.triggers.scalar(renew, "var:xalw_growth_suppressed_until")
        self.assertEqual((comparison.operator, comparison.value), ("<=", "xalw_renewal_window_ends_value"))
        window = self.values.named("xalw_renewal_window_ends_value")
        self.assertEqual(self.values.scalar(window, "value").value, "current_date")
        self.assertEqual(self.values.scalar(window, "add").value, "30")
        timer = self.events.named("xalw.4")
        guard = self.events.scalar(self.events.child(timer, "trigger"), "var:xalw_suppression_timer_sequence")
        self.assertEqual(guard.value, "scope:xalw_suppression_timer_sequence")
        charge = script.named("xalw_suppress_effect")
        extensions = script.variable_actions(charge, "change_variable", "xalw_growth_suppressed_until")
        self.assertEqual(len(extensions), 1)
        self.assertEqual(script.scalar(extensions[0], "add").value, "90")

    def test_native_hunger_uses_artifact_modifiers_without_character_residue(self) -> None:
        script = Script(core.render_core_modifiers())
        for points in range(1, 6):
            modifier = script.named(f"xalw_hunger_{points}_modifier")
            self.assertEqual(Decimal(script.scalar(modifier, "health").value), Decimal(points) * Decimal("-0.1"))
        refresh = self.effects.named("xalw_refresh_artifact_effect")
        self.assertTrue(any(item.key == "add_artifact_modifier" for branch in self.effects.children(refresh)
                            for item in self.effects.scalars(branch)))
        self.assertFalse(any(item.key == "add_character_modifier" for item in self.effects.blocks))
        self.assertNotIn("add_character_modifier", self.effects.mask)

    def test_vanilla_callbacks_only_append_child_actions(self) -> None:
        script = Script(core.render_core_on_actions())
        for name in ("on_game_start_after_lobby", "random_yearly_everyone_pulse", "on_artifact_changed_owner"):
            self.assertEqual(tuple(child.key for child in script.children(script.named(name))), ("on_actions",))
        self.assertFalse(any(item.key in ("on_artifact_equipped", "on_artifact_unequipped") for item in script.blocks))

    def test_ai_review_is_queueing_not_a_feeding_eligibility_gate(self) -> None:
        script = self.effects
        review = script.named("xalw_queue_ai_review_effect")
        timer = script.descendants(review, "trigger_event")
        self.assertEqual(len(timer), 1)
        self.assertEqual(script.scalar(timer[0], "days").value, "1")
        feed = script.named("xalw_feed_material_effect")
        transaction_condition = script.child(script.child(feed, "if"), "limit")
        condition_text = script.mask[transaction_condition.opening + 1:transaction_condition.end - 1]
        self.assertNotIn("xalw_ai_review_queued", condition_text)
        self.assertNotIn("cooldown", condition_text)
        material = self.triggers.named("xalw_is_safe_feed_material_trigger")
        self.assertFalse(any(item.key in ("days", "months", "years", "current_date") for item in self.triggers.scalars(material)))
        ai_event = self.events.child(self.events.named("xalw.2"), "immediate")
        self.assertEqual(self.events.scalar(ai_event, "remove_variable").value, "xalw_ai_review_queued")

    def test_manual_management_declares_explicit_native_ai_schedule(self) -> None:
        # R2 actually logged missing frequency/interval while parsing these.
        # Automatic AI cultivation is owned by its separate real monthly path.
        interactions = Script(core.render_core_interactions())
        for key in ("xalw_manage_interaction", "xalw_feed_interaction", "xalw_keep_interaction"):
            block = interactions.named(key)
            interactions.child(block, "ai_targets")
            self.assertEqual(interactions.scalar(block, "ai_frequency").value, "0")
        decision = Script(core.render_core_decisions())
        self.assertEqual(decision.scalar(decision.named("xalw_manage_decision"), "ai_check_interval").value, "0")


if __name__ == "__main__":
    unittest.main()
