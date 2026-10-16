"""Seal actual R0180 six-image review and a bounded intake copy plan.

No source video reads, capture context, SDK, desktop, game, provider or signoff.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json

PREP=Path(__file__).resolve().parent
PKG=PREP.parent
BASE=PKG.parent
OUT=PKG/'attempt-a01'
DEADLINE=datetime.fromisoformat('2026-10-16T07:45:01.597+00:00')
LIMIT=8388608
META_LIMIT=131072

def require(ok,message):
    if not ok:raise RuntimeError(message)

def now():return datetime.now(timezone.utc).isoformat()

def load(path):
    require(path.is_file() and not path.is_symlink() and path.suffix=='.json' and path.stat().st_size<=300000,'bounded existing JSON required')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def pin(path):
    require(path.is_file() and not path.is_symlink() and path.suffix in ('.json','.py','.txt','.bin') and path.stat().st_size<=300000,'bounded text/code/stdio only; raw hash forbidden')
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def amounts():
    files=[p for p in PKG.rglob('*') if p.is_file()]
    return {'all_derived_bytes':sum(p.stat().st_size for p in files),'metadata_bytes':sum(p.stat().st_size for p in files if p.suffix.lower() not in ('.jpg','.jpeg'))}

require(datetime.now(timezone.utc)<DEADLINE,'original fixed deadline reached')
report=load(OUT/'report.json')
require(report['state']=='PASS_RAW_METADATA_AND_STRICT_DECODE_ONLY' and report['decoded_frames']==1350,'actual single-pass machine audit required')
require([s['source_frame_ordinal'] for s in report['samples']]==[0,120,240,360,540,1200] and all(s['encoded_sample_width']==1600 and s['encoded_sample_height']==900 for s in report['samples']),'wrong actual sample frames or dimensions')
require((report['metadata_probe_count'],report['strict_whole_decode_count'],report['extra_seek_count'],report['raw_SHA_reads'],report['raw_reencodes'])==(1,1,0,0,0),'unexpected media actions')
closure=load(BASE/'raw-land-arrival-a01/result.json')
start=datetime.fromisoformat(closure['started_at_utc'])
identity=load(BASE/'runtime-actor-identity.actual-a01.json')
require(identity['source_head']==report['actual_source_head']=='c4992c304d196135d9590799d69ffb3c9f5510e6' and identity['pid']==16736 and identity['process_creation_filetime_100ns']==134365825176284454 and identity['connection_generation']==1,'runtime or source binding changed')
days=[]
for n,date in [(3,53147544),(4,53147568),(5,53147592)]:
    path=BASE/f'normal-county-preparation-a01/day-{n:02d}.complete.actual.json';d=load(path)
    require(d['day']==n and d['date_raw']==date and d['normal_preparation_only'] is True and d['R04_positive_claim'] is False and d['actual_army']['army_id']==18,'actual exact day differs')
    days.append({'source':pin(path),'at_utc':d['at_utc'],'receipt_minus_recorder_started_seconds':(datetime.fromisoformat(d['at_utc'])-start).total_seconds(),'day':n,'date_raw':date,'actual_army':d['actual_army'],'clock':d['clock']})
for d in days[:2]:require(d['actual_army']['current_province_id']==2635 and d['actual_army']['route_province_ids']==[2645] and d['actual_army']['army_state']=='sieging','prearrival state differs; do not rename sieging as moving')
require(days[-1]['actual_army']['current_province_id']==2645 and days[-1]['actual_army']['route_read_status']=='complete_empty' and days[-1]['actual_army']['army_state']=='regular' and days[-1]['actual_army']['in_combat'] is False,'actual arrival state differs')
card_path=BASE/'R04-ARRIVAL.actual-a01.json';card=load(card_path)
require(card['status']=='HOLD_NO_R04_CARD_POSITIVE' and card['R04_positive_accepted'] is False and card['precondition_observations']['native_condition_passes'] is False,'R04 actual HOLD boundary differs')
release=load(PKG/'release-check-a01/result.json')
require(release['returncode']==0 and release['actual_latest_official_tag']=='v0.2.1' and release['installed_matches_latest'] is True,'latest official release no longer matches this attempt')
native={'schema':'xar.e04.R0180-land-arrival-native-boundary.actual.v1','at_utc':now(),'source_head':report['actual_source_head'],'run_id':report['actual_run_id'],'actual_runtime':{'pid':16736,'create_filetime_100ns':134365825176284454,'generation':1,'actor':31254,'army_id':18,'episode':identity['episode_run_id']},'raw_identity_reused':report['raw_identity_reused'],'recorder_started_at_utc':closure['started_at_utc'],'exact_day_receipts':days,'actual_R04_card':pin(card_path),'R04_status':card['status'],'R04_positive_accepted':False,'native_condition_passes':False,'county_positive_physical_event_count':card['county_positive_physical_event_count'],'complete_window_available':card['complete_window_available'],'R04_no_matching_event_is_not_observed_zero_total':card['no_matching_event_is_not_observed_zero_total'],'normal_preparation_only':True,'Root_reported_arrival_after_recording_ACK_seconds':15.74,'Root_reported_ACK_delta_is_not_encoded_event_PTS':True,'wall_to_encoded_PTS_calibrated':False,'exact_first_arrival_pixel_PTS':None,'human_approval':False}
write(PKG/'native-boundary.actual-a01.json',native)
dates=['公元1067年1月26日','公元1067年1月26日','公元1067年1月27日','公元1067年1月28日','公元1067年1月29日','公元1067年1月29日']
right_totals=[1431,1431,1416,1402,1371,1371]
right_event=[246,246,231,217,186,186]
samples=[]
for i,(s,date) in enumerate(zip(report['samples'],dates)):
    arrived=i>=4
    samples.append({**s,'AI_sample_viewed':True,'AI_visual_observation':{'bottom_game_date':date,'selected_army_soldiers_text':'1184','selected_army_supply_text':'300/300','selected_army_panel_state_text':'待命' if arrived else '围攻','selected_army_attrition_icon_text':'0%' if arrived else '1%','map_army_position':'首段后新位置' if arrived else 'Palermo附近旧位置','map_siege_graphic':'不再见旧围城条' if arrived else '旧位置附近可见围城图形','right_military_panel_open':True,'right_military_total_soldiers_text':right_totals[i],'right_event_troops_text':right_event[i],'right_panel_scope':'总军力/事件兵为其他集合，不是左下选中1184人的同一计数','pause_banner_visible':True,'tooltip_or_system_modal_visible':False,'old_notification_panel_visible':False,'composition_limit':'右军事面板约占右侧三成画幅，左下Army面板遮部分地图；目标军旗与前后位置仍可见。'},'Root_visual_review':None,'human_approval':False,'native_event_exact_frame_claimed':False})
spans=[{'id':'R180-old-position-siege-context','in_seconds':0,'out_seconds':8,'support_seconds':[0,4,8],'purpose':'开场地理与军队上下文候选；1184人、300/300，原生/画面围攻状态，不能改称已处于moving UI。'}, {'id':'R180-arrival-before-after','in_seconds':12,'out_seconds':18,'support_seconds':[12,18],'purpose':'原位置围攻面板→新位置待命面板、Jan28→Jan29；仅授到达视觉bracket(12,18]秒。'}, {'id':'R180-arrived-stationary','in_seconds':18,'out_seconds':40,'support_seconds':[18,40],'purpose':'到达后1184人/300/300/待命留屏；优先剪短，右军事面板持续作为构图限制。'}]
for span in spans:
    span.update({'source_time_base':report['time_base'],'in_PTS_ticks':int(span['in_seconds']*1000),'out_PTS_ticks':int(span['out_seconds']*1000),'state':'CANDIDATE_PENDING_ROOT_CONTINUOUS_REVIEW','clean_spans_certified':False,'human_1x_review':False,'human_signoff':False})
cuts={'schema':'xar.e04.R0180-land-arrival-visual-review.actual.v1','state':'MACHINE_MEDIA_PASS_ACTUAL_ARRIVAL_SAMPLES_CANDIDATE_ONLY','at_utc':now(),'raw_identity_reused':report['raw_identity_reused'],'machine_report':pin(OUT/'report.json'),'native_boundary':pin(PKG/'native-boundary.actual-a01.json'),'samples':samples,'span_candidates':spans,'arrival_visual_bracket_seconds':'(12,18]','exact_first_transition_PTS':None,'marks_scope':'AI proposed source-PTS editorial marks only; no pre-existing clean capture marks/timeline supplied or fabricated','R02_R03_opening_routing':{'opening':'Candidate for Palermo geography/actual Army18/arrival contrast; retain or later crop right military panel only under compositor policy.','R02':'Shared land-route/arrival illustration candidate; native day3/4 have route[2645] but state=sieging, so no newly demonstrated moving-UI or complete chapter proof.','R03':'Shared actual before/after arrival illustration candidate; exact chapter-specific gameplay proof and acceptance remain with intake.','qualified_R02_R03_positive_credited_here':False},'scope_limits':['右军力总数和事件兵变化不是选中Army18的县损耗；选中1184人六样本均未变。','骷髅1%到0%的UI显示不能充当实际物理扣兵；R04 HOLD/conditionfalse和窗口不完整保留。','0/4/8/12样本是sieging/围攻，不能改称native moving。','6帧不是连续观看；所有样本暂停不能推断全区间一直暂停。','不自动提高dynamic0/11，不记录human1×或approval。'],'R04_positive_accepted':False,'dynamic_counter_auto_increment':0,'continuous_clean_review':False,'human_1x_review':False,'human_signoff':False,'adapter_GREEN_capture_report_created':False,'raw_SHA_reads':0,'raw_reencodes':0,'metadata_probe_count':1,'strict_whole_decode_count':1,'extra_seek_count':0,'new_SDK_desktop_game_main_provider_signoff_actions':0,'sealing_source':pin(Path(__file__))}
write(PKG/'visual-review-and-spans.actual-a01.json',cuts)

small_paths=[PREP/'audit_r0180_finished_raw_a01.py',PREP/'actual-finished-binding-a01.json',Path(__file__),OUT/'report.json',OUT/'ACTUAL-METADATA.json',OUT/'PLAN-AND-INPUTS.json',OUT/'strict-whole-decode-and-samples/argv.json',OUT/'strict-whole-decode-and-samples/result.json',PKG/'native-boundary.actual-a01.json',PKG/'visual-review-and-spans.actual-a01.json',PKG/'release-check-a01/result.json',PKG/'release-check-a01/stdout.json']
small_files=[]
for p in small_paths:
    item=pin(p);small_files.append({'source_path':str(p),'relative_path':str(p.relative_to(PKG)).replace('\\','/'),'bytes':item['bytes'],'sha256':item['sha256']})
for s in report['samples']:
    small_files.append({'source_path':s['image']['path'],'relative_path':'attempt-a01/samples/'+Path(s['image']['path']).name,'bytes':s['image']['bytes'],'sha256':s['image']['sha256']})
plan={'schema':'xar.e04.R0180-intake-small-copy-plan.actual.v1','at_utc':now(),'state':'ACTUAL_SOURCE_FILES_PINNED_COPY_PLAN_ONLY','source_root':str(PKG),'target_root':None,'target_chosen_and_copy_owned_by_intake':True,'files':small_files,'planned_copy_bytes':sum(f['bytes'] for f in small_files),'raw_identity_reference_only_do_not_copy':report['raw_identity_reused'],'raw_hash_reused_from_actual_recorder':True,'actual_copy_performed_here':False,'clip_creation_performed_here':False,'render_dynamic_credit_or_human_approval':False,'append_only_intake_instruction':'Copy only these bounded code/text/JPEG files into a fresh intake attempt and verify their small pins; consume exact raw identity separately without hashing the large original again. Do not convert samples into continuous-clean or R04 approval.'}
write(PKG/'INTAKE-SMALL-COPY-PLAN.actual-a01.json',plan)
require(amounts()['metadata_bytes']<META_LIMIT-8192,'metadata reserve insufficient before root delivery')
delivery={'schema':'xar.e04.R0180-root-media-delivery.actual.v1','at_utc':now(),'state':cuts['state'],'raw_identity_reused':report['raw_identity_reused'],'machine_report':pin(OUT/'report.json'),'native_boundary':pin(PKG/'native-boundary.actual-a01.json'),'visual_review_and_spans':pin(PKG/'visual-review-and-spans.actual-a01.json'),'intake_small_copy_plan':pin(PKG/'INTAKE-SMALL-COPY-PLAN.actual-a01.json'),'latest_official_release_check':pin(PKG/'release-check-a01/result.json'),'media_summary':'45.000s /1350frames / native2560x1440@30 H264 yuv420p silent; 6 actual1600x900 JPEG samples from the only strict full decode','sample_seconds':[0,4,8,12,18,40],'AI_samples_actually_viewed':6,'arrival_visual_bracket_seconds':'(12,18]','right_military_panel_composition_limit':True,'R04_status':'HOLD_NO_R04_CARD_POSITIVE','dynamic_counter_auto_increment':0,'continuous_clean_review':False,'human_1x_review':False,'human_signoff':False,'raw_SHA_reads':0,'raw_reencodes':0,'metadata_probe_count':1,'strict_full_decode_count':1,'extra_seek_count':0,'new_SDK_game_desktop_main_provider_OneDrive_actions':0,'budget_pool':'scene original other256MiB, Root allocation8MiB; global quota unchanged','all_derived_limit_bytes':LIMIT,'metadata_limit_bytes':META_LIMIT,'actual_amounts_before_receipt':amounts(),'fixed_deadline_utc':DEADLINE.isoformat()}
write(PKG/'ROOT-MEDIA-DELIVERY.actual-a01.json',delivery)
actual=amounts()
require(actual['all_derived_bytes']<=LIMIT and actual['metadata_bytes']<=META_LIMIT,'actual combined derived or metadata budget exceeded')
print(json.dumps({'delivery':pin(PKG/'ROOT-MEDIA-DELIVERY.actual-a01.json'),'visual_spans':pin(PKG/'visual-review-and-spans.actual-a01.json'),'intake_copy_plan':pin(PKG/'INTAKE-SMALL-COPY-PLAN.actual-a01.json'),'actual_amounts':actual,'limits':{'all_derived_bytes':LIMIT,'metadata_bytes':META_LIMIT},'copy_plan_bytes':plan['planned_copy_bytes']},ensure_ascii=False,indent=2))
