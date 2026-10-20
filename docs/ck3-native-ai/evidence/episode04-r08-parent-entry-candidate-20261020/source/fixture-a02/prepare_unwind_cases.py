"""Future own-project-EXE instruction-boundary input; never reads CK3.

Run only after its exact new SYSTEM receipt. This file is prepared source; it
has not been run against a built candidate. It reuses manifest SHA provenance,
double-stats the same open image and reads bounded headers/two function spans.
"""
import argparse,datetime,hashlib,json,os,re,struct
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def write_new(path,data):
 with path.open('xb') as f:f.write(data)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('exe','manifest','description','output','receipt','build-root'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build_root.resolve();exe=a.exe.resolve()
 assert exe==build/'parent_entry_opportunity_cold.exe'
 for out in (a.output,a.receipt):assert out.resolve().is_relative_to(build) and not out.exists()
 manifest_raw=a.manifest.read_bytes();manifest=json.loads(manifest_raw)
 entries=[x for x in manifest['files'] if Path(x['path']).resolve()==exe]
 assert len(entries)==1
 description_raw=a.description.read_bytes();description=json.loads(description_raw)
 from capstone import Cs,CS_ARCH_X86,CS_MODE_64
 decoder=Cs(CS_ARCH_X86,CS_MODE_64)
 cases=[];spans=[];reads=0
 with exe.open('rb') as f:
  before=os.fstat(f.fileno());assert before.st_size==entries[0]['size']
  def read(offset,size):
   nonlocal reads
   assert 0<=offset<=before.st_size-size and size<=8192
   reads+=1;assert reads<=16
   f.seek(offset);data=f.read(size);assert len(data)==size;return data
  dos=read(0,64);assert dos[:2]==b'MZ'
  pe=struct.unpack_from('<I',dos,0x3c)[0];assert pe<=0x100000
  file=read(pe,24);assert file[:4]==b'PE\0\0'
  sections=struct.unpack_from('<H',file,6)[0];optional_size=struct.unpack_from('<H',file,20)[0]
  assert 0<sections<=64 and 0<optional_size<=1024
  optional=read(pe+24,optional_size);assert optional[:2]==b'\x0b\x02'
  table=read(pe+24+optional_size,40*sections)
  def offset(rva,size):
   matches=[]
   for i in range(sections):
    row=table[i*40:(i+1)*40];va,raw_size,raw=struct.unpack_from('<III',row,12)
    if va<=rva and rva+size<=va+raw_size:matches.append(raw+rva-va)
   assert len(matches)==1;return matches[0]
  for key,kind in (('thunk','T'),('prefix','P')):
   item=description[key];rva=item['rva'];size=item['bytes'];assert 0<size<=8192
   raw=read(offset(rva,size),size);decoded=list(decoder.disasm(raw,rva))
   assert decoded and sum(x.size for x in decoded)==size
   assert decoded[0].address==rva
   if kind=='P':assert raw[:16].hex()=='488bc453554881ec980000004c8970e0' and raw[-4:].hex()=='ff642408'
   else:assert decoded[-1].bytes[:2]==b'\xff\x25'
   delta=0;frame=0
   for ins in decoded:
    cases.append(f'{kind} {ins.address-rva:x} {delta} {frame}\n')
    op=ins.op_str.replace(' ','').lower();mn=ins.mnemonic
    if mn in ('push','pushfq'):delta-=8
    elif mn=='popfq':delta+=8
    elif mn=='pop':
     delta+=8
     if op=='rbp':frame=0
    elif mn=='sub' and op=='rsp,0x98':delta-=0x98
    elif mn=='lea':
     if op=='rsp,[rsp-0x40]':delta-=0x40
     elif op=='rbp,[rsp]':frame=1
     elif op=='rsp,[rbp+0x40]':delta=-0x10
     elif op.startswith('rsp,') or op.startswith('rbp,'):raise AssertionError('Unmodelled frame instruction '+op)
    elif mn in ('add','mov') and op.startswith('rsp,'):raise AssertionError('Unmodelled stack write '+op)
   spans.append({'function':key,'rva':rva,'file_offset':offset(rva,size),'bytes':size,
     'sha256':sha(raw),'instruction_count':len(decoded),'last_instruction_hex':bytes(decoded[-1].bytes).hex()})
  after=os.fstat(f.fileno())
 assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
 instruction_count=len(cases)
 header=f"COUNTS T {spans[0]['instruction_count']} {spans[0]['bytes']} P {spans[1]['instruction_count']} {spans[1]['bytes']}\n"
 data=(header+''.join(cases)).encode('ascii');assert len(data)<=32768
 receipt={'schema':'xar.parent-entry.own-fixture-unwind-boundaries.v1',
  'machine_id':'desktop-3fevhd2-1c74096080','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'EXE':str(exe),'manifest_sha256':sha(manifest_raw),'registered_EXE_sha256':entries[0]['sha256'],
  'description_sha256':sha(description_raw),'stat_identity':{'dev':before.st_dev,'ino':before.st_ino,'size':before.st_size,'mtime_ns':before.st_mtime_ns},
  'full_EXE_hashes':0,'game_EXE_reads':0,'bounded_reads':reads,'spans':spans,
  'case_file':{'path':str(a.output),'bytes':len(data),'sha256':sha(data),'instruction_boundaries':instruction_count},
  'actual_RtlVirtualUnwind_pass':False,'case_file_is_native_qualification':False}
 write_new(a.output,data);write_new(a.receipt,(json.dumps(receipt,indent=2)+'\n').encode())
 print(json.dumps(receipt))
if __name__=='__main__':main()
