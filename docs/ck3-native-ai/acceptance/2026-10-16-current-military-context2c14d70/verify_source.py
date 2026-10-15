"""Offline stdlib replay of saved source bytes/structure; no EXE or native calls."""
import argparse,datetime as dt,hashlib,json,struct,zipfile
from pathlib import Path,PurePosixPath
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def run(root):
 manifest=json.loads((root/'MANIFEST.json').read_bytes())
 need(sha((root/manifest['verifier']['path']).read_bytes())==manifest['verifier']['sha256'],'Verifierpin')
 archive=root/manifest['archive']['path']
 need(sha(archive.read_bytes())==manifest['archive']['sha256'],'ArchiveSHA')
 with zipfile.ZipFile(archive) as z:
  names=z.namelist();need(len(names)==len(set(names)),'Duplicatemembers')
  expected={r['path']:r for r in manifest['members']}
  need(set(names)==set(expected),'Exactmemberinventory')
  payload={}
  for name in names:
   q=PurePosixPath(name)
   need(not q.is_absolute() and '..' not in q.parts and '\\' not in name,'Unsafemember')
   b=z.read(name);pin=expected[name]
   need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'Memberpin:'+name)
   payload[name]=b
 raw=payload['actual-function.bin'];asm=payload['actual-function.asm'].decode('utf-8')
 contract=json.loads(payload['SOURCE-CONTRACT.actual.json'])
 branches=json.loads(payload['BRANCHES.actual.json'])
 receipt=json.loads(payload['READ-RECEIPT.actual.json'])
 need((root/'SOURCE-CONTRACT.actual.json').read_bytes()==payload['SOURCE-CONTRACT.actual.json'],'Externalcontractmatchesarchivedcontract')
 begin=0x2C14D70;end=0x2C14FD5;cursor=begin;instructions={}
 for line in asm.splitlines():
  pc=int(line[:8],16);b=bytes.fromhex(line[10:54].strip());parts=line[55:].split(None,1)
  need(pc==cursor and b and raw[pc-begin:pc-begin+len(b)]==b,'Continuousinstructionbytes')
  instructions[pc]=(b,parts[0],parts[1] if len(parts)>1 else '')
  cursor+=len(b)
 need(cursor==end and len(raw)==613 and len(instructions)==155,'Exactcompletebody')
 need(sum(m.startswith('j') for b,m,o in instructions.values())==13,'Allactualjumpinstructionslisted')
 need(sum(m=='call' for b,m,o in instructions.values())==5,'AllactualCALLinstructionslisted')
 def target(pc,b):
  if b[0] in (0xE8,0xE9):return pc+5+struct.unpack('<i',b[1:5])[0]
  if b[0]==0xEB or 0x70<=b[0]<=0x7F:return pc+2+struct.unpack('<b',b[1:2])[0]
  if b[0]==0x0F and 0x80<=b[1]<=0x8F:return pc+6+struct.unpack('<i',b[2:6])[0]
  raise ValueError('Unsupportedactualcontrolencoding')
 branch_pcs=[]
 for row in branches['branches']:
  pc=row['at_rva'];b,mnemonic,operands=instructions[pc]
  need(b.hex()==row['bytes'] and mnemonic==row['mnemonic'],'Branchbytes/mnemonic')
  t=target(pc,b);need(t==row['target_rva'] and t in instructions and row['internal'] is True,'Closedbranchtarget')
  branch_pcs.append(pc)
 need(len(branch_pcs)==len(set(branch_pcs))==13,'Exact13branches')
 for row in branches['external_calls']:
  pc=row['at_rva'];b,mnemonic,operands=instructions[pc]
  need(mnemonic=='call' and b.hex()==row['bytes'] and target(pc,b)==row['target_rva'],'ActualCALLtarget')
 need(len(branches['external_calls'])==5,'Exact5CALLs')
 declared=[int(x['branch_rva'],16) for x in contract['branch_contracts']]
 need(len(declared)==len(set(declared))==13 and set(declared)==set(branch_pcs),'Everybranchcontractonce')
 for pc,expected in [(0x2C14D82,'837a28ff'),(0x2C14D92,'803900'),(0x2C14D9E,'e87d81a1ff'),(0x2C14DB2,'e82979a1ff'),(0x2C14F78,'480111'),(0x2C14F9F,'48014128'),(0x2C14FA7,'48014130')]:
  need(instructions[pc][0].hex()==expected,'Criticalselectedbytes')
 need(receipt['function']['sha256']==sha(raw) and receipt['function']['chained_runtime_function'] is None,'Readreceiptbodyidentity')
 need(receipt['new_EXE_code_bytes']==613 and receipt['new_EXE_metadata_bytes']==220 and receipt['new_EXE_read_calls']==20,'Finitebudgetreceipt')
 need(receipt['callee_reads']==0 and receipt['whole_EXE_hashes']==0 and receipt['global_scans']==0,'Nocallee/globalread')
 need(contract['maintenance_attribution']=='unclosed' and contract['direct_secondary_context_28_30_relation'] is None,'No inventedpaidmapping')
 return dict(result='SAVED_SOURCE_BYTES_AND_BRANCH_STRUCTURE_VERIFIED',archive_sha256=sha(archive.read_bytes()),source_bytes=613,instructions=155,branches=13,call_instructions=5,checked_members=len(payload),semantic_correctness_automatically_proven=False,new_EXE_reads=0,new_runtime_actions=0,maintenance_attribution='unclosed',limits='Hashes/coverage/branchtargets verified; manualsemanticcontract isnot provedbythisverifier. Originalabsolutepathsarehistoricalonly.')
def main():
 p=argparse.ArgumentParser();p.add_argument('--machine-id',required=True);p.add_argument('--output',type=Path)
 a=p.parse_args();result=run(Path(__file__).resolve().parent)
 result.update(machine_id=a.machine_id,observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
 if a.output:
  with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result))
if __name__=='__main__':main()
