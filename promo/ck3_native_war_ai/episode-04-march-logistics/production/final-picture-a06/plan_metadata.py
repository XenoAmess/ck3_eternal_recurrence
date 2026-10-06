"""Local metadata-only default plan; never reads the external media."""
from pathlib import Path
import json
def main():
 root=Path(__file__).resolve().parent
 state=json.loads((root/'results/production-state-at-freeze.json').read_text(encoding='utf-8'))
 config=json.loads((root/'inputs/project.original.json').read_text(encoding='utf-8'))
 rows=json.loads((root/'inputs/picture-rows.original.json').read_text(encoding='utf-8'))
 print(json.dumps({'state':'LOCAL_METADATA_PLAN','chapters':len(config['chapters']),'paragraphs':sum(len(c['cues']) for c in config['chapters']),'incremental_picture_rows':[r['id'] for r in rows],'actual_narration_seconds':state['actual_narration_seconds'],'expected_frames':state['expected_picture_frames'],'external_media_included':False,'cross_machine_render_admitted':False,'media_reads':0,'processes_started':0,'human_signoff':False},ensure_ascii=False,indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
