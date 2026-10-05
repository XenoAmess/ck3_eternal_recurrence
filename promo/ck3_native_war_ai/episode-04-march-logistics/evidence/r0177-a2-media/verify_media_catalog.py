"""Validate portable small evidence bytes/relations only; never opens raw or PNG."""
from pathlib import Path
import hashlib, json, re, sys

BASE=Path(__file__).resolve().parent
def read(relative):
 p=(BASE/relative).resolve()
 assert p.is_relative_to(BASE.resolve()),'Relative evidence path escapes package'
 return json.loads(p.read_text(encoding='utf-8-sig'))
def pins(value):
 if isinstance(value,dict):
  if {'bytes','sha256'}<=set(value):yield (value['bytes'],value['sha256'])
  for v in value.values():yield from pins(v)
 elif isinstance(value,list):
  for v in value:yield from pins(v)
manifest=read('manifest.json')
assert manifest['schema']=='xar.ck3.portable-small-evidence-manifest.v1'
assert len(manifest['files'])==len({x['path'] for x in manifest['files']})
for item in manifest['files']:
 p=(BASE/item['path']).resolve()
 assert p.is_relative_to(BASE.resolve()) and p.suffix.lower() not in {'.mkv','.mp4','.png'}
 data=p.read_bytes()
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],item['path']
catalog=read('catalog.json')
assert catalog['schema']=='xar.ck3.episode04.a2.closed-media-catalog.v1'
assert [s['segment_id'] for s in catalog['segments']]==['S01','S02']
assert not catalog['human_signoff'] and not catalog['film_approved'] and not catalog['continuous_clean_spans_certified']
summary=[]
for seg,expected in zip(catalog['segments'],[('3600.000000',108000,6),('2884.966000',86549,5)],strict=True):
 audit=read(seg['audit']);candidates=read(seg['candidate_delivery']);review=read(seg['Root_encoded_review'])
 assert audit['state']=='PASS' and not audit['errors']
 assert (audit['actual_duration_seconds'],audit['decoded_frames'],candidates['candidate_count'])==expected
 assert audit['video_packets']==audit['decoded_frames'] and audit['stream_counts']['audio']==0
 assert audit['strict_full_decode']['reached_progress_end'] is True
 assert audit['strict_full_decode']['final_decoded_frames']==audit['decoded_frames']
 assert audit['audit_raw_sha_reads']==0 and audit['sealed_terminal_hash_reused'] is True
 assert audit['source_identity']==seg['sealed_raw_identity']
 assert audit['strict_full_decode']['errors_on_stderr']==0
 assert all(v['strictly_increasing'] is True for v in audit['timestamps'].values())
 terminal=read(seg['terminal_result']);assert terminal['state']=='NORMAL_TREE_EMPTY'
 assert terminal['job']['returncode']==0 and terminal['job']['job_active_processes']==0
 assert terminal['raw']==audit['source_identity']
 review_pins=set(pins(review))
 rows=[s for r in candidates['results'] for s in r['selections']]
 projected_frames=read(seg['selected_frame_records'])['records']
 projected_packets=read(seg['selected_packet_records'])['records']
 assert len(rows)==expected[2]==len(projected_frames)==len(projected_packets)
 for row,fr,pk in zip(rows,projected_frames,projected_packets,strict=True):
  assert (row['decoded_png']['bytes'],row['decoded_png']['sha256']) in review_pins
  assert row['showinfo_pts_confirmed'] is True and row['png_size']==[1920,1080]
  assert row['time_base']==fr['time_base']==pk['time_base']=='1/1000'
  assert row['actual_pts']==fr['record']['pts']==pk['record']['pts']
  assert fr['frame_zero_based']==row['decoded_frame_index_zero_based']
  assert row['saved_complete_frame_record']==fr['record']
  assert row['saved_complete_packet_record']==pk['record']
 for extraction in seg['extractions']:
  receipt=read(extraction['receipt']);assert receipt['returncode']==0
  log=(BASE/extraction['showinfo_log']).read_text(encoding='utf-8',errors='replace')
  observed=[int(m.group(1)) for m in re.finditer(r'\[Parsed_showinfo_\d+[^\]]*\].*?\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:',log)]
  assert observed==receipt['showinfo_actual_pts']==extraction['actual_pts']
 summary.append({'segment_id':seg['segment_id'],'seconds':audit['actual_duration_seconds'],'frames':audit['decoded_frames'],'encoded_candidates_bound_to_Root_direct_review':len(rows)})
print(json.dumps({'state':'PASS_PORTABLE_SMALL_BYTES_AND_RECORDED_RELATIONS_ONLY','segments':summary,'raw_or_PNG_opened':False,'full_frame_tables_opened':False,'media_probes_run':False,'fresh_pixel_review_performed':False,'continuous_clean_span_certified':False,'human_signoff':False,'film_approved':False},ensure_ascii=False,indent=2))
