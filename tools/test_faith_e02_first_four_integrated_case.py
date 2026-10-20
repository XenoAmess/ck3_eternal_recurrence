"""Narrow real-case consumers with authored IO; no process, host or game launch."""
from copy import deepcopy
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(REPO/'tools'),str(REPO),str(REPO/'ck3_autonomous_player/src')]

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

A=module(HERE/'ck3_mod_acceptance_cases/faith_e02_first_four_integrated_adapter.py','root_integrated_adapter_under_test')
Q=A.Q
M=SimpleNamespace(pin=A.S.pin)
from ck3_mod_acceptance_client import CaseClient
FULL_ITEM=0x010001ed
FULL_HOLDER=0x01000003
SITE=101
EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'

def frame():
    return {'source':'injected-dll-named-pipe','backend_id':'native-headless','episode_projection':'native_campaign',
        'snapshot_id':'synthetic:integrated','revision':5,'native_revision':4,'date_raw':51394920,
        'played_character':{'character_id':15893,'alive':True,'source':'native'},'paused':True,'map_ready':True,
        'active_event':None,'pending_character_interaction':None,'episode_run_id':None,
        'played_character_gold':2250,'played_character_piety':12000,
        'diagnostics':{'bridge_pid':1234,'connection_generation':4,'hello':{'pid':1234,'connection_generation':4,
            'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':EXE,'ck3_build_match':True,
            'game_adapter_id':'ck3-1.20.0.4-msvc-x64'}}}

