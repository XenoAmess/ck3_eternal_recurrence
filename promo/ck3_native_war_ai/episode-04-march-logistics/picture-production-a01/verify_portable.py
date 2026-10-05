"""Read only this relative source/config/result package; no outside or media access."""
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
def read(name):return json.loads((R/name).read_text(encoding='utf-8-sig'))
def need(value,reason):
 if value is not True:raise ValueError(reason)
manifest=read('portable-manifest-a01.json')
for row in manifest['files']:
 p=Path(row['path']);need(not p.is_absolute() and ':' not in row['path'] and '\\' not in row['path'] and '..' not in p.parts,'unsafe package path')
 data=(R/p).read_bytes();need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed package file '+str(p))
for p in R.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
config=read('project/promo-project.json');clock=read('project/paragraph-state-and-clock.json');result=read('project/actual-A-only-result.json');projection=read('project/config-projection-notes.json')
need(len(config['chapters'])==6,'six chapters')
cues=[c for ch in config['chapters'] for c in ch['cues']]
need(len(cues)==69 and [c['id'] for c in cues]==[p['id'] for p in clock['paragraphs']],'exact 69 cue order')
cursor=0;framecursor=0
for c,p in zip(cues,clock['paragraphs']):
 need(c['narration']['zh']==c['subtitles']['zh'],'Chinese narration/subtitle divergence')
 need(hashlib.sha256(c['narration']['zh'].encode()).hexdigest()==p['text_zh_sha256'],'actual Chinese text binding')
 need(hashlib.sha256(c['subtitles']['en'].encode()).hexdigest()==p['text_en_sha256'],'actual English text binding')
 need(p['actual_PCM_start_sample']==cursor and p['actual_PCM_end_sample']>cursor,'continuous actual PCM')
 need(p['actual_picture_start_frame']==framecursor and p['actual_picture_end_frame']>framecursor,'continuous actual picture')
 need(abs(p['picture_cut_start_offset_frames'])<=1 and abs(p['picture_cut_end_offset_frames'])<=1,'bounded preserved cut offset')
 cursor=p['actual_PCM_end_sample'];framecursor=p['actual_picture_end_frame']
need(cursor==37900224 and framecursor==47376,'full actual duration clock')
need(result['B'] is None and result['C'] is None and result['winner'] is None,'B/C/winner unknown')
need(result['A']['first_observed_elapsed_days']==51 and result['A']['observed_arrival_interval_endpoint_inclusion']=='(49,51]' and result['A']['exact_arrival_tick'] is None,'A finite observed interval')
need(result['A']['payment_ledger'] is None,'payment attribution unknown')
need(result['music']=={'title':'Quiet Courtly Tension','gain_db':-17,'ducking':False,'normalize':False},'fixed soundtrack')
for key in ['continuous_source_clean_review','human_full_1x_review','listening_signoff','film_signoff','final_film_ready','uploaded','portable_assembler_projection_has_actual_render_credit']:need(result[key] is False,'no invented '+key)
need([p['cue_id'] for p in projection['changed_fields']]==['C05-03','C05-15','C05-16'],'finite new config projection')
probe=read('provenance/actual-full-bound-probe-a01.json');raw=read('provenance/actual-root-delivery-a01.json');v=next(s for s in probe['ffprobe']['streams'] if s['codec_type']=='video');a=next(s for s in probe['ffprobe']['streams'] if s['codec_type']=='audio')
need((v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',47376),'actual bound video metadata')
need((a['codec_name'],a['sample_rate'],a['channels'])==('aac','48000',2),'actual bound AAC metadata')
need(probe['subject']['sha256'].lower()==result['source_movie']['sha256']==raw['picture']['sha256'] and probe['subject']['bytes']==result['source_movie']['bytes']==raw['picture']['bytes'],'exact sealed movie identity')
need(result['source_movie']['included_in_package'] is False,'movie external')
need(not any(p.suffix.lower() in {'.mp4','.mkv','.mov','.wav','.mp3','.png','.exe','.dll'} for p in R.rglob('*') if p.is_file()),'source/metadata only')
for key,target in result['source_receipts'].items():need((R/'project'/target).resolve().is_relative_to(R) and (R/'project'/target).is_file(),'relative source receipt '+key)
need(result['toolchain']['actual_version']=='0.2.1' and result['toolchain']['wheel_sha256']=='f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621','actual formal wheel identity')
print(json.dumps({'state':'PORTABLE_SOURCE_CONFIG_ACTUAL_METADATA_PASS','files':len(manifest['files']),'cues':69,'samples':cursor,'picture_frames':framecursor,'external_media_reads':0,'outside_dependencies':0,'runtime_mutations':0,'B_C_winner':None,'human_signoff':False}))
