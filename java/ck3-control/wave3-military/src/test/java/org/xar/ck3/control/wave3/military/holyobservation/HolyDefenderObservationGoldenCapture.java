package org.xar.ck3.control.wave3.military.holyobservation;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Captures the unchanged original Python readers and ordinary planner, using disclosed synthetic callback inputs. */
public final class HolyDefenderObservationGoldenCapture {
    private HolyDefenderObservationGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository python retained-holycost-golden new-output required"); }
        Path output = Path.of(arguments[3]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("new admitted output required"); }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, arguments[0], arguments[2], output.toString()));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1");
        Process child = builder.directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IOException("original holy observation capture timeout; shared Job owns descendants"); }
        if (child.exitValue() != 0) { throw new IOException("original holy observation capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) < 1 || Files.size(output) > 65_536) { throw new IOException("bounded original capture missing or oversized"); }
    }
    private static final String SCRIPT = """
import copy,datetime,gzip,hashlib,json,pathlib,sys,types
repo=pathlib.Path(sys.argv[1]);basepath=pathlib.Path(sys.argv[2]);output=pathlib.Path(sys.argv[3])
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.player_holy_war_defender_join_inputs import normalize_holy_war_defender_join_inputs
from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_observation import normalize_player_ordinary_holy_war_declaration_context_v1
from xar_autoplayer.ordinary_holy_war_defender_observation_v1 import project_ordinary_holy_war_defender_observation_v1,plan_ordinary_holy_war_defender_observation_v1
from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_transport import PERMISSION
from xar_autoplayer.bridge.version_identity import CK3_12003
basebytes=basepath.read_bytes()
if len(basebytes)!=41847 or hashlib.sha256(basebytes).hexdigest()!='e3c1b7d8d306e4a022b1f70200162ef84f21bf4f8d3a10c92c153cd734a5ed32':raise RuntimeError('retained original holycost base drift')
base=json.loads(basebytes)['base'];snapshot=copy.deepcopy(base['snapshot']);owner=copy.deepcopy(base['context'])
snapshot.update(snapshot_id='synthetic-original-ordinary-plan-frame',paused=True,map_ready=True,active_event=None,pending_character_interaction=None,active_wars=[dict(war_id=100663329)])
owner=normalize_player_ordinary_holy_war_declaration_context_v1(owner,snapshot=snapshot,declaration_id=base['declaration_id'],selected_declaration=base['selected'])
child={key:copy.deepcopy(owner[key]) for key in ['capture_epoch','native_revision','public_revision','date_raw','played_character_id','declaration_id','selected_declaration']}
child.update(schema='ck3_12004_holy_war_defender_join_inputs_v1',read_only=True,available=True,unavailable_reason=None,primary_attacker_character_id=owner['context_additional_role_character_id']&0xffffffff,primary_defender_character_id=owner['context_recipient_character_id']&0xffffffff,primary_defender_faith_available=True,primary_defender_faith_unavailable_reason=None,primary_defender_rite_id=0,primary_defender_faith_id=0,cb_flags_raw=32768,defender_faith_can_join=True,native_joiner_set_observed=True,joiner_count=1,joiners=[dict(character_id=0,row_faith_available=True,row_fervor_available=True,unavailable_reason=None,rite_id=0,faith_id=0,faith_fervor_raw=0,matches_primary_defender_faith=True)],raw_scale=100000,unit='fervor_points',is_final_join_score=False)
query=copy.deepcopy(owner);query.update(player_holy_war_defender_join_inputs=child,query_status='observed',backend_id='synthetic-original-normalized-query')
planned=dict(revision=snapshot['revision'],plan=dict(phase='native_war_pursuit',selected_step='life-advance',reason='existing active-war continuation',decision=dict(decision='continue_current_war')),sdk=dict(float=1.0,zero=-0.0,id=18446744073709551615,empty=[],nil=None))
paths=['ck3_autonomous_player/src/xar_autoplayer/ordinary_holy_war_defender_observation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_war_defender_join_inputs.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_observation.py','ck3_autonomous_player/src/xar_autoplayer/bridge/declaration_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','tools/ck3_live_run_id.py']
pins={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths};cases=[]
def add(name,operation='project',edit=None,permission=True,query_available=True,error=None,diagnostic=False):
    s,q,p=copy.deepcopy(snapshot),copy.deepcopy(query),copy.deepcopy(planned)
    if edit:edit(s,q,p)
    request=dict(schema='xar.ck3.holy-defender-project-input.v1',normalized_query=q,snapshot=s) if operation=='project' else dict(schema='xar.ck3.holy-defender-normalize-input.v1',value=q['player_holy_war_defender_join_inputs'],current_context={k:v for k,v in q.items() if k in owner},snapshot=s) if operation=='normalize' else dict(schema='xar.ck3.holy-defender-plan-input.v1',planned=p,snapshot=s,permission=permission,query_available=query_available,normalized_query=q,query_error=error)
    calls=[]
    def normalize_actual():
        core={k:v for k,v in q.items() if k in owner}
        actual_owner=normalize_player_ordinary_holy_war_declaration_context_v1(core,snapshot=s,declaration_id=q['declaration_id'],selected_declaration=q['selected_declaration'])
        c=q.get('player_holy_war_defender_join_inputs')
        if c is not None:q['player_holy_war_defender_join_inputs']=normalize_holy_war_defender_join_inputs(c,current_context=actual_owner,snapshot=s)
    try:
        if operation!='fold':normalize_actual()
        if operation=='normalize':expected=q['player_holy_war_defender_join_inputs']
        elif operation=='project':expected=project_ordinary_holy_war_defender_observation_v1(q,snapshot=s)
        else:
            def read(**kwargs):
                calls.append(kwargs)
                if error is not None:raise OSError(error)
                normalize_actual()
                return copy.deepcopy(q)
            driver=types.SimpleNamespace(**{PERMISSION:permission});service=types.SimpleNamespace(driver=driver)
            if query_available:service.query_player_ordinary_holy_war_declaration_context_private_v1=read
            expected=plan_ordinary_holy_war_defender_observation_v1(service,planned=p,snapshot=s)
        cases.append(dict(name=name,operation=operation,input=request,accepted=True,expected=expected,original_query_calls=len(calls),diagnostic_reason_text_reimplemented=diagnostic))
    except ValueError as rejection:cases.append(dict(name=name,operation=operation,input=request,accepted=False,original_error=str(rejection)))
add('complete-native-set-legal-zero')
add('strict-normalizer-original','normalize')
add('child-not-returned',edit=lambda s,q,p:q.pop('player_holy_war_defender_join_inputs'))
add('child-null',edit=lambda s,q,p:q.update(player_holy_war_defender_join_inputs=None))
def empty(s,q,p):q['player_holy_war_defender_join_inputs'].update(joiner_count=0,joiners=[])
add('observed-empty-native-set',edit=empty)
def disabled(s,q,p):empty(s,q,p);q['player_holy_war_defender_join_inputs'].update(cb_flags_raw=0,defender_faith_can_join=False)
add('observed-disabled-native-branch',edit=disabled)
def failed(s,q,p):q['player_holy_war_defender_join_inputs']['joiners'][0].update(row_fervor_available=False,faith_fervor_raw=None,unavailable_reason='synthetic native getter failure')
add('set-remains-observed-after-fervor-failure',edit=failed)
def duplicate(s,q,p):c=q['player_holy_war_defender_join_inputs'];c.update(joiner_count=2,joiners=c['joiners']*2)
add('ordered-duplicate-native-occurrences',edit=duplicate)
def full(s,q,p):q['player_holy_war_defender_join_inputs']['joiners'][0].update(character_id=4294967295,rite_id=4294967295,faith_id=4294967295,faith_fervor_raw=-(1<<63),matches_primary_defender_faith=False)
add('full-unsigned-id-and-signed-fervor',edit=full)
def unknown(s,q,p):empty(s,q,p);q['player_holy_war_defender_join_inputs'].update(available=False,native_joiner_set_observed=False,unavailable_reason='synthetic unobserved native set')
add('unknown-native-set-stays-unknown',edit=unknown)
def actual3(s,q,p):q.update(game_version=CK3_12003.game_version,executable_sha256=CK3_12003.executable_sha256);s['diagnostics']['hello'].update(expected_ck3_version=CK3_12003.game_version,expected_ck3_sha256=CK3_12003.executable_sha256);q['player_holy_war_defender_join_inputs']['schema']='ck3_12003_holy_war_defender_join_inputs_v1'
add('distinct-exact3-owner-schema',edit=actual3)
add('existing-fullplanner-action-retained','fold')
add('permission-off-retains-plan','fold',permission=False)
add('missing-query-method-retains-current-action','fold',query_available=False)
add('actual-query-error-retains-current-action','fold',error='original one-shot query unavailable')
add('no-war-only-observation','fold',edit=lambda s,q,p:s.update(active_wars=[]))
add('nonobject-plan-passes-through','fold',edit=lambda s,q,p:p.update(plan=None))
add('no-ordinary-candidate','fold',edit=lambda s,q,p:s.update(declarable_wars=[]))
add('native-catalogue-unavailable','fold',edit=lambda s,q,p:s.update(declarable_wars=None),diagnostic=True)
add('planned-revision-float-is-not-ready','fold',edit=lambda s,q,p:p.update(revision=float(p['revision'])))
add('snapshot-native-revision-bool-is-not-ready','fold',edit=lambda s,q,p:s.update(native_revision=True))
for key in ['paused','map_ready']:
    add('frame-not-ready-'+key,'fold',edit=lambda s,q,p,key=key:s.update(**{key:False}))
for key in ['active_event','pending_character_interaction']:
    add('frame-blocker-'+key,'fold',edit=lambda s,q,p,key=key:s.update(**{key:{'id':1}}))
for key,value in [('capture_epoch',True),('native_revision',1.0),('public_revision',0),('date_raw',True),('played_character_id',1.0),('joiner_count',True),('joiner_count',2),('cb_flags_raw',True),('defender_faith_can_join',False),('is_final_join_score',True),('extra',1)]:
    add('reject-child-'+key+'-'+str(len(cases)),'normalize',edit=lambda s,q,p,key=key,value=value:q['player_holy_war_defender_join_inputs'].update(**{key:value}))
add('reject-child-missing-field','normalize',edit=lambda s,q,p:q['player_holy_war_defender_join_inputs'].pop('joiners'))
add('reject-child-declaration-mismatch','normalize',edit=lambda s,q,p:q['player_holy_war_defender_join_inputs'].update(declaration_id='other'))
def fallback(s,q,p):q.update(additional_role_uses_native_fallback=True)
add('reject-observed-native-fallback','normalize',edit=fallback)
refs=[]
for p in paths:
    raw=(repo/p).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=pins[p]:raise RuntimeError('original source changed: '+p)
    refs.append(dict(path=p,bytes=len(raw),sha256=digest))
data=dict(schema='xar.holy-defender-original-producer-golden/v1',machine_id=current_machine_id(),observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,base_ref=dict(path=str(basepath),bytes=len(basebytes),sha256=hashlib.sha256(basebytes).hexdigest()),actual_original_functions=True,synthetic_world_and_callback_outcomes=True,native_compiled_packet_qualification=False,game_calls=0,cases=cases)
raw=(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\\n').encode()
if len(raw)>524288:raise RuntimeError('expanded capture bound exceeded')
compressed=gzip.compress(raw,mtime=0)
if len(compressed)>65536:raise RuntimeError('compressed capture bound exceeded')
with output.open('xb') as stream:stream.write(compressed)
print(json.dumps(dict(machine_id=data['machine_id'],observed_at_utc=data['observed_at_utc'],cases=len(cases),bytes=len(compressed),sha256=hashlib.sha256(compressed).hexdigest(),actual_original_functions=True,game_calls=0)))
""";
}
