"""Exact immutable caller duplicate archive; raw695B stays directly available."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile
H=Path(__file__).parent.resolve();z=H/'CALLER-DETAILS.exact.zip';members=[]
if z.exists():raise ValueError('Archive alreadyexists')
for name in ('CALLER.held.actual.json','caller28A63E0.asm'):
    p=(H/name).resolve()
    if p.parent!=H or not p.is_file():raise ValueError('Exact path guard')
    b=p.read_bytes();members.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    with zipfile.ZipFile(z,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as f:f.writestr(name,b)
    with zipfile.ZipFile(z) as f:
        if f.read(name)!=b:raise ValueError('Roundtrip')
    p.unlink()
with (H/'CALLER-DETAILS-ARCHIVE.actual.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(dict(machine_id='desktop-3fevhd2-1c74096080',at_utc=datetime.now(timezone.utc).isoformat(),reason='Caller details duplicate canonicalR0178 source; exact archive preserves both while body695B remains unfolded. Not new evidence or rerun.',archive=dict(path=z.name,bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest()),members=members,unfolded_archived_files_no_longer_present=True,new_EXE_reads=0),f,indent=2);f.write('\n')
print(json.dumps(dict(package_bytes=sum(p.stat().st_size for p in H.iterdir() if p.is_file()),archive_bytes=z.stat().st_size,new_EXE_reads=0)))
