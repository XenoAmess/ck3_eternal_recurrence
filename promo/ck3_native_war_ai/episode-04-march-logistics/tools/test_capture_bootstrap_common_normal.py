"""One real normal-Save DTO/closure compound; no SDK or large-save reads.

--proof consumes the exact R213 public receipts. Its large payload identity is
explicitly substituted by the native Save declaration. Default uses a tiny
portable fixture with the same null native_campaign DTO, never live credit.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch

OPTIONS=None
REL='promo/ck3_native_war_ai/episode-04-march-logistics/tools/capture_bootstrap.py'

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class CommonNormalCheckpointTests(unittest.TestCase):
    def test_original_null_campaign_DTO_and_legacy_guard_compound(self):
        repo=Path(OPTIONS.source_repo) if OPTIONS else Path(__file__).resolve().parents[4]
        stage=Path(OPTIONS.stage_root) if OPTIONS and OPTIONS.stage_root else repo
        self.addCleanup(setattr,sys,'path',list(sys.path))
        sys.path[:0]=[str(repo),str(repo/'tools'),str(repo/'ck3_autonomous_player/src'),str(repo/Path(REL).parent)]
        spec=importlib.util.spec_from_file_location('e04_common_normal_checkpoint_compound',stage/REL)
        subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)
        subject.ROOT=repo
        root=Path(OPTIONS.work_root) if OPTIONS and OPTIONS.work_root else Path(tempfile.mkdtemp(prefix='e04-common-normal-source-'))
        root.mkdir(parents=True,exist_ok=True)
        actual=bool(OPTIONS and OPTIONS.proof)
        if actual:
            proof_path=Path(OPTIONS.proof);proof=json.loads(proof_path.read_bytes())
            source=Path(proof['source']['path']);profile_path=Path(proof['normal_campaign_provenance']['profile']['path'])
        else:
            profile=root/'profile';(profile/'save games').mkdir(parents=True,exist_ok=True)
            source=profile/'save games/xar_checkpoint.ck3';source.write_bytes(b'portable-native-campaign-save-fixture')
            dlc=write(profile/'dlc_load.json',{'enabled_mods':[],'disabled_dlcs':[]})
            profile_path=root/'profile-preparation.json'
            profile_ref=write(profile_path,{'schema':'ck3-mod-acceptance-prepared-product-v1','fixture_mounted':False,
                'state_dir':str(root),'profile_dir':str(profile),'game_version':'1.20.0.4','steam_build_id':'25734779',
                'exe_sha256':subject.game_target('1.20.0.4')['exe_sha256'],'files':{'dlc_load.json':dlc}})
            run='fixture-public-run';frame={'date_raw':53148432,'paused':True,'map_ready':True,'local_player_id':1,
                'episode_projection':'native_campaign','played_character':{'character_id':33388},
                'diagnostics':{'bridge_pid':27056,'connection_generation':1},
                'managed_campaign_run_binding':{'run_id':run,'state_dir':str(root)},
                'player_armies':[{'army_id':0,'owner_character_id':33388,'current_province_id':2170,'route_province_ids':[]}]}
            cp={'status':'saved','path':str(source),'size':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'date_raw':53148432,'episode_projection':'native_campaign','succession_lifecycle':None,
                'episode_character_id':None,'episode_run_id':None}
            body={'step':'save-checkpoint','accepted':True,'checkpoint':cp}
            save_ref=write(root/'save.json',{'rows':[{'id':'original-save','ok':True,'plan':{'tool':'ck3_save_checkpoint','args':{'expected_revision':141}},
                'result':body,'after_snapshot':frame,'started_at':'2026-10-18T17:14:45Z','finished_at':'2026-10-18T17:14:50Z'}]})
            after_ref=write(root/'after.json',{'rows':[{'id':'independent-after','ok':True,'plan':{'tool':'ck3_take_snapshot'},
                'after_snapshot':copy.deepcopy(frame),'started_at':'2026-10-18T17:14:51Z'}]})
            machine=subject.current_machine_id()
            cleanup=write(root/'cleanup.json',{'machine_id':machine,'run_id':run,'actual_binding':{'run_id':run,'pid':27056,'create_time':1792338019.838657},
                'cleanup':{'errors':[],'normal_Save_verified':True,'sampling_OFF_clear_verified':True,'Save_result':body}})
            close=write(root/'close.json',{'normal_close_qualified':True,'retained_handle':{'actual_retained_os0':True,'pid':27056,'exit_code':0,'create_time':1792338019.838657},
                'native_zero_proof':{'pid':27056,'process_exit_code':0,'shutdown':{'ck3_pid':27056,'tree_gone':True,'cleanup_proven':True}}})
            host=write(root/'host.json',{'run_id':run,'actual_original_popen_wait':True,'returncode':0})
            proof={'schema':'xar.e04.normal-source-promotion-candidate.v1','machine_id':machine,'source_run_id':run,
                'source':{'path':str(source),'bytes':cp['size'],'sha256':cp['sha256']},
                'actual_save':{'reference':save_ref,'pointer':'/rows/0/result/checkpoint'},
                'independent_after':{'reference':after_ref,'pointer':'/rows/0/after_snapshot','army':{'army_id':0}},
                'normal_campaign_provenance':{'profile':profile_ref},'closure':{'cleanup':cleanup,'normal_close':close,'host_original_wait':host}}
            proof_path=root/'proof.json';write(proof_path,proof)
        original_identity=subject.identity
        payload_calls=[]
        def bounded_identity(path):
            if actual and path.resolve()==source.resolve():
                payload_calls.append(str(path));return {**proof['source'],'path':str(path.resolve())}
            return original_identity(path)
        original_reader=subject._checkpoint_small_json
        with patch.object(subject,'identity',side_effect=bounded_identity):
            result=subject.checkpoint_source(source,proof_path,profile_path,subject.game_target('1.20.0.4'),33388)
            self.assertEqual((result['actor_id'],result['date_raw'],result['source_lifecycle']),(33388,53148432,None))
            self.assertTrue(result['original_episode_fields_preserved'])
            if actual:self.assertEqual(len(payload_calls),1)
            save_ref=proof['actual_save']['reference'];after_ref=proof['independent_after']['reference']
            def changed(ref,kind):
                value=copy.deepcopy(original_reader(ref))
                if ref==save_ref and kind=='one-life':value['rows'][0]['result']['checkpoint']['episode_projection']='rogue_one_life'
                if ref==after_ref and kind=='local-player':value['rows'][0]['after_snapshot']['local_player_id']+=1
                if ref==proof['closure']['host_original_wait'] and kind=='host-exit':value['returncode']=1
                return value
            for kind in ('one-life','local-player','host-exit'):
                with self.subTest(guard=kind),patch.object(subject,'_checkpoint_small_json',side_effect=lambda ref:changed(ref,kind)):
                    with self.assertRaises(ValueError):subject.checkpoint_source(source,proof_path,profile_path,subject.game_target('1.20.0.4'),33388)
            # Original SDK route still rejects a one-life/missing normal lifecycle.
            raw=copy.deepcopy(original_reader(save_ref)['rows'][0]['result'])
            raw['checkpoint']['succession_lifecycle']={'lifecycle':'rogue_one_life','xar_enabled':'xar_on',
                'pact_contract':'terminal_settlement_required','source':'legacy-driver-default'}
            legacy=root/'legacy-one-life-guard.json'
            write(legacy,{'is_error':False,'request':{'tool':'ck3_save_checkpoint','arguments':{}},'body':raw})
            with self.assertRaisesRegex(ValueError,'pure vanilla ordinary campaign'):
                subject.checkpoint_source(source,legacy,profile_path,subject.game_target('1.20.0.4'),33388)
        print(json.dumps({'actual_R213_small_sources':actual,'large_save_identity_substituted':actual,
            'large_save_payload_reads':0 if actual else 'tiny-portable-fixture-only','actual_native_or_business_credit':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repo',type=Path,default=Path.cwd())
    parser.add_argument('--stage-root',type=Path)
    parser.add_argument('--proof',type=Path)
    parser.add_argument('--work-root',type=Path)
    OPTIONS,remaining=parser.parse_known_args()
    unittest.main(argv=[sys.argv[0],*remaining])
