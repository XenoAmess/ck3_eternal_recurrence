from pathlib import Path
import argparse
import copy
import importlib
import json
import sys
import tempfile

parser = argparse.ArgumentParser(description="Exercise production occupation-query history and existing route-step admission with a fake native endpoint and supplied actual Robert receipts; creates no game actions.")
parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument("--dependency-root", type=Path)
parser.add_argument("--preview-artifact", type=Path, required=True)
parser.add_argument("--occupation-artifacts-dir", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
OUT = args.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = (args.dependency_root or args.source_root).resolve()
DRIVER_SOURCE = args.source_root.resolve()
sys.path[:0] = [str(SOURCE / 'ck3_autonomous_player/src'), str(SOURCE / 'ck3_autonomous_player/tests/unit'), str(SOURCE / 'tools')]
import xar_autoplayer.bridge
xar_autoplayer.bridge.__path__.insert(0, str(DRIVER_SOURCE / 'ck3_autonomous_player/src/xar_autoplayer/bridge'))
sys.modules.pop('xar_autoplayer.bridge.native_driver', None)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _fresh_war_occupation_route_steps
from xar_autoplayer.bridge.war_contract import MOVE_ARMY_CAPABILITY, PREVIEW_MOVE_ARMY_CAPABILITY, QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY, move_army_step, preview_move_army_step, query_route_contact_horizon_step
from xar_autoplayer.bridge.war_occupation_targets_contract import QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY, query_war_occupation_targets_v1_step
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot

checks = 0
def Check(condition, detail):
    global checks
    checks += 1
    if not condition:
        raise RuntimeError(detail)

receipt = json.loads(args.preview_artifact.read_text(encoding='utf-8'))
root_snapshot = receipt['initial']
occupation = {}
for name in ('024-ck3_query_war_occupation_targets_v1.json', '026-ck3_query_war_occupation_targets_v1.json', '028-ck3_query_war_occupation_targets_v1.json'):
    value = json.loads((args.occupation_artifacts_dir / name).read_text(encoding='utf-8'))['packet']['structuredContent']
    occupation[value['war_id']] = value

caps = ('game.state.snapshot', 'game.state.war-objectives', 'game.state.army-routes', MOVE_ARMY_CAPABILITY, PREVIEW_MOVE_ARMY_CAPABILITY, QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY, QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY)
endpoint = FakeEndpoint()
responses = []
with tempfile.TemporaryDirectory(prefix='occupation-route-fixture-', dir=OUT) as state_dir:
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir, command_timeout_seconds=0.2)
    endpoint.publish(_hello(*caps))
    endpoint.publish(_snapshot(3, date_raw=root_snapshot['date_raw'], speed=root_snapshot['speed'], paused=True, map_ready=True, played_character=root_snapshot['played_character'], active_wars=root_snapshot['active_wars'], player_armies=root_snapshot['player_armies']))
    start = driver.take_snapshot()
    army_id = 83886367
    candidates = (2604,2625,2629)
    Check(all(preview_move_army_step(army_id, pid) not in driver.capabilities()['action_steps'] for pid in candidates), 'actual RED candidates should be absent before the native occupation query')

    def answer(frame):
        if frame.get('type') != 'execute_step':
            return
        step = frame['step']
        if step.startswith('query-war-occupation-targets-v1-'):
            war_id = int(step.removeprefix('query-war-occupation-targets-v1-'))
            response = copy.deepcopy(occupation[war_id])
            response['snapshot_revision'] = 3
            response['war_occupation_targets_v1']['snapshot_revision'] = 3
        elif step.startswith('preview-move-army-'):
            pid = int(step.rsplit('-to-',1)[1])
            response = {'step':step,'accepted':True,'status':'available','route_preview':{'status':'available','army_id':army_id,'origin_province_id':2610,'target_province_id':pid,'route_province_ids':[2610,pid]}}
        else:
            raise RuntimeError('Unexpected fixture endpoint command: ' + step)
        responses.append({'request':copy.deepcopy(frame),'fixture_response':copy.deepcopy(response)})
        endpoint.publish({'type':'command_result','protocol_version':1,'request_id':frame['request_id'],'ok':True,'result':response})

    endpoint.send_hook = answer
    for war_id in (16777231,50331736,129):
        result = driver.execute_step(query_war_occupation_targets_v1_step(war_id), expected_revision=start['revision'])
        Check(result['war_occupation_targets_v1']['available'] is True, 'genuine typed query must complete')
        Check(result['queried_connection_generation'] == start['diagnostics']['connection_generation'], 'query cache must keep current connection domain')
        Check(result['queried_episode_run_id'] == start['episode_run_id'], 'query cache must keep current episode domain')
    steps = set(driver.capabilities()['action_steps'])
    payload = occupation[16777231]['war_occupation_targets_v1']
    expected_ids = {row['province_id'] for row in payload['rows'] if row['territory_side']=='defender' and row['counted_occupied_by_opposing_side']}
    Check(len(expected_ids)==17, 'fixture must use all17 actual recovery holdings, not hardcoded three')
    hostiles = sorted({enemy['army_id'] for war in root_snapshot['active_wars'] for enemy in war['enemy_armies'] if enemy.get('retreating') is not True and enemy.get('army_state')!='retreating' and enemy.get('army_state_code')!=6})
    for pid in expected_ids:
        Check(preview_move_army_step(army_id,pid) in steps, 'missing preview candidate '+str(pid))
        Check(move_army_step(army_id,pid) in steps, 'missing move candidate '+str(pid))
        Check(query_route_contact_horizon_step(army_id,pid,hostiles) in steps, 'missing existing horizon candidate '+str(pid))
    Check(preview_move_army_step(army_id,99999) not in steps, 'unobserved province was not derived')
    for pid in candidates:
        result = driver.execute_step(preview_move_army_step(army_id,pid), expected_revision=start['revision'])
        Check(result['route_preview']['target_province_id']==pid, 'production execute_step must reach generic preview endpoint')
        Check(result['queried_native_revision']==3, 'preview native revision must remain3')
    history = driver._history_tail_snapshot(128)
    Check(bool(_fresh_war_occupation_route_steps(start,history,set(caps))), 'fresh result should expand targets')
    without_relevant = [row for row in history if row.get('command')!=query_war_occupation_targets_v1_step(16777231)]
    Check(_fresh_war_occupation_route_steps(start,without_relevant,set(caps))==set(), 'outside-war physical occupation alone must not expand recovery targets')
    unavailable = copy.deepcopy(history)
    unavailable.append({'command':query_war_occupation_targets_v1_step(16777231),'ok':True,'result':{'war_occupation_targets_v1':{'available':False,'collection_complete':False}}})
    Check(_fresh_war_occupation_route_steps(start,unavailable,set(caps))==set(), 'new unavailable must not reuse older complete query')
    changed = copy.deepcopy(start)
    changed['native_revision'] = 4
    Check(_fresh_war_occupation_route_steps(changed,history,set(caps))==set(), 'changed frame requires a fresh observation')
    changed = copy.deepcopy(start)
    changed['diagnostics']['connection_generation'] += 1
    Check(_fresh_war_occupation_route_steps(changed,history,set(caps))==set(), 'cold connection must not reuse old occupation cache')
    restored = history + [{'command':'restore-checkpoint','ok':True}]
    Check(_fresh_war_occupation_route_steps(start,restored,set(caps))==set(), 'restore uses existing history invalidation')
    moving_armies = copy.deepcopy(root_snapshot['player_armies'])
    for army in moving_armies:
        if army['army_id']==army_id:
            army.update({'current_province_id':2610,'route_province_ids':[2604],'route_read_status':'complete_nonempty','route_source_count':1,'move_target_province_id':2604,'move_target_observable':True})
    moving_wars = copy.deepcopy(root_snapshot['active_wars'])
    moving_army = next(army for army in moving_armies if army['army_id']==army_id)
    for war in moving_wars:
        for i, army in enumerate(war['allied_armies']):
            if army['army_id']==army_id:
                war['allied_armies'][i] = copy.deepcopy(moving_army)
    endpoint.publish(_snapshot(4,date_raw=root_snapshot['date_raw']+24,speed=root_snapshot['speed'],paused=True,map_ready=True,played_character=root_snapshot['played_character'],active_wars=moving_wars,player_armies=moving_armies))
    moving = driver.take_snapshot()
    Check(moving['native_revision']==4 and moving['date_raw']==root_snapshot['date_raw']+24, 'fixture future native frame must actually be adopted: '+str(moving.get('diagnostics')))
    Check(_fresh_war_occupation_route_steps(moving,history,set(caps))==set(), 'old occupation frame must expire after a saved day')
    moving_steps = set(driver.capabilities()['action_steps'])
    Check(query_route_contact_horizon_step(army_id,2604,hostiles) in moving_steps, 'observed complete actual route must preserve2604 horizon after occupation cache expires')
    Check(preview_move_army_step(army_id,2604) in moving_steps, 'actual route waypoint remains an existing preview candidate')
    arrived_armies = copy.deepcopy(moving_armies)
    for army in arrived_armies:
        if army['army_id']==army_id:
            army.update({'current_province_id':2604,'route_province_ids':[],'route_read_status':'complete_empty','route_source_count':0,'move_target_province_id':None,'move_target_observable':False,'army_state':'regular','army_state_code':1,'in_combat':False,'retreating':False})
    arrived_wars = copy.deepcopy(moving_wars)
    arrived_army = next(army for army in arrived_armies if army['army_id']==army_id)
    for war in arrived_wars:
        for i, army in enumerate(war['allied_armies']):
            if army['army_id']==army_id:
                war['allied_armies'][i] = copy.deepcopy(arrived_army)
    endpoint.publish(_snapshot(5,date_raw=root_snapshot['date_raw']+48,speed=root_snapshot['speed'],paused=True,map_ready=True,played_character=root_snapshot['played_character'],active_wars=arrived_wars,player_armies=arrived_armies))
    arrived_steps = set(driver.capabilities()['action_steps'])
    Check(query_route_contact_horizon_step(army_id,2604,hostiles) in arrived_steps, 'arrived stationary empty-route army must preserve same-current2604 readonly horizon')
    Check(move_army_step(army_id,2604) not in arrived_steps, 'stationary current horizon must not create a new same-province move')
    driver.close()

result = {'status':'GREEN','python_optimization':sys.flags.optimize,'runtime_checks':checks,'actual_input_war_id':16777231,'recovery_province_ids':sorted(expected_ids),'advertised_existing_formats':['preview-move-army','move-army','query-route-contact-horizon-v1'],'production_driver_preview_dispatch_targets':list(candidates),'post_day_moving_route_waypoint_horizon':2604,'arrived_stationary_current_horizon':2604,'fixture_endpoint':True,'native_route_or_game_live_claim':False,'new_sdk_calls':0,'new_game_actions':0,'new_day_credit':0,'wire_calls':responses}
(OUT / 'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key: value for key,value in result.items() if key!='wire_calls'},indent=2))
