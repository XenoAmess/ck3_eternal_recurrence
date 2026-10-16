"""Preserve failed whitespace-parser seal exactly; correct portable parser only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,shutil,subprocess,sys,zipfile
H=Path(__file__).parent.resolve()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def pin(p):
    b=p.read_bytes();return dict(path=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(n,o):
    with (H/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,indent=2);f.write('\n')
source=json.loads((H/'SOURCE.actual.json').read_bytes());oldverify=(H/'verify_portable.py').read_text(encoding='utf-8')
names=['seal.py','SOURCE.actual.json','VERIFY.actual.json','verify_portable.py','PLAN.before-read.corrected-a03.json','GRAPH.before-read.corrected-a03.md']
z=H/'FIRST-SEAL-AND-INITIAL-PLAN.exact.zip';need(not z.exists(),'Archive existing');members=[]
for n in names:
    p=(H/n).resolve();need(p.parent==H and p.is_file(),'Exact path');b=p.read_bytes();members.append(pin(p))
    with zipfile.ZipFile(z,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as f:f.writestr(n,b)
    with zipfile.ZipFile(z) as f:need(f.read(n)==b,'Exact archive member')
    p.unlink()
newverify=oldverify.replace("read('SOURCE.actual.json')","read('SOURCE.final-a02.json')").replace("m[3]))","m[3].strip()))")
need(newverify!=oldverify and 'm[3].strip()' in newverify,'Whitespace parser correction')
with (H/'verify_portable_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(newverify)
write('FINALIZATION-CORRECTION.actual.json',dict(machine_id=source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),reason='First verifier incorrectly compared savedasm ret-with-trailing-space to exactret and rejected. Byte/source semantics unchanged. Corrected parser strips mnemonic whitespace; no new EXE read.',archive=pin(z),members=members,unfolded_archived_files_no_longer_present=True,whole_EXE_hashes=0,new_EXE_reads=0))
source['schema']='xar.e04.r08.context-owner29591E0.source.final-a02';source['sealed_at_utc']=datetime.now(timezone.utc).isoformat()
source['first_seal_correction']='FINALIZATION-CORRECTION.actual.json; exact first source/verifier/failed result retained in FIRST-SEAL-AND-INITIAL-PLAN.exact.zip'
source['files']=[pin(p) for p in sorted(H.iterdir()) if p.is_file()]
write('SOURCE.final-a02.json',source)
argv=[sys.executable,'-I','-B','-O',str(H/'verify_portable_a02.py'),str(H)]
r=subprocess.run(argv,cwd=Path('C:/Users/1/AppData/Local/Temp'),capture_output=True,text=True,encoding='utf-8')
write('VERIFY.final-a02.actual.json',dict(machine_id=source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,source=pin(H/'SOURCE.final-a02.json')))
need(r.returncode==0,r.stderr or r.stdout)
write('DELIVERY.final-a02.actual.json',dict(machine_id=source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),source=pin(H/'SOURCE.final-a02.json'),verify=pin(H/'VERIFY.final-a02.actual.json'),graph=pin(H/'GRAPH.result.md'),correction=pin(H/'FINALIZATION-CORRECTION.actual.json'),code_bytes=225,metadata_bytes=252,read_calls=26,free_bytes_at_close=shutil.disk_usage(H).free,package_ceiling_bytes=98304,review_at_utc=(datetime.now(timezone.utc)+timedelta(hours=168)).isoformat(),no_new_EXE_read_during_finalize=True,paid_payer_cadence_confirmed=False))
size=sum(p.stat().st_size for p in H.iterdir() if p.is_file());need(size<=98304,'Output ceiling '+str(size))
print(json.dumps(dict(source=pin(H/'SOURCE.final-a02.json'),delivery=pin(H/'DELIVERY.final-a02.actual.json'),package_bytes=size,verifier_exit=r.returncode,stdout=r.stdout)))
