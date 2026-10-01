"""Create-only R0143 audit consumers from preserved read-only R0142 readers."""
from pathlib import Path
import hashlib,json,sys
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
O=B/'R0143-four-save-endpoint-audit-reinforcement-a01'
OLDLIVE='episode02-e2-05-d26-six-gap-ui-live-20261001-a06'
NEWLIVE='episode02-e2-05-d26-six-gap-trace-live-20261001-a07'
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:s=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':s}
def dump(p,v):
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 sys.stdout.reconfigure(encoding='utf-8');assert not O.exists()
 sources=[('inspect_R0142_endpoints_a01.py','inspect_R0143_endpoints_a01.py'),('decode_R0142_four_endpoints_a03.py','decode_R0143_four_endpoints_a01.py'),('summarize_R0142_saved_facts_a04.py','summarize_R0143_saved_facts_a01.py')]
 rows=[]
 for old,new in sources:
  src=B/old;s=src.read_text(encoding='utf-8');oldpin=ident(src)
  s=s.replace('R0142','R0143').replace('R0143-four-save-endpoint-audit-reinforcement-a02','R0143-four-save-endpoint-audit-reinforcement-a01').replace(OLDLIVE,NEWLIVE).replace('root-attempt-06-hidden-modal-ui','root-attempt-07-trace-diagnostic').replace('C:/w/e2cap1001d','C:/w/e2cap1001e').replace('4ad477ee33e15a93e412f711c7b05b216a2e6651','419cac1a956c7be356d886256c7bc689cda5327d').replace('Runtime explicitly4ad','Runtime explicitly419cac')
  if old.startswith('decode'):
   s=s.replace("report['runtime_source_head']=config['source_commit'];report['runtime_dll']=ident(Path(config['bridge_dll']))", "report['runtime_source_head']=config['source_commit'];report['runtime_dll']=ident(Path(config['bridge_dll']));gate('runtime parser checkout equals explicit capture source',RUNTIME.resolve()==Path(config['source_root']).resolve())")
   s=s.replace("raw=checked(pair['immutable']);gate", "raw=checked(pair['immutable']);copies.append(freeze(raw,label+'-immutable.ck3'));gate")
   s=s.replace("'Daily managed DTO unavailable; no old trace used, no selector/case-sole-cause check run.'", "'Daily managed trace export cap failure; DTO unavailable. No previous-run trace, selector or causal success verifier used.'")
  if old.startswith('summarize'):
   s=s.replace("if any(r['key']=='name'and r['value']==key for r in v)","if any(r['key']in['name','flag']and isinstance(r['value'],str)and r['value'].strip(chr(34))==key for r in v)")
   s=s.replace("fields['trait_XP_saved_block']=one(c['entries'],'trait_xp')", "fields['saved_trait_xp_amounts']=one(c['entries'],'trait_xp_amounts');fields['complete_saved_death_data']=dead;fields['saved_death_artifact_field']=one(dead,'artifact')if dead is not None else None;fields['saved_death_artifact_missing_not_actual_native_null']=dead is not None and not any(r['key']=='artifact'for r in dead)")
   s=s.replace('Runtime4ad/DLLC4C16...','Runtime419cac / actual R0143 DLL0F752E3F...')
  assert 'R0142'not in s and OLDLIVE not in s and 'Runtime4ad'not in s
  compile(s,str(B/new),'exec')
  with(B/new).open('x',encoding='utf-8',newline='\n')as f:f.write(s)
  assert ident(src)==oldpin
  rows.append({'base_reader':oldpin,'new_reader':ident(B/new),'runtime_inputs':'R0143 only; no R0142 raw or endpoint value loaded','mutations':'paths/source pins, correct saved flag matcher/trait key, exact four raw save preservation'})
 dump(B/'R0143-endpoint-audit-reader-derivation-a01.json',{'readers':rows,'compile_only':'PASS','no_launch_no_source_change':True})
 print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
