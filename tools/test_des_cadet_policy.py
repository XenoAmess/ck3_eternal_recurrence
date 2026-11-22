"""File-only regressions for actual DES guards and annual snapshot AST.

The tiny interpreter covers only the new policy scripts. It does not establish
engine scheduling, Native eligibility or a naturally elapsed game year.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest

REPO=Path(os.environ.get('DES_REPO',str(Path(__file__).resolve().parents[1])))
SOURCE=Path(os.environ.get('DES_CADET_SOURCE',str(REPO)))
BASE_SOURCE=Path(os.environ.get('DES_CADET_BASE_SOURCE',str(REPO)))
STOCK_FIXTURE=REPO/'tools/testdata/des_cadet_stock_26785313.json'
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
sys.path.insert(0,str(REPO/'tools/lyd_i3b_checkpoint_readback/reader/dependencies'))
from xar_autoplayer.campaign_score_save_reader import melt_tokens
from bounded_save_parser import parse_block
MOD='mod_dynastic_esotericism/'
ALLOW='des_ai_cadet_creation_allowed_trigger'

def read(relative):
    p=SOURCE/relative
    if not p.exists():p=BASE_SOURCE/relative
    if not p.exists():p=REPO/relative
    return p.read_text(encoding='utf-8-sig')

def ast(text):return parse_block('{ '+' '.join(melt_tokens(io.BytesIO(text.encode('utf-8'))))+' }')
def body(rows,key):
    found=[x['value'] for x in rows if x['key']==key]
    if len(found)!=1:raise ValueError(('expected unique',key,len(found)))
    return found[0]
def definition(relative,key):return body(ast(read(MOD+relative)),key)

@dataclass(eq=False)
class Obj:
    kind:str
    name:str
    ai:bool=True
    alive:bool=True
    dynasty:object=None
    house:object=None
    house_head:object=None
    founder:object=None
    top:object=None
    liege:object=None
    ruler:bool=False
    rank:int=0
    noble_title:bool=False
    needs_cadet:bool=True
    reclaim:bool=False
    variables:dict=field(default_factory=dict)
    doctrines:set=field(default_factory=set)
    houses:list=field(default_factory=list)
    members:list=field(default_factory=list)

class Policy:
    def __init__(self):
        self.triggers={r['key']:r['value'] for r in ast(read(MOD+'common/scripted_triggers/des_cadet_triggers.txt'))}
        self.triggers.update({r['key']:r['value'] for r in ast(read(MOD+'common/scripted_triggers/des_dynastic_triggers.txt'))})
        self.effects={r['key']:r['value'] for r in ast(read(MOD+'common/scripted_effects/des_cadet_effects.txt'))}
        self.scopes={}
        self.writes=[]
        self.collected=[]
        self.before_move_hook=None
    def ref(self,text,current,prev=None):
        parts=text.split('.')
        first=parts.pop(0)
        if first=='this':obj=current
        elif first=='prev':obj=prev
        elif first.startswith('scope:'):obj=self.scopes.get(first[6:])
        else:obj=self.attr(current,first); 
        for part in parts:obj=self.attr(obj,part)
        return obj
    def attr(self,obj,name):
        if obj is None:raise ValueError('unguarded missing scope '+name)
        if name.startswith('var:'):return obj.variables.get(name[4:])
        if name=='house_dynasty':return obj.dynasty
        if name in ('dynasty_founder','house_founder'):return obj.founder
        if name=='top_liege':return obj.top
        if name=='highest_held_title_tier':return obj.rank
        return getattr(obj,name)
    def exists(self,text,current,prev):
        try:return self.ref(text,current,prev) is not None
        except (AttributeError,ValueError):return False
    def condition(self,rows,current,prev=None):
        values=[];i=0;last=None
        while i<len(rows):
            r=rows[i];key,value=r['key'],r['value'];i+=1
            if key is None and value=='highest_held_title_tier':
                op=rows[i]['value'];target=rows[i+1]['value'];i+=2
                if op!='<':raise ValueError('unexpected comparison')
                values.append(current.rank<self.ref(target,current,prev));continue
            if key in ('AND','OR','NOT','NOR','NAND'):
                clauses=[];j=0
                while j<len(value):
                    width=3 if value[j]['key'] is None and value[j]['value']=='highest_held_title_tier' else 1
                    clauses.append(value[j:j+width]);j+=width
                operands=[self.condition(clause,current,prev) for clause in clauses]
                ok=all(operands) if key=='AND' else any(operands) if key=='OR' else not any(operands) if key=='NOR' else not all(operands)
            elif key=='trigger_if':
                passed=self.condition(body(value,'limit'),current,prev)
                ok=not passed or self.condition([r for r in value if r['key']!='limit'],current,prev)
                last=passed
            elif key=='trigger_else':ok=last or self.condition(value,current,prev)
            elif key=='exists':ok=self.exists(value,current,prev)
            elif key=='is_ai':ok=current.ai==(value=='yes')
            elif key=='is_alive':ok=current.alive==(value=='yes')
            elif key=='is_ruler':ok=current.ruler==(value=='yes')
            elif key=='rite_has_doctrine':ok=value in current.doctrines
            elif key=='has_variable':ok=value in current.variables
            elif key=='is_noble_family_title':ok=current.noble_title==(value=='yes')
            elif key=='any_held_title':ok=current.noble_title
            elif key=='gdp_merchant_can_reclaim_house_company_title_trigger':ok=current.reclaim==(value=='yes')
            elif key=='gdp_merchant_needs_cadet_for_new_company_trigger':ok=current.needs_cadet==(value=='yes')
            elif key in self.triggers:ok=self.condition(self.triggers[key],current,prev)==(value=='yes')
            elif isinstance(value,list):ok=self.condition(value,self.ref(key,current,prev),current)
            else:ok=self.ref(key,current,prev) is self.ref(value,current,prev)
            values.append(ok)
        return all(values)
    def allowed(self,actor):return self.condition(self.triggers[ALLOW],actor)
    def run(self,key,current):self.execute(self.effects[key],current)
    def execute(self,rows,current):
        last=None
        for r in rows:
            key,value=r['key'],r['value']
            if key=='limit':continue
            if key=='if':
                last=self.condition(body(value,'limit'),current)
                if last:self.execute([r for r in value if r['key']!='limit'],current)
            elif key=='else':
                if last is None:raise ValueError('else without if')
                if not last:self.execute(value,current)
            elif key=='save_scope_as':self.scopes[value]=current
            elif key=='clear_saved_scope':self.scopes.pop(value,None)
            elif key=='set_variable':current.variables[body(value,'name')]=True if body(value,'value')=='yes' else self.ref(body(value,'value'),current)
            elif key=='remove_variable':current.variables.pop(value,None)
            elif key=='clear_variable_list':current.variables[value]=[]
            elif key=='add_to_variable_list':
                target=self.ref(body(value,'target'),current)
                current.variables.setdefault(body(value,'name'),[]).append(target);self.collected.append(target)
            elif key in ('every_dynasty_house','every_dynasty_member','every_in_list'):
                if key=='every_in_list' and self.before_move_hook:
                    self.before_move_hook();self.before_move_hook=None
                members=current.houses if key=='every_dynasty_house' else current.members if key=='every_dynasty_member' else current.variables[body(value,'variable')]
                for target in list(members):
                    limits=[x['value'] for x in value if x['key']=='limit']
                    if not limits or self.condition(limits[0],target):self.execute([x for x in value if x['key'] not in ('variable','limit')],target)
            elif key=='set_house':
                target=self.ref(value,current);self.writes.append((current,target));current.house=target
            elif key=='debug_log':pass
            elif key in self.effects:self.run(key,current)
            elif isinstance(value,list):self.execute(value,self.ref(key,current))
            else:raise ValueError('unexpected effect '+str(key))

def world():
    founder=Obj('character','original founder')
    dynasty=Obj('dynasty','bound',founder=founder)
    main=Obj('house','original main',dynasty=dynasty,founder=founder)
    cadet=Obj('house','cadet',dynasty=dynasty,founder=Obj('character','cadet founder'))
    dynasty.houses=[main,cadet]
    rite=Obj('rite','bound rite',doctrines={'des_doctrine_dynastic'})
    rite.variables={'des_bound_dynasty':dynasty,'des_join_house':cadet}
    dynasty.variables={'des_bound_rite':rite}
    ai=Obj('character','AI other faith',dynasty=dynasty,house=cadet)
    player=Obj('character','player cadet',ai=False,dynasty=dynasty,house=cadet)
    main_member=Obj('character','main member',dynasty=dynasty,house=main)
    dynasty.members=[ai,player,main_member]
    return dynasty,rite,main,cadet,ai,player,main_member

class CadetPolicyTest(unittest.TestCase):
    def test_ai_bound_dynasty_is_blocked_across_faith_and_existing_house(self):
        d,r,h,c,ai,p,m=world();policy=Policy()
        self.assertFalse(policy.allowed(ai));self.assertFalse(policy.allowed(m))
        ai.house=h;self.assertFalse(policy.allowed(ai))
    def test_player_creation_and_other_dynasty_remain_allowed(self):
        d,r,h,c,ai,p,m=world();policy=Policy();self.assertTrue(policy.allowed(p))
        ai.dynasty=Obj('dynasty','other');self.assertTrue(policy.allowed(ai))
    def test_lowborn_missing_partial_and_conflicting_backlinks_are_safe(self):
        d,r,h,c,ai,p,m=world();policy=Policy()
        ai.dynasty=None;self.assertTrue(policy.allowed(ai));ai.dynasty=d
        r.variables.pop('des_join_house');self.assertTrue(policy.allowed(ai))
        r.variables['des_join_house']=c;r.variables['des_bound_dynasty']=Obj('dynasty','wrong');self.assertTrue(policy.allowed(ai))
    def test_unchecked_none_stops_ai_guard_and_yearly_recovery(self):
        d,r,h,c,ai,p,m=world();policy=Policy();r.doctrines={'des_doctrine_none'}
        self.assertTrue(policy.allowed(ai));policy.run('des_annual_cadet_recovery_effect',r)
        self.assertIs(ai.house,c);self.assertIs(p.house,c);self.assertEqual([],policy.writes)
    def test_cadet_creation_entry_wraps_are_exact_and_other_stock_ast_unchanged(self):
        operations=json.loads(STOCK_FIXTURE.read_text())['stock_overrides']
        for change in operations:
            normalized=ast(read(change['relative_path']))
            for op in reversed(change['operations']):
                target=body(normalized,op['definition'])
                if op.get('child'):target=body(target,op['child'])
                if op['kind']=='direct':
                    self.assertEqual({'key':op['predicate'],'value':'yes'},target.pop(0))
                else:
                    self.assertEqual(1,len(target));wrapped=body(target,'if')
                    self.assertEqual([{'key':op['predicate'],'value':'yes'}],body(wrapped,'limit'))
                    target[:]=[r for r in wrapped if r['key']!='limit']
            canonical=json.dumps(normalized,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
            self.assertEqual(change['original_canonical_ast_sha256'],hashlib.sha256(canonical).hexdigest(),change['relative_path'])
    def test_decision_checks_validity_ai_potential_and_execution(self):
        d=definition('common/decisions/00_dynasty_decisions.txt','create_cadet_branch_decision')
        for key in ('is_valid','ai_potential'):self.assertEqual('yes',body(body(d,key),ALLOW))
        gate=body(body(body(d,'effect'),'if'),'limit');self.assertEqual('yes',body(gate,ALLOW))
        f=definition('common/scripted_effects/00_decisions_effects.txt','found_cadet_house_decision_effect')
        self.assertEqual(['$CHARACTER$'],[x['key'] for x in f])
        self.assertEqual('yes',body(body(body(body(f,'$CHARACTER$'),'if'),'limit'),ALLOW))
    def test_non_cadet_merchant_and_republic_paths_are_preserved(self):
        d,r,h,c,ai,p,m=world();policy=Policy()
        merchant=policy.triggers['des_merchant_creation_without_forbidden_cadet_trigger']
        self.assertFalse(policy.condition(merchant,ai));ai.reclaim=True;self.assertTrue(policy.condition(merchant,ai))
        ai.reclaim=False;ai.needs_cadet=False;self.assertTrue(policy.condition(merchant,ai))
        head=Obj('character','other head');c.house_head=head
        republic=policy.triggers['des_republic_creation_without_forbidden_cadet_trigger']
        self.assertFalse(policy.condition(republic,ai));c.house_head=ai;self.assertTrue(policy.condition(republic,ai))
    def test_noble_family_keeps_existing_head_and_legitimate_transfer(self):
        d,r,h,c,ai,p,m=world();policy=Policy();gate=policy.triggers['des_noble_family_without_forbidden_cadet_trigger']
        c.house_head=ai;self.assertTrue(policy.condition(gate,ai))
        head=Obj('character','head',noble_title=True,liege=object());c.house_head=head
        self.assertFalse(policy.condition(gate,ai));head.noble_title=False;head.liege=None
        self.assertTrue(policy.condition(gate,ai));head.ai=False;self.assertFalse(policy.condition(gate,ai))
        head.ai=True;head.liege=object();head.top=ai.top=object();head.ruler=True;head.rank=1;ai.rank=2
        self.assertTrue(policy.condition(gate,ai));head.rank=3;self.assertFalse(policy.condition(gate,ai))
    def test_legacy_anchor_uses_unique_dynasty_founder_not_cadet_join_house(self):
        d,r,h,c,ai,p,m=world();policy=Policy();policy.run('des_capture_cadet_main_house_effect',d)
        self.assertIs(d.variables['des_cadet_main_house'],h)
        self.assertIs(r.variables['des_join_house'],c)
        d.founder.house=c;policy.run('des_capture_cadet_main_house_effect',d)
        self.assertIs(d.variables['des_cadet_main_house'],h)
    def test_ambiguous_or_invalid_anchor_never_selects_arbitrary_house(self):
        d,r,h,c,ai,p,m=world();policy=Policy();c.founder=d.founder
        policy.run('des_annual_cadet_recovery_effect',r)
        self.assertNotIn('des_cadet_main_house',d.variables);self.assertTrue(d.variables['des_cadet_main_house_unresolved'])
        self.assertEqual([],policy.writes)
        d.variables['des_cadet_main_house']=Obj('house','foreign',dynasty=Obj('dynasty','other'))
        policy.run('des_annual_cadet_recovery_effect',r);self.assertEqual([],policy.writes)
    def test_annual_snapshot_returns_all_living_cadets_including_player_once(self):
        d,r,h,c,ai,p,m=world();policy=Policy();dead=Obj('character','dead',alive=False,dynasty=d,house=c);d.members.append(dead)
        policy.run('des_annual_cadet_recovery_effect',r)
        self.assertIs(ai.house,h);self.assertIs(p.house,h);self.assertIs(m.house,h);self.assertIs(dead.house,c)
        self.assertEqual([ai,p],policy.collected);self.assertEqual([(ai,h),(p,h)],policy.writes)
        self.assertEqual([],d.variables['des_cadet_recovery_members'])
        policy.run('des_annual_cadet_recovery_effect',r);self.assertEqual(2,len(policy.writes))
    def test_reverse_binding_loss_and_post_snapshot_dynasty_change_do_not_move_others(self):
        d,r,h,c,ai,p,m=world();policy=Policy();d.variables['des_bound_rite']=Obj('rite','different')
        policy.run('des_annual_cadet_recovery_effect',r);self.assertEqual([],policy.writes)
        d.variables['des_bound_rite']=r
        other=Obj('dynasty','other');policy.before_move_hook=lambda:setattr(ai,'dynasty',other)
        policy.run('des_annual_cadet_recovery_effect',r)
        self.assertIs(ai.house,c);self.assertIs(p.house,h);self.assertEqual([(p,h)],policy.writes)
    def test_current_stock_primitive_inventory_is_finite_and_all_four_files_are_overridden(self):
        import re
        expected=json.loads(STOCK_FIXTURE.read_text())['primitive_inventory']
        found={path:len(re.findall(r'\bcreate_cadet_branch\s*=',read(MOD+path))) for path in expected}
        self.assertEqual(expected,found)
        self.assertEqual(8,sum(found.values()))
    def test_native_dynast_reuse_captures_anchor_in_same_binding_effect(self):
        reuse=definition('common/scripted_effects/des_binding_effects.txt','des_reuse_native_dynast_binding_effect')
        branch=body(reuse,'if')
        dynasty=body(branch,'var:des_native_source_dynasty')
        self.assertEqual(['set_variable','des_capture_cadet_main_house_effect'],[r['key'] for r in dynasty])
        self.assertEqual('des_bound_rite',body(body(dynasty,'set_variable'),'name'))
        self.assertEqual('yes',body(dynasty,'des_capture_cadet_main_house_effect'))
    def test_only_yearly_hook_calls_member_sweep_and_fresh_anchor_is_recorded(self):
        hook=ast(read(MOD+'common/on_action/des_cadet_on_actions.txt'))
        self.assertEqual(['des_annual_cadet_recovery'],[r['key'] for r in hook])
        original=ast(read(MOD+'common/on_action/des_on_actions.txt'))
        pulse=body(body(original,'yearly_global_pulse'),'on_actions')
        self.assertEqual(['des_annual_watchdog','des_annual_cadet_recovery','des_annual_house_leadership_recovery'],[r['value'] for r in pulse])
        self.assertIn('des_annual_cadet_recovery_effect',read(MOD+'common/on_action/des_cadet_on_actions.txt'))
        binding=read(MOD+'common/scripted_effects/des_binding_effects.txt')
        self.assertIn('name = des_cadet_main_house value = scope:des_created_house',binding)
        self.assertNotIn('des_annual_cadet_recovery_effect',binding)
        self.assertNotIn('des_annual_cadet_recovery_effect',read(MOD+'common/scripted_effects/des_maintenance_effects.txt'))

if __name__=='__main__':unittest.main()
