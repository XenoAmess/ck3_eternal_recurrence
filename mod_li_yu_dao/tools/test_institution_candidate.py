"""Focused independent authorization and generated-AST checks; L0 only."""
import os,pathlib,sys,unittest
from copy import deepcopy
SOURCE=pathlib.Path(os.environ.get('LYD_CONTENT_TEST_SOURCE',str(pathlib.Path(__file__).resolve().parents[1])))
REPO=pathlib.Path(os.environ.get('LYD_CONTENT_TEST_REPO',str(SOURCE.parent)))
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(SOURCE/'tools'))
from extract_auto_upgrade_buildings import Block,parse_clausewitz
from validate_static import player_guard,guarded_effect,parse_localization
from test_content_leadership import Corpus,walk,one,scalar,has,contains_direct_fragment,blocks
from institution_oracle import World,School,Member,Institution,Refused

def world():
    return World({'kongmen':School('kongmen',1),'xunzi':School('xunzi',1),'dormant':School('dormant')},
        {n:Member(n,r,human) for n,r,human in [('a','kongmen',True),('b','kongmen',False),('c','kongmen',False),
                                             ('d','xunzi',False),('e','xunzi',False),('f','xunzi',True)]},
        political_titles={'county_a':'a','duchy_a':'a','foreign_county':'f'})

def authorized():
    p=Institution(world(),'a',1,1)
    p.nominate('kongmen','a',p.token());p.nominate('xunzi','d',p.token());p.seal(p.token())
    for n in 'abde':p.vote(n,True,p.token())
    for n in 'af':p.consent(n,True,p.token())
    p.sign('kongmen','a',p.token());p.sign('xunzi','d',p.token())
    return p

class PolicyTests(unittest.TestCase):
    def test_headless_scholarly_nominees_need_no_native_rite_head(self):
        p=authorized();self.assertIsNone(p.world.head)
        plan=p.plan(p.token(),native_proof=True)
        self.assertEqual(plan['rites'],('dormant','kongmen','xunzi'))
        self.assertEqual(plan['political_transfers'],())
        self.assertEqual(plan['government_changes'],())
        self.assertIsNone(p.world.head,'Oracle must not manufacture a native head')

    def test_global_majority_cannot_replace_each_schools_two_thirds(self):
        p=authorized();p.votes['e']=False;p.votes['c']=True
        self.assertTrue(p.quorum('kongmen'));self.assertFalse(p.quorum('xunzi'))
        with self.assertRaises(Refused):p.plan(p.token(),True)

    def test_emperor_sponsor_cannot_replace_other_human_consent(self):
        p=authorized();p.consents.remove('f')
        with self.assertRaises(Refused):p.plan(p.token(),True)

    def test_active_zero_elector_is_not_a_dormant_yes_vote(self):
        w=world();w.members={k:(Member(m.id,m.rite,m.human,False) if m.rite=='xunzi' else m) for k,m in w.members.items()}
        p=Institution(w,'a',1,1)
        self.assertNotIn('xunzi',p.dormant)
        with self.assertRaises(Refused):p.nominate('xunzi','d',p.token())
        with self.assertRaises(Refused):p.seal(p.token())

    def test_expiry_cancel_and_seal_nonce_prevent_old_callbacks(self):
        p=authorized();token=p.token()
        with self.assertRaises(Refused):p.verify(token,365)
        with self.assertRaises(Refused):p.verify(('a',1,1,'draft'))
        p.cancel('a',token)
        with self.assertRaises(Refused):p.sign('xunzi','d',token)
        fresh=Institution(world(),'a',2,3)
        with self.assertRaises(Refused):fresh.verify(token)

    def test_foreign_new_rite_new_human_and_nominee_drift_stop_enactment(self):
        p=authorized()
        for mutate in (
            lambda w:w.schools.update({'new':School('new')}),
            lambda w:w.members.update({'newhuman':Member('newhuman','kongmen',True)}),
            lambda w:w.members.update({'d':Member('d','kongmen')}),
            lambda w:w.schools.update({'xunzi':School('xunzi',1,False)}),
        ):
            q=deepcopy(p);mutate(q.world)
            with self.assertRaises(Refused):q.plan(q.token(),True)

    def test_refusal_and_duplicate_choices_never_create_a_plan(self):
        p=authorized();p.signatures.remove('xunzi')
        with self.assertRaises(Refused):p.plan(p.token(),True)
        with self.assertRaises(Refused):p.vote('a',True,p.token())
        with self.assertRaises(Refused):p.consent('a',True,p.token())
        p=authorized()
        with self.assertRaises(Refused):p.plan(p.token())

    def test_identity_and_eligibility_drift_blocks_enactment_but_owner_can_withdraw(self):
        for change in (
            lambda w:setattr(w,'faith','foreign_faith'),
            lambda w:w.members.update({'a':Member('a','xunzi',True)}),
            lambda w:w.members.update({'a':Member('a','kongmen',True,False)}),
        ):
            p=authorized();token=p.token();change(p.world)
            with self.assertRaises(Refused):p.plan(token,True)
            p.cancel('a',token)
            self.assertEqual(p.phase,'closed')

    def test_cleanup_rejects_foreign_dead_ai_and_previous_round_tokens(self):
        p=authorized();old=p.token()
        for actor in ('d','f'):
            with self.assertRaises(Refused):p.cancel(actor,old)
        for person in (Member('a','kongmen',False),Member('a','kongmen',True,True,False)):
            q=deepcopy(p);q.world.members['a']=person
            with self.assertRaises(Refused):q.cancel('a',old)
        fresh=Institution(world(),'a',2,3)
        with self.assertRaises(Refused):fresh.cancel('a',old)
        self.assertEqual(fresh.phase,'draft')

    def test_missing_representative_seal_is_state_free_and_nonce_advances_once(self):
        p=Institution(world(),'a',1,1);p.nominate('kongmen','a',p.token())
        before=(p.phase,p.nonce,deepcopy(p.votes),deepcopy(p.consents))
        with self.assertRaises(Refused):p.seal(p.token())
        self.assertEqual(before,(p.phase,p.nonce,p.votes,p.consents))
        p.nominate('xunzi','d',p.token());p.seal(p.token())
        self.assertEqual((p.phase,p.nonce),('ballot',2))
        with self.assertRaises(Refused):p.seal(p.token())
        self.assertEqual(p.nonce,2)

class ActualScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=Corpus()

    def test_only_commit_can_change_doctrine_and_requires_all_guards_first(self):
        danger={'remove_doctrine','add_doctrine','change_rite_doctrine'}
        for name,body in self.c.effects.items():
            if not name.startswith('lyd_i3b_'):continue
            direct=[e for e,_ in walk(body) if e.key in danger]
            self.assertFalse(direct if name!='lyd_i3b_commit_effect' else [])
            for e in direct:self.assertIn(e.value,{'doctrine_no_head','doctrine_temporal_head'})
        body=one(self.c.effects['lyd_i3b_commit_effect'],'if')
        gate=one(body,'limit')
        self.assertTrue(contains_direct_fragment(gate,'lyd_i3b_actor_trigger = yes lyd_i3b_event_context_trigger = yes this = scope:lyd_i3b_actor lyd_i3b_ready_trigger = { ACTOR = scope:lyd_i3b_actor } lyd_i3b_native_admitted_trigger = yes'))
        runtime=self.c.triggers['lyd_i3b_native_admitted_trigger']
        self.assertEqual([e.key for e in runtime.entries],
                         ['lyd_i3b_actor_trigger','lyd_i3b_event_context_trigger','this','lyd_i3b_ready_trigger'])
        self.assertTrue(contains_direct_fragment(runtime,
            'lyd_i3b_actor_trigger = yes lyd_i3b_event_context_trigger = yes this = scope:lyd_i3b_actor lyd_i3b_ready_trigger = { ACTOR = scope:lyd_i3b_actor }'))
        self.assertFalse(any(e.key=='always' for e,_ in walk(runtime)))
        ops=[e.key for e,_ in self.c.operations(body)]
        self.assertLess(ops.index('change_rite_doctrine'),ops.index('create_dynamic_title'))
        self.assertFalse(set(ops)&{'set_head_of_rite','set_government_type','set_parent_faith','detach_rite_to_new_faith','destroy_title','set_realm_capital','add_tenet','remove_tenet'})
        # The sole title transfer belongs to the shared factory's newly created office.
        transfers=[a for e,a in self.c.operations(body) if e.key=='change_title_holder']
        self.assertEqual(len(transfers),1);self.assertIn('scope:new_title',transfers[0])

    def test_expiry_cleanup_retains_ownership_and_fresh_round_resets_signature_delivery(self):
        begin=self.c.effects['lyd_i3b_begin_effect']
        self.assertTrue(contains_direct_fragment(one(one(begin,'if'),'faith'),
            'every_faith_rite = { set_variable = { name = lyd_i3b_owner value = scope:lyd_i3b_actor days = 366 } remove_variable = lyd_i3b_signature_requested }'))
        self.assertTrue(has(begin,'days','365'))
        timer=self.c.events['lyd.439']
        self.assertTrue(has(timer,'var:lyd_i3b_serial','scope:lyd_i3b_event_serial'))
        self.assertFalse(has(timer,'lyd_i3b_bind_event_effect'),'Expiry must not rebind an old timer to a new round')

    def test_separate_school_quorum_and_all_players_are_executable_requirements(self):
        ready=self.c.triggers['lyd_i3b_ready_trigger']
        self.assertTrue(contains_direct_fragment(ready,'NOT = { any_in_list = { variable = lyd_i3b_rites var:lyd_i3b_dormant = 0 NOT = { AND = { var:lyd_i3b_total > 0 lyd_i3b_quorum_value >= 0 var:lyd_i3b_signed = 1 exists = var:lyd_i3b_delegate } } } }'))
        self.assertTrue(contains_direct_fragment(ready,'NOT = { any_in_list = { variable = lyd_i3b_members var:lyd_i3b_was_player = 1 NOT = { var:lyd_i3b_player_yes = 1 } } }'))
        self.assertTrue(contains_direct_fragment(self.c.defs['lyd_i3b_quorum_value'],'value = var:lyd_i3b_yes multiply = 3 subtract = { value = var:lyd_i3b_total multiply = 2 }'))
        nomination=self.c.effects['lyd_i3b_accept_nomination_effect']
        self.assertFalse(has(nomination,'head_of_rite'), 'A nominee cannot require an existing native HoR')
        self.assertFalse(has(nomination,'set_religious_head_title'))

    def test_stale_callbacks_cannot_rebind_identity_or_create_duplicate_yes(self):
        context=one(self.c.triggers['lyd_i3b_event_context_trigger'],'scope:lyd_i3b_actor')
        self.assertTrue(contains_direct_fragment(context,'var:lyd_i3b_serial = scope:lyd_i3b_event_serial var:lyd_i3b_nonce = scope:lyd_i3b_event_nonce var:lyd_i3b_phase = scope:lyd_i3b_event_phase'))
        self.assertTrue(has(self.c.triggers['lyd_i3b_ballot_trigger'],'var:lyd_i3b_vote','-1'))
        for name in ('lyd_i3b_accept_nomination_effect','lyd_i3b_player_yes_effect','lyd_i3b_player_no_effect','lyd_i3b_sign_effect','lyd_i3b_sign_no_effect'):
            self.assertTrue(has(one(one(self.c.effects[name],'if'),'limit'),'lyd_i3b_event_context_trigger','yes'),name)
        self.assertTrue(has(one(one(self.c.effects['lyd_i3b_cancel_event_effect'],'if'),'limit'),'lyd_i3b_cancel_context_trigger','yes'))
        close=self.c.effects['lyd_i3b_close_effect']
        self.assertFalse(any(e.key=='remove_variable' and e.value in {'lyd_i3b_nonce','lyd_i3b_serial'} and not a for e,a in walk(close)))

    def test_nomination_delivery_does_not_vote_sign_or_enact(self):
        interaction=self.c.defs['lyd_i3b_nominate_interaction']
        self.assertTrue(player_guard(one(one(interaction,'is_shown'),'scope:actor'),self.c.triggers))
        self.assertEqual(scalar(one(interaction,'ai_will_do'),'base'),'0')
        delivered=[e.key for e,_ in self.c.operations(one(interaction,'on_auto_accept'))]
        self.assertFalse(set(delivered)&{'change_rite_doctrine','add_doctrine','set_religious_head_title','change_title_holder'})
        self.assertNotIn('lyd_i3b_vote_effect',delivered)
        self.assertTrue(has(self.c.effects['lyd_i3b_nominate_self_effect'],'trigger_event','lyd.410'))
        for name in self.c.effects:
            if name.startswith('lyd_i3b_'):
                self.assertFalse(any(e.key=='hidden_trigger' or 'prev.prev' in e.key or isinstance(e.value,str) and 'prev.prev' in e.value for e,_ in walk(self.c.effects[name])))

    def test_cross_flow_locks_and_full_roster_changes_block_confirmation(self):
        for name in ('lyd_c2_school_free_trigger','lyd_c2_receiver_free_trigger'):
            self.assertTrue(contains_direct_fragment(self.c.triggers[name],'NOT = { has_variable = lyd_i3b_owner }'))
        self.assertTrue(has(self.c.effects['lyd_c3_begin_round_effect'],'has_variable','lyd_i3b_owner'))
        current=self.c.triggers['lyd_i3b_current_trigger']
        self.assertTrue(has(current,'var:lyd_i3b_member_owner','$ACTOR$'))
        self.assertTrue(has(current,'var:lyd_i3b_member_serial','$ACTOR$.var:lyd_i3b_serial'))
        self.assertTrue(has(current,'var:lyd_i3b_owner','$ACTOR$'))
        self.assertTrue(has(current,'lyd_i3b_compatible_rite_trigger','yes'))
        self.assertTrue(has(current,'var:lyd_i3b_delegate'))

    def test_npc_ballot_root_does_not_become_the_signature_owner(self):
        # Resolve the authored helper's saved scope/ACTOR parameter under a
        # recipient ROOT, then evaluate ownership independently for two rites.
        helper=self.c.effects['lyd_i3b_request_signatures_effect']
        scopes={};actor='a';event_root='b'
        saved=scalar(helper,'save_scope_as');self.assertIsNotNone(saved)
        scopes[saved]=actor
        body=one(helper,'if');gate=one(body,'limit')
        parameter=scalar(one(gate,'lyd_i3b_current_trigger'),'ACTOR')
        resolved=event_root if parameter=='root' else scopes.get(parameter.removeprefix('scope:'))
        self.assertEqual(resolved,actor,'An NPC ROOT must not replace the saved initiator')
        rites=[{'owner':'a','serial':9,'yes':2,'total':3,'delegate':'a'},
               {'owner':'a','serial':9,'yes':4,'total':6,'delegate':'d'}]
        self.assertTrue(all(r['owner']==resolved and r['serial']==9 for r in rites))
        self.assertFalse(all(r['owner']==event_root for r in rites),'Counterexample must reject the old ROOT implementation')
        self.assertEqual([(r['delegate'],r['owner'],r['serial']) for r in rites if 3*r['yes']>=2*r['total']],
                         [('a','a',9),('d','a',9)])
        # Each child receives the iteration rite scope, after original callback
        # validation. No bind is evaluated before that callback's limit.
        ballot=one(self.c.effects['lyd_i3b_vote_effect'],'if')
        self.assertTrue(has(one(ballot,'limit'),'lyd_i3b_ballot_trigger','yes'))
        self.assertTrue(has(self.c.triggers['lyd_i3b_ballot_trigger'],'lyd_i3b_event_context_trigger','yes'))
        self.assertTrue(has(ballot,'scope:lyd_i3b_actor'))
        self.assertTrue(has(one(body,'every_in_list'),'save_scope_as','lyd_i3b_ballot_rite'))
        self.assertTrue(has(one(body,'every_in_list'),'trigger_event','lyd.413'))
        self.assertFalse(has(gate,'lyd_i3b_bind_event_effect'))

    def test_withdrawal_is_minimal_and_cleanup_matches_exact_owner_and_serial(self):
        minimum=self.c.triggers['lyd_i3b_cancel_actor_trigger']
        self.assertTrue(player_guard(minimum,self.c.triggers))
        self.assertTrue(has(minimum,'is_alive','yes'))
        forbidden={'faith','rite','is_landed','highest_held_title_tier','has_trait','lyd_i3b_actor_trigger','lyd_i3b_current_trigger'}
        self.assertFalse({e.key for e,_ in walk(minimum)}&forbidden)
        context=self.c.triggers['lyd_i3b_cancel_context_trigger']
        self.assertTrue(contains_direct_fragment(context,'this = scope:lyd_i3b_actor var:lyd_i3b_serial = scope:lyd_i3b_event_serial var:lyd_i3b_nonce = scope:lyd_i3b_event_nonce var:lyd_i3b_phase = scope:lyd_i3b_event_phase'))
        close=self.c.effects['lyd_i3b_close_effect']
        for list_name,owner_key,serial_key in (
            ('lyd_i3b_rites','var:lyd_i3b_owner','var:lyd_i3b_serial'),
            ('lyd_i3b_members','var:lyd_i3b_member_owner','var:lyd_i3b_member_serial'),
        ):
            loop=next(b for b in blocks(close,'every_in_list') if scalar(b,'variable')==list_name)
            selector=one(one(loop,'if'),'limit')
            self.assertEqual(scalar(selector,owner_key),'scope:lyd_i3b_closing_actor')
            self.assertEqual(scalar(selector,serial_key),'scope:lyd_i3b_closing_actor.var:lyd_i3b_serial')
            rows=[('a',10),('a',11),('b',10)]
            removed=[r for r in rows if r[0]=='a' and r[1]==10]
            self.assertEqual(removed,[('a',10)])
        self.assertFalse(any(e.key=='remove_variable' and e.value.startswith(('lyd_c2_','lyd_c3_')) for e,_ in walk(close)))

    def test_display_and_seal_execution_share_the_real_preconditions(self):
        seal=self.c.defs['lyd_i3b_seal_decision']
        displayed=one(one(seal,'is_valid'),'custom_description')
        invoked=one(one(self.c.effects['lyd_i3b_seal_effect'],'if'),'limit')
        self.assertEqual(scalar(one(displayed,'lyd_i3b_can_seal_trigger'),'ACTOR'),scalar(one(invoked,'lyd_i3b_can_seal_trigger'),'ACTOR'))
        required=self.c.triggers['lyd_i3b_can_seal_trigger']
        self.assertTrue(has(required,'var:lyd_i3b_phase','1'))
        self.assertTrue(has(required,'lyd_i3b_current_trigger'))
        self.assertTrue(has(required,'lyd_i3b_representatives_ready_trigger','yes'))
        representatives=self.c.triggers['lyd_i3b_representatives_ready_trigger']
        self.assertTrue(has(representatives,'exists','var:lyd_i3b_delegate'))
        self.assertTrue(has(representatives,'var:lyd_i3b_total','0','>'))
        for name,body in self.c.defs.items():
            if name.startswith('lyd_i3b_') and name.endswith('_decision'):
                valid=one(body,'is_valid');self.assertEqual([e.key for e in valid.entries],['custom_description'])
        failures=one(self.c.defs['lyd_i3b_nominate_interaction'],'is_valid_showing_failures_only')
        for scope in ('scope:actor','scope:recipient'):
            self.assertEqual([e.key for e in one(failures,scope).entries],['custom_description'])

    def test_all_entry_mutations_are_hidden_and_visible_preview_is_read_only(self):
        mutation={'set_variable','remove_variable','change_variable','save_scope_as','save_scope_value_as','clear_variable_list',
                  'add_to_variable_list','remove_doctrine','add_doctrine','change_rite_doctrine','create_dynamic_title',
                  'change_title_holder','set_religious_head_title','set_character_rite','add_character_flag','remove_character_flag','trigger_event'}
        entries=[]
        for name,body in self.c.defs.items():
            if name.startswith('lyd_i3b_') and name.endswith('_decision'):entries.append(one(body,'effect'))
        entries.append(one(self.c.defs['lyd_i3b_nominate_interaction'],'on_auto_accept'))
        for event_id in ('lyd.410','lyd.411','lyd.412','lyd.413','lyd.430','lyd.431','lyd.432'):
            entries.extend(blocks(self.c.events[event_id],'option'))
        entries.append(one(self.c.events['lyd.439'],'immediate'))
        for body in entries:
            for e,ancestors in self.c.operations(body):
                if e.key in mutation:self.assertIn('hidden_effect',ancestors,e.key)
            # Direct display wrappers cannot contain mutable calls or effects.
            for e,ancestors in walk(body):
                if e.key=='custom_description':
                    self.assertFalse(any(x.key in mutation or x.key in self.c.effects for x,_ in walk(e.value)))

    def test_whole_decision_execution_hides_transitive_internal_conditions(self):
        def visible_reads(body, seen=frozenset()):
            found=[]
            for e in body.entries:
                if e.key in {'hidden_effect','custom_description'}:
                    continue
                if e.key in self.c.effects and e.key not in seen:
                    found.extend(visible_reads(self.c.effects[e.key],seen|{e.key}))
                elif isinstance(e.value,Block):
                    if e.key in {'limit','trigger'}:
                        for condition in self.c.trigger_closure(e.value):
                            for node,_ in walk(condition):
                                if node.key.startswith(('var:','scope:')) or node.key=='has_variable' or isinstance(node.value,str) and node.value.startswith(('var:','scope:')):
                                    found.append((node.key,node.value))
                    else:
                        found.extend(visible_reads(e.value,seen))
            return found
        decisions=[body for name,body in self.c.defs.items() if name.startswith('lyd_i3b_') and name.endswith('_decision')]
        self.assertEqual(len(decisions),6)
        for body in decisions:
            execution=one(body,'effect')
            self.assertEqual([e.key for e in execution.entries],['hidden_effect'])
            self.assertEqual(visible_reads(execution),[])
            # Expose the actual inner if as a source mutant; every decision must
            # detect its real transitive condition graph, not only mutation.
            exposed=one(execution,'hidden_effect')
            self.assertTrue(visible_reads(exposed),'An exposed real guard escaped the preview regression')

    def test_partial_native_failure_preserves_typed_receipt_and_has_visible_result(self):
        body=one(self.c.effects['lyd_i3b_commit_effect'],'if')
        writes={scalar(e.value,'name'):scalar(e.value,'value') for e in body.entries if e.key=='set_variable'}
        self.assertEqual(writes['lyd_i3b_result_serial'],'var:lyd_i3b_serial')
        self.assertEqual(writes['lyd_i3b_result_nonce'],'var:lyd_i3b_nonce')
        self.assertNotIn('lyd_i3b_result_faith',writes)
        self.assertNotIn('lyd_i3b_result_main',writes)
        post=one(body,'if');failure=one(body,'else')
        self.assertTrue(has(post,'set_variable'))
        self.assertTrue(has(post,'faith.religious_head','this'))
        self.assertTrue(has(post,'lyd_c3_owned_current_head_trigger','yes'))
        self.assertTrue(contains_direct_fragment(one(post,'limit'),'NOT = { any_in_list = { variable = lyd_i3b_political_titles NOT = { holder = scope:lyd_i3b_actor } } }'))
        self.assertTrue(contains_direct_fragment(post,'set_variable = { name = lyd_i3b_result_code value = 1 } set_variable = { name = lyd_i3b_result_head_title value = faith.religious_head_title }'))
        # The factory failure branch follows identity failure, and must precede
        # doctrine/old-title tests: doctrines can succeed while the factory fails.
        branches=[e.value for e in failure.entries if e.key in {'if','else_if','else'}]
        codes=[scalar(one(b,'set_variable'),'value') for b in branches]
        self.assertEqual(codes,['2','3','4','5','7','6'])
        factory=branches[1]
        self.assertTrue(has(one(factory,'limit'),'faith.religious_head','this'))
        self.assertTrue(has(one(factory,'limit'),'lyd_c3_owned_current_head_trigger','yes'))
        self.assertFalse(any(e.key=='remove_variable' and e.value.startswith('lyd_i3b_result_') for e,_ in walk(self.c.effects['lyd_i3b_close_effect'])))
        ordered=[e.key for e in body.entries]
        self.assertLess(ordered.index('lyd_i3b_close_effect'),ordered.index('lyd_i3b_show_result_effect'))
        delivered=self.c.effects['lyd_i3b_show_result_effect']
        self.assertTrue(has(delivered,'trigger_event','lyd.431'));self.assertTrue(has(delivered,'trigger_event','lyd.432'))
        self.assertTrue(has(self.c.events['lyd.431'],'var:lyd_i3b_result_code','1'))
        self.assertTrue(has(self.c.events['lyd.432'],'var:lyd_i3b_result_code','1','>'))
        for event_id in ('lyd.431','lyd.432'):
            self.assertTrue(has(self.c.events[event_id],'var:lyd_i3b_result_serial','scope:lyd_i3b_result_event_serial'))
            self.assertTrue(has(self.c.events[event_id],'var:lyd_i3b_result_nonce','scope:lyd_i3b_result_event_nonce'))
        fees={'remove_short_term_gold','add_gold','add_piety','add_prestige','add_experience','add_trait_xp'}
        self.assertFalse(any(e.key in fees for name,body in self.c.effects.items() if name.startswith('lyd_i3b_') for e,_ in self.c.operations(body)))

    def test_additive_ast_localization_and_event_references_are_complete(self):
        chinese=parse_localization(SOURCE/'localization/simp_chinese/lyd_i3b_institution_l_simp_chinese.yml')
        english=parse_localization(SOURCE/'localization/english/lyd_i3b_institution_l_english.yml')
        self.assertEqual(chinese.keys(),english.keys())
        tooltips=self.c.effects['lyd_i3b_show_terms_effect']
        named=[e.value for e,_ in walk(tooltips) if e.key=='this' and isinstance(e.value,str)]
        self.assertEqual(set(named),{f'rite:{r}' for r in self.c.rites},'Explicit terms omit a catalogue rite')
        self.assertTrue(has(tooltips,'variable','lyd_i3b_rites'),'Terms must enumerate the captured list')
        self.assertFalse(any(e.key in {'set_variable','change_variable','add_doctrine','change_rite_doctrine','set_character_rite'} for e,_ in walk(tooltips)))
        for p in SOURCE.rglob('lyd_i3b_*.txt'):
            data=p.read_bytes();self.assertTrue(data.startswith(b'\xef\xbb\xbf'),str(p))
            ast=parse_clausewitz(data.decode('utf-8-sig'))
            for e,a in walk(ast):
                if e.key=='trigger_event':
                    event=e.value if isinstance(e.value,str) else scalar(e.value,'id')
                    self.assertIn(event,self.c.events)
                if e.key.startswith('lyd_i3b_') and e.operator=='=' and e.value=='yes':self.assertIn(e.key,self.c.defs)
                if e.key in {'name','title','desc','confirm_text','selection_tooltip'} and isinstance(e.value,str) and e.value.startswith('lyd_i3b_') and not any(x in a for x in ('set_variable','change_variable','save_scope_value_as','add_to_variable_list')):
                    self.assertIn(e.value,chinese)

