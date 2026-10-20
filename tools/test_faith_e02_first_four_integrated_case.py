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
sys.path[:0]=[str(REPO/'tools'),str(REPO)]

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

def scout(case,evidence):
    # Original scout's own 12 finite consumers are retained separately. This
    # fixture starts at its actual caller shape, never claims a live character.
    evidence.update(site_ids=[SITE],site_observations=[{'site_id':SITE,'relic':{
        'county_context':{'available':True,'county_holder_id':case.client.holder}}}],
        artifact_samples=[{'artifact_id':FULL_ITEM,'site_id':SITE,'owned_by_player':True,
            'can_enshrine':True,'equipped':False}],
        native_refusals=[{'scope':'type_CanPick_not_automatically_location','original_text':'AUTHORED original reason'}])

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
    def snapshot(self,**kwargs):return self.validate_frame(frame())
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
            before=frame()
            if tool==Q.EQUIP and self.unknown_equip:
                self.equipped=args['desired_equipped']
                rows.append({'id':step['id'],'ok':False,'error':'AUTHORED lost ACK',
                    'before_snapshot':before,'after_snapshot':frame()});continue
            if tool==Q.OPEN_INVENTORY and self.inventory_unknown:
                self.visible=True;self.inventory_sequence=17
                rows.append({'id':step['id'],'ok':False,'error':'AUTHORED lost inventory ACK',
                    'before_snapshot':before,'after_snapshot':frame()});continue
            rows.append({'id':step['id'],'ok':True,'result':self.response(tool,args),
                'before_snapshot':before,'after_snapshot':frame()})
        return rows
    def response(self,tool,args):
        common={'available':True,'played_character_id':15893,'date_raw':51394920,'read_only':True}
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
        if tool==Q.ARTIFACT:return self.item()
        if tool==Q.EQUIP:
            self.equipped=args['desired_equipped']
            return {'available':True,'artifact_id':FULL_ITEM,'intent_sequence':21 if self.equipped else 22,
                'desired_equipped':self.equipped,'needs_recovery':True,'invoked':True}
        if tool==Q.EQUIP_POST:
            resolved=not self.pending_post and not self.historical
            return {'available':True,'artifact_id':FULL_ITEM+1 if self.wrong_post_item else FULL_ITEM,
                'desired_equipped':self.equipped,'desired_inventory_state_observed':resolved,
                'status':'desired_inventory_state_observed'if resolved else'intent_previously_resolved_current_state_not_observed'if self.historical else'intent_pending_or_unknown'}
        if tool=='ck3_select_holy_site_relic_artifact_v1':self.selected=True
        if tool==Q.ACTION_CONTEXT:return self.action_context()
        if tool==Q.ENSHRINE:
            self.enshrined=True
            return {'invoked':True,'available':True,'business_outcome_observed':False}
        if tool==Q.RELIC_CONTEXT:return {**common,'requested_holy_site_id':SITE,'inventory':{'available':True,
            'artifact_ids':[FULL_ITEM]if self.enshrined else[],
            'slots':[{'slot_index':0,'artifact_id':FULL_ITEM if self.enshrined else None}]},
            'current_relic_evaluation':{'available':True,'is_active':self.enshrined,'active_artifact_rarity_sum':4 if self.enshrined else 0}}
        if tool=='ck3_query_player_holy_site_relic_permissions_v1':return {**common,'requested_holy_site_id':SITE,
            'requested_artifact_id':args.get('artifact_id'),
            'player_inventory':{'available':True,'owner_matches_player':True,'artifact_ids':[]if self.enshrined else[FULL_ITEM]}}
        return {**common,'invoked':True}
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
    def item(self):
        return {'available':True,'read_only':True,'date_raw':51394920,'played_character_id':15893,
            'requested_artifact_id':FULL_ITEM,'personally_owned':not self.enshrined,'inventory_artifact':True,
            'equipped':self.equipped,'inventory_view_visible':self.visible,'native_equipped_observed':True,
            'can_equip_in_effective_slot':not self.equipped,'can_unequip':self.equipped,
            'effective_slot_index':0,'equipped_slot_index':0 if self.equipped else None,
            'replacing_artifact_id':FULL_ITEM if self.equipped else None,'personal_net_effect_attributed':False,
            'modifier_description':{'available':True,'text':'AUTHORED item definition; not a net skill gain'}}
    def action_context(self):
        return {'available':True,'read_only':True,'played_character_id':15893,'date_raw':51394920,
            'requested_holy_site_id':SITE,'requested_artifact_id':FULL_ITEM,'selected_artifact_matches_request':self.selected,
            'preview_identity_available':True,'preview_identity_sha256':self.preview,
            'selected_action_effect_description':{'available':True,'text':'AUTHORED original quote'},
            'artifact_ownership':{'available':True,'artifact_id':FULL_ITEM,'character_owner_id':None if self.enshrined else 15893,
                'holy_site_owner_id':SITE if self.enshrined else None,'character_owner_matches_player':not self.enshrined,
                'player_owned_reference_member':not self.enshrined,'player_equipped_slot_member':{'available':True,'value':self.equipped}},
            'destination':{'available':True,'action_kind':'enshrine','effective_slot_index':0,'replacing_artifact_id':None},
            'permissions':{group:{'can_enshrine':{'available':True,'value':not self.enshrined}}
                for group in ('artifact_permissions','current_buttons')}}

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
        quals=A.ORIGIN.parents[2]
        providers=[quals/package/'SDK-DELIVERY.actual.json'for package in
            ('faith-observers-sdk-a02','actor-skill-effects-sdk-a02','inventory-open-sdk-a01')]
        cls.contract={'schema':'faith-e02-first-four-integrated-case-v1','product':A.PRODUCT,'case':A.CASE,
            'machine_id':'4-8e1c2f1861','saved_input':{'save':'authored-not-restored.ck3',**A.S.SAVE},
            'profile':{'enabled_mods':[],'product_files':[]},'scope':A.SCOPE,'max_public_calls':A.MAX_CALLS,
            'dependencies':[M.pin(path)for path in dependencies],
            'provider_source_evidence':[M.pin(path)for path in providers]}
        cls.spec={'required_mcp_tools':sorted(A.REQUIRED),'opt_in_read_only_mcp_tools':sorted(Q.READONLY),
            **{flag:True for flag in ('opt_in_holy_site_creation_ui','opt_in_holy_site_relic_actions',
                'opt_in_player_artifact_personal_use_actions','opt_in_player_inventory_window_open')},
            **{flag:False for flag in ('opt_in_holy_site_creation_create_once','opt_in_player_rite_creation_actions',
                'opt_in_player_pilgrimage_execution')}}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,client):
        out=self.work/('out-'+str(len(list(self.work.glob('out-*')))));out.mkdir()
        ctx={'product':A.PRODUCT,'case':A.CASE,'run_id':'synthetic-integrated','output':str(out),
            'shared_source_root':str(REPO),'case_contract':deepcopy(self.contract),'case_spec':deepcopy(self.spec)}
        with patch.object(A.S,'collect_scout',scout):result=A.run_case(ctx,client)
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

if __name__=='__main__':unittest.main(verbosity=2)
