"""Stdlib verifier for retained byte cuts, not a rehash of the large wire."""
from pathlib import Path
import argparse,hashlib,json
def verify(root):
    root=Path(root)
    facts=json.loads((root/'ACTUAL-TINY-FACTS.json').read_bytes())
    results=[]
    for item in facts['queries']:
        values={}
        for key in ('request','response_prefix_file'):
            ref=item[key];raw=(root/ref['relative_path']).read_bytes()
            if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('Retained tiny cut changed')
            values[key]=raw
        message=json.loads(values['request'])['message']
        if message['request_id']!=item['native_request_id'] or message['step']!='query-army-strengths-v1' or message['army_ids']!=[0] or message['army_strengths_profile']!='observed_history_full_v1':raise ValueError('Actual native request scope/profile changed')
        literal=item['literal'].encode();prefix=values['response_prefix_file']
        if prefix.count(literal)!=1 or item['field_absolute_offset']!=item['original_response_prefix_byte_begin']+prefix.index(literal):raise ValueError('Exact raw null literal/offset changed')
        if item['native_request_id'].encode() not in prefix:raise ValueError('Response prefix belongs to another request')
        results.append(dict(query_sequence=item['query_sequence'],field_state='explicit_null',profile=message['army_strengths_profile'],army_ids=message['army_ids']))
    return dict(status='PASS_TINY_NATIVE_NULL_CUTS',queries=results,whole_response_rehashed=False,SDK_calls=0)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,default=Path(__file__).resolve().parent)
    print(json.dumps(verify(p.parse_args().evidence_root)))
