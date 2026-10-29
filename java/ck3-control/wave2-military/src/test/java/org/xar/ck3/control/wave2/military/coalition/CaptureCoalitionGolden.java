package org.xar.ck3.control.wave2.military.coalition;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit offline original-producer capture, executed only by the shared bounded Job owner. */
public final class CaptureCoalitionGolden {
    private CaptureCoalitionGolden() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo-root python-exe new-D-output required");
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path scratchRoot = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1").toRealPath();
        if (!output.startsWith(scratchRoot) || Files.exists(output)) throw new IllegalArgumentException("new output in admitted scratch root required");
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, args[0], output.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1");
        Process child = builder.directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!child.waitFor(100, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IOException("coalition capture timeout; shared Win32 Job owns descendants");
        }
        if (child.exitValue() != 0) throw new IOException("actual Python producer exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 81_920) {
            throw new IOException("coalition golden exceeded bounded 80KiB output");
        }
    }

    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
repo=pathlib.Path(sys.argv[1]); output=pathlib.Path(sys.argv[2])
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit')]
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.prewar_force_coalition_v2_contract import normalize_prewar_force_coalition_v2,assess_prewar_force_risk_v2
from test_ordinary_prewar_force_admission_v2 import _evidence
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_prewar_force_admission_v2.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_transport.py','ck3_autonomous_player/tests/unit/test_ordinary_prewar_force_admission_v2.py','ck3_autonomous_player/tests/unit/test_prewar_surrogate_authority_regression.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','tools/ck3_live_run_id.py']
before={path:hashlib.sha256((repo/path).read_bytes()).hexdigest() for path in paths}
snapshot,declaration,domain,envelope=_evidence()
keys=('paused','map_ready','revision','native_revision','date_raw','played_character','diagnostics','declarable_wars')
snapshot={k:copy.deepcopy(snapshot[k]) for k in keys}
base=dict(domain=domain,snapshot=snapshot,declaration=declaration,receipt=dict(request_id=envelope['native_request_id'],**envelope['execution_receipt']),request_id=envelope['native_request_id'],expected_capture_epoch=None,policy=None)
cases=[]
def edit(path,value):return dict(path=path,value_json=json.dumps(value,ensure_ascii=False,separators=(',',':')))
def remove(path):return dict(path=path,remove=True)
def apply(data,edits):
    for e in edits:
        parent=data
        for component in e['path'][:-1]:parent=parent[component]
        key=e['path'][-1]
        if e.get('remove'):del parent[key]
        else:parent[key]=json.loads(e['value_json'])
def add(name,edits=(),include_normalized=False):
    data=copy.deepcopy(base);apply(data,edits);untouched=copy.deepcopy(data)
    kwargs=dict(snapshot=data['snapshot'],expected_declaration=data['declaration'],expected_request_binding=data['receipt'],expected_request_id=data['request_id'],expected_capture_epoch=data['expected_capture_epoch'])
    try:
        normalized=normalize_prewar_force_coalition_v2(data['domain'],**kwargs)
        risk=assess_prewar_force_risk_v2(data['domain'],policy=data['policy'],**kwargs)
        expected=dict(accepted=True,risk=risk,final_can_send=normalized['final_cb_roles']['final_can_send'])
        if include_normalized:expected['normalized']=normalized
    except ValueError:expected=dict(accepted=False)
    if data!=untouched:raise RuntimeError('original producer mutated fixture')
    cases.append(dict(id=name,edits=list(edits),expected=expected))
def floor(n):
    return [edit(['domain','actor_lower_soldiers'],n),edit(['domain','owner_forces',0,'actor_lower_soldiers'],n),edit(['domain','owner_forces',0,'inventory_upper_soldiers'],n),edit(['domain','native_mobilization_qualification','unraised_lower_soldiers'],n),edit(['domain','native_mobilization_qualification','executable_lower_soldiers'],n),edit(['domain','native_mobilization_qualification','physical_inventory_lower_soldiers'],n),edit(['domain','native_mobilization_qualification','native_unraised_stock_soldiers'],n)]
add('complete_boundary',include_normalized=True)
add('one_below_margin',floor(1499));add('zero_actor_zero_enemy',floor(0)+[edit(['domain','enemy_upper_soldiers'],0),edit(['domain','owner_forces',1,'inventory_upper_soldiers'],0)])
add('positive_actor_zero_enemy',floor(1)+[edit(['domain','enemy_upper_soldiers'],0),edit(['domain','owner_forces',1,'inventory_upper_soldiers'],0)])
add('false_raise_independent_standing_force',[edit(['domain','native_mobilization_qualification','native_raise_legal'],False),edit(['domain','native_mobilization_qualification','raised_commandable_lower_soldiers'],1500),edit(['domain','native_mobilization_qualification','raised_lower_ready'],True)])
add('nullable_final_legality',[edit(['domain','final_cb_roles','final_can_send'],None)])
add('native_fallback_can_settle_roles',[edit(['domain','final_cb_roles','native_fallback'],True)])
add('uppercase_normalization',[edit(['domain','executable_sha256'],domain['executable_sha256'].lower())],True)
add('generic_effective_target_is_diagnostic',[edit(['domain','effective_target_character_id'],123)])
add('snapshot_extension',[edit(['snapshot','extra_sdk_field'],{'allowed':True}),edit(['declaration','extra_sdk_field'],0)])
for physical,stock in [(1500,1),(1,1500)]:
    add('minimum_proven_unraised_'+str(physical)+'_'+str(stock),floor(1)+[edit(['domain','native_mobilization_qualification','physical_inventory_lower_soldiers'],physical),edit(['domain','native_mobilization_qualification','native_unraised_stock_soldiers'],stock),edit(['domain','owner_forces',0,'inventory_upper_soldiers'],physical)])
