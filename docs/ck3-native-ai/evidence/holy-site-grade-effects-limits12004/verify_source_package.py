"""Verify this portable static research package, never CK3 semantics or execution."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
checks=0
def need(value,message):
 global checks
 checks+=1
 if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

contract=json.loads((HERE/'effect-condition-contract-a03.json').read_text(encoding='utf-8'))
need(contract['machine_id']=='4-8e1c2f1861','Machine source mismatch')
need(contract['new_live_evidence'] is False and contract['no_build'] is True,'Proof layer changed')
for row in contract['evidence_files']:
 path=(ROOT/row['package_path']).resolve()
 need(ROOT.resolve() in path.parents,'Source path escapes package')
 need(path.is_file() and path.stat().st_size==row['bytes'],'Source size mismatch '+str(path))
 need(digest(path)==row['sha256'],'Source SHA mismatch '+str(path))
for folder in ('native','limits-native'):
 for p in (HERE/folder).glob('*.json'):
  data=json.loads(p.read_text(encoding='utf-8'))
  if isinstance(data.get('bytes_hex'),str) and isinstance(data.get('raw_sha256'),str):
   body=bytes.fromhex(data['bytes_hex'])
   need(hashlib.sha256(body).hexdigest()==data['raw_sha256'],'Raw source byte SHA mismatch '+p.name)
faiths=json.loads((HERE/'authored-faith-counts.json').read_text(encoding='utf-8'))
need(len(faiths['religions'])==49 and len(faiths['faiths'])==103,'Authored count mismatch')
need(not faiths['above_total_cap'] and not faiths['above_eminent_cap'],'Authored excess changed')
need(all(all(v is None for v in r['authored_overrides'].values()) for r in faiths['religions']),'Authored Religion overrides changed')
types=json.loads((HERE/'parameter-consumer-census.json').read_text(encoding='utf-8'))
need(types['type_count']==336 and types['block_counts']['parameters']==6,'Type/parameter definition count mismatch')
need(len(contract['conditions'])==7,'Enumerated domain count mismatch')
print(json.dumps({'schema':'ck3-12004-grade-effects-source-package-check-v1','checks':checks,'result':'PASS',
 'machine_id':contract['machine_id'],'proof_layer':'record-structure-source-byte-integrity-and-enumerated-census',
 'semantic_correctness_verified':False,'live_execution_performed':False,
 'native_calls':0,'script_execution_performed':False,'limitations':['No execution of original native consumers','No proof of cache freshness or actual attribute changes','No authorization to launch CK3']}))
