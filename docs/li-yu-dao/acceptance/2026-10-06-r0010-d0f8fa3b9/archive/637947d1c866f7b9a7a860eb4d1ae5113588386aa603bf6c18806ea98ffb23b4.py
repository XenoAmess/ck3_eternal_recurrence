import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'r10-actual-fourth-open-join-readback-20261005-001/finalize_open.py';raw=SOURCE.read_bytes();text=raw.decode('utf-8');changes=[]
def replace(old,new):
    global text
    count=text.count(old)
    if not count:raise ValueError('Missing qualified finalizer anchor '+old)
    text=text.replace(old,new);changes.append({'old':old,'new':new,'occurrences':count})
replace('r10-actual-third-post-cancel-readback-20261005-001','r10-actual-fifth-post-cancel-readback-20261005-001')
for old,new in [('0086-','0127-'),('0087-','0128-'),('0089-','0130-')]:replace(old,new)
replace('87e2fdfb02e76bea3755285e6cf4bfcd7ec0588d5652e92bf83e548949e8de20','b233c9ed3ece500c5bc68357de621fea8b6c37ba72142dc3ffb302f4bcf940f6')
text=re.sub(r"'(9|10)'",lambda m:"'"+{'9':'11','10':'12'}[m.group(1)]+"'",text);changes.append({'exact_quoted_round_literals':{'9':'11','10':'12'}})
text=re.sub(r'==\s*(38|39|40|41|63)\b',lambda m:'=='+{'38':'58','39':'59','40':'60','41':'61','63':'74'}[m.group(1)],text);changes.append({'exact_revision_event_comparisons':{'38':'58','39':'59','40':'60','41':'61','63':'74'}})
for old,new in [('before82','before125'),('after88','after129'),('metadata88','metadata129'),('save88','save129'),('fresh86','fresh127'),('send87','send128'),('typed89','typed130'),('event63','event74')]:replace(old,new)
replace('round10','round12');replace('round9','round11')
replace('nonce9_to10','nonce11_to12');replace('serial9_to10','serial11_to12')
replace('public41_native40','public61_native60');replace('samepub39_native38','samepub59_native58');replace('after39native38','after59native58');replace('snapshot40native39','snapshot60native59');replace('pub41native40','pub61native60')
replace('ordinal3_parent2','ordinal5_parent4');replace('Actual fourth-open checks','Actual sixth-open checks')
replace('actual-fourth-JOIN-proposal-opened-pair-facts','actual-sixth-JOIN-proposal-opened-pair-facts');replace('ACTUAL_FOURTH_PROPOSAL_OPENED_ROUND10_TARGET_YES_NOT_PROVEN_NOT_FINAL_JOIN','ACTUAL_SIXTH_PROPOSAL_OPENED_ROUND12_TARGET_YES_NOT_PROVEN_NOT_FINAL_JOIN');replace('fourth-open-independent-readback','sixth-open-independent-readback')
replace("'actual_round_diff':", "'root_plan_result_refs':{'plan':controls['root_player_plan']['ref'],'result':controls['root_player_result']['ref'],'typed130_record_used':controls['typed130_record_used'],'other_five_callbacks_not_used_as_save129_business_result':True},'all_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_round_diff':")
start=text.index("with (HERE/'REPORT-zh.md').open");end=text.index("write('REPORT.json'",start)
human="""with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\\n') as out:out.write('第六opening0129单次AST对sealed0125缓存：nonce/serial11→12，active1(tick365)，source_signed、target_requested、target_signed缺失，result identity省略保留null。sourceNPC65865 current owner31254/serial/nonce12、vote_yes1；targetNPC65866 current12但票identity省略，保持null，不合成NO0。source_yes1/total2；target/player_yes identity省略、total1/1；玩家旧票和个人同意11不计12。159/169 ownerlocks31254/serial12，retry/transitionCD缺失，reset_count5未变。\\n\\nwallet1543/5650/2200、XP0、joins1/detaches2保持，savedstress缺失null/native0分开，expectednull；角色仍169/106、HoR31254。全Faithmain/Riteparent links、selected heads/完整tenet-doctrine rows、政治7完整AST、actor landed及三角色保护分支保持。\\n\\nFresh127同125frame59/native58；newsend128 ordinal5/UUID1d9cf9c7... parent4/same6/permit exactSHA350483fb...绑定。pendingresult/after59native58/businessfalse与wrapper snapshot60native59/event74分别保全。保存129pub61/native60；ROOT PLAN.exact与RESULT原字节绑定，从RESULT唯一sequence130取得原SDK exactSHA788ee7... typed74=lyd.200/root31254同保存帧。RESULT其余131–135不作save129业务结果；只认PROPOSAL_OPENED，无最终JOIN，旧save不重解析。\\n')\n"""
text=text[:start]+human+text[end:];dest=HERE/'finalize_open.py'
with dest.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
with (HERE/'FINALIZER-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'qualified_original':{'path':str(SOURCE),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'new_external_finalizer':{'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},'parameter_changes':changes,'human_report_replaced_with_actual_sixth_open_observations':True,'new_save_AST_reparsed':False,'product_or_source_mutations':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'new_finalizer':str(dest),'reuse_count':len(changes)},ensure_ascii=False))
