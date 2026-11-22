"""Actual-AST annual maintenance regression; file-only model, never engine timing or speed proof.

Reuses existing DES cadet/leadership parser and objects. No separate runner or CLI.
Set DES_ANNUAL_SOURCE (and DES_REPO for an adopted support tree) to Root's candidate.
Unsupported statements fail closed instead of being silently credited.
"""
from __future__ import annotations
from collections import Counter
import copy
import importlib.util
import os
from pathlib import Path
import sys
import unittest

REPO=Path(os.environ.get('DES_REPO',str(Path(__file__).resolve().parents[1])))
SOURCE=Path(os.environ.get('DES_ANNUAL_SOURCE',str(REPO)))
os.environ['DES_CADET_SOURCE']=str(SOURCE)
spec=importlib.util.spec_from_file_location('des_annual_existing_leadership',REPO/'tools/test_des_religious_house_leadership.py')
l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
b=l.b
MOD=b.MOD


class AnnualPolicy(l.LeadershipPolicy):
    """Only actual primitives used by these DES maintenance/pair scripts are modeled."""
    def __init__(self):
        super().__init__()
        for relative in ('des_initialization_effects.txt','des_maintenance_effects.txt','des_character_effects.txt','des_crime_effects.txt'):
            self.effects.update({r['key']:r['value'] for r in b.ast(b.read(MOD+'common/scripted_effects/'+relative))})
        self.global_root=b.Obj('global','world')
        self.religions=[]
        self.root=None
        self.params=[]
        self.depth=0
        self.trace=[]
        self.count=Counter()
        self.opinions=set()
        self.opinion_adds=[]
        self.opinion_removes=[]
        self.scheduled=[]
        self.day=0
        self.before_pair=None
        self.snapshot_hook=None

    def expand(self,text):
        if not isinstance(text,str):return text
        for values in reversed(self.params):
            for key,value in values.items():text=text.replace('$'+key+'$',value)
        if '$' in text:raise AssertionError('Unbound actual AST parameter '+text)
        return text

    def ref(self,text,current,prev=None):
        text=self.expand(text)
        if text=='yes':return True
        if text=='no':return False
        if text=='current_date':return self.day
        if text.startswith('doctrine:'):return sys.intern(text.removeprefix('doctrine:'))
        if text.startswith('root.'):
            value=self.root
            for part in text[5:].split('.'):value=self.attr(value,part)
            return value
        if text=='root':return self.root
        if text.startswith('global_var:'):
            first,*parts=text.split('.')
            value=self.globals.get(first[11:])
            for part in parts:value=self.attr(value,part)
            return value
        return super().ref(text,current,prev)

    def attr(self,obj,name):
        # Absent references in predicates are false DATA, never a writable scope.
        return None if obj is None else super().attr(obj,name)

    def condition(self,rows,current,prev=None):
        if current is None:return False
        results=[];previous_if=None
        for row in rows:
            key,value=row['key'],row['value']
            if key in ('AND','OR','NOT','NOR','NAND'):
                terms=[self.condition([r],current,prev) for r in value]
                ok=all(terms) if key=='AND' else any(terms) if key=='OR' else not all(terms) if key=='NAND' else not any(terms)
            elif key=='trigger_if':
                previous_if=self.condition(b.body(value,'limit'),current,prev)
                ok=not previous_if or self.condition([r for r in value if r['key']!='limit'],current,prev)
            elif key=='trigger_else':
                if previous_if is None:raise AssertionError('Unpaired trigger_else')
                ok=previous_if or self.condition(value,current,prev)
            elif key=='has_global_variable':ok=self.expand(value) in self.globals
            elif key=='has_global_variable_list':ok=bool(self.global_lists.get(self.expand(value),[]))
            elif key=='has_variable_list':ok=bool(current.variables.get(self.expand(value),[]))
            elif key in ('is_target_in_global_variable_list','is_target_in_variable_list'):
                name=self.expand(b.body(value,'name'));target=self.ref(b.body(value,'target'),current,prev)
                container=self.global_lists if key=='is_target_in_global_variable_list' else current.variables
                ok=target in container.get(name,[])
            elif key=='knows_doctrine':ok=self.expand(value).removeprefix('doctrine:') in current.known
            elif key=='is_playable_character':ok=current.playable==(value=='yes')
            elif key=='has_trait':ok=self.expand(value) in current.traits
            elif key in self.triggers:
                params={} if not isinstance(value,list) else {r['key']:self.expand(r['value']) for r in value}
                self.params.append(params)
                try:actual=self.condition(self.triggers[key],current,prev)
                finally:self.params.pop()
                ok=actual if isinstance(value,list) else actual==(value=='yes')
            else:
                # Existing identity/AI/alive/Rite/exists and nested scope semantics.
                ok=b.Policy.condition(self,[row],current,prev)
            results.append(ok)
        return all(results)

    def run(self,key,current,parameters=None):
        outer=self.depth==0
        if outer:self.root=current
        self.depth+=1;self.params.append(parameters or {})
        self.trace.append((key,current.name));self.count['calls:'+key]+=1
        try:
            if key in ('des_repair_rite_binding_effect','des_ensure_own_rite_binding_effect'):
                rite=current if current.kind=='rite' else current.rite
                if 'des_doctrine_none' in rite.doctrines and 'des_doctrine_dynastic' not in rite.doctrines:return
                if not self.condition(self.triggers['des_has_active_binding_trigger'],rite):
                    raise AssertionError('Model boundary cannot invent/repair a binding')
                return
            if key=='des_ensure_pair_effect' and self.before_pair:self.before_pair(self,current)
            self.execute(self.effects[key],current)
        finally:self.params.pop();self.depth-=1

    def action(self,name,current):
        outer=self.depth==0
        if outer:self.root=current
        self.depth+=1;self.trace.append(('action:'+name,current.name))
        try:
            rows=self.actions[name]
            # Whole actual action composition, rather than manually calling three phases.
            for child in [r for r in rows if r['key']=='on_actions']:
                for entry in child['value']:self.action(entry['value'],current)
            for effect in [r for r in rows if r['key']=='effect']:self.execute(effect['value'],current)
        finally:self.depth-=1

    def execute(self,rows,current):
        if current is None:raise AssertionError('Actual effect attempted an absent scope')
        last=None
        for row in rows:
            key,value=row['key'],row['value']
            if key in ('limit','variable'):continue
            if key=='if':
                last=self.condition(b.body(value,'limit'),current)
                if last:self.execute([r for r in value if r['key']!='limit'],current)
            elif key in ('else','else_if'):
                if last is None:raise AssertionError('Unpaired actual else')
                admitted=not last and (key=='else' or self.condition(b.body(value,'limit'),current))
                if admitted:self.execute([r for r in value if r['key']!='limit'],current)
                last=last or admitted
            elif key=='set_global_variable':self.globals[self.expand(b.body(value,'name'))]=self.ref(b.body(value,'value'),current)
            elif key=='remove_global_variable':self.globals.pop(self.expand(value),None)
            elif key=='clear_global_variable_list':self.global_lists[self.expand(value)]=[]
            elif key in ('add_to_global_variable_list','add_to_variable_list'):
                name=self.expand(b.body(value,'name'));target=self.ref(b.body(value,'target'),current)
                (self.global_lists if key=='add_to_global_variable_list' else current.variables).setdefault(name,[]).append(target)
            elif key in ('remove_list_global_variable','remove_list_variable'):
                name=self.expand(b.body(value,'name'));target=self.ref(b.body(value,'target'),current)
                container=self.global_lists if key=='remove_list_global_variable' else current.variables
                container[name]=[v for v in container.get(name,[]) if v is not target]
            elif key.startswith('every_'):
                name=None
                if key=='every_religion_global':members=self.religions
                elif key=='every_faith':members=current.faiths
                elif key=='every_faith_rite':members=current.rites
                elif key=='every_faith_character':members=current.characters
                elif key=='every_dynasty_member':members=current.members
                elif key=='every_dynasty_house':members=current.houses
                elif key in ('every_in_list','every_in_global_list'):
                    name=self.expand(b.body(value,'variable'))
                    members=(self.global_lists if key=='every_in_global_list' else current.variables).get(name,[])
                else:raise AssertionError('Unsupported actual iterator '+key)
                self.count['enum:'+key]+=1
                self.count['enum:'+key+':'+current.name]+=1
                snapshot=list(members);self.count['candidate:'+key]+=len(snapshot)
                if self.snapshot_hook:self.snapshot_hook(self,key,current,snapshot)
                for target in snapshot:
                    limits=[r['value'] for r in value if r['key']=='limit']
                    if not limits or self.condition(limits[0],target):self.execute([r for r in value if r['key'] not in ('limit','variable')],target)
            elif key=='trigger_event':self.scheduled.append((self.day+int(b.body(value,'days')),current,copy.deepcopy(value)))
            elif key in ('add_trait','remove_trait'):
                if key=='add_trait':current.traits.add(self.expand(value))
                else:current.traits.discard(self.expand(value))
            elif key=='add_known_doctrine':
                current.known.add(self.expand(value).removeprefix('doctrine:'));self.count['knowledge_writes']+=1
            elif key=='add_rite_doctrine':current.doctrines.add(self.expand(value))
            elif key in ('add_opinion','remove_opinion'):
                target=self.ref(b.body(value,'target'),current);pair=(current,target,self.expand(b.body(value,'modifier')))
                if key=='add_opinion':self.opinions.add(pair);self.opinion_adds.append(pair)
                else:self.opinions.discard(pair);self.opinion_removes.append(pair)
            elif key in self.effects or key in ('des_repair_rite_binding_effect','des_ensure_own_rite_binding_effect'):
                params={} if not isinstance(value,list) else {r['key']:self.expand(r['value']) for r in value}
                self.run(key,current,params)
            elif key=='debug_log':pass
            elif key in ('save_scope_as','clear_saved_scope','set_variable','remove_variable','clear_variable_list','set_house','set_house_head'):
                # Existing tested snapshot/identity/write semantics, not a second implementation.
                super().execute([row],current)
            elif isinstance(value,list):self.execute(value,self.ref(key,current))
            else:raise AssertionError('Unsupported actual annual primitive '+str(key))


