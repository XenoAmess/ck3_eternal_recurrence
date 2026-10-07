from pathlib import Path
from hashlib import sha256
import json,subprocess,ast,sys
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=Path(__file__).parent
SRC=B/'i4-argument-author-r17-source-review-fix-20261007-002/author_i4_arguments.py'
RUN=B/'live-attempt-017';PY=Path(sys.executable)
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
prepared=load(RUN/'PREPARED.json');consumer=load(B/'r17-actual-consumer-source-20261007-001/INDEX.json')
snapshot=RUN/'mcp-client-001/0003-r17-005-snapshot.sdk-result.json';wrapper=load(snapshot)
texts=[json.loads(x['text']) for x in wrapper['content'] if x.get('type')=='text' and 'ck3.native-profile-receipt.v1' in x.get('text','')]
assert len(texts)==1;native=texts[0];assert wrapper.get('structuredContent',native)==native
session=native['session_id'];ready=load(RUN/'mcp-client-001/ready.json')
assert prepared['profile']['sha256']==native['profile_sha256']==ready['profile_sha256']
assert consumer['source_revision']==prepared['source_revision']=='c706a74f9d00dd842b7edce8901fb3417344fd9c'
core=O/'fixture-mirror/consumer';core.mkdir(parents=True,exist_ok=False)
mirror=O/'fixture-mirror/run';mirror.mkdir(parents=True,exist_ok=False)
fixture_consumer=dict(consumer);fixture_consumer['run_root']=mirror.as_posix()
index=put(core/'INDEX.json',fixture_consumer);pre=put(mirror/'PREPARED.json',prepared)
author=B/'r17-formal-original0240-source-20261007-002/author_formal_request.py'
common=['--consumer-source',core.as_posix(),'--consumer-index-sha256',index['sha256'],'--request-author',author.as_posix(),'--request-author-sha256',ref(author)['sha256'],'--prepared',pre['path'],'--prepared-sha256',pre['sha256'],'--session-id',session,'--snapshot-sdk',snapshot.as_posix(),'--snapshot-sdk-sha256',ref(snapshot)['sha256']]
refs=[B/'r17-actual-sdk-metadata-20261007-001/RESULT.json',B/'r17-actual-sdk-metadata-20261007-001/ACTUAL-grant28-profile-all-tools.json',B/'r17-actual-consumer-source-20261007-001/INDEX.json',RUN/'PREPARED.json',RUN/'native-profile-with-exit-inventory.json',RUN/'mcp-client-001/ready.json',RUN/'ROOT-ATTACHED-BINDING.actual.json',snapshot,RUN/'mcp-client-001/0003-r17-005-snapshot.native-01.json',author]
actual=put(O/'ACTUAL-SOURCE-INTERFACE-REFS.json',{'refs':[ref(p) for p in refs],'native_session_id_from_original_snapshot':session,'Client_session_id':ready['client_session_id'],'fixture_index_only_run_root_relocated':True,'profile_guard_meta_raw_original_refs_unchanged':True,'actual_baseline_source_only':{'actor':native['snapshot']['played_character']['character_id'],'public_revision':native['snapshot']['revision'],'native_revision':native['snapshot']['native_revision'],'date_raw':native['snapshot']['date_raw']},'actual_I4_query':None,'actual_newT':None,'game_SDK_calls':0,'save_body_reads':0})
put(O/'FIXTURE-MIRROR.json',{'common_argv':common,'original_snapshot_SDK':ref(snapshot),'synthetic_mirror_consumer':index,'synthetic_mirror_PREPARED':pre,'mirror_run':mirror.as_posix(),'actual_interface_refs':actual,'fixture_runtime_credit':None})
ast.parse(SRC.read_bytes(),filename=str(SRC))
help_argv=[str(PY),'-B','-X','utf8',str(SRC),'--help'];h=subprocess.run(help_argv,capture_output=True)
(O/'SOURCE002-help.stdout').write_bytes(h.stdout);(O/'SOURCE002-help.stderr').write_bytes(h.stderr)
put(O/'SOURCE002-HELP-AST.actual.json',{'source':ref(SRC),'AST_parse':True,'help_argv':help_argv,'help_exit':h.returncode,'stdout':ref(O/'SOURCE002-help.stdout'),'stderr':ref(O/'SOURCE002-help.stderr'),'game_SDK_calls':0})
argv=[str(PY),'-B','-X','utf8',str(SRC),*common,'--mode','open-decisions','--output',str(mirror/'first-SOURCE002-open')]
r=subprocess.run(argv,capture_output=True);(O/'SOURCE002-first.stdout').write_bytes(r.stdout);(O/'SOURCE002-first.stderr').write_bytes(r.stderr)
receipt=put(O/'SOURCE002-FIRST-CHECK.actual.json',{'source':ref(SRC),'argv':argv,'exit_code':r.returncode,'stdout':ref(O/'SOURCE002-first.stdout'),'stderr':ref(O/'SOURCE002-first.stderr'),'expected_pure_fixture':'Actual28/final10/session bytes, mirror run only, no requests executed.','output_created':(mirror/'first-SOURCE002-open').exists(),'SDK_calls':0,'native_calls':0,'game_calls':0,'main_writes':0,'formal_credit':None})
print(json.dumps({'first_check':receipt,'exit':r.returncode,'stderr':r.stderr.decode('utf-8','replace')[-1900:],'source_shape_AST_help_exit':h.returncode,'actual_interface_refs':actual}))
