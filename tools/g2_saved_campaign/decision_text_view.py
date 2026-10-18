"""Pure audience-facing projection of actual plans, replies and repair status."""
from collections import deque
from datetime import datetime,timezone
import json
from pathlib import Path

TITLE='智能体实时决策'

def decode(row):
    if row.get('tool')=='root_before_auto_turn_submit':return row.get('body') or {}
    result=row.get('result') or {}
    body=result.get('structured_content',result.get('structuredContent'))
    if isinstance(body,dict):return body
    for block in result.get('content',[]):
        if block.get('type')=='text':
            try:value=json.loads(block.get('text',''))
            except (ValueError,TypeError):continue
            if isinstance(value,dict):return value
    return {}

def action(step):
    if not isinstance(step,str) or not step:return '观察当前局势'
    if step.startswith(('life-advance','exact-one-day')):return '推进时间，观察局势变化'
    if step.startswith('declare-war-'):return '向选定目标宣战'
    if step.startswith(('move-army-','halt-army-')):return '调整军队行动'
    if step.startswith(('select-event-option','resolve-mandatory','choose-')):return '处理当前事件选择'
    if step.startswith(('save-checkpoint','save-')):return '保存本次进度'
    if step.startswith(('raise-troops','raise-army')):return '集结军队'
    if step.startswith(('center-map','camera-')):return '调整观察镜头'
    if 'construction' in step or 'building' in step:return '检查或安排领地建设'
    if any(k in step for k in ('family','guardian','education','focus')):return '处理家族与教育事务'
    if 'crown' in step or 'realm-law' in step:return '处理领地政务'
    if step.startswith(('query-','preview-','verify-')):return '核对当前局势与行动条件'
    return '处理当前游戏事务'

def clean_chinese(value,limit=120):
    if not isinstance(value,str):return ''
    lines=[]
    for line in value.splitlines():
        if any(x in line for x in ('PID','creation_filetime','native_revision','snapshot_id','sdk-','SourceSHA','XAR_','query-')):continue
        line=line.replace('state_changed','局势发生变化').replace('SDK','游戏接口').replace('Native','游戏')
        if any('\u4e00'<=c<='\u9fff' for c in line):lines.append(line.strip())
    return ' '.join(lines)[:limit]

def reason(plan,step):
    readable=clean_chinese(plan.get('reason'))
    if readable:return readable
    if isinstance(step,str) and step.startswith('life-advance'):return '当前没有更优先的事务，继续观察新的变化。'
    if isinstance(step,str) and step.startswith('declare-war-'):return '已核对当前目标与宣战条件，准备提交行动。'
    if isinstance(step,str) and 'move-army' in step:return '根据当前路线、目标和风险调整军队。'
    return '依据当前游戏回执核对条件，再决定下一步。'

def result_text(body):
    inner=body.get('result') if isinstance(body.get('result'),dict) else body
    status=inner.get('status',body.get('status'))
    if status=='observed_after_native_error' or inner.get('native_ack_status')=='unknown_after_error':
        return '观察到新的游戏状态，原操作回执仍未确认。'
    if inner.get('checkpoint',{}).get('status')=='saved':return '进度已保存。'
    if inner.get('accepted') is False:return '操作未获确认，保留实际回执。'
    if status in ('blocked','rejected','failed','readonly_unavailable'):return '当前条件未满足，尚未执行。'
    if status in ('available','hidden','not_visible'):return '局势信息已读回。'
    if status in ('submitted','queued'):return '已提交，等待游戏结果。'
    if status in ('executed','enacted','centered','already_centered','closed','completed'):
        return '实际回执已返回。'
    if status=='planned':return '计划已形成，尚未提交。'
    return '已收到实际回执，继续核对结果。'

class AudienceState:
    def __init__(self):
        self.stage='观察当前游戏';self.decision='核对当前局势';self.reason='继续已有战役，保留本次进度。'
        self.result='等待当前地图与实际回执。';self.events=deque(maxlen=3);self.repair=None;self.last_key=(0,-1)

    def switch_namespace(self):self.last_key=(0,-1)

    def consume(self,row):
        if row.get('root_runtime_repair_status'):return
        body=decode(row);plan=body.get('plan') if isinstance(body.get('plan'),dict) else {}
        step=body.get('selected_step') or body.get('step') or plan.get('selected_step')
        tool=(row.get('tool') if row.get('tool')=='root_before_auto_turn_submit'
              else (row.get('request') or {}).get('tool') or row.get('tool',''))
        number=(row.get('request') or {}).get('sequence')
        if number is None and tool=='root_before_auto_turn_submit':number=(row.get('request') or {}).get('parent_sequence')
        if type(number) is int:
            key=(number,0 if tool in ('root_before_auto_turn_submit','ck3_plan_turn') else 1)
            if key<self.last_key:return
            self.last_key=key
        error=row.get('client_error') or (row.get('result') or {}).get('is_error',(row.get('result') or {}).get('isError'))
        if error:
            self.result='本次请求失败，保留原始结果。';return
        if tool=='root_before_auto_turn_submit' or tool=='ck3_plan_turn':
            self.decision=action(step);self.reason=reason(plan,step);self.result='计划已形成，尚未提交。'
            self.events.append('计划：'+self.decision);return
        if any(x in tool for x in ('bookmark','frontend','new_game','start_game')):
            if 'query' in tool:self.decision='确认菜单与开局状态'
            elif 'bookmark' in tool:self.decision='选择开局角色'
            else:self.decision='开始新的战役'
            self.reason='从1066年书签建立一局干净的新游戏。';self.result=result_text(body)
            self.events.append('回执：'+self.decision);return
        if tool=='ck3_auto_turn' or step:
            self.stage='自动游玩';self.decision=action(step);self.reason=reason(plan,step)
            self.result=result_text(body);self.events.append('回执：'+self.decision)

    def repair_status(self,state,binding,now=None):
        if not state:self.repair=None;return
        active=state.get('active_binding',state.get('binding')) or {}
        if any(active.get(k)!=binding.get(k) for k in ('session','game_pid','game_creation_filetime')):
            self.repair=None;return
        phase=state.get('phase')
        if state.get('withdrawn') or phase=='expired':self.repair=None;return
        brief=clean_chinese(state.get('pause_reason')) or '自动推进暂时停止'
        if phase in ('repairing','repair_applied_waiting_for_progress'):
            self.repair=brief+'\n正在修复中';return
        proof=state.get('recovery_proof') or {}
        if phase=='resolved' and type(proof.get('actual_date_delta_raw')) is int and proof['actual_date_delta_raw']>0:
            end=state.get('expires_at_utc')
            if end and datetime.fromisoformat(end)<= (now or datetime.now(timezone.utc)):
                self.repair=None;return
            self.repair=(clean_chinese(state.get('repair_message')) or '修复已完成')+'\n已恢复推进'
        else:self.repair=None

    def render(self):
        text=TITLE+'\n'+self.stage+'\n\n决策：'+self.decision+'\n理由：'+self.reason+'\n结果：'+self.result
        if self.repair:text+='\n\n'+self.repair
        if self.events:text+='\n\n最近\n'+'\n'.join(self.events)
        return text
