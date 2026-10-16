"""Offline stdlib saved-cost source verification; no EXE/native access."""
import argparse,datetime as dt,hashlib,json,struct,zipfile
from pathlib import Path,PurePosixPath
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def run(root):
 manifest=json.loads((root/'MANIFEST.json').read_bytes())
 need(sha((root/manifest['verifier']['path']).read_bytes())==manifest['verifier']['sha256'],'Verifierpin')
 archive=root/manifest['archive']['path'];need(sha(archive.read_bytes())==manifest['archive']['sha256'],'ArchiveSHA')
 with zipfile.ZipFile(archive) as z:
  names=z.namelist();need(len(names)==len(set(names)),'Duplicatemembers')
  expected={r['path']:r for r in manifest['members']};need(set(names)==set(expected),'Exactmemberinventory')
  payload={}
  for name in names:
   q=PurePosixPath(name);need(not q.is_absolute() and '..' not in q.parts and '\\' not in name,'Unsafemember')
   b=z.read(name);p=expected[name];need(len(b)==p['bytes'] and sha(b)==p['sha256'],'Memberpin:'+name);payload[name]=b
 raw=payload['actual-function.bin'];asm=payload['actual-function.asm'].decode('utf-8')
 contract=json.loads(payload['SOURCE-CONTRACT.actual.json']);branches=json.loads(payload['BRANCHES.actual.json']);receipt=json.loads(payload['READ-RECEIPT.actual.json'])
 need((root/'SOURCE-CONTRACT.actual.json').read_bytes()==payload['SOURCE-CONTRACT.actual.json'],'Externalcontractmatchesarchive')
 begin=0x262BE10;end=0x262C0A4;cursor=begin;ins={}
 for line in asm.splitlines():
  pc=int(line[:8],16);b=bytes.fromhex(line[10:54].strip());parts=line[55:].split(None,1)
  need(pc==cursor and b and raw[pc-begin:pc-begin+len(b)]==b,'Continuousinstructionbytes')
  ins[pc]=(b,parts[0],parts[1] if len(parts)>1 else '');cursor+=len(b)
 need(cursor==end and len(raw)==660 and len(ins)==171,'Exactcompletebody')
 need(sum(m.startswith('j') for b,m,o in ins.values())==32,'All32jumpslisted')
 need(sum(m=='call' for b,m,o in ins.values())==9,'All9CALLslisted')
 def target(pc,b):
  if b[0] in (0xE8,0xE9):return pc+5+struct.unpack('<i',b[1:5])[0]
  if b[0]==0xEB or 0x70<=b[0]<=0x7F:return pc+2+struct.unpack('<b',b[1:2])[0]
  if b[0]==0x0F and 0x80<=b[1]<=0x8F:return pc+6+struct.unpack('<i',b[2:6])[0]
  raise ValueError('Unsupportedactualcontrolencoding')
 pcs=[]
 for row in branches['branches']:
  pc=row['at_rva'];b,m,o=ins[pc];need(b.hex()==row['bytes'] and m==row['mnemonic'],'Branchbytes')
  t=target(pc,b);need(t==row['target_rva'] and t in ins and row['internal'] is True,'Closedbranchtarget');pcs.append(pc)
 need(len(pcs)==len(set(pcs))==32,'32uniquebranches')
 for row in branches['external_calls']:
  pc=row['at_rva'];b,m,o=ins[pc];need(m=='call' and b.hex()==row['bytes'] and target(pc,b)==row['target_rva'],'ActualCALLtarget')
 need(sum(row['target_rva']==begin for row in branches['external_calls'])==2,'Exactly2selfrecursivecalls')
 declared=[int(x['branch_rva'],16) for x in contract['branch_contracts']]
 need(len(declared)==len(set(declared))==32 and set(declared)==set(pcs),'Everybranchcontractonce')
 critical={0x262BE25:'450fb6f1',0x262BE29:'410fb6e8',0x262BE33:'83b93801000000',0x262BE3C:'0f57c0',0x262BE3F:'0f1102',0x262BE42:'0f114210',0x262BE46:'0f114220',0x262BE4A:'0f114230',0x262BE4E:'0f114240',0x262BF85:'41b002',0x262BF9C:'41b001',0x262BFD2:'48638728010000',0x262BFD9:'4c69c8a0860100',0x262C089:'488bc3'}
 for pc,expected in critical.items():need(ins[pc][0].hex()==expected,'Criticalselectedbytes')
 upstream=json.loads(payload['UPSTREAM-CALLS.actual.json'])['calls'];need(len(upstream)==6,'6upstreamcalls')
 for row in upstream:
  line=next(line for line in row['literal_instructions'] if int(line[:8],16)==int(row['call_rva'],16))
  b=bytes.fromhex(line[10:54].strip());need(b[0]==0xE8 and target(int(row['call_rva'],16),b)==begin,'UpstreamactualCALL')
 need(receipt['function']['sha256']==sha(raw) and receipt['function']['chained_runtime_function'] is None,'Readreceiptidentity')
 need(receipt['new_EXE_code_bytes']==660 and receipt['new_EXE_metadata_bytes']==220 and receipt['new_EXE_read_calls']==20,'Finitebudget')
 need(receipt['callee_reads']==0 and receipt['whole_EXE_hashes']==0 and receipt['global_scans']==0,'Noexternalfollow/globalread')
 need(contract['maintenance_attribution']=='unclosed' and contract['direct_secondary_context_28_30_relation'] is None,'Noinventedpaidmapping')
 return dict(result='SAVED_COST_SOURCE_BYTES_AND_STRUCTURE_VERIFIED',archive_sha256=sha(archive.read_bytes()),source_bytes=660,instructions=171,branches=32,call_instructions=9,self_recursive_calls=2,upstream_calls=6,checked_members=len(payload),semantic_correctness_automatically_proven=False,new_EXE_reads=0,new_runtime_actions=0,maintenance_attribution='unclosed',limits='Hashes/coverage/relativecontroltargets/declaredcontractsverified; manualsemantics andpaidcausalitynotautomaticallyproved. Historicalabsolutepathsnotfollowed.')
def main():
 p=argparse.ArgumentParser();p.add_argument('--machine-id',required=True);p.add_argument('--output',type=Path);a=p.parse_args()
 result=run(Path(__file__).resolve().parent);result.update(machine_id=a.machine_id,observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
 if a.output:
  with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result))
if __name__=='__main__':main()
