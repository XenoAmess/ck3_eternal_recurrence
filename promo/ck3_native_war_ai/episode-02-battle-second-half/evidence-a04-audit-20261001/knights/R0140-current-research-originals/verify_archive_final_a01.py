from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def identity(p):
 h=hashlib.sha256();n=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
 return {'path':str(p).replace('\\','/'),'bytes':n,'sha256':h.hexdigest().upper()}
def write(p,value):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
index=json.loads((HERE/'all-assets-index-a01.json').read_text(encoding='utf-8'))
copies=0
for row in index['all_assets']:
 original=Path(row['path']);stat=original.stat()
 assert stat.st_size==row['bytes'] and stat.st_mtime_ns==row['original_mtime_ns_observed'], 'Original changed: '+str(original)
 if 'repository_copy' in row:
  copies+=1;source=identity(original);current=identity(Path(row['repository_copy']['path']))
  assert source['bytes']==current['bytes']==row['bytes']
  assert source['sha256']==current['sha256']==row['sha256']==row['repository_copy']['sha256']
assert copies==index['copied_files']==696
summary=json.loads((BASE/'current-native-research-R0140.json').read_text(encoding='utf-8'))
assert summary['six_gap_evidence_closed'] is False and summary['global_mutable_bundle_complete'] is False
assert len(summary['six_gaps'])==6 and summary['actual_day_advance']==0
assert summary['rng_owner0_reason_is_source_inference_not_wire'] is True and summary['raw_native_UI_return_missing_for_R0140'] is True
assert summary['latest_fda_sampling_fix_is_pending_live'] is True
write(HERE/'verification-final-a01.json',{'schema':'ck3.e2.research-archive-final-verification/v1',
 'status':'PASS_CURRENT_ORIGINALS_AND_CREATED_COPIES_MATCH_HASH_BOUND_INDEX',
 'originals_stat_stable':len(index['all_assets']),'source_and_repository_copy_SHA256_recomputed_matches':copies,
 'six_gaps_pending':True,'raw_native_UI_missing_and_source_inference_labeled':True,'fda_sampling_fix_pending_live':True,
 'no_old_file_mutated':True})
created=sorted(p for p in HERE.rglob('*') if p.is_file())+[BASE/'current-native-research-R0140.json',BASE/'current-native-research-R0140.md']
write(HERE/'new-files-manifest-final-a02.json',{'schema':'ck3.e2.create-only-new-file-list/v1',
 'new_files':[identity(p) for p in created],
 'listed_files_count':len(created),'self_is_one_additional_new_file_identity_supplied_separately':True})
print(json.dumps({'all_assets':len(index['all_assets']),'copies_reverified':copies,
 'summary':identity(BASE/'current-native-research-R0140.json'),'verification':identity(HERE/'verification-final-a01.json'),
 'manifest':identity(HERE/'new-files-manifest-final-a02.json'),'total_new_files_including_manifest':len(created)+1},ensure_ascii=False))
