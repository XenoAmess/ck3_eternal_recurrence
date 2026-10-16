"""Preserve exact producer/first-seal originals in ZIP, then seal within128KiB."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,zipfile
H=Path(__file__).parent.resolve()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def pin(p):
    b=p.read_bytes();return dict(path=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(name,obj):
    with (H/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
old_source=json.loads((H/'SOURCE.actual.json').read_bytes())
old_verify=(H/'verify_portable.py').read_text(encoding='utf-8')
before=sum(p.stat().st_size for p in H.iterdir() if p.is_file())
names=sorted([p.name for p in H.iterdir() if p.is_file() and p.suffix=='.py' and p.name!=Path(__file__).name]+['SOURCE.actual.json','VERIFY.actual.json','DELIVERY.actual.json'])
raw={name:(H/name).read_bytes() for name in names}
members=[pin(H/name) for name in names]
z=H/'PRODUCERS-FIRST-SEAL.exact.zip'
with zipfile.ZipFile(z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as f:
    for name,b in raw.items():
        zi=zipfile.ZipInfo(name,(2026,10,16,19,42,0));zi.compress_type=zipfile.ZIP_DEFLATED;f.writestr(zi,b)
with zipfile.ZipFile(z) as f:
    need(sorted(f.namelist())==names,'Archive member names')
    for name,b in raw.items():need(f.read(name)==b,'Archive byte comparison '+name)
for name in names:
    p=(H/name).resolve();need(p.parent==H and p.is_file() and p.read_bytes()==raw[name],'Exact unlink guard');p.unlink()
new_verify=old_verify.replace("read('SOURCE.actual.json')","read('SOURCE.final-a01.json')")
needle="l=read('LITERALS.actual.json');"
extra="import zipfile\nwith zipfile.ZipFile(H/src['exact_archive']['path']) as z:\n    for p in src['archived_members']:\n        b=z.read(p['path']);need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'Archived pin '+p['path'])\n"
need(needle in new_verify,'Verifier insertion')
new_verify=new_verify.replace(needle,extra+needle,1)
with (H/'verify_portable_final.py').open('x',encoding='utf-8',newline='\n') as f:f.write(new_verify)
write('PACKAGE-REPACK.actual.json',dict(machine_id=old_source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),reason='Initial portable verification passed but first closed package131445B exceeded131072B by373B. Exact producer/first-seal originals archived and byte-compared before unlinking unfolded copies.',first_seal_package_bytes=131445,old_source_pin=next(p for p in members if p['path']=='SOURCE.actual.json'),archive=pin(z),members=members,unfolded_original_producers_and_first_seal_no_longer_present=True,new_EXE_reads=0,raw_locator_receipts_unchanged=True))
source=dict(old_source)
source['schema']='xar.e04.r08.resource4-name-locator-source.final-a01'
source['sealed_at_utc']=datetime.now(timezone.utc).isoformat()
source['exact_archive']=pin(z);source['archived_members']=members
source['files']=[pin(p) for p in sorted(H.iterdir()) if p.is_file()]
source['first_seal_failure_preserved_in']='PACKAGE-REPACK.actual.json and PRODUCERS-FIRST-SEAL.exact.zip'
write('SOURCE.final-a01.json',source)
argv=[sys.executable,'-B','-O',str(H/'verify_portable_final.py'),str(H)]
r=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8')
write('VERIFY.final-a01.actual.json',dict(machine_id=source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,source_pin=pin(H/'SOURCE.final-a01.json')))
need(r.returncode==0,'Repacked portable verifier')
write('DELIVERY.final-a01.actual.json',dict(machine_id=source['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),source=pin(H/'SOURCE.final-a01.json'),verify=pin(H/'VERIFY.final-a01.actual.json'),archive=pin(z),repack=pin(H/'PACKAGE-REPACK.actual.json'),no_new_EXE_reads_during_repack=True))
size=sum(p.stat().st_size for p in H.iterdir() if p.is_file());need(size<=131072,'Final package ceiling')
print(json.dumps(dict(source=pin(H/'SOURCE.final-a01.json'),delivery=pin(H/'DELIVERY.final-a01.actual.json'),archive=pin(z),repack=pin(H/'PACKAGE-REPACK.actual.json'),package_bytes=size,verifier_exit=r.returncode)))
