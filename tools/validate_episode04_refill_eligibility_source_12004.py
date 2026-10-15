"""Portable raw/instruction integrity checks; no EXE, native, SDK or live proof."""
from pathlib import Path
import argparse,hashlib,json

def need(ok,m):
 if not ok:raise ValueError(m)
def validate(index):
 index=Path(index);root=index.parent;v=json.loads(index.read_text(encoding='utf-8'))
 need(v['schema']=='xar.episode04.persistent-refill-eligibility-source.v1','source schema differs')
 need(v['version']=='1.20.0.4' and v['exe_sha256']=='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518','exact source build differs')
 all_ins={};count=0
 for row in v['functions']:
  raw=bytes.fromhex((root/row['hex_file']).read_text(encoding='ascii'))
  need(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'raw source hash differs')
  p=root/row['instructions_file'];b=p.read_bytes()
  need(hashlib.sha256(b).hexdigest()==row['instructions_sha256'],'instruction JSON differs')
  ins=json.loads(b);cursor=int(row['begin_rva'],16)
  for value in ins:
   rva=int(value['rva'],16);code=bytes.fromhex(value['bytes'])
   need(rva==cursor and raw[rva-int(row['begin_rva'],16):rva-int(row['begin_rva'],16)+len(code)]==code,'source instruction gap/mismatch')
   need(rva not in all_ins,'overlapping source functions');all_ins[rva]=value;cursor+=len(code);count+=1
  need(cursor==int(row['end_rva_exclusive'],16),'source endpoint differs')
 for rva,code in {0x262C6F2:'83b93801000001',0x262C743:'b001',0x262C989:'e862b50200',
                  0x262CABF:'8b8938010000',0x262CAC5:'83f903',0x262CB52:'83f902',
                  0x2657EF4:'8b01',0x2657F08:'0f8d1b010000',0x2657F5E:'837a1803',
                  0x262CA14:'e8d7b40200'}.items():
  need(all_ins[rva]['bytes'].lower()==code,'critical operand/call source differs at '+hex(rva))
 p=root/v['cached_core_call_file'];b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==v['cached_core_call_sha256'],'cache caller source differs')
 cached={int(r['rva'],16):r for r in json.loads(b)}
 need(cached[0x2A98B44]['bytes'].lower()=='488b9648010000' and cached[0x2A98B53]['bytes'].lower()=='e8583eb9ff','actual cached148 caller changed')
 return {'status':'PORTABLE_SOURCE_INTEGRITY_PASS','instructions':count,'functions':len(v['functions']),
  'semantic_correctness_verified':False,'live_execution_performed':False,'new_EXE_reads':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('index',type=Path);args=p.parse_args();print(json.dumps(validate(args.index)))
if __name__=='__main__':main()