class OwnedPublicClient(CaseClient):
    operator_reviewer='synthetic-integrated-reviewer'
    def __init__(self,image):
        self.manifest={'game':{'version':'1.20.0.4','exe_sha256':EXE}}
        self._binding=None;self.image=image;self.holder=FULL_HOLDER
        self.equipped=False;self.enshrined=False;self.visible=False;self.selected=False
        self.calls=[];self.checkpoints={};self.denied=None;self.pending_post=False
        self.unknown_equip=False;self.historical=False;self.wrong_post_item=False
        self.preview='a'*64;self.change_preview_after_review=False;self.claim_attribution=False
        self.inventory_sequence=0;self.inventory_no_call=False;self.inventory_rejected=False
        self.inventory_unknown=False;self.inventory_no_call_historical=0
        self.owned=[FULL_ITEM];self.court=set();self.not_enshrinable=set()
        self.epoch=10;self.action_origins={};self.snapshot_count=0
        self.bad_action_before=None;self.bad_post=None;self.supplied_before=None
        self.creation_type=None;self.creation_barony=None;self.all_creation_types=False
        self.close_sequence=0;self.close_before=None;self.close_resolved=False
        self.close_unknown=False;self.close_pending=False;self.close_keep_visible=False
        self.close_wrong_sequence=False;self.close_bad_before=False;self.close_reappears=False
        self.close_initial_hidden=False;self.close_return=False
    def snapshot(self,**kwargs):
        self.snapshot_count+=1
        return self.validate_frame(frame())
    def remaining(self):return 2400
    def guard(self,reserve=90,**kwargs):
        if reserve<120:raise AssertionError('Normal Quit reserve lost')
        return {}
    def checkpoint(self,name,value):
        if name in self.checkpoints:raise AssertionError('Reused evidence name')
        self.checkpoints[name]=deepcopy(value)
    def root_checkpoint(self,name,request,reserve):
        self.guard(reserve)
        answer={'run_id':'synthetic-integrated','reviewer':self.operator_reviewer,'status':'complete'}
        if 'approval_key' in request:
            answer.update(original_image_directly_reviewed=True,original_image=M.pin(self.image),
                reviewed_native_observation_sha256=A.visual_observation_sha256(request['native_observation']))
            answer[request['approval_key']]=request['approval_key']!=self.denied
            if request['approval_key']=='enshrine_once_authorized' and self.change_preview_after_review:self.preview='b'*64
        return answer
    def execute_plan(self,steps,name,timeout=None):
        Q.validate({'steps':steps});rows=[]
        for step in steps:
            self.calls.append(deepcopy(step));tool,args=step['tool'],step['args']
            if tool==Q.EQUIP and self.unknown_equip:
                self.equipped=args['desired_equipped']
                rows.append({'id':step['id'],'plan':deepcopy(step),'ok':False,'error':'AUTHORED lost ACK',
                    'after_snapshot':frame()});continue
            if tool==Q.OPEN_INVENTORY and self.inventory_unknown:
                self.visible=True;self.inventory_sequence=17
                rows.append({'id':step['id'],'plan':deepcopy(step),'ok':False,'error':'AUTHORED lost inventory ACK',
                    'after_snapshot':frame()});continue
            if tool==Q.CLOSE_INVENTORY and self.close_unknown:
                self.visible=False;self.close_sequence=31
                rows.append({'id':step['id'],'plan':deepcopy(step),'ok':False,'error':'AUTHORED lost Close ACK',
                    'after_snapshot':frame()});continue
            row={'id':step['id'],'plan':deepcopy(step),'ok':True,'result':self.response(tool,args),
                'after_snapshot':frame()}
            if self.supplied_before is not None:row['before_snapshot']=deepcopy(self.supplied_before)
            rows.append(row)
        return rows
    def response(self,tool,args):
        common={'available':True,'played_character_id':15893,'date_raw':51394920,'read_only':True}
        if tool=='ck3_query_player_religion_context_v1':return common
        if tool=='ck3_query_player_holy_site_v1':return {**common,'current_faith_sites':[{'available':True,'holy_site_id':SITE}]}
        if tool=='ck3_select_holy_site_creation_type_v1':self.creation_type=args['type_key']
        if tool=='ck3_select_holy_site_creation_barony_v1':self.creation_barony=args['barony_title_id']
        if tool=='ck3_query_player_holy_site_creation_context_v1':
            return {**common,'models_complete':True,'selected_type_key':self.creation_type,
                'selected_barony_title_id':self.creation_barony,'potential_barony_title_ids':[50],
                'normal_requirements_legality_observed':True,'normal_requirements_can_create':False,
                'create_tooltip_available':True,'create_tooltip':'AUTHORED current tuple refusal',
                'available_holy_site_types':[{'type_key':key,'native_can_pick_observed':True,
                    'native_can_pick':self.all_creation_types,'tooltip_available':True,
                    'tooltip':'AUTHORED actual type refusal'}for key in sorted(Q.TYPES)]}
        if tool==Q.ACTOR:
            return {**common,'character_id':args['character_id'],'requested_skill':'diplomacy',
                'faith_id':50,'rite_id':15,'site_attribution_observed':self.claim_attribution,
                'selected_site_contribution_raw':None,'current_skill_points':{'diplomacy':10+int(self.enshrined),
                    'martial':9,'stewardship':8,'intrigue':7,'learning':6,'prowess':5},
                'effective_devotion_level':3,'devotion_total_raw':30000000,
                'actual_skill_breakdown':'AUTHORED whole native-style text; no selected-site numeric proof',
                'cache_generation_time_known':False}
        if tool=='ck3_query_ingame_ui_window_v1':
            if args['window_kind']=='inventory':return self.inventory('query')
            return {'available':True,'effective_visible':True,'subject_id_available':True,'current_subject_id':SITE}
        if tool==Q.OPEN_INVENTORY:
            if self.inventory_no_call:
                self.visible=True;self.inventory_sequence=self.inventory_no_call_historical
            elif not self.inventory_rejected:
                self.visible=True;self.inventory_sequence=17
            return self.inventory('open')
        if tool==Q.INVENTORY_POST:return self.inventory('post')
        if tool==Q.INVENTORY_CLOSE_QUERY:return self.inventory_close('query')
        if tool==Q.CLOSE_INVENTORY:return self.inventory_close('close')
        if tool==Q.INVENTORY_CLOSE_POST:return self.inventory_close('post')
        if tool==Q.ARTIFACT:return self.item(args['artifact_id'])
        if tool==Q.EQUIP:
            before=self.item(args['artifact_id'])
            self.equipped=args['desired_equipped']
            value=self.action(args,before)
            self.action_origins[value['intent_sequence']]=deepcopy(value)
            if self.bad_action_before=='date':value['before']['date_raw']+=1
            elif self.bad_action_before=='pid':value['before_game_pid']+=1
            elif self.bad_action_before=='generation':value['before_connection_generation']+=1
            return value
        if tool==Q.EQUIP_POST:
            resolved=not self.pending_post and not self.historical
            value=deepcopy(self.action_origins[args['expected_intent_sequence']])
            value.update(read_only=True,after=self.item(args['artifact_id']),after_native_revision=4,
                after_connection_generation=4,after_game_pid=1234,desired_inventory_state_observed=resolved,
                needs_recovery=self.pending_post,status='desired_inventory_state_observed'if resolved else
                    'intent_previously_resolved_current_state_not_observed'if self.historical else'intent_pending_or_unknown')
            if self.wrong_post_item:value['artifact_id']+=1
            if self.bad_post=='sequence':value['intent_sequence']+=1
            elif self.bad_post=='before':value['before']['capture_epoch']+=1
            elif self.bad_post=='date':value['after']['date_raw']+=1
            elif self.bad_post=='pid':value['after_game_pid']+=1
            elif self.bad_post=='generation':value['after_connection_generation']+=1
            return value
        if tool=='ck3_select_holy_site_relic_artifact_v1':self.selected=True
        if tool==Q.ACTION_CONTEXT:return self.action_context(args['artifact_id'])
        if tool==Q.ENSHRINE:
            self.enshrined=True
            return {'invoked':True,'available':True,'business_outcome_observed':False}
        if tool==Q.RELIC_CONTEXT:return {**common,'requested_holy_site_id':SITE,'inventory':{'available':True,
            'artifact_ids':[FULL_ITEM]if self.enshrined else[],
            'slots':[{'slot_index':0,'artifact_id':FULL_ITEM if self.enshrined else None}]},
            'county_context':{'available':True,'county_holder_id':self.holder},
            'current_relic_evaluation':{'available':True,'is_active':self.enshrined,'active_artifact_rarity_sum':4 if self.enshrined else 0}}
        if tool=='ck3_query_player_holy_site_relic_permissions_v1':return {**common,'requested_holy_site_id':SITE,
            'requested_artifact_id':args.get('artifact_id'),
            'player_inventory':{'available':True,'owner_matches_player':True,'artifact_ids':[]if self.enshrined else list(self.owned)}}
        return {**common,'invoked':True}
    def action(self,args,before):
        return {'schema':'ck3_12004_player_artifact_personal_use_action_v1','game_version':'1.20.0.4',
            'executable_sha256':EXE,'read_only':False,'available':True,'unavailable_reason':None,
            'played_character_id':15893,'artifact_id':args['artifact_id'],'desired_equipped':args['desired_equipped'],
            'expected_slot_index':args['expected_slot_index'],'expected_replacing_artifact_id':None,
            'intent_sequence':21 if args['desired_equipped']else 22,'intent_found':True,
            'invoked':True,'once_intent_consumed':True,'dispatch_call_returned':True,'needs_recovery':True,
            'desired_inventory_state_observed':False,'status':'original_callback_invoked_post_pending',
            'before_native_revision':4,'before_connection_generation':4,'before_game_pid':1234,
            'after_native_revision':0,'after_connection_generation':0,'after_game_pid':0,'before':before,'after':None,
            **{key:False for key in ('business_outcome_observed','actor_aggregate_observed',
                'personal_net_effect_attributed','total_payment_observed','automatic_retry')}}
    def inventory(self,operation):
        no_claim=operation=='open' and (self.inventory_no_call or self.inventory_rejected)
        sequence=0 if no_claim else self.inventory_sequence
        return {'available':True,'read_only':operation!='open','operation':operation,'intent_sequence':sequence,
            'once_intent_consumed':sequence>0,'invoked':sequence>0,'needs_recovery':sequence>0 and operation!='post',
            'client_replay_blocked':False,'desired_window_observed':operation=='post',
            'status':'inventory_current_player_already_visible_no_call'if no_claim and self.inventory_no_call else
                'inventory_owner_unavailable'if no_claim else'inventory_current',
            'current':{'available':True,'played_character_id':15893,'selected_character_id':15893 if self.visible else None,
                **{key:self.visible for key in ('root_present','native_visible','effective_visible','current_player_selected')},
                'window_present':True}}
    def close_view(self):
        self.epoch+=1
        return {'available':True,'native_revision':4,'capture_epoch':self.epoch,'date_raw':51394920,
            'game_pid':1234,'connection_generation':4,'played_character_id':15893,'selected_character_id':15893,
            'window_present':True,'root_present':True,'native_visible':self.visible,
            'effective_visible':self.visible,'current_player_selected':True}
    def inventory_close(self,operation):
        if operation=='query' and self.close_initial_hidden and not self.close_sequence:self.visible=False
        if operation=='query' and self.close_resolved and self.close_reappears:self.visible=True
        if operation=='close':
            self.close_before=self.close_view();self.close_sequence=31
            if not self.close_keep_visible:self.visible=False
        current=self.close_view();found=self.close_sequence>0
        observed=operation=='post' and not self.close_pending and not self.close_keep_visible
        if observed:self.close_resolved=True
        value={'schema':'ck3_12004_player_inventory_window_close_v1','game_version':'1.20.0.4',
            'executable_sha256':EXE,'operation':operation,'read_only':operation!='close',
            'available':True,'unavailable_reason':None,'loaded_code_pins_verified':True,
            'loaded_gui_sources_verified':True,'current':current,'intent_sequence':self.close_sequence,
            'intent_found':found,'once_intent_consumed':found,'invoked':found,'call_returned':found,
            'needs_recovery':found and not self.close_resolved,'desired_window_observed':observed,
            'status':'inventory_window_observed'if operation=='query'else
                'inventory_close_invoked_post_pending'if operation=='close'else
                'inventory_window_closed_observed'if observed else'inventory_intent_pending_or_unknown',
            'before':deepcopy(self.close_before),'after':current if operation=='post'else None,
            **{key:False for key in ('artifact_equipped_observed','actor_aggregate_observed',
                'personal_net_effect_attributed','business_outcome_observed','automatic_retry')},
            'client_replay_blocked':found and not self.close_resolved}
        if operation=='post' and self.close_wrong_sequence:value['intent_sequence']+=1
        if operation=='post' and self.close_bad_before:value['before']['capture_epoch']+=1
        return value
    def item(self,artifact=FULL_ITEM):
        self.epoch+=1;personal=artifact not in self.court;equipped=self.equipped and artifact==FULL_ITEM
        return {'schema':'ck3_12004_player_artifact_personal_use_v1','game_version':'1.20.0.4',
            'executable_sha256':EXE,'available':True,'unavailable_reason':None,'read_only':True,
            'date_raw':51394920,'played_character_id':15893,'capture_epoch':self.epoch,'loaded_source_pins_verified':True,
            'requested_artifact_id':artifact,'personally_owned':not self.enshrined,'inventory_artifact':personal,
            'owned_ids':list(self.owned),'slots':[{'index':0,'key':'weapon','personal':True,
                'artifact_id':FULL_ITEM if self.equipped else None}],
            'equipped':equipped,'inventory_view_available':True,'inventory_view_visible':self.visible,'native_equipped_observed':True,
            'can_equip_in_effective_slot':not equipped if personal else None,'can_unequip':equipped,
            'effective_slot_index':0,'equipped_slot_index':0 if equipped else None,
            'replacing_artifact_id':FULL_ITEM if self.equipped else None,'personal_net_effect_attributed':False,
            'item_modifier_definition':{'available':True,'entries':[]},'modifier_names_bound':False,
            **{key:False for key in ('actor_aggregate_observed','total_payment_observed','action_ready','business_outcome_observed')},
            'modifier_description':{'available':True,'text':'AUTHORED item definition; not a net skill gain'}}
    def action_context(self,artifact=FULL_ITEM):
        value={'available':True,'read_only':True,'played_character_id':15893,'date_raw':51394920,
            'requested_holy_site_id':SITE,'requested_artifact_id':artifact,'selected_artifact_matches_request':self.selected,
            'preview_identity_available':True,'preview_identity_sha256':self.preview,
            'selected_action_effect_description':{'available':True,'text':'AUTHORED original quote'},
            'artifact_ownership':{'available':True,'artifact_id':artifact,'character_owner_id':None if self.enshrined else 15893,
                'holy_site_owner_id':SITE if self.enshrined else None,'character_owner_matches_player':not self.enshrined,
                'player_owned_reference_member':not self.enshrined,'player_equipped_slot_member':{'available':True,'value':self.equipped}},
            'destination':{'available':True,'action_kind':'enshrine','effective_slot_index':0,'replacing_artifact_id':None},
            'permissions':{group:{'can_enshrine':{'available':True,'value':not self.enshrined}}
                for group in ('artifact_permissions','current_buttons')}}
        if artifact in self.not_enshrinable:
            for group in ('artifact_permissions','current_buttons'):
                value['permissions'][group]['can_enshrine']['value']=False
        return value

