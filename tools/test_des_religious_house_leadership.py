"""Execute the actual small leadership AST using the existing cadet test model.

This is file-only Source regression, not engine scheduling, setter, Dynast or Save proof.
"""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

REPO=Path(os.environ.get('DES_REPO','D:/workspace/ck3_eternal_recurrence'))
spec=importlib.util.spec_from_file_location('des_cadet_original_test_support',REPO/'tools/test_des_cadet_policy.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
MOD=b.MOD
NEW_EFFECTS='common/scripted_effects/des_leadership_effects.txt'
NEW_TRIGGERS='common/scripted_triggers/des_leadership_triggers.txt'
SYNC='des_sync_created_dynasty_leadership_effect'
TARGET='des_created_dynasty_leadership_target_trigger'

class LeadershipPolicy(b.Policy):
    def __init__(self):
        super().__init__()
        self.triggers.update({r['key']:r['value'] for r in b.ast(b.read(MOD+NEW_TRIGGERS))})
        self.effects.update({r['key']:r['value'] for r in b.ast(b.read(MOD+NEW_EFFECTS))})
        # Reuse actual existing adoption statements; knowledge/binding internals
        # are explicit boundaries and receive no new qualification here.
        self.effects['des_join_rite_dynasty_effect']=b.definition('common/scripted_effects/des_character_effects.txt','des_join_rite_dynasty_effect')
        self.actions={r['key']:r['value'] for r in b.ast(b.read(MOD+'common/on_action/des_on_actions.txt'))}
        self.actions.update({r['key']:r['value'] for r in b.ast(b.read(MOD+'common/on_action/des_cadet_on_actions.txt'))})
        self.globals={'des_initialized':True}
        self.global_lists={}
        self.head_writes=[]
        self.boundaries=[]
        self.after_adoption=None
        self.before_head_set=None
        self.suppress_head_set=False
    def ref(self,text,current,prev=None):
        if text.startswith('flag:'):return sys.intern(text)
        return super().ref(text,current,prev)
    def condition(self,rows,current,prev=None):
        global_rows=[r for r in rows if r['key']=='has_global_variable']
        if global_rows:
            return all(r['value'] in self.globals for r in global_rows) and super().condition([r for r in rows if r['key']!='has_global_variable'],current,prev)
        return super().condition(rows,current,prev)
    def action(self,name,current):self.execute(b.body(self.actions[name],'effect'),current)
    def execute(self,rows,current):
        last=None
        for row in rows:
            key,value=row['key'],row['value']
            if key in ('limit','variable'):continue
            if key=='if':
                last=self.condition(b.body(value,'limit'),current)
                if last:self.execute([r for r in value if r['key']!='limit'],current)
            elif key=='else':
                if last is None:raise ValueError('else without actual if')
                if not last:self.execute(value,current)
            elif key=='save_scope_as':self.scopes[value]=current
            elif key=='clear_saved_scope':self.scopes.pop(value,None)
            elif key=='set_variable':current.variables[b.body(value,'name')]=True if b.body(value,'value')=='yes' else self.ref(b.body(value,'value'),current)
            elif key=='remove_variable':current.variables.pop(value,None)
            elif key=='clear_variable_list':current.variables[value]=[]
            elif key=='add_to_variable_list':
                target=self.ref(b.body(value,'target'),current);current.variables.setdefault(b.body(value,'name'),[]).append(target)
            elif key in ('every_dynasty_house','every_dynasty_member','every_in_list','every_in_global_list'):
                members=current.houses if key=='every_dynasty_house' else current.members if key=='every_dynasty_member' else self.global_lists[b.body(value,'variable')] if key=='every_in_global_list' else current.variables[b.body(value,'variable')]
                for target in list(members):
                    limits=[r['value'] for r in value if r['key']=='limit']
                    if not limits or self.condition(limits[0],target):self.execute([r for r in value if r['key'] not in ('limit','variable')],target)
            elif key=='set_house':
                target=self.ref(value,current)
                old=current.dynasty
                current.house=target;current.dynasty=target.dynasty
                if old is not current.dynasty:
                    if old is not None and current in old.members:old.members.remove(current)
                    if current not in current.dynasty.members:current.dynasty.members.append(current)
                self.writes.append((current,target))
            elif key=='set_house_head':
                target=self.ref(value,current)
                self.head_writes.append((current,target))
                if self.before_head_set:
                    callback=self.before_head_set;self.before_head_set=None;callback()
                if not self.suppress_head_set:current.house_head=target
            elif key in ('des_teach_doctrines_effect','des_ensure_own_rite_binding_effect'):
                self.boundaries.append((key,current))
                if key=='des_ensure_own_rite_binding_effect' and not self.condition(self.triggers['des_has_active_binding_trigger'],current.rite):
                    raise ValueError('test attempted to invent an unqualified binding at the boundary')
            elif key=='des_join_rite_dynasty_effect':
                self.execute(self.effects[key],current)
                if self.after_adoption:
                    callback=self.after_adoption;self.after_adoption=None;callback()
            elif key=='des_sync_rite_effect':
                # A full Rite sync remains an explicit model boundary. The
                # title-gain path must now avoid it and perform only leadership.
                self.boundaries.append((key,current));self.run(SYNC,current)
            elif key=='debug_log':pass
            elif key in self.effects:self.run(key,current)
            elif isinstance(value,list):self.execute(value,self.ref(key,current))
            else:raise ValueError('unexpected leadership Source effect '+str(key))

def world():
    dynasty,rite,main,cadet,ai,player,member=b.world()
    faith=b.Obj('faith','own faith')
    rite.faith=faith
    rite.variables.update(des_join_house=main,des_binding_mode=sys.intern('flag:new_dynasty'))
    dynasty.variables['des_cadet_main_house']=main
    dynasty.dynast=member
    main.house_head=member
    head=b.Obj('character','actual religious head',dynasty=dynasty,house=cadet)
    head.rite=rite;head.faith=faith
    rite.head_of_rite=head
    for actor in [ai,player,member]:actor.rite=rite;actor.faith=faith
    dynasty.members.append(head)
    return dynasty,rite,main,cadet,head,ai,player,member

class ReligiousHouseLeadershipTest(unittest.TestCase):
    def test_created_binding_follows_actual_rite_head_and_observes_house_field(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertIs(head.house,h);self.assertIs(h.house_head,head)
        self.assertIs(r.variables['des_last_religious_house_head'],head)
        self.assertNotIn('des_house_leadership_pending',r.variables)
        self.assertNotIn('des_leadership_sync_in_progress',r.variables)
        self.assertIs(d.dynast,old) # The model does not fake engine Dynast recalculation.
    def test_new_actual_religious_head_replaces_old_house_head_and_is_idempotent(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.run(SYNC,r)
        successor=b.Obj('character','new actual head',dynasty=d,house=c);successor.rite=r;successor.faith=r.faith
        d.members.append(successor);r.head_of_rite=successor
        policy.run(SYNC,r);self.assertIs(h.house_head,successor)
        count=len(policy.head_writes)
        for _ in range(3):policy.run(SYNC,r)
        self.assertEqual(count,len(policy.head_writes));self.assertIs(d.variables['des_cadet_main_house'],h)
    def test_native_reuse_of_user_old_dynasty_is_not_new_permission(self):
        d,r,h,c,head,ai,p,old=world();r.variables['des_binding_mode']=sys.intern('flag:native_dynast_reuse')
        policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertIs(head.house,c);self.assertIs(h.house_head,old)
        self.assertEqual([],policy.writes);self.assertEqual([],policy.head_writes)
    def test_original_binding_and_native_claim_pending_are_preserved_until_complete(self):
        for marker in ('des_binding_in_progress','des_native_head_claim_pending'):
            with self.subTest(marker=marker):
                d,r,h,c,head,ai,p,old=world();r.variables[marker]=True
                policy=LeadershipPolicy();policy.run(SYNC,r)
                self.assertEqual([],policy.writes);self.assertEqual([],policy.head_writes)
                self.assertTrue(r.variables[marker]);self.assertIs(h.house_head,old)
                self.assertNotIn('des_house_leadership_pending',r.variables)
                del r.variables[marker];policy.run(SYNC,r);self.assertIs(h.house_head,head)
    def test_shared_pope_or_other_faith_or_dead_head_is_never_pulled(self):
        for change in ('other-rite','other-faith','dead','absent'):
            with self.subTest(change=change):
                d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
                if change=='other-rite':head.rite=b.Obj('rite','shared Pope own rite')
                elif change=='other-faith':head.faith=b.Obj('faith','other faith')
                elif change=='dead':head.alive=False
                else:r.head_of_rite=None
                policy.run(SYNC,r)
                self.assertEqual([],policy.writes);self.assertEqual([],policy.head_writes)
                self.assertIs(h.house_head,old);self.assertIn('des_house_leadership_pending',r.variables)
    def test_disabled_missing_reverse_or_invalid_stable_anchor_does_nothing(self):
        for change in ('disabled','missing-anchor','other-dynasty-anchor','join-not-main','broken-reverse','missing-binding'):
            with self.subTest(change=change):
                d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
                if change=='disabled':r.doctrines={'des_doctrine_none'}
                elif change=='missing-anchor':del d.variables['des_cadet_main_house']
                elif change=='other-dynasty-anchor':h.dynasty=b.Obj('dynasty','unrelated')
                elif change=='join-not-main':r.variables['des_join_house']=c
                elif change=='broken-reverse':d.variables['des_bound_rite']=b.Obj('rite','other binding')
                else:del r.variables['des_bound_dynasty']
                policy.run(SYNC,r);self.assertEqual([],policy.writes);self.assertEqual([],policy.head_writes)
    def test_normal_adoption_can_move_same_rite_head_without_deleting_old_dynasty(self):
        d,r,h,c,head,ai,p,old=world();foreign=b.Obj('dynasty','old dynasty');old_house=b.Obj('house','old house',dynasty=foreign)
        head.dynasty=foreign;head.house=old_house;d.members.remove(head);foreign.members=[head]
        policy=LeadershipPolicy();policy.run(SYNC,r)
        self.assertIs(head.dynasty,d);self.assertIs(head.house,h);self.assertIs(h.house_head,head)
        self.assertEqual('old dynasty',foreign.name);self.assertIs(old_house.dynasty,foreign)
        self.assertFalse(any(key=='des_ensure_own_rite_binding_effect' for key,actor in policy.boundaries))
        # The existing active binding is sufficient; adoption does not rediscover it.
        self.assertIs(d.variables['des_bound_rite'],r)
    def test_reentrancy_and_changed_head_after_adoption_do_not_set_stale_head(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.before_head_set=lambda:policy.run(SYNC,r)
        policy.run(SYNC,r);self.assertEqual([(h,head)],policy.head_writes)
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
        policy.after_adoption=lambda:setattr(r,'head_of_rite',None)
        policy.run(SYNC,r);self.assertEqual([],policy.head_writes);self.assertIs(h.house_head,old)
        self.assertNotIn('des_leadership_sync_in_progress',r.variables)
        self.assertIn('des_house_leadership_pending',r.variables)
    def test_failed_setter_keeps_pending_and_never_claims_success_from_membership(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.suppress_head_set=True
        policy.run(SYNC,r);self.assertIs(head.house,h);self.assertIs(h.house_head,old)
        self.assertIn('des_house_leadership_pending',r.variables)
        self.assertNotIn('des_last_religious_house_head',r.variables)
        policy.suppress_head_set=False;policy.run(SYNC,r)
        self.assertIs(h.house_head,head);self.assertNotIn('des_house_leadership_pending',r.variables)
    def test_real_title_gain_action_only_routes_the_actual_religious_holder(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy()
        policy.action('des_on_religious_head_title_gain',ai)
        self.assertEqual([],policy.head_writes)
        policy.action('des_on_religious_head_title_gain',head)
        self.assertIs(h.house_head,head)
        self.assertNotIn(('des_sync_rite_effect',r),policy.boundaries)
        self.assertEqual([(h,head)],policy.head_writes)
    def test_annual_cadet_all_living_first_then_head_preserves_player_recovery(self):
        d,r,h,c,head,ai,p,old=world();policy=LeadershipPolicy();policy.global_lists['des_bound_rites']=[r]
        p.rite=b.Obj('rite','player other rite');p.faith=b.Obj('faith','player other faith')
        dead=b.Obj('character','dead branch member',alive=False,dynasty=d,house=c);d.members.append(dead)
        policy.action('des_annual_cadet_recovery',b.Obj('global','yearly-root'))
        self.assertIs(ai.house,h);self.assertIs(p.house,h);self.assertIs(head.house,h);self.assertIs(dead.house,c)
        policy.action('des_annual_house_leadership_recovery',b.Obj('global','yearly-root'))
        self.assertIs(h.house_head,head);self.assertIs(d.variables['des_cadet_main_house'],h)
    def test_two_rites_sharing_a_head_only_match_its_actual_owned_rite(self):
        d,r,h,c,head,ai,p,old=world();d2,r2,h2,c2,head2,ai2,p2,old2=world()
        r2.head_of_rite=head;r2.faith=r.faith
        policy=LeadershipPolicy();policy.run(SYNC,r);policy.run(SYNC,r2)
        self.assertIs(h.house_head,head);self.assertIs(h2.house_head,old2)
        self.assertIs(head.dynasty,d);self.assertIn('des_house_leadership_pending',r2.variables)
    def test_hook_order_inventory_and_old_binding_contract_are_not_rewritten(self):
        actions=b.ast(b.read(MOD+'common/on_action/des_on_actions.txt'))
        pulse=b.body(b.body(actions,'yearly_global_pulse'),'on_actions')
        self.assertEqual(['des_annual_watchdog','des_annual_cadet_recovery','des_annual_house_leadership_recovery'],[r['value'] for r in pulse])
        sync=b.definition('common/scripted_effects/des_maintenance_effects.txt','des_sync_rite_effect')
        self.assertEqual({'key':SYNC,'value':'yes'},sync[-1])
        source=b.read(MOD+NEW_EFFECTS)
        self.assertNotIn('set_dynast =',source);self.assertNotIn('set_dynasty_head =',source)
        self.assertNotIn('set_religious_head_title',source)
        for relative in ['common/scripted_effects/des_binding_effects.txt','common/scripted_effects/des_cadet_effects.txt']:
            self.assertEqual((REPO/MOD/relative).read_text(encoding='utf-8-sig'),b.read(MOD+relative))
        whitelist=b.read(MOD+'tools/src/main/java/org/xar/ck3/dynastic/release/ReleaseProduct.java')
        self.assertEqual(1,whitelist.count('"'+NEW_EFFECTS+'"'));self.assertEqual(1,whitelist.count('"'+NEW_TRIGGERS+'"'))

if __name__=='__main__':unittest.main()
