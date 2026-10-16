"""Portable stdlib verification of retained R08 source bytes, not live credit."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,re,struct,zipfile,zlib
def need(ok,msg):
 if not ok:raise ValueError(msg)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def original(record):
 need(record['encoding']in('zlib+base64','base64'),'unsupported original encoding')
 coded=base64.b64decode(record['payload'],validate=True)
 raw=zlib.decompress(coded)if record['encoding']=='zlib+base64'else coded
 need(len(raw)==record['bytes']and digest(raw)==record['sha256'],'original exact bytes changed: '+record['id']);return raw
def target(pc,raw):
 if raw[0]in(0xE8,0xE9):return pc+len(raw)+int.from_bytes(raw[1:],'little',signed=True)
 if raw[0]==0xEB or 0x70<=raw[0]<=0x7F:return pc+len(raw)+int.from_bytes(raw[1:],'little',signed=True)
 if raw[:1]==b'\x0f'and 0x80<=raw[1]<=0x8F:return pc+len(raw)+int.from_bytes(raw[2:],'little',signed=True)
 raise ValueError('unsupported relative edge encoding')
def contiguous(rows,begin,raw):
 cursor=begin
 for pc,code in rows:
  need(pc==cursor and raw[pc-begin:pc-begin+len(code)]==code,'instruction span differs');cursor+=len(code)
 need(cursor==begin+len(raw),'instruction coverage differs')
def verify(path):
 bundle=json.loads(Path(path).read_text(encoding='utf-8'));orig={v['id']:original(v)for v in bundle['originals']};records={k:json.loads(v)for k,v in orig.items()if k!='scalar-archive'}
 image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518';need(bundle['image']['sha256']==image,'exact image differs')
 need(all(v['machine_id']==bundle['source_machine_id']for v in records.values()),'source-machine IDs differ')
 need(records['image-identity']['sha256']==image,'source identity differs')
 caller=records['caller'];gate=records['application-source'];contract=records['application-contract'];scalar=records['scalar'];ae=records['key-ae']
 gateway=bytes.fromhex(bundle['source_bytes']['gateway_28B9950']['hex']);parent=bytes.fromhex(bundle['source_bytes']['parent_tail']['hex']);leaf=bytes.fromhex(bundle['source_bytes']['gate_2BAFF30']['hex']);body=bytes.fromhex(bundle['source_bytes']['scalar_2BD3320']['hex'])
 for key,data in [('gateway_28B9950',gateway),('parent_tail',parent),('gate_2BAFF30',leaf),('scalar_2BD3320',body)]:
  row=bundle['source_bytes'][key];need(len(data)==row['bytes']and digest(data)==row['sha256'],'visible raw hex differs '+key)
 need(gateway.hex()==caller['source_gateway']['complete_raw_hex']and parent.hex()==caller['parent_selected_span']['raw_hex'],'caller original mismatch')
 begin=int(caller['source_gateway']['begin_rva'],16)
 table_offset=int(caller['source_gateway']['jump_table_rva'],16)-begin
 need(table_offset==516 and len(gateway)==540,'table/data extent differs')
 table=struct.unpack('<6I',gateway[table_offset:]);need(list(table)==[int(v,16)for v in caller['source_gateway']['table_targets']],'gateway table differs')
 need(table[4]==0x28B9B29,'selector4 table target differs')
 for row in caller['selected_instructions']:
  pc=int(row['rva'],16);code=bytes.fromhex(row['bytes']);start=int(caller['parent_selected_span']['begin_rva'],16);raw=parent
  if begin<=pc<begin+len(gateway):start=begin;raw=gateway
  need(start<=pc and raw[pc-start:pc-start+len(code)]==code,'caller selected instruction bytes differ')
 need(leaf.hex()==gate['source_hex']and digest(leaf)==contract['source_body_sha256'],'gate original mismatch')
 contiguous([(int(r['rva'],16),bytes.fromhex(r['bytes']))for r in gate['instructions']],0x2BAFF30,leaf)
 calls=[r for r in gate['instructions']if r['mnemonic']=='call'];branches=[r for r in gate['instructions']if r['mnemonic'].startswith('j')]
 need(len(calls)==1 and target(int(calls[0]['rva'],16),bytes.fromhex(calls[0]['bytes']))==0x28C2DF0,'gate helper edge differs')
 need(len(branches)==3 and all(target(int(r['rva'],16),bytes.fromhex(r['bytes']))==0x2BAFF5F for r in branches),'gate false branches differ')
 archive=orig['scalar-archive'];need(digest(archive)==scalar['source_archive_sha256'],'scalar original ZIP differs')
 with zipfile.ZipFile(BytesIO(archive))as z:
  need(set(z.namelist())=={'function.bin','function.asm','source-details.json'},'ZIP members differ')
  need(z.read('function.bin')==body,'scalar raw differs');text=z.read('function.asm').decode('utf-8');detail=json.loads(z.read('source-details.json'))
 rows=[]
 for line in text.splitlines():
  match=re.fullmatch(r'([0-9A-Fa-f]+) ([0-9A-Fa-f]+) (.+)',line);need(match is not None,'malformed scalar asm line');rows.append((int(match[1],16),bytes.fromhex(match[2])))
 need(len(rows)==253 and len(body)==938,'scalar count differs');contiguous(rows,0x2BD3320,body)
 need(len(detail['jumps'])==26 and len(detail['calls'])==8,'scalar edge counts differ')
 for edge in detail['jumps']+detail['calls']:
  pc=int(edge['rva'],16);code=bytes.fromhex(edge['raw']);need(body[pc-0x2BD3320:pc-0x2BD3320+len(code)]==code,'scalar edge byte differs');need(target(pc,code)==int(edge['target'],16),'scalar relative target differs')
 grouped=[int(v,16)for group in scalar['branch_groups']for v in group['rvas']];need(len(grouped)==len(set(grouped))==26 and set(grouped)=={int(v['rva'],16)for v in detail['jumps']},'scalar branch partition differs')
 need(ae['consumer_source']['key_id_decimal']==174 and ae['consumer_source']['key_id_hex']=='AE','AE identity differs')
 need(ae['results']['business_name']is None and ae['results']['cadence']is None,'unclosed AE scope changed')
 for k in('paid_military_amount_raw','cadence'):need(bundle['business'][k]is None,'unclosed business field changed')
 need(bundle['business']['maintenance_attribution']=='unclosed'and bundle['new_live_credit']==0,'runtime scope changed')
 return {'status':'PASS','scope':'retained source byte/instruction/relative-edge/portable-original integrity only','source_machine_id':bundle['source_machine_id'],'image_sha256':image,'originals_verified':len(orig),'gateway_bytes':540,'parent_tail_bytes':len(parent),'scalar_bytes':938,'gate_bytes':54,'scalar_instructions':253,'scalar_branches':26,'gate_false_branches':3,'paid_military_amount_raw':None,'cadence':None,'new_live_credit':0}
def verify_scalar_leaves(path,parent_path):
 b=json.loads(Path(path).read_text(encoding='utf-8'));parent_raw=Path(parent_path).read_bytes();parent=json.loads(parent_raw)
 need(len(parent_raw)==b['parent_bundle']['bytes']and digest(parent_raw)==b['parent_bundle']['sha256'],'frozen parent bundle changed')
 orig={r['id']:original(r)for r in b['originals']};records={k:json.loads(v)for k,v in orig.items()if not k.endswith('-archive')}
 need(set(orig)=={'addend-source','addend-archive','factor-source','factor-semantics','factor-archive'},'scalar original set differs')
 need(all(v['machine_id']==b['machine_id']for v in records.values())and b['machine_id']==parent['source_machine_id'],'scalar source machine differs')
 a=records['addend-source'];f=records['factor-source'];sem=records['factor-semantics'];image=parent['image']['sha256']
 need(a['image']['sha256']==f['image_sha256']==b['image']['sha256']==image,'scalar leaf image differs')
 need(a['frozen_source_commit']==f['frozen_source_commit']==b['source_commit'],'scalar source commit differs')
 need(sem['source_record_sha256']==digest(orig['factor-source']),'factor semantics source changed')
 parent_orig={r['id']:original(r)for r in parent['originals']}
 need(sem['parent_contract_sha256']==digest(parent_orig['scalar'])and sem['parent_archive_sha256']==digest(parent_orig['scalar-archive']),'factor parent source differs')
 parent_body=bytes.fromhex(parent['source_bytes']['scalar_2BD3320']['hex'])
 for pc,destination in((0x2BD35A3,0x2BD2790),(0x2BD3611,0x2BD2510)):
  raw=parent_body[pc-0x2BD3320:pc-0x2BD3320+5];need(raw[:1]==b'\xe8'and target(pc,raw)==destination,'parent scalar call edge differs')
 counts={}
 for id,record,begin,nins,njump,ncall in(('addend',a,0x2BD2790,355,36,34),('factor',f,0x2BD2510,177,19,3)):
  archive=orig[id+'-archive'];need(digest(archive)==record['source_archive_sha256'],'scalar leaf original ZIP differs')
  with zipfile.ZipFile(BytesIO(archive))as z:
   members={'function.bin','function.asm','source-details.json'}if id=='addend'else{'function.bin','function.asm','metadata.json','image-identity.original.json'}
   need(set(z.namelist())==members,'scalar leaf ZIP members differ');body=z.read('function.bin');asm=z.read('function.asm').decode('utf-8');detail=json.loads(z.read('source-details.json'if id=='addend'else'metadata.json'))
   if id=='factor':need(z.read('image-identity.original.json')==parent_orig['image-identity'],'factor exact original identity differs')
  visible=b['source_bytes'][id];need(body==bytes.fromhex(visible['hex'])and len(body)==visible['bytes']==record['function']['bytes']and digest(body)==visible['sha256']==record['function']['sha256'],'scalar leaf full source differs')
  need(begin==int(visible['begin_rva'],16)and begin+len(body)==int(visible['end_rva_exclusive'],16),'scalar leaf boundary differs')
  rows=[]
  for line in asm.splitlines():
   match=re.fullmatch(r'([0-9A-Fa-f]+) ([0-9A-Fa-f]+) (.+)',line);need(match is not None,'malformed scalar leaf ASM');rows.append((int(match[1],16),bytes.fromhex(match[2])))
  need(len(rows)==nins,'scalar leaf instruction count differs');contiguous(rows,begin,body)
  jumps=detail['jumps']if id=='addend'else detail['direct_branches'];calls=detail['calls']if id=='addend'else detail['direct_calls'];need(len(jumps)==njump and len(calls)==ncall,'scalar leaf edge counts differ')
  indirect=0
  for e in jumps+calls:
   pc=int(e['rva'],16);raw=bytes.fromhex(e['raw']if 'raw'in e else e['bytes']);need(body[pc-begin:pc-begin+len(raw)]==raw,'scalar leaf edge byte differs')
   if e['target']is None:need(raw[:1]==b'\xff','nonrelative call encoding differs');indirect+=1
   else:need(target(pc,raw)==int(e['target'],16),'scalar leaf relative target differs')
  if id=='addend':
   groups=[int(v,16)for group in a['branch_groups']for v in group['rvas']];need(len(groups)==len(set(groups))==36 and set(groups)=={int(e['rva'],16)for e in jumps}and indirect==4,'addend branch partition or indirect call count differs')
  else:need(detail==f['function']and indirect==0,'factor metadata differs')
  counts[id]=dict(bytes=len(body),instructions=nins,branches=njump,calls=ncall,indirect_call_targets_unresolved=indirect)
 for k in('paid_military_amount_raw','cadence'):need(b['business'][k]is None,'scalar unresolved business scope changed')
 need(b['business']['maintenance_attribution']=='unclosed'and b['new_live_credit']==0,'scalar live scope changed')
 return dict(status='PASS',scope='two new retained-source leaf combination; byte, instruction, edge and exact-original integrity only',functions=counts,originals_verified=len(orig),source_machine_id=b['machine_id'],paid_military_amount_raw=None,cadence=None,new_live_credit=0)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('sources.json'));p.add_argument('--scalar-leaves',type=Path,default=Path(__file__).with_name('scalar-leaves-a02.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle);result['scalar_leaves']=verify_scalar_leaves(a.scalar_leaves,a.bundle)
 if a.extract_originals:
  need(not a.extract_originals.exists(),'exclusive new original-extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False)
  for input_path in(a.bundle,a.scalar_leaves):
   for record in json.loads(input_path.read_text(encoding='utf-8'))['originals']:
    suffix='.zip'if record['id'].endswith('-archive')else'.json'
    with(a.extract_originals/(record['id']+suffix)).open('xb')as f:f.write(original(record))
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
