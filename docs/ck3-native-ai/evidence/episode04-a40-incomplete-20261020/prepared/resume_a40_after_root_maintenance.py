"""Bounded no-configure/no-work continuation after actual exact-root enrollment."""
from pathlib import Path
import importlib.util,json,subprocess,hashlib,os
O=Path(__file__).parent
spec=importlib.util.spec_from_file_location('a40_original_execution',O/'execute_a40.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
m=e.m;p=e.p;g=e.g;B=g.root
FAIL={'path':str(B/'A40-FIRST-FAILURE.actual-a01.json'),'bytes':8029,'sha256':'dd9b428687c87137fc02a827f24e22eea95c5ebd139b8e8026de51db52b0cfc1'}
failure=m.load(FAIL);m.source(p);g.check();m.need(failure['production_build_succeeded'] and not failure['any_project_EXE_executed'],'failure identity differs')
for key in ['phase','phase_intent','phase_stdout','phase_stderr','producer_result','configure_log','build_log','compile_commands','manifest','client_receipt','actual_protected_SYSTEM_rejection']:m.need(m.same(m.pin(failure[key]['path']),failure[key]),'preserved evidence changed: '+key)
for output in failure['production_linked_artifacts']:m.need(m.same(m.pin(output['path']),output),'linked artifact changed before resume')
maintenance=m.pin(B/'BROKER-EXACT-ROOT-MAINTENANCE.actual-a01.json');mrec=m.load(maintenance)
m.need(mrec['status']=='EXACT_A40_BUILD_ROOT_INSTALLED_AND_READ_BACK' and mrec['runtime_code_task_seal_external_source_roots_unchanged'] is True,'actual root maintenance not accepted')
m.need(mrec['token_identity']=={'sid':'S-1-5-21-4063940640-1897558599-686929869-1001','admin':True},'actual admin owner token absent')
root=Path('C:/Program Files/XAR CK3 Project EXE Broker')
for name,key in [('policy.json','BROKER-POLICY-EXACT-A40-ROOT.candidate-a01.json'),('installation-manifest.json','BROKER-INSTALLATION-MANIFEST-EXACT-A40-ROOT.candidate-a01.json')]:m.need(m.pin(root/name)['sha256']==m.pin(O/key)['sha256'],'actual installed candidate bytes differ')
temp=B/'temp';os.environ.update({'TEMP':str(temp),'TMP':str(temp),'PYTHONDONTWRITEBYTECODE':'1','PYTHONPYCACHEPREFIX':str(B/'python-cache')})
fresh=O.parent/'capacity/fresh_a40_stage.py';m.need(m.pin(fresh)['sha256']=='d68bd70fb300aa781802f8cba27ec9742d838f55980a3bfdcf41192b19d9d1b0','fresh helper changed')
def preflight(phase,name):
 e.bus('taskbus-before-'+name+'.actual-a01.json');output=B/('CAPACITY-FRESH-'+name+'.actual-a01.json')
 subprocess.run([p['python'],'-B','-X','utf8',str(fresh),'--phase',phase,'--output',str(output)],check=True)
 return m.pin(output)
admission=preflight('main-build','SYSTEM-resume')
argv=list(p['configure_build_argv']);argv.remove('--configure');argv[argv.index('--evidence-dir')+1]=str(B/'producer-evidence-a02')
e.evidence('BOUNDED-SYSTEM-RESUME-INTENT.actual-a01.json',{'previous_failure':FAIL,'actual_root_maintenance':maintenance,'capacity':e.CAP,'producer_plan':e.PLAN,'execution_helper':m.pin(__file__),'fresh_capacity':admission,'argv':argv,'configuration_requested':False,'production_bytes_must_remain_identical':True})
build=g.run('02-public-production-build-only-SYSTEM-resume',argv)
e.cachecheck(B,p['all_feature_flags']);m.source(p)
report_path=B/'producer-evidence-a02/native-msvc-result.json';report=json.loads(report_path.read_bytes())
m.need(report['configured'] is False,'resume unexpectedly requested configure')
log=B/'producer-evidence-a02/msvc-build.log';m.need(b'no work to do' in log.read_bytes().lower(),'resume did not explicitly report no work')
system,outputs=e.qualified(B,p['targets'],B/'producer-evidence-a02')
for old in failure['production_linked_artifacts']:m.need(m.same(m.pin(old['path']),old),'production bytes changed during registration resume')
ui_admission=preflight('main-UI-cold','UI-cold-after-SYSTEM')
ctest=str(Path(report['tools']['cmake']).with_name('ctest.exe'))
cold=g.run('02-focused-ui-cold',[ctest,'--test-dir',str(B),'-C','Release','--output-on-failure','--no-tests=error','-R',p['ctest_regex']])
e.evidence('MAIN-UI-COLD-FRESH-CAPACITY-BINDING.actual-a01.json',{'fresh_phase_capacity':ui_admission,'phase_intent':m.pin(B/'qualification-phases/02-focused-ui-cold/intent.actual.json'),'phase_result':cold})
m.source(p);m.need(all(m.same(m.pin(x['path']),x) for x in outputs),'main artifact changed after cold')
result=e.evidence('ROOT-A40-MAIN-PRODUCTION-QUALIFICATION.actual-a01.json',{'schema':'xar.e04.a40-production-focused-qualification.v1','status':'QUALIFIED_PRODUCTION_AND_CHANGED_SOURCE_SYNTHETIC_COLD',**e.common(),'previous_SYSTEM_root_scope_failure':FAIL,'actual_exact_root_maintenance':maintenance,'production_recompiled_in_resume':False,'resume_log_explicit_no_work':True,'same_four_artifact_bytes_as_first_build':True,'outputs':outputs,'all_feature_flags':p['all_feature_flags'],'production_steps':[{'build_step':build,'verification':system}],'focused_cold':{'targets':p['cold_targets'],'ctest':cold,'fresh_capacity':ui_admission},'production_bytes_qualified':True,'focused_cold_qualified':True,'worker_qualification_pending':True,'remaining_heavy_stages':['worker-live-build','worker-v5-build','worker-two-cold-cases']})
print(json.dumps(result),flush=True)
