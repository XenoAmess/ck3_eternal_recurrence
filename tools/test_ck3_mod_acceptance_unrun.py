"""One focused compound over actual allocated-only metadata, without game/SDK."""
from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest.mock import patch
import argparse,json
import ck3_mod_acceptance_unrun as subject
from ck3_mod_acceptance_allocate import read_failed_runtime_release

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);a=p.parse_args()
    bundle=subject._read(a.bundle);live=Path(bundle['ready']['path']).parent
    freeze=subject._read(bundle['frozen']['path']);keeper=Path(bundle['keeper']['path']).parent
    release=read_failed_runtime_release(Path(bundle['admin_done']['path']));bus={'tasks':[release['task']]}
    def invoke(path=a.bundle):return subject.validate_allocated_unrun(live,freeze,path,keeper,release,bus)
    verdict=invoke()
    assert verdict['mode']=='previous-shared-allocated-unrun-idle'
    assert verdict['failure_cleanup']['typed_normal_exit_proven'] is False
    assert verdict['failure_cleanup']['original_host_exit_code'] is None
    def refuses(expected,call):
        try:call()
        except ValueError as error:assert expected in str(error),(expected,str(error))
        else:raise AssertionError('Unsafe actual branch was admitted: '+expected)
    exists=Path.exists
    with patch.object(Path,'exists',lambda path: True if path==live/'host-started.json' else exists(path)):
        refuses('host/native/control/Save',invoke)
    original=subject._read
    def alive(path):
        value=original(path)
        if Path(path).resolve()==Path(bundle['keeper']['path']).resolve():value={**value,'thread_exited':False}
        return value
    with patch.object(subject,'_read',side_effect=alive):refuses('keeper STOP/wait0',invoke)
    # Both pins are genuine. Substituting the administrative DONE for the CAS
    # must still be rejected; a later closed task alone is not the CAS sequence.
    with TemporaryDirectory(prefix='unrun-compound-') as td:
        wrong=deepcopy(bundle);wrong['CAS_release']=wrong['admin_done'];path=Path(td)/'wrong-cas.json'
        path.write_text(json.dumps(wrong),encoding='utf-8')
        refuses('CAS then admin DONE',lambda:invoke(path))
    print(json.dumps({'test':'actual_allocated_unrun_positive_and_host_keeper_wrongCAS_rejected',
        'passed':1,'machine_id':bundle['machine_id'],'run_id':bundle['run_id'],
        'SDK_or_game':False,'normal_exit_credit':False,'actual_process_inventory_scanned_once':True}))
if __name__=='__main__':main()
