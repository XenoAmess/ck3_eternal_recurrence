"""Central-only fresh native whole wire -> actual private transport -> source strict."""
import argparse, copy, importlib.util, json, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument('--native-stdout',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True); args=p.parse_args()
    own=Path(__file__).resolve().parents[1]/'src'/'xar_autoplayer'/'bridge'
    sys.path.insert(0,str(own.parent.parent))
    import xar_autoplayer.bridge as bridge
    bridge.__path__.insert(0,str(own))
    module_name='xar_autoplayer.bridge.player_prisoner_collection_private_transport'
    spec=importlib.util.spec_from_file_location(module_name,own/'player_prisoner_collection_private_transport.py')
    transport=importlib.util.module_from_spec(spec); sys.modules[module_name]=transport; spec.loader.exec_module(transport)
    from xar_autoplayer.bridge.prisoner_selected_quote_source_contract_12004 import normalize_prisoner_selected_quote_source_12004, SHA
    raw=args.native_stdout.read_bytes().decode('utf-8').replace('\r\n','\n')
    wire=json.loads(raw.split('SOURCE_WIRE_BEGIN\n',1)[1].split('\nSOURCE_WIRE_END',1)[0])
    cost=json.loads(raw.split('SOURCE_COST_BEGIN\n',1)[1].split('\nSOURCE_COST_END',1)[0])
    before={'snapshot_id':'native:17','revision':17,'native_revision':17,'date_raw':1,
            'paused':True,'map_ready':True,'played_character':{'character_id':0x41000001,'alive':True},
            'diagnostics':{'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':SHA}}}
    class Endpoint:
        request=None
        def send(self,value): self.request=value
    class State:
        def wait_for_command_result(self,request_id,timeout):
            frame=copy.deepcopy(wire); frame['request_id']=request_id
            frame['result']['step']=driver.endpoint.request['step']; return frame
    class Driver:
        allow_private_prisoner_collection_query=True
        endpoint=Endpoint(); state=State()
        def take_internal_semantic_snapshot(self): return copy.deepcopy(before)
    driver=Driver()
    result=transport.query_player_prisoner_collection_private_v1(driver,expected_revision=17)
    source=result['prisoner_selected_quote_source_12004']
    assert source['samples'][0]['recipient_score']['native_final_output_q64']==-123456
    assert source['samples'][0]['frame']['date_raw']==1
    kw=dict(native_revision=17,query_sequence=23,proof_epoch=29,date_raw=1,
            jailer_full_id=0x41000001,prisoner_full_id=0x41000002,source_ordinal=0,quote_kind='ordinary_ransom')
    checks=2
    def reject(value,kwargs=kw):
        nonlocal checks
        try: normalize_prisoner_selected_quote_source_12004(value,**kwargs)
        except ValueError: checks+=1; return
        raise AssertionError('unbound new source accepted')
    mutated=copy.deepcopy(source); mutated['samples'][0]['frame']['prisoner_full_id']=0x42000002; reject(mutated)
    mutated=copy.deepcopy(source); mutated['samples'][0]['frame']['query_sequence']=24; reject(mutated)
    mutated=copy.deepcopy(source); mutated['samples'][0]['recipient_score']['modifier_count_raw_i32']=1; reject(mutated)
    mutated=copy.deepcopy(source); mutated['samples'][0]['recipient_score']['native_final_output_q64']=None
    mutated['samples'][0]['recipient_score']['projected_value_matches_native_final']=None
    normalize_prisoner_selected_quote_source_12004(mutated,**kw); checks+=1
    mutated=copy.deepcopy(source); sample=mutated['samples'][0]; sample['frame']['date_raw']=None
    sample['source_answer_raw_u8']=None; sample['answer_source_ready']=False; sample['answer_effects_source_ready']=False
    score=sample['recipient_score']; score['projected_q64']=None; score['numeric_source_ready']=False
    score['projected_value_matches_native_final']=None; score['unavailable_reason']='source_frame_date_unavailable'
    normalize_prisoner_selected_quote_source_12004(mutated,**kw); checks+=1
    cost_kw={**kw,'quote_kind':'negotiated_preview'}
    normalize_prisoner_selected_quote_source_12004(cost,**cost_kw); checks+=1
    expected=[-100000,0,100000,0,200000,-200000,0,100000,-100000,0]
    assert cost['samples'][0]['actor_on_send_costs']['projected_q64']==expected; checks+=1
    mutated=copy.deepcopy(cost); mutated['samples'][0]['actor_on_send_costs']['projected_q64'][0]=0; reject(mutated,cost_kw)
    receipt={'schema':'prisoner-selected-quote-source-wire-first/1','status':'GREEN','checks':checks,
             'source_input':'same new C++ stdout','native_calls_from_python':0,'old_test_entries_called':0,
             'game_runtime_qualification':False,'private_transport_called_once':True,
             'source_and_native_outputs_separate':True}
    args.result.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__': main()
