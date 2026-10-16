from pathlib import Path
import hashlib,io,json,zipfile
ROOT=Path(__file__).resolve().parent
def need(v,m):
    if not v:raise ValueError(m)
def read(n):return json.loads((ROOT/n).read_bytes())
i=read('source-index.json')
for r in i['originals']:
    b=(ROOT/r['local']).read_bytes();p=r['source'];need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'original '+r['local'])
b=(ROOT/'small-originals.portable.zip').read_bytes();need(hashlib.sha256(b).hexdigest()==i['archive']['sha256'],'archive')
z=zipfile.ZipFile(io.BytesIO(b))
for r in i['archive']['members']:
    b=z.read(r['member']);p=r['source'];need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'member '+r['member'])
f=read('facts.derived-a01.json');need(hashlib.sha256((ROOT/'facts.derived-a01.json').read_bytes()).hexdigest()==i['generated_facts_sha256'],'facts')
for n in range(1,13):
    d=read('days/r190-film-a01-d%02d-complete.actual.json'%n)
    need(d['date_raw']==53148144+24*n and d['sentinel']['state']=='triggered' and d['sentinel']['overshoot_days']==0,'day chain')
old=json.loads(z.read('film-input.actual-a01.json'));new=json.loads(z.read('film-input.actual-a02.json'))
old['checkpoint_source']['save']['path']=new['checkpoint_source']['save']['path'];need(old==new,'only config path changed')
norm=read('receipts/film-source-path-normalization.actual-a02.json');need(norm['original_failed_preflight_had_no_recorder_or_SDK_calls'] is True,'preflight boundary')
film=read('receipts/r190-film-a01-film-result.actual.json');need(film['completed_days']==12 and film['additional_resumes_during_tail']==0,'film')
a=json.loads(z.read('media-audit.actual-a01.json'));tail=a['paused_tail'];need(len(tail['readonly_snapshot_pins'])==76 and tail['all_snapshots_paused'] and tail['all_snapshot_dates_raw']==53148432,'audited tail')
need(len({p['source']['sha256'] for p in tail['readonly_snapshot_pins']})==76,'76 distinct source receipts')
need(tail['additional_resumes_reported']==0 and tail['research_qualification_credit'] is False,'paused tail no credit')
m=read('media/portable-media-facts.actual-a01.json');need(m['video']['timeline']['frames']==3220 and m['encoded_frame_end_seconds']==107.333 and m['full_AV_decode_exit']==0,'decode')
need(m['wall_110_seconds_met'] and m['encoded_100_seconds_met'] and not m['encoded_110_seconds_met'],'distinct duration checks')
before=json.loads(z.read('BEFORE-ANALYSIS.actual-a01.json'));after=json.loads(z.read('AFTER-ANALYSIS.actual-a01.json'));br=before['rows'][0];ar=after['rows'][0]
need(len(br['physical_baseline'])==21 and sum(x['current_soldiers'] for x in br['physical_baseline'])==1174,'before physical')
need(br['physical_current_max']==[1174,1185] and ar['physical_current_max']==[1163,1185] and ar['net_same_cohort_physical_debit']==11,'owner physical summary')
need(f['endpoint']['after_21slot_array_NOT_HELD'] and not f['endpoint']['after_21slot_portable_arithmetic_independently_recomputed'],'after detail limit')
nz=zipfile.ZipFile(io.BytesIO(z.read('R190-native-loss-math.portable.zip')));w=json.loads(nz.read('natural-loss-math-witness.json'));row=w['army_rows'][0]
need(sum(x['current_soldiers'] for x in row['regiment_strengths'])==1173 and br['current_soldiers']==1184,'cached layer')
loss=row['actual_loss_writer_observations_v1'];need(loss['event_count']==0 and loss['events']==[] and loss['overwritten_events']==2535 and loss['latest_sequence']==3047,'ring gap')
need(w['expected']['physical'][0]['positive_physical_debit_observed'] is False and 'writer_fence_gap_or_reset' in w['expected']['joined'][0]['unknown_reasons'],'strict negative output')
cb=row['actual_supply_callback_observations_v1']['events'];need(len(cb)==1 and cb[0]['sequence']==8 and cb[0]['passed_date_raw64']&0xffffffff==53148192,'callback date')
need(cb[0]['before']['supply_raw']==30000000 and cb[0]['after']['supply_raw']==30000000,'callback stock only')
s=read('close/SCREEN-RELEASE.actual.json');t=json.loads(s['stdout'])['task'];need(s['exit_code']==0 and t['state']=='done' and t['resources']==[] and s['normal_exit_zero'],'close')
need(f['qualification']['new_R03_single_event_positive']==0 and not f['qualification']['human_signoff'],'no credit')
print(json.dumps({'status':'PASS','machine_id':i['machine_id'],'exact_original_files':len(i['originals']),'exact_archive_members':len(i['archive']['members']),'portable_only':True,'full_Driver_video_save_reads':0,'after21_recomputed':False}))
