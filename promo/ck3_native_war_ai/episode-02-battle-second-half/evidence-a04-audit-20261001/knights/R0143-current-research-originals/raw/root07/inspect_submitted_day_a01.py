from pathlib import Path
import importlib.util
import json
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_actual_day_inspection',ROOT/'scoped_ui_research_a09.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cfg=m.read(ROOT/'current-run-bindings.json')
live,output,evidence,transport,steps=m.bind(cfg)
path=output/'interactive-requests-responses/scoped-a12-one-day.json'
row=m.read(path)
body=row.get('body',{})
safe={k:v for k,v in body.items() if isinstance(v,(str,int,float,bool,type(None)))}
snap,sr=transport.call(output,'a13-actual-post-day-readonly','ck3_take_snapshot',{},120)
fields={k:snap.get(k) for k in ['episode_run_id','date_raw','paused','revision','native_revision','snapshot_id']}
fields['actor']=snap.get('played_character',{}).get('character_id')
m.write(evidence/'submitted-day-actual-schema-inspection.json',{'day_original':m.identity(path),'day_result':row.get('result'),'day_top_keys':list(body),'actual_scalar_fields':safe,'current_snapshot_receipt':sr,'current_fields':fields,'no_day_retry':True,'no_UI_action':True})
print(json.dumps({'day_result':row.get('result'),'day_top_keys':list(body),'day_scalar_fields':safe,'current':fields}))
