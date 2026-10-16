"""Portable metadata preflight and content-bound interruption identity."""
from pathlib import Path
import hashlib
import json

def require_published_full(sequence, *, inbox, read):
    if type(sequence) is not int or sequence <= 4:
        raise ValueError('reviewed later FULL control sequence required')
    path=Path(inbox)/f'{sequence:04d}-1-result.json'
    if not path.is_file():
        raise ValueError('publish the actual first FULL before continuity attachment')
    request=read(path)
    maximum=(request.get('arguments') or {}).get('max_turns')
    if (request.get('sequence')!=sequence or request.get('command')!='full_loop'
        or 'tool' in request or type(maximum) is not int or not 1<=maximum<=30):
        raise ValueError('first request must be the exact ordinary bounded FULL')
    return request

def interruption_evidence_id(*, source, source_pins, reason, frame, completed_cycles):
    value={'source':str(source),'source_pins':source_pins,'reason':str(reason)[:2048],
           'frame':frame,'completed_cycles':completed_cycles}
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
    return 'manual-repair:'+hashlib.sha256(raw).hexdigest()
