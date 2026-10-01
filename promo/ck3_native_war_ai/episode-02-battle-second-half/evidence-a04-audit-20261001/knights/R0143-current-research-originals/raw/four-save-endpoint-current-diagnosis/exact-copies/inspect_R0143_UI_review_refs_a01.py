from pathlib import Path
import json,sys
B=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07/scoped-ui-research-attempt-01')
sys.stdout.reconfigure(encoding='utf-8')
for phase in ['before','after']:
 v=json.loads((B/(phase+'-ui-root-review.json')).read_text(encoding='utf-8-sig'))
 print(json.dumps({'phase':phase,'reviewed_images':v['reviewed_images'],'full_panel_original_image':v['full_panel_original_image']},ensure_ascii=False))
for s in ['before-victim-character-original-ui-binding.json','before-combat-fit-full-combat-panel-binding.json','after-victim-character-original-ui-binding.json']:
 v=json.loads((B/s).read_text(encoding='utf-8-sig'));print(json.dumps({'binding':s,'query_values':v['query_values'],'post_pixels_values':v['post_pixels_values'],'body':{k:v['readback_body'][k]for k in ['available','effective_visible','accepted','native_revision','application_owner_thread_verified','rng_owner_is_ui_admission_gate']}}))
