"""Bounded offline source check runner. Never invokes Steam, SDK, game or native EXE."""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import subprocess


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    root=here.parent
    index=here/'BUNDLE-SOURCE-INDEX.prepared.json'
    value=json.loads(index.read_bytes())
    for row in value['files']:
        data=Path(row['path']).read_bytes()
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    index.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    output=here/args.label
    output.mkdir()
    python=args.repo/'tools/.venv/Scripts/python.exe'
    argv=[str(python),'-B',str(here/'test_parent_public_source.py'),'--repo',str(args.repo)]
    child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.GetProcessTimes.restype=wintypes.BOOL
    fields=[wintypes.FILETIME() for _ in range(4)]
    got=kernel.GetProcessTimes(child._handle,*[ctypes.byref(v) for v in fields])
    birth=str((fields[0].dwHighDateTime<<32)|fields[0].dwLowDateTime) if got else None
    stdout,stderr=child.communicate()
    code=child.wait()
    current=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if len(stdout)+len(stderr)>65536 or current+len(stdout)+len(stderr)+10000>4194304:
        raise ValueError('Aggregate/log cap before write')
    (output/'stdout.log').write_bytes(stdout)
    (output/'stderr.log').write_bytes(stderr)
    def pin(path: Path) -> dict:
        data=path.read_bytes()
        return dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    receipt=dict(schema='xar.e04.parent.public.focused-original-wait.v1',
        machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
        argv=argv,pid=child.pid,process_creation_filetime_100ns=birth,returncode=code,
        actual_original_popen_wait=True,stdout=pin(output/'stdout.log'),stderr=pin(output/'stderr.log'),
        test_source=pin(here/'test_parent_public_source.py'),SDK_Steamprobe_game_native_execution=False)
    (output/'ORIGINAL-WAIT.actual.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(stderr.decode(errors='replace'))
    print('ORIGINAL_WAIT',code,output/'ORIGINAL-WAIT.actual.json')
    return code


if __name__=='__main__':
    raise SystemExit(main())
