"""Generated-AST software contracts only; callbacks are explicit fallible DATA.

Creation deliberately defaults to switching the caller's Rite as a1528 did.
Restoration, output identity and original Faith/main can fail independently.
No model outcome proves native callbacks, head/NPC/domain conservation or Save.
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
    main_rite: str = 'daoxue'
    human: bool = True
    alive: bool = True
    main_rite_exists: bool = True
    source_rite_exists: bool = True
    source_rite_faith: str = 'confucian_faith'
    checked: bool = False
    rites: dict[str, str] = field(default_factory=dict)
    saved: dict[str, tuple[str, str]] = field(default_factory=dict)
    parents: dict[str, str] = field(default_factory=dict)
    create_failures: set[str] = field(default_factory=set)
    creates: list[str] = field(default_factory=list)
    restores: list[str] = field(default_factory=list)
    switch_on_create: bool = True
    restore_fails: bool = False
    wrong_output: bool = False
    create_changes_faith: bool = False
    create_changes_main: bool = False


class MissingReference(AssertionError):
    pass


def saved_ref(data, text):
    name, dot, attr = text.removeprefix('scope:').partition('.')
    if name not in data.saved:
        raise MissingReference(text)
    ref = data.saved[name]
    if dot:
        if attr != 'faith' or ref[0] != 'rite':
            raise AssertionError(text)
        parent = data.rites.get(ref[1], data.parents.get(ref[1]))
        if parent is None:
            raise MissingReference(text)
        return ('faith', parent)
    return ref


def predicate(body, data, faith_scope=False, *, any_mode=False, scope_this=None):
    """All ordinary AND/OR siblings evaluate eagerly; trigger_if is conditional."""
    values = []
    entries = list(body.entries)
    i = 0
    while i < len(entries):
        e = entries[i]
        k, v = e.key, e.value
        if k == 'trigger_if':
            matched = predicate(one(v, 'limit'), data, faith_scope, scope_this=scope_this)
            if matched:
                rest = Block(tuple(x for x in v.entries if x.key != 'limit'))
                result = predicate(rest, data, faith_scope, scope_this=scope_this)
            elif i + 1 < len(entries) and entries[i + 1].key == 'trigger_else':
                result = predicate(entries[i + 1].value, data, faith_scope, scope_this=scope_this)
            else:
                result = True
            if i + 1 < len(entries) and entries[i + 1].key == 'trigger_else':
                i += 1
            values.append(result)
        elif k in {'AND', 'OR', 'NOT'}:
            result = predicate(v, data, faith_scope, any_mode=k == 'OR', scope_this=scope_this)
            values.append(not result if k == 'NOT' else result)
        elif k == 'faith' and isinstance(v, Block):
            values.append(predicate(v, data, True, scope_this=('faith', data.faith)))
        elif k == 'main_rite' and isinstance(v, Block):
            values.append(predicate(v, data, scope_this=('rite', data.main_rite)))
        elif k.startswith('scope:') and isinstance(v, Block):
            values.append(predicate(v, data, scope_this=saved_ref(data, k)))
        elif k == 'exists':
            if v.startswith('scope:'):
                values.append(v.removeprefix('scope:') in data.saved)
            elif v in {'faith.main_rite', 'main_rite'}:
                values.append(data.main_rite_exists)
            elif v == 'rite':
                values.append(data.source_rite_exists)
            else:
                values.append(v.removeprefix('rite:') in data.rites)
        elif k == 'faith':
            if v.startswith('scope:'):
                target = saved_ref(data, v)
            elif v.startswith('rite:'):
                key = v.removeprefix('rite:').removesuffix('.faith')
                if key not in data.rites:
                    raise MissingReference(key)
                target = ('faith', data.rites[key])
            else:
                target = ('faith', v.removeprefix('faith:'))
            values.append(('faith', data.faith) == target)
        elif k in {'rite', 'this'}:
            if v.startswith('scope:'):
                target = saved_ref(data, v)
            else:
                key = v.removeprefix('rite:')
                if key not in data.rites:
                    raise MissingReference(key)
                target = ('rite', key)
            actual = ('rite', data.current_rite) if k == 'rite' else scope_this
            values.append(actual == target)
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


def execute(body, data, context=None):
    for e in body.entries:
        if e.key == 'limit':
            continue
        if e.key == 'if':
            if predicate(one(e.value, 'limit'), data):
                execute(e.value, data, context)
        elif e.key == 'clear_saved_scope':
            data.saved.pop(e.value, None)
        elif e.key == 'save_scope_as':
            if context is None:
                raise AssertionError('Object scope required')
            data.saved[e.value] = context
            if context[0] == 'rite':
                data.parents.setdefault(context[1], data.rites.get(context[1], data.source_rite_faith))
        elif e.key in {'rite', 'faith', 'main_rite'} and isinstance(e.value, Block):
            kind, value = ('faith', data.faith) if e.key == 'faith' else ('rite', data.main_rite if e.key == 'main_rite' else data.current_rite)
            execute(e.value, data, (kind, value))
        elif e.key == 'create_rite_from_type':
            key = scalar(e.value, 'type')
            assert scalar(e.value, 'convert') == 'no'
            data.creates.append(key)
            if key not in data.create_failures:
                data.rites[key] = data.faith
                data.saved[scalar(e.value, 'save_scope_as')] = ('rite', 'foreign_output' if data.wrong_output else key)
                if data.switch_on_create:
                    data.current_rite = key
                if data.create_changes_faith:
                    data.faith = 'other_faith'
                if data.create_changes_main:
                    data.main_rite = 'other_main'
        elif e.key == 'set_character_rite':
            target = saved_ref(data, e.value)
            assert target[0] == 'rite'
            data.restores.append(target[1])
            if not data.restore_fails:
                data.current_rite = target[1]
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
            self.assertEqual({e.key for e in call.entries}, {'type', 'convert', 'save_scope_as'})
            self.assertEqual(scalar(call, 'type'), key)
            self.assertEqual(scalar(call, 'convert'), 'no')
            self.assertEqual(scalar(call, 'save_scope_as'), producer.CREATED_RITE)
            self.assertEqual([e.key for e in branch.entries[:3]], ['limit', 'clear_saved_scope', 'create_rite_from_type'])

    def test_actual_character_faith_human_alive_and_existing_main_rite_are_required(self):
        for changes in ({'faith': 'catholic'}, {'human': False}, {'alive': False}, {'main_rite_exists': False}, {'source_rite_exists': False}):
            d = DataState(**changes)
            execute(self.effect, d)
            self.assertEqual(d.creates, [])
            self.assertFalse(d.checked)

    def test_all_missing_software_callback_can_create_and_then_set_checked(self):
        d = DataState(current_rite='actual_custom_original', main_rite='actual_custom_main')
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids)
        self.assertEqual(d.restores, ['actual_custom_original'] * 36)
        self.assertTrue(d.checked)
        self.assertEqual((d.current_rite, d.faith, d.main_rite), ('actual_custom_original', 'confucian_faith', 'actual_custom_main'))

    def test_partial_existing_objects_are_preserved_and_only_missing_types_are_requested(self):
        existing = {self.ids[0]: 'confucian_faith', self.ids[17]: 'confucian_faith'}
        d = DataState(rites=dict(existing))
        execute(self.effect, d)
        self.assertEqual(d.creates, [x for x in self.ids if x not in existing])
        self.assertEqual({k: d.rites[k] for k in existing}, existing)

    def test_second_invocation_is_idempotent_and_does_not_repeat_creation(self):
        d = DataState()
        execute(self.effect, d)
        before = (dict(d.rites), list(d.creates), list(d.restores))
        execute(self.effect, d)
        self.assertEqual((d.rites, d.creates, d.restores), before)

    def test_explicit_create_failure_does_not_set_completion_or_fake_ready(self):
        d = DataState(create_failures={self.ids[4]})
        execute(self.effect, d)
        self.assertNotIn(self.ids[4], d.rites)
        self.assertEqual(len(d.restores), 35)
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
        self.assertIn('GetPlayer.MakeScope', self.outputs['gui/lyd_saved_rite_bootstrap.gui'].decode('utf-8-sig'))
        sgui = one(parse_clausewitz(self.outputs['common/scripted_guis/lyd_saved_rite_bootstrap.txt'].decode('utf-8-sig')), 'lyd_saved_rite_bootstrap_gui')
        shown = one(sgui, 'is_shown')
        self.assertEqual([e.value for e in shown.entries if e.key == 'faith' and isinstance(e.value, str)], ['faith:confucian_faith'])
        self.assertEqual(scalar(one(shown, 'faith'), 'exists'), 'main_rite')
        self.assertEqual(scalar(one(shown, 'NOT'), 'has_global_variable'), producer.CHECKED)
        self.assertEqual([e.value for e in shown.entries if e.key == 'exists'], ['rite'])
        forbidden = {'set_character_faith', 'set_character_faith_with_conversion', 'set_parent_faith', 'set_main_rite', 'set_religious_head_title', 'force_refresh_head_of_rite', 'every_faith_character', 'every_living_character', 'trigger_event', 'add_gold', 'add_piety', 'set_personal_tenet', 'add_known_tenet'}
        self.assertFalse({e.key for e in walk(self.effect)} & forbidden)
        self.assertEqual([e.value for e in walk(self.effect) if e.key == 'set_character_rite'], ['scope:' + producer.ORIGINAL_RITE] * 36)

    def test_no_caller_rite_drift_never_invokes_restoration(self):
        d = DataState(switch_on_create=False)
        execute(self.effect, d)
        self.assertTrue(d.checked)
        self.assertEqual(d.restores, [])

    def test_failed_restore_stops_next_creation_and_completion(self):
        d = DataState(restore_fails=True)
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids[:1])
        self.assertEqual(d.restores, ['jingxue'])
        self.assertEqual(d.current_rite, self.ids[0])
        self.assertFalse(d.checked)

    def test_wrong_output_scope_cannot_authorize_restore(self):
        d = DataState(wrong_output=True)
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids[:1])
        self.assertEqual(d.restores, [])
        self.assertFalse(d.checked)

    def test_actual_faith_change_does_not_force_cross_faith_restore(self):
        d = DataState(create_changes_faith=True)
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids[:1])
        self.assertEqual(d.restores, [])
        self.assertEqual(d.faith, 'other_faith')
        self.assertFalse(d.checked)

    def test_actual_main_rite_change_is_not_overwritten_or_marked_complete(self):
        d = DataState(create_changes_main=True)
        execute(self.effect, d)
        self.assertEqual(d.creates, self.ids[:1])
        self.assertEqual(d.restores, [])
        self.assertEqual(d.main_rite, 'other_main')
        self.assertFalse(d.checked)


if __name__ == '__main__':
    unittest.main()