class IntegrationOwnershipTests(unittest.TestCase):
    def test_complete_runtime_composition_has_one_factory_owner_and_institution_extension(self):
        import gen_runtime,gen_institution,gen_leadership
        from unittest.mock import patch
        # Inspect full production generation using its real permanent primitive receipt.
        composed=gen_runtime.build_outputs()
        institution=gen_institution.build_outputs()
        self.assertTrue(institution.keys()<=composed.keys())
        for name,payload in institution.items():self.assertEqual(composed[name],payload)
        leadership=gen_leadership.build_outputs()
        for path in ('common/scripted_effects/lyd_c3_head_factory.txt','common/scripted_effects/lyd_c3_migration_hooks.txt'):
            self.assertNotIn(path,institution)
            self.assertEqual(composed[path],leadership[path])
        duplicate={'common/scripted_effects/lyd_c3_head_factory.txt':b'unreviewed overwrite'}
        with patch.object(gen_institution,'build_outputs',return_value=duplicate):
            with self.assertRaisesRegex(ValueError,'Duplicate generated runtime paths'):gen_runtime.build_outputs()

    def test_l0_and_official_workflow_include_authorization_checks_and_state_closed_scope(self):
        import run_acceptance
        rows=run_acceptance.l0_commands(SOURCE,REPO,lambda argv,output,name:{'argv':argv,'returncode':0})
        self.assertIn('institution-tests',[row['name'] for row in rows])
        workflow=(REPO/'.github/workflows/li-yu-dao-static.yml').read_text(encoding='utf-8')
        self.assertIn('python mod_li_yu_dao/tools/test_institution_candidate.py',workflow)
        self.assertFalse(any(line.strip().split()[:2]==['python','mod_li_yu_dao/tools/run_acceptance.py'] for line in workflow.splitlines()),'Official CI must not perform live preflight')

if __name__=='__main__':unittest.main(verbosity=2)
