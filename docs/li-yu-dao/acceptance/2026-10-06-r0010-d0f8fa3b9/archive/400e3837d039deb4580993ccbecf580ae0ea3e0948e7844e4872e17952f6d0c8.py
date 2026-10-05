import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'r10-actual-fourth-open-join-readback-20261005-001/finalize_open.py'
raw=SOURCE.read_bytes();text=raw.decode('utf-8')
changes=[]
def replace(old,new):
    global text
    count=text.count(old)
    if not count:raise ValueError('Missing qualified finalizer anchor '+old)
    text=text.replace(old,new);changes.append({'old':old,'new':new,'occurrences':count})
replace('r10-actual-third-post-cancel-readback-20261005-001','r10-actual-fourth-post-cancel-readback-20261005-001')
for old,new in [('0086-','0109-'),('0087-','0110-'),('0089-','0112-')]:replace(old,new)
replace('87e2fdfb02e76bea3755285e6cf4bfcd7ec0588d5652e92bf83e548949e8de20','929e9d361ac0c3903fb1822248cf50b5d1a3a13d80d3c901310bc6422e29e62d')
text=re.sub(r"'(9|10)'",lambda m:"'"+{'9':'10','10':'11'}[m.group(1)]+"'",text);changes.append({'exact_quoted_round_literals':{'9':'10','10':'11'}})
text=re.sub(r'==\s*(38|39|40|41|63)\b',lambda m:'=='+{'38':'49','39':'50','40':'51','41':'52','63':'69'}[m.group(1)],text);changes.append({'exact_revision_event_comparisons':{'38':'49','39':'50','40':'51','41':'52','63':'69'}})
for old,new in [('before82','before107'),('after88','after111'),('metadata88','metadata111'),('save88','save111'),('fresh86','fresh109'),('send87','send110'),('typed89','typed112'),('event63','event69')]:replace(old,new)
replace('round10','roundNEW');replace('round9','round10');replace('roundNEW','round11')
replace('nonce9_to10','nonce10_to11');replace('serial9_to10','serial10_to11')
replace('public41_native40','public52_native51');replace('samepub39_native38','samepub50_native49');replace('after39native38','after50native49');replace('snapshot40native39','snapshot51native50');replace('pub41native40','pub52native51')
replace('ordinal3_parent2','ordinal4_parent3');replace('actual fourth-open checks','actual fifth-open checks')
replace('actual-fourth-JOIN-proposal-opened-pair-facts','actual-fifth-JOIN-proposal-opened-pair-facts');replace('ACTUAL_FOURTH_PROPOSAL_OPENED_ROUND10_TARGET_YES_NOT_PROVEN_NOT_FINAL_JOIN','ACTUAL_FIFTH_PROPOSAL_OPENED_ROUND11_NPC_YES_NOT_PROVEN_NOT_FINAL_JOIN');replace('fourth-open-independent-readback','fifth-open-independent-readback')
replace("'actual_round_diff':", "'all_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_round_diff':")
start=text.index("with (HERE/'REPORT-zh.md').open");end=text.index("write('REPORT.json'",start)
human="""with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\\n') as out:out.write('第五opening0111单次AST对sealed0107缓存：nonce/serial10→11，active1(tick365)，source_signed、target_requested、target_signed缺失；result identity省略保留null。NPC65865/65866 current owner31254/serial/nonce11，但两vote_yes identity均省略，不合成YES1或NO0。source/target/player_yes identity均省略，total2/1/1；玩家旧票及个人同意10不计11。159/169 ownerlocks31254/serial11，retry/transitionCD缺失，reset_count5未变，无新reset。\\n\\nwallet1543/5650/2200、XP0、joins1/detaches2不变，savedstress缺失null/native0单独观察，expectednull；角色仍169/106、HoR31254。Faithmain/Riteparent links、selected heads/完整tenet-doctrine rows、政治7完整AST、actor landed及三角色保护分支保持。\\n\\nFresh109 exactSHA929e...同107frame50/native49；newsend110 ordinal4/UUID9e0a5f40... parent3/same6identity/permit exactSHAa2c0a17d...均核对。result pending/after50native49/businessfalse与wrapper snapshot51native50/event69分别记录。save111actualpub52native51与typed112同帧event69=lyd.200/root31254。只给第五PROPOSAL_OPENED，无最终JOIN信用；旧save不重解析。\\n')\n"""
text=text[:start]+human+text[end:]
dest=HERE/'finalize_open.py'
with dest.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
with (HERE/'FINALIZER-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'qualified_original':{'path':str(SOURCE),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'new_external_finalizer':{'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},'parameter_changes':changes,'human_report_replaced_with_actual_fifth_open_observations':True,'new_save_AST_reparsed':False,'product_or_source_mutations':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'new_finalizer':str(dest),'reuse_count':len(changes)},ensure_ascii=False))
