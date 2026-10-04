"""Offline integration contracts for LYD content and leadership.

These checks inspect generated Clausewitz ASTs and generator ownership. They do
not emulate CK3, native scope validation, consent outcomes or title succession.
Run this file normally after importing it into mod_li_yu_dao/tools. External
review can set LYD_CONTENT_TEST_SOURCE and LYD_CONTENT_TEST_REPO to frozen inputs.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SOURCE = Path(os.environ.get("LYD_CONTENT_TEST_SOURCE", str(Path(__file__).resolve().parents[1])))
REPO = Path(os.environ.get("LYD_CONTENT_TEST_REPO", str(SOURCE.parent)))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(SOURCE / "tools"))
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from validate_static import guarded_effect, player_guard

# Public legacy behaviour, deliberately independent of the current content table.
# Values are base script amounts: gold cost, piety, prestige, stress, learning XP.
# Engine trait modifiers and rounding are outside this offline contract.
LEGACY = {
    "kongmen": ("lyd.100", ((10,35,0,5,25), (25,25,15,0,15), (40,-15,25,0,0))),
    "mengzi": ("lyd.101", ((20,40,-10,5,25), (15,25,0,0,15), (0,-20,0,5,0))),
    "xunzi": ("lyd.102", ((10,35,0,-10,35), (15,25,0,-5,20), (0,-20,0,10,0))),
    "zhengxuan": ("lyd.103", ((15,30,0,0,40), (10,20,0,0,25), (30,-20,15,0,0))),
    "wangsu": ("lyd.104", ((15,30,0,0,40), (10,20,0,0,25), (25,-20,10,0,0))),
    "jingshu": ("lyd.105", ((15,30,0,0,45), (20,25,0,-5,30), (35,-15,15,0,0))),
    "zhuxi": ("lyd.106", ((15,35,0,5,40), (10,25,0,0,25), (35,-20,20,0,0))),
    "lujiuyuan": ("lyd.107", ((0,40,-15,10,25), (15,25,0,0,30), (0,-25,25,-5,0))),
}
RESOURCE_KEYS = ("remove_short_term_gold", "add_piety", "add_prestige", "add_stress", "add_learning_lifestyle_xp")
SHARED = {"common/scripted_effects/lyd_c3_head_factory.txt", "common/scripted_effects/lyd_c3_migration_hooks.txt"}
META = {"name", "custom_tooltip", "trigger", "limit", "ai_chance", "show_as_tooltip"}


def blocks(body, key):
    return [e.value for e in body.entries if e.key == key and isinstance(e.value, Block)]


def one(body, key):
    values = blocks(body, key)
    if len(values) != 1:
        raise AssertionError(f"Expected one {key} block; got {len(values)}")
    return values[0]


def scalar(body, key):
    values = [e.value for e in body.entries if e.key == key and isinstance(e.value, str)]
    if len(values) > 1:
        raise AssertionError(f"Duplicate scalar {key}")
    return values[0].strip('"') if values else None


def walk(body, ancestors=()):
    for entry in body.entries:
        yield entry, ancestors
        if isinstance(entry.value, Block):
            yield from walk(entry.value, ancestors + (entry.key,))


def has(body, key, value=None, operator="="):
    return any(e.key == key and e.operator == operator and (value is None or e.value == value)
               for e, _ in walk(body))


def contains_direct_fragment(body, text):
    """Match policy conjuncts with their logical wrappers intact."""
    def subset(actual, expected):
        for wanted in expected.entries:
            if not any(e.key == wanted.key and e.operator == wanted.operator and
                       (subset(e.value, wanted.value) if isinstance(e.value,Block) and isinstance(wanted.value,Block)
                        else e.value == wanted.value) for e in actual.entries):
                return False
        return True
    return subset(body, parse_clausewitz(text))


class Corpus:
    def __init__(self):
        self.defs = {}
        self.paths = {}
        for directory in ("common", "events"):
            for path in sorted((SOURCE / directory).rglob("*.txt")):
                category = "events" if directory == "events" else path.parent.relative_to(SOURCE).as_posix()
                for entry in parse_clausewitz(path.read_text(encoding="utf-8-sig")).entries:
                    if not isinstance(entry.value, Block):
                        continue
                    if entry.key in self.defs:
                        raise AssertionError(f"Duplicate definition: {entry.key}")
                    self.defs[entry.key] = entry.value
                    self.paths[entry.key] = category
        self.effects = {k:v for k,v in self.defs.items() if self.paths[k] == "common/scripted_effects"}
        self.triggers = {k:v for k,v in self.defs.items() if self.paths[k] == "common/scripted_triggers"}
        self.events = {k:v for k,v in self.defs.items() if self.paths[k] == "events"}
        self.rites = {k:v for k,v in self.defs.items() if self.paths[k] == "common/religion/rite_types"}

    def operations(self, body, stack=(), ancestors=()):
        """Follow actual effect calls; skip UI metadata and condition evaluation."""
        for entry in body.entries:
            if entry.key in META:
                continue
            if entry.key in self.effects:
                if entry.key in stack:
                    raise AssertionError(f"Recursive executable effect chain: {stack + (entry.key,)}")
                yield from self.operations(self.effects[entry.key], stack + (entry.key,), ancestors)
            else:
                yield entry, ancestors
                if isinstance(entry.value, Block):
                    yield from self.operations(entry.value, stack, ancestors + (entry.key,))

    def trigger_closure(self, body, seen=frozenset()):
        result = [body]
        for entry, _ in walk(body):
            if entry.key in self.triggers and entry.key not in seen:
                result.extend(self.trigger_closure(self.triggers[entry.key], seen | {entry.key}))
        return result


class ContentLeadershipIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Corpus()

    def assert_cancel_clean(self, event_id):
        event = self.c.events[event_id]
        for phase in ("immediate", "after"):
            self.assertFalse(blocks(event, phase), f"{event_id}: opening/closing the menu writes state")
        cancels = [o for o in blocks(event, "option") if scalar(o, "name") == "lyd_cancel"]
        self.assertEqual(len(cancels), 1, f"{event_id}: missing/ambiguous safe cancel")
        self.assertEqual(list(self.c.operations(cancels[0])), [], f"{event_id}: cancel executes state changes")

    def test_catalogue_is_reachable_through_state_free_chooser_pages(self):
        # Verify a usable connected UI graph, not only the number of definitions.
        first = "lyd.10"
        catalogue = importlib.import_module("content_data")
        self.assertEqual(set(self.c.rites), {r.script_id for r in catalogue.RITES}, "Authored catalogue lost a generated rite")
        self.assertEqual({r.code for r in catalogue.RITES}, {f"R{i:02}" for i in range(1,37)}, "Free-chronology catalogue is incomplete")
        todo, visited, selections, links = [first], set(), {}, {}
        while todo:
            event_id = todo.pop()
            if event_id in visited:
                continue
            visited.add(event_id)
            event = self.c.events[event_id]
            self.assertEqual(scalar(event, "title"), "lyd_choose_school_t")
            self.assertTrue(player_guard(one(event, "trigger"), self.c.triggers), event_id)
            self.assert_cancel_clean(event_id)
            links[event_id] = set()
            for option in blocks(event, "option"):
                name = scalar(option, "name")
                if name in {"lyd_cancel"}:
                    continue
                if name in {"lyd_choose_school_next_page", "lyd_choose_school_previous_page"}:
                    ops = list(self.c.operations(option))
                    self.assertTrue(ops, f"{event_id}: empty navigation")
                    self.assertTrue(all(e.key in {"if", "trigger_event"} for e,_ in ops), f"{event_id}: navigation writes state")
                    self.assertTrue(player_guard(one(one(option, "if"), "limit"), self.c.triggers))
                    targets = [e.value for e,_ in ops if e.key == "trigger_event"]
                    self.assertEqual(len(targets), 1)
                    target = targets[0]
                    self.assertIn(target, self.c.events)
                    links[event_id].add(target)
                    todo.append(target)
                    continue
                calls = [e.key for e in option.entries if e.key in self.c.effects]
                self.assertEqual(len(calls), 1, f"{event_id}/{name}: ambiguous selection")
                targets = [e.value for e,_ in self.c.operations(option) if e.key == "set_character_rite"]
                self.assertEqual(len(targets), 1, f"{event_id}/{name}: selection must change one personal rite")
                target = targets[0].removeprefix("rite:")
                self.assertNotIn(target, selections, f"Unreachable/duplicate menu choice for {target}")
                self.assertIn(target, self.c.rites)
                self.assertTrue(contains_direct_fragment(one(option,"trigger"), f"NOT = {{ rite = rite:{target} }}"))
                selections[target] = calls[0]
        chooser_events = {k for k,v in self.c.events.items() if scalar(v, "title") == "lyd_choose_school_t"}
        self.assertEqual(visited, chooser_events, "A chooser page is orphaned")
        self.assertEqual(set(selections), set(self.c.rites), "A defined tradition cannot be personally selected")
        for page, targets in links.items():
            for target in targets:
                self.assertIn(page, links[target], f"Navigation cannot return from {target} to {page}")
        self.assertEqual({e.key for e in blocks(self.c.events[first], "option")[0].entries if e.key.endswith("_effect")},
                         {"lyd_adopt_kongmen_effect"})
        self.assertEqual({scalar(o, "name") for o in blocks(self.c.events[first], "option") if scalar(o, "name").startswith("lyd_adopt_")},
                         {f"lyd_adopt_{slug}" for slug in LEGACY}, "Legacy choices disappeared from their stable entry page")

    def test_every_selected_rite_dispatches_to_its_own_affordable_guarded_practice(self):
        dispatch = self.c.effects["lyd_open_study_effect"]
        outer = one(dispatch, "if")
        self.assertTrue(player_guard(one(outer, "limit"), self.c.triggers))
        routes = {}
        for branch in blocks(outer, "if"):
            rite = scalar(one(branch, "limit"), "rite").removeprefix("rite:")
            event_id = scalar(branch, "trigger_event")
            self.assertNotIn(rite, routes)
            routes[rite] = event_id
        self.assertEqual(set(routes), set(self.c.rites), "Selected tradition has no practice dispatch")
        self.assertEqual(len(set(routes.values())), len(routes), "Two traditions share the wrong practice event")
        for rite, event_id in routes.items():
            event = self.c.events[event_id]
            self.assertTrue(has(one(event, "trigger"), "rite", f"rite:{rite}"))
            self.assertTrue(player_guard(one(event, "trigger"), self.c.triggers))
            self.assert_cancel_clean(event_id)
            for option in blocks(event, "option"):
                if scalar(option, "name") == "lyd_cancel":
                    continue
                calls = [e.key for e in option.entries if e.key in self.c.effects]
                self.assertEqual(len(calls), 1)
                effect = self.c.effects[calls[0]]
                self.assertTrue(guarded_effect(effect, self.c.triggers, self.c.effects), calls[0])
                body = one(effect, "if")
                gate = one(body, "limit")
                self.assertTrue(has(gate, "rite", f"rite:{rite}"), f"{event_id} applies to another tradition")
                costs = [int(e.value) for e,_ in self.c.operations(effect) if e.key == "remove_short_term_gold"]
                cost = sum(costs)
                self.assertTrue(has(gate, "gold", str(cost), ">="), f"{calls[0]} can execute without its cost")
                self.assertTrue(has(one(option, "trigger"), "gold", str(cost), ">="), f"{event_id} offers unaffordable option")
                flags = [e.value for e,_ in self.c.operations(effect) if e.key == "add_character_flag"]
                self.assertEqual([(scalar(f,"flag"),scalar(f,"days")) for f in flags], [("lyd_study_cooldown","180")])
                self.assertFalse(any(e.key in {"set_character_rite", "set_parent_faith", "detach_rite_to_new_faith", "set_religious_head_title"}
                                     or e.key.startswith("every_") for e,_ in self.c.operations(effect)), calls[0])

    def test_legacy_event_ids_and_base_practice_rewards_are_preserved(self):
        for slug, (event_id, outcomes) in LEGACY.items():
            with self.subTest(tradition=slug):
                event = self.c.events[event_id]
                self.assertEqual(scalar(event, "title"), f"lyd_practice_{slug}_t")
                self.assertTrue(has(one(event, "trigger"), "rite", f"rite:lyd_rite_{slug}"))
                for option_key, expected in zip("abc", outcomes):
                    name = f"lyd_practice_{slug}_{option_key}"
                    option = next(o for o in blocks(event, "option") if scalar(o,"name") == name)
                    self.assertTrue(has(option, name + "_effect", "yes"))
                    ops = list(self.c.operations(option))
                    actual = tuple(sum(int(e.value) for e,_ in ops if e.key == key) for key in RESOURCE_KEYS)
                    self.assertEqual(actual, expected, f"Legacy practice changed: {name}")

    def test_personal_adoption_never_migrates_a_shared_rite_or_faith(self):
        for rite in self.c.rites:
            slug = rite.removeprefix("lyd_rite_")
            effect = self.c.effects[f"lyd_adopt_{slug}_effect"]
            self.assertTrue(guarded_effect(effect, self.c.triggers, self.c.effects), slug)
            ops = list(self.c.operations(effect))
            allowed = {"if", "else", "set_character_rite", "add_character_flag", "flag", "days", "debug_log", "trigger_event"}
            self.assertFalse([(e.key, ancestors) for e,ancestors in ops if e.key not in allowed], f"{slug}: personal adoption reaches global mutation")
            setters = [(e.value,ancestors) for e,ancestors in ops if e.key == "set_character_rite"]
            self.assertEqual(setters, [(f"rite:{rite}", ("if",))], f"{slug}: affects another scope")
            self.assertTrue(contains_direct_fragment(one(one(effect,"if"),"limit"), f"NOT = {{ rite = rite:{rite} }}"))
            post = one(one(one(effect,"if"),"if"),"limit")
            self.assertTrue(has(post,"rite",f"rite:{rite}"))
            self.assertTrue(has(post,"faith",f"rite:{rite}.faith"))
            flags = [e.value for e,_ in ops if e.key == "add_character_flag"]
            self.assertEqual([(scalar(f,"flag"),scalar(f,"days")) for f in flags], [("lyd_school_cooldown","365")])

    def test_shared_factory_has_one_formal_generator_owner(self):
        consent = importlib.import_module("gen_school_consent")
        leadership = importlib.import_module("gen_leadership")
        runtime = importlib.import_module("gen_runtime")
        # Admission is unrelated to ownership; use a closed, deterministic input.
        with patch.object(consent, "native_admission", return_value={"admitted":False,"status":"CLOSED","receipt":None}):
            c2 = consent.build_outputs(include_shared=False)
            c3 = leadership.build_outputs()
            integrated = runtime.build_outputs()
            self.assertFalse(set(c2) & SHARED)
            self.assertEqual(set(c3) & SHARED, SHARED)
            self.assertFalse(set(c2) & set(c3), "Two components render the same formal path")
            for path in SHARED:
                self.assertEqual(integrated[path], c3[path], f"Formal C3 owner shadowed: {path}")
                self.assertEqual((SOURCE/path).read_bytes(), c3[path], f"Generated shared component is stale: {path}")
            # Preserve explicit legacy API tests, but reject legacy output into the formal root.
            with self.assertRaises(ValueError, msg="Standalone C2 rendering may overwrite formal C3 ownership"):
                consent.generate(SOURCE, include_shared=True, check=True)

    def test_native_challenger_is_closed_and_personal_teaching_does_not_fake_hor(self):
        gate = self.c.triggers["lyd_c3_native_challenger_admitted_trigger"]
        self.assertEqual([(e.key,e.operator,e.value) for e in gate.entries], [("always","=","no")])
        registration = self.c.effects["lyd_c3_declare_claim_effect"]
        outer = one(registration, "if")
        native = one(outer, "if")
        self.assertTrue(has(one(native,"limit"), "lyd_c3_native_challenger_admitted_trigger", "yes"))
        self.assertTrue(has(one(native,"limit"), "lyd_c3_native_challenger_eligible_trigger", "yes"))
        outside = Block(tuple(e for e in outer.entries if e.key != "if"))
        self.assertFalse(any(e.key in {"create_dynamic_title","sponsor_new_religious_head_challenger","set_religious_head_title"}
                             for e,_ in self.c.operations(outside)))
        for effect, body in self.c.effects.items():
            self.assertFalse(any(e.key in {"set_head_of_rite","set_rite_head","set_head_of_rite_title","set_religious_head"}
                                 for e,_ in self.c.operations(body)), f"Invented native setter in {effect}")
        teacher = list(self.c.operations(self.c.effects["lyd_c3_accept_teacher_effect"]))
        self.assertFalse(any(e.key in {"set_religious_head_title","change_title_holder","create_dynamic_title"} for e,_ in teacher))

    def test_migration_cleanup_runs_before_the_native_setter(self):
        for name, native in (("lyd_c2_commit_join_effect","set_parent_faith"),
                             ("lyd_c2_commit_detach_effect","detach_rite_to_new_faith")):
            ordered = [e.key for e,_ in self.c.operations(self.c.effects[name])]
            # Shared pre-hook now also clears separately owned claim offices.
            self.assertIn("destroy_title", ordered, f"{name}: claim-office cleanup is absent from the migration chain")
            self.assertLess(ordered.index("remove_religious_head_challenger"), ordered.index(native), name)
            self.assertLess(ordered.index("destroy_title"), ordered.index(native), name)
            calls = [e.key for e,_ in walk(self.c.effects[name])]
            self.assertLess(calls.index("lyd_c3_before_rite_migration_effect"),calls.index("lyd_c3_cleanup_rite_claim_offices_effect"),name)
            self.assertLess(calls.index("lyd_c3_cleanup_rite_claim_offices_effect"),calls.index(native),name)

    def test_owned_title_retirement_never_selects_other_held_titles(self):
        retirement = self.c.effects["lyd_c2_retire_source_head_effect"]
        self.assertTrue(has(one(one(retirement,"if"),"limit"),"lyd_c2_source_retirement_trigger"))
        rules = self.c.triggers["lyd_c2_source_retirement_trigger"]
        self.assertTrue(has(rules,"var:lyd_c2_source_faith.religious_head_title","var:lyd_c2_source_head_title"))
        owned = one(rules,"var:lyd_c2_source_head_title")
        self.assertTrue(has(owned,"has_variable","lyd_c2_owned_head_title") or has(owned,"var:lyd_c2_owned_head_title","1"))
        self.assertTrue(has(owned,"var:lyd_c2_owner_faith","$ACTOR$.var:lyd_c2_source_faith"))
        self.assertTrue(has(owned,"holder","$ACTOR$.var:lyd_c2_source_head"))
        withdrawal = self.c.effects["lyd_c3_withdraw_claim_effect"]
        title = one(withdrawal,"var:lyd_c3_claim_title")
        guard = one(one(title,"if"),"limit")
        self.assertTrue(has(guard,"var:lyd_c3_owned_claim_title","1"))
        self.assertTrue(has(guard,"holder","scope:lyd_c3_withdrawing_claimant","?="))
        self.assertTrue(contains_direct_fragment(guard,
            "trigger_if = { limit = { exists = scope:lyd_c3_withdrawing_claimant.faith.religious_head_title } NOT = { this = scope:lyd_c3_withdrawing_claimant.faith.religious_head_title } }"))
        self.assertTrue(contains_direct_fragment(guard,
            "trigger_if = { limit = { exists = var:lyd_c3_owner_faith.religious_head_title } NOT = { this = var:lyd_c3_owner_faith.religious_head_title } }"))
        for name, expected in (("lyd_c2_retire_source_head_effect","var:lyd_c2_source_head_title"),
                               ("lyd_c3_withdraw_claim_effect","scope:lyd_c3_withdrawing_office"),
                               ("lyd_c3_abdicate_owned_head_effect","scope:lyd_c3_abdicating_title")):
            ops = list(self.c.operations(self.c.effects[name]))
            self.assertEqual([e.value for e,_ in ops if e.key == "destroy_title"], [expected], name)
            self.assertFalse(any(e.key == "every_held_title" for e,_ in ops), f"{name}: destruction sweeps other held titles")
        abdication = one(one(self.c.effects["lyd_c3_abdicate_owned_head_effect"],"if"),"limit")
        self.assertTrue(has(abdication,"lyd_c3_owned_current_head_trigger","yes"))
        current_owned = self.c.triggers["lyd_c3_owned_current_head_trigger"]
        self.assertTrue(has(current_owned,"var:lyd_c2_owned_head_title","1"))
        self.assertTrue(has(current_owned,"var:lyd_c2_owner_faith","prev"))
        recognition = list(self.c.operations(self.c.effects["lyd_c3_recognize_effect"]))
        transfers = [(e,ancestors) for e,ancestors in recognition if e.key == "change_title_holder"]
        self.assertTrue(transfers)
        for _, scopes in transfers:
            self.assertTrue("faith.religious_head_title" in scopes or "scope:new_title" in scopes,
                            "Recognition transfers unrelated titles")
        self.assertTrue(has(self.c.effects["lyd_c3_recognize_effect"],"variable","lyd_c3_protected_titles"))

    def test_player_initiation_and_recipient_consent_are_separate(self):
        for identifier, body in self.c.defs.items():
            category = self.c.paths[identifier]
            if category == "common/decisions":
                self.assertTrue(player_guard(one(body,"is_shown"),self.c.triggers), identifier)
                self.assertTrue(guarded_effect(one(body,"effect"),self.c.triggers,self.c.effects), identifier)
                self.assertEqual(scalar(body,"ai_check_interval"),"0")
            if category == "common/character_interactions":
                shown_actor = one(one(body,"is_shown"),"scope:actor")
                self.assertTrue(player_guard(shown_actor,self.c.triggers), identifier)
                self.assertEqual(scalar(one(body,"ai_will_do"),"base"),"0",identifier)
                if identifier.startswith("lyd_c3_"):
                    self.assertEqual(scalar(body,"ai_maybe"),"no",identifier)
                if blocks(body,"on_auto_accept"):
                    # C2 automatic delivery only opens a round; it cannot enact affiliation.
                    delivered = list(self.c.operations(one(body,"on_auto_accept")))
                    self.assertFalse(any(e.key in {"set_parent_faith","detach_rite_to_new_faith","set_religious_head_title","destroy_title"}
                                         for e,_ in delivered),identifier)
        contracts = (
            ("lyd_c3_request_teacher_interaction", "lyd_c3_accept_teacher_effect", "lyd_c3_teacher_requested", "lyd_c3_personal_teacher"),
            ("lyd_c3_nominate_claim_interaction", "lyd_c3_nomination_accepted_effect", "lyd_c3_nominated_claimant", "lyd_c3_claim_faith"),
            ("lyd_c3_request_withdraw_interaction", "lyd_c3_nominated_withdrawal_accepted_effect", "lyd_c3_claim_sponsor", None),
        )
        for interaction, callback, pending, committed in contracts:
            body = self.c.defs[interaction]
            self.assertTrue(has(one(body,"on_accept"),callback,"yes"),interaction)
            callback_limit = one(one(self.c.effects[callback],"if"),"limit")
            actor = one(callback_limit,"scope:actor")
            self.assertTrue(player_guard(actor,self.c.triggers),callback)
            self.assertTrue(has(callback_limit,f"var:{pending}"), f"{callback}: stale/unrelated recipient can accept")
            self.assertTrue(blocks(callback_limit,"scope:recipient"), callback)
            preaccept = blocks(body,"on_send") + blocks(body,"on_decline")
            for phase in preaccept:
                ops = list(self.c.operations(phase))
                if committed:
                    self.assertFalse(any(e.key == "set_variable" and scalar(e.value,"name") == committed for e,_ in ops),
                                     f"{interaction}: consent applied before acceptance")
                self.assertFalse(any(e.key in {"destroy_title","set_religious_head_title","set_character_rite","set_parent_faith"} for e,_ in ops))

    def test_c3_trigger_bindings_preserve_player_gate_and_follower_identity(self):
        # Regressions observed by CK3 1.20.0.3 at R0005 cold load: hidden_trigger
        # is not a trigger, and a global prev link cannot follow another prev.
        for name, body in self.c.triggers.items():
            if name.startswith("lyd_c3_"):
                self.assertFalse(any(e.key == "hidden_trigger" for e,_ in walk(body)), name)
                self.assertFalse(any("prev.prev" in e.key or isinstance(e.value,str) and "prev.prev" in e.value
                                     for e,_ in walk(body)), name)
        actor = self.c.triggers["lyd_c3_player_actor_trigger"]
        self.assertTrue(contains_direct_fragment(actor,
            "is_ai = no is_alive = yes is_adult = yes is_landed = yes NOT = { has_trait = incapable } religion = religion:confucianism_religion has_character_flag = lyd_enabled lyd_member_rite_trigger = yes"))
        current = self.c.triggers["lyd_c3_round_current_trigger"]
        self.assertTrue(contains_direct_fragment(current,
            "$ACTOR$ = { save_temporary_scope_as = lyd_c3_checked_actor } scope:lyd_c3_checked_actor.var:lyd_c3_round_faith = { save_temporary_scope_as = lyd_c3_checked_faith }"))
        rite_lists = [e.value for e,_ in walk(current) if e.key == "any_in_list" and
                      isinstance(e.value,Block) and scalar(e.value,"variable") == "lyd_c3_rites"]
        self.assertEqual(len(rite_lists),1)
        self.assertEqual(scalar(rite_lists[0],"save_temporary_scope_as"),"lyd_c3_checked_rite")
        rite_conditions = one(rite_lists[0],"NOT")
        branches = blocks(one(rite_conditions,"OR"),"AND")
        empty = next(b for b in branches if has(b,"var:lyd_c3_delegate_required","0"))
        self.assertTrue(contains_direct_fragment(empty,
            "var:lyd_c3_delegate_required = 0 rite_counties = 0 scope:lyd_c3_checked_faith = { NOT = { any_faith_character = { is_alive = yes rite = scope:lyd_c3_checked_rite } } }"),
            "An empty-school exemption must test the captured rite in the captured round faith")
        delegated = next(b for b in branches if has(b,"var:lyd_c3_delegate_required","1"))
        self.assertTrue(contains_direct_fragment(delegated,
            "exists = head_of_rite head_of_rite = var:lyd_c3_delegate var:lyd_c3_delegate = { is_alive = yes is_adult = yes rite = scope:lyd_c3_checked_rite NOT = { has_trait = incapable } }"))
        represented = self.c.triggers["lyd_c3_rite_represented_trigger"]
        self.assertTrue(contains_direct_fragment(represented,
            "save_temporary_scope_as = lyd_c3_represented_rite faith = { save_temporary_scope_as = lyd_c3_represented_faith }"))
        branches = blocks(one(represented,"OR"),"AND")
        empty = next(b for b in branches if has(b,"rite_counties","0"))
        self.assertTrue(contains_direct_fragment(empty,
            "rite_counties = 0 scope:lyd_c3_represented_faith = { NOT = { any_faith_character = { is_alive = yes rite = scope:lyd_c3_represented_rite } } }"),
            "A candidate rite with living followers cannot be silently treated as empty")
        delegated = next(b for b in branches if has(b,"exists","head_of_rite"))
        self.assertTrue(contains_direct_fragment(delegated,
            "exists = head_of_rite head_of_rite = { is_alive = yes is_adult = yes rite = scope:lyd_c3_represented_rite NOT = { has_trait = incapable } }"))

    def test_council_callback_revalidates_serial_and_all_affected_players(self):
        context = self.c.triggers["lyd_c3_response_context_trigger"]
        actor_context = one(context,"scope:lyd_c3_actor")
        self.assertTrue(has(actor_context,"var:lyd_c3_serial","scope:lyd_c3_event_serial"))
        self.assertTrue(has(actor_context,"lyd_c3_round_current_trigger"))
        self.assertTrue(player_guard(self.c.triggers["lyd_c3_round_current_trigger"],self.c.triggers))
        for callback, gate in (("lyd_c3_delegate_yes_effect","lyd_c3_delegate_context_trigger"),
                               ("lyd_c3_player_yes_effect","lyd_c3_player_ballot_context_trigger"),
                               ("lyd_c3_incumbent_yes_effect","lyd_c3_response_context_trigger")):
            self.assertTrue(has(one(one(self.c.effects[callback],"if"),"limit"),gate,"yes"),callback)
        player_context = self.c.triggers["lyd_c3_player_ballot_context_trigger"]
        self.assertTrue(has(player_context,"var:lyd_c3_affected_owner","scope:lyd_c3_actor"))
        self.assertTrue(has(player_context,"var:lyd_c3_affected_serial","scope:lyd_c3_event_serial"))
        can = self.c.triggers["lyd_c3_can_recognize_trigger"]
        self.assertTrue(has(can,"lyd_c3_round_current_trigger"))
        self.assertTrue(has(can,"var:lyd_c3_head_yes","1"))
        self.assertTrue(contains_direct_fragment(can,
            "NOT = { any_in_list = { variable = lyd_c3_players NOT = { var:lyd_c3_player_yes = 1 } } }"))
        self.assertTrue(contains_direct_fragment(can,
            "NOT = { any_in_list = { variable = lyd_c3_rites var:lyd_c3_delegate_required = 1 NOT = { var:lyd_c3_delegate_yes = 1 } } }"))
        executable_gate = one(one(self.c.effects["lyd_c3_recognize_effect"],"if"),"limit")
        self.assertTrue(has(executable_gate,"lyd_c3_response_context_trigger","yes"))
        self.assertTrue(has(executable_gate,"lyd_c3_can_recognize_trigger"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