class IntegratedConsumers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(dir=HERE,prefix='finite-owned-')
        cls.work=Path(cls.temp.name)
        cls.image=cls.work/'AUTHORED-synthetic-not-game.png'
        cls.image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='))
        # Exercise the actual Root adapter/queue. No external candidate/template
        # is imported; retained scout and source-evidence dependencies stay explicit.
        dependencies=[A.__file__,Q.__file__,A.S.__file__,A.S.queue.__file__,
            A.S.shared_opening_binding.__code__.co_filename,A.require_root_visual_review.__code__.co_filename]
        # Pin-only authored provider records keep this unit fixture portable.
        # They do not claim native/SDK qualification or replace production evidence.
        providers=[]
        for package in ('faith-observers','actor-skill-effects','inventory-open'):
            path=cls.work/(package+'-source-fixture.json')
            path.write_text(json.dumps({'authored_unit_fixture':True,'native_qualified':False}),encoding='utf-8')
            providers.append(path)
        cls.contract={'schema':'faith-e02-first-four-integrated-case-v1','product':A.PRODUCT,'case':A.CASE,
            'machine_id':'4-8e1c2f1861','saved_input':{'save':'authored-not-restored.ck3',**A.S.SAVE},
            'profile':{'enabled_mods':[],'product_files':[]},'scope':A.SCOPE,'max_public_calls':A.MAX_CALLS,
            'dependencies':[M.pin(path)for path in dependencies],
            'provider_source_evidence':[M.pin(path)for path in providers]}
        cls.spec={'required_mcp_tools':sorted(A.REQUIRED),'opt_in_read_only_mcp_tools':sorted(Q.READONLY),
            **{flag:True for flag in ('opt_in_holy_site_creation_ui','opt_in_holy_site_relic_actions',
                'opt_in_player_artifact_personal_use_actions','opt_in_player_inventory_window_open')},
            'opt_in_player_inventory_window_close':True,
            **{flag:False for flag in ('opt_in_holy_site_creation_create_once','opt_in_player_rite_creation_actions',
                'opt_in_player_pilgrimage_execution')}}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,client):
        out=self.work/('out-'+str(len(list(self.work.glob('out-*')))));out.mkdir()
        ctx={'product':A.PRODUCT,'case':A.CASE,'run_id':'synthetic-integrated','output':str(out),
            'shared_source_root':str(REPO),'case_contract':deepcopy(self.contract),'case_spec':deepcopy(self.spec)}
        result=A.run_case(ctx,client)
        return result
    def count(self,client,tool):return sum(x['tool']==tool for x in client.calls)
    def test_real_case_minimal_item_chain_and_two_fullid_pairs_keep_attribution_unknown(self):
        client=OwnedPublicClient(self.image);r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        self.assertEqual(r['actual_recipient_ids'],[15893,FULL_HOLDER])
        self.assertEqual(r['selected_artifact_id'],FULL_ITEM)
        self.assertEqual(self.count(client,Q.EQUIP),2);self.assertEqual(self.count(client,Q.ENSHRINE),1)
        self.assertTrue(r['enshrine_owner_slot_inventory_observed'])
        self.assertTrue(all(x['independent_pair_observed'] for x in r['actor_pairs']))
        self.assertEqual([x['unattributed_diplomacy_difference']for x in r['actor_pairs']],[1,1])
        self.assertFalse(r['site_attribution_observed']);self.assertIsNone(r['selected_site_contribution_raw'])
        self.assertFalse(r['required_slots']['E2-A1']['closed']);self.assertFalse(r['required_slots']['E2-A2']['location_specific_refusal_proven'])
        self.assertFalse(r['payment_total_proven']);self.assertLessEqual(r['public_calls_used'],96)
    def test_manual_equip_denial_never_dispatches_world_action(self):
        client=OwnedPublicClient(self.image);client.denied='equip_once_authorized';self.run_case(client)
        self.assertEqual(self.count(client,Q.EQUIP),0);self.assertEqual(self.count(client,Q.ENSHRINE),0)
    def test_inventory_no_call_uses_fresh_visibility_without_claiming_old_sequence(self):
        for history in (0,13):
            with self.subTest(history=history):
                client=OwnedPublicClient(self.image);client.inventory_no_call=True;client.inventory_no_call_historical=history
                r=self.run_case(client)
                self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
                self.assertTrue(r['inventory_open']['already_visible']);self.assertFalse(r['inventory_open']['new_open_observed'])
                self.assertEqual(self.count(client,Q.INVENTORY_POST),0);self.assertFalse(r['unknown_original_action'])
    def test_inventory_preinvoke_rejection_never_posts_retained_sequence(self):
        client=OwnedPublicClient(self.image);client.inventory_sequence=13;client.inventory_rejected=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.OPEN_INVENTORY),1);self.assertEqual(self.count(client,Q.INVENTORY_POST),0)
        self.assertEqual(self.count(client,Q.EQUIP),0);self.assertIn('preinvoke rejection',r['failure'])
    def test_unknown_inventory_ack_does_not_attribute_retained_query_sequence(self):
        client=OwnedPublicClient(self.image);client.inventory_sequence=13;client.inventory_unknown=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.OPEN_INVENTORY),1);self.assertEqual(self.count(client,Q.INVENTORY_POST),0)
        self.assertEqual(self.count(client,Q.EQUIP),0);self.assertTrue(r['unknown_original_action'])
    def test_unknown_equip_ack_has_no_sequence_recovery_and_is_never_replayed(self):
        client=OwnedPublicClient(self.image);client.unknown_equip=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.EQUIP),1);self.assertEqual(self.count(client,Q.ENSHRINE),0)
        self.assertTrue(r['unknown_original_action']);self.assertEqual(r['world_submissions']['unequip'],0)
    def test_pending_or_historical_post_cannot_authorize_unequip_or_shrine(self):
        for field in ('pending_post','historical'):
            with self.subTest(field=field):
                client=OwnedPublicClient(self.image);setattr(client,field,True);r=self.run_case(client)
                self.assertEqual(self.count(client,Q.EQUIP),1);self.assertEqual(self.count(client,Q.EQUIP_POST),3)
                self.assertEqual(self.count(client,Q.ENSHRINE),0);self.assertTrue(r['unknown_original_action'])
    def test_wrong_post_item_identity_never_dispatches_next_world_action(self):
        client=OwnedPublicClient(self.image);client.wrong_post_item=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.EQUIP),1);self.assertEqual(self.count(client,Q.ENSHRINE),0)
        self.assertNotIn('equip_post',r)
    def test_quote_changes_after_manual_review_prevent_shrine_confirm(self):
        client=OwnedPublicClient(self.image);client.change_preview_after_review=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.EQUIP),2);self.assertEqual(self.count(client,Q.ENSHRINE),0)
        self.assertIn('changed after review',r['failure'])
    def test_same_player_holder_deduplicates_and_does_not_fabricate_second_character(self):
        client=OwnedPublicClient(self.image);client.holder=15893;r=self.run_case(client)
        self.assertEqual(r['actual_recipient_ids'],[15893]);self.assertEqual(len(r['actor_pairs']),1)
        self.assertFalse(r['required_slots']['E2-A1']['closed'])
    def test_provider_attribution_claim_is_rejected_not_promoted_to_site_gain(self):
        client=OwnedPublicClient(self.image);client.claim_attribution=True;r=self.run_case(client)
        self.assertFalse(r['site_attribution_observed']);self.assertEqual(self.count(client,Q.EQUIP),0)
    def test_finite_queue_rejects_forbidden_world_ops_replacement_and_nonfullrefs(self):
        base={'id':'one','tool':Q.EQUIP,'args':{'artifact_id':FULL_ITEM,'desired_equipped':True,
            'expected_slot_index':0,'expected_replacing_artifact_id':None,'policy_positive':True},
            'fresh_revision':True,'continue_on_error':True}
        for change in ({'tool':'ck3_create_holy_site_once_v1'},{'tool':'ck3_remove_holy_site_relic_v1'},
                       {'args':{**base['args'],'artifact_id':0xffffffff}},
                       {'args':{**base['args'],'expected_replacing_artifact_id':7}}):
            with self.subTest(change=change),self.assertRaises(ValueError):Q.validate({'steps':[{**base,**change}]})
    def test_independent_actor_pair_rejects_target_faith_change(self):
        client=OwnedPublicClient(self.image);value=client.response(Q.ACTOR,{'character_id':FULL_HOLDER})
        after=deepcopy(value);after['faith_id']=51
        pairs=A.paired_actors({str(FULL_HOLDER):value},{str(FULL_HOLDER):after},[FULL_HOLDER])
        self.assertFalse(pairs[0]['independent_pair_observed']);self.assertIsNone(pairs[0]['unattributed_diplomacy_difference'])

    def test_public_after_only_rows_keep_actual_action_date_nested_and_capture_fresh_pre_read(self):
        client=OwnedPublicClient(self.image);r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        for record in r['submitted_rows']:
            row=record['row'];self.assertNotIn('before_snapshot',row)
            self.assertIsInstance(row['after_snapshot'],dict)
            if record['step']['tool'] not in A.READONLY_FRAMES:
                self.assertIn('independent_before_snapshot',record)
            if record['step']['tool']==Q.EQUIP:
                self.assertNotIn('date_raw',row['result'])
                self.assertEqual(row['result']['before']['date_raw'],51394920)
        self.assertEqual(r['public_calls_used'],len(client.calls)+client.snapshot_count)
        self.assertFalse(r['unknown_original_action'])

    def test_supplied_before_frame_is_still_validated(self):
        client=OwnedPublicClient(self.image);client.supplied_before=frame()
        client.supplied_before['played_character']['character_id']+=1
        r=self.run_case(client)
        self.assertEqual(self.count(client,Q.EQUIP),0)
        self.assertIn('failure',r)

    def test_parse_failure_after_actual_invocation_keeps_unknown_and_blocks_next_mutation(self):
        for field in ('date','pid','generation'):
            with self.subTest(field=field):
                client=OwnedPublicClient(self.image);client.bad_action_before=field;r=self.run_case(client)
                self.assertEqual(self.count(client,Q.EQUIP),1)
                self.assertEqual(self.count(client,Q.EQUIP_POST),0)
                self.assertEqual(self.count(client,Q.ENSHRINE),0)
                self.assertTrue(r['unknown_original_action']);self.assertEqual(r['world_submissions']['unequip'],0)

    def test_post_requires_original_sequence_before_and_current_owner_frame(self):
        for field in ('sequence','before','date','pid','generation'):
            with self.subTest(field=field):
                client=OwnedPublicClient(self.image);client.bad_post=field;r=self.run_case(client)
                self.assertEqual(self.count(client,Q.EQUIP),1)
                self.assertEqual(self.count(client,Q.ENSHRINE),0)
                self.assertTrue(r['unknown_original_action'])

    def test_complete_owned_list_skips_court_items_and_preserves_all_creation_previews_within_budget(self):
        client=OwnedPublicClient(self.image)
        client.owned=[237,188,189,FULL_ITEM,277];client.court={237,188,189,277}
        client.all_creation_types=True
        r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        self.assertEqual(r['selected_artifact_id'],FULL_ITEM)
        self.assertEqual(r['evidence']['inventory_refs'],client.owned)
        self.assertEqual([x['artifact_id']for x in r['evidence']['personal_probes']],[237,188,189,FULL_ITEM])
        self.assertEqual({x['selected_type_key']for x in r['evidence']['creation_samples']},Q.TYPES)
        self.assertTrue(r['evidence']['native_refusals'])
        self.assertFalse(r['evidence']['artifact_sample_complete'])
        self.assertTrue(all(x['args']['artifact_id']==FULL_ITEM for x in client.calls if x['tool']==Q.EQUIP))
        self.assertFalse(any(x['args']['artifact_id'] in client.court for x in client.calls if x['tool']==Q.ACTION_CONTEXT))
        self.assertLessEqual(r['public_calls_used'],70)

    def test_legal_personal_item_must_also_have_observed_can_enshrine(self):
        client=OwnedPublicClient(self.image);client.owned=[FULL_ITEM-1,FULL_ITEM]
        client.not_enshrinable={FULL_ITEM-1};r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        self.assertEqual(r['selected_artifact_id'],FULL_ITEM)
        self.assertFalse(r['evidence']['artifact_samples'][0]['can_enshrine'])

    def test_owned_inventory_is_never_silently_truncated_or_deduplicated(self):
        for owned in ([FULL_ITEM,FULL_ITEM],list(range(A.MAX_OWNED_REFS+1))):
            with self.subTest(owned_count=len(owned)):
                client=OwnedPublicClient(self.image);client.owned=owned;r=self.run_case(client)
                self.assertEqual(self.count(client,Q.EQUIP),0)
                self.assertIn('Complete bounded owned references malformed',r['failure'])

    def test_selection_exhaustion_keeps_full_chain_reserve_and_reports_incomplete_sampling(self):
        client=OwnedPublicClient(self.image);client.owned=list(range(A.MAX_OWNED_REFS));client.court=set(client.owned)
        r=self.run_case(client)
        self.assertEqual(r['evidence']['inventory_refs'],client.owned)
        self.assertFalse(r['evidence']['selection_complete'])
        self.assertIn('selection incomplete',r['failure'])
        self.assertLess(len(r['evidence']['personal_probes']),len(client.owned))
        self.assertEqual(self.count(client,Q.EQUIP),0)
        self.assertFalse(r['unknown_original_action']);self.assertLessEqual(r['public_calls_used'],96)

    def test_close_is_independent_once_after_unequip_post_and_before_holy_site_quote(self):
        client=OwnedPublicClient(self.image);r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        self.assertEqual(r['world_submissions']['inventory_open'],1)
        self.assertEqual(r['world_submissions']['inventory_close'],1)
        self.assertTrue(r['inventory_close']['new_close_observed'])
        self.assertNotEqual(r['inventory_open']['submit']['intent_sequence'],r['inventory_close']['submit']['intent_sequence'])
        self.assertTrue(A.inventory_hidden(r['inventory_close']['post']))
        self.assertTrue(A.inventory_hidden(r['inventory_close']['current']))
        def positions(tool):return [i for i,x in enumerate(client.calls)if x['tool']==tool]
        self.assertLess(positions(Q.EQUIP_POST)[-1],positions(Q.CLOSE_INVENTORY)[0])
        self.assertLess(positions(Q.CLOSE_INVENTORY)[0],positions(Q.INVENTORY_CLOSE_POST)[0])
        self.assertLess(positions(Q.INVENTORY_CLOSE_POST)[0],positions(Q.INVENTORY_CLOSE_QUERY)[-1])
        self.assertLess(positions(Q.INVENTORY_CLOSE_QUERY)[-1],positions('ck3_open_holy_site_window_v1')[-1])
        self.assertLessEqual(r['public_calls_used'],96)

    def test_unknown_close_ack_keeps_its_own_lock_without_borrowing_open_sequence(self):
        client=OwnedPublicClient(self.image);client.close_unknown=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.CLOSE_INVENTORY),1)
        self.assertEqual(self.count(client,Q.INVENTORY_CLOSE_POST),0)
        self.assertEqual(self.count(client,Q.ENSHRINE),0)
        self.assertTrue(r['unknown_original_action'])
        self.assertEqual(r['world_submissions']['inventory_open'],1)
        self.assertEqual(r['world_submissions']['inventory_close'],1)

    def test_pending_or_still_visible_close_never_enters_shrine_quote(self):
        for field in ('close_pending','close_keep_visible'):
            with self.subTest(field=field):
                client=OwnedPublicClient(self.image);setattr(client,field,True);r=self.run_case(client)
                self.assertEqual(self.count(client,Q.CLOSE_INVENTORY),1)
                self.assertEqual(self.count(client,Q.INVENTORY_CLOSE_POST),3)
                self.assertEqual(self.count(client,Q.ENSHRINE),0)
                self.assertTrue(r['unknown_original_action'])

    def test_close_post_cannot_cross_original_sequence_or_before_view(self):
        for field in ('close_wrong_sequence','close_bad_before'):
            with self.subTest(field=field):
                client=OwnedPublicClient(self.image);setattr(client,field,True);r=self.run_case(client)
                self.assertEqual(self.count(client,Q.CLOSE_INVENTORY),1)
                self.assertEqual(self.count(client,Q.ENSHRINE),0)
                self.assertTrue(r['unknown_original_action'])

    def test_final_close_query_must_still_be_hidden_before_quote(self):
        client=OwnedPublicClient(self.image);client.close_reappears=True;r=self.run_case(client)
        self.assertEqual(self.count(client,Q.CLOSE_INVENTORY),1)
        self.assertEqual(self.count(client,Q.ENSHRINE),0)
        self.assertTrue(r['unknown_original_action'])
        self.assertIn('visible/unknown before',r['failure'])

    def test_independently_already_hidden_inventory_does_not_force_an_extra_close(self):
        client=OwnedPublicClient(self.image);client.close_initial_hidden=True;r=self.run_case(client)
        self.assertEqual(r['status'],'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING')
        self.assertEqual(self.count(client,Q.CLOSE_INVENTORY),0)
        self.assertEqual(self.count(client,Q.INVENTORY_CLOSE_POST),0)
        self.assertTrue(r['inventory_close']['already_hidden']);self.assertFalse(r['inventory_close']['new_close_observed'])

    def test_close_queue_requires_independent_flag_and_rejects_combined_mutations(self):
        close={'id':'close-one','tool':Q.CLOSE_INVENTORY,'args':{},'fresh_revision':True,'continue_on_error':True}
        op={'id':'open-one','tool':Q.OPEN_INVENTORY,'args':{},'fresh_revision':True,'continue_on_error':True}
        self.assertTrue(Q.validate({'steps':[close]})['validated'])
        with self.assertRaises(ValueError):Q.validate({'steps':[op,close]})
        out=self.work/'missing-close-flag';out.mkdir()
        spec=deepcopy(self.spec);spec['opt_in_player_inventory_window_close']=False
        context={'product':A.PRODUCT,'case':A.CASE,'run_id':'synthetic-integrated','output':str(out),
            'case_contract':deepcopy(self.contract),'case_spec':spec}
        with self.assertRaisesRegex(ValueError,'Independent public flag missing'):
            A.validate_contract(context)

if __name__=='__main__':unittest.main(verbosity=2)
