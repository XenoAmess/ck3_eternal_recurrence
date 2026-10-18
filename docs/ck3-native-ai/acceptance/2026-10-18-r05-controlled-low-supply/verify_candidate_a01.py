"""Stdlib candidate verification; optional one canonical glue case, no CK3."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,sys,unittest,zipfile
BASE=Path(__file__).resolve().parent
def digest(raw):return hashlib.sha256(raw).hexdigest()
def check(condition,message):
    if not condition:raise ValueError(message)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree',type=Path,default=BASE/'patch-root')
    p.add_argument('--copy-plan',type=Path,default=BASE/'COPYPLAN.actual-a01.json')
    p.add_argument('--archive',type=Path)
    p.add_argument('--smoke-repo',type=Path)
    p.add_argument('--temp-root',type=Path)
    a=p.parse_args();tree=a.tree.resolve();plan=json.loads(a.copy_plan.read_bytes())
    check(plan['mode']=='add_only','unexpected plan mode')
    for row in plan['files']:
        name=Path(row['relative_path']);check(not name.is_absolute() and '..' not in name.parts,'unsafe path')
        raw=(tree/name).read_bytes();check(len(raw)==row['bytes'] and digest(raw)==row['sha256'],'file changed: '+str(name))
    if a.archive:
        with zipfile.ZipFile(a.archive) as archive:
            check(archive.testzip() is None,'archive CRC failed')
            for row in plan['files']:
                raw=archive.read('patch-root/'+row['relative_path'])
                check(len(raw)==row['bytes'] and digest(raw)==row['sha256'],'archive member changed')
            check(archive.read('COPYPLAN.actual-a01.json')==a.copy_plan.read_bytes(),'archived plan differs')
    result={'schema':'xar.r05-candidate-verification.v1','source_machine_id':plan['machine_id'],
        'current_machine_id':'unknown','files_verified':len(plan['files']),
        'copy_plan_sha256':digest(a.copy_plan.read_bytes()),'SDK_calls':0,'CK3_started':False,'R05_pass':False}
    identity_repo=(a.smoke_repo or Path.cwd()).resolve()
    identity_helper=identity_repo/'tools/ck3_live_run_id.py'
    if identity_helper.is_file():
        identity=load('r05_verifier_machine_identity',identity_helper)
        result['current_machine_id']=identity.current_machine_id()
    result['machine_id']=result['current_machine_id']
    if a.smoke_repo:
        repo=a.smoke_repo.resolve();check(a.temp_root is not None,'one smoke case needs new external temp root')
        temp=a.temp_root.resolve();check(not temp.exists() and not temp.is_relative_to(repo),'new external temp root required')
        temp.mkdir(parents=True)
        sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
        from ck3_live_run_id import current_machine_id
        result['current_machine_id']=current_machine_id()
        tests=load('r05_canonical_one_glue_case',repo/'tools/test_r05_low_supply_fixture.py')
        tests.DEPENDENCIES=repo;tests.TEMP=temp;tests.ACTUAL_PREFLIGHT=None
        tests.M=load('xar_autoplayer.bridge.r05_low_supply_fixture',repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
        tests.R=load('r05_canonical_once_runner',repo/'tools/run_r05_low_supply_initializer_once.py')
        tests.A=load('r05_canonical_adapter',repo/'tools/ck3_mod_acceptance_cases/r05_low_supply_adapter.py')
        name='test_public_common_adapter_profile_and_actual_load_declaration'
        stream=io.StringIO();run=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([tests.Contracts(name)]))
        result['one_canonical_smoke']={'name':name,'tests_run':run.testsRun,'passed':run.wasSuccessful(),
            'output':stream.getvalue(),'scope':'actual source glue; SDK/OS process synthetic boundaries'}
        check(run.wasSuccessful(),'one canonical source glue case failed')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
