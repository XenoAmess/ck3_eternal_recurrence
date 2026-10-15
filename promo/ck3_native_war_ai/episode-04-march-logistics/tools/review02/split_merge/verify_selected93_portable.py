"""Verify portable original bytes, then call the owner's literal-only reader.

Full raw archive integrity is separate from selected/role semantic replay.
This tool never reconstructs a whole-roster qualification from partial data.
"""
from __future__ import annotations
import argparse, datetime, hashlib, importlib.util, json, sys, types, zipfile
from pathlib import Path, PurePosixPath


def require(ok,message):
    if not ok:raise ValueError(message)


def archive_integrity(index, path):
    require(path.stat().st_size==index['archive']['bytes'] and path.stat().st_size<=12*1024**2,'portable archive size differs')
    require(hashlib.sha256(path.read_bytes()).hexdigest()==index['archive']['sha256'],'portable archive SHA differs')
    rows={row['path']:row for row in index['files']}
    require(len(rows)==len(index['files']),'duplicate indexed member')
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist()
        require(len(infos)==len(rows) and {info.filename for info in infos}==set(rows),'portable membership differs')
        require(sum(info.file_size for info in infos)<=192*1024**2,'uncompressed finite archive bound exceeded')
        for info in infos:
            member=PurePosixPath(info.filename)
            require(not member.is_absolute() and '..' not in member.parts and '\\' not in info.filename,'unsafe member path')
            row=rows[info.filename]
            require(info.file_size==row['bytes'] and info.file_size<=64*1024**2,'per-file original bound exceeded')
            digest=hashlib.sha256();total=0
            with archive.open(info) as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):
                    total+=len(block);digest.update(block)
            require(total==row['bytes'] and digest.hexdigest()==row['sha256'],'original member pin differs')
    return len(rows)


def exact_file(repo,ref):
    relative=PurePosixPath(ref['path'])
    require(not relative.is_absolute() and '..' not in relative.parts,'reader/projection path must be repository-relative')
    path=repo/ref['path'];raw=path.read_bytes()
    require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'owner reader/projection pin differs')
    return path,raw


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,required=True);parser.add_argument('--archive',type=Path)
    parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-overlay',type=Path,action='append',default=[],help='Optional explicit Python source roots for a sealed external overlay')
    args=parser.parse_args();require(not args.output.exists(),'append-only output already exists')
    index=json.loads(args.index.read_bytes());repo=args.repo.resolve()
    count=archive_integrity(index,args.archive or args.index.parent/index['archive']['path'])
    reader_ref=index['owner_semantic_reader'];projection_ref=index['owner_literal_projection']
    reader_path,_=exact_file(repo,reader_ref);projection_path,raw=exact_file(repo,projection_ref)
    roots=[repo/'ck3_autonomous_player/src',*args.source_overlay]
    for dependency in index['owner_dependencies']:
        suffix=Path(dependency['path']).relative_to('ck3_autonomous_player/src')
        found=next((root/suffix for root in roots if (root/suffix).exists()),None)
        require(found is not None and hashlib.sha256(found.read_bytes()).hexdigest()==dependency['sha256'],'owner pure dependency pin differs')
    # Isolated namespace paths avoid bridge.__init__/Driver bootstrap. The
    # same exact pure observation/transfer modules are used by the owner.
    for name,suffix in (('xar_autoplayer','xar_autoplayer'),('xar_autoplayer.bridge','xar_autoplayer/bridge')):
        package=types.ModuleType(name);package.__path__=[str(root/suffix) for root in roots];sys.modules[name]=package
    spec=importlib.util.spec_from_file_location('r09_owner_selected93_literal_reader',reader_path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    function=getattr(module,index['owner_reader_entrypoint'])
    selected=function(json.loads(raw))
    result={'schema':'episode04.r0176.selected93.portable-replay.v1','status':'PASS','machine_id':index['machine_id'],
            'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':index['run_id'],
            'raw_archive_integrity_members':count,'full_raw3_archived':True,'full_raw3_integrity_verified':True,
            'semantic_scope':'owner frozen literal selected93/role projection only; no fullraw-to-projection reconstruction',
            'owner_reader':reader_ref,'owner_projection':projection_ref,'owner_result':selected,
            'all_roster_strengths_qualified':False,'R09_full_card_closed':False,'original_legacy_strict_failure_preserved':True,
            'new_source_or_role_analysis_performed':False,'historical_absolute_paths_followed':0,
            'native_build_or_EXE_operations':0,'SDK_game_desktop_calls':0,'video_save_DLL_body_reads_or_hashes':0,
            'dynamic_video_qualification':False,'continuous_clean':False,'human_approval':False,'new_live_evidence_by_replay':False}
    with args.output.open('xb') as f:f.write((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({'status':'PASS','original_members':count,'semantic_scope':result['semantic_scope']}))


if __name__=='__main__':main()
