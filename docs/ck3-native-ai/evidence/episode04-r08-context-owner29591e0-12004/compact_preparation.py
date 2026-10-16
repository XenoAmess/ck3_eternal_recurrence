"""Exact small preparation archive before continuation output; no EXE reads."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile
H=Path(__file__).parent.resolve()
names=['prepare.py','repair_plan.py','repair_status.py','derive_continuation.py','read_body.py','PLAN.before-read.json','PLAN.before-read.corrected-a02.json','PLAN-CHECK.rejected-a01.actual.json','PLAN-CHECK.rejected-a02.actual.json']
members=[];z=H/'PREPARATION.exact.zip'
if z.exists():raise ValueError('Archive alreadyexists')
for name in names:
    p=(H/name).resolve()
    if p.parent!=H or not p.is_file():raise ValueError('Exact archive guard')
    b=p.read_bytes();members.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    with zipfile.ZipFile(z,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as f:f.writestr(name,b)
    with zipfile.ZipFile(z) as f:
        if f.read(name)!=b:raise ValueError('Exact member roundtrip')
    p.unlink()
with (H/'PREPARATION-ARCHIVE.actual.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(dict(machine_id='desktop-3fevhd2-1c74096080',at_utc=datetime.now(timezone.utc).isoformat(),reason='Preserve exact source/check rejection and readproducer scripts while keeping approved96KiB lane bounded. Raw caller/newbody/metadata unchanged.',archive=dict(path=z.name,bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest()),members=members,unfolded_archived_files_no_longer_present=True,new_EXE_reads=0),f,indent=2);f.write('\n')
size=sum(p.stat().st_size for p in H.iterdir() if p.is_file())
if size>98304:raise ValueError('Output ceiling')
print(json.dumps(dict(package_bytes=size,archive_bytes=z.stat().st_size,new_EXE_reads=0)))