def character(name,rite,house,*,ai=True,alive=True,playable=True):
    actor=b.Obj('character',name,ai=ai,alive=alive,dynasty=house.dynasty,house=house)
    actor.rite=rite;actor.faith=rite.faith;actor.playable=playable;actor.known=set();actor.traits=set();actor.age=30
    house.dynasty.members.append(actor);rite.faith.characters.append(actor)
    return actor


def fixture(member_count=4):
    policy=AnnualPolicy()
    faith=b.Obj('faith','faith');faith.characters=[];faith.rites=[]
    religion=b.Obj('religion','persistent');religion.faiths=[faith];policy.religions=[religion]
    founder=b.Obj('character','historic-founder')
    dynasty=b.Obj('dynasty','bound',founder=founder)
    main=b.Obj('house','main',dynasty=dynasty,founder=founder)
    cadet=b.Obj('house','cadet',dynasty=dynasty,founder=b.Obj('character','cadet-founder'));dynasty.houses=[main,cadet]
    rite=b.Obj('rite','bound-rite',doctrines={'des_doctrine_dynastic'});rite.faith=faith;faith.rites=[rite]
    rite.variables={'des_bound_dynasty':dynasty,'des_join_house':main,'des_binding_mode':sys.intern('flag:new_dynasty')}
    dynasty.variables={'des_bound_rite':rite,'des_cadet_main_house':main}
    head=character('head',rite,cadet);rite.head_of_rite=head;main.house_head=founder;cadet.house_head=head
    player=character('player',rite,cadet,ai=False)
    child=character('child',rite,cadet,playable=False);child.age=5
    dead=character('dead',rite,cadet,alive=False)
    extra=[character('ai'+str(i),rite,cadet) for i in range(max(0,member_count-4))]
    for a in [head,player,child,*extra]:a.variables['des_adopted_bound_rite']=rite
    policy.global_lists['des_bound_rites']=[rite]
    return policy,rite,dynasty,main,cadet,head,player,child,dead


