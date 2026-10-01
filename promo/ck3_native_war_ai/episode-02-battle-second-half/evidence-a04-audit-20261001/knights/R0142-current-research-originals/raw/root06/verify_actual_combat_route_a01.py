"""Verify the actual stock window after the already accepted army selection."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_combat_route', ROOT/'scoped_ui_research_a08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bindings=ROOT/'current-run-bindings.json';config=m.read(bindings)
live,output,evidence,transport,steps=m.bind(config)
m.require(not (evidence/'one-day-intent.json').exists(),'A day was already attempted')
snap,sr,values=m.snapshot(output,transport,steps,'army-combat-route-source',config['before_date_raw'])
body,rr=transport.call(output,'army-combat-route-readonly','ck3_query_ingame_ui_window_v1',{'window_kind':'combat','expected_revision':values['revision']},120)
m.verify_window(body,'combat',config['combat_id'],values,config)
record={'at_utc':datetime.now(timezone.utc).isoformat(),'binding':m.identity(bindings),'snapshot':sr,
        'source_values':values,'readback':rr,'readback_body':body,
        'current_original_combat_verified':True,'army_window_visibility_failure_preserved':True,
        'no_new_selection_or_open_action':True,'no_day_advance':True,'full_panel_pixels_reviewed':False}
m.write(evidence/'actual-army-combat-route-readonly.json',record)
print(json.dumps({key:body.get(key) for key in ('available','window_kind','effective_visible','subject_id_available','current_subject_id','date_raw','native_revision','thread_id','pump_epoch','left_knight_count','right_knight_count')},ensure_ascii=False))
