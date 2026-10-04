"""Archive a completed attempt's process files without altering its old inputs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt-directory',type=Path,required=True)
    p.add_argument('--archive-directory',type=Path,required=True)
    p.add_argument('--extra-directory',type=Path,action='append',default=[])
    a=p.parse_args()
    attempt=a.attempt_directory.resolve(strict=True)
    archive=a.archive_directory.resolve()
    archive.mkdir(parents=True,exist_ok=False)
    manifest=attempt/'native-run/run-manifest.json'
    sources=[]
    for directory in [attempt/'build',attempt/'orchestration-commands',attempt/'native-build-command',attempt/'native-run/postflight',*a.extra_directory]:
        directory=directory.resolve(strict=True)
        for path in sorted(directory.rglob('*')):
            if path.is_file():sources.append((path,f'{directory.name}/{path.relative_to(directory).as_posix()}'))
    for path in sorted(attempt.glob('*.json')):sources.append((path,'attempt/'+path.name))
    names=[name for _,name in sources]
    assert len(names)==len(set(names)), 'Archive roots must have distinct names.'
    index=[]
    payload=archive/'process-materials.zip'
    with zipfile.ZipFile(payload,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for path,name in sources:
            blob=path.read_bytes()
            index.append({'path':str(path),'archive_path':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
            z.writestr(name,blob)
        z.writestr('index.json',json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    cli=[sys.executable,'-X','utf8','-m','xar_promo']
    commands=[cli+['preserve',str(payload),'--run-manifest',str(manifest),'--artifact-id','process.completed-attempt','--collection','derived','--role','process-archive'],cli+['validate',str(manifest),'--json']]
    for i,argv in enumerate(commands,1):
        r=subprocess.run(argv,capture_output=True)
        (archive/f'{i:02d}.stdout.txt').write_bytes(r.stdout)
        (archive/f'{i:02d}.stderr.txt').write_bytes(r.stderr)
        (archive/f'{i:02d}.command.json').write_text(json.dumps({'argv':argv,'exit_code':r.returncode},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        r.check_returncode()
    run=json.loads(manifest.read_bytes())
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'attempt':str(attempt),'archive':str(payload),'archive_sha256':hashlib.sha256(payload.read_bytes()).hexdigest(),'archive_bytes':payload.stat().st_size,'process_file_count':len(index),'native_manifest':str(manifest),'native_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'native_artifact_count':len(run['artifacts']),'signoff_count':len(run.get('signoffs',[])),'validation_passed':True,'original_materials_retained':True}
    (archive/'retention-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
