from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def run(label: str, argv: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env.update(PYTHONPATH='C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib',
               PYTHONDONTWRITEBYTECODE='1',TMP=str(ROOT),TEMP=str(ROOT))
    proc: subprocess.Popen[bytes] = subprocess.Popen(argv,cwd=ROOT,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW)
    stdout,stderr = proc.communicate(timeout=60)
    code = proc.wait(timeout=5)
    for suffix,body in (('stdout',stdout),('stderr',stderr)):
        with (ROOT/(label+'.'+suffix+'.actual.txt')).open('xb') as stream:
            stream.write(body)
    return dict(argv=argv,original_Popen_pid=proc.pid,original_wait_returncode=code,
        stdout_bytes=len(stdout),stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_bytes=len(stderr),stderr_sha256=hashlib.sha256(stderr).hexdigest())

def main() -> None:
    py=sys.executable
    files=['r13_contract.py','r13_once_contacts.py','test_r13_guards.py','run_modified_checks.py']
    mypy=run('mypy',[py,'-B','-m','mypy','--config-file',str(ROOT/'mypy-empty.ini'),
        '--no-incremental','--cache-dir','nul','--python-version','3.14','--platform','win32',
        '--check-untyped-defs','--disallow-untyped-defs']+files)
    tests=run('guard-tests',[py,'-B',str(ROOT/'test_r13_guards.py'),'-v'])
    row=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_only=True,real_decoder_calls=0,mypy=mypy,focused_guards=tests,
        passed=mypy['original_wait_returncode']==0 and tests['original_wait_returncode']==0)
    with (ROOT/'SOURCE-CHECKS.actual-a02.json').open('x',encoding='utf-8') as stream:
        json.dump(row,stream,separators=(',',':'))
    print(json.dumps(row))

if __name__=='__main__':
    main()
