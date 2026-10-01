"""Commit only the reviewed create-only R0140 research archive on the private video branch."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2gold1001')
BASE = SOURCE / 'promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights'
MANIFEST = BASE / 'R0140-current-research-originals/new-files-manifest-final-a02.json'

def require(ok,message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper()}

def write(name,value):
    with (ROOT / name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')

def git(*args):
    return subprocess.check_output(['git',*args],cwd=SOURCE).decode('utf-8').strip()

def main():
    require(git('rev-parse','HEAD') == 'e6fdde91b30d099c0e659578602b749bdbc62bd4','Private archive predecessor differs')
    require(git('branch','--show-current') == 'codex/war-series-brown-gold-20261001','Wrong private branch')
    require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked files changed')
    require(identity(MANIFEST)['sha256'] == '38CFA6D6FA444519EE902B01B3E10068B4742C656DB751EA9013B1EE797E0A45','Reviewed archive manifest changed')
    body = json.loads(MANIFEST.read_text(encoding='utf-8'))
    pins = body['new_files']
    require(len(pins) == 708,'Reviewed archive file count differs')
    files = []
    for pin in pins:
        path = Path(pin['path']).resolve()
        relative = path.relative_to(SOURCE).as_posix()
        allowed = path.is_relative_to(BASE / 'R0140-current-research-originals') or path in {
            BASE / 'current-native-research-R0140.json',BASE / 'current-native-research-R0140.md'}
        require(allowed and identity(path) == pin,'Archive path or bytes changed: ' + relative)
        files.append(relative)
    files.append(MANIFEST.relative_to(SOURCE).as_posix())
    require(len(set(files)) == 709 and set(git('ls-files','--others','--exclude-standard').splitlines()) == set(files),
            'Unreviewed untracked file or missing archive file')
    verification = json.loads((BASE / 'R0140-current-research-originals/verification-final-a01.json').read_text(encoding='utf-8'))
    require(verification['status'] == 'PASS_CURRENT_ORIGINALS_AND_CREATED_COPIES_MATCH_HASH_BOUND_INDEX','Archive check not passed')
    write('R0140-private-archive-commit-intent.json', {'source':str(SOURCE),'files':files,
        'manifest':identity(MANIFEST),'verification':verification,'video_bytes_or_config_changed':False,
        'R0140_six_gap_status':'PENDING','master_intake_merge_push':False})
    for index,argv in enumerate((['git','add','--',*files],['git','diff','--cached','--check'],
         ['git','commit','-m','Preserve R0140 rejected UI evidence and pending six-gap research status'])):
        result = subprocess.run(argv,cwd=SOURCE,capture_output=True,text=True,encoding='utf-8')
        write(f'R0140-private-archive-git-step-{index+1}.json',{'argv':argv,'returncode':result.returncode,
              'stdout':result.stdout,'stderr':result.stderr})
        require(result.returncode == 0,'Private archive commit failed')
    require(not git('status','--porcelain=v1'),'Committed private archive not clean')
    write('R0140-private-archive-commit.json',{'source':str(SOURCE),'source_commit':git('rev-parse','HEAD'),
        'branch':git('branch','--show-current'),'new_file_count':709,'video_revision_started':False,
        'remote_operations':False,'master_intake':False})
    print(git('rev-parse','HEAD'))

if __name__ == '__main__':
    main()
