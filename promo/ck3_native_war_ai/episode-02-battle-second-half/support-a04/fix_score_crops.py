from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json,hashlib,importlib.util,shutil
ROOT=Path(__file__).resolve().parent;PROJECT=Path('C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/project')
script=PROJECT.parent/'compose_review_boards_a04.py';module_spec=importlib.util.spec_from_file_location('board_a04',script);m=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(m)
spec=json.loads((ROOT/'visual-spec-final-v1.json').read_text(encoding='utf-8'));edit=json.loads((ROOT/'edit-final-v1.json').read_text(encoding='utf-8'))
work=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-a04-boards-a03');work.mkdir(exist_ok=False);shutil.copyfile(script,work/'board-composer-source.py')
changes=[]
for key in ['terminal-t031','closing-c004']:
    before=spec['utterances'][key];row={**before,'extra_ui':[],'source_image':'C:/Users/1/AppData/Local/ck3-review-analysis/episode02-20260930-a03/ui-pursuit-terminal/a2-480.png','crop_xyxy':[668,895,1233,985],'ui_label':'同次A05结算后真实UI：总分−50% / 剑形分项−50%'}
    row['footer']='A05第32日真实结算后界面｜主放大为−50%；右侧原生记录另列'
    spec['utterances'][key]=row;result=m.board(work,key,row);edit['utterances'][key]=result
    changes.append({'key':key,'old_spec':before,'new_spec':row,'new_image':result['rendered_image'],'scope':'Primary enlargement is now the actual AFTER −50% panel rather than BEFORE 0%; narration/timing unchanged.'})
for path,data in [(ROOT/'visual-spec-final-v2.json',spec),(ROOT/'edit-final-v2.json',edit),(work/'crop-fix-receipt.json',{'changes':changes,'previous_final_sha256':'1D787A95A4A70C9DD2445AB29075D1745807A450423FB9DC8B2E2281027025DA','narration_changed':False,'tts_changed':False,'timeline_changed':False})]:m.write(path,data)
for source,name in [(ROOT/'visual-spec-final-v2.json','review-story-a04-board-specs-v2.json'),(ROOT/'edit-final-v2.json','review-story-a04-edit-v2.json')]:
    with (PROJECT/name).open('xb') as f:f.write(source.read_bytes())
print(json.dumps({'changes':changes,'edit':m.ref(ROOT/'edit-final-v2.json')},ensure_ascii=False))
