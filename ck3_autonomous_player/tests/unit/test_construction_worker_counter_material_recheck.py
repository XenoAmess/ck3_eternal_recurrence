"""Material recheck after worker counter reset, using a synthetic native packet."""
from copy import deepcopy
import pytest
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as t
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer import construction_formal_consumer as c
# Selected recorded counter/identity values; packet and carrier are synthetic.
FIXTURES = {'ledger': {'schema': 'xar.ck3.construction_formal_pending_v1',
            'applied': {'status': 'applied',
                        'postcondition_verified': True,
                        'completion_status': 'in_progress',
                        'episode_run_id': 'native-40526-c7a6edcc32b8',
                        'actor_character_id': 40526,
                        'action_request_id': 'construction-submit-f99c45ab7ecd41dc8f9b9c90ea710d81',
                        'pre_native_revision': 806,
                        'pre_date_raw': 53334096,
                        'pre_proof_epoch': 4339977,
                        'source_bridge_pid': 249712,
                        'source_bridge_creation_date': '20261015230508.297017+480',
                        'post_bridge_pid': 249712,
                        'post_bridge_creation_date': '20261015230508.297017+480',
                        'post_native_revision': 1070,
                        'post_public_revision': 542,
                        'post_date_raw': 53338320,
                        'post_proof_epoch': 4562479,
                        'completion_last_check_date_raw': 53338320,
                        'candidate': {'barony_title_id': 2232,
                                      'province_id': 2619,
                                      'building_type_id': 532,
                                      'slot_index': 3,
                                      'stock_gold_cost_raw': 14250000,
                                      'gold_before_raw': 34472433,
                                      'building_key': 'murex_farm_01',
                                      'authored_monthly_income_hundredths': 35,
                                      'authored_monthly_income_delta_hundredths': 10,
                                      'old_authored_monthly_income_hundredths': 25,
                                      'old_building_key': 'curtain_walls_01',
                                      'slot_was_empty': False},
                        'native_ack': {'schema_version': 1,
                                       'advertised': False,
                                       'status': 'pending_receipt',
                                       'candidate_failure': 'none',
                                       'native_failure': 'none',
                                       'stock_candidate_ready': True,
                                       'production_native_path': True,
                                       'applied': False,
                                       'proof_epoch': 4339977,
                                       'actor_character_id': 40526,
                                       'barony_title_id': 2232,
                                       'province_id': 2619,
                                       'building_type_id': 532,
                                       'slot_index': 3,
                                       'gold_before_raw': 34472433,
                                       'stock_gold_cost_raw': 14250000,
                                       'gold_after_reserve_raw': 20222433,
                                       'receiver_command_sequence': 1,
                                       'validator_calls': 1,
                                       'materialize_calls': 1,
                                       'receiver_calls': 1},
                        'start_receipt': {'action_request_id': 'construction-submit-f99c45ab7ecd41dc8f9b9c90ea710d81',
                                          'post_native_revision': 807}}},
 'metrics': {'started_at_utc': '2026-10-16T04:41:54.039401+00:00',
             'ended_at_utc': '2026-10-16T04:41:54.044394+00:00',
             'elapsed_seconds': 0.004990600049495697,
             'request': {'sequence': 737,
                         'tool': 'root_current_runtime_metrics',
                         'arguments': {},
                         'source': "Root's bounded full_loop; unique new request"},
             'result': {'meta': None,
                        'content': [{'type': 'text',
                                     'text': '{\n'
                                             '  "snapshot_id": "native:3",\n'
                                             '  "revision": 630,\n'
                                             '  "native_revision": 3,\n'
                                             '  "date_raw": 53339880,\n'
                                             '  "paused": true,\n'
                                             '  "map_ready": true,\n'
                                             '  "actor_character_id": 40526,\n'
                                             '  "actor_alive": true,\n'
                                             '  "episode_run_id": '
                                             '"native-40526-c7a6edcc32b8",\n'
                                             '  "connection_generation": 1,\n'
                                             '  "war_count": 1,\n'
                                             '  "driver_state_bytes": 34721887,\n'
                                             '  "army_strengths_profile": null,\n'
                                             '  "army_strengths_query_sequence": null,\n'
                                             '  "army_strength_result_write_v1": null\n'
                                             '}',
                                     'annotations': None,
                                     'meta': None}],
                        'structured_content': {'snapshot_id': 'native:3',
                                               'revision': 630,
                                               'native_revision': 3,
                                               'date_raw': 53339880,
                                               'paused': True,
                                               'map_ready': True,
                                               'actor_character_id': 40526,
                                               'actor_alive': True,
                                               'episode_run_id': 'native-40526-c7a6edcc32b8',
                                               'connection_generation': 1,
                                               'war_count': 1,
                                               'driver_state_bytes': 34721887,
                                               'army_strengths_profile': None,
                                               'army_strengths_query_sequence': None,
                                               'army_strength_result_write_v1': None},
                        'is_error': False,
                        'result_type': 'complete'},
             'mcp_result_projection_json_utf8_bytes': 1011},
 'error': {'result': {'is_error': True,
                      'content': [{'text': 'construction receipt requires a later paused actor '
                                           'frame'}]}},
 'plan': {'result': {'structured_content': {'selected_step': 'private-query-player-construction-receipt-v1'}}}}
