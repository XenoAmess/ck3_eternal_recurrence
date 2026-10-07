from pathlib import Path
import ast,hashlib,json,subprocess,sys,datetime
root=Path('C:/lr21rw1');package=Path(__file__).parent;out=package/'normal-exit-render-001';out.mkdir()
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.normal_exit_contract_v1 import ExitWireBinding,NATIVE_PROOF_KEYS,normalize_native_exit_observation
test=root/'ck3_autonomous_player/tests/unit/test_normal_exit_integrated_v1.py'
module=ast.parse(test.read_text('utf-8-sig'))
function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='native_observation')
namespace={'NATIVE_PROOF_KEYS':NATIVE_PROOF_KEYS}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(test),'exec'),namespace)
wire=ExitWireBinding(72,9301,43,8,133000000000000043,'b'*64)
request={'action':'query_context','expected_revision':72,'expected_connection_generation':8,'expected_game_pid':43,'expected_player_character_id':9301,'expected_process_creation_filetime_100ns':133000000000000043}
cases=[];paths=[]
for action in ('query_context','prepare_confirmation','confirm_desktop'):
 request['action']=action
 raw=namespace['native_observation'](request)
 normalize_native_exit_observation(raw,wire,action)
 path=out/(action+'.inert.json');path.write_text(json.dumps(raw,separators=(',',':'))+'\n',encoding='utf-8');paths.append(path)
argv=[str(package/'isolated-004/confucian_semantic_identity_fixture.exe')]+[str(p) for p in paths]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
run=subprocess.run(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(out/'stdout.raw').write_bytes(run.stdout);(out/'stderr.raw').write_bytes(run.stderr)
assert run.returncode==0,run.stderr
actual=json.loads(run.stdout)
for row,path,action in zip(actual['cases'],paths,('query_context','prepare_confirmation','confirm_desktop'),strict=True):
 before=json.loads(path.read_bytes())
 for label in ('original','fixed'):
  normalized=normalize_native_exit_observation(row[label],wire,action)
  assert normalized==before
  assert normalized['exit_context_signature']=='c'*64
  assert normalized['orderly_exit_verified'] is False and normalized['autosave_verified'] is False
 cases.append({'action':action,'original_renderer_equal':True,'fixed_renderer_equal':True,'canonical_schema':'ck3-normal-exit-map-v1','signature_bytes_unchanged':True,'strict_DTO_accepted':True,'live_credit':None})
def ref(path):
 data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
refs=[ref(test),ref(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_contract_v1.py'),ref(root/'ck3_autonomous_player/native_bridge/src/normal_exit_map_request_v1.cpp'),ref(root/'ck3_autonomous_player/native_bridge/src/normal_exit_map_v1.cpp'),ref(root/'ck3_autonomous_player/native_bridge/src/bridge.cpp')]
bridge=(root/'ck3_autonomous_player/native_bridge/src/bridge.cpp').read_text('utf-8-sig')
begin=bridge.index('} else if (step == xar::ck3_12003::kNormalExitMapV1Step)')
end=bridge.index('#if defined(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)',begin)
handler=bridge[begin:end]
assert 'SerializeNormalExitMapObservationV1(exit.observation)' in handler and 'Render12004BuildIdentity' not in handler
serializer=(root/'ck3_autonomous_player/native_bridge/src/normal_exit_map_request_v1.cpp').read_text('utf-8-sig')
assert r'\"schema\":\"ck3-normal-exit-map-v1\"' in serializer
report={'schema':'lyd.r21.normal-exit-canonical-render-acceptance.v1','status':'INERT_RENDER_AND_STRICT_DTO_ACCEPTED','started_at_utc':start,'ended_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'exit_code':run.returncode,'input_refs':[ref(p) for p in paths],'source_refs':refs,'existing_compiled_fixture':ref(Path(argv[0])),'output_ref':ref(out/'stdout.raw'),'cases':cases,'actual_handler_serializes_directly_without_build_rewrite':True,'shared_native_wire_schema_version_independent':True,'no_context_callback_or_signature_generation_executed':True,'runtime_DLL_build_or_live_operations':False,'live_native_context_credit':None}
(out/'RESULT.actual.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(ref(out/'RESULT.actual.json')))
