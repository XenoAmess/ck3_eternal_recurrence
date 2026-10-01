from pathlib import Path
from datetime import datetime,timezone
import importlib.util
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_day_end_red',ROOT/'scoped_ui_research_a08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bindings=ROOT/'current-run-bindings.json';cfg=m.read(bindings)
live,out,evidence,transport,steps=m.bind(cfg)
day=out/'interactive-requests-responses/scoped-a11-one-day.json'
finish=out/'interactive-requests-responses/scoped-a11-chain-finish-once.json'
d=m.read(day);f=m.read(finish)
m.require(d['result']=='CALL_COMPLETED' and d['body']['progress_status']=='postcondition' and d['body']['starting_date_raw']==cfg['before_date_raw'] and d['body']['elapsed_days']==1 and d['body']['requested_horizon_days']==1 and d['body']['ending_date_raw']==cfg['after_date_raw'],'Actual day completion not proven')
m.require(f['result']=='RED' and 'experimental trace managed DTO unavailable' in str(f.get('error')),'Actual trace finish outcome differs')
body,sr,values=m.snapshot(out,transport,steps,'actual-finished-day-dto-red-snapshot',cfg['after_date_raw'])
record={'at_utc':datetime.now(timezone.utc).isoformat(),'one_day':m.identity(day),'one_day_body':d['body'],
    'post_day_snapshot':sr,'post_day_values':values,'trace_finish':m.identity(finish),'trace_finish_body':None,
    'trace_finish_original_response':f,'source_binding':m.identity(bindings),
    'day_advance_count':1,'day_postcondition_verified':True,'trace_export_status':'RED_MANAGED_DTO_UNAVAILABLE',
    'trace_detour_uninstallation_evidence_level':'source-inferred from unique exact frozen bridge.cpp10305-10323 error branch; no raw detour-uninstalled DTO published',
    'complete_causal_chain':False,'one_day_retry_performed':False,'human_movie_signoff':False}
m.write(evidence/'one-day-finished.json',record)
print(m.identity(evidence/'one-day-finished.json'))