large=(1<<63)-1
add('int64_floor_exact_bigint_products',floor(1500)+[edit(['domain','actor_lower_soldiers'],large),edit(['domain','owner_forces',0,'actor_lower_soldiers'],large),edit(['domain','owner_forces',0,'inventory_upper_soldiers'],large),edit(['domain','native_mobilization_qualification','raised_commandable_lower_soldiers'],large),edit(['domain','native_mobilization_qualification','raised_lower_ready'],True),edit(['domain','native_mobilization_qualification','executable_lower_soldiers'],large),edit(['domain','enemy_upper_soldiers'],large),edit(['domain','owner_forces',1,'inventory_upper_soldiers'],large)])
policy=dict(policy_id='explicit-large-margin-v1',scope='same_frame_owned_current_inventory_v1',minimum_actor_to_enemy_ratio_numerator=large,minimum_actor_to_enemy_ratio_denominator=large,assumption='policy_margin_not_calibrated_probability')
add('policy_int64_products',[edit(['policy'],policy)])
for value in [0,-2147483648]:
    add('native_defender_handle_'+str(value),[edit(['domain','final_cb_roles','primary_defender_character_id'],value),edit(['domain','potential_enemy_participants','participants',0,'character_id'],value),edit(['domain','owner_forces',1,'owner_character_id'],value)])
for key in ['capture_epoch','native_revision','public_revision','ticket','query_sequence']:
    edits=[edit(['domain',key],(1<<64)-1)]
    if key in ['capture_epoch','ticket','query_sequence']:edits+=[edit(['receipt',key],(1<<64)-1)]
    if key in ['native_revision','public_revision']:edits+=[edit(['snapshot','native_revision' if key=='native_revision' else 'revision'],(1<<64)-1)]
    add('uint64_max_'+key,edits,True)
add('same_frame_epoch',[edit(['snapshot','capture_epoch'],17),edit(['expected_capture_epoch'],17)])
add('partial_rounds',[edit(['domain','status'],'partial'),edit(['domain','two_round_observation','complete_dto_equal'],False),edit(['domain','two_round_observation','unavailable_reason'],'changed'),edit(['domain','actor_lower_soldiers'],None),edit(['domain','enemy_upper_soldiers'],None),edit(['domain','enemy_force_coverage_complete'],False),edit(['domain','complete_initial_participants_ready'],False),edit(['domain','missing_required_domains'],['same_frame_two_round_observation'])],True)
add('partial_enemy',[edit(['domain','status'],'partial'),edit(['domain','owner_forces',1,'inventory_upper_ready'],False),edit(['domain','owner_forces',1,'inventory_upper_soldiers'],None),edit(['domain','owner_forces',1,'unavailable_reasons'],['not_observable']),edit(['domain','enemy_upper_soldiers'],None),edit(['domain','enemy_force_coverage_complete'],False),edit(['domain','missing_required_domains'],['enemy_current_inventory_upper'])],True)
add('partial_supporter_domain',[edit(['domain','status'],'partial'),edit(['domain','potential_enemy_participants','available'],False),edit(['domain','potential_enemy_participants','collection_complete'],False),edit(['domain','potential_enemy_participants','unavailable_reason'],'incomplete'),edit(['domain','potential_enemy_participants','current_allies_complete'],False),edit(['domain','enemy_upper_soldiers'],None),edit(['domain','enemy_force_coverage_complete'],False),edit(['domain','complete_initial_participants_ready'],False),edit(['domain','missing_required_domains'],['potential_enemy_current_allies','potential_enemy_participants'])],True)
extra=copy.deepcopy(domain['owner_forces'][1]);extra.update(owner_character_id=-2147483648,inventory_upper_soldiers=large)
participants=copy.deepcopy(domain['potential_enemy_participants']['participants'])+[dict(character_id=-2147483648,sources=['current_ally'])]
add('enemy_sum_overflow_is_unknown',[edit(['domain','status'],'partial'),edit(['domain','potential_enemy_participants','participants'],participants),edit(['domain','owner_forces'],[domain['owner_forces'][0],dict(domain['owner_forces'][1],inventory_upper_soldiers=large),extra]),edit(['domain','enemy_upper_soldiers'],None),edit(['domain','enemy_force_coverage_complete'],False),edit(['domain','missing_required_domains'],['enemy_upper_aggregate_overflow'])],True)
for path,value in [(['schema_version'],True),(['schema_version'],2.0),(['actor_lower_soldiers'],True),(['actor_lower_soldiers'],1500.0),(['ticket'],13.0),(['ticket'],True),(['ticket'],0),(['ticket'],1<<64),(['date_raw'],1<<31),(['date_raw'],False),(['read_only'],1),(['selected_declaration','target_title_ids'],[True]),(['selected_declaration','target_title_ids'],[91.0]),(['native_mobilization_qualification','native_unraised_stock_soldiers'],1<<31),(['native_mobilization_qualification','source'],'wrong'),(['native_mobilization_qualification','component_combination'],'sum'),(['native_mobilization_qualification','executable_lower_soldiers'],3000),(['native_mobilization_qualification','default_raise_province_id'],None),(['native_mobilization_qualification','unraised_lower_soldiers'],1501),(['native_mobilization_qualification','native_raise_legal'],False),(['final_cb_roles','primary_attacker_character_id'],-1),(['final_cb_roles','primary_defender_character_id'],-1),(['final_cb_roles','primary_defender_character_id'],domain['actor_character_id']),(['final_cb_roles','source'],'wrong'),(['final_cb_roles','unavailable_reason'],'contradiction'),(['two_round_observation','round_count'],3),(['two_round_observation','unavailable_reason'],'contradiction'),(['potential_enemy_participants','current_allies_complete'],False),(['potential_enemy_participants','collection_complete'],False),(['potential_enemy_participants','participants'],[]),(['potential_enemy_participants','participants',0,'sources'],[]),(['potential_enemy_participants','participants',0,'sources'],['unknown']),(['potential_enemy_participants','participants',0,'sources'],['primary_defender','primary_defender']),(['owner_forces',0,'inventory_upper_soldiers'],1499),(['owner_forces',1,'actor_lower_soldiers'],1),(['owner_forces',1,'actor_lower_ready'],True),(['owner_forces',0,'inventory_scope'],'wrong'),(['enemy_upper_soldiers'],1001),(['enemy_force_coverage_complete'],False),(['complete_initial_participants_ready'],False),(['missing_required_domains'],['final_cb_roles']),(['missing_required_domains'],['unknown']),(['missing_required_domains'],['final_cb_roles','final_cb_roles']),(['status'],'partial'),(['extra'],1)]:
    add('reject_domain_'+'.'.join(map(str,path))+'_'+str(len(cases)),[edit(['domain']+path,value)])
