package org.xar.ck3.control.g2.m7.producer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Test-only caller of unchanged production functions on explicit synthetic observations. */
public final class M7OriginalProducerCapture {
    private static final int MAX_BYTES = 262_144;
    private M7OriginalProducerCapture() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output"); }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("original capture is create-only"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(MAX_BYTES + 1));
            if (!child.waitFor(Duration.ofSeconds(90).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original M7 producer capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally {
            if (child.isAlive()) { child.destroyForcibly(); }
        }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > MAX_BYTES) {
            throw new IllegalStateException("original M7 producer capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original M7 producer: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,copy,datetime,importlib.util
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root));sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/ordinary_campaign_government_context_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/government_runtime_adapter_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/tests/unit/test_ordinary_campaign_government_context_leaf_v1.py','ck3_autonomous_player/tests/unit/test_succession_transition_contract.py','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/hello.json','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/initial-state.json','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/government-response-red.json']
            def refs():
                result=[]
                for rel in relatives:
                    raw=(root/rel).read_bytes();result.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
                return result
            before=refs()
            import test_ordinary_campaign_government_context_leaf_v1 as fixture
            import test_succession_transition_contract as transition_fixture
            from xar_autoplayer.ordinary_campaign_government_context_v1 import build_ordinary_campaign_government_context_v1 as government
            from xar_autoplayer.strategy import new_ordinary_campaign_goal_v1 as new_goal,normalize_ordinary_campaign_goal_v1 as normalize_goal,continue_ordinary_campaign_goal_v1 as continue_goal,ordinary_campaign_goal_plan_v1 as plan_goal
            from xar_autoplayer.bridge.succession_transition_contract import freeze_succession_expectation_v1 as freeze,reconcile_succession_transition_v1 as reconcile
            snapshot,observation=fixture._ordinary_fixture_inputs()
            def projected(source):
                value={key:copy.deepcopy(source[key]) for key in ('native_revision','date_raw','campaign_goal') if key in source}
                value['played_character']={'character_id':source['played_character']['character_id']}
                value['succession_lifecycle']={'lifecycle':source['succession_lifecycle']['lifecycle']}
                hello=source['diagnostics']['hello'];value['diagnostics']={'hello':{key:copy.deepcopy(hello[key]) for key in ('expected_ck3_version','expected_ck3_sha256','game_version','executable_sha256') if key in hello}}
                return value
            government_cases=[]
            def add_government(name,key,query=True,goal_actor=None):
                source=projected(snapshot);observed=copy.deepcopy(observation);observed['government']['key']=key
                if goal_actor is not None:source['campaign_goal']['current_character_id']=goal_actor
                request={'schema':'xar.java-government-context-request/v1','snapshot':source,'government_observation':observed,'query_permitted':query}
                expected=government(source,government_observation=observed,query_permitted=query)
                government_cases.append({'name':name,'scope':'synthetic explicit key variation of retained primitive; no current native observation','input':request,'expected':expected})
            add_government('feudal_same_ruler','feudal_government')
            add_government('clan_same_core_family_distinct_key','clan_government')
            add_government('clan_default_query_off','clan_government',False)
            add_government('clan_goal_current_actor_mismatch','clan_government',True,100)
            case=transition_fixture.SuccessionTransitionContractTests();case.setUp()
            expectation=freeze(case.pre,episode_run_id='native-100-test',episode_character_id=100)
            reconciled=reconcile(expectation,case.snapshot,case.post)
            if reconciled['verdict']!='matched' or len(reconciled)!=18:raise RuntimeError('original complete reconciliation differs')
            original_goal=new_goal('m7-original-producer-fixture',100)
            original_before=copy.deepcopy(original_goal)
            continued=continue_goal(original_goal,reconciled)
            if original_goal!=original_before:raise RuntimeError('original continuation mutated its input')
            goal_cases=[{'name':'goal_new','operation':'goal_new','input':{'campaign_id':'m7-original-producer-fixture','character_id':100},'expected':original_goal},{'name':'goal_normalize','operation':'goal_normalize','input':original_goal,'expected':normalize_goal(original_goal)},{'name':'goal_initial_plan','operation':'goal_plan','input':original_goal,'expected':plan_goal(original_goal)},{'name':'goal_continue_original_complete_reconciliation','operation':'goal_continue','input':{'goal':original_goal,'reconciliation':reconciled},'expected':continued},{'name':'goal_successor_normalize','operation':'goal_normalize','input':continued,'expected':normalize_goal(continued)},{'name':'goal_successor_plan','operation':'goal_plan','input':continued,'expected':plan_goal(continued)}]
            rejections=[]
            for name,verdict in [('unknown_transition','unknown'),('unexpected_successor','unexpected_successor'),('title_distribution_mismatch','title_distribution_mismatch')]:
                item=copy.deepcopy(reconciled);item['verdict']=verdict
                try:continue_goal(original_goal,item)
                except ValueError as error:rejections.append({'name':name,'operation':'goal_continue','input':{'goal':original_goal,'reconciliation':item},'legacy_error':str(error),'expected_java_rejection':True})
                else:raise RuntimeError('original unknown/mismatch unexpectedly continued')
            item=copy.deepcopy(reconciled);item['predecessor_character_id']=101
            try:continue_goal(original_goal,item)
            except ValueError as error:rejections.append({'name':'wrong_predecessor','operation':'goal_continue','input':{'goal':original_goal,'reconciliation':item},'legacy_error':str(error),'expected_java_rejection':True})
            else:raise RuntimeError('original wrong predecessor unexpectedly continued')
            strict_rejections=[]
            for field,token in [('format_version',True),('format_version',1.0),('origin_character_id',True),('current_character_id',100.0)]:
                value=copy.deepcopy(original_goal);value[field]=token
                try:normalize_goal(value);legacy='accepted'
                except ValueError:legacy='rejected'
                strict_rejections.append({'name':field+'_'+type(token).__name__,'operation':'goal_normalize','input':value,'legacy_result':legacy,'expected_java_rejection':True})
            for token in [None,True,1.0,'1',-1]:
                value=copy.deepcopy(original_goal);value['progress']['reconciled_successions']=token
                strict_rejections.append({'name':'progress_'+repr(token),'operation':'goal_normalize','input':value,'expected_java_rejection':True})
            for item in goal_cases+rejections+strict_rejections:
                item['raw_input_json']=json.dumps(item['input'],ensure_ascii=False,separators=(',',':'),allow_nan=False)
            after=refs()
            if before!=after:raise RuntimeError('original producer sources changed during capture')
            from tools.ck3_live_run_id import current_machine_id
            output={'schema':'xar.g2-m7-original-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Unchanged production government/goal/freeze/reconciliation functions on explicit fixture frames; no true Driver/SAVE body, Game, native query, new writer or live qualification. Known raw-token tightening is recorded separately.','source_refs':before,'source_refs_unchanged':True,'government_cases':government_cases,'goal_cases':goal_cases,'goal_rejections':rejections,'strict_token_rejections':strict_rejections,'complete_reconciliation':reconciled,'predecessor_expectation':expectation,'original_inputs_unchanged':original_goal==original_before}
            print(json.dumps(output,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
