from pathlib import Path
import json
p=Path(__file__).parent/'current-input-inspection-a01.json'
v=json.loads(p.read_text('utf-8'))
for k,r in v['documents'].items():
 body=r['value']
 if 'ui-root-review' in k:
  print(json.dumps({'name':k,'original':r['original'],'observations':body['observations'],'images':body['reviewed_images'],'full_panel':body['full_panel_original_image'],'source_values':body['source_values'],'source_binding':body['source_binding'],'extra_flags':{x:body[x] for x in ['UI_getter_full_ordered_roster_IDs_proven','native_hover_provider_stays_RED','six_gaps_not_yet_closed','daily_trace_export_succeeded','global_mutable_bundle_complete'] if x in body}},ensure_ascii=False))
 elif 'saved-pair' in k or 'one-day-finished' in k:
  print(json.dumps({'name':k,'original':r['original'],'value':{x:body[x] for x in ['phase','source_values','immutable','source_binding','day_advance_count','day_postcondition_verified','trace_export_status','complete_causal_chain','one_day_retry_performed','post_day_values'] if x in body}},ensure_ascii=False))
 elif 'candidate-manifest' in k or 'session-result' in k or 'readback' in k or 'screen-release' in k or 'current-run-bindings' in k:
  print(json.dumps({'name':k,'original':r['original'],'value':body},ensure_ascii=False))
