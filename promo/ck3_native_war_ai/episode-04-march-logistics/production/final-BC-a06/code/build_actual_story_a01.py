"""Actual closed C story projection. No TTS, UI, native, Git or media reads."""
from pathlib import Path
from datetime import datetime,timezone
import copy
import hashlib
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parent
CROOT=ROOT.parent
ORAL=CROOT/'e04-final-BC-oral-preparation-a01/main-scope-connection-a05'
CASE=CROOT/'r0176-C-final-review01-preparation-a01/closed-review01-a05-a01'
OUT=ROOT/'actual-story-a01';OUT.mkdir(exist_ok=False)
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as stream:stream.write(raw)
def frozen_source(name,rel,size,sha):
    source=CASE/rel;raw=source.read_bytes()
    assert len(raw)==size and hashlib.sha256(raw).hexdigest()==sha
    target=OUT/'sources'/name;write(target,raw)
    return target,json.loads(raw)
normal_path,C=frozen_source('C-normalized-original.json','normalized_C_result.json',7599,'69cc82ed5371d11d73af1b1308f40fad516bcb15ad227ff72018951d9b9b9873')
terminal_path,terminal=frozen_source('C-Root-terminal.json','terminal/inputs/Root_terminal.json',6937,'991f578aa40f3131681b34473636d0a8d96dc48d77f96812591f5422fe0d4817')
root_path,root_review=frozen_source('C-terminal-Root-review.json','terminal/inputs/latest_Root_review.json',16482,'bfbeacb02084e5c20dc58730b8bcbb40fb2f49ee62ee922fed7ce491a5129c1b')
scope_path,scope=frozen_source('C-terminal-Main-scope.json','terminal/inputs/current_Main_scope.json',6330,'cddd162f23396adf95c06ee4048be466d9795484a5a5b3eab695a84584419a57')
assert C['closed'] is True and C['status']=='ARRIVED_LONDON' and C['actual_days_used']==77
assert C['observed_arrival_interval_days']==[75,77] and C['source_sha256']==pin(terminal_path)['sha256']
assert C['winner'] is None and C['controlled_comparison_eligibility']=='NOT_GRANTED'
assert C['subject_scope']['global_health_status']=='available' and C['subject_scope']['unassessed_CUnit_ids']==[]
assert C['subject_scope']['all_player_total_soldiers'] is None
consumer_C=copy.deepcopy(C)
conversion=[]
for number,row in enumerate(consumer_C['sampling_deviations'],1):
    assert all(type(value) in (int,float) and int(value)==value for value in row['observed_days'])
    row['observed_days']=[int(value) for value in row['observed_days']]
    original=C['sampling_deviations'][number-1]['source_pin']
    source=CASE/original['path'];raw=source.read_bytes()
    assert len(raw)==original['bytes'] and hashlib.sha256(raw).hexdigest()==original['sha256']
    target=OUT/'sources'/f'C-original-sampling-STOP-{number:02d}.json';write(target,raw)
    row['source_pin']=pin(target)
    conversion.append({'source_observed_days':C['sampling_deviations'][number-1]['observed_days'],
       'consumer_integral_days':row['observed_days'],'original_STOP':original,'snapshot_STOP':pin(target)})
assert len(conversion)==15
write(OUT/'C-normalized-consumer.json',consumer_C)
write(OUT/'NORMALIZATION-RECEIPT.json',{'status':'LOSSLESS_INTEGRAL_DAYS_AND_RELOCATED_PINS_ONLY',
 'original':pin(normal_path),'consumer':pin(OUT/'C-normalized-consumer.json'),
 'actual_Root_terminal_unchanged':pin(terminal_path),'sampling_rows':conversion,
 'no_raw_data_rewritten':True,'no_runtime_or_provider_calls':True})
