"""Stdlib byte/branch/CHAININFO replay; no EXE, repo, capstone or runtime."""
from pathlib import Path
import gzip,hashlib,json,re,struct,sys,zipfile
H=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(n):return json.loads((H/n).read_bytes())
s=read('SOURCE.final-a02.json')
for p in s['files']:
    b=(H/p['path']).read_bytes();need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'Pin '+p['path'])
for record in ('PREPARATION-ARCHIVE.actual.json','CALLER-DETAILS-ARCHIVE.actual.json'):
    a=read(record)
    with zipfile.ZipFile(H/a['archive']['path']) as z:
        for p in a['members']:
            b=z.read(p['path']);need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'Archived '+p['path'])
with zipfile.ZipFile(H/'CALLER-DETAILS.exact.zip') as z:
    caller=json.loads(z.read('CALLER.held.actual.json'));caller_asm=z.read('caller28A63E0.asm')
rawcaller=(H/'caller28A63E0.bin').read_bytes()
need(len(rawcaller)==695 and hashlib.sha256(rawcaller).hexdigest()=='ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede','Held caller')
need(caller['selected_call']['at_rva']==0x28a65be and caller['selected_call']['target_rva']==0x29591e0,'Caller role')
need(rawcaller[0x1de:0x1e3].hex()=='e81d2c0b00','Actual CALL boundary')
need(0x28a65c3+int.from_bytes(rawcaller[0x1df:0x1e3],'little',signed=True)==0x29591e0,'CALL target')
def rows(text):
    out=[]
    for line in text.decode().splitlines():
        m=re.fullmatch(r'([0-9A-Fa-f]{8})\s+((?:[0-9A-Fa-f]{2} )*[0-9A-Fa-f]{2})\s+(.*)',line)
        if m:out.append((int(m[1],16),bytes.fromhex(m[2]),m[3].strip()))
    return out
need(b''.join(x[1] for x in rows(caller_asm))==rawcaller,'Saved caller ASM')
spec=[(0x29591e0,0x2959214,'function.bin','function.asm.gz'),(0x2959214,0x29592b1,'continuation-2959214.bin','continuation-2959214.asm.gz'),(0x29592b1,0x29592c1,'continuation-29592B1.bin','continuation-29592B1.asm.gz')]
allrows=[]
for begin,end,binname,asmname in spec:
    raw=(H/binname).read_bytes();rr=rows(gzip.decompress((H/asmname).read_bytes()));at=begin
    need(len(raw)==end-begin,'Extent bytes')
    for pc,b,asm in rr:need(pc==at,'Continuous decode');at+=len(b)
    need(at==end and b''.join(x[1] for x in rr)==raw,'Complete saved extent ASM')
    allrows+=rr
need(len(allrows)==54 and sum(len(x[1]) for x in allrows)==225,'Combined size')
starts={x[0] for x in allrows};calls=[];jumps=[]
for pc,b,asm in allrows:
    op=asm.split()[0]
    if op=='call':
        need(b[0]==0xe8 and len(b)==5,'Direct call');calls.append((pc,pc+5+int.from_bytes(b[1:],'little',signed=True)))
    if op.startswith('j'):
        if len(b)==2:to=pc+2+int.from_bytes(b[1:],'little',signed=True)
        elif len(b)==6 and b[0]==15:to=pc+6+int.from_bytes(b[2:],'little',signed=True)
        else:raise ValueError('Unexpected branchform')
        need(to in starts,'Unclosed external branch');jumps.append((pc,to))
need(calls==[(0x2959251,0x230f8e0),(0x295928c,0x880340)],'Named calls')
need([pc for pc,b,asm in allrows if asm=='ret']==[0x29592c0],'One RET')
original=read('CAPTURE.physical.actual.json');cont=read('CONTINUATION.actual.json')
need(original['stat_before']==original['stat_after']==cont['stat_before']==cont['stat_after'],'Observed local file identity')
need(original['machine_id']==cont['machine_id']==s['machine_id'],'Machine')
ledger=original['read_ledger']+cont['read_ledger']
need(len(ledger)==26 and sum(x['bytes'] for x in ledger if x['kind']=='code')==225 and sum(x['bytes'] for x in ledger if x['kind']=='metadata')==252,'Exact read budget')
for x in ledger:
    if x['kind']=='metadata':
        raw=bytes.fromhex(x['hex']);need(len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256'],'Metadata raw')
for e in cont['source_extents']:need(e['flags']==4 and e['chained_to']==[0x29591e0,0x2959214,0x514120c],'Exact CHAININFO root')
need(s['decision']['paid_military_amount_raw'] is None and s['decision']['payer'] is None and s['decision']['cadence'] is None,'Typed unknowns')
print(json.dumps(dict(ok=True,portable=True,files_verified=len(s['files']),code_bytes=225,metadata_bytes=252,read_calls=26,instructions=54,internal_jump_count=len(jumps),direct_calls=calls,RET_RVA='29592C0',runtime_or_business_proved=False,semantic_layer='Saved bytes/source analysis only; no opaquecallee effects or paid/payer/cadence proof')))
