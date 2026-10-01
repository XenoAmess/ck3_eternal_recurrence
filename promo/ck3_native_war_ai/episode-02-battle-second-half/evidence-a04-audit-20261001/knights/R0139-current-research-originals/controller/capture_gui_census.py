from pathlib import Path
import json,sys
from datetime import datetime,timezone
import knight_saved_pair as pair
ROOT=Path(__file__).resolve().parent
OUT=pair.OUTPUT
EVIDENCE=pair.NEW/'gui-census-attempt-01'
EVIDENCE.mkdir(exist_ok=False)
pair.require((ROOT/'native-research-plan-check.json').exists(),'Sampling plan check missing')
pair.require((OUT/'interactive-requests-responses/service.json').exists(),'Owning MCP service not ready')
snapshot,sr=pair.transport.call(OUT,'six-gap-gui-source-snapshot','ck3_take_snapshot',{},120)
ok,values=pair.step.snapshot_case(snapshot,53146848,require_combat=True)
pair.require(ok,'Source date/actor/combat mismatch')
tree,tr=pair.transport.call(OUT,'six-gap-current-gui-tree','ck3_inspect_frontend_gui_tree_v1',{},120)
image=pair.capture_window(EVIDENCE,'d26-gui-census')
after,ar=pair.transport.call(OUT,'six-gap-gui-after-snapshot','ck3_take_snapshot',{},120)
ok,av=pair.step.snapshot_case(after,53146848,require_combat=True)
pair.require(ok,'Paused source drifted during GUI inspection')
pair.write(EVIDENCE/'gui-census-binding.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'before_values':values,'after_values':av,
 'snapshot':sr,'tree_response':tr,'image':image,'after_snapshot':ar,'tree_body':tree,
 'human_full_panel_review':False,'character_UI_confirmed':False,'scope':'bounded original native GUI census; no navigation input'})
print(json.dumps({'result':'GUI_CENSUS_CAPTURED_PENDING_REVIEW','evidence':str(EVIDENCE),'before_values':values,'after_values':av,
 'tree_body_keys':list(tree)},ensure_ascii=False))
