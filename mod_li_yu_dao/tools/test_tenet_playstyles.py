"""Portable contracts for active practices; no CK3, native DLL, or save reads."""
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[2] / 'tools'))
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from validate_static import blocks, scalar, guarded_effect, player_guard, parse_localization
from content_data import TENETS_BY_CODE
from tenet_playstyle_data import PRACTICES, validate_practices
from gen_tenet_playstyles import build_outputs, option_key, PHASE_FLAG


def entries(block):
    return {e.key:e.value for e in block.entries if isinstance(e.value,Block)}


class TriggerWorld:
    """Evaluate only the generated eligibility vocabulary against explicit facts.

    This is a policy regression, not an assertion that CK3 executed any action.
    Unknown operations fail, so learned-only knowledge cannot become permission.
    """
    def __init__(self,defs,*,core=(),personal=(),known=(),flags=(),ai=False,alive=True,adult=True,imprisoned=False,incapable=False,gold=1000,piety=1000,prestige=1000,landed=True,war=False,control=50,courtier=True):
        self.defs=defs
        self.facts=locals()
    def check(self,block,scope='character'):
        return all(self.one(e,scope) for e in block.entries)
    def one(self,e,scope):
        k,v=e.key,e.value
        f=self.facts
        if k=='OR': return any(self.one(row,scope) for row in v.entries)
        if k in ('AND','custom_description'): return self.check(v,scope)
        if k=='text': return True
        if k=='NOT': return not self.check(v,scope)
        if k in self.defs: return self.check(self.defs[k],scope)
        if k=='rite': return self.check(v,'rite')
        if k=='capital_county': return f['landed'] and self.check(v,'county')
        if k=='any_courtier': return f['courtier']
        if k=='rite_has_tenet': return scope=='rite' and v in f['core']
        if k=='has_personal_tenet': return v in f['personal']
        if k=='has_character_flag': return v in f['flags']
        if k=='has_trait': return v=='incapable' and f['incapable']
        if k=='exists': return (v=='rite') or (v=='capital_county' and f['landed'])
        booleans={'is_ai':'ai','is_alive':'alive','is_adult':'adult','is_imprisoned':'imprisoned','is_landed':'landed','is_at_war':'war'}
        if k in booleans: return f[booleans[k]]==(v=='yes')
        if k in ('gold','piety','prestige'): return e.operator=='>=' and f[k]>=int(v)
        if k=='county_control': return e.operator=='<' and f['control']<int(v)
        raise AssertionError(f'unsupported predicate {scope}:{k}')


class TenetPlaystyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=build_outputs()
        cls.scripts={p:parse_clausewitz(b.decode('utf-8-sig')) for p,b in cls.outputs.items() if p.endswith('.txt')}
        cls.triggers=entries(cls.scripts['common/scripted_triggers/lyd_tenet_playstyle_triggers.txt'])
        cls.effects={k:v for p,b in cls.scripts.items() if '/scripted_effects/' in p for k,v in entries(b).items()}
        cls.decisions=entries(cls.scripts['common/decisions/lyd_tenet_playstyle_decisions.txt'])
        cls.events=entries(cls.scripts['events/lyd_tenet_playstyle_events.txt'])
        cls.modifiers=entries(cls.scripts['common/modifiers/lyd_tenet_playstyle_modifiers.txt'])

    def test_exact_catalogue_coverage_and_distinct_mechanics(self):
        validate_practices()
        self.assertEqual(len(self.decisions),36)
        self.assertEqual(len(self.events),36)
        self.assertEqual(set(p.code for p in PRACTICES),set(TENETS_BY_CODE))
        self.assertEqual(len(self.effects),sum(len(p.options) for p in PRACTICES))
        self.assertEqual({len(p.options) for p in PRACTICES},{1,2,3,4,6})

    def test_actual_core_or_chosen_personal_both_unlock_but_knowledge_does_not(self):
        for p in PRACTICES:
            tenet=TENETS_BY_CODE[p.code].script_id
            trigger=self.triggers[p.key+'_eligible_trigger']
            self.assertTrue(TriggerWorld(self.triggers,core=(tenet,)).check(trigger),p.code)
            self.assertTrue(TriggerWorld(self.triggers,personal=(tenet,)).check(trigger),p.code)
            self.assertFalse(TriggerWorld(self.triggers,known=(tenet,)).check(trigger),p.code)
            self.assertFalse(TriggerWorld(self.triggers,core=(tenet,),ai=True).check(trigger),p.code)

    def test_resources_and_cooldown_rechecked_before_first_mutation(self):
        for p in PRACTICES:
            for i,o in enumerate(p.options):
                key=option_key(p,i)
                effect=self.effects[key+'_effect']
                self.assertEqual(len(effect.entries),1)
                branch=effect.entries[0]
                self.assertEqual(branch.key,'if')
                limit=blocks(branch.value,'limit')[0]
                self.assertEqual(scalar(limit,key+'_trigger'),'yes')
                self.assertTrue(guarded_effect(effect,self.triggers,self.effects),key)
                flag=p.key+'_cooldown'
                world=TriggerWorld(self.triggers,core=(TENETS_BY_CODE[p.code].script_id,),war=('is_at_war = yes' in o.conditions),flags=((PHASE_FLAG,) if o.phase=='practice' else ()))
                trigger=self.triggers[key+'_trigger']
                self.assertTrue(world.check(trigger),key)
                for resource,amount in (('gold',o.gold),('piety',o.piety),('prestige',o.prestige)):
                    if amount:
                        world.facts[resource]=amount-1
                        self.assertFalse(world.check(trigger),key+' insufficient '+resource)
                        world.facts[resource]=1000
                world.facts['flags']=(*world.facts['flags'],flag)
                self.assertFalse(world.check(trigger),key+' stale second choice')
                world.facts['flags']=()
                world.facts['core']=()
                self.assertFalse(world.check(trigger),key+' dropped tenet')

    def test_t33_inquiry_and_practice_are_mutually_exclusive_stored_phases(self):
        p=next(p for p in PRACTICES if p.code=='T33')
        world=TriggerWorld(self.triggers,personal=(TENETS_BY_CODE['T33'].script_id,))
        a,b=(self.triggers[option_key(p,i)+'_trigger'] for i in (0,1))
        self.assertTrue(world.check(a)); self.assertFalse(world.check(b))
        world.facts['flags']=(PHASE_FLAG,)
        self.assertFalse(world.check(a)); self.assertTrue(world.check(b))
        raw='\n'.join(self.outputs[p].decode('utf-8-sig') for p in self.outputs if '/scripted_effects/' in p)
        self.assertIn('add_character_flag = '+PHASE_FLAG,raw)
        self.assertIn('remove_character_flag = '+PHASE_FLAG,raw)

    def test_context_restrictions_and_landless_personal_path(self):
        p=next(p for p in PRACTICES if p.code=='T11')
        world=TriggerWorld(self.triggers,personal=(TENETS_BY_CODE[p.code].script_id,),war=False)
        self.assertFalse(world.check(self.triggers[option_key(p,0)+'_trigger']))
        world.facts['war']=True
        self.assertTrue(world.check(self.triggers[option_key(p,0)+'_trigger']))
        p=next(p for p in PRACTICES if p.code=='T02')
        world=TriggerWorld(self.triggers,personal=(TENETS_BY_CODE[p.code].script_id,),landed=False)
        self.assertTrue(world.check(self.triggers[option_key(p,0)+'_trigger']))
        p=next(p for p in PRACTICES if p.code=='T06')
        world.facts['personal']=(TENETS_BY_CODE[p.code].script_id,)
        self.assertFalse(world.check(self.triggers[option_key(p,0)+'_trigger']))

    def test_all_decisions_guarded_player_only_and_events_reachable(self):
        for p in PRACTICES:
            decision=self.decisions[p.key+'_decision']
            self.assertEqual(scalar(decision,'selection_tooltip'),p.key+'_decision_tooltip')
            self.assertEqual(scalar(decision,'confirm_text'),p.key+'_decision_confirm')
            self.assertEqual(scalar(decision,'ai_check_interval'),'0')
            self.assertTrue(player_guard(blocks(decision,'is_shown')[0],self.triggers))
            self.assertTrue(guarded_effect(blocks(decision,'effect')[0],self.triggers,self.effects))
            self.assertEqual(scalar(blocks(decision,'ai_will_do')[0],'base'),'0')
        raw='\n'.join(b.decode('utf-8-sig') for b in self.outputs.values())
        for event in self.events:
            self.assertIn('trigger_event = '+event,raw)
        self.assertNotRegex(raw,r'\b(?:every_living_character|every_character|every_faith|on_yearly_pulse|set_religious_head_title|change_title_holder)\b')
        for path,block in self.scripts.items():
            if '/scripted_effects/' in path:
                self.assertLessEqual(len(block.entries),8)

    def test_modifiers_are_referenced_in_correct_scope_and_no_orphans(self):
        for p in PRACTICES:
            for i,o in enumerate(p.options):
                raw=str(self.effects[option_key(p,i)+'_effect'])
                for suffix,values in (('character',o.character),('county',o.county)):
                    if values:
                        key=option_key(p,i)+'_'+suffix
                        self.assertIn(key,raw)
                        self.assertEqual({e.key:e.value for e in self.modifiers[key].entries},dict(values))
                if o.county or o.control or o.development:
                    self.assertIn('capital_county',raw)
                    self.assertIn('exists',str(self.triggers[option_key(p,i)+'_trigger']))
        self.assertEqual(len(self.modifiers),sum(bool(o.character)+bool(o.county) for p in PRACTICES for o in p.options))

    def test_localization_bilingual_bom_and_all_choice_names_resolved(self):
        languages=[]
        for lang in ('english','simp_chinese'):
            payload=self.outputs[f'localization/{lang}/lyd_tenet_playstyle_l_{lang}.yml']
            self.assertTrue(payload.startswith(b'\xef\xbb\xbf'))
            lines=payload.decode('utf-8-sig').splitlines()
            self.assertEqual(lines[0],'l_'+lang+':')
            keys=[line.strip().split(':',1)[0] for line in lines[1:] if line.strip() and not line.strip().startswith('#')]
            self.assertEqual(len(keys),len(set(keys)))
            languages.append(set(keys))
        self.assertEqual(*languages)
        for p in PRACTICES:
            self.assertIn(p.key+'_decision',languages[0])
            for i,_ in enumerate(p.options):
                self.assertIn(option_key(p,i),languages[0])

    def test_invalid_missing_cost_duplicate_or_wrong_scope_data_rejected(self):
        first=PRACTICES[0]
        for choice in (replace(first.options[0],gold=0,piety=0,prestige=0),replace(first.options[0],character=(('county_opinion_add','20'),)),replace(first.options[0],rewards=('invented_setter = yes',))):
            with self.assertRaises(ValueError):
                validate_practices((replace(first,options=(choice,)),*PRACTICES[1:]))
        with self.assertRaisesRegex(ValueError,'identical'):
            validate_practices((first,replace(PRACTICES[1],options=first.options),*PRACTICES[2:]))

    def test_output_is_reproducible_and_generated_files_match(self):
        self.assertEqual(self.outputs,build_outputs())
        root=Path(__file__).resolve().parents[1]
        for path,payload in self.outputs.items():
            self.assertEqual((root/path).read_bytes(),payload,path)
            self.assertIn(b'GENERATED FILE',payload,path)


if __name__=='__main__':
    unittest.main()
