"""Strict reader for owned synthetic debugger receipts. It cannot grant CK3 evidence."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import struct

class Rejected(ValueError):
    pass

def require(condition, label):
    if not condition:
        raise Rejected(label)

def consume(case: Path) -> dict:
    raw_path=case/'observer.raw.ndjson'
    raw=raw_path.read_bytes()
    result=json.loads((case/'RESULT.actual.json').read_text(encoding='utf-8'))
    meta=dict(line.split('=',1) for line in (case/'target.meta.txt').read_text().splitlines())
    sites=json.loads((case/'owned-site-bytes.actual.json').read_text())
    rows=[json.loads(line) for line in raw.decode('utf-8').splitlines()]
    def one(kind):
        found=[row for row in rows if row.get('kind')==kind]
        require(len(found)==1,'exactly one '+kind)
        return found[0]
    start=one('start');pair=one('physical_ADD_pair');terminal=one('terminal')
    shared_v3=start.get('schema')=='xar.ck3.refill_ADD_12004.shared_probe_cold.v1'
    if result.get('shared_production_probe_v3') is True:
        require(shared_v3,'shared production Probe source schema')
    guard=one('fixture_mismatch_guard');budget=one('fixture_debug_budget')
    require(result['status']=='PASS' and result['synthetic'] is True,'actual cold run result')
    require(hashlib.sha256(raw).hexdigest()==result['raw_sha256'],'immutable native raw bytes')
    require(start['fixture'] is True and pair['fixture'] is True,'fixture source kind')
    require(pair['CK3_actual_ADD_observed'] is False and result['CK3_actual_ADD_observed'] is False,
            'synthetic receipt must never grant CK3 evidence')
    require(start['pid']==int(meta['pid']) and start['process_created_filetime']==int(meta['created']),
            'process generation')
    require(start['machine_id']==result['machine_id']==sites['machine_id'],'machine identity')
    require(sites['CK3_binary_read'] is False and sites['pid']==start['pid'],'owned synthetic read')
    expected=('0150f4','8b48f43b48f0')
    for i,site in enumerate(sites['sites']):
        b=bytes.fromhex(site['hex'])
        require(site['synthetic_site_address']==int(meta[f'site{i}']) and site['hex']==expected[i],
                'exact synthetic instruction bytes')
        require(len(b)==site['bytes'] and hashlib.sha256(b).hexdigest()==site['sha256'],'site byte hash')
    hit=[row for row in rows if row.get('kind')=='raw_ADD_boundary']
    require(len(hit)==2,'exactly two retained boundaries')
    a,b=hit
    identity=('pid','thread_id','regi_pointer','regi_full_id_u32','physical_slot','rax_anchor','rsp',
      'manager_iterator','q_index','q_u32','q_i32','maximum_u32','arrg_raw','arrg_resolved',
      'arrg_pointer','army_raw','army_resolved','data_count','DATA')
    require(all(a[k]==b[k] for k in identity),'same physical occurrence')
    require(a['pid']==start['pid'] and a['thread_id']==int(meta['tid']) and
      a['regi_full_id_u32']==int(meta['regiment']) and a['physical_slot']==int(meta['slot']),'selected full identities')
    for i,h in enumerate(hit):
        require(h['machine_id']==start['machine_id'] and h['event_ordinal']==i+1,'raw event identity/order')
        require(int(h['synthetic_site_address'],0)==int(meta[f'site{i}']),'actual synthetic pre/post address')
        require(h['physical_complete'] is True and h['associated_ArRg_DATA_complete'] is True,'complete physical and DATA')
        require(h['native_core_token'] is None and h['natural_parent_token'] is None and
          h['natural_attribution_ready'] is False,'no fabricated natural parent')
        require(h['q_i32']==struct.unpack('<i',struct.pack('<I',h['q_u32']))[0],'signed q bits')
        require(int(h['rax_anchor'],0)==int(h['regi_pointer'],0)+0x28+h['physical_slot']*0x24,'physical slot arithmetic')
        require(h['arrg_raw']==h['arrg_resolved']!=0 and h['army_raw']==h['army_resolved']!=0,'full ArRg/Army identity')
        require(h['data_count']==len(h['DATA'])==2,'two retained DATA aliases')
        require([r['stored_index'] for r in h['DATA']]==[0,1],'stored DATA order')
        require(all(r['persistent_full_id_u32']==h['regi_full_id_u32'] and
          r['physical_ordinal_u32']==h['physical_slot'] for r in h['DATA']),'alias identity')
    stack_q_source=None
    if shared_v3:
        windows=[]
        for h in hit:
            require('site_rva' not in h and h.get('stack_q_source_complete') is True,'cold-only site and actual q source')
            window=h.get('stack_q_window_28_hex')
            require(type(window) is str and len(window)==56 and all(c in '0123456789abcdef' for c in window),'exact28B q window')
            require(type(h['q_index']) is int and 0<=h['q_index']<7,'bounded q-index')
            require(struct.unpack_from('<I',bytes.fromhex(window),4*h['q_index'])[0]==h['q_u32'],'q slot equals EDX')
            windows.append(window)
        require(windows[0]==windows[1],'unchanged stack q pair')
        stack_q_source={'status':'available','q_index':a['q_index'],'before_hex':windows[0],'after_hex':windows[1]}
    require(a['qpc']<b['qpc'],'strict native QPC ordering')
    before=bytes.fromhex(a['physical_seven_hex']);after=bytes.fromhex(b['physical_seven_hex'])
    require(len(before)==len(after)==7*0x24,'complete seven physical slots')
    offset=a['physical_slot']*0x24+4
    for h,physical in ((a,before),(b,after)):
        require(struct.unpack_from('<I',physical,offset)[0]==h['current_u32'],'raw current DWORD')
        require(struct.unpack_from('<I',physical,offset-4)[0]==h['maximum_u32'],'raw maximum DWORD')
    require(before[:offset]==after[:offset] and before[offset+4:]==after[offset+4:],
            'one current DWORD may change')
    require(((a['current_u32']+a['q_u32'])&0xffffffff)==b['current_u32'],'DWORD modular ADD')
    require(pair['synthetic_instruction_ADD_observed'] is True and pair['native_instruction_replayed_by_probe'] is False,
            'CPU executes original ADD')
    require(pair['q_i32']==a['q_i32'] and pair['before_current_u32']==a['current_u32'] and
      pair['after_current_u32']==b['current_u32'] and pair['DWORD_wrap_matches'] is True and
      pair['associated_DATA_pair_complete'] is True,'native paired receipt agrees')
    require(terminal=={'kind':'terminal','status':'paired','reason':'paired',
      'debug_registers_cleared':True,'detached':True,'hit_count':2},'actual clean detach')
    require(result['debug_register_audit']['exact_equal'] is True and
      result['debug_register_audit']['initial']==result['debug_register_audit']['after'],'independent debug register readback')
    require(guard['derived_from_actual_owned_hits'] is True and
      guard['cross_tid_q_pointer_current_all_refused'] is True,'native mismatch guards')
    require(budget['debug_hits']==2,'no unrelated selected-TID traps')
    require(result['target_result']['main_ADD_execution_count']==1,'independent original ADD once counter')
    require(result['target_result']['before_u32']==a['current_u32'] and
      result['target_result']['q_u32']==a['q_u32'] and result['target_result']['after_u32']==b['current_u32'],
            'independent target endpoint')
    return {'schema':'xar.refill_ADD.synthetic_strict_item.v1','source_kind':'controlled_synthetic_ADD',
      'machine_id':start['machine_id'],'observed_at_utc':result['observed_at_utc'],
      'consumer_observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'raw_path':str(raw_path),'raw_sha256':hashlib.sha256(raw).hexdigest(),
      'pid':start['pid'],'process_created_filetime':start['process_created_filetime'],
      'thread_id':a['thread_id'],'regi_full_id_u32':a['regi_full_id_u32'],
      'arrg_full_id_u32':a['arrg_resolved'],'army_full_id_u32':a['army_resolved'],
      'physical_slot':a['physical_slot'],'before_u32':a['current_u32'],'after_u32':b['current_u32'],
      'q_u32':a['q_u32'],'q_i32':a['q_i32'],'applied_i32':a['q_i32'],
      'DWORD_wrap_matches':True,'DATA_alias_count':2,'synthetic_instruction_ADD_observed':True,
      'original_ADD_execution_count':1,'clean_detach_and_register_restore':True,
      'CK3_actual_ADD_observed':False,'natural_parent_token':None,'full_window_coverage_ready':False,
      'refill_business_qualification_granted':False,'shared_production_probe_v3':shared_v3,'stack_q_source_v3':stack_q_source}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    item=consume(args.case)
    with args.output.open('x',encoding='utf-8') as out:
        json.dump(item,out,indent=2);out.write('\n')
    print(json.dumps(item))
