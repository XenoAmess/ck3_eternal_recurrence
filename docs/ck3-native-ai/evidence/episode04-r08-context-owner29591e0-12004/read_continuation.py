"""Only approved real fallthrough/JE extents and explicit unwind chaining."""
from pathlib import Path
from datetime import datetime,timezone
import capstone,gzip,hashlib,json,struct,subprocess,sys
H=Path(__file__).parent;R=Path('D:/workspace/ck3_eternal_recurrence')
E=Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')
def need(ok,msg):
    if not ok:raise ValueError(msg)
def load(n):return json.loads((H/n).read_bytes())
def write(n,o):
    with (H/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,indent=2);f.write('\n')
def stamp():
    s=E.stat();return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino)
prior=load('CAPTURE.physical.actual.json');layout=load('PE-MAP.held.actual.json')
plan=load('PLAN.before-read.corrected-a03.json')
plan['topic']='e04-R08-29591E0-real-sameframe-continuations'
plan['created_at_utc']=datetime.now(timezone.utc).isoformat()
plan['question']='Close only the real fallthrough2959214 and JE29592B1 extents after proving explicit unwind relationship.'
plan['observation']['owner_scope']='Root-approved173B continuation only, unwindheads/CHAININFO tuples; cumulativecode225/meta252/reads26; no new callee'
plan['observation']['stop_condition']='Read only heldextent2959214..29592B1 and29592B1..29592C1 after sameframeproof; stop RET/newexternaledge; no claim farther logic complete.'
write('PLAN.before-continuation.json',plan)
argv=[sys.executable,'-B',str(R/'tools/native_research_plan.py'),'check',str(H/'PLAN.before-continuation.json')]
run=subprocess.run(argv,cwd=R,capture_output=True,text=True,encoding='utf-8')
write('CHECK.before-continuation.actual.json',dict(machine_id=plan['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),argv=argv,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,new_EXE_bytes=0))
need(run.returncode==0,'Ordinary continuationplan')
before=stamp();need(before==prior['stat_before']==prior['stat_after'],'Same actual EXE')
ledger=[];extents=[(0x2959214,0x29592b1,0x52888ec),(0x29592b1,0x29592c1,0x5288900)]
try:
    with E.open('rb') as f:
        def read(rva,n,kind):
            need(len(ledger)+prior['read_calls']<26,'Total reads')
            if kind=='metadata':need(sum(x['bytes'] for x in ledger if x['kind']=='metadata')+n+prior['metadata_bytes']<=252,'Total metadata')
            else:need(sum(x['bytes'] for x in ledger if x['kind']=='code')+n+prior['code_bytes']<=225,'Total code')
            ss=[s for s in layout['sections'] if s['rva']<=rva<rva+n<=s['rva']+s['raw_size']];need(len(ss)==1,'Raw mapping')
            off=ss[0]['raw_offset']+rva-ss[0]['rva'];f.seek(off);b=f.read(n);need(len(b)==n,'Short read')
            ledger.append(dict(rva=rva,file_offset=off,bytes=n,kind=kind,hex=b.hex() if kind=='metadata' else None,sha256=hashlib.sha256(b).hexdigest()))
            return b
        meta=[]
        for b,e,u in extents:
            header=read(u,4,'metadata');flags=header[0]>>3;chain=None
            if flags&4:chain=struct.unpack('<III',read(u+4+((header[2]+1)//2)*4,12,'metadata'))
            need(chain==(0x29591e0,0x2959214,0x514120c),'Require exact CHAININFO originalroot before continuationcode')
            meta.append(dict(begin_rva=b,end_exclusive=e,unwind_rva=u,header_hex=header.hex(),flags=flags,chained_to=list(chain)))
        bodies=[]
        for b,e,u in extents:
            raw=read(b,e-b,'code');name=f'continuation-{b:X}.bin'
            with (H/name).open('xb') as o:o.write(raw)
            bodies.append(raw)
    need(stamp()==before,'Image changed')
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);dis.detail=True;out=[]
    for (b,e,u),raw in zip(extents,bodies):
        ins=list(dis.disasm(raw,b));need(sum(i.size for i in ins)==len(raw),'Full extent decode')
        asm='\n'.join(f'{i.address:08X}  {i.bytes.hex(" "):<44} {i.mnemonic} {i.op_str}' for i in ins)+'\n'
        with (H/f'continuation-{b:X}.asm.gz').open('xb') as o:o.write(gzip.compress(asm.encode(),mtime=0))
        out.append(dict(begin_rva=b,end_exclusive=e,bytes=len(raw),instruction_count=len(ins),sha256=hashlib.sha256(raw).hexdigest(),assembly_sha256=hashlib.sha256(asm.encode()).hexdigest()))
    write('CONTINUATION.actual.json',dict(machine_id=plan['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),exe_sha256_reused=prior['exe_sha256_reused'],stat_before=before,stat_after=stamp(),source_extents=meta,decoded=out,read_ledger=ledger,cumulative_code_bytes=prior['code_bytes']+sum(len(x) for x in bodies),cumulative_metadata_bytes=prior['metadata_bytes']+sum(x['bytes'] for x in ledger if x['kind']=='metadata'),cumulative_read_calls=prior['read_calls']+len(ledger),no_new_callee=True,no_whole_hash=True,logical_complete_not_yet_claimed=True))
    print(json.dumps(dict(continuations=out,cumulativecode=225,cumulativemetadata=252,cumulativereads=26,package_bytes=sum(p.stat().st_size for p in H.iterdir() if p.is_file()))))
except Exception as e:
    write('CONTINUATION-STOPPED.actual.json',dict(machine_id=plan['machine_id'],at_utc=datetime.now(timezone.utc).isoformat(),error=repr(e),ledger=ledger,no_further_reads=True))
    raise
