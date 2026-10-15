"""Verify archived JSON bytes and replay the existing pair checker without CK3.

Inputs remain immutable. Only a new explicit work directory is written. Historical
source-drive strings are mapped to extracted data; they are never opened directly.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath

REPO=Path(__file__).resolve().parents[5]
RELATIVE_BUNDLE='docs/ck3-native-ai/evidence/episode04-r0174-20261015'
def need(condition,message):
    if not condition:raise ValueError(message)
def read(path):
    path=Path(path);need(path.stat().st_size<=1024*1024,'small metadata bound exceeded')
    return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    h=hashlib.sha256();count=0
    with Path(path).open('rb') as source:
        while data:=source.read(131072):h.update(data);count+=len(data)
    return count,h.hexdigest()
def pinned(path,pin):
    need(digest(path)==(pin['bytes'],pin['sha256']),'archive/source pin differs: '+Path(path).name)
def new(path,value):
    with Path(path).open('x',encoding='utf-8') as out:json.dump(value,out,ensure_ascii=False,indent=2)
def verify(repo,bundle,work):
    repo=repo.resolve();bundle=bundle.resolve();work=work.resolve()
    need(not work.exists(),'use a new empty explicit replay work directory')
    index=read(bundle/'bundle-index.json')
    need(index['schema']=='xar.e04.r0174-portable-pair-evidence.v1','unsupported archive contract')
    need(index['uncompressed_bytes']<=128*1024*1024 and index['archive']['bytes']<=16*1024*1024,'archive budget exceeded')
    archive=bundle/index['archive']['path'];pinned(archive,index['archive'])
    portable=bundle/index['portable_manifest']['path'];pinned(portable,index['portable_manifest'])
    shared=index['shared_R0173']
    shared_manifest=repo/shared['manifest_repo_path'];shared_zip=repo/shared['archive_repo_path']
    pinned(shared_manifest,{'bytes':shared['manifest_bytes'],'sha256':shared['manifest_sha256']})
    pinned(shared_zip,{'bytes':shared['archive_bytes'],'sha256':shared['archive_sha256']})
    work.mkdir(parents=True,exist_ok=False)
    checked=extracted=bytes_checked=bytes_extracted=0
    with zipfile.ZipFile(archive) as source:
        infos=source.infolist();names=[item.filename for item in infos]
        expected={row['archive_member']:row for row in index['files']}
        need(len(names)==len(set(names))==index['member_count'] and set(names)==set(expected),'archive member set/duplicates differ')
        need(sum(item.file_size for item in infos)==index['uncompressed_bytes'],'archive uncompressed size differs')
        for info in infos:
            row=expected[info.filename];member=PurePosixPath(info.filename)
            need(not member.is_absolute() and '..' not in member.parts and '\\' not in info.filename
                and ':' not in info.filename and info.filename.startswith('data/'),'unsafe archive member')
            need(info.file_size==row['bytes'] and info.file_size<=16*1024*1024,'member size differs/exceeds bound')
            destination=(work/Path(*member.parts)).resolve()
            need(destination.is_relative_to(work),'archive target escapes replay root')
            write=bool(row['extract_for_pair_replay'])
            output=None
            if write:
                destination.parent.mkdir(parents=True,exist_ok=True);output=destination.open('xb')
            h=hashlib.sha256();count=0
            try:
                with source.open(info) as raw:
                    while data:=raw.read(131072):
                        h.update(data);count+=len(data)
                        if output:output.write(data)
            finally:
                if output:output.close()
            need((count,h.hexdigest())==(row['bytes'],row['sha256']),'original JSON bytes differ: '+info.filename)
            checked+=1;bytes_checked+=count
            if write:extracted+=1;bytes_extracted+=count
    # Derived manifest is separate; original archived packets are not rewritten.
    portable_copy=work/'pair.manifest.portable.json'
    with portable_copy.open('xb') as output:output.write(portable.read_bytes())
    checker=repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/validate_common_t0_control.py'
    pair_output=work/'pair-result.actual.json'
    pair_argv=[sys.executable,'-B','-X','utf8',str(checker),'--archive-root',str(work),
        '--manifest','pair.manifest.portable.json','--phase','pair','--output',str(pair_output)]
    pair=subprocess.run(pair_argv,capture_output=True,text=True,encoding='utf-8')
    new(work/'pair-command.actual.json',{'argv':pair_argv,'returncode':pair.returncode,'stdout':pair.stdout,'stderr':pair.stderr})
    need(pair.returncode==0,'existing portable pair checker failed; keep exact result/command')
    result=read(pair_output)
    need(result.get('matched_seed_no_boarding_control')=='PASS' and result.get('original_R07_full_qualified') is False,
         'pair scope/qualification changed')
    # Reuse the existing eighteen-file positive archive in its canonical repo
    # location. Its verifier rejoins production raw payment evidence independently.
    positive_argv=[sys.executable,'-B','-X','utf8',str(repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/verify_r0173_evidence.py'),
        '--evidence',str(shared_manifest.parent)]
    positive=subprocess.run(positive_argv,capture_output=True,text=True,encoding='utf-8')
    new(work/'shared-R0173-command.actual.json',{'argv':positive_argv,'returncode':positive.returncode,
        'stdout':positive.stdout,'stderr':positive.stderr})
    need(positive.returncode==0,'shared historical positive archive verifier failed')
    positive_result=json.loads(positive.stdout)
    need(positive_result.get('boarding_gold')==3 and positive_result.get('R07_original_card_complete') is False,
         'historical payment scope differs')
    sys.path.insert(0,str(repo))
    from tools.ck3_live_run_id import current_machine_id
    report={'schema':'xar.e04.r0174-relative-archive-replay.actual.v1','verifier_machine_id':current_machine_id(),
      'archive_producer_machine_id':index['machine_id'],'result':'PASS','existing_pair_checker':'PASS',
      'shared_R0173_positive_verifier':'PASS','shared_positive_gold':positive_result['boarding_gold'],
      'exact_members_verified':checked,'exact_JSON_bytes_verified':bytes_checked,
      'members_extracted':extracted,'bytes_extracted':bytes_extracted,
      'unextracted_daily_full_sidecars_verified':checked-extracted,
      'archive_root':str(work),'manifest_argument':'pair.manifest.portable.json',
      'original_source_C_or_D_data_roots_used':False,'original_receipts_rewritten':False,
      'control_days':21,'end_date_raw':53145552,'original_R07_full_qualified':False,
      'maintenance_attribution':'unclosed','zero_expenses_proved':False,
      'current_machine_live_acceptance':False,'SDK_game_desktop_calls':0,
      'quota_review_at_utc':index['quota_review_at_utc']}
    new(work/'REPLAY.actual.json',report)
    return report
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=REPO)
    parser.add_argument('--bundle-dir',type=Path)
    parser.add_argument('--work-dir',type=Path,required=True)
    args=parser.parse_args()
    bundle=args.bundle_dir or args.repo/RELATIVE_BUNDLE
    print(json.dumps(verify(args.repo,bundle,args.work_dir),ensure_ascii=False))
if __name__=='__main__':main()
