"""Generated AST contracts; no CK3, faith mutation or personal selection is executed."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('LYD_VANILLA_TEST_REPO', str(HERE.parents[1])))
TOOLS = Path(os.environ.get('LYD_VANILLA_TEST_TOOLS', str(HERE)))
sys.path[:0] = [str(TOOLS), str(REPO / 'mod_li_yu_dao/tools'), str(REPO / 'tools')]
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from gen_runtime import build_outputs as runtime_outputs
from gen_content import build_outputs as content_outputs
from content_data import ACTIVE_RITES, ACTIVE_TENETS, MAIN_RITE_ID
from validate_static import validate
from build_release import collect_runtime_files

def blocks(body, key):
    return [e.value for e in body.entries if e.key == key and isinstance(e.value, Block)]

def one(body, key):
    found = blocks(body, key)
    if len(found) != 1:
        raise AssertionError((key, len(found)))
    return found[0]

def values(body, key):
    return [e.value for e in body.entries if e.key == key and isinstance(e.value, str)]

def walk(body):
    for entry in body.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from walk(entry.value)

def direct(body, key, value):
    return value in values(body, key)

class VanillaFaithIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = {**runtime_outputs(), **content_outputs()}
        cls.defs = {}
        for rel, payload in cls.outputs.items():
            if rel.startswith(('common/', 'events/')) and rel.endswith('.txt'):
                for entry in parse_clausewitz(payload.decode('utf-8-sig')).entries:
                    if isinstance(entry.value, Block):
                        cls.defs[entry.key] = entry.value

    def test_36_rites_enrich_vanilla_faith_without_overriding_vanilla_rites(self):
        rites = parse_clausewitz(self.outputs['common/religion/rite_types/lyd_rites.txt'].decode('utf-8-sig'))
        self.assertEqual(len(rites.entries), 36)
        self.assertEqual({e.key for e in rites.entries}, {r.script_id for r in ACTIVE_RITES})
        for rite in rites.entries:
            self.assertTrue(direct(rite.value, 'faith', 'confucian_faith'))
            self.assertEqual(len(one(rite.value, 'tenets').entries), 3)

    def test_legacy_definition_has_no_live_history_or_vanilla_localization_override(self):
        faiths = parse_clausewitz(self.outputs['common/religion/faith_types/lyd_faiths.txt'].decode('utf-8-sig'))
        self.assertEqual([e.key for e in faiths.entries], ['lyd_common_faith'])
        self.assertTrue(direct(faiths.entries[0].value, 'historical', 'yes'))
        self.assertEqual(values(faiths.entries[0].value, 'main_rite'), [])
        self.assertEqual(parse_clausewitz(self.outputs['history/faiths/lyd_faith_history.txt'].decode('utf-8-sig')).entries, ())
        for lang in ('english', 'simp_chinese'):
            text = self.outputs[f'localization/{lang}/lyd_runtime_l_{lang}.yml'].decode('utf-8-sig')
            self.assertNotIn('\n confucian_faith:', text)
            self.assertIn('\n lyd_common_faith:', text)

    def test_entry_requires_exact_current_and_target_faith_before_character_setter(self):
        display = self.defs['lyd_can_enter_display_trigger']
        self.assertTrue(direct(display, 'faith', 'faith:confucian_faith'))
        self.assertTrue(direct(display, 'faith', f'rite:{MAIN_RITE_ID}.faith'))
        branch = one(self.defs['lyd_enter_effect'], 'if')
        pre = one(branch, 'limit')
        self.assertTrue(direct(pre, 'faith', 'faith:confucian_faith'))
        self.assertTrue(direct(pre, 'faith', f'rite:{MAIN_RITE_ID}.faith'))
        self.assertEqual(values(branch, 'set_character_rite'), [f'rite:{MAIN_RITE_ID}'])
        post_branch = one(branch, 'if')
        self.assertTrue(direct(one(post_branch, 'limit'), 'faith', 'faith:confucian_faith'))
        self.assertTrue(direct(post_branch, 'lyd_learn_catalogue_tenets_effect', 'yes'))

    def test_every_school_effect_and_option_reject_cross_faith_adoption(self):
        for rite in ACTIVE_RITES:
            pre = one(one(self.defs[f'lyd_adopt_{rite.slug}_effect'], 'if'), 'limit')
            self.assertTrue(direct(pre, 'faith', f'rite:{rite.script_id}.faith'))
            self.assertTrue(direct(pre, 'exists', f'rite:{rite.script_id}'))
            options = [o for body in self.defs.values() for o in blocks(body, 'option') if direct(o, 'name', f'lyd_adopt_{rite.slug}')]
            self.assertEqual(len(options), 1)
            self.assertTrue(direct(one(options[0], 'trigger'), 'faith', f'rite:{rite.script_id}.faith'))

    def test_personal_study_registers_only_new_ids_and_preserves_all_existing_statuses(self):
        branch = one(self.defs['lyd_learn_catalogue_tenets_effect'], 'if')
        guard = one(branch, 'limit')
        self.assertTrue(direct(guard, 'lyd_is_player_trigger', 'yes'))
        self.assertTrue(direct(guard, 'faith', 'faith:confucian_faith'))
        registrations = blocks(one(branch, 'faith'), 'if')
        self.assertEqual(len(registrations), 36)
        for entry, tenet in zip(registrations, ACTIVE_TENETS):
            statuses = one(one(one(entry, 'limit'), 'NOT'), 'OR')
            checks = [one(b, 'has_tenet_status') for b in blocks(statuses, 'main_rite')]
            self.assertEqual({values(c, 'status')[0] for c in checks}, {'core', 'permitted', 'known', 'prohibited'})
            self.assertEqual({values(c, 'tenet')[0] for c in checks}, {tenet.script_id})
            write = one(entry, 'set_tenet_status')
            self.assertEqual(values(write, 'tenet'), [tenet.script_id])
            self.assertEqual(values(write, 'status'), ['permitted'])
        learns = [b for b in blocks(branch, 'if') if values(b, 'add_known_tenet')]
        self.assertEqual([values(b, 'add_known_tenet')[0] for b in learns], [t.script_id for t in ACTIVE_TENETS])
        for b in learns:
            self.assertEqual(values(one(one(b, 'limit'), 'NOT'), 'knows_tenet'), values(b, 'add_known_tenet'))
        keys = {e.key for e in walk(branch)}
        self.assertFalse(keys & {'force_set_personal_tenet', 'set_personal_tenet', 'every_faith_character', 'set_parent_faith', 'set_main_rite'})

    def test_study_decision_is_explicit_human_same_faith_entry(self):
        decision = self.defs['lyd_learn_tenets_decision']
        shown = one(decision, 'is_shown')
        self.assertTrue(direct(shown, 'lyd_is_player_trigger', 'yes'))
        self.assertTrue(direct(shown, 'faith', 'faith:confucian_faith'))
        self.assertTrue(direct(one(decision, 'effect'), 'lyd_learn_catalogue_tenets_effect', 'yes'))

    def test_i3b_admits_vanilla_with_complete_supported_roster_and_independent_mandates(self):
        guard = self.defs['lyd_i3b_only_owned_rites_faith_trigger']
        self.assertTrue(blocks(guard, 'NOT'))
        self.assertTrue(any(e.key == 'any_faith_rite' for e in walk(guard)))
        actor = self.defs['lyd_i3b_actor_trigger']
        self.assertTrue(any(e.key == 'faith' and e.value == 'faith:confucian_faith' for e in walk(actor)))
        self.assertTrue(direct(actor, 'lyd_i3b_player_actor_trigger', 'yes'))
        authority = [b for b in blocks(one(actor, 'OR'), 'AND') if direct(b, 'faith', 'faith:confucian_faith')]
        self.assertEqual(len(authority), 1)
        self.assertTrue(direct(one(authority[0], 'rite'), 'lyd_i3b_supported_rite_trigger', 'yes'))
        player = one(self.defs['lyd_i3b_player_actor_trigger'], 'OR')
        self.assertTrue(direct(player, 'lyd_c3_player_actor_trigger', 'yes'))
        untouched = [b for b in blocks(player, 'AND') if direct(b, 'faith', 'faith:confucian_faith')]
        self.assertEqual(len(untouched), 1)
        for key, value in [('is_ai', 'no'), ('is_alive', 'yes'), ('is_adult', 'yes'),
                           ('is_landed', 'yes'), ('religion', 'religion:confucianism_religion')]:
            self.assertEqual(values(untouched[0], key), [value])
        self.assertTrue(direct(one(untouched[0], 'NOT'), 'has_trait', 'incapable'))
        self.assertTrue(direct(one(untouched[0], 'rite'), 'lyd_i3b_supported_rite_trigger', 'yes'))
        self.assertFalse(any(e.key in {'has_character_flag', 'lyd_member_rite_trigger'} for e in walk(untouched[0])))
        self.assertTrue(direct(actor, 'lyd_i3b_no_other_office_trigger', 'yes'))
        captured = one(self.defs['lyd_i3b_captured_authority_trigger'], 'OR')
        mode2 = [b for b in blocks(captured, 'AND') if direct(b, 'var:lyd_i3b_authority_mode', '2')]
        self.assertEqual(len(mode2), 1)
        self.assertEqual(values(mode2[0], 'faith'), ['faith:confucian_faith'])
        self.assertEqual(values(mode2[0], 'rite'), ['var:lyd_i3b_actor_rite'])
        self.assertTrue(direct(one(mode2[0], 'rite'), 'lyd_i3b_supported_rite_trigger', 'yes'))
        supported = self.defs['lyd_i3b_supported_faith_trigger']
        self.assertTrue(any(e.key == 'this' and e.value == 'faith:confucian_faith' for e in walk(supported)))
        self.assertTrue(any(e.key == 'any_faith_rite' for e in walk(supported)))
        self.assertTrue(any(e.key == 'lyd_i3b_supported_rite_trigger' for e in walk(supported)))
        rites = self.defs['lyd_i3b_supported_rite_trigger']
        self.assertTrue({'rite:jingxue','rite:daoxue'} <= {e.value for e in walk(rites) if e.key == 'this'})
        ready = self.defs['lyd_i3b_ready_trigger']
        self.assertTrue(any(e.key == 'variable' and e.value == 'lyd_i3b_rites' for e in walk(ready)))
        self.assertTrue(any(e.key == 'var:lyd_i3b_signed' and e.value == '1' for e in walk(ready)))
        self.assertTrue(any(e.key == 'var:lyd_i3b_player_yes' and e.value == '1' for e in walk(ready)))

    def test_real_static_validator_accepts_projection_and_rejects_parallel_rite_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            for rel,payload in self.outputs.items():
                path = source/rel; path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
            (source/'descriptor.mod').write_bytes((REPO/'mod_li_yu_dao/descriptor.mod').read_bytes())
            inventory = collect_runtime_files(source)
            self.assertEqual(len(inventory), 83)
            self.assertNotIn("history/faiths/lyd_faith_history.txt", inventory)
            result = validate(source)
            self.assertEqual(result['errors'], [])
            path = source/'common/religion/rite_types/lyd_rites.txt'
            text = path.read_text(encoding='utf-8-sig').replace('faith = confucian_faith', 'faith = lyd_common_faith', 1)
            path.write_text(text,encoding='utf-8-sig')
            self.assertTrue(any('LYD rite must enrich vanilla confucian_faith' in e for e in validate(source)['errors']))

if __name__ == '__main__':
    unittest.main()
