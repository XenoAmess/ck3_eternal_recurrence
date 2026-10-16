from pathlib import Path
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 m=json.loads((H/'MANIFEST.json').read_bytes());p=H/'source-originals.zip';raw=p.read_bytes()
 need(len(raw)==m['archive']['bytes'] and sha(raw)==m['archive']['sha256'],'Archive changed')
 with zipfile.ZipFile(p) as z:
  need(z.testzip() is None and set(z.namelist())==set(m['members']),'ZIP differs')
  for n,e in m['members'].items():
   b=z.read(n);need(len(b)==e['bytes'] and sha(b)==e['sha256'],'Member changed')
  f=json.loads(z.read('attempt-a02/FUNCTION.actual-a01.json'));c=json.loads(z.read('SOURCE-CONTRACT.actual-a02.json'));raw=z.read('attempt-a02/actual-function.bin');cur=int(f['begin_rva'],16);joined=b'';starts=set()
  for at,h,_,_ in f['instructions']:
   need(cur==int(at,16),'Source gap');starts.add(cur);b=bytes.fromhex(h);cur+=len(b);joined+=b
  need(joined==raw and len(raw)==131 and cur==0x2C09E73 and sha(raw)=='344dc31069a905f0615c45fd59967f35530a14f75e496cda079841c897a3652b','Body differs')
  for row in f['branches']+f['calls_unexpanded']:
   at=int(row['at_rva'],16);b=bytes.fromhex(row['hex']);delta=int.from_bytes(b[1:5] if b[0] in (0xE8,0xE9) else b[1:2],'little',signed=True);target=at+len(b)+delta
   need(target==int(row['target_rva'],16),'Branchtarget differs')
   if row['internal']:need(target in starts,'Internal boundary differs')
  tails=[r for r in f['branches'] if not r['internal']];need(len(tails)==1 and tails[0]['mnemonic']=='jmp' and int(tails[0]['target_rva'],16)==0x2C09620,'Exact opaque tail differs')
  need(len(f['calls_unexpanded'])==1 and int(f['calls_unexpanded'][0]['target_rva'],16)==0x24D4ED0,'Only directcallee differs')
  pcs=[int(x,16) for g in c['branches'] for x in g['branch_rvas']];need(len(pcs)==len(set(pcs))==8 and set(pcs)=={int(r['at_rva'],16) for r in f['branches']},'Grouping differs')
  need(c['R04_positive'] is False and c['military_relation_semantics_closed'] is False and c['attempt_accounting']['first_exact_read_ledger_persisted'] is False,'Scope changed')
 print(json.dumps(dict(machine_id=m['machine_id'],result='SOURCE_STRUCTURE_PASS',body131=True,tail2C09620_opaque=True,first_failed_preserved=True,semantic_correctness_verified=False,R04_positive=False,SDK_or_EXE_actions=0)))
 return 0
if __name__=='__main__':raise SystemExit(main())
