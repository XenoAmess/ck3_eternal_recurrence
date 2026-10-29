package org.xar.ck3.control.wave2.events.choiceplanning;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit fixture capture only. Default JUnit never runs Python; the shared Job owner schedules this main. */
public final class ChoicePlanningGoldenCapture {
    private ChoicePlanningGoldenCapture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository output_path existing_python required"); }
        Path repository = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path taskLogs = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize().getParent().resolve("logs");
        if ((!output.startsWith(repository.resolve("java/ck3-control/wave2-events/src/test/resources/choiceplanning"))
                && !output.startsWith(taskLogs)) || Files.exists(output)) { throw new IllegalArgumentException("new exact lane output required"); }
        Files.createDirectories(output.getParent());
        String script = """
import sys,json,copy,runpy,hashlib,datetime
from pathlib import Path
r=Path(sys.argv[1]); output=Path(sys.argv[2]); sys.path.insert(0,str(r/'ck3_autonomous_player/src'))
t=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_mandatory_choice_planning_v1.py'))
same=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_mandatory_choice_same_typed_event_v1.py'))
from xar_autoplayer.mandatory_choice_planning_v1 import plan_native_mandatory_choice_v1,QUERY_STEP,SELECT_STEP,QUERY_CAPABILITY
cases=[]
def emit(name,snapshot,commands=(),steps=None,caps=None):
    steps=[QUERY_STEP] if steps is None else steps; caps=[QUERY_CAPABILITY] if caps is None else caps
    request={'schema':'xar.java-mandatory-choice-planning-request/v1','snapshot':copy.deepcopy(snapshot),'commands':copy.deepcopy(list(commands)),'action_steps':sorted(steps),'bridge_capabilities':sorted(caps)}
    result=plan_native_mandatory_choice_v1(list(commands),snapshot=snapshot,action_steps=steps,bridge_capabilities=caps)
    cases.append({'name':name,'request':request,'output':copy.deepcopy(result)})
emit('no_snapshot',None)
emit('query_before_select',t['snapshot']())
emit('actual_native_catalogue_order',t['snapshot'](),[t['query_row']()])
emit('capability_missing',t['snapshot'](),caps=[])
s=t['snapshot'](); s['played_character']={}; emit('incomplete_frame',s)
s=t['snapshot'](); s['played_character']={}; s['active_event']={'instance_id':9}; emit('typed_event_frame_unavailable_keeps_priority',s)
s=t['snapshot'](); s['pending_character_interaction']={'instance_id':99}; emit('interaction_keeps_priority',s,[t['query_row']()])
s=t['snapshot'](); s['top_exclusive_modal_choice_hint']['owner_verified']=False; emit('unverified_hint',s)
q=t['query_row'](); q['ok']=False; emit('failed_query_no_retry',t['snapshot'](),[q])
q=t['query_row'](); q['result']['queried_native_revision']-=1; emit('stale_query_requests_fresh_query',t['snapshot'](),[q])
q=t['query_row'](); q['result']['mandatory_choice']['schema']='other'; emit('malformed_query',t['snapshot'](),[q])
q=t['query_row'](); q['result']['mandatory_choice']['choices_complete']=False; emit('incomplete_catalogue_no_select',t['snapshot'](),[q])
q={'command':'auto-turn','ok':True,'result':{'auto_turn':{'selected_step':QUERY_STEP,'result':t['query_row']()['result']}}}; emit('nested_auto_turn_query',t['snapshot'](),[q])
s=t['snapshot'](); s['active_event']={'instance_id':9}; emit('typed_event_without_root_proof',s,[t['query_row']()])
prior={'command':'auto-turn','ok':True,'result':{'auto_turn':{'selected_step':SELECT_STEP,'status':'pending','result':{'accepted':True,'verification_pending':True},'plan':{'unknown_mandatory_choice_v1':{'frame_binding':t['frame'](),'native_window':t['dto']()}}}}}
emit('pending_same_instance_no_second_token',t['snapshot'](),[prior,t['query_row']()])
q=t['query_row'](); q['result']['mandatory_choice']['window_instance_id']='new-instance'; emit('different_instance_not_prior_instance',t['snapshot'](),[prior,q])
rows,s= same['_case'](); emit('actual_p09_same_root_unavailable_event',s,rows,steps=[QUERY_STEP,SELECT_STEP])
rows,s= same['_case'](); rows[0]['result']['auto_turn']['result']['queried_native_revision']-=1; emit('stale_typed_event_read_no_borrow',s,rows,steps=[QUERY_STEP,SELECT_STEP])
rows,s= same['_case'](); rows[-1]['result']['mandatory_choice']['typed_window_relation']['typed_window_instance_id']=52; emit('wrong_typed_instance_no_borrow',s,rows)
rows,s= same['_case'](); c=rows[0]['result']['auto_turn']['result']['current_event_window_context']; c.update(event_definition_key='stewardship_general.1054',calculated_event_id=21054,runtime_stats_ordinal=3); c['readiness']['event_definition_identity_ready']=True; emit('actual_unavailable_partial_identity_stays_nonactionable',s,rows)
paths=['ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_planning_v1.py','ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_policy_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/event_window_context_contract.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_planning_v1.py','ck3_autonomous_player/tests/unit/test_mandatory_choice_same_typed_event_v1.py','ck3_autonomous_player/tests/fixtures/mandatory_choice_v1/native-query-event-same-root.json','ck3_autonomous_player/tests/fixtures/mandatory_choice_v1/p09-event53-unavailable-typed-query.json']
sources=[{'path':p,'sha256':hashlib.sha256((r/p).read_bytes()).hexdigest()} for p in paths]
body={'schema':'xar.java-choice-planning-golden/v1','provenance':{'machine_id':'xenoamess-full-tower-eb9d2c1186','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'actual unmodified Python planner calls; existing offline Native wire and P09 projected source fixture; no live qualification','sources':sources},'cases':cases}
raw=(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode()
if len(raw)>102400: raise RuntimeError('golden exceeds finite 100 KiB cap')
with output.open('xb') as handle: handle.write(raw)
print(json.dumps({'cases':len(cases),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'output':str(output)}))
""";
        ProcessBuilder builder = new ProcessBuilder(arguments[2], "-c", script, repository.toString(), output.toString());
        builder.directory(repository.toFile()); builder.redirectErrorStream(true);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        if (!process.waitFor(Duration.ofSeconds(75).toMillis(), TimeUnit.MILLISECONDS)) {
            process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
            throw new IllegalStateException("actual producer capture timed out");
        }
        byte[] log = process.getInputStream().readNBytes(16_384);
        System.out.print(new String(log, StandardCharsets.UTF_8));
        if (process.exitValue() != 0) { throw new IllegalStateException("actual producer exit " + process.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) > 102_400) { throw new IllegalStateException("golden output missing or oversized"); }
    }
}
