"""Run the existing stream archive collector once, only over selected original text/JSON."""
from pathlib import Path
import hashlib,json,subprocess
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=B/'r29-business-permanent-archive-sourceonly-20261008-001'
CP=B/'r29-checkpoint-author-sourceonly-20261008-002'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve();v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
q=read(O/'REQUEST.final.actual.json');seen={Path(r['path']).resolve().as_posix().casefold()for r in q['files']}
for p in [CP/'source-005/title_reference/formal_native_qualification.py',CP/'source-008/title_reference/formal_native_qualification.py',CP/'qualify_retained_formal.py',CP/'qualify_retained_formal_json_root_only.py',O/'prepare_selected_archive.py',O/'finalize_selected_request.py',O/'create_one_archive.py',O/'INDEX.json']:
 k=p.resolve().as_posix().casefold()
 if k not in seen:seen.add(k);q['files'].append(pin(p)|{'role':'exact formal leaf source and bounded R29 curation/stream author source; no rerun'})
put(O/'REQUEST.sealed.actual.json',q)
a=read(O/'CREATE-ARGV.final.actual.json');argv=a['argv'];argv[argv.index('--request')+1]=(O/'REQUEST.sealed.actual.json').as_posix();argv[argv.index('--sha256')+1]=pin(O/'REQUEST.sealed.actual.json')['sha256'];a['request']=pin(O/'REQUEST.sealed.actual.json');put(O/'CREATE-ARGV.sealed.actual.json',a)
result=subprocess.run(argv,capture_output=True,check=False)
with (O/'archive.stdout').open('xb')as f:f.write(result.stdout)
with (O/'archive.stderr').open('xb')as f:f.write(result.stderr)
put(O/'ARCHIVE-ORIGINAL-EXEC.actual.json',{'argv':argv,'argv_ref':pin(O/'CREATE-ARGV.sealed.actual.json'),'exit_code':result.returncode,'stdout':pin(O/'archive.stdout'),'stderr':pin(O/'archive.stderr'),'SDK_process_game_body_binary_MAIN_calls':0})
print(result.stdout.decode('utf-8'));print('archive_exit',result.returncode)
if result.returncode:print(result.stderr.decode('utf-8',errors='replace'))
raise SystemExit(result.returncode)
