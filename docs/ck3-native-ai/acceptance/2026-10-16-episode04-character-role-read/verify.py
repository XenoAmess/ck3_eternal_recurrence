"""Replay this exact paused ordinary-query publication proof; no native access."""
from pathlib import Path
import argparse,hashlib,json,sys,datetime

def need(condition,message):
    if not condition:raise ValueError(message)

def verify(packet_path,repo_root):
    sys.path.insert(0,str(Path(repo_root)/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge import army_replenishment_records_contract as production_DATA
    from xar_autoplayer.bridge import army_regiment_character_role_12004 as production_role
    packet=json.loads(Path(packet_path).read_text(encoding='utf-8'))
    need(packet['schema']=='xar.episode04.character-role-actual-read.v1','packet schema differs')
    f=packet['frame'];q=packet['query'];binding=packet['root_binding'];diagnostics=f['diagnostics'];hello=diagnostics['hello']
    need(packet['machine_id']=='desktop-3fevhd2-1c74096080','source machine differs')
    need(packet['root_source_head']=='dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb','source baseline differs')
    need(binding['pid']==diagnostics['bridge_pid']==hello['pid']==16512,'PID binding differs')
    need(binding['process_create_time_100ns']==134365577928096099,'baseline creation binding differs')
    need(binding['generation']==diagnostics['connection_generation']==hello['connection_generation']==q['queried_connection_generation']==1,'connection generation differs')
    need(binding['episode']==f['episode_run_id']==q['queried_episode_run_id']=='native-31254-13a1253fe701','episode binding differs')
    need(f['paused'] is True and f['map_ready'] is True and diagnostics['connected'] is True,'snapshot is not paused/ready/connected')
    need(f['played_character']['alive'] is True and f['played_character']['character_id']==binding['actor']==31254,'played actor differs')
    need(q['accepted'] is True and q['status']=='available' and q['army_strengths_profile']=='ordinary_core_v1','ordinary query unavailable')
    need(q['queried_snapshot_id']==f['snapshot_id'] and q['queried_revision']==f['revision']
         and q['queried_native_revision']==f['native_revision'] and q['queried_date_raw']==f['date_raw'],'query does not bind its own actual frame')
    need(hello['expected_ck3_version']=='1.20.0.4' and hello['expected_ck3_sha256'].lower()=='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
         and hello['game_adapter_status']=='ready' and hello['ck3_build_match'] is True,'exact adapter/build differs')
    need(len(q['army_strengths'])==1,'query scope differs');army=q['army_strengths'][0]
    need(army['army_id']==binding['army_id']==18 and army['native_carmy_id']==binding['native_carmy_id']==18
         and army['status']=='available','Army full-generation binding differs')
    roster=next(row for row in f['player_armies'] if row['army_id']==18)
    need(roster['controllable'] is True and roster['owner_character_id']==31254,'Army owner/control differs')
    rows=production_DATA.normalize_regiment_replenishment_records_v1(army['regiment_replenishment_records_v1'])
    strengths={row['army_regiment_id']:row for row in army['regiment_strengths']}
    need(len(rows)==army['regiment_count']==len(strengths)==22,'complete role/DATA/strength roster differs')
    need({row['army_regiment_id'] for row in rows}==set(strengths),'role/DATA identities differ')
    results=[]
    for row in rows:
        identity=row['army_regiment_id'];leaf=row.get('native_character_role_v1')
        need(leaf is not None and leaf['status']=='available' and leaf['same_ArRg_instance_after'] is True,'actual new role leaf is absent/partial')
        need(row['status']=='available' and row['ready'] is True,'actual allDATA incomplete')
        value=production_role.classify_current_regiment_character_role_12004(
            strengths[identity],row,leaf,native_carmy_id=18,
            current_commander={'status':'unavailable','character_id':None},knights=None)
        if value['native_character_predicate'] is True:
            need(row['native_data_record_count']==0 and row['records']==[],'observed Character record has physical DATA')
            need((strengths[identity]['current_soldiers'],strengths[identity]['maximum_soldiers'])==(1,1),'observed Character cache differs')
            need(leaf['extension_arrg_id_f8']==identity and leaf['arrg_army_id_140']==18,'observed Character backlink differs')
        results.append(value)
    def pin(module):
        path=Path(module.__file__);return {'repo_relative_path':path.relative_to(repo_root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'status':'ACTUAL_PAUSED_ORDINARY_ROLE_LEAF_PUBLISHED_AND_CONSUMED','source_machine_id':packet['machine_id'],
            'capture_time_utc':packet['capture_time_utc'],'root_binding':binding,
            'process_creation_time_evidence':'Root baseline binding, not an independent process probe by this verifier',
            'snapshot_id':f['snapshot_id'],'revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],
            'production_code':[pin(production_DATA),pin(production_role)],'role_leaf_rows':len(rows),
            'observed_empty_Character_1_1_ids':[row['army_regiment_id'] for row in results if row['native_character_predicate'] is True],
            'observed_noncharacter_leaf_ids':[row['army_regiment_id'] for row in results if row['native_character_predicate'] is False],
            'consumer_results':results,'actual_split_or_merge_postcondition':None,
            'birth_producer_observed':False,'actual_physical_refill':None,
            'current_commander_readback_available':False,'combat_Knights_readback_available':False,
            'SDK_game_desktop_or_EXE_executed_by_verifier':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[4])
    parser.add_argument('--packet',type=Path,default=Path(__file__).with_name('packet-minimum.json'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--machine-id',default='unknown',help='Replay host identity, independently supplied')
    args=parser.parse_args();result=verify(args.packet,args.repo_root.resolve())
    result['machine_id']=args.machine_id
    result['verified_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    text=json.dumps(result,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf-8',newline='\n') as handle:handle.write(text)
    else:print(text,end='')

if __name__=='__main__':main()
