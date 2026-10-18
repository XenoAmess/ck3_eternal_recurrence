"""Verify retained source bytes and exact join frontier; no game or debugger access."""
from pathlib import Path
import hashlib
import json

def need(ok, why):
    if not ok:
        raise ValueError(why)

def verify(facts):
    bodies=facts['retained_bodies']
    for name,body in bodies.items():
        raw=bytes.fromhex(body['raw_hex'])
        need(len(raw)==body['bytes'] and hashlib.sha256(raw).hexdigest()==body['sha256'], 'Saved bytes differ: '+name)
    for row in facts['opcode_edges']:
        body=bodies[row['body']]
        offset=row['rva']-body['begin_rva']
        raw=bytes.fromhex(body['raw_hex'])
        op=bytes.fromhex(row['bytes_hex'])
        need(offset>=0 and raw[offset:offset+len(op)]==op, 'Opcode edge differs: '+hex(row['rva']))
        if 'relative_call_target' in row:
            need(op[0]==0xE8 and len(op)==5 and row['rva']+5+int.from_bytes(op[1:],'little',signed=True)==row['relative_call_target'], 'Direct call target differs')
    gate=facts['a07_actual_compiled_source']
    need(gate['frozen_source_pin']['bytes']==23688 and gate['frozen_source_pin']['sha256']=='24b9d584ee451ef822c6386484efcda2578072cb5569ce1740b910e3bbadd0ee', 'Not the qualified a07 source')
    need('x.episode.empty()' in gate['parser_line'] and 'return 2;' in gate['parser_line'], 'Original nonempty episode gate missing')
    need('full_window_all_writes_covered\\\":false' in gate['terminal_line'], 'Partial coverage boundary changed')
    need(facts['actual_c_d_writer_pc'] is None and facts['same_NET_invocation_qualified'] is False and facts['maintenance_paid_qualified'] is False, 'Source frontier was promoted')
    return {'status':'PASS_RETAINED_OPCODE_AND_REAL_A07_FRONTIER','bodies':len(bodies),'opcode_edges':len(facts['opcode_edges']),'SDK_calls':0,'debugger_started':False,'live_or_paid_credit':False}

if __name__=='__main__':
    print(json.dumps(verify(json.loads((Path(__file__).resolve().parent/'SOURCE-FRONTIER.json').read_bytes())),indent=2))
