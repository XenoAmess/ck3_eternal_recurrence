"""ROOT-only author/check existing v3 R15 boundary from actual closed refs."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys
sys.dont_write_bytecode=True
from verify_previous_boundary import author_values,verify_previous_boundary_v3,byte_ref,need,BASE
def put(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def ref(p):return byte_ref(p)[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True,type=Path);p.add_argument('--sha256',required=True)
 modes=p.add_mutually_exclusive_group(required=True);modes.add_argument('--check',action='store_true');modes.add_argument('--create',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 raw,row=byte_ref(a.request);need(row['sha256']==a.sha256.lower(),'Actual author request SHA changed')
 review,helpers,checked=author_values(json.loads(raw))
 if a.check:
  print(json.dumps({'status':'ACTUAL_FUTURE_INPUTS_VERIFIED_NO_BOUNDARY_WRITTEN','request':row,'actual_limits':checked['actual_exit_observation_limits'],'main_writes':0,'SDK_calls':0,'game_calls':0,'process_lookups':0},ensure_ascii=False));return 0
 need(a.output is not None,'New explicit external output required');out=a.output.resolve()
 need(BASE in out.parents and not out.exists(),'Fresh external output required; no overwrite of any attempt');out.mkdir()
 try:
  put(out/'HELPERS-CLOSED.actual.json',helpers);review['helpers_closed']=ref(out/'HELPERS-CLOSED.actual.json')
  put(out/'PREVIOUS-BOUNDARY.actual.json',review);verified=verify_previous_boundary_v3({'review':ref(out/'PREVIOUS-BOUNDARY.actual.json')})
  put(out/'VERIFIED.actual.json',verified)
  for name in ['verify_previous_boundary.py','DEPENDENCIES.json']:
   source=Path(__file__).resolve().parent/name
   with (out/name).open('xb') as f:f.write(source.read_bytes())
  put(out/'INDEX.json',{'schema':'lyd.actual-closed-boundary-source-index.v1','status':'ACTUAL_R17_CLOSED_RELEASED_BOUNDARY_VERIFIED','review':ref(out/'PREVIOUS-BOUNDARY.actual.json'),'verifier':ref(out/'verify_previous_boundary.py'),'verifier_dependencies':ref(out/'DEPENDENCIES.json'),'request':row,'author_source':ref(__file__),'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'source_head':review['source_head'],'business_GREEN':False,'autosave_verified':False,'SDK_calls':0,'game_calls':0,'process_lookups':0,'lease_mutated':False})
  print(json.dumps({'review':ref(out/'PREVIOUS-BOUNDARY.actual.json'),'verifier':ref(out/'verify_previous_boundary.py'),'index':ref(out/'INDEX.json'),'limits':verified['actual_exit_observation_limits']},ensure_ascii=False));return 0
 except BaseException as e:
  put(out/'FAILURE.actual.json',{'status':'FAILURE_PRESERVED_NO_RETRY','error':type(e).__name__+': '+str(e),'SDK_calls':0,'game_calls':0,'process_lookups':0,'main_writes':0});raise
if __name__=='__main__':raise SystemExit(main())