def load(name):
    return deepcopy(FIXTURES[name])
class Driver:
    allow_private_construction_formal_trial=True
    def __init__(self,state,frame):
        self.state_dir=state
        self.snapshot=frame
        self.records=[]
    def take_snapshot(self):
        return deepcopy(self.snapshot)
    def _record_command(self,command,**record):
        self.records.append((command,record))
@pytest.fixture
def case(tmp_path,monkeypatch):
    actual=load("ledger")
    old=deepcopy(actual["applied"])
    ledger={"schema":actual["schema"],"pending":None,"applied":old,"applied_prior":[]}
    metric=load("metrics")["result"]["structured_content"]
    # Scalars are actual; optional map-carrier fields/material below synthetic.
    frame={**metric,"played_character":{"character_id":metric["actor_character_id"],"alive":metric["actor_alive"]},
           "active_event":None,"pending_character_interaction":None,
           "active_wars":[{"war_id":134217770}],"player_armies":[],"native_command_history":[]}
    driver=Driver(tmp_path,frame)
    identity=(old["source_bridge_pid"],old["source_bridge_creation_date"])
    monkeypatch.setattr(t,"_identity",lambda ignored:identity)
    monkeypatch.setattr(t,"private_native_build_identity",lambda ignored:CK3_12004)
    monkeypatch.setattr(t,"private_native_provenance",lambda ignored:{})
    monkeypatch.setattr(c,"private_native_build_identity",lambda ignored:CK3_12004)
    row={**{k:old["candidate"][k] for k in t.TUPLE_KEYS},
         "active":True,"initiator_character_id":old["actor_character_id"],
         "native_remaining_work_raw":81000000,"native_progress_divisor_raw":60000,
         "native_province_monthly_income_observed":True,"native_province_monthly_income_raw":221692}
    world={"status":"source_available","snapshot_revision":frame["native_revision"],
           "date_raw":frame["date_raw"],"player_character_id":old["actor_character_id"],
           "native_final_legality_evaluated":True,"native_cost_evaluated":False,
           "player_gold_raw":31190221,"active_constructions":[row],
           "completed_buildings_observed":True,"completed_buildings":[],"legal_samples":[]}
    sends=[]
    def send(ignored,step,revision,request_id):
        sends.append((step,revision,request_id))
        assert step==t.QUERY_NATIVE
        return {"step":step,"accepted":True,"private_probe":{
            "advertised":False,"snapshot_revision":revision,"date_raw":frame["date_raw"],
            "proof_epoch":100,"player_world_building_sources":deepcopy(world)}}
    monkeypatch.setattr(t,"_send",send)
    c.write_construction_ledger(tmp_path,ledger)
    return driver,old,ledger,world,sends

