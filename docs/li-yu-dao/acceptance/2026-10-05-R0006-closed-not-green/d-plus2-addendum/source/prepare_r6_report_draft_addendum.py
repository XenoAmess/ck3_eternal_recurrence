from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json

base=Path('C:/workspace/ck3_lyd_runtime_20261004')
out=base/'r6-report-draft-addendum-001'
out.mkdir(exist_ok=False)
def emit(name,data):
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
def jemit(name,obj):emit(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def dig(data):return sha256(data).hexdigest()
draft=base/'r6-report-draft-001'
expected='fa0aad4d907cb0a57b1627a6afeb4cfd3e1f3cf172f4c9286c8f7c03258850da'
assert dig((draft/'index.json').read_bytes())==expected
source=base/'r6-i2-after-two-days-readback-001'
summary=json.loads((source/'compact-summary.json').read_bytes())
assert summary['result']=='PASS_ACTUAL_D_PLUS2_OBSERVATION_ONLY'
assert summary['actual_date']=='1066.9.17' and summary['actual_native_raw_date']==53144376
assert summary['saved_base_learning']=='14' and summary['saved_total_learning'] is None
for name in ['README.md','actual-natural-time-graph-changes.json','INDEX-compact-addendum.json']:
    emit('source/'+name,(source/name).read_bytes())
report={'schema':'ck3.lyd.r0006-draft-addendum.v1','utc':datetime.now(timezone.utc).isoformat(),'original_draft_index_sha256':expected,'original_draft_795_files_unchanged':True,'status':'ADDENDUM_ONLY_EXIT_PENDING_NOT_GREEN','actual_D_plus2':'1066.9.17 / raw53144376','saved_base_learning':'14','independent_fresh_total_learning':None,'qualification_boundary':summary['qualification_boundary'],'native_rite_head_boundary':'ZhuXi head_of_rite naturally became actor31254; no saved C3 appointment record; both Faith HoF titles remain absent. Do not grant C3 leadership lifecycle acceptance.','milestones_boundary':'60% is a parent reported development estimate, not tests or release acceptance. Oct5/6/7-8/9 are parent reported estimated target dates; exact scope wording pending parent, not fabricated.','failed_request_boundary':'All available raw requests/SDK envelopes/UI action receipts preserved in draft. NO_DISPATCH_RESPONSE_FOUND does not prove an SDK call was made or failed; tool-output-only failures need parent note, not a manufactured receipt.','exit':'PENDING','source_freeze_release':'PENDING','side_effects':{'tracked':0,'git':0,'game_or_screen':0,'ci_network':0,'original_changes':0}}
jemit('report.json',report)
emit('REPORT-addendum.md',('# R0006 草稿补充：两日自然变化与资格边界\n\n'
'本补充只新增说明，绑定原795件草稿 index SHA `'+expected+'`；原草稿及51件诊断不修改。R6仍NOT_GREEN，exit／freeze释放PENDING。\n\n'
'独立D+2包已冻结，结果为PASS_ACTUAL_D_PLUS2_OBSERVATION_ONLY。实际日期1066.9.17／raw53144376，保留35＋1图、实际NPC和对应自然tick／人物政治保护观察。\n\n'
'朱子之学的native head_of_rite自然变为actor31254，存档没有C3任命记录，两Faith仍无宗主title。必须区分礼仪领袖的引擎自然刷新与C3主动任命／认可；本变化不授予C3生命周期验收信用。原始[自然图变化](source/actual-natural-time-graph-changes.json)与[原README](source/README.md)保留。\n\n'
'保存base Learning仍14，fresh total Learning没有独立可读字段；旧资格before8/delta7/after8与setup_before8不变。根报告资格夹具消失、正式决议可见，与当前执行资格相符，但不是精确总学识15的独立测量，也不改写此前资格RED。\n\n'
'普通时间可改变人物／钱包／Faith／native rite head，D+2检查不要求整个世界与D0完全相同。它不证明精确D+1、后续候选延迟校验、正式C2／C3同意／迁移或零错误。100,000条cap后的日志覆盖仍UNAVAILABLE。\n\n'
'向用户报告的60%为开发进度估算，非测试通过率；10月5、6、7—8、9是估算节点。具体目标原措辞尚待根补充，不凭日期杜撰任务或未来GREEN。全部已存在请求／SDK／UI原件保留；缺dispatcher响应与仅工具输出失败分别注明来源边界，不制造本地失败回执。\n').encode('utf-8'))
emit('source/prepare_r6_report_draft_addendum.py',Path(__file__).read_bytes())
files=[]
for path in sorted(out.rglob('*')):
    if path.is_file():
        data=path.read_bytes();files.append({'path':path.relative_to(out).as_posix(),'bytes':len(data),'sha256':dig(data)})
jemit('index.json',{'schema':'ck3.lyd.r0006-draft-addendum-index.v1','files':files,'self_boundary':'index excludes itself'})
print(json.dumps({'path':str(out),'files':len(files)+1,'bytes':sum(row['bytes'] for row in files)+(out/'index.json').stat().st_size,'index_sha256':dig((out/'index.json').read_bytes()),'original_draft_index_unchanged':dig((draft/'index.json').read_bytes())==expected},ensure_ascii=False,indent=2))
