from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parent
TREE=ROOT/'candidate'
TEST=TREE/'ck3_autonomous_player/tests/unit/test_native_bridge_dispatch_topology.py'
NATIVE=TREE/'ck3_autonomous_player/native_bridge'
ORIGINAL=Path('C:/lr17s1/ck3_autonomous_player/native_bridge')
PRIOR=Path('C:/workspace/ck3_lyd_runtime_20261004/r17-first430-native-timeout-diagnostic-20261007-001')
PYTHON='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
def ref(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':p.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def put(name,v):
 p=ROOT/name;b=v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with p.open('xb') as f:f.write(b)
 return ref(p)
spec=importlib.util.spec_from_file_location('native_dispatch_topology_candidate',TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
names,files=module.private_flag_registry(ORIGINAL)
for p in sorted(files):
 target=NATIVE/p.relative_to(ORIGINAL);target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(p.read_bytes())
for rel in ['include/xar_bridge/h2743_stock_private_query_v1.hpp']:
 target=NATIVE/rel;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write((ORIGINAL/rel).read_bytes())
target=NATIVE/'src/bridge.cpp';target.parent.mkdir(parents=True,exist_ok=True)
with target.open('xb') as f:f.write((PRIOR/'bridge.cpp.candidate').read_bytes())
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',XAR_NATIVE_DISPATCH_TEST_CMAKE_CACHE='C:/lr17b1/CMakeCache.txt')
results={}
for mode,native in [('original_known_red',ORIGINAL),('candidate',NATIVE)]:
 taskenv=dict(env,XAR_NATIVE_DISPATCH_TEST_NATIVE_ROOT=str(native))
 result=subprocess.run([PYTHON,'-B','-X','utf8',str(TEST),'-v'],env=taskenv,capture_output=True)
 stdout=put(mode+'.stdout',result.stdout);stderr=put(mode+'.stderr',result.stderr)
 if result.returncode!=(1 if mode=='original_known_red' else 0):raise ValueError('Unexpected focused result '+mode)
 results[mode]={'argv':[PYTHON,'-B','-X','utf8',str(TEST),'-v'],'native_root':native.as_posix(),'actual_cache':'C:/lr17b1/CMakeCache.txt','exit_code':result.returncode,'stdout':stdout,'stderr':stderr}
patch=(PRIOR/'CANDIDATE.incremental.patch').read_text(encoding='utf-8')
rel='ck3_autonomous_player/tests/unit/test_native_bridge_dispatch_topology.py'
source=TEST.read_text(encoding='utf-8')
new='--- /dev/null\n+++ b/'+rel+'\n@@ -0,0 +1,'+str(len(source.splitlines()))+' @@\n'+''.join('+'+line+'\n' for line in source.splitlines())
combined=put('NATIVE-AND-REGRESSION.incremental.patch',(patch+new).encode('utf-8'))
base=ROOT/'apply-check-base';target=base/'ck3_autonomous_player/native_bridge/src/bridge.cpp';target.parent.mkdir(parents=True)
target.write_bytes((ORIGINAL/'src/bridge.cpp').read_bytes())
checked=subprocess.run(['git','apply','--check',combined['path']],cwd=base,capture_output=True)
put('APPLY-CHECK.stdout',checked.stdout);put('APPLY-CHECK.stderr',checked.stderr)
if checked.returncode!=0:raise ValueError('Exact isolated combined apply check failed')
index=put('INDEX.json',{'status':'TWO_FILE_SOURCE_ONLY_DISPATCH_FIX_AND_CHECKED_IN_REGRESSION_READY','source_revision':'c706a74f9d00dd842b7edce8901fb3417344fd9c',
 'prior_native_patch':ref(PRIOR/'CANDIDATE.incremental.patch'),'native_after':ref(target if False else NATIVE/'src/bridge.cpp'),'test':ref(TEST),'combined_patch':combined,
 'focused_results':results,'test_cases':2,'configuration_subcases':7,'source_flag_census_count':len(names),'source_flag_census':sorted(names),'apply_check_exit_code':checked.returncode,
 'scope':'Pure source brace/conditional model; no C++ compiler or runtime callback. Original known RED is retained; candidate source-only PASS is separate.',
 'future_native_compile':None,'future_game_runtime':None,'main_writes':0,'SDK_calls':0,'game_calls':0,'bus_calls':0,'native_builds':0})
print(json.dumps({'INDEX':index,'combined_patch':combined,'test':ref(TEST),'original_expected_negative_exit':results['original_known_red']['exit_code'],'candidate_focused_exit':results['candidate']['exit_code'],'apply_check_exit':checked.returncode}))
