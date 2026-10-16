"""Actual P26 response projections; synthetic capital qualification stays explicit."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer import strategy as S
from xar_autoplayer.bridge import native_driver as D
strategy = S
FIXTURE = json.loads(gzip.decompress((Path(__file__).parent / 'fixtures/p26_native_negative_routes_v1.json.gz').read_bytes()))
def body(sequence):
    return copy.deepcopy(FIXTURE['responses'][str(sequence)])

def test_owned_nonleader_capital_qualification_and_negative_gates():
    s=copy.deepcopy(FIXTURE['semantic65'])
    assert s['date_raw']==53411208 and s['active_wars'][0]['war_id']==201326630
    assert s['active_wars'][0]['player_is_primary_war_leader'] is False
    assert [(x['army_id'],x['owner_character_id'],x['controllable']) for x in s['player_armies']]==[(620757086,40526,True)]
    actor=s['played_character']['character_id']; diag=s['diagnostics']
    # Synthetic complete root uses an invented title id; it is not a live Game observation.
    q={'cache_binding':{'snapshot_id':s['snapshot_id'],'revision':s['revision'],'native_revision':s['native_revision'],'date_raw':s['date_raw'],'actor_character_id':actor,'bridge_pid':diag['bridge_pid'],'connection_generation':diag['connection_generation']},'campaign_root_context':{'status':'available','snapshot_revision':s['native_revision'],'date_raw':s['date_raw'],'player_character_id':actor,'readiness':{'ready':True,'held_title_partition_ready':True},'capital_province_id':2619,'held_title_partition':[{'title':{'title_id':999,'tier_raw':2},'capital_province_id':2619}]}}
    scope=D._capital_regroup_capability_scope(s,q)
    assert scope and scope['army_id']==620757086 and scope['capital_province_id']==2619
    assert len(scope['hostile_army_ids'])==13
    wrong=copy.deepcopy(q);wrong['campaign_root_context']['held_title_partition'][0]['capital_province_id']=2620
    assert D._capital_regroup_capability_scope(s,wrong) is None
    wrong=copy.deepcopy(s);wrong['player_armies'][0]['owner_character_id']=123
    assert D._capital_regroup_capability_scope(wrong,q) is None
    wrong=copy.deepcopy(s);wrong['player_armies'][0]['in_combat']=True
    assert D._capital_regroup_capability_scope(wrong,q) is None
    wrong=copy.deepcopy(q);wrong['cache_binding']['connection_generation']+=1
    assert D._capital_regroup_capability_scope(s,wrong) is None
    
    # Synthetic all-exits classification uses factual shapes from the actual two
    # horizon responses. Source-frame consistency is enforced upstream by _fresh.
    def horizon(seq):
     return copy.deepcopy(FIXTURE['responses'][str(seq)]['result']['route_contact_horizon'])
    h5965=horizon(20);h5969=horizon(70)
    assert h5965['one_day_contact_free'] is False and h5969['one_day_contact_free'] is False
    rejections=[{'target_province_id':t,'status':'unsafe','native_contact_veto':'one_day_contact_not_free','contact_horizon':h} for t,h in ((5965,h5965),(5969,h5969))]
    kwargs=dict(active_wars=s['active_wars'],controlled_armies=s['player_armies'],tactical_war=s['active_wars'][0],subject_army_id=620757086,current_province_id=5967,exact_objective_province_ids=[5965,5969],route_rejections=rejections,route_contact_scope_supported=True)
    assert S._nonleader_attacker_capital_regroup_input_ready(s,**kwargs)
    assert not S._nonleader_attacker_capital_regroup_input_ready(s,**{**kwargs,'route_rejections':rejections[:1]})
    assert not S._nonleader_attacker_capital_regroup_input_ready(s,**{**kwargs,'route_contact_scope_supported':False})
    wrong=copy.deepcopy(rejections);wrong[0].pop('native_contact_veto')
    assert not S._nonleader_attacker_capital_regroup_input_ready(s,**{**kwargs,'route_rejections':wrong})
    wrong=copy.deepcopy(s);wrong['player_armies'][0]['route_province_ids']=[5963,5965]
    assert not S._nonleader_attacker_capital_regroup_input_ready(wrong,**{**kwargs,'controlled_armies':wrong['player_armies']})
    wrong=copy.deepcopy(s);wrong['active_wars'][0]['player_is_primary_war_leader']=True
    assert not S._nonleader_attacker_capital_regroup_input_ready(wrong,**{**kwargs,'active_wars':wrong['active_wars'],'tactical_war':wrong['active_wars'][0]})
    print('GREEN: actual P26 SEM65 nonleader/owned army, synthetic source-bound capital qualification, 6 negative gates, native-negative exit classifier')


def test_actual_native_negative_horizon_lease_and_four_old_cycles():
    preview = body(18)
    query = body(20)
    assert preview['planning_source_frame'] == query['planning_source_frame']
    assert preview['result']['route_preview']['status'] == 'available'
    assert query['result']['route_contact_horizon']['status'] == 'available'
    assert query['result']['route_contact_horizon']['one_day_contact_free'] is False
    source = query['planning_source_frame']
    snapshot = {
        'snapshot_id': source['snapshot_id'],
        'revision': source['revision'],
        'native_revision': source['native_revision'],
        'date_raw': source['date_raw'],
        'episode_run_id': source['episode_run_id'],
        'diagnostics': {'connection_generation': source['connection_generation']},
    }
    row = {'command': query['selected_step'], 'ok': True, 'result': query['result']}
    horizon = query['result']['route_contact_horizon']
    common = dict(
        army_id=620757086,
        origin_province_id=940,
        target_province_id=5965,
        hostile_army_ids=tuple(horizon['hostile_army_ids']),
        route_province_ids=preview['result']['route_preview']['route_province_ids'],
    )
    assert strategy._fresh_route_contact_horizon([row], snapshot, **common) == horizon
    assert strategy._fresh_route_contact_horizon([row], {**snapshot, 'native_revision': 9}, **common) is None
    assert strategy._fresh_route_contact_horizon([row], snapshot, **{**common, 'hostile_army_ids': (common['hostile_army_ids'][0],)}) is None
    
    for move_seq, post_query_seq, halt_seq in ((56, 58, 62), (74, 76, 80), (91, 93, 97), (109, 111, 115)):
        move = body(move_seq)
        post_query = body(post_query_seq)
        halt = body(halt_seq)
        assert move['selected_step'] == 'move-army-620757086-to-5965'
        assert move['plan']['pursuit']['route_audit']['status'] == 'safe'
        assert post_query['result']['route_contact_horizon']['one_day_contact_free'] is False
        assert halt['selected_step'] == 'halt-army-620757086'
        assert move['planning_source_frame']['date_raw'] == post_query['planning_source_frame']['date_raw'] == halt['planning_source_frame']['date_raw'] == 53411208
    print('GREEN: exact same-frame preview/query proof at AUTO18/20, stale-scope negatives, four actual move→contact-false→HALT cycles')


def test_ordinary_geometric_safe_route_queries_then_respects_native_negative():
    """Synthetic Native-negative proof must also govern the ordinary chooser."""
    helper_path = Path(__file__).with_name('test_gameplay_bridge.py')
    spec = importlib.util.spec_from_file_location('ordinary_route_test_helpers', helper_path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    query_step = 'query-route-contact-horizon-v1-11-to-2585-h-1-21'

    def plan(history):
        player = helpers._army(
            11, soldiers=900, province_id=20, controllable=True,
            army_state='regular', route_province_ids=[])
        enemy = helpers._army(
            21, soldiers=800, province_id=99, controllable=False,
            army_state='regular', route_province_ids=[])
        return helpers._native_war_plan(
            player=player, enemies=[enemy], score=0, date_raw=24000,
            history=history, objective=2585,
            steps=('preview-move-army-11-to-2585', query_step,
                   'move-army-11-to-2585', 'life-advance-one-day'),
            route_contact_horizon_supported=True,
            episode_run_id='portable-episode')

    preview = helpers._preview_row(
        1, origin=20, target=2585, date_raw=24000, route=[31, 2585])
    preview['result'].update(
        queried_snapshot_id='session:90', queried_revision=90,
        queried_native_revision=90, queried_connection_generation=1,
        queried_episode_run_id='portable-episode')
    before = plan([preview])
    assert before['selected_step'] == query_step
    assert before['phase'] == 'native_war_candidate_contact_horizon'
    assert before['route_audit']['status'] == 'safe'

    negative = helpers._route_contact_row(
        2, origin=20, target=2585, date_raw=24000, route=[31, 2585],
        hostile_ids=(21,), contact_free=False,
        episode_run_id='portable-episode')
    after = plan([preview, negative])
    assert after.get('selected_step') != 'move-army-11-to-2585'
    assert any(row.get('native_contact_veto') == 'one_day_contact_not_free'
               for row in after.get('route_rejections', []))
