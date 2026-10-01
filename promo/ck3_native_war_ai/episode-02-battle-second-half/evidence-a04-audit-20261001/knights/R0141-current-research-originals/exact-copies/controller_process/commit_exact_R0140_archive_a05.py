"""Preserve historical raw evidence as exact Git blobs and commit the reviewed private archive."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2gold1001')
BASE = SOURCE / 'promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a05-audit-20261001/knights'
ARCHIVE = BASE / 'R0140-current-research-originals'
GIT = ['git','-c','core.longpaths=true']

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
    return subprocess.check_output([*GIT,*args],cwd=SOURCE).decode('utf-8').strip()

def process(label,argv,standard_input=None):
    result = subprocess.run(argv,cwd=SOURCE,input=standard_input,capture_output=True)
    for suffix,content in [('stdout',result.stdout),('stderr',result.stderr)]:
        with (ROOT / (label+'-'+suffix+'.bin')).open('xb') as stream:
            stream.write(content)
    write(label+'-process.json',{'argv':argv,'returncode':result.returncode,
        'stdout':identity(ROOT / (label+'-stdout.bin')),'stderr':identity(ROOT / (label+'-stderr.bin'))})
    require(result.returncode == 0,label+' failed; native output bytes retained')
    return result.stdout

def main():
    require(git('rev-parse','HEAD') == 'e6fdde91b30d099c0e659578602b749bdbc62bd4','Private predecessor changed')
    require(git('branch','--show-current') == 'codex/war-series-brown-gold-20261001','Wrong private branch')
    manifest = ARCHIVE / 'new-files-manifest-final-a02.json'
    require(identity(manifest)['sha256'] == '38CFA6D6FA444519EE902B01B3E10068B4742C656DB751EA9013B1EE797E0A45','Manifest changed')
    pins = json.loads(manifest.read_text(encoding='utf-8'))['new_files'] + [identity(manifest)]
    require(len(pins) == 709,'Original 709-file reviewed inventory changed')
    for pin in pins:
        current = identity(pin['path'])
        require(current['bytes'] == pin['bytes'] and current['sha256'] == pin['sha256'],'Original asset changed')
    original_names = {Path(pin['path']).relative_to(SOURCE).as_posix() for pin in pins}
    require(set(git('diff','--cached','--name-only').splitlines()) == original_names | {(ARCHIVE / '.gitattributes').relative_to(SOURCE).as_posix()},'Unexpected existing stage')
    require(set(git('diff','--name-only').splitlines()).issubset(original_names),'Unreviewed tracked worktree file changed')
    attributes = ARCHIVE / '.gitattributes'
    require(attributes.read_bytes() == b'exact-copies/** -text -diff\nderived-exact-line-slices/** -text -diff\n','Wrong raw preservation attributes')
    pins.append(identity(attributes))
    names = [Path(pin['path']).relative_to(SOURCE).as_posix() for pin in pins]
    require(len(set(names)) == 710,'Final archive inventory differs')
    process('R0140-stage-exact-raw-a05',[*GIT,'add','--renormalize','-f','--',str(ARCHIVE),str(BASE / 'current-native-research-R0140.json'),str(BASE / 'current-native-research-R0140.md')])
    require(set(git('diff','--cached','--name-only').splitlines()) == set(names),'Staged file set differs')
    query = ''.join(':'+name+'\n' for name in names).encode('utf-8')
    with (ROOT / 'R0140-git-blob-queries-a05.bin').open('xb') as stream:
        stream.write(query)
    raw = process('R0140-exact-blob-batch-a05',[*GIT,'cat-file','--batch'],query)
    offset = 0
    checks = []
    for pin,name in zip(pins,names):
        end = raw.find(b'\n',offset)
        require(end >= offset,'Git batch header missing')
        header = raw[offset:end].decode('ascii').split()
        require(len(header) == 3 and header[1] == 'blob','Git batch object is not a blob')
        size = int(header[2])
        content = raw[end+1:end+1+size]
        require(len(content) == size and raw[end+1+size:end+2+size] == b'\n','Git batch blob truncated')
        digest = hashlib.sha256(content).hexdigest().upper()
        require(size == pin['bytes'] and digest == pin['sha256'],'Canonical Git blob differs from original bytes: '+name)
        checks.append({'path':name,'git_object':header[0],'bytes':size,'sha256':digest})
        offset = end+2+size
    require(offset == len(raw),'Unexpected extra Git batch bytes')
    write('R0140-exact-canonical-blobs-a05.json',{'file_count':710,'checks':checks,
        'all_git_blobs_match_reviewed_worktree_bytes':True,'prior_autoCRLF_stage_replaced_before_commit':True,
        'old_originals_never_edited':True,'directory_scoped_attributes':identity(attributes)})
    process('R0140-private-archive-diff-check-a05',[*GIT,'diff','--cached','--check'])
    process('R0140-private-archive-commit-a05',[*GIT,'commit','-m','Preserve exact R0140 rejected UI evidence and pending research status'])
    require(not git('status','--porcelain=v1'),'Private archive not clean')
    write('R0140-private-archive-commit-a05.json',{'source':str(SOURCE),'source_commit':git('rev-parse','HEAD'),
        'branch':git('branch','--show-current'),'new_file_count':710,'video_revision_started':False,
        'original_709_assets_plus_scoped_gitattributes':True,'master_intake_merge_push':False})
    print(git('rev-parse','HEAD'))

if __name__ == '__main__':
    main()
