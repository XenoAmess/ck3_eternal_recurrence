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

    def test_star_name_migrates_only_living_artifacts_and_does_not_repeat(self) -> None:
        script = self.effects
        naming = script.named("xalw_ensure_star_name_effect")
        branch = script.child(naming, "if")
        condition = script.child(branch, "limit")
        self.assertEqual(script.scalar(condition, "xalw_is_living_trigger").value, "yes")
        self.assertEqual(script.scalar(script.child(condition, "NOT"), "has_variable").value, "xalw_star_named")
        self.assertEqual(script.scalar(branch, "save_scope_as").value, "xalw_named_artifact")
        self.assertEqual(script.scalar(branch, "set_artifact_name").value, "xalw_star_name")
        marker = script.variable_actions(naming, "set_variable", "xalw_star_named")
        self.assertEqual(len(marker), 1)
        self.assertGreater(marker[0].start, script.scalar(branch, "set_artifact_name").start)
        for path in ("xalw_refresh_artifact_effect", "xalw_artifact_monthly_effect"):
            self.assertEqual(script.scalar(script.named(path), "xalw_ensure_star_name_effect").value, "yes")
        for language in ("simp_chinese", "english"):
            self.assertEqual(core.render_core_localization(language)["xalw_star_name"], "★[xalw_named_artifact.GetNameNoTooltip]")

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

    def test_rarity_shortcuts_only_select_safe_food_and_leave_destruction_to_confirmation(self) -> None:
        script = self.effects
        chooser = script.named("xalw_choose_feed_rarity_effect")
        branch = script.child(chooser, "if")
        eligible = script.child(script.child(branch, "limit"), "any_character_artifact")
        chosen = script.child(branch, "ordered_character_artifact")
        selected_limit = script.child(chosen, "limit")
        for condition in (eligible, selected_limit):
            self.assertEqual(script.scalar(condition, "xalw_is_safe_feed_material_trigger").value, "yes")
            self.assertEqual(script.scalar(condition, "rarity").value, "$RARITY$")
        self.assertEqual(script.scalar(chosen, "max").value, "1")
        self.assertEqual(script.scalar(chosen, "save_scope_as").value, "xalw_material")
        text = script.mask[chooser.opening:chooser.end]
        self.assertNotIn("destroy_artifact", text)
        self.assertNotIn("change_variable", text)
        self.assertNotIn("cooldown", text)
        self.assertEqual(script.scalar(branch, "trigger_event").value, "xalw.11")
        menu = self.events.named("xalw.10")
        for rarity in ("common", "masterwork", "famed", "illustrious"):
            option = next(item for item in self.events.children(menu) if item.key == "option" and
                          self.events.scalar(item, "name").value == f"xalw.10.feed_{rarity}")
            call = self.events.child(option, "xalw_choose_feed_rarity_effect")
            self.assertEqual(self.events.scalar(call, "RARITY").value, rarity)

    def test_guidance_shortcut_requires_an_owned_equipped_living_target(self) -> None:
        script = self.events
        menu = script.named("xalw.12")
        candidate = script.child(script.child(menu, "immediate"), "ordered_character_artifact")
        limit = script.child(candidate, "limit")
        self.assertEqual(script.scalar(limit, "xalw_is_living_trigger").value, "yes")
        self.assertEqual(script.scalar(limit, "is_equipped").value, "yes")
        self.assertEqual(script.scalar(candidate, "max").value, "1")
        self.assertEqual(script.scalar(candidate, "save_scope_as").value, "xalw_artifact")
        open_option = next(item for item in script.children(menu) if item.key == "option" and
                           script.scalar(item, "name").value == "xalw.12.open")
        # The shared block scanner intentionally recognizes '=' assignments;
        # inspect this optional '?=' scope guard in its original masked text.
        trigger = script.child(open_option, "trigger")
        self.assertRegex(script.mask[trigger.opening:trigger.end],
                         r"scope:xalw_artifact\s*\?=\s*\{[^{}]*artifact_owner\s*=\s*root\b")
        self.assertEqual(script.scalar(open_option, "trigger_event").value, "xalw.10")

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
        renewal_branch = self.triggers.descendants(renew, "trigger_if")
        self.assertEqual(len(renewal_branch), 1)
        comparison = self.triggers.scalar(renewal_branch[0], "var:xalw_growth_suppressed_until")
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

    def assert_lazy_branches(
        self, script: Script, parent: Block, fields: tuple[str, ...], *, missing_allowed: bool,
    ) -> tuple[Block, ...]:
        found: list[Block] = []
        for branch in script.descendants(parent, "trigger_if"):
            guard = script.child(branch, "limit")
            presence = {item.value for item in script.scalars(guard) if item.key == "has_variable"}
            if presence != set(fields):
                continue
            enclosing = max(script.ancestors(branch), key=lambda block: block.opening)
            siblings = script.children(enclosing)
            following = siblings[siblings.index(branch) + 1]
            self.assertEqual(following.key, "trigger_else")
            self.assertEqual(script.scalar(following, "always").value, "yes" if missing_allowed else "no")
            found.append(branch)
        self.assertTrue(found, (parent.key, fields))
        return tuple(found)

    def test_optional_suppression_and_renewal_require_present_deadline(self) -> None:
        for name, operator, value in (
            ("xalw_is_growth_suppressed_trigger", ">", "current_date"),
            ("xalw_can_renew_suppression_trigger", "<=", "xalw_renewal_window_ends_value"),
        ):
            parent = self.triggers.named(name)
            branches = self.assert_lazy_branches(self.triggers, parent, ("xalw_growth_suppressed_until",), missing_allowed=False)
            self.assertEqual(len(branches), 1)
            comparison = self.triggers.scalar(branches[0], "var:xalw_growth_suppressed_until")
            self.assertEqual((comparison.operator, comparison.value), (operator, value))

    def test_optional_debt_keeper_guards_independent_fields_without_inventory(self) -> None:
        parent = self.triggers.named("xalw_owner_needs_monthly_trigger")
        alternatives = self.triggers.child(parent, "OR")
        self.assertEqual(len(tuple(item for item in self.triggers.children(alternatives) if item.key == "any_character_artifact")), 2)
        for field in ("xalw_content_loan_periods", "xalw_content_loan_arrears"):
            branches = self.assert_lazy_branches(self.triggers, parent, (field,), missing_allowed=False)
            self.assertEqual(len(branches), 1)
            comparison = self.triggers.scalar(branches[0], "var:" + field)
            self.assertEqual((comparison.operator, comparison.value), (">", "0"))

    def test_optional_appeasement_hunger_and_expiry_are_absent_no_ops(self) -> None:
        for script, parent, operator in (
            (self.values, self.values.named("xalw_actual_hunger_value"), ">"),
            (self.events, self.events.named("xalw.5"), "<="),
        ):
            branches = self.assert_lazy_branches(script, parent, ("xalw_appeased_until",), missing_allowed=False)
            self.assertEqual(len(branches), 1)
            comparison = script.scalar(branches[0], "var:xalw_appeased_until")
            self.assertEqual((comparison.operator, comparison.value), (operator, "current_date"))

    def test_first_appeasement_missing_deadline_stays_allowed_in_ui_and_effect(self) -> None:
        for script, parent in (
            (self.effects, self.effects.named("xalw_appease_effect")),
            (self.events, self.events.named("xalw.10")),
        ):
            branches = self.assert_lazy_branches(script, parent, ("xalw_appease_available_on",), missing_allowed=True)
            self.assertEqual(len(branches), 1)
            comparison = script.scalar(branches[0], "var:xalw_appease_available_on")
            self.assertEqual((comparison.operator, comparison.value), ("<=", "current_date"))

    def test_empty_upgrade_slots_cannot_read_rank_or_become_candidates(self) -> None:
        parent = self.effects.named("xalw_upgrade_affix_effect")
        for slot in range(1, 7):
            field = f"xalw_affix_rank_{slot}"
            branches = self.assert_lazy_branches(self.effects, parent, (f"xalw_affix_{slot}", field), missing_allowed=False)
            self.assertEqual(len(branches), 2)  # total eligibility and actual random-list candidate
            for branch in branches:
                comparison = self.effects.scalar(branch, "var:" + field)
                self.assertEqual((comparison.operator, comparison.value), ("<", "3"))
        fallback = self.effects.child(parent, "else")
        self.assertEqual(self.effects.scalar(fallback, "xalw_mutate_affix_effect").value, "yes")

    def test_ai_rank_score_reads_only_inside_complete_slot_effect_branches(self) -> None:
        parent = self.values.named("xalw_ai_living_adjustment_value")
        checked = 0
        for addition in self.values.descendants(parent, "add"):
            scalars = tuple(item for item in self.values.scalars(addition) if item.key == "value")
            if not scalars:
                continue
            match = re.fullmatch(r"var:(xalw_(?:affix|curse))_rank_([1-6])", scalars[0].value)
            if match is None:
                continue
            container = max((item for item in self.values.ancestors(addition) if item.key == "if"), key=lambda block: block.opening)
            guard = self.values.child(container, "limit")
            presence = {item.value for item in self.values.scalars(guard) if item.key == "has_variable"}
            stem, slot = match.groups()
            self.assertTrue({f"{stem}_{slot}", f"{stem}_rank_{slot}"}.issubset(presence))
            checked += 1
        self.assertEqual(checked, 10)

    def test_monthly_keeper_is_shared_by_bootstrap_start_and_continuation(self) -> None:
        actions = Script(core.render_core_on_actions())
        bootstrap = actions.named("xalw_bootstrap_on_action")
        holders = actions.descendants(bootstrap, "every_living_character")
        self.assertEqual(len(holders), 1)
        startup = actions.scalar(actions.child(holders[0], "limit"), "xalw_owner_needs_monthly_trigger")
        self.assertEqual(startup.value, "yes")
        discovery = self.effects.named("xalw_discover_owner_effect")
        chain_starts = tuple(branch for branch in self.effects.descendants(discovery, "if")
                             if any(item.key == "xalw_owner_needs_monthly_trigger"
                                    for item in self.effects.scalars(self.effects.child(branch, "limit"))))
        self.assertEqual(len(chain_starts), 1)
        start_guard = self.effects.scalar(self.effects.child(chain_starts[0], "limit"), "xalw_owner_needs_monthly_trigger")
        self.assertEqual(start_guard.value, "yes")
        daily = self.events.child(self.events.named("xalw.1"), "immediate")
        continuations = tuple(branch for branch in self.events.children(daily) if branch.key == "if"
                              and self.events.descendants(branch, "trigger_event"))
        self.assertEqual(len(continuations), 1)
        continuation = self.events.scalar(self.events.child(continuations[0], "limit"), "xalw_owner_needs_monthly_trigger")
        self.assertEqual(continuation.value, "yes")
        ending = self.events.child(daily, "else")
        self.assertEqual(self.events.scalar(ending, "remove_variable").value, "xalw_monthly_chain")


if __name__ == "__main__":
    unittest.main()
