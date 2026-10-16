"""Saved exact-source integrity/alias checks only; no game, EXE or old C: input."""
from pathlib import Path
import argparse,hashlib,json,struct

def need(ok,message):
    if not ok: raise ValueError(message)

def verify(path):
    j=json.loads(Path(path).read_bytes());g=j['getter'];w=j['writers'];s=j['semantics']
    need(j['schema']=='xar.r08.raw-selector4-wallet-getter-link.v1','schema')
    need(j['image_sha256']=='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518','exact image')
    raw=bytes.fromhex(g['raw_hex'])
    need(len(raw)==256 and hashlib.sha256(raw).hexdigest()==g['sha256']=='a321c1283d0c8348674bb0fd9dca7598507d909fbba956c147917a67fe315557','held mixed source')
    need(g['code_bytes']==232 and g['table_bytes']==24 and raw[231]==0xc3,'code/data boundary')
    targets=list(struct.unpack('<6I',raw[232:]));need(targets==[0x28B94CB,0x28B9569,0x28B9569,0x28B94DD,0x28B954B,0x28B9569],'six raw cases')
    def instruction(pc,expected):
        at=pc-0x28B9490;b=bytes.fromhex(expected);need(raw[at:at+len(b)]==b,'getter instruction '+hex(pc))
    instruction(0x28B9494,'4c8b91b0010000')
    instruction(0x28B954B,'488b82c0010000')
    instruction(0x28B9557,'488b80a0040000')
    instruction(0x28B955E,'498901')
    instruction(0x28B9569,'49c70100000000')
    for item,pc,expected in [(w['gateway'],0x28B9B3C,'482998a0040000'),(w['parent_tail'],0x28F7C66,'480198a0040000')]:
        body=bytes.fromhex(item['hex']);need(hashlib.sha256(body).hexdigest()==item['sha256'],'writer source hash')
        at=pc-int(item['begin_rva'],16);want=bytes.fromhex(expected);need(body[at:at+len(want)]==want,'physical writer displacement')
    incoming=j['incoming'];prefix=bytes.fromhex(incoming['captured_prefix_hex'])
    need(hashlib.sha256(prefix).hexdigest()==incoming['sha256'],'caller prefix hash')
    need(prefix[0x1f:0x24]==bytes.fromhex('e86ceeceff'),'real CALL bytes')
    need(0x2BCA624+int.from_bytes(prefix[0x20:0x24],'little',signed=True)==0x28B9490,'real CALL target')
    need(incoming['passes_only_rawselectors']==[0,3] and incoming['raw4_actual_incoming_observed'] is False,'incoming scope')
    need(s['selector4_authoritative_business_name'] is None and s['selector4_GetCurrency_registration_confirmed'] is False,'formal name unsupported')
    need(all(s[k] is None for k in ['paid_military_amount_raw','payer','cadence']) and s['new_live_credit']==0,'paid/cadence unsupported')
    need(j['new_EXE_reads']=={'code':0,'metadata':0,'whole_hashes':0,'scans':0},'source reuse scope')
    return {'status':'PASS','scope':'saved-source-bytes/table/physical-alias-and-claim-boundaries','source_bytes':256,'code_bytes':232,'table_bytes':24,'actual_raw4_incoming_proven':False,'formal_resource_name':None,'paid_military_amount_raw':None,'cadence':None,'semantic_correctness_automatically_verified':False,'game_or_EXE_access':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=Path(__file__).with_name('source.json'));a=p.parse_args();print(json.dumps(verify(a.source),sort_keys=True))
