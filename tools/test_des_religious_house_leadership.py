"""Execute the actual DES0.2.4 leadership AST with explicit engine boundaries.

File-only regression: does not qualify CK3 scheduling, House/Dynast setters, Save
or engine recomputation. House-head writes NEVER silently set the model Dynast.
Tests requiring a successful recomputation install an independent observation
callback, and tests without it must retain pending until both actual fields agree.
"""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from collections import Counter

REPO=Path(os.environ.get('DES_REPO','D:/workspace/ck3_eternal_recurrence'))
spec=importlib.util.spec_from_file_location('des_cadet_original_test_support',REPO/'tools/test_des_cadet_policy.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
b.Obj.__repr__=lambda self:'Obj('+self.kind+':'+self.name+')'
MOD=b.MOD
NEW_EFFECTS='common/scripted_effects/des_leadership_effects.txt'
NEW_TRIGGERS='common/scripted_triggers/des_leadership_triggers.txt'
SYNC='des_sync_created_dynasty_leadership_effect'
TARGET='des_created_dynasty_leadership_target_trigger'
LOADED='des_reconcile_loaded_leadership_024_effect'

class LeadershipPolicy(b.Policy):
    def __init__(self):
        super().__init__()
        self.triggers.update({r['key']:r['value'] for r in b.ast(b.read(MOD+NEW_TRIGGERS))})
        self.effects.update({r['key']:r['value'] for r in b.ast(b.read(MOD+NEW_EFFECTS))})
        if LOADED not in self.effects:raise ValueError('This test requires actual DES0.2.4 candidate Source, not the old0.2.3 product')
        self.effects['des_join_rite_dynasty_effect']=b.definition('common/scripted_effects/des_character_effects.txt','des_join_rite_dynasty_effect')
        self.effects['des_initialize_loaded_game_effect']=b.definition('common/scripted_effects/des_initialization_effects.txt','des_initialize_loaded_game_effect')
        self.actions={r['key']:r['value'] for r in b.ast(b.read(MOD+'common/on_action/des_on_actions.txt'))}
        self.actions.update({r['key']:r['value'] for r in b.ast(b.read(MOD+'common/on_action/des_cadet_on_actions.txt'))})
        self.globals={'des_initialized':True,'des_procreation_preset_023_checked':True}
        self.global_lists={};self.religions=[];self.fixed_rites={}
        self.head_writes=[];self.boundaries=[];self.events=[];self.stats=Counter();self.calls=Counter()
        self.after_adoption=None;self.before_head_set=None;self.after_head_set_observation=None
        self.suppress_head_set=False
        self.refresh_witnesses=[];self.force_refresh_observation=None
    def ref(self,text,current,prev=None):
        if text.startswith('flag:'):return sys.intern(text)
        if text.startswith('rite:'):return self.fixed_rites.get(text[5:])
        if text.startswith('global_var:'):return self.globals.get(text[11:])
        return super().ref(text,current,prev)
    def condition(self,rows,current,prev=None):
        # Only ordinary boolean/scoped clauses of these actual policy files.
        # No permissive unknown-operator fallback; guard scopes precede use.
        previous_trigger=False
        for row in rows:
            key,value=row['key'],row['value']
            if key=='has_global_variable':ok=value in self.globals
            elif key in ('AND','OR','NOT','NOR','NAND'):
                operands=lambda:(self.condition([r],current,prev) for r in value)
                ok=all(operands()) if key=='AND' else any(operands()) if key=='OR' else not any(operands()) if key=='NOR' else not all(operands())
            elif key=='trigger_if':
                passed=self.condition(b.body(value,'limit'),current,prev);previous_trigger=passed
                ok=not passed or self.condition([r for r in value if r['key']!='limit'],current,prev)
            elif key=='trigger_else':ok=previous_trigger or self.condition(value,current,prev)
            elif key=='any_dynasty_member':
                ok=False
                for actor in current.members:
                    self.stats['any_dynasty_member_visits']+=1
                    if self.condition(value,actor,current):ok=True;break
            else:ok=super().condition([row],current,prev)
            if not ok:return False
        return True
    def action(self,name,current):
        self.calls['on_action:'+name]+=1
        self.execute(b.body(self.actions[name],'effect'),current)
    def run(self,name,current):
        self.calls[name]+=1
        self.execute(self.effects[name],current)
    def register(self,rites):
        faiths=[]
        for rite in rites:
            faith=rite.faith
            if not hasattr(faith,'rites'):faith.rites=[]
            if rite not in faith.rites:faith.rites.append(rite)
            if faith not in faiths:faiths.append(faith)
        religion=b.Obj('religion','test religion');religion.faiths=faiths;self.religions=[religion]
        self.global_lists['des_bound_rites']=list(rites)
    def execute(self,rows,current):
        last=None;i=0
        while i<len(rows):
            row=rows[i];i+=1;key,value=row['key'],row['value']
            if key in ('limit','variable'):continue
            if key is None:
                # Existing parser represents `scope:house ?= {...}` as these
                # TWO real AST rows. Interpret exactly that optional scope pair.
                if i>=len(rows) or rows[i]['key']!='?' or not isinstance(rows[i]['value'],list):raise ValueError('Unsupported anonymous effect token '+str(value))
                body=rows[i]['value'];i+=1
                if self.exists(value,current,None):self.execute(body,self.ref(value,current))
            elif key=='if':
                last=self.condition(b.body(value,'limit'),current)
                if last:self.execute([r for r in value if r['key']!='limit'],current)
            elif key=='else_if':
                if last is None:raise ValueError('else_if without actual if')
                if not last:
                    matched=self.condition(b.body(value,'limit'),current)
                    if matched:self.execute([r for r in value if r['key']!='limit'],current)
                    last=matched
            elif key=='else':
                if last is None:raise ValueError('else without actual if')
                if not last:self.execute(value,current)
                last=True
            elif key=='save_scope_as':self.scopes[value]=current
            elif key=='clear_saved_scope':self.scopes.pop(value,None)
            elif key in ('set_variable','set_global_variable'):
                target=self.globals if key=='set_global_variable' else current.variables
                target[b.body(value,'name')]=True if b.body(value,'value')=='yes' else self.ref(b.body(value,'value'),current)
            elif key=='remove_variable':current.variables.pop(value,None)
            elif key=='clear_variable_list':current.variables[value]=[]
            elif key=='add_to_variable_list':
                target=self.ref(b.body(value,'target'),current);current.variables.setdefault(b.body(value,'name'),[]).append(target);self.collected.append(target)
            elif key in ('every_dynasty_house','every_dynasty_member','every_in_list','every_in_global_list','every_religion_global','every_faith','every_faith_rite'):
                if key=='every_in_list' and self.before_move_hook:
                    callback=self.before_move_hook;self.before_move_hook=None;callback()
                members=(current.houses if key=='every_dynasty_house' else current.members if key=='every_dynasty_member'
                    else current.variables[b.body(value,'variable')] if key=='every_in_list' else self.global_lists[b.body(value,'variable')] if key=='every_in_global_list'
                    else self.religions if key=='every_religion_global' else current.faiths if key=='every_faith' else current.rites)
                self.stats['iterator_calls:'+key]+=1
                for target in list(members):
                    self.stats['iterator_visits:'+key]+=1
                    limits=[r['value'] for r in value if r['key']=='limit']
                    if not limits or self.condition(limits[0],target):self.execute([r for r in value if r['key'] not in ('limit','variable')],target)
            elif key=='set_house':
                target=self.ref(value,current);old=current.dynasty;current.house=target;current.dynasty=target.dynasty
                if old is not current.dynasty:
                    if old is not None and current in old.members:old.members.remove(current)
                    if current not in current.dynasty.members:current.dynasty.members.append(current)
                self.writes.append((current,target))
            elif key=='set_house_head':
                target=self.ref(value,current);self.head_writes.append((current,target))
                if self.before_head_set:
                    callback=self.before_head_set;self.before_head_set=None;callback()
                if not self.suppress_head_set:current.house_head=target
                # Independent TEST observation only, never a default setter side
                # effect. Real engine Dynast recomputation remains unqualified.
                if self.after_head_set_observation:self.after_head_set_observation(current,target)
            elif key=='force_refresh_head_of_rite':
                # Explicit engine boundary: requests do not invent a head.
                self.refresh_witnesses.append(current)
                if self.force_refresh_observation:self.force_refresh_observation(current)
            elif key=='trigger_event':self.events.append((current,b.body(value,'on_action'),b.body(value,'days')))
            elif key=='des_snapshot_relationships_effect':
                # Explicit existing relationship boundary, using this fixture's
                # actual empty/nonempty outgoing list, not a world/member sweep.
                self.boundaries.append((key,current))
                current.variables['des_relationship_snapshot']=list(current.variables.get('des_penalty_targets',[]))
            elif key in ('des_teach_doctrines_effect','des_ensure_own_rite_binding_effect','des_repair_rite_binding_effect','des_reconcile_procreation_preset_023_effect','des_initialize_world_effect','des_maintenance_effect','des_clear_apostasy_effect','des_sync_character_effect'):
                self.boundaries.append((key,current))
                if key=='des_ensure_own_rite_binding_effect' and not self.condition(self.triggers['des_has_active_binding_trigger'],current.rite):raise ValueError('No model-invented new binding authority')
            elif key=='des_join_rite_dynasty_effect':
                self.run(key,current)
                if self.after_adoption:
                    callback=self.after_adoption;self.after_adoption=None;callback()
            elif key=='des_sync_rite_effect':self.boundaries.append((key,current));self.run(SYNC,current)
            elif key=='debug_log':pass
            elif key in self.effects:self.run(key,current)
            elif isinstance(value,list):self.execute(value,self.ref(key,current))
            else:raise ValueError('Unexpected leadership Source effect '+str(key))

def world(mode='flag:new_dynasty'):
    d,r,h,c,ai,p,old=b.world();faith=b.Obj('faith','own faith');faith.rites=[r];r.faith=faith
    r.variables['des_join_house']=h
    if mode is not None:r.variables['des_binding_mode']=sys.intern(mode)
    d.variables['des_cadet_main_house']=h;d.dynast=old;h.house_head=old
    head=b.Obj('character','actual religious head',dynasty=d,house=c);head.rite=r;head.faith=faith;r.head_of_rite=head
    for actor in (ai,p,old):actor.rite=r;actor.faith=faith
    d.members.append(head)
    return d,r,h,c,head,ai,p,old

def observe_both(policy,dynasty):
    # This callback is an explicit independent fixture observation, NOT inferred
    # CK3 behavior from set_house_head. The no-callback tests enforce pending.
    policy.after_head_set_observation=lambda house,target:setattr(dynasty,'dynast',target)

class ReligiousHouseLeadershipTest(unittest.TestCase):
    def test_house_write_alone_never_claims_dynast_success(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertTrue(h.house_head is head);self.assertTrue(d.dynast is old)
        self.assertIn('des_house_leadership_pending',r.variables)
        self.assertNotIn('des_last_religious_dynast',r.variables)
        self.assertNotIn('des_last_religious_house_head',r.variables)
    def test_only_independently_observed_both_fields_clear_pending(self):
        for mode in ('flag:new_dynasty','flag:native_dynast_reuse','flag:legacy_reciprocal_binding'):
            with self.subTest(mode=mode):
                d,r,h,c,head,ai,p,old=world(mode);policy=LeadershipPolicy();observe_both(policy,d);policy.run(SYNC,r)
                self.assertTrue(h.house_head is head and d.dynast is head)
                self.assertTrue(r.variables['des_last_religious_house_head'] is head and r.variables['des_last_religious_dynast'] is head)
                self.assertNotIn('des_house_leadership_pending',r.variables)
                self.assertEqual(mode,r.variables['des_binding_mode'])
    def test_same_head_is_not_reissued_to_fake_a_dynast_refresh(self):
        d,r,h,c,head,ai,p,old=world();h.house_head=head
        for actor in d.members:actor.house=h
        policy=LeadershipPolicy();policy.run(SYNC,r);policy.run(SYNC,r)
        self.assertEqual([],policy.head_writes);self.assertTrue(d.dynast is old)
        self.assertIn('des_house_leadership_pending',r.variables);self.assertEqual(1,len(policy.events))
    def test_new_actual_rite_head_and_reentry_are_idempotent_when_both_observed(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();observe_both(policy,d)
        policy.before_head_set=lambda:policy.run(SYNC,r);policy.run(SYNC,r)
        self.assertEqual([(h,head)],policy.head_writes)
        successor=b.Obj('character','new actual head',dynasty=d,house=c);successor.rite=r;successor.faith=r.faith;d.members.append(successor);r.head_of_rite=successor
        policy.run(SYNC,r);self.assertTrue(h.house_head is successor and d.dynast is successor)
        count=len(policy.head_writes)
        for _ in range(3):policy.run(SYNC,r)
        self.assertEqual(count,len(policy.head_writes));self.assertTrue(d.variables['des_cadet_main_house'] is h)
    def test_missing_mode_uses_reciprocal_legacy_not_fabricated_new_origin(self):
        d,r,h,c,head,ai,p,old=world(None);policy=LeadershipPolicy();observe_both(policy,d);policy.run(SYNC,r)
        self.assertEqual('flag:legacy_reciprocal_binding',r.variables['des_binding_mode'])
        self.assertNotEqual('flag:new_dynasty',r.variables['des_binding_mode'])
        d,r,h,c,head,ai,p,old=world(None);r.variables.update(des_join_house=c,des_native_source_was_dynast=True,des_native_source_dynasty=d,des_native_source_house=c)
        policy=LeadershipPolicy();observe_both(policy,d);policy.run(SYNC,r)
        self.assertEqual('flag:native_dynast_reuse',r.variables['des_binding_mode'])
        self.assertTrue(r.variables['des_join_house'] is h);self.assertTrue(d.variables['des_cadet_main_house'] is h)
    def test_native_binding_pending_and_invalid_or_ambiguous_binding_remain_safe(self):
        for change in ('binding-pending','native-pending','disabled','broken-reverse','missing-binding','foreign-main','ambiguous-anchor'):
            with self.subTest(change=change):
                d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
                if change=='binding-pending':r.variables['des_binding_in_progress']=True
                elif change=='native-pending':r.variables['des_native_head_claim_pending']=True
                elif change=='disabled':r.doctrines={'des_doctrine_none'}
                elif change=='broken-reverse':d.variables['des_bound_rite']=b.Obj('rite','different')
                elif change=='missing-binding':del r.variables['des_bound_dynasty']
                elif change=='foreign-main':h.dynasty=b.Obj('dynasty','foreign')
                else:del d.variables['des_cadet_main_house'];c.founder=d.founder
                policy.run(SYNC,r);self.assertEqual([],policy.head_writes);self.assertEqual([],policy.writes)
    def test_shared_pope_or_foreign_faith_dead_and_missing_heads_not_pulled(self):
        for change in ('other-rite','other-faith','dead','absent'):
            with self.subTest(change=change):
                d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
                if change=='other-rite':head.rite=b.Obj('rite','shared Pope own rite')
                elif change=='other-faith':head.faith=b.Obj('faith','other')
                elif change=='dead':head.alive=False
                else:r.head_of_rite=None
                policy.run(SYNC,r);self.assertEqual([],policy.head_writes);self.assertEqual([],policy.writes)
                self.assertIn('des_house_leadership_pending',r.variables)
    def test_two_rites_sharing_a_head_use_only_actual_owned_rite(self):
        d,r,h,c,head,ai,p,old=world();d2,r2,h2,c2,head2,ai2,p2,old2=world()
        r2.head_of_rite=head;r2.faith=r.faith
        policy=LeadershipPolicy();observe_both(policy,d);policy.run(SYNC,r);policy.run(SYNC,r2)
        self.assertTrue(h.house_head is head and d.dynast is head)
        self.assertTrue(h2.house_head is old2 and d2.dynast is old2);self.assertIn('des_house_leadership_pending',r2.variables)
    def test_house_and_dynast_hooks_route_affected_scope_even_cross_rite_new_head(self):
        for action,scope in (('des_on_bound_house_head_changed','house'),('des_on_bound_dynast_changed','dynasty')):
            with self.subTest(action=action):
                d,r,h,c,head,ai,p,old=world();outsider=b.Obj('character','new head other Rite',dynasty=d,house=h);outsider.rite=b.Obj('rite','unrelated');outsider.faith=b.Obj('faith','unrelated')
                policy=LeadershipPolicy();observe_both(policy,d);policy.scopes[scope]=h if scope=='house' else d
                policy.action(action,outsider);self.assertTrue(h.house_head is head and d.dynast is head)
                self.assertFalse(any(key=='des_sync_rite_effect' for key,actor in policy.boundaries))
    def test_stale_backlink_of_affected_old_dynasty_never_touches_another_dynasty(self):
        for action,scope in (('des_on_bound_house_head_changed','house'),('des_on_bound_dynast_changed','dynasty')):
            with self.subTest(action=action):
                d,r,h,c,head,ai,p,old=world();other=b.Obj('dynasty','affected old dynasty');oh=b.Obj('house','old house',dynasty=other);other.variables['des_bound_rite']=r
                policy=LeadershipPolicy();observe_both(policy,d);policy.scopes[scope]=oh if scope=='house' else other
                policy.action(action,old);self.assertEqual([],policy.head_writes);self.assertEqual(0,policy.calls[SYNC]);self.assertTrue(h.house_head is old)
    def test_missing_optional_affected_scope_or_uninitialized_hook_is_noop(self):
        for action in ('des_on_bound_house_head_changed','des_on_bound_dynast_changed'):
            d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.action(action,head);self.assertEqual([],policy.head_writes)
            policy.scopes.update(house=h,dynasty=d);del policy.globals['des_initialized'];policy.action(action,head);self.assertEqual([],policy.head_writes)
    def test_aligned_1216_member_local_paths_have_no_member_or_world_enumeration(self):
        for action,scope in ((None,None),('des_on_bound_house_head_changed','house'),('des_on_bound_dynast_changed','dynasty')):
            d,r,h,c,head,ai,p,old=world();h.house_head=d.dynast=head
            for actor in d.members:actor.house=h
            while len(d.members)<1216:
                actor=b.Obj('character','large population '+str(len(d.members)),dynasty=d,house=h);actor.rite=r;actor.faith=r.faith;d.members.append(actor)
            policy=LeadershipPolicy();policy.scopes.update(house=h,dynasty=d)
            if action:policy.action(action,old)
            else:policy.run(SYNC,r)
            self.assertEqual([],policy.head_writes);self.assertEqual([],policy.writes)
            self.assertEqual(0,policy.stats['any_dynasty_member_visits']);self.assertEqual(0,policy.stats['iterator_visits:every_dynasty_member'])
            self.assertEqual(0,policy.stats['iterator_visits:every_religion_global']);self.assertEqual(0,policy.calls['des_annual_cadet_recovery_effect'])
    def test_exceptional_dynast_mismatch_recovers_one_snapshot_including_player_cross_rite(self):
        d,r,h,c,head,ai,p,old=world();p.rite=b.Obj('rite','player other');p.faith=b.Obj('faith','player other');dead=b.Obj('character','dead branch',alive=False,dynasty=d,house=c);d.members.append(dead)
        policy=LeadershipPolicy();observe_both(policy,d);policy.run(SYNC,r)
        self.assertEqual(1,policy.calls['des_annual_cadet_recovery_effect']);self.assertEqual(1,policy.stats['iterator_calls:every_dynasty_member'])
        self.assertTrue(ai.house is h and p.house is h and head.house is h);self.assertTrue(dead.house is c)
        self.assertTrue(h.house_head is head and d.dynast is head)
    def test_dynast_aligned_never_enumerates_cadets_on_local_leadership_path(self):
        d,r,h,c,head,ai,p,old=world();d.dynast=head;policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertEqual(0,policy.stats['any_dynasty_member_visits']);self.assertEqual(0,policy.calls['des_annual_cadet_recovery_effect'])
        self.assertTrue(ai.house is c and p.house is c);self.assertTrue(h.house_head is head)
    def test_failure_and_changed_head_after_adoption_keep_pending(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.suppress_head_set=True;policy.run(SYNC,r)
        self.assertTrue(h.house_head is old and d.dynast is old);self.assertIn('des_house_leadership_pending',r.variables)
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.after_adoption=lambda:setattr(r,'head_of_rite',None);policy.run(SYNC,r)
        self.assertEqual([],policy.head_writes);self.assertTrue(h.house_head is old);self.assertIn('des_house_leadership_pending',r.variables)
        self.assertNotIn('des_leadership_sync_in_progress',r.variables)
    def test_pending_queue_is_single_and_callback_does_not_self_renew(self):
        d,r,h,c,head,ai,p,old=world();r.head_of_rite=None;policy=LeadershipPolicy()
        for _ in range(4):policy.run(SYNC,r)
        self.assertEqual([(r,'des_local_house_leadership_recheck','1')],policy.events)
        policy.action('des_local_house_leadership_recheck',r);self.assertEqual(1,len(policy.events));self.assertNotIn('des_leadership_recheck_queued',r.variables)
        self.assertIn('des_house_leadership_pending',r.variables)
    def test_already_initialized_load_has_independent024_once_gate_without_full_init(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();observe_both(policy,d);policy.register([r]);policy.fixed_rites['des_procreation_rite']=r
        gui=b.body(b.ast(b.read(MOD+'common/scripted_guis/des_saved_game_initialization.txt')),'des_saved_game_initialize_gui')
        self.assertTrue(policy.condition(b.body(gui,'is_shown'),p));policy.run('des_initialize_loaded_game_effect',p)
        self.assertTrue(policy.globals['des_initialized']);self.assertTrue(policy.globals['des_procreation_preset_023_checked']);self.assertTrue(policy.globals['des_leadership_024_checked'])
        self.assertFalse(any(key in ('des_initialize_world_effect','des_maintenance_effect') for key,actor in policy.boundaries));self.assertTrue(h.house_head is head and d.dynast is head)
        count=policy.stats['iterator_calls:every_religion_global'];writes=len(policy.head_writes)
        policy.run('des_initialize_loaded_game_effect',p);self.assertFalse(policy.condition(b.body(gui,'is_shown'),p))
        self.assertEqual(count,policy.stats['iterator_calls:every_religion_global']);self.assertEqual(writes,len(policy.head_writes))
    def test_load_marker_is_consumed_before_setter_reentry_and_unbound_rites_are_skipped(self):
        d,r,h,c,head,ai,p,old=world();unbound=b.Obj('rite','unbound',doctrines={'des_doctrine_none'});unbound.faith=r.faith
        policy=LeadershipPolicy();policy.register([r,unbound]);observe_both(policy,d)
        policy.before_head_set=lambda:policy.run(LOADED,p);policy.run(LOADED,p)
        self.assertEqual(1,policy.stats['iterator_calls:every_religion_global']);self.assertEqual([(h,head)],policy.head_writes)
        self.assertEqual(1,policy.calls['des_repair_rite_binding_effect'] if 'des_repair_rite_binding_effect' in policy.calls else sum(key=='des_repair_rite_binding_effect' for key,actor in policy.boundaries))
    def test_ast_hooks_annual_contract_and_no_fake_dynast_primitive(self):
        actions=b.ast(b.read(MOD+'common/on_action/des_on_actions.txt'))
        self.assertEqual(['des_on_bound_house_head_changed'],[x['value'] for x in b.body(b.body(actions,'on_became_house_head'),'on_actions')])
        self.assertEqual(['des_on_bound_dynast_changed'],[x['value'] for x in b.body(b.body(actions,'on_became_dynasty_head'),'on_actions')])
        pulse=b.body(b.body(actions,'yearly_global_pulse'),'on_actions');self.assertEqual(['des_annual_watchdog','des_annual_cadet_recovery','des_annual_house_leadership_recovery'],[x['value'] for x in pulse])
        effects=b.read(MOD+NEW_EFFECTS);self.assertNotIn('set_dynast =',effects);self.assertNotIn('set_dynasty_head =',effects)
        for action,scope in (('des_on_bound_house_head_changed','scope:house'),('des_on_bound_dynast_changed','scope:dynasty')):
            rows=b.body(b.body(actions,action),'effect');render=str(rows);self.assertIn(scope,render)
        gui=b.body(b.ast(b.read(MOD+'common/scripted_guis/des_saved_game_initialization.txt')),'des_saved_game_initialize_gui')
        self.assertIn('des_leadership_024_checked',str(b.body(gui,'is_shown')))
        loaded=b.definition('common/scripted_effects/des_initialization_effects.txt','des_initialize_loaded_game_effect')
        self.assertIn(LOADED,str(loaded));self.assertIn('des_reconcile_procreation_preset_023_effect',str(loaded))

    def test_non_main_title_gain_queues_one_reread_without_guessing_future_head(self):
        d,r,h,c,head,ai,p,old=world();r.head_of_rite=old;d.dynast=h.house_head=old
        policy=LeadershipPolicy();observe_both(policy,d);policy.scopes['title']=b.Obj('title','not the faith main title')
        policy.action('des_on_religious_head_title_gain',head)
        self.assertTrue(h.house_head is old and d.dynast is old);self.assertEqual([],policy.head_writes)
        self.assertEqual([(r,'des_local_house_leadership_recheck','1')],policy.events)
        # Actual own-Rite head settles after the title transaction; title itself
        # was never taken as permission or an observed head field.
        r.head_of_rite=head;policy.action('des_local_house_leadership_recheck',r)
        self.assertTrue(h.house_head is head and d.dynast is head)
        self.assertEqual(1,len(policy.events));self.assertNotIn('des_leadership_recheck_queued',r.variables)
    def test_before_death_current_or_recorded_head_queues_one_then_reads_actual_successor(self):
        for route in ('current','last-house','last-dynast','observed-head','all-records'):
            with self.subTest(route=route):
                d,r,h,c,head,ai,p,old=world();successor=old;successor.rite=r;successor.faith=r.faith
                h.house_head=d.dynast=head;head.house=h
                if route not in ('current','all-records'):r.head_of_rite=successor
                if route in ('last-house','all-records'):r.variables['des_last_religious_house_head']=head
                if route in ('last-dynast','all-records'):r.variables['des_last_religious_dynast']=head
                if route in ('observed-head','all-records'):r.variables['des_last_observed_religious_head']=head
                policy=LeadershipPolicy();observe_both(policy,d)
                policy.action('des_on_death',head)
                self.assertTrue(head.alive);self.assertEqual([],policy.head_writes)
                self.assertEqual([(r,'des_local_house_leadership_recheck','1')],policy.events)
                self.assertEqual(0,policy.stats['iterator_visits:every_dynasty_member'])
                head.alive=False;r.head_of_rite=successor
                policy.action('des_local_house_leadership_recheck',r)
                self.assertTrue(h.house_head is successor);self.assertEqual(1,len(policy.events))
    def test_nonleader_death_has_zero_leadership_queue_and_no_population_sweep(self):
        d,r,h,c,head,ai,p,old=world();r.variables.update(des_last_religious_house_head=head,des_last_religious_dynast=head)
        policy=LeadershipPolicy();policy.action('des_on_death',ai)
        self.assertEqual([],policy.events);self.assertEqual([],policy.head_writes)
        self.assertEqual(0,policy.stats['iterator_visits:every_dynasty_member']);self.assertEqual(0,policy.stats['any_dynasty_member_visits'])
    def test_rite_departure_rereads_only_matching_old_rite_not_all_rites(self):
        for was_leader in (True,False):
            with self.subTest(was_leader=was_leader):
                d,r,h,c,head,ai,p,old=world();actor=head if was_leader else ai
                other=b.Obj('rite','new ordinary rite',doctrines={'des_doctrine_none'});other.faith=b.Obj('faith','new faith');other.head_of_rite=None
                actor.rite=other;actor.faith=other.faith
                if was_leader:r.variables.update(des_last_religious_house_head=actor,des_last_religious_dynast=actor)
                policy=LeadershipPolicy();policy.scopes['old_rite']=r
                policy.action('des_on_rite_change',actor)
                self.assertEqual(1 if was_leader else 0,len(policy.events));self.assertEqual([],policy.head_writes)
                if was_leader:self.assertTrue(policy.events[0][0] is r)
                self.assertEqual(0,policy.stats['iterator_visits:every_religion_global']);self.assertEqual(0,policy.stats['iterator_visits:every_dynasty_member'])
    def test_pending_observed_head_is_only_a_witness_not_double_position_success(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertTrue(r.variables['des_last_observed_religious_head'] is head)
        self.assertTrue(h.house_head is head and d.dynast is old)
        self.assertIn('des_house_leadership_pending',r.variables)
        self.assertNotIn('des_last_religious_house_head',r.variables);self.assertNotIn('des_last_religious_dynast',r.variables)

    def _lost_lifecycle_head_for_refresh_test(self, cause):
        d,r,h,c,head,ai,p,old=world()
        h.house_head=d.dynast=head;head.house=h
        r.variables.update(des_last_observed_religious_head=head,des_last_religious_house_head=head,des_last_religious_dynast=head)
        policy=LeadershipPolicy()
        if cause=='death':
            policy.action('des_on_death',head)
            head.alive=False
        elif cause=='departure':
            other=b.Obj('rite','departed to ordinary rite',doctrines={'des_doctrine_none'});other.faith=b.Obj('faith','new ordinary faith');other.head_of_rite=None
            head.rite=other;head.faith=other.faith;policy.scopes['old_rite']=r
            policy.action('des_on_rite_change',head)
        else:raise ValueError('No caller-invented lifecycle cause')
        # Independent engine observation after the lifecycle input, before its
        # delayed callback. The script does not invent a successor here.
        r.head_of_rite=None
        return d,r,h,c,head,ai,p,old,policy

    def test_matched_missing_lifecycle_head_refreshes_once_then_reads_actual_successor(self):
        for cause in ('death','departure'):
            with self.subTest(cause=cause):
                d,r,h,c,head,ai,p,successor,policy=self._lost_lifecycle_head_for_refresh_test(cause)
                self.assertEqual([],policy.refresh_witnesses)
                policy.force_refresh_observation=lambda rite:setattr(rite,'head_of_rite',successor)
                observe_both(policy,d)
                policy.action('des_local_house_leadership_recheck',r)
                self.assertEqual([r],policy.refresh_witnesses)
                self.assertTrue(r.head_of_rite is successor and h.house_head is successor and d.dynast is successor)
                self.assertNotIn('des_house_leadership_pending',r.variables)
                self.assertEqual(1,len(policy.events));self.assertNotIn('des_leadership_recheck_queued',r.variables)

    def test_valid_owned_living_successor_never_refreshes_or_changes_the_election(self):
        for cause in ('death','departure'):
            with self.subTest(cause=cause):
                d,r,h,c,head,ai,p,successor,policy=self._lost_lifecycle_head_for_refresh_test(cause)
                r.head_of_rite=successor
                def forbidden(rite):raise AssertionError('Valid own living successor must not be re-elected')
                policy.force_refresh_observation=forbidden;observe_both(policy,d)
                policy.action('des_local_house_leadership_recheck',r)
                self.assertEqual([],policy.refresh_witnesses)
                self.assertTrue(r.head_of_rite is successor and h.house_head is successor and d.dynast is successor)

    def test_ordinary_title_and_unmatched_lifecycle_never_authorize_a_head_refresh(self):
        for cause in ('title','nonleader-death','nonleader-departure'):
            with self.subTest(cause=cause):
                d,r,h,c,head,ai,p,old=world();r.head_of_rite=None
                policy=LeadershipPolicy()
                if cause=='title':
                    policy.scopes['title']=b.Obj('title','ordinary secular title')
                    policy.action('des_on_religious_head_title_gain',ai)
                elif cause=='nonleader-death':policy.action('des_on_death',ai)
                else:
                    other=b.Obj('rite','unbound destination',doctrines={'des_doctrine_none'});other.faith=b.Obj('faith','other faith');other.head_of_rite=None
                    ai.rite=other;ai.faith=other.faith;policy.scopes['old_rite']=r
                    policy.action('des_on_rite_change',ai)
                policy.action('des_local_house_leadership_recheck',r)
                self.assertEqual([],policy.refresh_witnesses)
                self.assertIsNone(r.head_of_rite);self.assertEqual([],policy.head_writes)

    def test_lifecycle_refresh_intent_deduplicates_and_callback_cannot_self_renew(self):
        d,r,h,c,head,ai,p,old,policy=self._lost_lifecycle_head_for_refresh_test('death')
        for _ in range(4):policy.run('des_queue_matching_religious_head_recheck_effect',r)
        self.assertEqual(1,len(policy.events))
        policy.action('des_local_house_leadership_recheck',r)
        policy.action('des_local_house_leadership_recheck',r)
        self.assertEqual([r],policy.refresh_witnesses)
        self.assertEqual(1,len(policy.events));self.assertNotIn('des_leadership_recheck_queued',r.variables)
        self.assertIn('des_house_leadership_pending',r.variables)

    def test_failed_or_foreign_refresh_never_claims_dual_position_success(self):
        for observed in ('none','dead','foreign-rite','foreign-faith','own-but-dynast-unconfirmed'):
            with self.subTest(observed=observed):
                d,r,h,c,head,ai,p,successor,policy=self._lost_lifecycle_head_for_refresh_test('death')
                if observed!='none':
                    if observed=='dead':successor.alive=False
                    elif observed=='foreign-rite':successor.rite=b.Obj('rite','shared foreign Pope rite')
                    elif observed=='foreign-faith':successor.faith=b.Obj('faith','shared foreign Pope faith')
                    policy.force_refresh_observation=lambda rite:setattr(rite,'head_of_rite',successor)
                # No independent Dynast observation is installed. A house-head
                # setter or refresh request alone never proves the second field.
                policy.action('des_local_house_leadership_recheck',r)
                self.assertEqual([r],policy.refresh_witnesses)
                self.assertTrue(d.dynast is head);self.assertIn('des_house_leadership_pending',r.variables)
                self.assertTrue(r.variables['des_last_religious_house_head'] is head)
                self.assertTrue(r.variables['des_last_religious_dynast'] is head)
                if observed=='own-but-dynast-unconfirmed':self.assertTrue(h.house_head is successor)
                else:self.assertEqual([],policy.head_writes)
                self.assertEqual(1,len(policy.events));self.assertNotIn('des_leadership_recheck_queued',r.variables)


if __name__=='__main__':unittest.main()
