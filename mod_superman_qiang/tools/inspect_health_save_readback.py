"""Extend the frozen v6 variable reader with exact saved native basehealth."""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re

LEGACY=Path(__file__).with_name('inspect_save_readback.py')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def inspect(args):
 args.output_dir.mkdir(exist_ok=False)
 spec=importlib.util.spec_from_file_location('retained_sxad_v6',LEGACY)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 data=module.inspect(args.run,args.save_dir,args.sdk,args.player_id,args.output_dir)
 for c in data['characters']:
  raw_path=args.output_dir/f'character-{c["character_id"]}.txt'
  text=raw_path.read_text(encoding='utf-8')
  health=re.findall(r'(?m)^\s*health=(-?\d+(?:\.\d+)?)\s*$',text)
  if len(health)!=1:raise ValueError(f'unique native basehealth missing for{c["character_id"]}: {health}')
  raw=health[0];ticks=Decimal(raw)*100000
  if ticks!=ticks.to_integral_value():raise ValueError('basehealth finer thanQ100000')
  c['base_health_saved']={'field':'alive_data.health','raw_text':raw,'decimal':str(Decimal(raw)),'q100000_ticks':int(ticks)}
  for v in c['variables'].values():
   if v.get('type')=='value':
    signed=v['signed_identity']
    v['fixed5_ticks_exact']=signed
    assert v['integer_exact']==(signed//100000 if signed%100000==0 else None)
  for m in c['modifiers']:
   q=Decimal(m['scale_decimal'])*100000
   m['scale_q100000_ticks_exact']=int(q) if q==q.to_integral_value() else None
 data['schema']='sxad.real-save-health1.1.0-readback.v1'
 data['decoder_script_sha256']=sha(Path(__file__))
 data['retained_v6_decoder']={'path':LEGACY.as_posix(),'sha256':sha(LEGACY)}
 data['readback_scope']='Independently saved base skills/basehealth, signed variables and sampled modifier scale; native effective health comes from separate player query or recorded scripted getters.'
 output=args.output_dir/'health-readback.json'
 with output.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'output':str(output),'sha256':sha(output),'counts':[data['pass_count'],data['fail_count'],data['missing_count']],'characters':len(data['characters'])}))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['run','save-dir','sdk','output-dir']:p.add_argument('--'+name,required=True,type=Path)
 p.add_argument('--player-id',required=True,type=int)
 inspect(p.parse_args())
if __name__=='__main__':main()
