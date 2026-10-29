package org.xar.ck3.control.wave2.military.holycost;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Real old normalizer capture using the existing whole-wire test's explicit synthetic callback constants. */
public final class CaptureHolyCostGolden {
    private CaptureHolyCostGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo python new-D-output required");
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (!output.startsWith(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1").toRealPath()) || Files.exists(output)) throw new IllegalArgumentException("new admitted D output required");
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-c", SCRIPT, args[0], output.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1"); builder.environment().put("OMP_NUM_THREADS", "1");
        Process child = builder.directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!child.waitFor(100, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IOException("holy-cost capture timeout; shared Job owns descendants"); }
        if (child.exitValue() != 0) throw new IOException("actual old holy-cost normalizer exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 65_536) throw new IOException("holy-cost golden exceeded 64KiB");
    }
    private static final String SCRIPT = """
import copy,datetime,hashlib,json,pathlib,sys
repo=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2])
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests')]
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_observation import normalize_player_ordinary_holy_war_declaration_context_v1,selected_ordinary_holy_war_declaration,RESOURCE_KEYS
from xar_autoplayer.bridge.version_identity import CK3_12003,CK3_12004
from test_player_ordinary_holy_war_declaration_context_12004_whole_wire import ACTOR,TARGET,ADDITIONAL,TITLE_IDS,FRAME,CB_COSTS_RAW
paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_observation.py','ck3_autonomous_player/src/xar_autoplayer/bridge/declaration_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_holy_war_defender_observation_v1.py','ck3_autonomous_player/tests/test_player_ordinary_holy_war_declaration_context_12003_whole_wire.py','ck3_autonomous_player/tests/test_player_ordinary_holy_war_declaration_context_12004_whole_wire.py','tools/ck3_live_run_id.py']
before={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
selected=dict(target_character_id=TARGET,casus_belli_index=0,casus_belli_key='religious_war',configuration_index=0,claimant_character_id=-1,target_title_ids=TITLE_IDS)
identity=str(TARGET)+'-0-0'
snapshot=dict(revision=FRAME['public_revision'],native_revision=FRAME['native_revision'],date_raw=FRAME['date_raw'],played_character=dict(character_id=ACTOR,alive=True),declarable_wars=[dict(selected,declaration_id=identity)],diagnostics=dict(hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))
context=dict(schema='player_ordinary_holy_war_declaration_context_v1',read_only=True,game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,available=True,unavailable_reason=None,capture_epoch=FRAME['capture_epoch'],public_revision=FRAME['public_revision'],native_revision=FRAME['native_revision'],date_raw=FRAME['date_raw'],played_character_id=ACTOR,declaration_id=identity,selected_declaration=selected,context_actor_character_id=ACTOR,context_recipient_character_id=TARGET,context_additional_role_character_id=ADDITIONAL,context_claimant_character_id=-1,recipient_uses_native_fallback=False,additional_role_uses_native_fallback=False,claimant_uses_native_fallback=True,final_can_send=False,cb_cost=dict(available=True,unavailable_reason=None,resource_keys=list(RESOURCE_KEYS),resource_costs_raw=CB_COSTS_RAW,raw_scale=100000),generic_interaction_cost_raw=None,total_declaration_cost_raw=None,total_cost_ready=False)
base=dict(context=copy.deepcopy(context),snapshot=copy.deepcopy(snapshot),declaration_id=identity,selected=copy.deepcopy(selected))
cases=[]
def edit(path,value):return dict(path=path,value_json=json.dumps(value,ensure_ascii=False,separators=(',',':')))
def remove(path):return dict(path=path,remove=True)
def add(name,edits=(),mode='normalize',harden=False):
    data=copy.deepcopy(base)
    for e in edits:
        parent=data
        for key in e['path'][:-1]:parent=parent[key]
        if e.get('remove'):del parent[e['path'][-1]]
        else:parent[e['path'][-1]]=json.loads(e['value_json'])
    untouched=copy.deepcopy(data)
    try:
        actual=selected_ordinary_holy_war_declaration(data['snapshot'],data['declaration_id']) if mode=='select' else normalize_player_ordinary_holy_war_declaration_context_v1(data['context'],snapshot=data['snapshot'],declaration_id=data['declaration_id'],selected_declaration=data['selected'])
        expected=dict(original_accepted=True,java_accepted=not harden)
        if not harden:expected['output']=actual
    except (ValueError,RuntimeError):expected=dict(original_accepted=False,java_accepted=False)
    if harden and not expected['original_accepted']:raise RuntimeError('intended original loose expectation comparison was not reproduced')
    if data!=untouched:raise RuntimeError('original holy-cost producer mutated input')
    cases.append(dict(id=name,mode=mode,strict_expectation_type_hardening=harden,edits=list(edits),expected=expected))
add('actual4_test_constants_synthetic_quote')
add('selected_actual4',mode='select')
add('known_zero_quote',[edit(['context','cb_cost','resource_costs_raw'],[0]*10)])
unavailable=[edit(['context','cb_cost','available'],False),edit(['context','cb_cost','unavailable_reason'],'cb_eval_unavailable'),edit(['context','cb_cost','resource_costs_raw'],None)]
add('unavailable_cb_quote',unavailable)
add('actual3_distinct_build',[edit(['context','game_version'],CK3_12003.game_version),edit(['context','executable_sha256'],CK3_12003.executable_sha256),edit(['snapshot','diagnostics','hello','expected_ck3_version'],CK3_12003.game_version),edit(['snapshot','diagnostics','hello','expected_ck3_sha256'],CK3_12003.executable_sha256)])
add('sha_original_case_preserved',[edit(['context','executable_sha256'],CK3_12004.executable_sha256.lower())])
add('hello_declared_legacy_field_projection',[remove(['snapshot','diagnostics','hello','expected_ck3_version']),remove(['snapshot','diagnostics','hello','expected_ck3_sha256']),edit(['snapshot','diagnostics','hello','game_version'],CK3_12004.game_version),edit(['snapshot','diagnostics','hello','executable_sha256'],CK3_12004.executable_sha256)])
unread=unavailable+[edit(['context','available'],False),edit(['context','unavailable_reason'],'unread'),edit(['context','final_can_send'],None)]
for key in ['context_actor_character_id','context_recipient_character_id','context_additional_role_character_id','context_claimant_character_id','recipient_uses_native_fallback','additional_role_uses_native_fallback','claimant_uses_native_fallback']:unread.append(edit(['context',key],None))
add('unread_context_preserves_null_roles',unread)
add('roles_keep_signed_generation_and_absent_handles',[edit(['context','context_actor_character_id'],-2147483648),edit(['context','context_recipient_character_id'],0),edit(['context','context_additional_role_character_id'],2147483647)])
add('signed_int64_cost_terms',[edit(['context','cb_cost','resource_costs_raw'],[-(1<<63),(1<<63)-1]+[0]*8)])
add('final_can_send_true_does_not_make_total_known',[edit(['context','final_can_send'],True)])
for path,value in [(['schema'],'wrong'),(['read_only'],1),(['available'],1),(['unavailable_reason'],'contradiction'),(['capture_epoch'],True),(['capture_epoch'],1007.0),(['capture_epoch'],0),(['capture_epoch'],1<<64),(['public_revision'],True),(['public_revision'],FRAME['public_revision']+1),(['native_revision'],FRAME['native_revision']+1),(['date_raw'],FRAME['date_raw']+1),(['date_raw'],1<<31),(['played_character_id'],1<<31),(['played_character_id'],ACTOR+1),(['game_version'],'1.20.0.2'),(['executable_sha256'],CK3_12003.executable_sha256),(['context_actor_character_id'],None),(['context_claimant_character_id'],-2147483649),(['recipient_uses_native_fallback'],0),(['final_can_send'],None),(['final_can_send'],1),(['selected_declaration','target_title_ids'],list(reversed(TITLE_IDS))),(['selected_declaration','target_character_id'],True),(['selected_declaration','extra'],0),(['cb_cost','available'],1),(['cb_cost','unavailable_reason'],'contradiction'),(['cb_cost','resource_keys'],list(reversed(RESOURCE_KEYS))),(['cb_cost','resource_costs_raw'],[0]*9),(['cb_cost','resource_costs_raw'],[True]+[0]*9),(['cb_cost','resource_costs_raw'],[0.0]+[0]*9),(['cb_cost','resource_costs_raw'],[1<<63]+[0]*9),(['cb_cost','raw_scale'],100000.0),(['cb_cost','extra'],1),(['generic_interaction_cost_raw'],0),(['total_declaration_cost_raw'],0),(['total_cost_ready'],True),(['total_cost_ready'],0),(['extra'],1)]:add('reject_'+'.'.join(map(str,path))+'_'+str(len(cases)),[edit(['context']+path,value)])
for key in list(context):add('missing_context_'+key,[remove(['context',key])])
for key in list(context['cb_cost']):add('missing_cb_cost_'+key,[remove(['context','cb_cost',key])])
add('unavailable_quote_cannot_invent_zeroes',[edit(['context','cb_cost','available'],False),edit(['context','cb_cost','unavailable_reason'],'unknown'),edit(['context','cb_cost','resource_costs_raw'],[0]*10)])
add('unread_context_cannot_have_final_gate',unread+[edit(['context','final_can_send'],False)])
add('selected_wrong_cb',[edit(['snapshot','declarable_wars',0,'casus_belli_key'],'county_conquest_cb')],mode='select')
add('selected_absent',[edit(['snapshot','declarable_wars'],[])],mode='select')
add('selected_duplicate_catalogue',[edit(['snapshot','declarable_wars'],snapshot['declarable_wars']*2)],mode='select')
add('selected_id_int32_ceiling',[edit(['snapshot','declarable_wars',0,'target_title_ids'],[1<<31])],mode='select')
for key in ['revision','native_revision','date_raw']:
    add('strict_snapshot_float_'+key,[edit(['snapshot',key],float(snapshot[key]))],harden=True)
add('strict_expected_selected_float',[edit(['selected','target_character_id'],float(TARGET))],harden=True)
refs=[]
for p in paths:
    raw=(repo/p).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=before[p]:raise RuntimeError('source changed during capture: '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=digest))
data=dict(schema='xar.holycost.original-producer-golden/v1',machine_id=current_machine_id(),observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,input_refs=[],scope='projection_not_original; unchanged real selected/current CB-only normalizer with explicitly synthetic callback inputs copied from existing whole-wire test constants; no compiled native packet generated, Game/private query/total-cost/action qualification',base=base,cases=cases)
raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>65536:raise RuntimeError('holy-cost golden exceeds 64KiB')
with output.open('xb') as handle:handle.write(raw)
print(json.dumps(dict(machine_id=data['machine_id'],observed_at_utc=data['observed_at_utc'],cases=len(cases),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
""";
}
