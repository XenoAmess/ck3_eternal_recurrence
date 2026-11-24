"""Actual generated-AST software contracts, not engine/Save/bootstrap proof.

The tiny interpreter is explicit DATA. Its create callback may fail; it does not
claim that CK3 changes only the modeled fields. Runtime invariants need real reads.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / 'tools')]
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from content_data import ACTIVE_RITES
import gen_saved_rite_bootstrap as producer
import build_release


def one(body, key):
    found = [e.value for e in body.entries if e.key == key and isinstance(e.value, Block)]
    if len(found) != 1:
        raise AssertionError((key, len(found)))
    return found[0]


def scalar(body, key):
    found = [e.value for e in body.entries if e.key == key]
    if len(found) != 1 or not isinstance(found[0], str):
        raise AssertionError((key, found))
    return found[0]


def walk(body):
    for e in body.entries:
        yield e
        if isinstance(e.value, Block):
            yield from walk(e.value)


def ast_definition(text):
    return one(parse_clausewitz('software_fixture = {\n' + text + '\n}'), 'software_fixture')


@dataclass
class DataState:
    faith: str = 'confucian_faith'
    current_rite: str = 'jingxue'
    human: bool = True
    alive: bool = True
    main_rite_exists: bool = True
    checked: bool = False
    rites: dict[str, str] = field(default_factory=dict)
    create_failures: set[str] = field(default_factory=set)
    creates: list[str] = field(default_factory=list)


class MissingReference(AssertionError):
    pass


def predicate(body, data, faith_scope=False, *, any_mode=False):
    """AND/OR evaluate every child. Only trigger_if controls dereference."""
    values = []
    entries = list(body.entries)
    i = 0
    while i < len(entries):
        e = entries[i]
        k, v = e.key, e.value
        if k == 'trigger_if':
            assert isinstance(v, Block)
            matched = predicate(one(v, 'limit'), data, faith_scope)
            rest = Block(tuple(x for x in v.entries if x.key != 'limit'))
            if matched:
                result = predicate(rest, data, faith_scope)
            elif i + 1 < len(entries) and entries[i + 1].key == 'trigger_else':
                result = predicate(entries[i + 1].value, data, faith_scope)
            else:
                result = True
            if i + 1 < len(entries) and entries[i + 1].key == 'trigger_else':
                i += 1
            values.append(result)
        elif k in {'AND', 'OR', 'NOT'}:
            # Keep trigger_if/trigger_else siblings together inside the logical
            # container. All ordinary siblings still evaluate eagerly.
            result = predicate(v, data, faith_scope, any_mode=k == 'OR')
            values.append(not result if k == 'NOT' else result)
        elif k == 'faith' and isinstance(v, Block):
            values.append(predicate(v, data, True))
        elif k == 'exists':
            values.append(data.main_rite_exists if faith_scope and v == 'main_rite' else v.removeprefix('rite:') in data.rites)
        elif k == 'faith':
            if v.startswith('rite:'):
                key = v.removeprefix('rite:').removesuffix('.faith')
                if key not in data.rites:
                    raise MissingReference(key)
                values.append(data.faith == data.rites[key])
            else:
                values.append(data.faith == v.removeprefix('faith:'))
        elif k == 'rite':
            key = v.removeprefix('rite:')
            if key not in data.rites:
                raise MissingReference(key)
            values.append(data.current_rite == key)
        elif k == 'has_global_variable':
            assert v == producer.CHECKED
            values.append(data.checked)
        elif k == 'is_ai':
            values.append((not data.human) == (v == 'yes'))
        elif k == 'is_alive':
            values.append(data.alive == (v == 'yes'))
        elif k == 'lyd_catalogue_instances_ready_trigger':
            assert v == 'yes'
            values.append(predicate(ast_definition(producer.catalogue_ready_gate()), data))
        elif k == 'always':
            values.append(v == 'yes')
        else:
            raise AssertionError(('unsupported actual AST predicate', k))
        i += 1
    return any(values) if any_mode else all(values)


def execute(body, data):
    for e in body.entries:
        if e.key == 'limit':
            continue
        if e.key == 'if':
            if predicate(one(e.value, 'limit'), data):
                execute(e.value, data)
        elif e.key == 'create_rite_from_type':
            key = scalar(e.value, 'type')
            assert scalar(e.value, 'convert') == 'no'
            data.creates.append(key)
            if key not in data.create_failures:
                data.rites[key] = data.faith
        elif e.key == 'set_global_variable':
            assert scalar(e.value, 'name') == producer.CHECKED
            assert scalar(e.value, 'value') == 'yes'
            data.checked = True
        else:
            raise AssertionError(('unsupported actual AST effect', e.key))


class SavedRiteBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = producer.build_outputs()
        cls.effect = one(parse_clausewitz(cls.outputs['common/scripted_effects/lyd_saved_rite_bootstrap_effects.txt'].decode('utf-8-sig')), 'lyd_materialize_missing_catalogue_rites_effect')
        cls.ids = [r.script_id for r in ACTIVE_RITES]

    def test_all_36_literal_types_have_individual_missing_guard_and_no_conversion(self):
        outer = one(self.effect, 'if')
        creates = [x.value for x in outer.entries if x.key == 'if' and any(y.key == 'create_rite_from_type' for y in x.value.entries)]
        self.assertEqual(len(creates), 36)
        for branch, key in zip(creates, self.ids):
            self.assertEqual(scalar(one(one(branch, 'limit'), 'NOT'), 'exists'), 'rite:' + key)
            call = one(branch, 'create_rite_from_type')
            self.assertEqual({e.key for e in call.entries}, {'type', 'convert'})
            self.assertEqual(scalar(call, 'type'), key)
            self.assertEqual(scalar(call, 'convert'), 'no')

    def test_actual_character_faith_human_alive_and_existing_main_rite_are_required(self):
        for changes in ({'faith': 'catholic'}, {'human': False}, {'alive': False}, {'main_rite_exists': False}):
            d = DataState(**changes)
            execute(self.effect, d)
            self.assertEqual(d.creates, [])
            self.assertFalse(d.checked)

    def test_all_missing_software_callback_can_create_and_then_set_checked(self):
        d = DataState()
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids)
        self.assertTrue(d.checked)
        self.assertEqual(d.current_rite, 'jingxue')
        self.assertEqual(d.faith, 'confucian_faith')

    def test_partial_existing_objects_are_preserved_and_only_missing_types_are_requested(self):
        existing = {self.ids[0]: 'confucian_faith', self.ids[17]: 'confucian_faith'}
        d = DataState(rites=dict(existing))
        execute(self.effect, d)
        self.assertEqual(d.creates, [x for x in self.ids if x not in existing])
        self.assertEqual({k: d.rites[k] for k in existing}, existing)

    def test_second_invocation_is_idempotent_and_does_not_repeat_creation(self):
        d = DataState()
        execute(self.effect, d)
        before = (dict(d.rites), list(d.creates))
        execute(self.effect, d)
        self.assertEqual((d.rites, d.creates), before)

    def test_explicit_create_failure_does_not_set_completion_or_fake_ready(self):
        d = DataState(create_failures={self.ids[4]})
        execute(self.effect, d)
        self.assertNotIn(self.ids[4], d.rites)
        self.assertFalse(d.checked)
        self.assertFalse(predicate(ast_definition(producer.catalogue_ready_gate()), d))

    def test_existing_foreign_parent_is_never_reparented_and_completion_stays_false(self):
        d = DataState(rites={self.ids[9]: 'player_custom_faith'})
        execute(self.effect, d)
        self.assertNotIn(self.ids[9], d.creates)
        self.assertEqual(d.rites[self.ids[9]], 'player_custom_faith')
        self.assertFalse(d.checked)

    def test_catalogue_missing_objects_are_false_without_eager_missing_reference(self):
        gate = ast_definition(producer.catalogue_gate())
        self.assertFalse(predicate(gate, DataState()))
        d = DataState(current_rite=self.ids[3], rites={self.ids[3]: 'confucian_faith'})
        self.assertTrue(predicate(gate, d))
        d.current_rite = 'jingxue'
        self.assertFalse(predicate(gate, d))

    def test_unsafe_membership_mutant_really_fails_the_missing_reference_oracle(self):
        mutant = ast_definition('OR = { rite = rite:' + self.ids[0] + ' }')
        with self.assertRaises(MissingReference):
            predicate(mutant, DataState())

    def test_only_four_new_runtime_paths_and_guarded_existing_gui_mechanism(self):
        self.assertEqual(set(self.outputs), producer.NEW_RUNTIME_PATHS)
        self.assertTrue(producer.NEW_RUNTIME_PATHS <= build_release.REQUIRED_RUNTIME_FILES)
        gui = self.outputs['gui/lyd_saved_rite_bootstrap.gui'].decode('utf-8-sig')
        self.assertIn('GetPlayer.MakeScope', gui)
        self.assertIn('alwaystransparent = yes', gui)
        sgui = one(parse_clausewitz(self.outputs['common/scripted_guis/lyd_saved_rite_bootstrap.txt'].decode('utf-8-sig')), 'lyd_saved_rite_bootstrap_gui')
        shown = one(sgui, 'is_shown')
        self.assertEqual([e.value for e in shown.entries if e.key == 'faith' and isinstance(e.value, str)], ['faith:confucian_faith'])
        self.assertEqual(scalar(one(shown, 'faith'), 'exists'), 'main_rite')
        self.assertEqual(scalar(one(shown, 'NOT'), 'has_global_variable'), producer.CHECKED)
        forbidden = {'set_character_rite', 'set_character_faith', 'set_character_faith_with_conversion', 'set_parent_faith', 'set_main_rite', 'set_religious_head_title', 'force_refresh_head_of_rite', 'every_faith_character', 'every_living_character', 'trigger_event', 'add_gold', 'add_piety', 'set_personal_tenet', 'add_known_tenet'}
        self.assertFalse({e.key for e in walk(self.effect)} & forbidden)


if __name__ == '__main__':
    unittest.main()
