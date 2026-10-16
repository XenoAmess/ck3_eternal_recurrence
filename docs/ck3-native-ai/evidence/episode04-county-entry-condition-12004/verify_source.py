from pathlib import Path
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 m=json.loads((H/'MANIFEST.json').read_bytes());p=H/'source-originals.zip';b=p.read_bytes()
 need(len(b)==m['archive']['bytes'] and sha(b)==m['archive']['sha256'],'Archive differs')
 with zipfile.ZipFile(p) as z:
  need(z.testzip() is None,'ZIP CRC differs');need(set(z.namelist())==set(m['members']),'Member set differs')
  for n,e in m['members'].items():
   raw=z.read(n);need(len(raw)==e['bytes'] and sha(raw)==e['sha256'],'Original member differs')
  f=json.loads(z.read('FUNCTION.actual-a01.json'));c=json.loads(z.read('SOURCE-CONTRACT.actual-a01.json'));raw=z.read('actual-function.bin');cursor=int(f['begin_rva'],16);starts=set();joined=b''
  for at,h,_,_ in f['instructions']:
   need(int(at,16)==cursor,'Instruction sequence gap');starts.add(cursor);v=bytes.fromhex(h);cursor+=len(v);joined+=v
  need(joined==raw and cursor==int(f['end_exclusive'],16) and len(raw)==420 and sha(raw)=='d011c6bb38172950e99324f1fa7157d0083cbe5316587b7945ed5b168f80370c','Complete raw body differs')
  for row in f['branches']+f['calls_unexpanded']:
   at=int(row['at_rva'],16);v=bytes.fromhex(row['hex']);op=v[0]
   if op in (0xE8,0xE9):d=int.from_bytes(v[1:5],'little',signed=True)
   elif op==0xEB or 0x70<=op<=0x7F:d=int.from_bytes(v[1:2],'little',signed=True)
   else:need(op==0x0F and 0x80<=v[1]<=0x8F,'Unknown branch form');d=int.from_bytes(v[2:6],'little',signed=True)
   target=at+len(v)+d;need(target==int(row['target_rva'],16),'Direct target differs')
   if row in f['branches']:need(target in starts,'Local branch not in complete body')
  grouped=[int(x,16) for g in c['branches'] for x in g['branch_rvas']]
  need(len(grouped)==len(set(grouped))==28 and set(grouped)=={int(x['at_rva'],16) for x in f['branches']},'Branch grouping differs')
  need(c['qualification']['R04_positive'] is False and c['qualification']['subpredicate_semantics_closed'] is False,'Evidence boundary differs')
 print(json.dumps(dict(machine_id=m['machine_id'],result='EXACT_SOURCE_STRUCTURE_PASS',code_bytes=420,branches=28,new_live_observation=False,R04_positive=False,semantic_correctness_verified=False,SDK_EXE_actions=0)))
 return 0
if __name__=='__main__':raise SystemExit(main())
