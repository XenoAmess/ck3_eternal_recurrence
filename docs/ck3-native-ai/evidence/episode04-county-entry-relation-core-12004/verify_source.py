from pathlib import Path
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 m=json.loads((H/'MANIFEST.json').read_bytes());p=H/'source-originals.zip';b=p.read_bytes();need(len(b)==m['archive']['bytes'] and sha(b)==m['archive']['sha256'],'Archive differs')
 with zipfile.ZipFile(p) as z:
  need(z.testzip() is None and set(z.namelist())==set(m['members']),'ZIP differs')
  for n,e in m['members'].items():
   b=z.read(n);need(len(b)==e['bytes'] and sha(b)==e['sha256'],'Member differs')
  f=json.loads(z.read('FUNCTION.actual-a01.json'));c=json.loads(z.read('SOURCE-CONTRACT.actual-a01.json'));raw=z.read('actual-function.bin');cur=0x2C09620;joined=b'';starts=set()
  for at,h,_,_ in f['instructions']:
   need(cur==int(at,16),'Gap');starts.add(cur);b=bytes.fromhex(h);joined+=b;cur+=len(b)
  need(joined==raw and cur==0x2C096DF and len(raw)==191 and sha(raw)=='701c63b6a5f7ed78ce75d6a591fcc4dc0ae2464267a05a23f5b5feb3a3cd8edb','Fullbody differs')
  for r in f['branches']+f['calls_unexpanded']:
   at=int(r['at_rva'],16);b=bytes.fromhex(r['hex'])
   if b[0] in(0xE8,0xE9):d=int.from_bytes(b[1:5],'little',signed=True)
   elif b[0]==0x0F:d=int.from_bytes(b[2:6],'little',signed=True)
   else:d=int.from_bytes(b[1:2],'little',signed=True)
   target=at+len(b)+d;need(target==int(r['target_rva'],16),'Target differs')
   if r['internal']:need(target in starts,'Internal boundary differs')
  need(raw[0x2C09698-0x2C09620:0x2C0969A-0x2C09620]==bytes.fromhex('7421'),'Aux equality JE changed')
  need(raw[0x2C09690-0x2C09620:0x2C09693-0x2C09620]==bytes.fromhex('4885db'),'Aux64pointer testchanged')
  pcs=[int(x,16) for g in c['branches'] for x in g['branch_rvas']];need(len(pcs)==len(set(pcs))==11 and set(pcs)=={int(r['at_rva'],16) for r in f['branches']},'Branch groups differ')
  need(c['qualification']['R04_positive'] is False and c['qualification']['formal_diplomatic_relation_name_closed'] is False,'Qualification changed')
 print(json.dumps(dict(machine_id=m['machine_id'],result='EXACT191B_SOURCE_STRUCTURE_PASS',aux_pointer_null_or_EQUAL=True,all11branches=True,semantic_correctness_verified=False,R04_positive=False,SDK_or_EXE_actions=0)))
 return 0
if __name__=='__main__':raise SystemExit(main())
