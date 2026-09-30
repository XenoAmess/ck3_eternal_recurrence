from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
ANALYSIS=Path('C:/Users/1/AppData/Local/ck3-review-analysis/episode02-20260930-a03')
RUN=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a03')
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
edit=json.loads(Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-a04-boards-a02/edit.json').read_text(encoding='utf-8'))
timeline=json.loads((RUN/'timeline.json').read_text(encoding='utf-8'));bykey={u['key']:u for c in timeline['chapters'] for u in c['utterances']}
raws={
 'pursuit':('D:/workspace/ck3_native_war_ai_promo_work/episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv',840210967,'25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC','ui-pursuit-terminal/visual_map.json'),
 'knights':('D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv',2451530594,'7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F','ui-knights/knights-ui-edit-map.json'),
 'reinforcement':('D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-live-20260928-a01/recording-e2-06-d11-a01/raw/e2-06-d11.mkv',1325156480,'501B4C2A8557DC2EBBE88FD0485A45265FDDC9BF8EF46F7A1E968F8EB51024C7','ui-reinforcement/ui-reinforcement-edit-map.json')}
shots=[('pursuit-p002','pursuit',80,'A05 独立后段回放 · 第28日追击'),('pursuit-p017','pursuit',100,'A05 同次回放 · 第29日803'),('pursuit-p021','pursuit',185,'A05 同次回放 · 第30日782'),('pursuit-p022','pursuit',300,'A05 同次回放 · 第31日761'),('knights-k034','knights',232.50,'a02 独立阵亡实录 · 11→10；非历史020/070'),('knights-k035','knights',233.00,'a02 同次实录 · 中文阵亡通知'),('reinforcement-r001','reinforcement',345,'A01 独立第11日检查点回放'),('reinforcement-r002','reinforcement',350,'A01 同次实录 · 我方893／敌方1603'),('reinforcement-r003','reinforcement',365,'A01 同次实录 · 我方827／敌方4106'),('reinforcement-r037','reinforcement',375,'A01 真实界面 · 内部战宽由原生解释图另述'),('terminal-t001','pursuit',470,'A05 同次后段回放 · 普通终局'),('terminal-t006','pursuit',480,'A05 同次原生战争界面 · 总分与战斗项−50%'),('closing-c006','reinforcement',225,'A01 独立回放示例 · 海上2570；非下一战预测')]
bindings={}
for rid,(path,expected,digest,mapname) in raws.items():
    source=Path(path)
    if source.stat().st_size!=expected:raise ValueError(f'raw size changed {source}')
    bindings[rid]={'path':str(source),'bytes':expected,'sha256':digest,'identity_provenance':ref(ANALYSIS/mapname),'method':'Previously completed full hash in frozen capture/UI receipts; current exact file size checked. Not a new raw hash or clean-span approval.'}
for key,rid,start,label in shots:
    old=edit['utterances'][key];duration=bykey[key]['duration']
    if rid=='pursuit' and any(start < hi and start+duration > lo for lo,hi in [(37.933,38.7),(179.6,180.067),(271.267,278.833)]):raise ValueError('excerpt crosses documented timestamp gap')
    edit['utterances'][key]={'kind':'raw-excerpt','image':raws[rid][0],'start':start,'source_duration':duration,'case':label,'source_binding':bindings[rid],'still_alternative':old,'admission':'Review excerpt anchored to documented actual frames; continuous human clean-span approval pending.'}
edit['full_episode_policy']={'chapter_order':['opening','pursuit','knights','reinforcement','terminal','closing'],'narration_duration':timeline['total_duration'],'raw_excerpts':len(shots),'looped_raw':False,'speed':1.0,'unvoiced_holds':0,'historical_missing_ui':'Labelled native-record diagrams, with separately labelled present-day UI examples; no invented historical capture.'}
out=ROOT/'edit-final-v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(edit,f,ensure_ascii=False,indent=2)
target=Path('C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/project/review-story-a04-edit.json')
with target.open('xb') as f:f.write(out.read_bytes())
print(json.dumps({'edit':ref(out),'raw_excerpts':len(shots),'narration_duration':timeline['total_duration']}))
