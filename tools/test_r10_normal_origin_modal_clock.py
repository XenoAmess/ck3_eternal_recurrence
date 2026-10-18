"""One source-only compound: common normal origin and B original-clock modals."""
from pathlib import Path
from types import SimpleNamespace as NS
from copy import deepcopy
from unittest.mock import patch
import argparse, hashlib, importlib.util, json, sys, tempfile, unittest

p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--candidate-root',type=Path)
p.add_argument('--actual-proof',type=Path)
p.add_argument('--actual-prepare',type=Path)
p.add_argument('--receipt',type=Path)
o,rest=p.parse_known_args()
stage=o.candidate_root or o.repo_root
sys.path[:0]=[str(o.repo_root/'tools'),str(o.repo_root/'ck3_autonomous_player/src')]
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0,str(stage/'tools/ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import r10_common_arm as subject
from ck3_live_run_id import current_machine_id
bp='promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison/strategy_b_normal_stages.py'
spec=importlib.util.spec_from_file_location('r10_B_modal_candidate',stage/bp)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,indent=2)+'\n').encode();path.write_bytes(raw)
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def portable(root,machine):
    # Default CI: legacy normal positive plus modal tests. Actual args test
    # the new original-common branch without copying source-machine payloads.
    state=root/'state';profile=state/'profile';sha='b'*64;actor=33388;date=53149056
    saved={'status':'saved','size':1,'sha256':sha,'date_raw':date,'episode_character_id':actor,
        'succession_lifecycle':{'lifecycle':'ordinary_campaign_succession','xar_enabled':'xar_off',
            'source':'pure-vanilla-enabled-mods-empty','pact_contract':'absent_by_fresh_campaign_xar_off_contract'}}
    proof={'is_error':False,'body':{'accepted':True,'checkpoint':saved}}
    source={'save':{'sha256':sha,'bytes':1},'actor_id':actor,'date_raw':date}
    prepared={'startup':{'mode':'saved_campaign','state_dir':str(state),'saved_campaign':{'sha256':sha,'bytes':1,'player_id':actor,'date_raw':date}}}
    profile_info={'profile_dir':str(profile),'fixture_mounted':False,'provenance':{'normal_checkpoint':source}}
    inventory={'schema':'ck3-saved-campaign-vanilla-profile-v1','enabled_mods':[],'product_files':[],'profile_path':str(profile)}
    return proof,prepared,profile_info,inventory

