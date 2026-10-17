"""Replay recorded R196 R01 inputs in memory with the existing pure consumer.

No extraction, original absolute-path access, SDK, CK3, desktop or save load.
The source machine's historical qualification never transfers to this host.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import lzma
import platform
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

def need(value,message):
    if not value:raise ValueError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def pointer(value,path):
    need(not path or path.startswith('/'),'invalid explicit JSON pointer')
    for segment in path.split('/')[1:]:
        key=segment.replace('~1','/').replace('~0','~')
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value

def verify(args):
    index_raw=args.index.read_bytes()
    need(len(index_raw)<=262144,'index ceiling')
    index=json.loads(index_raw)
    need(index['schema']=='xar.e04.r196.r01.portable-source-index.v1','wrong index schema')
    archive_path=args.archive or args.index.parent/index['archive']['path']
    raw=archive_path.read_bytes()
    need(len(raw)==index['archive']['bytes'] and digest(raw)==index['archive']['sha256'],'archive exact bytes/SHA differ')
    need(len(raw)<=524288,'archive exceeds the admitted portable lane ceiling')
    members=index['members'];names=[x['member'] for x in members]
    need(len(names)==len(set(names)),'duplicate indexed member')
    need(sum(x['bytes'] for x in members)<=16*1024*1024,'uncompressed total ceiling')
    objects={};parsed={}
    if index['compression'].startswith('solid-XZ'):
        decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=256*1024*1024)
        solid=decoder.decompress(raw,max_length=16*1024*1024+1)
        need(decoder.eof and not decoder.unused_data and len(solid)<=16*1024*1024,'solid stream exceeds bounded complete input')
        offset=0
        for row in members:
            name=row['member'];p=PurePosixPath(name)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,'unsafe member path')
            need(not name.lower().endswith(('.ck3','.exe','.dll')),'save or executable not allowed')
            need(row['solid_offset']==offset,'solid offsets are not exact contiguous original slices')
            need(row['bytes']<=(32*1024*1024 if name.startswith('full/') else 262144),'per-member ceiling')
            value=solid[offset:offset+row['bytes']];offset+=row['bytes']
            need(len(value)==row['bytes'] and digest(value)==row['sha256'],'member SHA/length differs: '+name)
            objects[name]=value
        need(offset==len(solid),'unindexed solid bytes')
    else:
        raise ValueError('unsupported recorded compression format')
    need(sum(len(x) for x in objects.values())==index['uncompressed_total_bytes'],'total differs')
    def body(ref):
        name=ref['member']
        if name not in parsed:parsed[name]=json.loads(objects[name])
        value=pointer(parsed[name],ref.get('pointer',''))
        need(isinstance(value,dict),'semantic body must be an object')
        return value
    inputs=body({'member':'portable-inputs.json'})
    need(inputs['schema']=='xar.e04.r196.r01.portable-input-binding.v1','wrong input binding schema')
    need(inputs['source_machine_id']==index['source_machine_id']=='desktop-3fevhd2-1c74096080','recorded source machine differs')
    need(inputs['source_run_id']==index['source_run_id']=='desktop-3fevhd2-1c74096080--vanilla--R0196','recorded run differs')
    repo=args.repo.resolve()
    pins=inputs['existing_pure_consumer_source_pins']
    for pin in pins:
        relative=PurePosixPath(pin['path'])
        need(not relative.is_absolute() and '..' not in relative.parts,'unsafe pure module path')
        source=(repo/Path(*relative.parts)).resolve()
        need(source.is_relative_to(repo),'module escapes repository')
        source_raw=source.read_bytes()
        need(len(source_raw)==pin['bytes'] and digest(source_raw)==pin['sha256'],'pinned pure consumer module differs: '+pin['path'])
    sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge.episode04_ready_t0_12004 import evaluate_episode04_ready_t0_12004
    bodies={key:body(ref) for key,ref in inputs['bodies'].items()}
    evaluation=evaluate_episode04_ready_t0_12004(**bodies,**inputs['selectors'])
    expected=body(inputs['expected_evaluation'])
    need(evaluation==expected,'existing pure consumer replay differs from original actual result')
    need(evaluation['military_t0_frame_ready'] is True and evaluation['normal_t0_saved'] is True and evaluation['missing_inputs']==[],'original military admission not ready')
    root=body(inputs['root_decision'])
    need(root['card']=='R01' and root['decision']=='research_core_closed','recorded Root decision differs')
    need(root['machine_id']==index['source_machine_id'] and root['run_id']==index['source_run_id'],'Root source binding differs')
    need(root['source_head']==inputs['source_head']==index['source_head'],'recorded source differs')
    need(root['video_signoff'] is False,'unexpected video signoff')
    before=bodies['before']
    previews={}
    for target,num in ((2644,5),(2645,6),(2619,7)):
        packet=body({'member':f'responses/0{num}-preview{target}.json'})
        need(packet.get('is_error') is False,'recorded preview error')
        q=packet['body'];r=q['route_preview']
        need(q['accepted'] is True and r['status']=='available','recorded preview unavailable')
        for qkey,fkey in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),('queried_native_revision','native_revision'),('queried_episode_run_id','episode_run_id')):
            need(q[qkey]==before[fkey],'preview/frame differs')
        need(q['queried_connection_generation']==before['diagnostics']['connection_generation'],'preview lifetime differs')
        need(r['army_id']==inputs['selectors']['army_id'] and r['origin_province_id']==2635 and r['target_province_id']==target,'preview subject differs')
        previews[target]=r
    need(previews[2644]['route_province_ids']==[2645,2644] and previews[2645]['route_province_ids']==[2645],'recorded goal/land route differs')
    rest=previews[2619]['province_supply']['target']
    captured=rest['captured_target_land_supply_inputs_v1']
    need(captured['native_resupply_eligible'] is True and captured['loaded_gain_raw']==2000000,'recorded rest eligibility differs')
    need(rest['native_supply_limit_soldiers']==6122 and rest['native_supply_usage_soldiers']==0,'recorded rest scalar differs')
    normal=inputs['normal_save_identity_manifest']['original_materialization_layer']
    need(normal['checkpoint']['sha256']==normal['episode_seed']['sha256']==bodies['checkpoint']['checkpoint']['sha256'],'normal identity-save relation differs')
    need(normal['checkpoint']['bytes']==normal['episode_seed']['bytes']==bodies['checkpoint']['checkpoint']['size'],'normal identity-save bytes differ')
    need(len([n for n in names if n.startswith('full/')])==1,'complete Driver not single-copy')
    return {
        'schema':'xar.e04.r196.r01.portable-verification.actual.v1',
        'verified_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_machine_id':index['source_machine_id'],'verification_machine_id':args.verification_machine_id,
        'verification_platform':platform.platform(),'source_run_id':index['source_run_id'],'source_head':index['source_head'],
        'accepted':True,'archive':index['archive'],'index_sha256':digest(index_raw),'members_verified':len(names),
        'uncompressed_bytes_verified':index['uncompressed_total_bytes'],'pure_consumer_module_pins_verified':len(pins),
        'military_t0_frame_ready':evaluation['military_t0_frame_ready'],'normal_t0_saved':evaluation['normal_t0_saved'],
        'recorded_Root_R01_decision':root['decision'],'recorded_progress':root['progress'],
        'recorded_goal':2644,'recorded_land_node':2645,'recorded_conditional_rest':2619,
        'root_limits_preserved':root['limits'],'video_signoff':False,
        'source_machine_qualification_transferred_to_verification_host':False,
        'proof_scope':'Exact archived original bytes and existing pure consumer consistency replay. Root decision remains a recorded source-machine fact. No independent attestation of original collection or current installation/runtime.',
        'game_or_SDK_execution':False,'save_load_or_save_body_access':False,'archive_extracted':False,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--index',type=Path,default=Path(__file__).with_name('source-index.json'))
    p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--verification-machine-id',default='unknown')
    a=p.parse_args(argv)
    try:out=verify(a);code=0
    except (OSError,ValueError,KeyError,TypeError,lzma.LZMAError) as e:
        out={'accepted':False,'error':str(e),'game_or_SDK_execution':False,'source_machine_qualification_transferred_to_verification_host':False};code=2
    raw=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        with a.output.open('x',encoding='utf8',newline='\n') as f:f.write(raw)
    else:sys.stdout.write(raw)
    return code

if __name__=='__main__':raise SystemExit(main())
