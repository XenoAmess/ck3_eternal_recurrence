"""Actual final PCM/source row binding. Small files only; no media decoding."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,copy,math,difflib,ast
R=Path('C:/ck3-war-episode04-research-20261004-a01')
W=R/'e4-final-review01-a01'
O=W/'actual-row-binding-a02'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
 p=Path(p);assert p.suffix.lower() in {'.py','.json','.jsonl','.md','.ass','.patch'} and p.stat().st_size<8*1024*1024
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def new(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  old=p.read_text(encoding='utf-8')
  expected=d if isinstance(d,str) else json.dumps(d,ensure_ascii=False,indent=2)+'\n'
  assert old==expected,('existing frozen source differs',p)
  return
 with p.open('x',encoding='utf-8',newline='\n') as f:
  if isinstance(d,str):f.write(d)
  else:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def frames(n):return math.ceil(Fraction(n*30,24000))
assert not O.exists()
oldsource=W/'candidate-a03/bc_pipeline.py'
s=oldsource.read_text(encoding='utf-8')
s=s.replace("require(chapters[chapter_id][0]['index'] == old_chapters[chapter_id][0]['index'],", "require((chapters[chapter_id][0]['index']['bytes'], chapters[chapter_id][0]['index']['sha256'].lower()) == (old_chapters[chapter_id][0]['index']['bytes'], old_chapters[chapter_id][0]['index']['sha256'].lower()),")
s=s.replace("end<=float(probe['format']['duration']) and end-begin>=n/FPS-1e-8,", "end<=float(probe['format']['duration'])+float(Fraction(visual['source_time_base']))+1e-8 and end-begin>=n/FPS-float(Fraction(visual['source_time_base']))-1e-8,")
s=s.replace("output=read(cue_root/'picture.bound-probe.json')['subject']", "output={'path':str(output_path), **read(cue_root/'picture.bound-probe.json')['subject']}")
s=s.replace("'picture':final_probe['subject'],", "'picture':{'path':str(final_path), **final_probe['subject']},")
ast.parse(s)
source=W/'candidate-a04/bc_pipeline.py';new(source,s)
new(W/'candidate-a04/checked_entry.py',(W/'candidate-a03/checked_entry.py').read_text(encoding='utf-8'))
new(W/'candidate-a04/entry-config.json',{'pipeline':pin(source)})
new(W/'candidate-a04/SOURCE-CHANGE-a04.patch',''.join(difflib.unified_diff(oldsource.read_text().splitlines(True),s.splitlines(True),fromfile='preserved-a03',tofile='candidate-a04')))
new(W/'candidate-a04/CORRECTIONS-a04.json',{'public_bound_probe_subject_path':'explicit actual output path + public subject bytes/SHA; one movie hash owner','stable_four_chapter_indices':'same current byte count/SHA, fresh directory path allowed; input bytes independently verified','millisecond_native_source_intervals':'one original 1/1000 source tick for timestamp quantization only; actual decoded source PTS/count and exact picture frames still independently checked','old_candidates_unchanged':True,'rendered':False})
template=read(R/'e4-final-BC-increment-preparation-a01/candidate-a02/input-pending.json')
audio_pin=pin(R/'e04-final-BC-audio-English-binding-a01/ROOT-DELIVERY.json');audio=read(audio_pin['path'])
sub_pin=pin(R/'e04-final-BC-subtitle-production-a01/actual-subtitles-a02/ROOT-DELIVERY.json');sub=read(sub_pin['path'])
master=read(sub['full_global']['timeline']['path'])
oldmovie=read(template['prior']['A_full_picture_receipt']['path']);prior={p['cue_id']:p for p in oldmovie['timeline']}
oldaudio=read(template['prior']['A_audio_delivery']['path'])
def rowmap(a):
 return {p['id']:(p,ch,idx) for ch in a['chapter_timeline'] for idx in [read(ch['index']['path'])] for p in idx['paragraphs']}
actual=rowmap(audio);old=rowmap(oldaudio)
changed={k for k in actual if actual[k][0]['subtitles_zh']!=old[k][0]['subtitles_zh']}
subchanged={k for k in actual if (actual[k][0]['subtitles_zh'],actual[k][0]['subtitles_en'])!=(old[k][0]['subtitles_zh'],old[k][0]['subtitles_en'])}
refresh={'C05-01','C05-15'}
assert changed=={'C05-04','C05-05','C05-08','C05-10','C05-14','C05-16','C06-10'}
O.mkdir()
config=read(R/'e4-A-only-production-portable-a01/candidate-a03/promo/ck3_native_war_ai/episode-04-march-logistics/picture-production-a01/project/promo-project.json')
config['project']['id']='ck3-war-ai-episode04-march-logistics-final-Review01'
config['project']['title']='CK3 战争 AI 第四期：行军、补给与休整'
for chapter in config['chapters']:
 for cue in chapter['cues']:
  p=actual[cue['id']][0];cue['narration']['zh']=p['subtitles_zh'];cue['subtitles']={'zh':p['subtitles_zh'],'en':p['subtitles_en']}
new(O/'promo-project-final-Review01.json',config)
catalog=read(R/'e4-final-source-pool-a01/Root-review-integration-a02/source-catalog-with-actual-Root-samples-a02.json')
entries={p['source_id']:copy.deepcopy(p) for p in catalog['source_entries'] if not p.get('replaced_cue_id') or p['replaced_cue_id'] in changed}
extra_root=pin(R/'root-S04-extra50-actual-source-review-a01/Root-sample-review.json')
last_root=pin(R/'root-r0176-S04-four-actual-coded-review-a01/receipt.json')
raw=read(R/'r0176-raw-abc-c-continuation-a04/result.json');raw=raw.get('body',raw)
for deliverypath,rootpin in [(W/'extra-C-S04-50s-a01/ROOT-DELIVERY-a01.json',extra_root),(R/'r0176-c-s04-terminal-window-a01/ROOT-DELIVERY-a01.json',last_root)]:
 delivery=read(deliverypath)
 for item in delivery['results']:
  report=read(item['report']['path'])
  pts=[p['source_pts'] for p in item['candidate_frames']];begin=pts[0]/1000
  n=300 if 'extra' in item['id'] else 360;end=begin+n/30
  review={'schema':'xar.e04.actual-sampled-window-admission.v1','source_binding':raw['raw'],'start_seconds':begin,'end_seconds_exclusive':end,'sampled_content_usable':True,'Root_actual_review':rootpin,'machine_clip_report':item['report'],'scope':'C +77 historical paused terminal post-state only','continuous_clean_review':False,'native_event_exact_PTS':False,'human_full_1x_review':False,'film_signoff':False}
  reviewpath=O/'source-reviews'/f"{item['id']}.json";new(reviewpath,review)
  entries[item['id']]={'source_id':item['id'],'maximum_frames':n,'prepared_clip':item['clip'],'prepared_clip_report':item['report'],'Root_actual_review':rootpin,'visible_date':'1067-05-21','visual':{'kind':'sealed-native-video','source':raw['raw'],'seal_receipt':pin(R/'r0176-raw-abc-c-continuation-a04/result.json'),'existing_media_audit':pin(R/'r0176-fourth-media-tools-a01/audit-attempt-a01/report.json'),'source_geometry':[1920,1080],'source_time_base':'1/1000','window_review':pin(reviewpath),'source_start_seconds':begin,'source_end_seconds_exclusive':end,'duration_frames':n,'playback_rate':1,'semantic_role':'C-actual-paused-terminal-state-no-arrival-action'}}
def label(key):
 if key.startswith('B-'):
  e=entries[key];return 'B · '+e['visible_date'].replace('-','年',1).replace('-','月')+'日 · 暂停回放 · 原速'
 if key.startswith('C-S04'):return 'C · 1067年5月21日 · 暂停终态回放 · 原速'
 if key.startswith('C-S02'):
  date='4月11日' if 'search' in key else '4月25日';return 'C · 1067年'+date+' · 暂停回放 · 原速'
 rawpath=entries[key]['visual']['source']['path']
 if 'r0173' in rawpath:return '独立资格样本 · 回放背景 · 原速'
 if 'r0168' in rawpath:return '独立合军样本 · 回放背景 · 原速'
 if 'r0165' in rawpath:return '独立补员样本 · 回放背景 · 原速'
 return 'A · 独立历史回放背景 · 原速'
for key,e in entries.items():e['visual']['visible_context_label']=label(key)
offset={k:0 for k in entries}
def take(key,n):
 e=entries[key];available=e['maximum_frames']-offset[key];n=min(n,available)
 if not n:return None
 v=copy.deepcopy(e['visual']);start=e['visual']['source_start_seconds'];i=offset[key]
 # Actual native PTS use the original millisecond clock. No invented frames.
 absolute_first_frame=round(start*30)
 begin=round((absolute_first_frame+i)*1000/30)/1000
 end=round((absolute_first_frame+i+n)*1000/30)/1000
 if i+n==e['maximum_frames']:end=e['visual']['source_end_seconds_exclusive']
 v.update(source_start_seconds=begin,source_end_seconds_exclusive=end,duration_frames=n,source_id=key,source_frame_offset_within_reviewed_window=i)
 v.pop('zoom',None);offset[key]+=n;return v
def allocated(pool,n):
 out=[]
 for item in pool:
  key,limit=item if isinstance(item,tuple) else (item,n)
  if n==0:break
  v=take(key,min(n,limit))
  if v:out.append(v);n-=v['duration_frames']
 assert n==0,('actual unique source capacity exhausted',n,pool)
 return out
notes={
 'C05-01':('三个方案，三种记录',['A：整军直走；已到伦敦','B：拆军休整；第38日门禁停止','C：绕道；首次观测第77日到达','C 多次采样偏差，严格比较未授予','本次没有 ABC 策略赢家']),
 'C05-04':('B：真实拆军与站点',['B 原编制 27 团拆为 15＋12 团','初始人数 3337＋3342＝6679','主军留原站；子军合法赴休整站','完整 ID 与 37 项 DATA 逐行核对','背景另标独立资格样本，非本次动作']),
 'C05-05':('C：首次观测到达',['C 第77日首次观测伦敦；窗口(75,77]','主力原始编制 6679→6689，净＋10','原27团／最大6747／统帅身份保持','库存110.38→101.90；容量300','当前1%读数，不是已死亡账本','多次采样偏差；严格比较未授予']),
 'C05-08':('B：两个补给窗口',['子军：第20→21日，110.38→100','以上容量回到100；允许零或负变更','主军：第31→32日，106.14→126.14','主军低于容量300，实际增加20','两窗口分开，不称同时更新','12秒片段为写回后的暂停状态']),
 'C05-10':('B：合军加权与上限',['B 两侧真实库存按原生定点顺序计算','截断前期望113.06109，合后上限100','实际库存100：本次数学核验通过','原27团保留，另出现新1／1团','统帅27357→33388；变化原因未知','背景为状态回放，不是合军点击时刻']),
 'C05-14':('B 停止；C 比较限制',['B 第38日门禁停止，剩52日','新增第28团1／1、统帅变化原因未知','B 无可比较的伦敦终态','C 多次计划1日、实际2日采样','严格 ABC 比较未授予；没有赢家','下面回到整军直走的 A']),
 'C05-15':('A：人数与库存终态',['此段回到 A：第51日首次观测伦敦','首次到达窗口(49,51]，非精确瞬间','主力原27团：6679→6689，净＋10','最大6747；库存110.38→106.14','整数增长不等于逐次补员／死亡账本']),
 'C05-16':('A／C：现金净差',['先讲 A：637.55→621.48，净−16.06','后讲 C：同起点，终态现金净−15.82','现金差不是已证行军付款或登船费','中间净−17／＋0.25，原因账本未知','B 门禁停止；C 严格比较未授予','本次不宣布 ABC 赢家']),
 'C06-10':('本次证据与边界',['A 到达；C 第77日首次观测到达','B 第38日门禁停止，无伦敦可比','主力原始编制按完整身份核对','C 多次采样偏差，严格比较未授予','库存、人数、现金净差分开记录','饥饿死亡／付款因果仍无应用账本'])}
plans={
 'C05-04':['B-S01-day6','REPLACED-C05-04-00','REPLACED-C05-04-01'],
 'C05-05':[f'C-S04-extra-terminal-context-{i:02}' for i in range(5)]+['C-S04-actual-terminal-state-last360'],
 'C05-08':['B-S01-day21','REPLACED-C05-08-00','REPLACED-C05-08-01','REPLACED-C05-08-02'],
 'C05-10':['B-S01-day27','B-S02-Main-positive',('B-S02-Postmerge-exception',180),'REPLACED-C05-10-00','REPLACED-C05-10-01','REPLACED-C05-10-02'],
 'C05-14':['B-S02-Postmerge-exception','B-S02-Child-return','REPLACED-C05-14-00','REPLACED-C05-14-01','C-S02-London-centered-sea-context-search','C-S02-actual-tail-date-pending','REPLACED-C05-10-02','REPLACED-C05-04-01','REPLACED-C05-08-02','REPLACED-C05-05-00'],
 'C05-16':['REPLACED-C05-16-00','REPLACED-C05-16-01','REPLACED-C05-16-02','C-S04-actual-terminal-state-last360','REPLACED-C05-05-00','REPLACED-C05-05-01'],
 'C06-10':['REPLACED-C06-10-00','REPLACED-C06-10-01','REPLACED-C05-05-01','REPLACED-C05-04-01','REPLACED-C05-08-02','REPLACED-C05-10-02','REPLACED-C05-05-00']}
cursor=samples=0;rows=[];allocation=[]
for p in master['paragraphs']:
 key=p['id'];a=actual[key][0];n=a['chapter_end_sample']-a['chapter_start_sample'];oldn=prior[key]['actual_picture_end_frame']-prior[key]['actual_picture_start_frame'];count=frames(samples+n)-cursor if key in changed|refresh else oldn
 assert abs(cursor-frames(samples))<=1 and abs(cursor+count-frames(samples+n))<=1
 if key in changed|refresh:
  title,card=notes[key]
  if key=='C05-14':
   bridge=entries['REPLACED-C05-10-02']['maximum_frames']-offset['REPLACED-C05-10-02']
   prefix=['B-S02-Postmerge-exception','B-S02-Child-return','REPLACED-C05-14-00','REPLACED-C05-14-01','C-S02-London-centered-sea-context-search','C-S02-actual-tail-date-pending']
   cap=sum(entries[j]['maximum_frames']-offset[j] for j in prefix)
   plans[key]=prefix+[('REPLACED-C05-04-01',count-cap-bridge),'REPLACED-C05-10-02']
  row={'id':key,'text_zh':a['subtitles_zh'],'text_en':a['subtitles_en'],'title':title,'source_label':'研究记录 · 各画面独立标明回放主体','record_note':card,'duration_frames':count,'visuals':allocated(plans[key],count) if key in changed else [],'source_scope':'real historical post-state background; no native-event join','actual_outcome_credit':False}
  if key=='C05-15':row['source_label']='A · 独立历史回放背景 · 原速'
  rows.append(row)
 allocation.append({'id':key,'mode':'new-native-picture' if key in changed else 'derived-picture-card-refresh' if key in refresh else 'exact-dry-picture-reuse','frames':count,'start_frame':cursor,'end_frame':cursor+count,'start_sample':samples,'end_sample':samples+n})
 cursor+=count;samples+=n
assert samples==41658624 and cursor-frames(samples) in (0,1)
assert all(sum(v['duration_frames'] for v in r['visuals'])==r['duration_frames'] for r in rows if r['id'] in changed)
new(O/'picture-rows.json',rows);new(O/'allocation.json',{'samples':samples,'seconds':samples/24000,'frames':frames(samples),'rows':allocation,'real_last_frames_to_trim':cursor-frames(samples)})
new(O/'source-catalog.json',{'schema':'xar.e04.actual-final-source-catalog.v1','source_entries':list(entries.values()),'actual_extra50_Root_review':extra_root,'actual_last12_Root_review':last_root,'source_read_operations':0,'fullclean_or_event_or_human1x_credit':False})
final={'project_config':pin(O/'promo-project-final-Review01.json'),'claim_ledger':pin(R/'e04-final-BC-story-a01/actual-story-a02/claim-ledger-final-BC-a06.json'),'audio_delivery':audio_pin,'subtitle_delivery':sub_pin,'C05_relative_delivery':sub['affected_chapter_relative_deliveries']['E4-05'],'C06_relative_delivery':sub['affected_chapter_relative_deliveries']['E4-06'],'C_terminal_receipt':pin(R/'root-r0176-C-terminal-London-a01/terminal.json'),'C_closed_media_receipt':pin(R/'r0176-c-s04-terminal-window-a01/ROOT-DELIVERY-a01.json'),'release_probe':pin(W/'release-probe-a01.json'),'picture_rows':rows,'picture_rows_json':pin(O/'picture-rows.json'),'Root_final_story_freeze':None}
template['final']=final;template['purpose']='actual-final-Review01-awaiting-Root-picture-row-freeze';new(O/'pipeline-input-PENDING-Root-review.json',template)
ledger=read(final['claim_ledger']['path']);claims={p['id']:p for p in ledger['claims']}
approved={k:{'zh_sha256':hashlib.sha256(v[0]['subtitles_zh'].encode()).hexdigest(),'en_sha256':hashlib.sha256(v[0]['subtitles_en'].encode()).hexdigest(),'claim_status':claims[k]['status']} for k,v in actual.items()}
for k,v in actual.items():assert v[0]['subtitles_zh']==claims[k]['claim_summary']
gate={'schema':'xar.e04.final-story-review-freeze.v1','approved_for_review_render':False,**{k:v for k,v in final.items() if k not in {'picture_rows','Root_final_story_freeze'}},'C_sampling_deviation_review':pin(R/'e04-final-BC-story-a01/actual-story-a02/sources/C-terminal-Root-review.json'),'audio_changed_ids':sorted(changed),'subtitle_changed_ids':sorted(subchanged),'picture_refresh_ids':sorted(refresh),'approved_paragraphs':approved,'B_status':'STOPPED_GATE_INCOMPLETE','B_London_comparable':False,'winner':None,'C_controlled_comparison':'NOT_GRANTED','human_full_1x_review':False,'human_signoff':False,'pipeline_source':pin(source),'Chinese_actual_NO_BLOCK':pin(R/'e04-final-BC-Root-actual-source-review-a01/Root-NO-BLOCK.json'),'English_actual_NO_BLOCK':pin(R/'e04-final-BC-Root-actual-English-review-a02/Root-English-NO-BLOCK.json'),'source_catalog':pin(O/'source-catalog.json'),'reviewed_utc':None,'Root_story_reviewer':None}
new(O/'Root-final-row-review-PENDING.json',gate)
lines=['# 实际最终 Review01 画面行','',f'实际中文 PCM：{samples} 样本 / {samples/24000:.3f} 秒；全片 {frames(samples)} 帧。52 稳定段及8个未变C05干净制作段沿用原字节，7段新声画＋2段卡面覆盖。','', '所有回放1×，每个原片时间窗唯一。原生现场数值由对应卡与字幕说明；另一个案例只作明确标注的独立背景。未授完整连续clean、动作时刻、人工1×或成片签核。','']
for row in rows:
 lines += [f"## {row['id']} · {row['title']} · {row['duration_frames']/30:.3f} 秒",'',row['text_zh'],'','卡面：'+'；'.join(row['record_note']),'','| 段内秒 | 原片窗口秒 | 时长 | 观众可见标签 | 内部来源 |','|---|---|---|---|---|']
 t=0
 for v in row['visuals']:
  n=v['duration_frames'];lines.append(f"| {t/30:.3f}→{(t+n)/30:.3f} | {v['source_start_seconds']:.3f}→{v['source_end_seconds_exclusive']:.3f} | {n/30:.3f} | {v['visible_context_label']} | {v['source_id']} |");t+=n
 if not row['visuals']:lines.append('| 全段 | 原已渲染动态MOV | 同实际PCM | '+row['source_label']+' | 仅整块覆盖旧卡面；不延长、不补帧 |')
 lines.append('')
new(O/'ROOT-READABLE-PICTURE-ROWS.md','\n'.join(lines)+'\n')
receipt={'schema':'xar.e04.actual-final-row-binding-delivery.v1','state':'ACTUAL_ROWS_READY_ROOT_REVIEW_PENDING','rows':pin(O/'picture-rows.json'),'readable_rows':pin(O/'ROOT-READABLE-PICTURE-ROWS.md'),'gate_PENDING':pin(O/'Root-final-row-review-PENDING.json'),'pipeline_input_PENDING':pin(O/'pipeline-input-PENDING-Root-review.json'),'pipeline':pin(source),'entry':pin(W/'candidate-a04/checked_entry.py'),'source_catalog':pin(O/'source-catalog.json'),'final_project_config':final['project_config'],'samples':samples,'seconds':samples/24000,'frames':frames(samples),'source_frame_capacity':sum(e['maximum_frames'] for e in entries.values()),'source_frames_used':sum(offset.values()),'remaining_source_frames':{k:entries[k]['maximum_frames']-v for k,v in offset.items() if entries[k]['maximum_frames']>v},'native_media_read_operations':0,'TTS_operations':0,'render_operations':0,'Root_approved_for_render':False,'human_signoff':False}
new(O/'ROOT-DELIVERY.json',receipt)
print(json.dumps({'delivery':pin(O/'ROOT-DELIVERY.json'),**receipt},ensure_ascii=False,indent=2))
