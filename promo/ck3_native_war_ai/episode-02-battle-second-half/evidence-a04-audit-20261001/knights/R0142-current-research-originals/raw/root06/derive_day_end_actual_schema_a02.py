from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
src=ROOT/'preserve_actual_day_end_trace_red_a01.py';dst=ROOT/'preserve_actual_day_end_trace_red_a02.py'
data=src.read_bytes();old=b"d['body']['accepted'] is True";new=b"d['body']['progress_status']=='postcondition' and d['body']['starting_date_raw']==cfg['before_date_raw'] and d['body']['elapsed_days']==1 and d['body']['requested_horizon_days']==1"
assert data.count(old)==1
with dst.open('xb') as stream:stream.write(data.replace(old,new))
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT/'actual-day-end-schema-derivation-a02.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump({'original':ident(src),'derived':ident(dst),'actual_schema':'life-advance native-composite result publishes progress_status/start/end/elapsed/requested; no accepted field. All four actual postcondition values are required.',
        'failed_a01_preserved_no_action_or_write':True,'trace_export_stays_RED':True,'game_day_retry':False},stream,indent=2);stream.write('\n')
print(str(dst))
