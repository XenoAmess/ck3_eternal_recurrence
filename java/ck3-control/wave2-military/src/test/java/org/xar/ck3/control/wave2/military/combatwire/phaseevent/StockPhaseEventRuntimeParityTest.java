package org.xar.ck3.control.wave2.military.combatwire.phaseevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.combatwire.phaseevent.PhaseJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.math.BigInteger;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.forecast.CombatCore;

/** Actual original producer and evaluator, all 13 families, full projections and ordered state feedback. */
class StockPhaseEventRuntimeParityTest {
    private static final StockPhaseEventRuntime RUNTIME=new StockPhaseEventRuntime();
    private static ObjectNode original;
    @TempDir Path temporary;
    private static final String CAPTURE="""
        import copy,json,runpy,sys,dataclasses
        from pathlib import Path
        root=Path(sys.argv[1])
        test=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_phase_event_ast_evaluator.py'))
        cls=test['PhaseEventAstEvaluatorTests'];cls.setUpClass();instance=cls()
        from xar_autoplayer.simulation.phase_event_evaluator import audit_stock_phase_event_evaluator,evaluate_phase_event_contexts,evaluate_phase_event_reachable_feedback,execute_phase_event_effect,execute_phase_event_trial_sequence
        from xar_autoplayer.simulation.candidate_source_proof import candidate_source_sequence_sha256
        from xar_autoplayer.simulation.phase_event_feedback import PhaseEventFeedbackInput,PhaseEventFeedbackResearchKernel
        from xar_autoplayer.simulation.combat_core import DrawState
        families=[]
        for family in cls.golden['families']:
            context=instance._valid_context(family['key'],family['type']);draws=[0]*family['draw_count']
            families.append({'key':family['key'],'context':context,'draws':draws,'result':execute_phase_event_effect(context,event_key=family['key'],draws=draws,advantage_model=cls.advantage)})
        context=instance._valid_context('commander_wounded','commander')
        steps=(('commander_wounded',(0,0)),('commander_killed',(0,0)))
        variants=[]
        def variant(name,c,draws,advantage=None):
            variants.append({'name':name,'context':c,'draws':draws,'advantage':advantage,'result':execute_phase_event_effect(c,event_key='commander_wounded',draws=draws,advantage_model=advantage)})
        c=copy.deepcopy(context);c['native_state_refs']['root.traits.wounded.rank_raw']=300000;variant('rank-three-death-detach',c,[0,0])
        variant('selected-enemy-prowess-writeback',copy.deepcopy(context),[0,1342177280])
        c=copy.deepcopy(context);template=c['candidate_rows'][0];rows=[]
        for i,id in enumerate([101,102,103,104]):
            candidate=copy.deepcopy(template);candidate['character_id']=id;p=0 if id==102 else 10000000
            candidate['candidate_refs']['candidate.skills.prowess_raw']=p;candidate['selected_enemy_knight_refs']['selected_enemy_knight.skills.prowess_raw']=p;rows.append(candidate)
        c['candidate_rows']=rows
        for path in ['enemy_side.character_membership','combat_side.ordered_enemy_knights']:
            owner=c['native_state_refs'] if path in c['native_state_refs'] else c['offline_state_refs'];owner[path]=[101,102,103,104]
        proof=c['candidate_source_proof'];commanders=[x for x in proof['ordered_sources'] if x['role']=='commander'];army=next(x['source_army_id'] for x in proof['ordered_sources'] if x['role']=='knight')
        proof['ordered_sources']=commanders+[{'role':'knight','source_army_id':army,'source_regiment_id':10000+i,'character_id':id} for i,id in enumerate([101,102,103,104])]
        proof['sequence_sha256']=candidate_source_sequence_sha256(c['enemy_side_index'],proof['ordered_sources']);variant('tail-swap-not-stable-filter',c,[0,0])
        feedback_context=copy.deepcopy(cls.commander_context);day0=(-feedback_context['root_character_id'])%5
        feedback=PhaseEventFeedbackResearchKernel().project_trial(PhaseEventFeedbackInput(feedback_context,role='commander',start_day_index=day0,effect_draws_by_day={day0:{'commander_wounded':(0,0)}}),selection_state=DrawState(0,21),horizon_days=6)
        print(json.dumps({'audit':audit_stock_phase_event_evaluator(),'contexts':cls.contexts,'projection':evaluate_phase_event_contexts(cls.contexts),'reachable':evaluate_phase_event_reachable_feedback(cls.contexts),'advantage':cls.advantage,'families':families,'sequence_context':context,'sequence':execute_phase_event_trial_sequence(context,steps=steps,advantage_model=cls.advantage),'variants':variants,'feedback_context':feedback_context,'feedback_start_day':day0,'feedback':dataclasses.asdict(feedback)},separators=(',',':')))
        """;
    @BeforeAll static void captureActualOriginal() throws Exception {
        String repo=required("xar.repository.root"),python=required("xar.python");Path root=Path.of(repo);assertTrue(Files.isRegularFile(Path.of(python)),"required original Python executable missing");pins(root);
        Process process=new ProcessBuilder(python,"-I","-c",CAPTURE,repo).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try{byte[] bytes=assertTimeoutPreemptively(Duration.ofSeconds(120),()->process.getInputStream().readAllBytes());assertTrue(process.waitFor(10,TimeUnit.SECONDS),"original producer did not terminate");assertEquals(0,process.exitValue(),"actual original producer failed");original=object(JSON.readTree(bytes),"capture");pins(root);}finally{process.getInputStream().close();process.getOutputStream().close();if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(10,TimeUnit.SECONDS),"producer survived termination");}}
    }
    @Test void allAstRowsAuditAndRealProducerContextsMatchFullCanonicalProjection() throws Exception {
        assertSameJson(original.get("audit"),RUNTIME.audit(),"whole 688-node audit");assertEquals(688,RUNTIME.audit().path("coverage").path("ast_node_count").intValue());assertEquals(132,RUNTIME.requiredStateRefs().size());assertEquals(11,RUNTIME.sourcePins().size());
        ArrayNode contexts=(ArrayNode)original.get("contexts");assertSameJson(original.get("projection"),RUNTIME.evaluateContexts(contexts),"whole context projection");assertSameJson(original.get("reachable"),RUNTIME.evaluateReachableFeedback(contexts),"whole reachable-feedback projection");
        ArrayNode roundtrip=(ArrayNode)JSON.readTree(JSON.writeValueAsBytes(contexts));assertSameJson(original.get("projection"),RUNTIME.evaluateContexts(roundtrip),"serialized context roundtrip");ObjectNode detached=RUNTIME.audit();detached.put("ast_evaluator_ready",true);assertFalse(RUNTIME.audit().path("ast_evaluator_ready").booleanValue());
    }
    @Test void allThirteenEffectFamiliesAndOrderedTrialWritebackMatchActualProducer() throws Exception {
        assertEquals(13,original.path("families").size());for(JsonNode family:original.get("families")){ObjectNode result=RUNTIME.executeEffect(family.get("context"),family.path("key").asText(),draws(family.get("draws")),original.get("advantage"),true);assertSameJson(family.get("result"),result,"entire family "+family.path("key").asText());assertFalse(result.path("planner_usable").booleanValue());assertFalse(result.path("active_attack_allowed").booleanValue());JsonNode reloaded=JSON.readTree(JSON.writeValueAsBytes(result));assertSameJson(result,reloaded,"result serialization roundtrip");}
        List<StockPhaseEventRuntime.TrialStep> steps=List.of(new StockPhaseEventRuntime.TrialStep("commander_wounded",List.of(0,0)),new StockPhaseEventRuntime.TrialStep("commander_killed",List.of(0,0)));assertSameJson(original.get("sequence"),RUNTIME.executeTrialSequence(original.get("sequence_context"),steps,original.get("advantage")),"ordered state and commander removal");
        for(JsonNode v:original.get("variants"))assertSameJson(v.get("result"),RUNTIME.executeEffect(v.get("context"),"commander_wounded",draws(v.get("draws")),v.get("advantage"),true),v.path("name").asText());
    }
    @Test void strictInputsRejectMissingWrongFieldBoolFloatSourceDriftAndUnknownResults() {
        ObjectNode context=original.get("sequence_context").deepCopy();ArrayNode singleton=arr().add(context);
        ObjectNode missing=context.deepCopy();missing.remove("root_source_regiment_id");assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(missing)));
        ObjectNode extra=context.deepCopy();extra.put("unmigrated_alias",false);assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(extra)));
        for(JsonNode invalid:List.of(J.booleanNode(true),J.numberNode(1.0),J.nullNode())){ObjectNode c=context.deepCopy();c.set("root_character_id",invalid);assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(c)));}
        ObjectNode overlap=context.deepCopy();object(overlap.get("offline_state_refs"),"refs").set("root.exists",J.booleanNode(true));assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(overlap)));
        ObjectNode proof=context.deepCopy();object(proof.get("candidate_source_proof"),"proof").put("sequence_sha256","0".repeat(64));assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(proof)));
        assertThrows(IllegalArgumentException.class,()->RUNTIME.executeEffect(context,"caller_defined_effect",List.of()));assertThrows(IllegalArgumentException.class,()->RUNTIME.executeEffect(context,"commander_wounded",List.of()));assertThrows(IllegalArgumentException.class,()->RUNTIME.executeEffect(context,"knight_none",List.of()));assertThrows(IllegalArgumentException.class,()->RUNTIME.executeTrialSequence(context,List.of(new StockPhaseEventRuntime.TrialStep("commander_none",List.of(0))),null));
        ObjectNode noScope=context.deepCopy();object(noScope.get("native_state_refs"),"refs").remove("root.skills.prowess_raw");assertThrows(IllegalArgumentException.class,()->RUNTIME.evaluateContexts(arr().add(noScope)));
        assertThrows(IllegalArgumentException.class,()->PhaseAst.auditValue(parse("{\"op\":\"caller_defined\"}"),java.util.Set.of()));assertThrows(IllegalArgumentException.class,()->PhaseAst.auditValue(parse("{\"op\":\"const_bool\",\"value\":true,\"unmigrated_alias\":false}"),java.util.Set.of()));assertThrows(IllegalArgumentException.class,()->PhaseAst.auditEffect(parse("{\"op\":\"call_transition\",\"key\":\"caller_defined\",\"args\":{},\"dependencies\":[]}"),java.util.Set.of(),new java.util.HashSet<>()));
    }
    @Test void nativeSignedWeightsAndBinary64SelectionsPreserveDistinctAlgorithms(){assertArrayEquals(new int[]{1,0,1,2,-1,Integer.MIN_VALUE},new int[]{PhaseDrawTape.nativeWeight(1),PhaseDrawTape.nativeWeight(-1),PhaseDrawTape.nativeWeight(100000),PhaseDrawTape.nativeWeight(100001),PhaseDrawTape.nativeWeight(-100001),PhaseDrawTape.nativeWeight((1L<<31)*100000)});PhaseDrawTape nativeTape=new PhaseDrawTape(List.of(5));assertEquals(1,nativeTape.takeNative("uniform",List.of(-100000L,0L)));assertEquals(1,nativeTape.position);assertEquals("nonpositive_total_uniform",nativeTape.records.get(0).path("selection_mode").asText());assertThrows(IllegalArgumentException.class,()->new PhaseDrawTape(List.of(-1)));}
    @Test void manifestRevalidatesCanonicalOrderSourceHashesAndFrozenReadiness() throws Exception {
        StockPhaseManifest manifest=StockPhaseManifest.load();assertFalse(manifest.fidelityGate());assertThrows(IllegalStateException.class,manifest::requireEvaluatorReady);ObjectNode data=manifest.toJson();data.put("game_version","1.20.0.4");Path file=temporary.resolve("drift.json");Files.writeString(file,data.toString());assertThrows(IllegalArgumentException.class,()->new StockPhaseEventRuntime(file));ObjectNode source=manifest.toJson();object(source.path("files").get(0),"source").put("sha256","F".repeat(64));Files.writeString(file,source.toString());assertThrows(IllegalArgumentException.class,()->new StockPhaseEventRuntime(file));assertEquals("1.19.0.6",manifest.toJson().path("game_version").asText());
    }
    @Test void actualDailyFeedbackConsumerPreservesDrawsStateAndNonresolution(){
        PhaseFeedbackResearchKernel kernel=new PhaseFeedbackResearchKernel();BigInteger day=integer(original.get("feedback_start_day"),"start day");PhaseFeedbackResearchKernel.Input input=new PhaseFeedbackResearchKernel.Input(original.get("feedback_context"),PhaseFeedbackResearchKernel.Role.COMMANDER,day,List.of(new PhaseFeedbackResearchKernel.EffectTape(day,"commander_wounded",List.of(0,0))));
        PhaseFeedbackResearchKernel.Projection projection=kernel.projectTrial(input,new CombatCore.DrawState(0,21),6);assertSameJson(original.get("feedback"),projection.toJson(),"actual same-root daily feedback consumer");assertEquals(2,projection.selectionState().counter());assertFalse(PhaseFeedbackResearchKernel.MANIFEST.fidelityGate());assertFalse(projection.plannerUsable());assertFalse(projection.activeAttackAllowed());CombatCore.TrialOutcome outcome=kernel.simulateTrial(input,new CombatCore.TrialRandomStreams(new CombatCore.DrawState(0,0),new CombatCore.DrawState(0,21)),6);assertEquals(CombatCore.TrialResult.NO_RESOLUTION,outcome.result());assertEquals(BigInteger.ZERO,outcome.playerHardLossRaw());assertEquals(BigInteger.ZERO,outcome.enemyHardLossRaw());
        PhaseFeedbackResearchKernel.Input missing=new PhaseFeedbackResearchKernel.Input(original.get("feedback_context"),PhaseFeedbackResearchKernel.Role.COMMANDER,day,List.of());assertThrows(IllegalArgumentException.class,()->kernel.projectTrial(missing,new CombatCore.DrawState(0,21),1));assertThrows(IllegalArgumentException.class,()->kernel.projectTrial(input,new CombatCore.DrawState(0,21),0));
    }
    private static List<Integer> draws(JsonNode value){List<Integer> out=new ArrayList<>();for(JsonNode n:array(value,"draws"))out.add(integer(n,"draw").intValueExact());return List.copyOf(out);}
    private static void assertSameJson(JsonNode expected,JsonNode actual,String message){assertTrue(CombatPhaseInputsCodec.sameJson(expected,actual),()->message+"\nEXPECTED: "+expected+"\nACTUAL: "+actual);}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException(key+" required; actual producer regression must not skip");return value;}
    private static void pins(Path root) throws Exception {for(String pin:List.of(
        "ck3_autonomous_player/src/xar_autoplayer/simulation/phase_event_evaluator.py 5c029f5887b538faa5f02c8ab1a422fcb7751c8d26ff14abf785616713e81d92",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/phase_event_manifest.py 124d5ba996c4c654b1931af34cb9ed63bb064dfc31da19900ecc944d7d853ddd",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/phase_event_feedback.py 9ffb20e170785ac5f822cc61fb6435364d175f082591428a23ebadb17e445773",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/candidate_source_proof.py f9651e2c7e7a73abc27fee0eb66bcbab06d3fc52ab300e81d186032fe58ff7ba",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/combat_core.py 15a9efce451e1830def6a7d93c87d0d00b7bb4e852fd75895780d289108a11b6",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_stock_combat_phase_events.json 749de2cb0ba7c4b072046db56bd5707a2ee4f7ebb6d7847f6851a88d74fdff8f",
        "ck3_autonomous_player/tests/unit/test_phase_event_ast_evaluator.py 903c60ee33253802fa60b6ce01d109135f2f535d526cd68f81ebf4e9c5e684aa",
        "ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_production_contract.py 8c925106ea6391a3ef002b8f9ee89f584f729ef4d7ba46cb2fa020a3ea118fc6",
        "ck3_autonomous_player/tests/fixtures/combat_phase_events/v3_ast_evaluator_family_golden.json 32565f7e42baf5ae1098718de0a81130815e1099fc996bb610dfddd62c36b5d9")){String[] p=pin.split(" ");Path file=root.resolve(p[0]);assertTrue(Files.isRegularFile(file),"required source missing "+file);assertEquals(p[1].toUpperCase(),digest(Files.readAllBytes(file)),"source SHA drift "+p[0]);}}
}
