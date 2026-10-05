"""Relative stdlib-only append audit; never dereference external media paths."""
import hashlib,json,runpy
from pathlib import Path
R=Path(__file__).resolve().parent
def read(n):return json.loads((R/n).read_bytes())
def need(v,r):
 if v is not True:raise ValueError(r)
m=read('portable-manifest-a03.json')
for row in m['files']:
 p=Path(row['path']);need(not p.is_absolute() and ':' not in row['path'] and '..' not in p.parts and '\\' not in row['path'],'unsafe relative path')
 b=(R/p).read_bytes();need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'changed file '+str(p))
for row in m['preserved_original_15']:
 b=(R/row['path']).read_bytes();need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'original file changed')
runpy.run_path(str(R/'verify_portable.py'),run_name='__portable_original_check__')
a=read('provenance/final-machine-audit-ROOT03.json');f=read('provenance/final-machine-audit-findings03.json');result=read('project/actual-A-only-result.json')
need(a['state']==f['state']=='DECODE_COUNTS_PASS_EXACT_AUDIO_PTS_CONTINUITY_RED','mixed audit status retained')
need(a['whole_decode_and_counts_pass'] is True and a['exact_audio_pts_continuity_pass'] is False,'counts PASS and exact continuity RED separate')
need(f['whole_decode_returncode']==0 and f['progress_end_reached'] is True,'actual decode complete')
need(f['actual_video_frames']==47376 and f['video_frame_count_delta']==0 and f['actual_audio_decoded_frames']==74025 and f['actual_audio_decoded_sample_frames_per_channel']==75801600 and f['audio_sample_count_delta']==0,'actual complete counts')
need(f['source_narration_PCM_seconds']=='1579.176' and f['planned_grid_tail_vs_source_PCM_seconds']=='0.024','source and grid tail separate')
t=f['audio_timing'];need(t['audio_pts_strictly_increasing'] is True and t['audio_pts_exact_contiguous'] is False,'exact PTS remains RED')
need(t['absolute_offset_samples_distribution']=={'-1':20,'0':74005} and t['adjacent_boundary_delta_samples_distribution']=={'-1':5,'0':74014,'1':5} and len(t['absolute_offset_runs'])==5,'observed one-sample boundaries exact')
need(t['cause_verified'] is False and t['audible_effect_verified'] is False,'cause/listening unknown')
need(f['medium_check_processes_total']==1 and f['new_media_processes_for_postanalysis']==0 and f['movie_SHA_reads']==0 and f['new_ffprobe_executions']==0 and f['old_raw_or_B_live_reads']==0,'single decode no repeated media check')
need(f['final_movie_identity_reused']['sha256']==result['source_movie']['sha256'] and f['final_movie_identity_reused']['bytes']==result['source_movie']['bytes'],'same exact movie identity')
need(result['whole_strict_video_audio_decode_at_this_cut'] is None,'old historical NULL not overwritten')
need(f['human_listening_performed'] is False and f['full_human_1x_review_completed'] is False and f['human_signoff'] is False and f['continuous_clean_source_review'] is False and f['film_approved'] is False and f['audio_perceptual_quality_verdict'] is None,'no invented human/clean/film credit')
need(bool(a['original_prefix_parse_RED_delivery_preserved']) and bool(f['failed_exact_continuity_reparse02_stdio_preserved']),'original RED and failed02 retained')
print(json.dumps({'state':'PORTABLE_APPEND_METADATA_PASS_DECODE_COUNTS_PASS_EXACT_PTS_RED','files':len(m['files'])+1,'original_15_exact':True,'default_plan_unchanged':True,'external_media_reads':0,'B_C_winner':None,'human_signoff':False}))
