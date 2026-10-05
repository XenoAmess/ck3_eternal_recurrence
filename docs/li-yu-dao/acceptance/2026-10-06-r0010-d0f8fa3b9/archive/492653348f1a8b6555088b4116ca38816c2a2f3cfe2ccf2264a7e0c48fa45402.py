import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'r10-actual-fifth-post-cancel-readback-20261005-001/finalize_cancel.py';raw=SOURCE.read_bytes();text=raw.decode('utf-8');changes=[]
def replace(old,new):
    global text
    count=text.count(old)
    if not count:raise ValueError('Missing qualified finalizer anchor '+old)
    text=text.replace(old,new);changes.append({'old':old,'new':new,'occurrences':count})
replace('r10-actual-fifth-open-join-readback-20261005-001','r10-actual-sixth-open-join-readback-20261005-001');replace('r10-actual-fourth-post-cancel-readback-20261005-001','r10-actual-fifth-post-cancel-readback-20261005-001')
start=text.index('personal=controls[');end=text.index('prior=read(',start)
text=text[:start]+"review=controls['0145-']['result']['current_event_window_context'];selection=controls['0146-']['result'];result_event=controls['0147-']['result']['current_event_window_context'];ack=controls['0148-']['result'];fresh=controls['0150-']['result'];q=fresh['character_interaction_ordinary_context']\n"+text[end:]
remove_prefixes=[" 'actual_personal114_"," 'actual_personal_yes115_"," 'actual_scholar116_"," 'actual_scholar_yes117_"," 'actual_review120_"]
for pref in remove_prefixes:
    lines=text.splitlines(True);matches=[line for line in lines if line.startswith(pref)]
    if len(matches)!=1:raise ValueError('Need single unused preceding control check '+pref)
    text=''.join(line for line in lines if not line.startswith(pref));changes.append({'removed_not_consumed_prior_control_check':pref})
old="'actual_source_target_signatures_and_request_absent':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested'])"
replace(old,"'actual_source_signed1_target_requested_signed_absent':num(av,'lyd_c2_source_signed')=='1' and all(av.get(k) is None for k in ['lyd_c2_target_signed','lyd_c2_target_requested'])")
replace("'actual_source1of2_player1of1':num(av,'lyd_c2_source_yes')=='1'", "'actual_source2of2_player1of1':num(av,'lyd_c2_source_yes')=='2'")
text=re.sub(r"'11'", "'12'",text);changes.append({'exact_quoted_round_literal':{'11':'12'}})
text=re.sub(r'==\s*(58|59|70|71)\b',lambda m:'=='+{'58':'69','59':'70','70':'76','71':'77'}[m.group(1)],text);changes.append({'exact_revision_event_comparisons':{'58':'69','59':'70','70':'76','71':'77'}})
for old,new in [('0121-','0145-'),('0122-','0146-'),('0123-','0147-'),('0124-','0148-'),('0126-','0150-'),('review121','review145'),('cancel122','cancel146'),('result123','result147'),('ACK124','ACK148'),('fresh126','fresh150')]:replace(old,new)
for old,new in [('open111','open129'),('opened111','opened129'),('baseline107','baseline125'),('postCancel125','postCancel149'),('save125','save149'),('metadata125','metadata149'),('public59_native58','public70_native69'),('frame59_native58','frame70_native69'),('instance70','instance76'),('instance71','instance77'),('round11','round12'),('ballot11','ballot12'),('consent11','consent12'),('serial11','serial12')]:replace(old,new)
replace('nonce_serial11','nonce_serial12') if 'nonce_serial11' in text else None
replace('same-frozen-fifth-cancel','same-frozen-sixth-cancel');replace('actual-fifth-post-explicit-cancel-facts','actual-sixth-post-explicit-cancel-facts');replace('fifth-post-cancel-independent-readback','sixth-post-cancel-independent-readback')
replace('ACTUAL_RESULT3_CANCELLED_NO_SIGNATURE_JOIN_TRANSITION_OR_FEE','ACTUAL_RESULT3_CANCELLED_SOURCE_SIGNED1_NO_TARGET_REQUEST_SIGNATURE_JOIN_OR_FEE')
replace("'controls_same_profile_session_success':", "'fresh150_actor_alive':q['actor_alive'] is True,'controls_same_profile_session_success':")
replace("if not all(checks.values()):", "complete=read(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json')\nchecks.update({'complete_'+k:v for k,v in complete['all_binding_checks'].items()})\nif not all(checks.values()):")
lines=text.splitlines(True);matches=[line for line in lines if line.startswith(" 'actual_personal114_context':")]
if len(matches)!=1:raise ValueError('Need exact preceding controls facts row')
text=''.join(" 'actual_review145_only_wait_cancel':review,'actual_cancel146_selection':selection,'actual_result147_context':result_event,'actual_ACK148_selection':ack,'actual_fresh150_query_only_same_frame149':q,'new_initiation_or_hostrelease_proven_by150_query':False,\n" if line.startswith(" 'actual_personal114_context':") else line for line in lines)
replace("'political7_full_AST':", "'complete_Rite_Faith_AST_diff':pin(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json'),'political7_full_AST':")
replace("'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'human_report':", "'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'complete_Rite_Faith_AST_diff':pin(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json'),'human_report':")
start=text.index("with (HERE/'REPORT-zh.md').open");end=text.index("write('REPORT.json'",start)
human="""with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\\n') as out:out.write('第六案0149明确撤回后单次AST：nonce/serial12，result3=CANCELLED，active缺失；source_signed1真实保存，target_requested/target_signed缺失。玩家owner31254 source票与个人同意serial/nonce12、vote_yes1，source_yes2/total2、player_yes1/total1；sourceNPC65865 current12YES1，targetNPC65866 current12票及target_yes identity省略保留null，与0129票据相同，不合成NO0，不推定AI随机分支。\\n\\n159/169 proposal_owner移除，历史lockserial12/moving proposalserial12保留，retry/transitionCD缺失，reset_count5未变。wallet1543G/5650P/2200prestige、XP0、joins1/detaches2，两基线0125/0129均保持。保存stress缺失null，native0单独观察，expectednull。完整169/159 AST精确匹配观测C2变量行投影后保持；与0129只有proposal_owner移除，与0125只有lockserial/proposalserial更新到12；其余完整AST、相关Faith全AST、全部main/parent links、heads/完整tenets、政治7完整AST、actorlanded和三角色保护分支保持。\\n\\n原SDK145 typed76=lyd.220仅native3wait/native4cancel；146实际native4/option5→77，147 typed77=lyd.228，148 ACK→none；save149 exactSHA/bytes/pub70/native69/date53144712/paused/noevent/no pending绑定。SDK150当前普通JOIN query同70/69，actoralive/ready/cansendtrue/noevent；只query事实，不执行或给下轮发起信用。仅新save149一次AST，旧save用sealed缓存，不给最终JOIN、新reset或自然到期信用。\\n')\n"""
text=text[:start]+human+text[end:];dest=HERE/'finalize_cancel.py'
with dest.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
with (HERE/'FINALIZER-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'qualified_original':{'path':str(SOURCE),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'new_external_finalizer':{'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},'parameter_changes':changes,'human_report_replaced_with_actual_sixth_cancel_observations':True,'new_save_AST_reparsed':False,'product_or_source_mutations':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'new_finalizer':str(dest),'reuse_count':len(changes)},ensure_ascii=False))
