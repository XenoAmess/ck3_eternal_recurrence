"""Freeze or verify the clergy-specific final query ABI; files only."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct

from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
EXE = Path('Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe')
MANIFEST = HERE / 'religion_rite_governance12002_clergy_abi.json'
SPANS = [
    ('CanReassign_registration', 0x15CA30, 0x15CB17),
    ('CanReassign_reflection', 0x11616E0, 0x1161756),
    ('CanReassign_final', 0x31B4980, 0x31B4A25),
    ('auto_fill_vacancy', 0x31B4830, 0x31B497C),
    ('compiled_appointment_predicate', 0x31BDEB0, 0x31BE12B),
    ('once_and_time_final', 0x31BD1C0, 0x31BD622),
    ('valid_position_reused', 0x31BCED0, 0x31BCF8C),
    ('valid_character_reused', 0x31BCF90, 0x31BD04C),
]
EDGES = [
    ('registration_callback', 0x15CAC4, 7, 3, 0x11616E0),
    ('reflection_final', 0x1161730, 5, 1, 0x31B4980),
    ('auto_fill_vacancy', 0x31B4990, 5, 1, 0x31B4830),
    ('compiled_can_reassign', 0x31B49E0, 5, 1, 0x31BDEB0),
    ('once_and_time', 0x31B4A06, 5, 1, 0x31BD1C0),
]
STOCK = [
    ('common/council_positions/00_council_positions.txt', [(554,611),(808,828)]),
    ('common/scripted_triggers/00_councillor_triggers.txt', [(1,36),(131,186)]),
    ('common/religion/doctrine_types/20_doctrines.txt', [(1261,1383),(1430,1649)]),
]

def digest(data):
    return hashlib.sha256(data).hexdigest().upper()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze', action='store_true')
    p.add_argument('--exe', type=Path, default=EXE)
    p.add_argument('--artifacts', type=Path, required=True)
    a=p.parse_args(); a.artifacts.mkdir(parents=True, exist_ok=True)
    data=a.exe.read_bytes(); pe=PeImage(data)
    if digest(data)!=SHA:
        raise ValueError('exact executable SHA mismatch')
    game=a.exe.parent.parent/'game'
    if a.freeze:
        rows=[]
        for name,start,end in SPANS:
            off=pe.rva_to_offset(start)
            rows.append(dict(name=name,start_rva=hex(start),end_rva=hex(end),sha256=digest(data[off:off+end-start])))
        stock=[]
        for path,ranges in STOCK:
            raw=(game/path).read_bytes()
            stock.append(dict(path=path,sha256=digest(raw),size=len(raw),ranges=ranges))
            lines=raw.decode('utf-8-sig').splitlines()
            text='\n\n'.join('\n'.join(f'{i}: {lines[i-1]}' for i in range(first,last+1)) for first,last in ranges)
            (a.artifacts/(Path(path).stem+'-clergy.txt')).write_text(text+'\n',encoding='utf-8')
        manifest=dict(schema='xar.ck3.religion-clergy-appointment-abi/v1',game_version='1.20.0.2',executable_sha256=SHA,
                      live_verified=False,spans=rows,edges=[dict(name=n,rva=hex(r),size=s,displacement_offset=d,target=hex(t)) for n,r,s,d,t in EDGES],
                      literal=dict(rva='0x452B7A0',value='CanReassignCouncillor'),stock=stock,
                      reused_council_abi=['council_candidates12002_abi.json','council_gates12002_abi.json'],
                      bindings=dict(valid_position='0x31BCED0',valid_character='0x31BCF90',can_reassign='0x31B4980',court_owner='0x28BFC70'),
                      layouts=dict(owner_landed='0x1C0',owner_task_ids='0x230',owner_task_count='0x23C',task_identity='0x10',task_type='0x18',task_owner='0x44',task_incumbent='0x40',type_position='0x40',position_key='0x18',character_rite='0xB4'))
        MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        from capstone import Cs,CS_ARCH_X86,CS_MODE_64
        cs=Cs(CS_ARCH_X86,CS_MODE_64)
        output=[]
        for name,start,end in SPANS[:6]:
            off=pe.rva_to_offset(start); output.append(name)
            output.extend(f'{i.address:08X} {i.bytes.hex():<28} {i.mnemonic:8} {i.op_str}' for i in cs.disasm(data[off:off+end-start],start))
        (a.artifacts/'native-disassembly.txt').write_text('\n'.join(output)+'\n',encoding='utf-8')
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    for row in m['spans']:
        start,end=int(row['start_rva'],0),int(row['end_rva'],0); off=pe.rva_to_offset(start)
        if digest(data[off:off+end-start])!=row['sha256']:
            raise ValueError(row['name'])
    for row in m['edges']:
        rva=int(row['rva'],0); off=pe.rva_to_offset(rva)
        if rva+row['size']+struct.unpack_from('<i',data,off+row['displacement_offset'])[0]!=int(row['target'],0):
            raise ValueError(row['name'])
    literal=m['literal']; off=pe.rva_to_offset(int(literal['rva'],0)); needle=literal['value'].encode()+b'\0'
    if data[off:off+len(needle)]!=needle:
        raise ValueError('CanReassign reflection literal')
    for row in m['stock']:
        raw=(game/row['path']).read_bytes()
        if digest(raw)!=row['sha256'] or len(raw)!=row['size']:
            raise ValueError(row['path'])
    header=(HERE.parent/'include/xar_bridge/religion_rite_governance12002_clergy.hpp').read_text(encoding='utf-8')
    names=dict(valid_position='kValidPositionRva',valid_character='kValidCharacterRva',
               can_reassign='kCanReassignRva',court_owner='kCourtOwnerRva')
    layouts=dict(owner_landed='kLandedOffset',owner_task_ids='kTaskIdsOffset',owner_task_count='kTaskCountOffset',
                 task_identity='kTaskIdentityOffset',task_type='kTaskTypeOffset',task_owner='kTaskOwnerOffset',
                 task_incumbent='kTaskIncumbentOffset',type_position='kTypePositionOffset',
                 position_key='kPositionKeyOffset',character_rite='kCharacterRiteOffset')
    for values,expected in [(m['bindings'],names),(m['layouts'],layouts)]:
        for key,name in expected.items():
            match=re.search(rf'{name}\s*=\s*(0x[0-9A-Fa-f]+)',header)
            if match is None or int(match[1],0)!=int(values[key],0):
                raise ValueError(name)
    result=dict(status='GREEN',exe_sha256=SHA,code_spans=len(m['spans']),relative_edges=len(m['edges']),stock_files=len(m['stock']),literal_checks=1,
                production_constants=len(names)+len(layouts),manifest_sha256=digest(MANIFEST.read_bytes()),live_verified=False)
    (a.artifacts/'abi-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    main()