class AnnualMaintenanceTest(unittest.TestCase):
    def test_legacy_monthly_callback_drains_without_work_reschedule_or_new_annual_state_loss(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        p.globals['des_maintenance_queued']=True
        sentinel=object();p.globals['unrelated_annual_state']=sentinel
        before={id(a):(a.house,dict(a.variables)) for a in d.members}
        # Explicit oldSave DATA: the real new handler must drain both inherited
        # due callbacks without adding another event or doing heavy work.
        old_payload=[{'key':'on_action','value':'des_monthly_maintenance'},{'key':'days','value':'30'}]
        p.scheduled=[(30,p.religions[0],copy.deepcopy(old_payload)),(30,p.religions[0],copy.deepcopy(old_payload))]
        for _ in range(2):
            due,current,payload=p.scheduled.pop(0);p.day=due;p.action(b.body(payload,'on_action'),current)
        self.assertNotIn('des_maintenance_queued',p.globals)
        self.assertEqual([],p.scheduled)
        self.assertEqual(0,p.count['calls:des_maintenance_effect'])
        self.assertEqual(before,{id(a):(a.house,dict(a.variables)) for a in d.members})
        self.assertIs(p.globals['unrelated_annual_state'],sentinel)
        p.run('des_ensure_maintenance_effect',p.religions[0]);self.assertEqual([],p.scheduled)

    def test_yearly_composition_executes_one_maintenance_then_living_return_then_head(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        p.action('yearly_global_pulse',p.global_root)
        self.assertEqual(1,p.count['calls:des_maintenance_effect'])
        self.assertIs(player.house,h);self.assertIs(child.house,h);self.assertIs(head.house,h);self.assertIs(dead.house,c)
        self.assertIs(h.house_head,head);self.assertIs(d.variables['des_cadet_main_house'],h)
        names=[x[0] for x in p.trace]
        self.assertLess(names.index('des_maintenance_effect'),names.index('des_annual_cadet_recovery_effect'))
        self.assertLess(names.index('des_annual_cadet_recovery_effect'),max(i for i,n in enumerate(names) if n==l.SYNC))
        old=p.count['calls:des_maintenance_effect'];p.day+=365;p.action('yearly_global_pulse',p.global_root)
        self.assertEqual(old+1,p.count['calls:des_maintenance_effect']) # distinct later pulse, not permanent skip.
        self.assertEqual([],p.scheduled)

    def test_stable_pardoned_pair_is_not_reissued_when_annual_refresh_finds_missing_opinion(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith;other.head_of_rite=None;r.faith.rites.append(other)
        target=character('apostate',other,c);target.variables['des_adopted_bound_rite']=r
        p.run('des_refresh_apostasy_effect',target)
        self.assertIn(target,head.variables['des_penalty_targets'])
        pair=(head,target,'des_apostasy_opinion');self.assertIn(pair,p.opinions)
        p.opinions.remove(pair);count=len(p.opinion_adds)
        p.run('des_maintenance_effect',p.global_root)
        self.assertNotIn(pair,p.opinions)
        self.assertEqual(count,len(p.opinion_adds))

    def test_immediate_apostasy_and_return_update_real_pairs_without_waiting_for_annual(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith;r.faith.rites.append(other)
        player.rite=other
        p.action('des_on_rite_change',player)
        self.assertIn('des_apostate',player.traits);self.assertIn((head,player,'des_apostasy_opinion'),p.opinions)
        self.assertEqual(0,p.count['calls:des_maintenance_effect'])
        player.rite=r;p.action('des_on_rite_change',player)
        self.assertNotIn('des_apostate',player.traits);self.assertNotIn((head,player,'des_apostasy_opinion'),p.opinions)

    def test_knowledge_eligibility_keeps_ai_player_and_children_separate_from_membership(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        playable_child=character('playable-child-player',r,c,ai=False,playable=True);playable_child.age=5
        for actor in (head,player,child,playable_child,dead):p.run('des_teach_doctrines_effect',actor)
        expected={'des_doctrine_none','des_doctrine_dynastic'}
        self.assertEqual(expected,head.known);self.assertEqual(expected,player.known);self.assertEqual(expected,playable_child.known)
        self.assertEqual(set(),child.known);self.assertEqual(set(),dead.known)
        p.action('yearly_global_pulse',p.global_root);self.assertIs(child.house,h);self.assertIs(dead.house,c)

    def test_birth_knowledge_precedes_delayed_house_finalization_and_no_full_scan(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        p.action('des_on_character_finalization',child)
        self.assertEqual(1,len(p.scheduled));due,current,payload=p.scheduled.pop()
        self.assertEqual(1,due);self.assertIs(child,current)
        # Actual stock may assign/change House later in the birth chain.
        child.house=h;p.day=due;p.action(b.body(payload,'on_action'),child)
        self.assertIs(child.house,h);self.assertEqual(0,p.count['calls:des_maintenance_effect'])
        self.assertEqual(0,p.count['enum:every_dynasty_member'])

    def test_death_cleans_outgoing_pairs_and_never_resurrects_membership(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith;player.rite=other
        p.run('des_refresh_apostasy_effect',player)
        self.assertIn(player,head.variables['des_penalty_targets'])
        p.action('des_on_death',head);head.alive=False
        self.assertNotIn((head,player,'des_apostasy_opinion'),p.opinions)
        self.assertNotIn(head,player.variables.get('des_observers',[]))
        before=head.house;p.action('yearly_global_pulse',p.global_root);self.assertIs(head.house,before)

    def test_dead_apostate_target_clears_incoming_indexes_immediately_and_keeps_other_opinion(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith;player.rite=other
        p.run('des_refresh_apostasy_effect',player)
        self.assertIn(player,p.global_lists['des_apostates'])
        foreign=(head,player,'other_product_opinion');p.opinions.add(foreign)
        identity=(player.dynasty,player.house,player.rite,player.faith)
        scans=p.count['enum:every_faith_character'];fanouts=p.count['calls:des_sync_apostate_pairs_effect']
        player.alive=False;p.action('des_on_death',player)
        self.assertNotIn(player,p.global_lists['des_apostates']);self.assertNotIn(player,r.variables.get('des_apostates',[]))
        self.assertEqual([],player.variables.get('des_observers',[]))
        self.assertNotIn('des_apostate_rite',player.variables);self.assertNotIn('des_apostate',player.traits)
        self.assertFalse(any(target is player and modifier=='des_apostasy_opinion' for _,target,modifier in p.opinions))
        self.assertIn(foreign,p.opinions)
        self.assertEqual(identity,(player.dynasty,player.house,player.rite,player.faith))
        self.assertEqual(scans,p.count['enum:every_faith_character'])
        self.assertEqual(fanouts,p.count['calls:des_sync_apostate_pairs_effect'])

    def test_bulk_join_phase_finishes_before_any_pair_evaluation(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        outsider=b.Obj('dynasty','old');old_house=b.Obj('house','old',dynasty=outsider)
        actor=character('adopter',r,old_house);actor.variables['des_adopted_bound_rite']=r
        def require_all_adopted(policy,observer):
            for a in r.faith.characters:
                if a.alive and a.rite is r:self.assertIs(a.dynasty,d,'Pair evaluation ran before complete same-Rite Join phase')
        p.before_pair=require_all_adopted
        # Existing apostate makes the pair phase observable.
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith
        target=character('apostate',other,c);target.variables['des_adopted_bound_rite']=r
        p.run('des_maintenance_effect',p.global_root)
        self.assertIs(actor.dynasty,d);self.assertIn((head,target,'des_apostasy_opinion'),p.opinions)

    def test_membership_snapshot_is_once_per_bound_dynasty_and_survives_mutation(self):
        p,r,d,h,c,head,player,child,dead=fixture(32)
        original=tuple(d.members)
        faith2=b.Obj('faith','second-faith');faith2.characters=[];faith2.rites=[]
        d2=b.Obj('dynasty','second-dynasty',founder=b.Obj('character','second-founder'))
        h2=b.Obj('house','second-main',dynasty=d2,founder=d2.founder);d2.houses=[h2]
        r2=b.Obj('rite','second-rite',doctrines={'des_doctrine_dynastic'});r2.faith=faith2;r2.head_of_rite=None
        r2.variables={'des_bound_dynasty':d2,'des_join_house':h2,'des_binding_mode':sys.intern('flag:native_dynast_reuse')}
        d2.variables={'des_bound_rite':r2,'des_cadet_main_house':h2};faith2.rites=[r2]
        p.religions[0].faiths.append(faith2);p.global_lists['des_bound_rites'].append(r2)
        victim=d.members[-1];r.faith.characters.remove(victim);faith2.characters.append(victim);victim.rite=r2;victim.faith=faith2
        seen=[]
        def hook(policy,key,current,snapshot):
            if key=='every_dynasty_member' and current is d:seen.append(tuple(snapshot))
        p.snapshot_hook=hook
        p.run('des_maintenance_effect',p.global_root)
        self.assertEqual(1,p.count['enum:every_dynasty_member:'+d.name])
        self.assertEqual(1,p.count['enum:every_dynasty_member:'+d2.name])
        self.assertEqual(set(original),set(seen[0]))
        self.assertIs(victim.dynasty,d2);self.assertIs(victim.house,h2)
        self.assertNotIn(victim,d.members);self.assertIn(victim,d2.members)

    def test_stable_bulk_fanout_is_one_observer_apostate_pass_not_repeated_target_faith_scans(self):
        p,r,d,h,c,head,player,child,dead=fixture(16)
        other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith
        targets=[character('apostate'+str(i),other,c) for i in range(3)]
        for target in targets:target.variables['des_adopted_bound_rite']=r
        p.run('des_maintenance_effect',p.global_root)
        eligible=[a for a in r.faith.characters if a.alive and a.rite is r]
        self.assertEqual(len(eligible)*len(targets),p.count['calls:des_ensure_pair_effect'])
        # Cost evidence separates required edges from underlying full-Faith enumerations.
        self.assertLessEqual(p.count['enum:every_faith_character'],3)
        before=len(p.opinion_adds);p.run('des_maintenance_effect',p.global_root)
        self.assertEqual(before,len(p.opinion_adds))

    def test_late_conversion_after_batch_is_not_skipped_by_persistent_processed_cache(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        p.run('des_maintenance_effect',p.global_root)
        other=b.Obj('rite','after-batch-other',doctrines={'des_doctrine_none'});other.faith=r.faith;player.rite=other
        p.action('des_on_rite_change',player)
        self.assertIn('des_apostate',player.traits);self.assertIn((head,player,'des_apostasy_opinion'),p.opinions)

    def test_later_title_gain_teaches_newly_playable_child_even_outside_des_bound_rites(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        ordinary=b.Obj('rite','ordinary-none',doctrines={'des_doctrine_none'});ordinary.faith=r.faith;ordinary.head_of_rite=None
        actor=character('later-playable-child',ordinary,c,playable=False);actor.age=5
        p.run('des_teach_doctrines_effect',actor);self.assertEqual(set(),actor.known)
        p.action('des_on_religious_head_title_gain',actor);self.assertEqual(set(),actor.known)
        actor.playable=True;actor.ruler=True
        p.action('des_on_religious_head_title_gain',actor)
        self.assertEqual({'des_doctrine_none','des_doctrine_dynastic'},actor.known)
        writes=p.count['knowledge_writes'];p.action('des_on_religious_head_title_gain',actor)
        self.assertEqual(writes,p.count['knowledge_writes'])
        self.assertEqual(0,p.count['calls:des_maintenance_effect'])
        self.assertEqual(0,p.count['enum:every_dynasty_member'])

    def test_unbound_none_rite_update_does_not_scan_its_faith_or_whole_dynasty(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        ordinary=b.Obj('rite','ordinary-none',doctrines={'des_doctrine_none'});ordinary.faith=r.faith;ordinary.head_of_rite=None
        p.run('des_sync_rite_effect',ordinary)
        self.assertEqual(0,p.count['enum:every_faith_character'])
        self.assertEqual(0,p.count['enum:every_dynasty_member'])
        self.assertEqual([],p.writes);self.assertEqual([],p.head_writes)

    def test_scaled_member_enumeration_is_linear_while_required_pair_work_is_counted_separately(self):
        for n in (16,64,256):
            with self.subTest(members=n):
                p,r,d,h,c,head,player,child,dead=fixture(n)
                other=b.Obj('rite','other',doctrines={'des_doctrine_none'});other.faith=r.faith
                for i in range(3):character('apostate'+str(i),other,c).variables['des_adopted_bound_rite']=r
                p.run('des_maintenance_effect',p.global_root)
                self.assertEqual(1,p.count['enum:every_dynasty_member:'+d.name])
                self.assertEqual(n+3,p.count['candidate:every_dynasty_member'])
                self.assertEqual((n-1)*3,p.count['calls:des_ensure_pair_effect'])
                self.assertLessEqual(p.count['enum:every_faith_character'],3)

    def test_annual_bulk_does_not_consume_or_rewrite_a_native_claim(self):
        p,r,d,h,c,head,player,child,dead=fixture()
        opaque=object();r.variables['des_native_head_claim_pending']=opaque
        p.action('yearly_global_pulse',p.global_root)
        self.assertIs(r.variables['des_native_head_claim_pending'],opaque)
        self.assertEqual(0,p.count['calls:des_finalize_native_rite_head_claim_effect'])


if __name__=='__main__':unittest.main()