def test_independent_material_rebind_then_repeated_plans(case):
    driver,old,ledger,world,sends=case
    auto=load("error")
    plan=load("plan")["result"]["structured_content"]
    assert auto["result"]["is_error"] is True
    assert "construction receipt requires a later paused actor frame" in auto["result"]["content"][0]["text"]
    assert plan["selected_step"]==t.RECEIPT_STEP
    assert driver.snapshot["native_revision"]==3 < old["pre_native_revision"]==806
    assert old["pre_proof_epoch"]==4339977
    baseline={"snapshot_id":"native:3","revision":630,"plan":{"phase":"ordinary","selected_step":"life-advance"}}
    before=c.plan_construction_private(driver,deepcopy(baseline),driver.snapshot,[],{"life-advance"})
    assert before["plan"]["phase"]=="construction_cold_applied_requery"
    result=t.query_construction_receipt(driver,pending=deepcopy(old),expected_revision=630)
    assert result["status"]=="applied" and result["postcondition_verified"] is True
    assert result["post_native_revision"]==3 and result["post_proof_epoch"]==100
    for key in ("pre_native_revision","pre_date_raw","pre_proof_epoch","native_ack","candidate","start_receipt"):
        assert result[key]==old[key]
    assert result["readonly_material_recheck"]["native_query_request_id"]==sends[0][2]
    assert result["readonly_material_recheck"]["source_frame"]["native_revision"]==3
    assert result["readonly_material_recheck"]["native_submit_calls"]==0
    updated=c.read_construction_ledger(driver.state_dir)
    assert updated["applied"]==result and updated["pending"] is None
    assert c.priority_construction_receipt(driver,updated,driver.snapshot) is None
    for unused in range(2):
        following=c.plan_construction_private(driver,deepcopy(baseline),driver.snapshot,[],{"life-advance"})
        assert following["plan"]["phase"]=="ordinary"
        assert following["plan"]["selected_step"]=="life-advance"
        assert following["plan"]["construction_receipt_consumed"]==result
    assert len(sends)==1

def test_unresolved_action_still_requires_later_native_counter(case):
    driver,old,ledger,world,sends=case
    pending={**old,"status":"submitted_verification_pending"}
    c.write_construction_ledger(driver.state_dir,{**ledger,"pending":pending,"applied":None})
    with pytest.raises(BridgeUnavailableError,match="later paused actor frame"):
        t.query_construction_receipt(driver,pending=pending,expected_revision=630)
    assert sends==[]

def test_unresolved_still_requires_later_proof_epoch(case):
    driver,old,ledger,world,sends=case
    driver.snapshot.update(native_revision=807,snapshot_id="native:807")
    world["snapshot_revision"]=807
    pending={**old,"status":"submitted_verification_pending"}
    c.write_construction_ledger(driver.state_dir,{**ledger,"pending":pending,"applied":None})
    with pytest.raises(BridgeUnavailableError,match="material proof unavailable"):
        t.query_construction_receipt(driver,pending=pending,expected_revision=630)
    assert len(sends)==1 and sends[0][0]==t.QUERY_NATIVE

@pytest.mark.parametrize("change",["actor","date","native_frame","material"])
def test_recheck_still_requires_original_subject_and_fresh_material(case,change):
    driver,old,ledger,world,sends=case
    if change=="actor": driver.snapshot["played_character"]["character_id"]+=1
    if change=="date": driver.snapshot["date_raw"]=old["pre_date_raw"]-24
    if change=="native_frame": world["snapshot_revision"]+=1
    if change=="material": world["active_constructions"][0]["building_type_id"]+=1
    with pytest.raises(BridgeUnavailableError):
        t.query_construction_receipt(driver,pending=old,expected_revision=630)
    assert c.read_construction_ledger(driver.state_dir)==ledger
    assert all(entry[0]==t.QUERY_NATIVE for entry in sends)
