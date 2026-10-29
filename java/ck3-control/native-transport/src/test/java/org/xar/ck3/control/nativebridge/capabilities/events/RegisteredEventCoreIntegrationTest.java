package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventoutcome.RegisteredEventMaterial;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Original fixture producer -> full production event codec -> actual CORE -> sole command adapter.
 * Native frames/expected postconditions here are explicitly synthetic software fixtures, never live evidence.
 */
final class RegisteredEventCoreIntegrationTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic-event-integration-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final PlanningReadPort NO_READS=new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("the already observed exact frame must not issue another native query");
        }
    };

    @Test void actualKnownRegistryProducerRetainsExactOptionAndScalarPlanThroughTheSoleCommandAdapter() throws Exception {
        ObjectNode context=EventWindowOriginalProducerTest.fixture("available",Build.CROZIER4);
        context.put("event_definition_key","trait_specific.8001");context.putArray("saved_scopes");
        ObjectNode first=((ObjectNode)context.get("options").get(0)).deepCopy();
        first.put("rendered_index",0).put("native_option_index",0).put("shown",true).put("enabled",true).put("fallback",false).put("cancel",false);
        first.put("unavailable_reason","");((ObjectNode)first.get("effect_indicators")).putArray("rows");
        ObjectNode second=first.deepCopy();second.put("rendered_index",1).put("native_option_index",1);
        context.putArray("options").add(first).add(second);
        EventWindowCodec.decode(raw(context),nativeBinding(context));
        PlanningRequest request=request(context,2);
        AtomicInteger bindings=new AtomicInteger();List<OpportunityJson.Obj> retained=new ArrayList<>();
        var core=core((input,operation,args,plan,purpose,domain)->{
            bindings.incrementAndGet();assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION,purpose);
            assertEquals("select-event-option-2",operation.value());assertEquals(args,plan);retained.add(args);
            return new OrdinaryCorePolicy.Prepared(command(input,operation,args));
        });
        var result=assertInstanceOf(OrdinaryPolicy.Replace.class,core.evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertEquals(1,bindings.get());ActionCommand selected=result.draft().command().orElseThrow();
        assertEquals(request.before(),selected.before());assertEquals(request.source(),selected.source());
        assertEquals("active_event_registry_choice",result.draft().phase());
        JsonNode arguments=OpportunityJson.toNode(selected.arguments());
        assertEquals(context.get("current_event_instance_id"),arguments.get("event_instance_id"));
        assertEquals(2,arguments.get("option_number").intValue());assertEquals(1,arguments.get("native_option_index").intValue());
        assertEquals(1,arguments.get("rendered_index").intValue());assertEquals("recommended",arguments.path("event_decision").path("status").textValue());
        assertEquals("ready",arguments.path("event_material_postcondition").path("status").textValue());
        assertEquals("played_character_gold.raw",arguments.path("event_material_postcondition").path("metric").textValue());
        assertEquals("strictly_increasing",arguments.path("event_material_postcondition").path("expected_relation").textValue());
        assertEquals(selected.arguments(),result.draft().detail());assertEquals(retained.getFirst(),selected.arguments());
    }

    @Test void disabledFirstUnknownOptionIsCapturedWithoutSelectingTheLegalSecond() throws Exception {
        ObjectNode context=EventWindowOriginalProducerTest.fixture("available",Build.CROZIER4);
        context.put("event_definition_key","unregistered_fixture.7711");
        ObjectNode second=((ObjectNode)context.get("options").get(0)).deepCopy();
        second.put("rendered_index",1).put("native_option_index",5).put("enabled",true);
        ((com.fasterxml.jackson.databind.node.ArrayNode)context.get("options")).add(second);
        assertFalse(context.path("options").get(0).path("enabled").booleanValue());
        EventWindowCodec.decode(raw(context),nativeBinding(context));
        PlanningRequest request=request(context,6);
        var core=core((input,operation,args,plan,purpose,domain)->{throw new AssertionError("unknown registry cannot submit");});
        var classified=assertInstanceOf(OrdinaryPolicy.Replace.class,core.evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertTrue(classified.draft().command().isEmpty());
        assertEquals("not_registered",OpportunityJson.toNode(classified.draft().detail()).path("event_decision").path("status").textValue());
        var captures = new java.util.ArrayList<OpportunityJson.Obj>();
        var policies=EventPolicies.policies(SOURCE,Optional.empty(),
            (input,operation,plan,material)->{throw new AssertionError("disabled first option cannot create an expected action");},
            NO_READS,List.of(),EventWindowService.validator(ignored->Build.CROZIER4),(actual,plan)->captures.add(plan),
            (actual,operation,args,originalPlan,purpose,domain)->{throw new AssertionError("disabled event continuation cannot prepare another shared command");});
        var continuation=policies.get(1).evaluate(request,classified.draft());
        assertInstanceOf(OrdinaryPolicy.Wait.class,continuation);
        assertTrue(continuation.reason().contains("first displayed"));
        assertEquals(1,captures.size());assertSame(OpportunityJson.Nil.INSTANCE,captures.getFirst().get("selected_step"));
        assertFalse(OpportunityJson.toNode(captures.getFirst()).path("unhandled_event_fallback").path("selection").path("enabled").booleanValue());
    }

    @Test void malformedHistoricalContextMustPassTheFullProductionCodecBeforeAnyRegistryOrAdapter() throws Exception {
        ObjectNode context=EventWindowOriginalProducerTest.fixture("available",Build.CROZIER4);
        context.remove("saved_scopes");
        PlanningRequest request=request(context,4);
        AtomicInteger bound=new AtomicInteger();
        var captures = new java.util.ArrayList<OpportunityJson.Obj>();
        var core=core((input,operation,args,plan,purpose,domain)->{bound.incrementAndGet();throw new AssertionError("malformed native history cannot submit");},(actual,plan)->captures.add(plan));
        var result=assertInstanceOf(OrdinaryPolicy.Stop.class,core.evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,result.stopReason());assertEquals(0,bound.get());
        assertTrue(result.reason().contains("typed event/power read contract"));
        assertEquals(1,captures.size());
        JsonNode diagnosis=OpportunityJson.toNode(captures.getFirst()).get("unhandled_native_window_diagnostic");
        assertEquals("xar.unhandled-native-window-diagnostic/v1",diagnosis.get("schema").textValue());
        assertTrue(diagnosis.get("selection").isNull());assertFalse(diagnosis.path("retained_history").isEmpty());
    }

    private static RegisteredEventCore core(OrdinaryCorePolicy.CommandBinding binding) throws Exception {
        return core(binding,org.xar.ck3.control.application.planning.events.EventIncidentCapturePort.unavailable());
    }
    @Test void publicExactRegisteredOptionCarriesItsOriginalScalarMaterialAndFullNativeRow() throws Exception {
        ObjectNode context=publicContext("trait_specific.8001");
        PlanningRequest request=request(context,2);
        var plan=PublicEventSelection.plan(request,2,Optional.of(context.get("current_event_instance_id").intValue()),
            RegisteredEventKnowledge.load(),Optional.empty(),EventWindowService.validator(ignored->Build.CROZIER4));
        JsonNode wire=OpportunityJson.toNode(plan);
        assertEquals("select-event-option-2",wire.get("selected_step").textValue());
        assertEquals("recommended",wire.path("event_decision").path("status").textValue());
        assertEquals("played_character_gold.raw",wire.path("event_material_postcondition").path("metric").textValue());
        assertEquals(context.get("options").get(1),wire.get("selected_native_event_option"));
        assertEquals(context,wire.get("event_window_context"));
        assertFalse(wire.get("material_effects_verified").booleanValue());
        assertEquals(plan,OpportunityJson.object(OpportunityJson.parse(OpportunityJson.encode(plan)),"serialized public plan"));
        assertEquals(request.before().frame().revision(),OpportunityJson.integer(request.observations().snapshot().get("revision"),"original revision"));
    }
    @Test void publicAlternateOptionCannotBorrowTheRecommendedOptionsEffects() throws Exception {
        ObjectNode context=publicContext("trait_specific.8001");
        var plan=PublicEventSelection.plan(request(context,2),1,Optional.empty(),RegisteredEventKnowledge.load(),Optional.empty(),
            EventWindowService.validator(ignored->Build.CROZIER4));
        JsonNode wire=OpportunityJson.toNode(plan);
        assertEquals("select-event-option-1",wire.get("selected_step").textValue());
        assertEquals(0,wire.get("native_option_index").intValue());
        assertFalse(wire.has("event_material_postcondition"));
        assertEquals("user_authorized_fallback",wire.path("event_decision").path("status").textValue());
        assertEquals(1,wire.path("unhandled_event_fallback").path("original_registry_decision").path("selected_native_option_index").intValue());
        assertEquals("public_explicit_authored_native_option_number",wire.path("unhandled_event_fallback").path("selection").path("selection_order").textValue());
        assertEquals("public-explicit-option-capture-before-submit",wire.path("unhandled_event_fallback").path("policy").textValue());
    }
    @Test void publicUnfamiliarOptionRetainsFullActualCaptureWithoutChoosingAnotherDisplayedOption() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        ((ObjectNode)context.get("options").get(0)).put("enabled",false);
        var plan=PublicEventSelection.plan(request(context,2),2,Optional.empty(),RegisteredEventKnowledge.load(),Optional.empty(),
            EventWindowService.validator(ignored->Build.CROZIER4));
        JsonNode wire=OpportunityJson.toNode(plan);
        assertEquals("select-event-option-2",wire.get("selected_step").textValue());
        assertEquals(context,wire.path("unhandled_event_fallback").path("window_context"));
        assertTrue(wire.path("unhandled_event_fallback").path("offline_followup_required").booleanValue());
        assertEquals(1,wire.path("unhandled_event_fallback").path("selection").path("native_option_index").intValue());
    }
    @Test void publicSelectionRejectsInstanceDriftDisabledOptionAndMalformedHistoryBeforeProducingAPlan() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        var knowledge=RegisteredEventKnowledge.load();var validator=EventWindowService.validator(ignored->Build.CROZIER4);
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(request(context,2),1,Optional.of(1),knowledge,Optional.empty(),validator));
        ((ObjectNode)context.get("options").get(0)).put("enabled",false);
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(request(context,2),1,Optional.empty(),knowledge,Optional.empty(),validator));
        ((ObjectNode)context.get("options").get(0)).put("enabled",true);context.remove("saved_scopes");
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(request(context,2),1,Optional.empty(),knowledge,Optional.empty(),validator));
    }
    @Test void publicSelectionRejectsWrongJsonOptionTypeAndDuplicateNativeMapping() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        var knowledge=RegisteredEventKnowledge.load();var validator=EventWindowService.validator(ignored->Build.CROZIER4);
        ((ObjectNode)context.get("options").get(0)).put("native_option_index",false);
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(request(context,2),1,Optional.empty(),knowledge,Optional.empty(),validator));
        ((ObjectNode)context.get("options").get(0)).put("native_option_index",1);
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(request(context,2),1,Optional.empty(),knowledge,Optional.empty(),validator));
    }
    @Test void publicSelectionRejectsWrongOuterReadRevisionWithoutRefreshingTheRequest() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");PlanningRequest original=request(context,2);
        ObjectNode row=(ObjectNode)OpportunityJson.toNode(original.observations().history().getFirst());
        ((ObjectNode)row.get("result")).put("queried_revision",10);
        var before=original.observations();var changed=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),
            new PlanningObservation(before.snapshot(),List.of(object(row)),before.actionSteps(),before.bridgeCapabilities(),before.battleSpeedReadiness(),
                before.actionFacts(),before.campaignGoal(),before.crossRunPlan(),before.initialLifestyleFocusRequired()));
        assertThrows(IllegalArgumentException.class,()->PublicEventSelection.plan(changed,1,Optional.empty(),RegisteredEventKnowledge.load(),Optional.empty(),
            EventWindowService.validator(ignored->Build.CROZIER4)));
        assertEquals(BigInteger.valueOf(9),changed.before().frame().revision());
    }
    private static ObjectNode publicContext(String key) throws Exception {
        ObjectNode context=EventWindowOriginalProducerTest.fixture("available",Build.CROZIER4);context.put("event_definition_key",key);context.putArray("saved_scopes");
        ObjectNode first=((ObjectNode)context.get("options").get(0)).deepCopy();
        first.put("rendered_index",0).put("native_option_index",0).put("shown",true).put("enabled",true).put("fallback",false).put("cancel",false).put("unavailable_reason","");
        ((ObjectNode)first.get("effect_indicators")).putArray("rows");
        ObjectNode second=first.deepCopy();second.put("rendered_index",1).put("native_option_index",1);
        context.putArray("options").add(first).add(second);return context;
    }
    private static RegisteredEventCore core(OrdinaryCorePolicy.CommandBinding binding,org.xar.ck3.control.application.planning.events.EventIncidentCapturePort captures) throws Exception {
        return new RegisteredEventCore(RegisteredEventKnowledge.load(),NO_READS,operation->Optional.empty(),
            EventWindowService.validator(ignored->Build.CROZIER4),RegisteredEventMaterial::plan,RegisteredEventCore.exactSourcePhases(),binding,captures);
    }
    private static Binding nativeBinding(JsonNode context) {
        return new Binding(Build.CROZIER4,context.get("snapshot_revision").bigIntegerValue(),context.get("date_raw").intValue(),context.get("current_event_instance_id").intValue());
    }
    private static PlanningRequest request(ObjectNode context,int optionCount) {
        BigInteger actor=context.path("root_scope").path("typed_identity").path("character_id").bigIntegerValue();
        if(actor==null)actor=BigInteger.valueOf(29829);
        BigInteger revision=BigInteger.valueOf(9),nativeRevision=context.get("snapshot_revision").bigIntegerValue(),date=context.get("date_raw").bigIntegerValue();
        ObjectNode snapshot=StrictJson.object().put("snapshot_id","event-frame-9").put("revision",revision).put("native_revision",nativeRevision)
            .put("date_raw",date).put("episode_run_id","event-episode").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",actor).put("alive",true).put("stress_points",0);
        snapshot.putObject("played_character_gold").put("raw",2_000_000).put("scale",100_000);
        snapshot.putObject("active_event").put("instance_id",context.get("current_event_instance_id").bigIntegerValue()).put("option_count",optionCount);
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");snapshot.putArray("declarable_wars");
        snapshot.putObject("diagnostics").put("connection_generation",1).put("bridge_pid",123);
        ObjectNode read=StrictJson.object().put("step",RegisteredEventCore.EVENT_QUERY).put("accepted",true).put("status",context.path("status").textValue())
            .put("queried_snapshot_id","event-frame-9").put("queried_revision",revision).put("queried_native_revision",nativeRevision)
            .put("snapshot_revision",nativeRevision).put("date_raw",date);
        read.set("current_event_instance_id",context.get("current_event_instance_id"));read.set("current_event_window_context",context);
        ObjectNode row=StrictJson.object().put("command",RegisteredEventCore.EVENT_QUERY).put("ok",true);row.set("result",read);
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new ObservationIdentity("fixture-machine-1",game,new JointBudgetSelector.ProposalFrame(
            new JointBudgetSelector.Frame(actor,nativeRevision,date),"event-frame-9",revision,"event-episode"),1);
        Set<OperationKey> steps=java.util.stream.Stream.of(RegisteredEventCore.EVENT_QUERY,"select-event-option-1","select-event-option-2",
            "select-event-option-4","select-event-option-6").map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet());
        var observation=new PlanningObservation(object(snapshot),List.of(object(row)),steps,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,new G2Source(before.machineId(),NOW.toString(),"synthetic-exact-build",SOURCE),"event-session",NOW.plusSeconds(60),observation);
    }
    private static ActionCommand command(PlanningRequest request,OperationKey operation,OpportunityJson.Obj arguments) {
        return new ActionCommand("synthetic-event-action",request.before(),request.source(),request.sessionId(),operation,arguments,
            new ExpectedPostcondition(1,request.before(),request.source(),"synthetic-window-observer/v1",
                List.of(new ExpectedBoolean(new FieldKey("native.window_verified"),true))),
            new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static RawJson raw(JsonNode value) { return new RawJson(StrictJson.canonical(value)); }
    private static OpportunityJson.Obj object(JsonNode value) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"synthetic original-producer integration value"); }
}

