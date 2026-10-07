"""Pure three-way retained JSON compare for the explicit grant-numeric diagnostic contract."""
from pathlib import Path
import argparse,hashlib,json,sys
sys.dont_write_bytecode=True
P=Path(__file__).parent;B=Path('C:/workspace/ck3_lyd_runtime_20261004');HEAD='9208b46c95b9dc13ab70bd2d11a0c146dd1fd412'
D=B/'r16-political-heir-diagnostic-source-20261007-004'
sys.path.insert(0,str(D))
from diagnostic_baseline_adapter_v2 import checked,load_packet,need
def ref(path):
 path=Path(path).resolve();need(path.stat().st_size<=2*1024*1024,'Retained JSON byte bound');raw=path.read_bytes()
 return {'path':path.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def entries(node,key):return [row.get('value') for row in node.get('entries',[]) if row.get('key')==key]
def titles(state):
 if 'protected_titles' in state:return {str(node['title_id']):node for node in state['protected_titles']}
 need(type(state.get('political7')) is dict,'Explicit retained political7/protected_titles required');return state['political7']
def view(node):return {'holder':node.get('holder'),'full_AST_sha256':node.get('AST_sha256'),'heir_raw_rows':entries(node,'heir'),'succession_result_type':entries(node,'succession_result_type'),'succession_laws':entries(node,'succession_laws'),'laws':entries(node,'laws')}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('cold-state','cold-input','author-result','qualified-native','baseline-input','metadata-result'):
  p.add_argument('--'+name,type=Path,required=True);p.add_argument('--'+name+'-sha256',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();refs={};data={}
 for name in ('cold_state','cold_input','author_result','qualified_native','baseline_input','metadata_result'):
  row=ref(getattr(a,name));need(row['sha256']==getattr(a,name+'_sha256'),'Explicit retained JSON SHA differs: '+name);refs[name]=row;data[name]=json.loads(checked(row)[1])
 packet=load_packet(refs['baseline_input']);cold=data['cold_state'];source=data['cold_input'];metadata=data['metadata_result'];result=data['author_result'];qualified=data['qualified_native']
 need(refs['baseline_input']['sha256']=='d0fe32c4f6a7e4cf2cb1db0fcb77b9ac771482c2381b52cce76a303678277baa','Exact diagnostic RED-B5 packet required')
 need(source['schema']=='lyd.next-cold.actual-checkpoint-author-request.grant-numeric.v1' and source['expected_source_head']==HEAD and source['window']=='baseline','New explicit baseline-only grant-numeric INPUT required')
 need(Path(source['metadata_result']).resolve()==a.metadata_result.resolve() and metadata['head']==HEAD and metadata['tool_count']==28 and metadata['grant_title_picker_opt_in'] is True,'Actual9208 official grant28 metadata binding required')
 need(result['status']=='ACTUAL_COMPACT_NATIVE_SAVED_OBSERVATIONS_JOINED' and result['save_body_reads']==1,'Original exact author single-scan/native-joined result required')
 need(any(row['path']==refs['qualified_native']['path'] and row['sha256']==refs['qualified_native']['sha256'] for row in result['outputs']),'Qualified JSON must be an exact original author output')
 need(result['source_refs']['profile']['sha256']=='38d54bd94502de17874ca2b5269955fa495a0598793ff5ae06ce25b781ac2dfb','Exact R16 profile source binding required')
 need(result['source_refs']['metadata_result']==refs['metadata_result'],'Exact author/metadata RESULT ref required')
 need(cold['checkpoint_sha256']==source['preserved_checkpoint']['sha256'],'Actual cold STATE/checkpoint descriptor differs')
 raw_refs={key:ref(source[key]) for key in ('checkpoint_receipt','G2_receipt','G3_receipt')}
 for key,row in raw_refs.items():need(result['source_refs'][key]==row,'Author original receipt ref changed: '+key)
 cp=json.loads(checked(raw_refs['checkpoint_receipt'])[1]);need(cold['identity']['pid']!=14452 and cold['identity']['session_id']==cp['session_id'] and cold['identity']['pid']==result['after_frame_binding']['game_pid'],'Fresh actual cold native identity required')
 before=json.loads(checked(packet['original0240_state'])[1]);b5=json.loads(checked(packet['state'])[1])
 maps={'original0240':titles(before),'saved_R15_B5_RED':titles(b5),'new_R16_cold':titles(cold)};rows=[]
 for full_id in ('2230','2231','2232','2235','2262','2263','2264'):
  need(all(full_id in items for items in maps.values()),'Political full ID missing: '+full_id)
  values={name:view(items[full_id]) for name,items in maps.items()}
  rows.append({'title_full_id':int(full_id),'observations':values,'new_cold_full_AST_equals_saved_B5':values['new_R16_cold']['full_AST_sha256']==values['saved_R15_B5_RED']['full_AST_sha256'],'new_cold_heir_rows_equal_original0240':values['new_R16_cold']['heir_raw_rows']==values['original0240']['heir_raw_rows'],'new_cold_heir_rows_equal_saved_B5':values['new_R16_cold']['heir_raw_rows']==values['saved_R15_B5_RED']['heir_raw_rows']})
 out=a.output.resolve();need(out.is_relative_to(B) and not out.exists(),'Fresh external compare output required');out.mkdir(parents=True,exist_ok=False)
 report={'status':'PURE_RETAINED_PARSED_THREE_WAY_POLITICAL_HEIR_COMPARE_NO_FORMAL_PASS','inputs':refs,'native_original_refs':raw_refs,'new_checkpoint_descriptor':source['preserved_checkpoint'],'baseline_original_refs':packet,'political_titles':rows,'native_frame_qualification':'Retains exact original author native-joined artifacts; comparison adds no qualification','original_author_status':result['status'],'original_G2_status':qualified['G2_status'],'original_G3_status':qualified['qualified_native_head']['status'],'formal_acceptance':None,'new_T_acceptance':None,'C3_credit':None,'I4_credit':None,'SDK_calls':0,'game_calls':0,'save_body_reads':0,'main_writes':0}
 with (out/'REPORT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'report':ref(out/'REPORT.json'),'formal_acceptance':None}));return 0
if __name__=='__main__':raise SystemExit(main())
