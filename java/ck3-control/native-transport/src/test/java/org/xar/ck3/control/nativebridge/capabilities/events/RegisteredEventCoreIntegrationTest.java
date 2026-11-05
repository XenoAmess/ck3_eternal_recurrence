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

    @Test void registeredPlaceholderMaterializesOnlyThroughActualContinuation() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        ((ObjectNode)context.get("options").get(0)).put("native_option_index",1);
        ((ObjectNode)context.get("options").get(1)).put("native_option_index",0);
        EventWindowCodec.decode(raw(context),nativeBinding(context));PlanningRequest request=request(context,2);
        var registry=core((input,operation,args,plan,purpose,domain)->{throw new AssertionError("unregistered registry may classify, not select");});
        var classified=assertInstanceOf(OrdinaryPolicy.Replace.class,registry.evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertEquals(OrdinaryPolicy.Kind.FOREGROUND,classified.draft().kind());assertEquals(OrdinaryPolicy.Purpose.READ_ONLY,classified.draft().purpose());
        assertTrue(classified.draft().command().isEmpty());assertTrue(classified.reason().contains("later continuation"));
        assertEquals(object(context),classified.draft().detail().get("event_window_context"));
        assertEquals(new OpportunityJson.Text("not_registered"),OpportunityJson.object(classified.draft().detail().get("event_decision"),"registry decision").get("status"));
        var captures=new ArrayList<OpportunityJson.Obj>();var policies=registryEventPolicies((actual,plan)->captures.add(plan));
        var calls=new AtomicInteger();var lower=new AtomicInteger();
        OrdinaryPolicy continuation=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(actual,previous)->{
            calls.incrementAndGet();assertSame(request,actual);assertEquals(classified.draft(),previous);return policies.get(1).evaluate(actual,previous);
        });
        var result=assertInstanceOf(PlanningResult.ActionSelected.class,registryPlanner(registry,continuation,policies.get(2),lower).plan(request));
        var selected=result.command();assertEquals("select-event-option-2",selected.operation().value());
        assertEquals(request.before(),selected.before());assertEquals(request.source(),selected.source());assertEquals(request.sessionId(),selected.sessionId());
        assertEquals(request.deadline(),selected.deadline());assertEquals(1,calls.get());assertEquals(0,lower.get());assertTrue(captures.isEmpty());
        assertEquals(BigInteger.ONE,OpportunityJson.integer(selected.arguments().get("native_option_index"),"native index"));
        assertEquals(BigInteger.ZERO,OpportunityJson.integer(selected.arguments().get("rendered_index"),"rendered index"));
        assertEquals(BigInteger.TWO,OpportunityJson.integer(selected.arguments().get("option_number"),"option number"));
        var capture=OpportunityJson.object(selected.arguments().get("unhandled_event_fallback"),"complete retained capture");
        assertEquals(object(context),capture.get("window_context"));
        var original=OpportunityJson.object(capture.get("original_registry_decision"),"original registered plan");
        assertEquals(classified.draft().detail().get("event_decision"),original.get("event_decision"));
        assertEquals(classified.draft().detail().get("event_window_context"),original.get("event_window_context"));
        var stages=result.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
        int coreIndex=stages.indexOf(PlanningStage.ORDINARY_CORE);assertEquals(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,stages.get(coreIndex+1));
        assertEquals(PlanTrace.Outcome.REPLACED,result.trace().visits().get(coreIndex).outcome());
        assertEquals(PlanTrace.Outcome.REPLACED,result.trace().visits().get(coreIndex+1).outcome());
        var finish=List.of(PlanningStage.M5_WARTIME_OBSERVATION,PlanningStage.DEFERRED_SUCCESSION_ROOT,PlanningStage.HOLY_WAR_DEFENDER_OBSERVATION,
                PlanningStage.PREWAR_FORCE_COALITION,PlanningStage.ORDINARY_SWAY,PlanningStage.EVENT_MATERIAL_POSTCONDITION,
                PlanningStage.CAMPAIGN_ADVANCE_CAP,PlanningStage.REALM_MEMBERSHIP_PUBLICATION);
        assertEquals(finish,stages.subList(stages.size()-finish.size(),stages.size()));assertFalse(stages.contains(PlanningStage.WAR_RENDEZVOUS));
        System.out.println("SOFTWARE_REGISTRY_MATERIALIZED real_registry_classification=true real_continuation=true native1_rendered0_option2=true full_context_retained=true lower_calls=0 finish_order=true");
    }

    @Test void disabledOrUnchangedRegistryPlaceholderNeverLeaksToLowerPolicies() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        ((ObjectNode)context.get("options").get(0)).put("native_option_index",1).put("enabled",false);
        ((ObjectNode)context.get("options").get(1)).put("native_option_index",0).put("enabled",true);
        EventWindowCodec.decode(raw(context),nativeBinding(context));PlanningRequest request=request(context,2);
        var registry=core((input,operation,args,plan,purpose,domain)->{throw new AssertionError("unregistered registry may not prepare");});
        var classified=assertInstanceOf(OrdinaryPolicy.Replace.class,registry.evaluate(request,OrdinaryPolicy.Draft.empty()));assertTrue(classified.draft().command().isEmpty());
        var captures=new ArrayList<OpportunityJson.Obj>();var policies=registryEventPolicies((actual,plan)->captures.add(plan));var lower=new AtomicInteger();var calls=new AtomicInteger();
        var actual=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(input,previous)->{calls.incrementAndGet();return policies.get(1).evaluate(input,previous);});
        var waiting=assertInstanceOf(PlanningResult.ReadOnlyWait.class,registryPlanner(registry,actual,policies.get(2),lower).plan(request));
        assertEquals(1,calls.get());assertEquals(0,lower.get());assertTrue(waiting.trace().finalPlan().orElseThrow().command().isEmpty());
        assertEquals(1,captures.size());assertSame(OpportunityJson.Nil.INSTANCE,captures.getFirst().get("selected_step"));
        var retained=OpportunityJson.object(captures.getFirst().get("unhandled_event_fallback"),"disabled original capture");
        assertEquals(object(context),retained.get("window_context"));var selection=OpportunityJson.object(retained.get("selection"),"disabled first display");
        assertEquals(BigInteger.ZERO,OpportunityJson.integer(selection.get("rendered_index"),"rendered"));
        assertEquals(BigInteger.ONE,OpportunityJson.integer(selection.get("native_option_index"),"native"));assertEquals(new OpportunityJson.Bool(false),selection.get("enabled"));
        for(boolean keep:List.of(true,false)) {
            var keptCalls=new AtomicInteger();var untouchedLower=new AtomicInteger();
            var unchanged=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(input,previous)->{
                keptCalls.incrementAndGet();assertEquals(classified.draft(),previous);
                return keep?new OrdinaryPolicy.Keep("controlled unchanged continuation"):new OrdinaryPolicy.NotApplicable("controlled absent continuation");
            });
            var unchangedResult=assertInstanceOf(PlanningResult.ReadOnlyWait.class,registryPlanner(registry,unchanged,policies.get(2),untouchedLower).plan(request));
            assertEquals(1,keptCalls.get());assertEquals(0,untouchedLower.get());assertEquals(classified.draft(),unchangedResult.trace().finalPlan().orElseThrow());
            var stages=unchangedResult.trace().visits().stream().map(PlanTrace.StageVisit::stage).toList();
            assertFalse(stages.contains(PlanningStage.WAR_RENDEZVOUS));assertTrue(stages.contains(PlanningStage.M5_WARTIME_OBSERVATION));
            assertEquals(PlanningStage.REALM_MEMBERSHIP_PUBLICATION,stages.getLast());
        }
        System.out.println("SOFTWARE_REGISTRY_EMPTY disabled_first_not_skipped=true original_capture=true keep_and_notapplicable_finish=true lower_calls=0");
    }

    @Test void placeholderMaterializationDoesNotRelaxSourceDomainOrExistingSelectionGuards() throws Exception {
        ObjectNode context=publicContext("unregistered_fixture.7711");
        ((ObjectNode)context.get("options").get(0)).put("native_option_index",1);
        ((ObjectNode)context.get("options").get(1)).put("native_option_index",0);
        EventWindowCodec.decode(raw(context),nativeBinding(context));PlanningRequest request=request(context,2);
        var bindings=new AtomicInteger();var registry=core((input,operation,args,plan,purpose,domain)->{
            bindings.incrementAndGet();return new OrdinaryCorePolicy.Prepared(command(input,operation,args));
        });
        var classified=assertInstanceOf(OrdinaryPolicy.Replace.class,registry.evaluate(request,OrdinaryPolicy.Draft.empty()));assertTrue(classified.draft().command().isEmpty());
        var policies=registryEventPolicies((actual,plan)->{throw new AssertionError("successful continuation has retained capture, not blocked incident");});
        for(String corruption:List.of("session","domain","kind")) {
            var delegated=new AtomicInteger();var lower=new AtomicInteger();
            var tampered=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(input,previous)->{
                delegated.incrementAndGet();var proposal=assertInstanceOf(OrdinaryPolicy.Replace.class,policies.get(1).evaluate(input,previous));
                var original=proposal.draft();ActionCommand selected=original.command().orElseThrow();
                if(corruption.equals("session"))selected=new ActionCommand(selected.actionId(),selected.origin(),selected.source(),selected.sessionId()+"-wrong",
                        selected.operation(),selected.arguments(),selected.expectation(),selected.claims(),selected.deadline(),selected.protocolIdentity());
                return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(original.policy(),original.phase(),original.reason(),
                        corruption.equals("kind")?OrdinaryPolicy.Kind.ORDINARY:original.kind(),Optional.of(selected),original.purpose(),
                        corruption.equals("domain")?Optional.of(org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.war):original.domain(),original.detail()),"controlled materialization corruption");
            });
            var planner=registryPlanner(registry,tampered,policies.get(2),lower);
            var rejected=assertThrows(IllegalArgumentException.class,()->planner.plan(request));assertEquals(1,delegated.get());assertEquals(0,lower.get());
            assertTrue(rejected.getMessage().contains(corruption.equals("session")?"domain producer crossed the complete Game/session/frame/source/deadline binding":"lower-priority policy replaced exclusive ordinary work"));
        }
        var genuine=assertInstanceOf(OrdinaryPolicy.Replace.class,policies.get(1).evaluate(request,classified.draft()));
        var kept=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(input,previous)->new OrdinaryPolicy.Keep("only designated continuation stays empty"));
        var wrongStage=registryStage(PlanningStage.EVENT_MATERIAL_POSTCONDITION,(input,previous)->genuine);
        var wrongPlanner=registryPlanner(registry,kept,wrongStage,new AtomicInteger());
        var wrongRejected=assertThrows(IllegalArgumentException.class,()->wrongPlanner.plan(request));
        assertTrue(wrongRejected.getMessage().contains("lower-priority policy replaced exclusive ordinary work"));assertEquals(0,bindings.get());
        ObjectNode known=publicContext("trait_specific.8001");EventWindowCodec.decode(raw(known),nativeBinding(known));PlanningRequest knownRequest=request(known,2);
        var complete=assertInstanceOf(OrdinaryPolicy.Replace.class,registry.evaluate(knownRequest,OrdinaryPolicy.Draft.empty()));assertTrue(complete.draft().command().isPresent());
        var continuationCalls=new AtomicInteger();var knownPolicies=registryEventPolicies((input,plan)->{throw new AssertionError("no blocked known event");});
        var never=registryStage(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,(input,previous)->{continuationCalls.incrementAndGet();return knownPolicies.get(1).evaluate(input,previous);});
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,registryPlanner(registry,never,knownPolicies.get(2),new AtomicInteger()).plan(knownRequest));
        assertEquals(complete.draft().command(),Optional.of(selected.command()));assertEquals(0,continuationCalls.get());
        System.out.println("SOFTWARE_REGISTRY_GUARDS source_binding_rejected=true wrong_domain_kind_stage_rejected=true real_complete_registry_selection_retained=true");
    }

    private static List<OrdinaryPolicy> registryEventPolicies(EventIncidentCapturePort captures) {
        return EventPolicies.policies(SOURCE,Optional.empty(),(input,operation,plan,material)->Optional.of(new ExpectedPostcondition(1,input.before(),input.source(),
                        "synthetic-continuation-observer/v1",List.of(new ExpectedBoolean(new FieldKey("native.window_closed"),true)))),
                NO_READS,List.of(),EventWindowService.validator(ignored->Build.CROZIER4),captures,
                (input,operation,args,plan,purpose,domain)->{throw new AssertionError("registered continuation uses original dedicated propose");});
    }
    private static OrdinaryPolicy registryStage(PlanningStage stage,java.util.function.BiFunction<PlanningRequest,OrdinaryPolicy.Draft,OrdinaryPolicy.Decision> work) {
        return new OrdinaryPolicy() {
            @Override public PlanningStage stage() {return stage;}
            @Override public ExactRef implementationSource() {return SOURCE;}
            @Override public Decision evaluate(PlanningRequest request,Draft previous) {return work.apply(request,previous);}
        };
    }
    private static OrdinaryPlanner registryPlanner(OrdinaryCorePolicy.CoreProducer registry,OrdinaryPolicy continuation,OrdinaryPolicy material,AtomicInteger lowerCalls) {
        var core=OrdinaryCorePolicy.assemble(SOURCE,link->{
            var leaves=new ArrayList<org.xar.ck3.control.application.planning.military.WarCorePlanner.Leaf>();
            for(var boundary:org.xar.ck3.control.application.planning.military.WarCorePlanner.Boundary.values())
                leaves.add(new org.xar.ck3.control.application.planning.military.WarCorePlanner.Leaf(boundary,SOURCE,
                        (input,previous)->new org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(Map.of()))));
            return new org.xar.ck3.control.application.planning.military.WarCorePlanner(leaves,
                    input->new org.xar.ck3.control.application.planning.military.WarCorePlanner.KnownTactics(input.before(),
                        new org.xar.ck3.control.application.planning.military.WarCorePlanner.RouteTactics(Set.of(),Set.of())),
                    (input,selection)->{throw new AssertionError("no military world action");},NO_READS,
                    (input,selection)->{throw new AssertionError("no military query");},link);
        },registry,(input,previous)->new OrdinaryPolicy.Keep("unused council"),(input,previous)->new OrdinaryPolicy.Keep("unused marriage"),
                (input,previous)->new OrdinaryPolicy.Keep("unused war entry"),
                (input,operation,args,plan,purpose,domain)->{throw new AssertionError("registered event never enters core fallback binding");},step->false);
        var policies=new java.util.EnumMap<PlanningStage,OrdinaryPolicy>(PlanningStage.class);
        for(var stage:PlanningStage.values())policies.put(stage,registryStage(stage,(input,previous)->new OrdinaryPolicy.Keep("unrelated software stage")));
        policies.put(PlanningStage.ORDINARY_CORE,core.core());policies.put(PlanningStage.EVENT_AND_INTERACTION_CONTINUATION,continuation);
        policies.put(PlanningStage.EVENT_MATERIAL_POSTCONDITION,material);
        policies.put(PlanningStage.WAR_RENDEZVOUS,registryStage(PlanningStage.WAR_RENDEZVOUS,(input,previous)->{
            lowerCalls.incrementAndGet();throw new AssertionError("registered placeholder/completion must not enter lower ordinary stage");
        }));
        var realm=new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle(SOURCE);
        policies.put(PlanningStage.REALM_MEMBERSHIP_PUBLICATION,realm);
        return new OrdinaryPlanner(new ArrayList<>(policies.values()),java.time.Clock.fixed(NOW,java.time.ZoneOffset.UTC),realm);
    }

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