spec=importlib.util.spec_from_file_location('pinned_oral_story',ORAL/'final_bc_increment.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
oldbody=(ORAL/'CURRENT-MAIN-SCOPE-DRAFT-NOT-FINAL.md').read_bytes()
body=tool.paragraphs(oldbody)
replacements={
 'C05-05':'方案C换路线，先经过已核验的中转点，再去伦敦。这次独立回放，在共同起点后的第七十七个游戏日，我们首次观察到主力已经抵达伦敦；第七十五日它还在路上，所以实际到达在这两次观察之间，精确时刻未知。这支主力从六千六百七十九人出发，到达观测时是六千六百八十九，净增十人；完整二十七个兵团的身份与满员数不变。补给从约一百一十点三八降到一百零一点九零，容量仍三百。终点当前损耗读到百分之一，这是当时的条件读数，不能直接换算成旅途中死了多少兵。这里报的是主力的原始编制，不是玩家所有单位的总人数。',
 'C05-14':'结果表按同日期或同事件对齐：先看实际抵达，再看完整兵团与可用人数，然后是库存、补员和损耗窗口，最后是实际支付。这次B合军后，原二十七个兵团仍在，但又多出一条满员一人的兵团记录；合后共有六千六百九十人，满员六千七百四十八。实际统帅也变了，与原先冻结的条件不符。新增记录和统帅变化的原因还没有确认。因此，这次B在第三十八日停止，尚有五十二日预算；停止是冻结条件未通过，不是时间耗尽。这段能保留为合军机制样本，却没有可比较的伦敦终点。C也出现多次采样偏差：原计划每次最多过一天，实际跨了两天。后续只保留为描述性观察，即使已经到达，也不能恢复成严格公平的A/C对照。A和C的实际到达观测各自保留。',
 'C05-16':'同一段日期，金币余额从约六百三十七点五五，变为六百二十一点四八，净少十六点零六。它是期间所有收支留下的净余额差，不能改名为行军费，也不能当作已经核验的登船付款。另看换路线的C回放：从共同起点到它的到达观测，余额净少约十五点八二金币。这个数字同样只是净变化。途中登船阶段曾观察到余额净少十七金币，另一个窗口又净增加约零点二五；各自原因都没有逐笔付款账来证明。现在A和C各有真实到达观测，B因冻结条件未通过而停止；C又保留采样偏差，本次不能排出严格三方案的赢家。',
 'C06-10':'本期已经分别观察到补给回满、实际补兵、不同窗口的兵员减少，以及同日分合军的库存和组织变化。后续休整也出现了真正的库存与人数增加。整军直走和换路线各自保留了真实到达观测；分兵方案因冻结条件变化停止，换路线回放又保留采样偏差，因此没有严格三方案的胜负结论。真实饥饿和逐笔付款仍等待各自证据。你可以按这个顺序读自己的军队，再让每条新结论有自己的日期、身份和结果。'}
body.update(replacements)
counts=(8,12,12,11,16,10)
titles=('行军前先看哪些数','库存、容量与当地供给','补员和兵员损耗','路线、更新与到达','三种安排的实际观察','把检查带回自己的军队')
lines=['# 战争第4期最终 B/C 中文口播：源审候选','',
 '状态：真实终端来源已绑定，等待 Root 对准确字节的中文源审；尚未触发新配音。','',
 '正文69段；仅方括号C编号后的文字配音。源编号、原始单位、哈希和历史切片只在来源账。','']
for chapter,count in enumerate(counts,1):
    lines.extend([f'## 第{chapter}章：{titles[chapter-1]}',''])
    for part in range(1,count+1):
        key=f'C{chapter:02d}-{part:02d}';lines.extend([f'[{key}] {body[key]}',''])
body_path=OUT/'six-chapter-final-BC-Chinese-a06.md';write(body_path,'\n'.join(lines).encode())
base=tool.paragraphs(tool.read_pin(json.loads((ORAL/'request-Mainpartial-current-TEMPLATE.json').read_bytes())['baseline_A_body'],ORAL))
changed=[key for key in base if base[key]!=body[key]]
assert changed==['C05-04','C05-05','C05-08','C05-10','C05-14','C05-16','C06-10']
assert all(body[key]==base[key] for key in ('C05-01','C05-03','C05-15'))
ledger=json.loads((ORAL/'ledger-Mainpartial-TEMPLATE-NOT-FINAL.json').read_bytes())
ledger['historical_pre_final_metadata']={key:ledger.get(key) for key in ('schema','created_utc','source_cut','source_review_status','current_C_source_cut_day','required_sampling_deviation_windows','authority_limits_scope','changed_paragraph_ids','pending_slots')}
ledger.update(schema='ck3.e04.final-BC-authoritative-claim-ledger.v1',created_utc=datetime.now(timezone.utc).isoformat(),
 narration=body_path.name,source_cut='Actual descriptive C London endpoint +77; exact Root terminal/newavailable Main scope/latest15deviations bound. Root narrative review pending in separate hash-bound receipt.',
 current_C_source_cut_day=77,changed_paragraph_ids=changed,subtitle_changed_ids=changed,
 C_controlled_comparison_eligibility='NOT_GRANTED',C_subject_scope=C['subject_scope'],
 C_Main_scope_source_sha256=pin(scope_path)['sha256'],C_sampling_Root_receipt_sha256=pin(root_path)['sha256'],
 C_terminal_source_sha256=pin(terminal_path)['sha256'],final_freeze=True,
 source_review_status='SEPARATE_HASH_BOUND_ROOT_REVIEW_REQUIRED',actual_audio_duration_seconds=None,
 actual_video_duration_seconds=None,ABC_winner=None,authority_limits_scope='Source-bound narration candidate only; no new audio/movie/continuousclean/human1x/signoff. Root source review is a separate receipt, not implied by final_freeze text immutability.')
ledger['ABC_results']['C']=consumer_C
ledger['ABC_results']['B'].update(actual_days_used=38,remaining_original_days=52,controlled_comparison_eligibility='GATE_FAILED',winner=None)
ledger['source_catalog'].update({
 'C-terminal-actual':{'citation':'sources/C-Root-terminal.json','pin':pin(terminal_path)},
 'C-terminal-Root-sampling':{'citation':'sources/C-terminal-Root-review.json','pin':pin(root_path)},
 'C-terminal-Main-scope':{'citation':'sources/C-terminal-Main-scope.json','pin':pin(scope_path)},
 'C-normalized-original':{'citation':'sources/C-normalized-original.json','pin':pin(normal_path)}})
keys_by_id={
 'C05-04':['B-research-published'],'C05-05':['C-terminal-actual','C-terminal-Main-scope','C-terminal-Root-sampling'],
 'C05-08':['B-research-published'],'C05-10':['B-research-published'],
 'C05-14':['B-research-published','C-terminal-actual','C-terminal-Root-sampling'],
 'C05-16':['r177-A2-values','r177-A2-doc','B-research-published','C-terminal-actual','C-terminal-Root-sampling'],
 'C06-10':['supply','refill','r162','r172-doc','merge','r173-qualification','B-research-published','C-terminal-actual','C-terminal-Root-sampling']}
for row in ledger['claims']:
    key=row['id']
    if key not in changed:continue
    prior=copy.deepcopy(row)
    row.update(status='supported-actual-closed-sources-narrative-review-separate',claim_summary=body[key],
       source_keys=keys_by_id[key],historical_pre_final_claim=prior,
       units_and_time='Actual source scopes below, scale100000 supply/cash and attrition fraction; originalT0 raw53148432 / END53150592; firstobserved C+77 interval(75,77]. Bmechanism windows separate21/27/32/38.',
       assumptions_and_limits='Main originalcohort only, not allplayer totals. All endpoint integers/cash are net observations; no applied casualty/refill/payment ledger. B STOPPED_GATE_INCOMPLETE; Cdescriptive NOT_GRANTED; no controlledwinner. Audio/media/signoff not granted by text freeze.')
    if key in ('C05-05','C05-14','C05-16','C06-10'):
        row['actual_C_endpoint_metrics']=C['London_endpoint_metrics']
        row['actual_C_bounds']={'T0_current':6679,'terminal_current':6689,'net_current':10,'max':6747,
          'stock_initial_raw':11037716,'stock_terminal_raw':10190260,'stock_net_raw':-847456,
          'treasury_initial_raw':63754562,'treasury_terminal_raw':62173052,'treasury_net_raw':-1581510,
          'boarding_window_treasury_net_raw':-1700000,'day60_treasury_net_raw':24723,
          'cash_income_cause':None,'cash_payment_ledger':None,'applied_loss_or_refill_ledger':None,
          'scope_terminal':C['subject_scope'],'historical_unknown_CUnit16777391_health':None,
          'historical_unknown_window_days':[59,75],'terminal_unassessed_CUnits':[],
          'terminal_available_is_not_allplayer_total':True}
ledger['required_sampling_deviation_windows']=[row['observed_days'] for row in consumer_C['sampling_deviations']]
ledger['sampling_requirements_source']=pin(root_path)
ledger['historical_a05_pending_slots_exact']=ledger['pending_slots']
ledger['pending_slots']=[{'id':'P-ABC-CONTROLLED','status':'not_granted','needs':'New qualified experiment; current Bgatefailed and C15samplingdeviations cannot yield controlledwinner'},
 {'id':'P-STARVATION','status':'pending','needs':'Actual starvation threshold/state/integers evidence'},
 {'id':'P-APPLIED-LEDGER','status':'pending','needs':'Actual applied losses/refill/payments distinct from endpointnet'},
 {'id':'P-REVIEW01','status':'production_pending','needs':'Actual minimalnewvoice/English/subtitles/picture/movieaudit; humanreview/signoff separate'}]
ledger_path=OUT/'claim-ledger-final-BC-a06.json';write(ledger_path,ledger)
oral=json.loads((ORAL/'request-Mainpartial-current-TEMPLATE.json').read_bytes())
for key in ('baseline_A_body','preserved_B_candidate_body','C05_01_reuse_proof'):
    raw=tool.read_pin(oral[key],ORAL);source=Path(oral[key]['path']);source=source if source.is_absolute() else ORAL/source
    oral[key]=pin(source)
oral['current_partial_draft_body']=pin(body_path)
oral['current_C_Root_basis_source']=pin(root_path);oral['current_C_Main_scope_source']=pin(scope_path)
oral['future'].update(final_C_terminal_source=pin(terminal_path),normalized_C_result=consumer_C,
   final_chinese_body=pin(body_path),final_claim_ledger=pin(ledger_path),source_review=None)
oral['normalized_C_original_producer_source']=pin(normal_path)
write(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json',oral)
tool.load_request(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json')
tool.validate_sampling_deviations(consumer_C['sampling_deviations'],oral,OUT/'oral-final-request-PENDING-ROOT-REVIEW.json')
scope_description,scope_sha=tool.current_Main_subject_scope(oral,OUT/'oral-final-request-PENDING-ROOT-REVIEW.json')
assert scope_description==C['subject_scope'] and scope_sha==pin(scope_path)['sha256']
review={'schema':'ck3.e04.final-BC-narrative-review-request.v1','source_review_status':None,'final_freeze':False,
 'changed_paragraph_ids':changed,'subtitle_changed_ids':changed,
 'chinese_body_sha256':pin(body_path)['sha256'],'chinese_ledger_sha256':pin(ledger_path)['sha256'],
 'C_terminal_source_sha256':pin(terminal_path)['sha256'],'C_sampling_Root_receipt_sha256':pin(root_path)['sha256'],
 'C_Main_scope_source_sha256':pin(scope_path)['sha256'],'C_subject_scope':C['subject_scope'],
 'C_controlled_comparison_eligibility':'NOT_GRANTED','ABC_results':ledger['ABC_results'],'ABC_winner':None,
 'required_reviewer':'/root','reviewer':None,'reviewed_utc':None,'NO_BLOCK_not_yet_granted':True,
 'new_TTS_requests':0,'human_listening_or_film_signoff':False}
write(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json',review)
diff={'status':'ACTUAL_SOURCE_BOUND_BODY_LEDGER_AWAITING_ROOT_NARRATIVE_REVIEW','body':pin(body_path),'ledger':pin(ledger_path),
 'changed_paragraph_ids':changed,'subtitle_changed_ids':changed,'exact_reused_Chinese_ids':[key for key in body if key not in changed],
 'C05_01_03_15_exactreuse':True,'changed_paragraphs':[{ 'id':key,'text_zh':body[key],'source_keys':keys_by_id[key]} for key in changed],
 'current_C_terminal_source':pin(terminal_path),'current_Root_review':pin(root_path),'current_Main_scope':pin(scope_path),
 'raw_sourcepins_all_verified':True,'consumer_sampling15_integral_window_checks':'PASS','source_review_status':None,
 'ABC_winner':None,'new_TTS_requests':0,'actual_final_audio_seconds':None}
write(OUT/'ROOT-CHINESE-REVIEW.json',diff)
write(OUT/'ROOT-DELIVERY.json',{'status':diff['status'],'Chinese':pin(body_path),'ledger':pin(ledger_path),
 'review_request':pin(OUT/'ROOT-SOURCE-REVIEW-REQUEST.json'),'changed_review':pin(OUT/'ROOT-CHINESE-REVIEW.json'),
 'oral_request':pin(OUT/'oral-final-request-PENDING-ROOT-REVIEW.json'),'normalized_original':pin(normal_path),
 'normalized_consumer':pin(OUT/'C-normalized-consumer.json'),'normalization_receipt':pin(OUT/'NORMALIZATION-RECEIPT.json'),
 'current_C_terminal':pin(terminal_path),'current_Root_review':pin(root_path),'current_Main_scope':pin(scope_path),
 'changed_paragraph_ids':changed,'new_TTS_requests':0,'new_movie_seconds':None,'human_signoff':False})
print(json.dumps({'status':'ACTUAL_FINAL_BODY_LEDGER_READY_FOR_ROOT_REVIEW','delivery':pin(OUT/'ROOT-DELIVERY.json'),
 'body':pin(body_path),'ledger':pin(ledger_path),'changed_ids':changed},ensure_ascii=False))
