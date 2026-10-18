"""One compound regression: normal-source proof instead of legacy ID inference."""
from pathlib import Path
from copy import deepcopy
import argparse
import importlib.util
import json
import sys
import unittest

_parser=argparse.ArgumentParser(add_help=False)
_parser.add_argument('--source-repo',type=Path,default=Path(__file__).resolve().parents[1])
_parser.add_argument('--preparation-candidate',type=Path)
_args,_remaining=_parser.parse_known_args()
sys.path.insert(0,str(_args.source_repo/'tools'))
sys.path.insert(0,str(_args.source_repo/'ck3_autonomous_player/src'))
import ck3_mod_acceptance_cases
if _args.preparation_candidate:
    ck3_mod_acceptance_cases.__path__.append(str(_args.preparation_candidate/'tools/ck3_mod_acceptance_cases'))
ck3_mod_acceptance_cases.__path__.append(str(Path(__file__).parent/'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases.r10_common_arm import validate_normal_common_source, full_query_with_one_same_date_rebound


class ActualCommonShape(unittest.TestCase):
    def test_common_product_id_with_real_empty_profile_and_normal_source(self):
        # Actual common DTO field shapes, synthetic values: no SDK or game.
        machine='synthetic-machine'; head='a'*40; sha='b'*64
        run=machine+'--war-episode04-r10--R0001'
        root=Path(__file__).resolve().parent
        state=root/'synthetic-profile-not-created'
        context={'schema':'ck3-mod-acceptance-run-context-v1','run_id':run,'run_dir':str(root/run),
                 'product':'war-episode04-r10','case':'r10-common-arm'}
        saved={'sha256':sha,'size':1,'episode_character_id':33388,'date_raw':53147376,'status':'saved',
            'succession_lifecycle':{'lifecycle':'ordinary_campaign_succession','xar_enabled':'xar_off',
                'source':'pure-vanilla-enabled-mods-empty','pact_contract':'absent_by_fresh_campaign_xar_off_contract'}}
        normal={'is_error':False,'body':{'accepted':True,'checkpoint':saved}}
        profile={'profile_dir':str(state/'profile'),'fixture_mounted':False,'provenance':{'normal_checkpoint':{
            'save':{'sha256':sha,'bytes':1},'actor_id':33388,'date_raw':53147376}}}
        inventory={'schema':'ck3-saved-campaign-vanilla-profile-v1','enabled_mods':[],'product_files':[],
                   'profile_path':str(state/'profile')}
        prepared={'schema':'ck3-mod-acceptance-prepared-case-v1','product':'war-episode04-r10','case':'r10-common-arm',
            'startup':{'mode':'saved_campaign','state_dir':str(state),'saved_campaign':{
                'sha256':sha,'bytes':1,'player_id':33388,'date_raw':53147376}}}
        frozen={'run_id':run,'mod_key':'war-episode04-r10','state_dir':str(state),
                'identity_allocation':{'machine_id':machine}}
        plan={'normal_save':{'sha256':sha,'bytes':1},'t0_raw':53147376,'build':{'source_head':head}}
        args=(context,prepared,frozen,profile,inventory,normal)
        actual=validate_normal_common_source(*args,machine=machine,source_head=head,plan=plan)
        self.assertEqual(actual['run_id'],run)
        self.assertEqual(actual['mod_key'],'war-episode04-r10')
        self.assertFalse(actual['original_context_modified'])
        self.assertNotIn('identity',context)
        self.assertEqual(actual['actor'],33388)
        changed=deepcopy(inventory); changed['enabled_mods']=['fixture.mod']
        with self.assertRaisesRegex(ValueError,'actual empty-mod profile'):
            validate_normal_common_source(context,prepared,frozen,profile,changed,normal,
                machine=machine,source_head=head,plan=plan)
        bad=deepcopy(normal); bad['body']['checkpoint']['succession_lifecycle']['source']='controlled-fixture'
        with self.assertRaisesRegex(ValueError,'normal-source Save'):
            validate_normal_common_source(context,prepared,frozen,profile,inventory,bad,
                machine=machine,source_head=head,plan=plan)
        from xar_autoplayer.bridge.r05_supply_observation_case import StrengthRevisionDrift
        class IO:
            class Client:
                def checkpoint(self,*args):return None
            client=Client()
            def __init__(self, results):self.results=list(results);self.calls=[];self.fresh_reads=0
            def request(self,name,tool,args):
                self.calls.append((name,tool,args))
                outcome=self.results.pop(0)
                if isinstance(outcome,BaseException):raise outcome
                return outcome
            def snapshot(self,name):
                self.fresh_reads+=1
                return {**frame,'revision':2},{'source':'actual-fresh-test-stand-in'}
        frame={'paused':True,'date_raw':53147376,'revision':1,'episode_run_id':run,
            'diagnostics':{'bridge_pid':1,'connection_generation':1},
            'played_character':{'character_id':33388},
            'player_armies':[{'army_id':0,'owner_character_id':33388,'current_province_id':1506}]}
        failed=StrengthRevisionDrift({'synthetic_original_error_retained':True})
        io=IO([failed,({'body':{'synthetic_only':True}},{'source':'second-test-query'})])
        fresh,_,_,_=full_query_with_one_same_date_rebound(io,'sample',frame,{},[0])
        self.assertEqual((len(io.calls),io.fresh_reads,fresh['revision'],frame['revision']),(2,1,2,1))
        self.assertEqual(io.calls[1][2]['army_ids'],[0])
        lost=IO([TimeoutError('result unknown')])
        with self.assertRaises(TimeoutError):full_query_with_one_same_date_rebound(lost,'lost',frame,{},[0])
        self.assertEqual((len(lost.calls),lost.fresh_reads),(1,0))
        twice=IO([failed,failed])
        with self.assertRaises(StrengthRevisionDrift):full_query_with_one_same_date_rebound(twice,'twice',frame,{},[0])
        self.assertEqual((len(twice.calls),twice.fresh_reads),(2,1))


if __name__=='__main__':unittest.main(argv=[sys.argv[0],*_remaining])