add('reject_duplicate_owner',[edit(['domain','owner_forces'],domain['owner_forces']+[domain['owner_forces'][1]])])
add('reject_missing_owner',[edit(['domain','owner_forces'],domain['owner_forces'][:1])])
add('reject_duplicate_participant',[edit(['domain','potential_enemy_participants','participants'],domain['potential_enemy_participants']['participants']*2)])
for root,path,value in [('receipt',['request_id'],'another'),('receipt',['ticket'],14),('receipt',['capture_epoch'],True),('receipt',['extra'],1),('snapshot',['paused'],False),('snapshot',['map_ready'],False),('snapshot',['revision'],2),('snapshot',['native_revision'],2),('snapshot',['capture_epoch'],18),('snapshot',['capture_epoch'],None),('snapshot',['played_character','alive'],False),('snapshot',['played_character','character_id'],2),('snapshot',['diagnostics','hello','expected_ck3_version'],'1.20.0.3'),('snapshot',['diagnostics','hello','expected_ck3_sha256'],'bad'),('snapshot',['declarable_wars'],[]),('snapshot',['declarable_wars'],[declaration,declaration]),('declaration',['declaration_id'],'0'+declaration['declaration_id']),('declaration',['target_title_ids'],[92]),('request_id',[], '\\u00a0unit-fresh-request'),('expected_capture_epoch',[],True),('policy',[],dict(policy,policy_id='prewar-current-inventory-force-risk-3-to-2-v1')),('policy',[],dict(policy,minimum_actor_to_enemy_ratio_numerator=3.0)),('policy',[],dict(policy,scope='wrong')),('policy',[],dict(policy,assumption='calibrated'))]:
    add('reject_'+root+'_'+'.'.join(map(str,path))+'_'+str(len(cases)),[edit([root]+path,value)])
for field in list(domain):add('missing_domain_'+field,[remove(['domain',field])])
refs=[]
for path in paths:
    raw=(repo/path).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=before[path]:raise RuntimeError('source changed during capture: '+path)
    refs.append(dict(path=path,bytes=len(raw),sha256=digest))
data=dict(schema='xar.coalition.original-producer-golden/v1',machine_id=current_machine_id(),observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,input_refs=[],scope='projection_not_original; unchanged real v2 normalizer and force-risk assessor; declared synthetic variants of existing original planner-input fixture; no Game/native query/action/ledger qualification',base=base,cases=cases)
raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>81920:raise RuntimeError('golden exceeds 80KiB')
with output.open('xb') as handle:handle.write(raw)
print(json.dumps(dict(machine_id=data['machine_id'],observed_at_utc=data['observed_at_utc'],cases=len(cases),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
""";
}