class Compound(unittest.TestCase):
    def test_actual_normal_origin_and_modal_original_clock(self):
        machine=current_machine_id()
        with tempfile.TemporaryDirectory(prefix='r10-source-contract-') as tmp:
            root=Path(tmp)
            actual=o.actual_proof is not None
            self.assertEqual(actual,o.actual_prepare is not None)
            if actual:
                proof=json.loads(o.actual_proof.read_bytes());receipt=json.loads(o.actual_prepare.read_bytes())
                self.assertEqual(receipt['exit_code'],0)
                prepared=subject.small_json(receipt['prepared_case'])
                profile=subject.small_json(receipt['profile_preparation'])
                inventory=subject.small_json(prepared['preparation']['profile_preparation']['product_inventory'])
            else:proof,prepared,profile,inventory=portable(root,machine)
            original=deepcopy((proof,prepared,profile,inventory))
            prepared=deepcopy(prepared);prepared.update(schema='ck3-mod-acceptance-prepared-case-v1',product='war-episode04-r10',case='r10-common-arm')
            seed=prepared['startup']['saved_campaign'];run='synthetic-independent-formal-context'
            context={'schema':'ck3-mod-acceptance-run-context-v1','run_id':run,'run_dir':str(root/run),'product':prepared['product'],'case':prepared['case']}
            frozen={'run_id':run,'identity_allocation':{'machine_id':machine},'state_dir':prepared['startup']['state_dir'],'mod_key':'war-episode04-r10'}
            source=profile['provenance']['normal_checkpoint']
            origin=subject.small_json(proof['normal_campaign_provenance']['profile']) if actual else {'game_version':'1.20.0.4','steam_build_id':'25734779','exe_sha256':'e'*64}
            plan={'normal_save':{'bytes':seed['bytes'],'sha256':seed['sha256']},'t0_raw':seed['date_raw'],
                'build':{'source_head':'a'*40,'version':origin['game_version'],'steam_build':int(origin['steam_build_id']),'exe_sha256':origin['exe_sha256']}}
            args=(context,prepared,frozen,profile,inventory,proof)
            result=subject.validate_normal_common_source(*args,machine=machine,source_head='a'*40,plan=plan)
            self.assertEqual((result['actor'],result['date_raw']),(33388,53149056))
            self.assertEqual(proof,original[0]);self.assertEqual(profile,original[2])
            saved=subject.small_json(proof['actual_save']['reference'])['rows'][0]['result']['checkpoint'] if actual else proof['body']['checkpoint']
            if actual:self.assertIsNone(saved['succession_lifecycle']);self.assertIsNone(saved['episode_character_id'])
            original_loader=subject.small_json
            for ref,mutate in (((proof['closure']['host_original_wait'],lambda v:v.update(returncode=1)),
                (proof['independent_after']['reference'],lambda v:v['rows'][0]['after_snapshot'].update(local_player_id=-1))) if actual else ()):
                def load(pin,limit=1024*1024):
                    value=deepcopy(original_loader(pin,limit))
                    if pin==ref:mutate(value)
                    return value
                with patch.object(subject,'small_json',side_effect=load),self.assertRaises(ValueError):
                    subject.validate_normal_common_source(*args,machine=machine,source_head='a'*40,plan=plan)
            legacy={'is_error':False,'body':{'accepted':True,'checkpoint':{**saved,'succession_lifecycle':{'lifecycle':'rogue_one_life','xar_enabled':'xar_on'}}}}
            with self.assertRaises(ValueError):subject.validate_normal_common_source(*args[:-1],legacy,machine=machine,source_head='a'*40,plan=plan)
            calls=[];claims=[]
            status={'state':'armed','generation':7,'starting_date_raw':1000,'target_date_raw':1024}
            clock=NS(modals=[])
            def resolve(frame):
                clock.modals.append({'same_window_gone':True});return {**frame,'active_event':None}
            clock.handle_modals=resolve;clock.clock_status=lambda:dict(status)
            live=NS(_clock=clock,request=lambda name,tool,args:(calls.append((name,tool,args)) or {'body':{'accepted':True}},{}))
            st=NS(live=live)
            claim={'start':1000,'target':1024,'arm':{'request_id':'original-arm'},'resume':{'request_id':'original-resume'}}
            frame={'date_raw':1000,'paused':True,'active_event':{'instance_id':1},'pending_character_interaction':None}
            with patch.object(b,'store',side_effect=lambda st,name,value:claims.append((name,value))):
                after=b._continue_original_day_modals(st,frame,claim,{'generation':7})
                self.assertIsNone(after['active_event']);self.assertEqual([x[2]['step'] for x in calls],['resume-map'])
                self.assertFalse(claims[0][1]['new_Arm']);self.assertEqual(claims[0][1]['generation'],7)
                calls.clear();status['generation']=8
                with self.assertRaises(ValueError):b._continue_original_day_modals(st,frame,claim,{'generation':7})
                self.assertEqual(calls,[])
                status['generation']=7;at_target={**frame,'date_raw':1024}
                b._continue_original_day_modals(st,at_target,claim,{'generation':7});self.assertEqual(calls,[])
                clock.handle_modals=lambda f:(_ for _ in ()).throw(TimeoutError('original selection result unknown'))
                with self.assertRaises(TimeoutError):b._continue_original_day_modals(st,frame,claim,{'generation':7})
                self.assertEqual(calls,[])
                clock.handle_modals=resolve
                live.request=lambda *a:(calls.append(a) or {'body':{'accepted':False}}, {})
                with self.assertRaises(ValueError):b._continue_original_day_modals(st,frame,claim,{'generation':7})
                b._continue_original_day_modals(st,after,claim,{'generation':7})
                self.assertEqual(len(calls),1)  # unknown Resume is not replayed
            facts={'machine_id':machine,'actual_Mar31_small_chain':actual,'original_native_episode_fields_still_null':True if actual else None,
                'source_only_formal_context':True,'actual_formal_or_game_credit':False,'large_save_read_or_hashed':False,
                'compound_tests':1,'SDK_calls':0,'source_gate_and_modal_counterexamples':'PASS'}
            if o.receipt:write(o.receipt,facts)
            print(json.dumps(facts))

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
