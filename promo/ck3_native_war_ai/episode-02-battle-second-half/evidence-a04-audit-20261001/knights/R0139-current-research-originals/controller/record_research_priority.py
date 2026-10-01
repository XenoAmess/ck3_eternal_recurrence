from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/w/e2gold1001')
now=datetime.now(timezone.utc).isoformat()
items=[('骑士次日角色界面','未完成：同次实机的角色窗原图待采'),('名单变化','未完成：原版名单界面与有序原生名单同身份对拍待采'),
       ('完整战斗窗','未完成：完整下半部构成和必要滚动画面待采'),('骑士选择器','研究中：候选构造、过滤、顺序、随机返回与新trace闭环'),
       ('唯一死因','研究中：本案death effect请求、延后commit与实际归因闭环'),('完整可变状态链','研究中：本期具体事件/加入案例的事件写回、伤亡和下一暂停帧；不能用局部观测翻转全局complete标志')]
pins=[]
for p in [ROOT/'ui-launch-plan.json',ROOT/'native-research-plan.json',ROOT/'native-research-plan-check.json',
          ROOT.parent/'root-attempt-01/operator-profile-a01.json',
          Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a01/ck3-output/entry-failure.json')]:
    pins.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()})
record={'at_utc':now,'user_order':'先研究全部六项，再使用研究成果优化视频','items':[{'item':a,'status':b} for a,b in items],
        'a07_status':'existing intermediate review artifact; no new video revision started',
        'research_branch':'codex/war-e2-mechanism-closure-20261001','research_base':'1901473429deb1297be7d5d4451169082629858b',
        'research_worktree':'C:/w/e2research1001','master_intake_allowed':False,
        'first_launch':'operator accepted; entry refused mismatched screen checkout; CK3 never launched and no live run ID',
        'second_launch':'R0139 warmup and final isolated CK3 process created; source is still loading; no successful mechanism sample yet','pins':pins}
with (ROOT/'user-six-gap-priority-and-current-status.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
table='\n'.join('| '+a+' | '+b+' |' for a,b in items)
text='\n\n## 2026-10-01：用户要求六项研究全部完成后才修改视频\n\n'
text+='用户明确将骑士次日角色界面、名单变化、完整战斗窗、骑士选择器、唯一死因、完整可变状态链全部列为本期视频的前置研究工作。先前按制作工作量给出的95%不再代表当前任务完成度；a07保留为中间审阅版，当前未开始新渲染或视频优化。\n\n'
text+='| 工作项 | 当前状态 |\n| --- | --- |\n'+table+'\n\n'
text+='研究在新独立工作树 `C:/w/e2research1001`、分支 `codex/war-e2-mechanism-closure-20261001` 推进，基线固定1901473429deb1297be7d5d4451169082629858b；继续禁止master intake/合入。骑士/死因静态研究、native状态链施工、UI能力施工按文件所有权并行，root独占实机。\n\n'
text+='首个新attempt因屏幕任务登记树与冻结capture执行树不一致而在实机前被拒绝，`native_session_invoked=false`/`ck3_process_created=false`；原件永久保留。新的R0139已实际创建warmup及final隔离进程，当前仍在载入，未将ACK写成live机制证据。研究采样方案 `native_research_plan.py check --for-observation` 已通过，校验只证明输入方案合同。\n\n'
text+='新过程索引：`'+str(ROOT/'user-six-gap-priority-and-current-status.json')+'`。原R0127的1040进一步定位为final-query1024加identity16，落在side1 scheduled RegimentID65的读取，尚未进入最终人物读取；新读口须正确表达原生retired lifecycle，继续保留完整ID/generation校验。死亡效果可defer的静态发现需新的实际请求/commit采样支持，暂不写成本案唯一死因已证明。\n'
paths=['docs/ck3-native-ai/a04-mechanism-evidence-audit-2026-10-01.md','docs/autonomous-agent-progress/daily/2026-10-01.md',
       'docs/autonomous-agent-progress/meetings/daily/2026-10-01.md','docs/autonomous-agent-progress/weekly/2026-W40.md']
for rel in paths:
    p=REPO/rel
    with p.open('ab') as f:f.write(text.encode('utf-8'))
print(json.dumps({'record':str(ROOT/'user-six-gap-priority-and-current-status.json'),'updated_docs':paths,'at_utc':now},ensure_ascii=False))
