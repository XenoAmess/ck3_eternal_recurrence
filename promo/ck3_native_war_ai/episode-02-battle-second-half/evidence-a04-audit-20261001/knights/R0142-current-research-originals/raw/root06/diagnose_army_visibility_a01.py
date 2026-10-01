"""Readonly diagnosis after accepted selection and failed initial visibility read."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_army_visibility', ROOT / 'scoped_ui_research_a08.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bindings = ROOT / 'current-run-bindings.json'
config = m.read(bindings)
live, output, evidence, transport, steps = m.bind(config)
m.require(not (evidence / 'one-day-intent.json').exists(), 'Day already attempted')
snap, sr, values = m.snapshot(output, transport, steps, 'army-visibility-diagnostic-source', config['before_date_raw'])
body, rr = transport.call(output, 'army-visibility-diagnostic-readonly', 'ck3_query_ingame_ui_window_v1', {'window_kind':'army', 'expected_revision':values['revision']}, 120)
image = m.capture_window(live, evidence, 'army-visibility-readonly-diagnostic')
post, pr, pv = m.snapshot(output, transport, steps, 'army-visibility-diagnostic-post', config['before_date_raw'])
m.require(values == pv, 'Paused source changed')
body2, rr2 = transport.call(output, 'army-visibility-diagnostic-post-readonly', 'ck3_query_ingame_ui_window_v1', {'window_kind':'army', 'expected_revision':pv['revision']}, 120)
record = {'at_utc':datetime.now(timezone.utc).isoformat(), 'binding':m.identity(bindings),
    'source_values':values,'source_snapshot':sr,'native_read':rr,'native_body':body,
    'original_image':image,'post_snapshot':pr,'post_values':pv,'post_read':rr2,'post_body':body2,
    'mutating_action_retried':False,'day_advance_count':0,'original_pixels_actually_reviewed':False}
m.write(evidence / 'army-visibility-readonly-diagnostic.json', record)
fields = ('available','window_kind','effective_visible','current_character_id','current_army_id','selected_army_id','native_revision','date_raw','thread_id','pump_epoch','unavailable_reason','gui_context_address','gui_owner_address')
print(json.dumps({'record':str(evidence / 'army-visibility-readonly-diagnostic.json'),
    'first':{key:body.get(key) for key in fields},'second':{key:body2.get(key) for key in fields},
    'image':image['image']},ensure_ascii=False))
