"""Append newly arrived independent source review; never rewrite first archive."""
from pathlib import Path
import datetime,hashlib,json,collections
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
PROCESS=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-permanent-archive-other-a01')
SOURCE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-hidden-modal-independent-review-knights-a01')
def ident(p):
 h=hashlib.sha256();size=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
 return {'path':str(p.resolve()).replace('\\','/'),'bytes':size,'sha256':h.hexdigest().upper()}
def load(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
assert ident(SOURCE/'readonly-source-review-a01.json')['sha256']=='763ABA846EB365D3368FFA894A4C376E7F1C3BD25B0106FD7245814B41A3CDA9'
original_handoff_path=PROCESS/'archive-handoff-a01.json';original_handoff=load(original_handoff_path)
for i in original_handoff['exact_new_files']:assert ident(Path(i['path']))==i
source_files=sorted([p for p in SOURCE.rglob('*') if p.is_file()],key=lambda p:str(p).lower())
rows=[];pairs=[]
for p in source_files:
 before=p.stat();meta=ident(p);after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 rel=p.relative_to(SOURCE)
 row={**meta,'source_group':'post_R0141_independent_modal_source_review','relative_to_source_group':str(rel).replace('\\','/'),'evidence_layer':'POST_R0141_INDEPENDENT_STATIC_AND_OFFLINE_SOURCE_REVIEW_ONLY_NOT_LIVE_UI','retained_external_original':True,'original_mtime_ns':after.st_mtime_ns}
 if meta['bytes']<=2*1024*1024 and p.suffix.lower() not in {'.exe','.dll','.obj','.pdb','.lib','.pyc'} and p.name!='.gitattributes':
  d=HERE/'exact-copies/post_R0141_independent_modal_source_review'/rel;d.parent.mkdir(parents=True,exist_ok=True)
  with p.open('rb') as inp,d.open('xb') as out:
   for b in iter(lambda:inp.read(1024*1024),b''):out.write(b)
  copy=ident(d);assert copy['sha256']==meta['sha256'] and copy['bytes']==meta['bytes']
  row['repository_copy']={**copy,'verified_exact_bytes':True,'no_text_line_ending_or_whitespace_change':True};pairs.append({'original':meta,'copy':copy,'exact_bytes_verified':True})
 else:row['copy_policy']='EXTERNAL_ONLY_LARGE_OR_COMPILED; FULL_ORIGINAL_RETAINED'
 rows.append(row)
subindex_path=HERE/'later-offline-review-assets-index-a01.json'
write(subindex_path,{'schema':'ck3.e2.append-only-later-source-review-assets/v1','arrived_after_base_asset_inventory_started':True,'source_root':str(SOURCE).replace('\\','/'),'all_assets':rows,'status':'POST_R0141_SOURCE_REVIEW_ONLY; SIX_GAPS_PENDING; NO_LIVE_SUCCESS','no_original_archive_file_rewritten':True})
base_index_path=HERE/'all-assets-index-a01.json';base_index=load(base_index_path)
combined=base_index['all_assets']+rows
group_counts=collections.Counter(r['source_group'] for r in combined)
final_index_path=HERE/'all-assets-index-final-a02.json'
write(final_index_path,{'schema':'ck3.e2.append-only-research-assets-index/v3','desktop_run_id':base_index['desktop_run_id'],'native_episode_run_id':base_index['native_episode_run_id'],'predecessor_index':ident(base_index_path),'append_only_supplement':ident(subindex_path),'source_groups':{**base_index['source_groups'],'post_R0141_independent_modal_source_review':str(SOURCE).replace('\\','/')},'all_assets':combined,'counts_by_group':dict(group_counts),'original_count':len(combined),'original_total_bytes':sum(r['bytes'] for r in combined),'repository_exact_copy_count':sum('repository_copy' in r for r in combined),'no_live_fields_or_research_status_changed':True,'raw_copies_not_line_normalized':True,'scope':'Complete final inventory = preserved base inventory + new independent static/offline review; later source cannot relabel R0141 GREEN.'})
all_pairs=load(HERE/'copy-verification-a01.json')['pairs']+pairs
for pair in all_pairs:
 assert ident(Path(pair['original']['path']))==pair['original']
 assert ident(Path(pair['copy']['path']))==pair['copy']
 assert pair['original']['bytes']==pair['copy']['bytes'] and pair['original']['sha256']==pair['copy']['sha256']
for row in combined:
 st=Path(row['path']).stat();assert st.st_size==row['bytes'] and st.st_mtime_ns==row['original_mtime_ns']
assert source_files==sorted([p for p in SOURCE.rglob('*') if p.is_file()],key=lambda p:str(p).lower())
verification_path=HERE/'copy-verification-final-a02.json'
write(verification_path,{'schema':'ck3.e2.original-current-copy-final-verification/v3','status':'PASS_ALL_ORIGINAL_CURRENT_COPY_SIZE_SHA_RECOMPUTED_MATCH; ORIGINAL_STATS_STABLE','original_count':len(combined),'copy_count':len(all_pairs),'pairs':all_pairs,'first_archive_hashes_unchanged':True,'new_offline_review_source_file_set_stable':True,'Git_canonical_acceptance_not_performed':True})
summary=load(BASE/'current-native-research-R0141.json')
final_summary={**summary,'schema':'ck3.e2.current-native-research-preservation/v4','first_summary_retained':ident(BASE/'current-native-research-R0141.json'),'first_document_retained':ident(BASE/'current-native-research-R0141.md'),'all_assets_index':ident(final_index_path),'copy_verification':ident(verification_path),'inventory_count':len(combined),'repository_exact_copy_count':len(all_pairs),'later_independent_offline_review':{'evidence':ident(SOURCE/'readonly-source-review-a01.json'),'asset_index':ident(subindex_path),'live_pass_claim':False,'R0141_mechanism_status_unchanged':True},'first_snapshot_counts_retained_in_original_summary_doc':True}
final_summary_path=HERE/'derived-facts/current-native-research-R0141-final-a02.json';write(final_summary_path,final_summary)
doc=HERE/'later-offline-review-record-a01.md'
with doc.open('x',encoding='utf-8',newline='\n') as f:
 f.write(f'''# R0141 后续离线源审追加保全

knights独立只读源审在基础归档已固定输入之后到达，因此另建追加索引，基础索引、summary、正文与第一次文件清单均保持原字节。

该源审 `readonly-source-review-a01.json` 为58696 bytes，SHA `763ABA846EB365D3368FFA894A4C376E7F1C3BD25B0106FD7245814B41A3CDA9`；结论是4文件 hidden-modal 修复 narrow静态/离线PASS。它不是R0141 live UI成功，不能补+24、主before、名单、完整战斗窗或机制因果链。

基础索引记录{len(base_index['all_assets'])}项输入；本次追加{len(rows)}项原件过程资产。最终[联合索引](all-assets-index-final-a02.json)共{len(combined)}项，[最终summary](derived-facts/current-native-research-R0141-final-a02.json)绑定联合索引和{len(all_pairs)}项重新比较 original/current SHA 的exact copies。原 `current-native-research-R0141.json/.md` 的数量属于第一次归档快照；它们的机制结论与最终summary一致：R0141 RED/no-day、六项pending、global_mutable_bundle_complete=false。

本追加未改任何原件、第一次归档文件、视频或Git；canonical Git blobs仍由根授权提交者验收。
''')
final_verification_path=HERE/'verification-final-a02.json'
write(final_verification_path,{'schema':'ck3.e2.R0141-final-archive-verification/v2','status':'PASS_DISK_BYTES','original_count':len(combined),'copy_count':len(all_pairs),'first_archive_files_unchanged':True,'no_legacy_input_or_video_changes':True,'summary':ident(final_summary_path),'combined_index':ident(final_index_path),'copy_verification':ident(verification_path),'new_offline_append_record':ident(doc),'raw_attributes':ident(HERE/'.gitattributes'),'canonical_Git_index_and_blob_verification_reserved_for_authorized_committer':True})
all_files=sorted([p for p in HERE.rglob('*') if p.is_file()]+[BASE/'current-native-research-R0141.json',BASE/'current-native-research-R0141.md'],key=lambda p:str(p).lower())
manifest_path=HERE/'new-files-manifest-final-a02.json'
write(manifest_path,{'schema':'ck3.e2.R0141-final-created-files-manifest/v2','files':[ident(p) for p in all_files],'manifest_self_excluded_to_avoid_recursive_hash':True,'new_file_count_including_this_manifest':len(all_files)+1,'predecessor_manifest':ident(HERE/'new-files-manifest-final-a01.json')})
all_files.append(manifest_path)
handoff={'schema':'ck3.e2.R0141-final-archive-handoff/v2','status':'FINAL_ARCHIVE_READY_STOPPED_WRITING_NO_GIT','first_handoff_retained':ident(original_handoff_path),'archive_root':str(HERE).replace('\\','/'),'new_file_count':len(all_files),'exact_new_files':[ident(p) for p in all_files],'primary_summary':ident(BASE/'current-native-research-R0141.json'),'primary_document':ident(BASE/'current-native-research-R0141.md'),'final_combined_summary':ident(final_summary_path),'manifest':ident(manifest_path),'verification':ident(final_verification_path),'all_assets_index':ident(final_index_path),'copy_verification':ident(verification_path),'original_assets':len(combined),'exact_copies':len(all_pairs),'R0141_mechanism_stays_RED':True,'six_items_still_pending':True,'global_mutable_bundle_complete':False,'source_latest_repair_only_offline_verified':True,'no_game_Git_video_or_master_action':True}
target=PROCESS/'archive-handoff-final-a02.json';write(target,handoff)
print(json.dumps({'handoff':ident(target),'primary_summary':handoff['primary_summary'],'final_combined_summary':handoff['final_combined_summary'],'manifest':handoff['manifest'],'verification':handoff['verification'],'new_files':len(all_files),'original_assets':len(combined),'copies':len(all_pairs),'status':handoff['status']},ensure_ascii=False))
