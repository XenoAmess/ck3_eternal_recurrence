package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags;

/** Exact original AST/pure dependencies -> actual Java projection -> public service/MCP/serde.
 * Detached DATA cases issue no current Root, Managed input, native scope or action permission. */
final class RootPublicPlanExecuteProducerParityTest {
    @TempDir Path temporary;
    private record Case(PlanFlags flags,OriginalPlanDomainEnvelope.Branch branch,Obj snapshot,List<Obj> history,Obj detail) { }
    private static Obj data(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);}
    private static JsonNode node(OpportunityJson.Value value){return OpportunityJson.toNode(value);}
    private static ObjectNode snapshot(){
        var input=PublicDataJson.object(new RawJson(PublicPlanningCodecTest.snapshot("1").getBytes(StandardCharsets.UTF_8)));
        input.put("format_version",1).put("speed",3).put("episode_character_id",29829).putNull("one_life_terminal_reason");
        input.putArray("player_armies");input.putNull("active_event");input.putNull("pending_character_interaction");
        ((ObjectNode)input.get("diagnostics")).put("bridge_pid",123);return input;
    }
    private static Obj detail(){return data("{\"policy\":\"original-source-plan\",\"phase\":\"source_boundary\",\"reason\":\"retain actual full domain detail\",\"selected_step\":null,\"event_decision\":{\"definition\":\"rite_growth.0010\",\"options\":[0,1]},\"campaign_goal_plan_used\":{\"rows\":[]},\"source_owned_extension\":{\"cost\":1.2500e-7,\"signed_zero\":-0.0,\"missing_is_not_null\":null},\"construction_pending_action\":null}");}
    private static PlanningRequest request(Case input){
        var base=PublicPlanningCodecTest.original(new String(PublicDataJson.encodeTyped(input.snapshot()).bytes(),StandardCharsets.UTF_8),BigInteger.ONE);
        var seen=new PlanningObservation(input.snapshot(),input.history(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),input.flags().initialLifestyleFocusRequired());
        return new PlanningRequest(base.before(),base.source(),base.sessionId(),base.deadline(),seen);
    }
    private static PlanningResult result(PlanningRequest request,Case input){
        PlanningStage stage=switch(input.branch()){
            case OPENING_FOCUS->PlanningStage.OPENING_LIFESTYLE_FOCUS;
            case WINDOW_PRIORITY->PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS;
            case ORDINARY->PlanningStage.ORDINARY_CORE;
            default->throw new IllegalArgumentException("finite observed envelope branches only");
        };
        var kind=input.branch()==OriginalPlanDomainEnvelope.Branch.OPENING_FOCUS?OrdinaryPolicy.Kind.OPENING_FOCUS
            :input.branch()==OriginalPlanDomainEnvelope.Branch.WINDOW_PRIORITY?OrdinaryPolicy.Kind.FOREGROUND:OrdinaryPolicy.Kind.ORDINARY;
        var draft=new OrdinaryPolicy.Draft("original-source-plan","source_boundary","retain actual full domain detail",kind,
            Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),input.detail());
        var trace=new PlanTrace(request.before(),List.of(new PlanTrace.StageVisit(stage,PlanTrace.Outcome.KEPT,
            "detached original envelope boundary, no Root authority",Optional.empty(),Optional.empty())),Optional.of(draft));
        return new PlanningResult.ReadOnlyWait(request.before(),draft.reason(),trace);
    }

    @Test void originalThreeLifeInputsAndFullDomainEnvelopeReachActualPublicBindingAndMcpSerde()throws Exception {
        Obj snapshot=data(new String(PublicDataJson.encode(snapshot()).bytes(),StandardCharsets.UTF_8));
        ObjectNode pendingRow=StrictJson.object();pendingRow.put("command","private-select-player-lifestyle-stock-focus-v1").put("ok",false);
        ObjectNode intent=pendingRow.putObject("result");intent.put("status","action_state_unknown").put("episode_run_id","native-29829-2bc2d599f7f9")
            .put("action_request_id","retained-once").put("target_key","strategy_focus").put("kind","stock_focus")
            .put("pre_public_revision",1).putNull("native_command_submitted");
        intent.putObject("source_frame").put("snapshot_id","native:1").put("revision",1).put("native_revision",1)
            .put("date_raw",53217264).put("player_character_id",29829);
        intent.putObject("unknown_extension").put("still_missing",true);
        Obj pending=DriverJson.object(PublicDataJson.encode(pendingRow).bytes(),RawJson.MAXIMUM_BYTES);
        var cases=new ArrayList<Case>();
        for(var branch:List.of(OriginalPlanDomainEnvelope.Branch.OPENING_FOCUS,OriginalPlanDomainEnvelope.Branch.WINDOW_PRIORITY,OriginalPlanDomainEnvelope.Branch.ORDINARY))
            for(boolean enabled:List.of(false,true))cases.add(new Case(new PlanFlags(enabled,enabled,enabled,enabled,enabled,enabled,
                branch==OriginalPlanDomainEnvelope.Branch.OPENING_FOCUS),branch,snapshot,List.of(pending),detail()));
        ArrayNode input=JsonNodeFactory.instance.arrayNode();for(Case value:cases)input.add(oracleCase(value));
        JsonNode expected=OriginalPublicPlanningOracle.run("plan",input,temporary.resolve("original-envelope"));assertEquals(6,expected.size());
        for(int index=0;index<cases.size();index++){
            Case value=cases.get(index);var request=request(value);var actual=result(request,value);
            var projected=OriginalPlanDomainEnvelope.project(request,actual,value.flags());
            assertOriginalTypedJsonEqual(expected.get(index).get("before_private"),node(projected.beforeConsumers()));
            var presentation=RootPublicPlanPresentation.produce(request,actual,value.flags());
            assertOriginalTypedJsonEqual(expected.get(index).get("public"),PublicDataJson.object(presentation.bytes()));
            assertEquals(presentation.original(),RootPublicPlanPresentation.decode(presentation.bytes()).original());
            var registry=new PublicBindings();new RootMcpPlanning(new RootMcpPlanning.Backend(){
                public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(true,false,List.of());}
                public RawJson plan(PublicPlanningCodec.PlanRequest caller)throws java.io.IOException{return RootPublicPlanPresentation.produce(request,actual,value.flags()).bytes();}
                public RawJson execute(PublicPlanningCodec.ExecuteRequest caller){throw new AssertionError("PLAN cannot dispatch EXECUTE");}
            }).register(registry,OriginalPublicPlanningOracle.bindingSource());
            registry.freeze(Set.of(PublicMethod.PLAN_TURN));
            var binding=registry.lookup(PublicMethod.PLAN_TURN).orElseThrow();
            if(!(binding instanceof PublicBindings.TypedBinding<?,?> typed))throw new AssertionError("actual registered PLAN binding must remain typed");
            var directory=OriginalPublicPlanningOracle.directory("ck3_plan_turn",typed);
            JsonNode envelope=PublicDataJson.object(new RawJson(directory.invoke(OriginalPublicPlanningOracle.call("ck3_plan_turn","{}")).bytes()));
            assertOriginalTypedJsonEqual(expected.get(index).get("public"),envelope.get("structuredContent"));
            assertEquals(envelope.get("structuredContent"),PublicDataJson.object(new RawJson(envelope.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8))));
            assertFalse(envelope.get("isError").booleanValue());
            assertTrue(new String(presentation.bytes().bytes(),StandardCharsets.UTF_8).contains("1.2500e-7"));
        }
    }
    private static ObjectNode oracleCase(Case input){
        var row=StrictJson.object();row.put("branch",input.branch().name());row.set("snapshot",node(input.snapshot()));
        var history=row.putArray("history");input.history().forEach(value->history.add(node(value)));row.set("detail",node(input.detail()));row.putArray("steps");
        row.putObject("flags").put("allow_private_lifestyle_formal_trial",input.flags().lifestyleFormalTrial())
            .put("allow_private_faction_gift_formal_trial",input.flags().factionGiftFormalTrial())
            .put("allow_private_construction_formal_trial",input.flags().constructionFormalTrial())
            .put("allow_private_family_marriage_formal_trial",input.flags().familyMarriageFormalTrial())
            .put("allow_private_council_action",input.flags().councilAction()).put("allow_private_m5_joint_collector",input.flags().m5JointCollector())
            .put("require_initial_lifestyle_focus_before_date_advance",input.flags().initialLifestyleFocusRequired());return row;
    }

    @Test void originalZeroRevisionAndWrongJsonTypesKeepPublicSerdeSeparateFromCurrentAdmission()throws Exception {
        ArrayNode input=JsonNodeFactory.instance.arrayNode();var tokens=List.of("0","1","true","1.0","-1","\"01\"","[]","{}");
        for(String token:tokens)input.add(PublicDataJson.object(new RawJson(("{\"value\":"+token+"}").getBytes(StandardCharsets.UTF_8))));
        JsonNode expected=OriginalPublicPlanningOracle.run("revision",input,temporary.resolve("revision"));
        for(int i=0;i<tokens.size();i++){
            String json="{\"step\":\"pause-map\",\"expected_revision\":"+tokens.get(i)+"}";
            if(expected.get(i).get("accepted").booleanValue()){
                var decoded=PublicPlanningCodec.decodeExecute(PublicBindings.present(new RawJson(json.getBytes(StandardCharsets.UTF_8))));
                assertEquals(decoded,PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(decoded))));
                assertEquals(new PublicPlanningCodec.RevisionValue(new BigInteger(tokens.get(i))),decoded.expectedRevision());
                if(tokens.get(i).equals("0"))assertThrows(IllegalArgumentException.class,()->decoded.requireCurrent(
                    PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"),BigInteger.ONE)));
            }else assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(PublicBindings.present(new RawJson(json.getBytes(StandardCharsets.UTF_8)))));
        }
        for(String revision:List.of("0","1","18446744073709551615")){
            var decoded=PublicPlanningCodec.decodeExecute(PublicBindings.present(new RawJson(("{\"step\":\"pause-map\",\"expected_revision\":\""+revision+"\"}").getBytes(StandardCharsets.UTF_8))));
            assertEquals(new PublicPlanningCodec.RevisionValue(new BigInteger(revision)),decoded.expectedRevision());
            assertEquals(decoded,PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(decoded))));
        }
    }
    @Test void actualOriginalRoutingKeepsEveryDomainDetailAcrossRequiredAndAvailableFallbacks()throws Exception {
        ArrayNode cases=JsonNodeFactory.instance.arrayNode();var plans=new ArrayList<Obj>();var sets=new ArrayList<Set<OperationKey>>();
        for(String step:List.of("declare-war-target-1","resolve-current-event","optional-source-action","pause-map"))
            for(int availability:List.of(0,1,2)){
                Obj plan=detail().with("selected_step",new OpportunityJson.Text(step));
                Set<OperationKey> steps=availability==0?Set.of():availability==1?Set.of(new OperationKey("life-advance")):Set.of(new OperationKey(step));
                plans.add(plan);sets.add(steps);var row=cases.addObject();row.set("detail",node(plan));var names=row.putArray("steps");steps.forEach(value->names.add(value.value()));
            }
        var expected=OriginalPublicPlanningOracle.run("routing",cases,temporary.resolve("routing"));
        for(int i=0;i<plans.size();i++){
            var routed=OriginalPlanRouting.route(plans.get(i),sets.get(i));assertOriginalTypedJsonEqual(expected.get(i),node(routed));
            assertEquals(plans.get(i).get("source_owned_extension"),routed.get("source_owned_extension"));
            assertEquals(routed,DriverJson.object(PublicDataJson.encodeTyped(routed).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }
    /** Original Python JSON parses decimal tokens as binary64; Java additionally preserves their exact text.
     * Compare that actual old value domain while keeping integer/float, null/missing and -0.0 distinct. */
    private static void assertOriginalTypedJsonEqual(JsonNode expected,JsonNode actual){
        assertNotNull(expected);assertNotNull(actual);
        if(expected.isObject()){
            assertTrue(actual.isObject());assertEquals(expected.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()),
                actual.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()));
            expected.properties().forEach(entry->assertOriginalTypedJsonEqual(entry.getValue(),actual.get(entry.getKey())));
        }else if(expected.isArray()){
            assertTrue(actual.isArray());assertEquals(expected.size(),actual.size());
            for(int i=0;i<expected.size();i++)assertOriginalTypedJsonEqual(expected.get(i),actual.get(i));
        }else if(expected.isFloatingPointNumber()){
            assertTrue(actual.isFloatingPointNumber());assertEquals(Double.doubleToRawLongBits(expected.doubleValue()),Double.doubleToRawLongBits(actual.doubleValue()));
        }else assertEquals(expected,actual);
    }

}
