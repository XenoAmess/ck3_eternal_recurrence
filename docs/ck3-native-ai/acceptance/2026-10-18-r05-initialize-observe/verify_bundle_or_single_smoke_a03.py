"""Stdlib archive/preimage verifier; optional one canonical glue smoke, no SDK."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,importlib,importlib.util,json,sys,unittest,zipfile

EXPECTED='949617ab74b5b4a6fdfc454487f6d140d528fa9f600e0a4152e54f1c49b5cbb2'
def require(value,message):
    if not value:raise ValueError(message)
def pin(path):
    raw=Path(path).read_bytes();return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def check(path,ref):require(pin(path)=={k:ref[k] for k in ('bytes','sha256')},'exact pin differs: '+str(path))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle-root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--target-root',type=Path);p.add_argument('--target-state',choices=('before','after'))
    p.add_argument('--single-canonical-smoke',action='store_true');p.add_argument('--temp-root',type=Path)
    a=p.parse_args();root=a.bundle_root.resolve();receipt=root/'ROOT-DELIVERY.actual-a03.json'
    require(pin(receipt)['sha256']==EXPECTED,'Root delivery bytes differ')
    delivery=json.loads(receipt.read_bytes());plan_path=root/'COPYPLAN.actual-a03.json'
    check(plan_path,delivery['copyplan']);check(root/'relative.patch',delivery['patch'])
    archive=root/'R05-INITIALIZE-OBSERVE-CANDIDATE.actual-a03.zip';check(archive,delivery['zip'])
    plan=json.loads(plan_path.read_bytes());files=plan['files'];require(len(files)==delivery['file_count']==11,'target count differs')
    names=[r['relative_path'] for r in files]
    require(len(set(names))==len(names),'duplicate target')
    with zipfile.ZipFile(archive) as z:
        require(set(z.namelist())==set(names)|{'COPYPLAN.actual-a03.json'},'ZIP entry set differs')
        require(z.read('COPYPLAN.actual-a03.json')==plan_path.read_bytes(),'ZIP copyplan differs')
        for row in files:
            name=row['relative_path'];parts=PurePosixPath(name)
            require(not parts.is_absolute() and '..' not in parts.parts and ':' not in name and '\\' not in name,'unsafe relative target')
            raw=z.read(name);require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'ZIP target differs')
            check(root/'patch-root'/name,row)
            if a.target_root:
                require(a.target_state is not None,'explicit target state required')
                dest=a.target_root/name;ref=row if a.target_state=='after' else row['expected_original']
                if ref.get('status')=='absent':require(not dest.exists(),'new target already exists: '+name)
                else:check(dest,ref)
    result={'schema':'xar.r05-observe-portable-verifier.v1','status':'PASSED','file_count':len(files),
        'bundle_machine_id':delivery['machine_id'],'target_machine_runtime_qualified':False,'SDK_calls':0,
        'target_state_verified':a.target_state if a.target_root else None,'single_smoke_run':False}
    if a.single_canonical_smoke:
        require(a.target_root is not None and a.target_state=='after' and a.temp_root is not None,'smoke requires exact applied target and external temp root')
        target=a.target_root.resolve();temp=a.temp_root.resolve();temp.mkdir(parents=True,exist_ok=True)
        sys.path[:0]=[str(target/'ck3_autonomous_player/src'),str(target/'tools')]
        test=load('r05_canonical_single_smoke',target/'tools/test_r05_supply_observation_case.py')
        test.DEPENDENCIES=target;test.TEMP=temp
        test.M=importlib.import_module('xar_autoplayer.bridge.r05_low_supply_fixture')
        test.I=load('r05_canonical_initializer_factory',target/'tools/test_r05_low_supply_fixture.py');test.I.M=test.M
        test.O=importlib.import_module('xar_autoplayer.bridge.r05_supply_observation_case')
        test.A=load('r05_canonical_observe_adapter',target/'tools/ck3_mod_acceptance_cases/r05_initialize_observe_adapter.py')
        suite=unittest.TestSuite([test.Contracts('test_public_adapter_continuation_and_verify_need_cleanup_and_close')])
        ran=unittest.TextTestRunner(verbosity=2).run(suite)
        require(ran.wasSuccessful() and ran.testsRun==1,'single canonical glue smoke failed')
        result.update(single_smoke_run=True,canonical_smoke_tests=ran.testsRun)
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error:
        print(json.dumps({'status':'FAILED','error':type(error).__name__+': '+str(error)}));raise SystemExit(1)
