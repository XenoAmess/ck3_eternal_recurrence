"""Portable stdlib integrity check; optional current repository source comparison."""
from pathlib import Path
import argparse,hashlib,json
P=Path(__file__).resolve().parent
def check(ok,why):
 if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path);a=p.parse_args()
 delivery=json.loads((P/'DELIVERY.json').read_text(encoding='utf-8'))
 for x in delivery['files']:
  f=P/x['relative_path'];raw=f.read_bytes();check(len(raw)==x['bytes'] and sha(raw)==x['sha256'],'Package bytes changed: '+str(f))
 d=json.loads((P/'INPUTS.json').read_text(encoding='utf-8'))
 check(d['evidence_layer']=='held_native_source_and_current_source_inference_only','Evidence layer changed')
 check(d['proposal']['Root_final_H'] is None and d['proposal']['positive_target'] is None,'Future admission filled')
 check(d['new_EXE_bytes_read']==d['SDK_calls']==d['native_builds']==0,'Source-only scope changed')
 for row in d['held_native_functions']:
  raw=bytes.fromhex(row['full_function_hex']);check(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'Held native function hash differs')
 gate=next(x for x in d['held_native_functions'] if x['id']=='chunk2657EF0')
 raw=bytes.fromhex(gate['full_function_hex']);base=int(gate['begin_rva'],16)
 for pc,hexbytes in [(0x2657F51,'83b988070000ff'),(0x2657F6F,'83b93c070000ff'),(0x2657FDD,'4180b8d401000000'),(0x2657FE7,'4180b8ec01000000'),(0x265800C,'4183b97001000000'),(0x2658019,'e8824ae5ff')]:
  b=bytes.fromhex(hexbytes);check(raw[pc-base:pc-base+len(b)]==b,'Exact chunk gate bytes differ')
 if a.repo:
  for x in d['repo_source_refs']:
   f=a.repo/x['repo_relative_path'];raw=f.read_bytes();check(len(raw)==x['bytes'] and sha(raw)==x['sha256'],'Repository source changed: '+str(f))
 print(json.dumps({'status':'PASS','package_files':len(delivery['files']),'held_function_count':len(d['held_native_functions']),'repo_sources_checked':bool(a.repo),'live_admission':False,'SDK_calls':0,'EXE_reads':0}))
if __name__=='__main__':main()
