package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.offline.IncidentJournalLayout;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.EventActionPreparation;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Actual policies/preparation/Driver collector/incident/worker consumers with synthetic native packets
 * and the retained original stock corpus. No ManagedGame, native submit or runtime qualification. */
final class UnknownEventProductionChainTest {
    @TempDir Path temporary;
    private static final Instant DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final String EVENT="sway_ongoing.1001";
    private static final int NATIVE_DATE=org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.1.1");
    private static final PlanningReadPort NO_READS=new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("the original validated same-frame window result is already captured");
        }
    };

    @Test void originalDisplayChoiceSerializesThenIndependentCollectorCompletesWorkerAndNextPolicyReadsKnowledge()throws Exception {
        var h=new Harness(temporary.resolve("complete"),true,true);
        OrdinaryPolicy.Replace selected=assertInstanceOf(OrdinaryPolicy.Replace.class,h.policy(h.before,17).evaluate(h.request(h.before,17),OrdinaryPolicy.Draft.empty()));
        ActionCommand ordinary=selected.draft().command().orElseThrow();
        var resolution=PublicEventResolution.plan(h.request(h.before,17),Optional.of(17),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,
            (request,raw)->Optional.of(raw));
        assertEquals(new OpportunityJson.Text("user-first-displayed-event-v1"),((OpportunityJson.Obj)resolution.get("public_event_resolution")).get("selection_strategy"));
        ActionCommand original=new ActionCommand(ordinary.actionId(),ordinary.before(),ordinary.source(),ordinary.sessionId(),ordinary.operation(),resolution,
            ordinary.expected(),ordinary.claims(),ordinary.deadline());
        assertEquals("select-event-option-2",original.operation().value(),"first display is native1, not lowest authored index0");
        JsonNode capture=node(original.arguments()).get("unhandled_event_fallback");
        assertEquals(EVENT,capture.path("event_definition_key").textValue());assertEquals(17,capture.path("current_event_instance_id").intValue());
        assertEquals(0,capture.path("selection").path("rendered_index").intValue());assertEquals(1,capture.path("selection").path("native_option_index").intValue());
        assertEquals(2,capture.path("window_context").path("options").size());assertFalse(capture.path("registry_known").booleanValue());
        ActionCommand command=ActionCodec.decodeCommand(ActionCodec.encodeCommand(original));assertEquals(original,command);
        var ordinaryRow=PublicEventResolution.ordinaryEvent(command.arguments());
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.TWO),ordinaryRow.get("selected_option_number"));
        assertEquals(ordinaryRow,PublicEventResolution.validateOrdinaryEvent(ordinaryRow,17,2));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.ordinaryEvent(command.arguments().with("option_number",new OpportunityJson.IntegerValue(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.validateOrdinaryEvent(ordinaryRow.with("event_index",new OpportunityJson.Bool(true)),17,2));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.validateOrdinaryEvent(ordinaryRow.with("selected_option_index",new OpportunityJson.DecimalValue("1.0")),17,2));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.validateOrdinaryEvent(ordinaryRow.with("title",new OpportunityJson.Bool(false)),17,2));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.validateOrdinaryEvent(ordinaryRow.with("selected_visible_text",new OpportunityJson.Text("changed")),17,2));
        NativeRequest nativeChoice=EventActionPreparation.prepare(command);
        assertEquals(command.operation().value(),nativeChoice.step());
        assertEquals(EventActionPreparation.EVENT_CAPABILITY,nativeChoice.requiredCapability().orElseThrow());
        var ticket=h.journal.before(command).orElseThrow();
        JsonNode beforeBody=StrictJson.parse(Files.readAllBytes(Path.of(ticket.before().path())),1<<20);
        assertEquals(EVENT,beforeBody.path("event_definition_key").textValue());assertEquals(17,beforeBody.path("current_event_instance_id").intValue());
        assertEquals(73,beforeBody.path("binding").path("actor_character_id").intValue());
        assertEquals(NATIVE_DATE,beforeBody.path("binding").path("date_raw").intValue());assertEquals(9,beforeBody.path("binding").path("native_revision").intValue());
        var attempt=h.attempt(command,nativeChoice);
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"synthetic transport lost its result",new byte[]{1},Optional.empty());
        AtomicInteger delivered=new AtomicInteger();
        var effects=new NativeEventEffects(new NativeEffectSnapshots(h.held,h.archive),NO_READS,h.material(),(c,a,p,durable)->{
            delivered.incrementAndGet();assertFalse(assertInstanceOf(ActionPorts.EffectObserved.class,durable.result()).observation().supportingEvidence().isEmpty());
            h.journal.observedAfter(c,a,p,durable);
        });
        var observed=effects.observe(command,attempt,unknown);assertEquals(1,delivered.get());
        var actual=assertInstanceOf(ActionPorts.EffectObserved.class,observed.result()).observation();
        JsonNode compatible=StrictJson.parse(observed.compatibleResult().orElseThrow().bytes(),1<<20);
        assertFalse(compatible.has("accepted"));assertTrue(compatible.path("event_selection").path("postcondition_verified").booleanValue());
        assertEquals(17,compatible.path("event_selection").path("old_event_instance_id").intValue());
        assertEquals(1,compatible.path("event_selection").path("selected_native_option_index").intValue());
        assertTrue(compatible.path("active_event").isNull());
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Applied(actual)));
        assertDoesNotThrow(()->NativeEventEffects.archivedVerifier(command.operation(),h.before.source().sourceRef(),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler()),h.material()).verifier().verify(null,receipt,h.archive));
        var scanned=h.journal.scan(h.binding);assertEquals(0,scanned.incompleteAfter());var batch=scanned.batch().orElseThrow();
        var files=new NativeCheckpointFiles();var io=h.io(files);Path work=Files.createDirectory(h.f.root.resolve("work"));
        AtomicInteger completed=new AtomicInteger();
        var settings=new OfflineEventAnalysisHost.Settings(true,false,Optional.of(h.f.grants),Optional.of(h.f.incidents),Optional.of(h.f.knowledge),Optional.of(h.f.scans));
        var host=OfflineAnalysisFiles.with(io,()->new OfflineEventAnalysisHost(Optional.of(h.f.sources),settings,Optional.of((originalBatch,report)->{
            assertEquals(batch,originalBatch);h.journal.acknowledge(originalBatch,report);completed.incrementAndGet();
        })));
        try(var worker=new OfflineAnalysisWorker(new OfflineAnalysisWorker.Settings(work,2,64),files,io)) {
            var binding=new OfflineAnalysisWorker.Binding(h.f.sources.machineId(),h.f.state,h.f.game,h.f.incidents,h.f.scans,h.f.knowledge,h.f.grants);
            var complete=worker.bind(host,binding,io).enqueue(batch).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertEquals(batch.batchId(),complete.batchId());assertEquals(1,completed.get());assertFalse(complete.persistedReviews().isEmpty());
            assertTrue(h.journal.scan(h.binding).batch().isEmpty());
            var next=h.complete(11,18,false);
            var knownResolution=PublicEventResolution.plan(h.request(next,18),Optional.of(18),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,
                (request,raw)->Optional.of(raw));
            assertEquals(new OpportunityJson.Text("backend-neutral-event-v1"),((OpportunityJson.Obj)knownResolution.get("public_event_resolution")).get("selection_strategy"));
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.ONE),knownResolution.get("option_number"),"only the source-reviewed public generic path uses original score/option-number ordering");
            var knownRow=PublicEventResolution.ordinaryEvent(knownResolution);
            assertEquals(knownRow,PublicEventResolution.validateOrdinaryEvent(knownRow,18,1));
            var repeated=assertInstanceOf(OrdinaryPolicy.Replace.class,h.policy(next,18).evaluate(h.request(next,18),OrdinaryPolicy.Draft.empty()));
            JsonNode nextCapture=node(repeated.draft().command().orElseThrow().arguments()).get("unhandled_event_fallback");
            assertTrue(nextCapture.path("registry_known").booleanValue(),"actual next policy must consume the worker's persisted source review");
            assertFalse(nextCapture.path("offline_followup_required").booleanValue());
            assertEquals("select-event-option-2",repeated.draft().command().orElseThrow().operation().value());
            assertFalse(node(repeated.draft().command().orElseThrow().arguments()).path("event_decision").path("material_effects_verified").booleanValue());
        }
    }

    @Test void ackOnlyDiagnosticRemainsUnsettledUntilOriginalInstanceActuallyAdvances()throws Exception {
        var h=new Harness(temporary.resolve("ack-only"),true,false);
        var selected=assertInstanceOf(OrdinaryPolicy.Replace.class,h.policy(h.before,17).evaluate(h.request(h.before,17),OrdinaryPolicy.Draft.empty()));
        var command=ActionCodec.decodeCommand(ActionCodec.encodeCommand(selected.draft().command().orElseThrow()));
        var prepared=EventActionPreparation.prepare(command);h.journal.before(command).orElseThrow();var attempt=h.attempt(command,prepared);
        var token=new RawJson(bytes("{\"step\":\"select-event-option-2\",\"accepted\":true}"));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),token,new byte[]{1});
        ExactRef originalDispatch=h.archive.preserve(ack);var positive=new AtomicInteger();var negative=new AtomicInteger();
        var effects=new NativeEventEffects(new NativeEffectSnapshots(h.held,h.archive),NO_READS,h.material(),new NativeEventEffects.ObservedAfter() {
            @Override public void record(ActionCommand c,ActionState.Attempt a,NativeEffectSnapshots.Pair p,NativeEffectRegistry.Projected r){positive.incrementAndGet();h.journal.observedAfter(c,a,p,r);}
            @Override public void recordUnsettled(ActionCommand c,ActionState.Attempt a,NativeEventEffects.UnsettledObservation actual) {
                negative.incrementAndGet();try{h.journal.observedUnsettled(c,a,actual,h.archive.referenceOf(actual.dispatch()));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            }
        });
        var result=effects.observe(command,attempt,ack);
        assertInstanceOf(ActionPorts.Pending.class,result.result());assertTrue(result.compatibleResult().isEmpty());
        assertEquals(0,positive.get());assertEquals(1,negative.get());
        assertEquals(1,h.journal.scan(h.binding).incompleteAfter());assertTrue(h.journal.scan(h.binding).batch().isPresent());
        ExactRef diagnostic=h.journal.scan(h.binding).originals().stream().filter(ref->ref.path().endsWith(".unsettled.json")).findFirst().orElseThrow();
        byte[] retained=Files.readAllBytes(Path.of(diagnostic.path()));ObjectNode body=(ObjectNode)StrictJson.parse(retained,1<<20);
        assertEquals("UNSETTLED",body.path("observation_status").textValue());assertEquals("ACK_RECEIVED",body.path("dispatch_kind").textValue());
        assertTrue(body.path("native_ok").booleanValue());assertTrue(body.path("original_instance_present").booleanValue());
        assertFalse(body.path("independent_postcondition_verified").booleanValue());assertFalse(body.path("replay_allowed").booleanValue());
        assertEquals(originalDispatch,ExactRef.fromJson(body.get("original_dispatch_ref")));
        assertInstanceOf(ActionPorts.Pending.class,effects.observe(command,attempt,ack).result());
        assertEquals(diagnostic,h.journal.scan(h.binding).originals().stream().filter(ref->ref.path().endsWith(".unsettled.json")).findFirst().orElseThrow());
        ObjectNode falseCredit=body.deepCopy();falseCredit.put("independent_postcondition_verified",true);Files.write(Path.of(diagnostic.path()),StrictJson.canonical(falseCredit,1<<20));
        assertThrows(IllegalArgumentException.class,()->h.journal.scan(h.binding));Files.write(Path.of(diagnostic.path()),retained);
        var reopened=EpisodeIncidentJournal.open(h.journal.configuration(),h.binding,h.journal.episodeReference());
        assertEquals(1,reopened.scan(h.binding).incompleteAfter());
        h.advance.set(true);assertInstanceOf(ActionPorts.EffectObserved.class,effects.observe(command,attempt,ack).result());
        assertEquals(1,positive.get());assertEquals(2,negative.get());assertEquals(0,reopened.scan(h.binding).incompleteAfter());
        assertArrayEquals(retained,Files.readAllBytes(Path.of(diagnostic.path())),"later qualified after must preserve the first real negative observation");
    }

    @Test void sourceKnownBlockedFirstDisplayStaysBlockedAcrossGenericConsumers()throws Exception {
        for(boolean disabled:new boolean[]{true,false}) {
            var h=new Harness(temporary.resolve(disabled?"known-disabled":"known-unadvertised"),!disabled,false);
            var initial=h.request(h.before,17);
            assertNotEquals(initial.before().frame().revision(),initial.before().frame().identity().nativeRevision());
            if(!disabled) initial=withoutSecondEventSelectionStep(initial);
            assertInstanceOf(OrdinaryPolicy.Wait.class,h.policy(h.before,17).evaluate(initial,OrdinaryPolicy.Draft.empty()));
            assertEquals(1,h.blocked.get());
            var batch=h.journal.scan(h.binding).batch().orElseThrow();
            var files=new NativeCheckpointFiles();var io=h.io(files);
            Path work=Files.createDirectory(h.f.root.resolve("blocked-work"));
            var settings=new OfflineEventAnalysisHost.Settings(true,false,Optional.of(h.f.grants),Optional.of(h.f.incidents),Optional.of(h.f.knowledge),Optional.of(h.f.scans));
            var host=OfflineAnalysisFiles.with(io,()->new OfflineEventAnalysisHost(Optional.of(h.f.sources),settings,Optional.of(h.journal::acknowledge)));
            try(var worker=new OfflineAnalysisWorker(new OfflineAnalysisWorker.Settings(work,2,64),files,io)) {
                var binding=new OfflineAnalysisWorker.Binding(h.f.sources.machineId(),h.f.state,h.f.game,h.f.incidents,h.f.scans,h.f.knowledge,h.f.grants);
                var complete=worker.bind(host,binding,io).enqueue(batch).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
                assertFalse(complete.persistedReviews().isEmpty());
                assertTrue(h.journal.scan(h.binding).batch().isEmpty());
                var next=h.complete(11,18,false);var request=h.request(next,18);
                if(!disabled) request=withoutSecondEventSelectionStep(request);
                var knowledge=org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load();
                var publicPlan=PublicEventResolution.plan(request,Optional.of(18),knowledge,h.trusted,(actual,raw)->Optional.of(raw));
                assertEquals(OpportunityJson.Nil.INSTANCE,publicPlan.get("selected_step"));
                assertEquals(new OpportunityJson.Text("user-first-displayed-event-v1"),
                        ((OpportunityJson.Obj)publicPlan.get("public_event_resolution")).get("selection_strategy"));
                var publicCapture=node(publicPlan).path("unhandled_event_fallback");
                assertTrue(publicCapture.path("registry_known").booleanValue());
                assertEquals(com.fasterxml.jackson.databind.node.BooleanNode.FALSE,publicCapture.path("offline_followup_required"));
                assertEquals(com.fasterxml.jackson.databind.node.BooleanNode.FALSE,node(publicPlan).path("event_decision").path("registry_contract_accepted"));
                assertEquals(com.fasterxml.jackson.databind.node.BooleanNode.FALSE,node(publicPlan).path("event_decision").path("material_effects_verified"));
                assertThrows(IllegalArgumentException.class,()->PublicEventResolution.ordinaryEvent(publicPlan));
                var window=RetainedJson.object(RetainedJson.parse(StrictJson.canonical(h.context(next,18))));
                var direct=new EventDecisionInput(next.identity(),next.source(),next.sessionId(),next.semantic(),request.observations().history(),
                        request.observations().actionSteps(),request.observations().bridgeCapabilities(),request.deadline(),window,Optional.empty());
                assertEquals(publicPlan,PublicEventResolution.plan(direct,Optional.of(18),knowledge,h.trusted));
                assertInstanceOf(OrdinaryPolicy.Wait.class,h.policy(next,18).evaluate(request,OrdinaryPolicy.Draft.empty()));
                assertEquals(2,h.blocked.get());
                var rescan=h.journal.scan(h.binding);
                assertTrue(rescan.batch().isEmpty(), "known blocked diagnostics do not create new offline work");
                var retained=new java.util.ArrayList<JsonNode>();
                for(var ref:rescan.originals()) {
                    if(!ref.path().endsWith(".before.json")) continue;
                    var body=StrictJson.parse(Files.readAllBytes(Path.of(ref.path())),1<<20);
                    if(body.path("current_event_instance_id").intValue()==18) retained.add(body);
                }
                assertEquals(1,retained.size());
                var capture=retained.getFirst();
                assertTrue(capture.path("registry_known").booleanValue());
                assertEquals(com.fasterxml.jackson.databind.node.BooleanNode.FALSE,capture.path("offline_followup_required"));
                assertEquals(0,capture.path("selection").path("rendered_index").intValue());
                assertEquals(1,capture.path("selection").path("native_option_index").intValue());
                assertTrue(capture.path("selection").path("selected_step").isNull());
            }
        }
    }

    @Test void sourceRootDriftRetainsOriginalBlockedDataAndRemainsUnavailable()throws Exception {
        var h=new Harness(temporary.resolve("blocked-source-drift"),false,false);
        Path gui=h.f.game.resolve("gui/event_windows/letter_event.gui");
        Files.writeString(gui,Files.readString(gui)+"\n# source drift\n");
        var request=h.request(h.before,17);
        var unavailable=assertThrows(TrustedEventSourceContext.UnavailableException.class,
                ()->h.policy(h.before,17).evaluate(request,OrdinaryPolicy.Draft.empty()));
        assertEquals(0,unavailable.getSuppressed().length);
        assertEquals(1,h.blocked.get());
        var retained=h.journal.scan(h.binding).batch().orElseThrow().capturedRefs().stream()
                .filter(ref->ref.path().endsWith(".before.json")).toList();
        assertEquals(1,retained.size());
        var capture=StrictJson.parse(Files.readAllBytes(Path.of(retained.getFirst().path())),1<<20);
        assertEquals(EVENT,capture.path("event_definition_key").textValue());
        assertEquals(17,capture.path("current_event_instance_id").intValue());
        assertTrue(capture.path("selection").path("selected_step").isNull());
        assertFalse(capture.has("registry_known"));
        assertTrue(capture.path("offline_followup_required").booleanValue());
    }

    private static PlanningRequest withoutSecondEventSelectionStep(PlanningRequest request) {
        var observed=request.observations();
        return new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),
                new PlanningObservation(observed.snapshot(),observed.history(),Set.of(new OperationKey("select-event-option-1")),
                        observed.bridgeCapabilities(),observed.battleSpeedReadiness(),observed.actionFacts(),
                        observed.campaignGoal(),observed.crossRunPlan(),observed.initialLifestyleFocusRequired()));
    }

    @Test void disabledFirstDisplayIsCapturedAndNeverSkippedToTheLaterEnabledRow()throws Exception {
        var h=new Harness(temporary.resolve("disabled"),false,true);
        var resolution=PublicEventResolution.plan(h.request(h.before,17),Optional.of(17),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,(request,raw)->Optional.of(raw));
        assertEquals(OpportunityJson.Nil.INSTANCE,resolution.get("selected_step"));
        assertEquals(new OpportunityJson.Text("user-first-displayed-event-v1"),((OpportunityJson.Obj)resolution.get("public_event_resolution")).get("selection_strategy"));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.ordinaryEvent(resolution));
        assertInstanceOf(OrdinaryPolicy.Wait.class,h.policy(h.before,17).evaluate(h.request(h.before,17),OrdinaryPolicy.Draft.empty()));
        assertEquals(1,h.blocked.get());assertEquals(0,h.journal.scan(h.binding).incompleteAfter());assertEquals(1,h.journal.scan(h.binding).diagnosticOnly());
        assertTrue(h.journal.scan(h.binding).batch().isPresent());
    }

    @Test void dedicatedBlockedProjectionRetainsPriorityAndResolutionCannotNormalizeUnboundedNativeCounts()throws Exception {
        var h=new Harness(temporary.resolve("dedicated"),true,false);
        h.eventKey="bookmark.1071";
        var actual=h.request(h.before,17);
        var plan=PublicEventResolution.plan(actual,Optional.of(17),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,(request,raw)->Optional.of(raw));
        assertEquals(OpportunityJson.Nil.INSTANCE,plan.get("selected_step"));
        assertEquals(new OpportunityJson.Text("dedicated-native-event-v1"),((OpportunityJson.Obj)plan.get("public_event_resolution")).get("selection_strategy"));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.ordinaryEvent(plan));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.plan(actual,Optional.of(18),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,(request,raw)->Optional.of(raw)));
        var source=actual.observations();
        var event=(OpportunityJson.Obj)source.snapshot().get("active_event");
        var snapshot=source.snapshot().with("active_event",event.with("option_count",new OpportunityJson.IntegerValue(BigInteger.ONE.shiftLeft(1000))));
        var unbounded=new PlanningRequest(actual.before(),actual.source(),actual.sessionId(),actual.deadline(),new PlanningObservation(snapshot,source.history(),source.actionSteps(),source.bridgeCapabilities(),
            source.battleSpeedReadiness(),source.actionFacts(),source.campaignGoal(),source.crossRunPlan(),source.initialLifestyleFocusRequired()));
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.plan(unbounded,Optional.empty(),org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load(),h.trusted,(request,raw)->Optional.of(raw)));
    }

    @Test void genuineOrdinaryAndDirectDataEntryUseOneChoiceAndPreparedSerialization()throws Exception {
        var h=new Harness(temporary.resolve("pure-data"),true,true);var request=h.request(h.before,17);
        var window=RetainedJson.object(RetainedJson.parse(StrictJson.canonical(h.context(h.before,17))));
        var direct=new EventDecisionInput(h.before.identity(),h.before.source(),h.before.sessionId(),h.before.semantic(),request.observations().history(),
                request.observations().actionSteps(),request.observations().bridgeCapabilities(),request.deadline(),window,Optional.empty());
        var knowledge=org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load();
        var ordinary=PublicEventResolution.plan(request,Optional.of(17),knowledge,h.trusted,(actual,raw)->Optional.of(raw));
        var pure=PublicEventResolution.plan(direct,Optional.of(17),knowledge,h.trusted);assertEquals(ordinary,pure);
        assertEquals(PublicEventSelection.plan(request,2,Optional.of(17),knowledge,h.trusted,(actual,raw)->Optional.of(raw)),PublicEventSelection.plan(direct,2,Optional.of(17),knowledge,h.trusted));
        var original=assertInstanceOf(OrdinaryPolicy.Replace.class,h.policy(h.before,17).evaluate(request,OrdinaryPolicy.Draft.empty())).draft().command().orElseThrow();
        var prepared=new ActionCommand(original.actionId(),original.before(),original.source(),original.sessionId(),original.operation(),pure,original.expected(),original.claims(),original.deadline());
        var restored=ActionCodec.decodeCommand(ActionCodec.encodeCommand(prepared));assertEquals(prepared,restored);assertEquals("select-event-option-2",EventActionPreparation.prepare(restored).step());
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.TWO),PublicEventResolution.ordinaryEvent(restored.arguments()).get("selected_option_number"));
    }

    @Test void directDecisionKeepsDedicatedQueryRequiredAndFocusWithoutFirstDisplayOverride()throws Exception {
        var h=new Harness(temporary.resolve("dedicated-data"),true,true);var original=h.request(h.before,17);
        ObjectNode snapshot=(ObjectNode)DriverJson.toNode(h.before.semantic());((ObjectNode)snapshot.get("active_event")).put("option_count",3);
        snapshot.putObject("played_character_gold").put("raw",10000000).put("scale",100000);snapshot.putArray("declarable_wars").addObject().put("target_character_id",84);
        ObjectNode window=h.context(h.before,17);window.put("event_definition_key","bookmark.1071");var scopes=window.putArray("saved_scopes");
        for(String name:List.of("byz_emperor","raiktor")){ObjectNode scope=((ObjectNode)window.get("root_scope")).deepCopy();((ObjectNode)scope.get("typed_identity")).put("character_id",name.equals("byz_emperor")?84:73);var row=scopes.addObject().put("name",name).put("name_identifier",name.equals("byz_emperor")?1:2);row.set("scope",scope);}
        var options=(com.fasterxml.jackson.databind.node.ArrayNode)window.get("options");var third=((ObjectNode)options.get(1)).deepCopy().put("rendered_index",2).put("native_option_index",2).put("enabled",true);options.add(third);
        EventWindowCodec.decode(new RawJson(StrictJson.canonical(window)),new EventWindowModels.Binding(EventWindowModels.Build.CROZIER4,h.before.identity().frame().identity().nativeRevision(),NATIVE_DATE,17));
        var typedSnapshot=DriverJson.object(DriverJson.encode(DriverJson.fromNode(snapshot)),DriverJson.MAX_NATIVE_BYTES);var typedWindow=RetainedJson.object(RetainedJson.parse(StrictJson.canonical(window)));
        var history=new java.util.ArrayList<OpportunityJson.Obj>();for(var row:original.observations().history()){var result=OpportunityJson.object(row.get("result"),"original software window result");history.add(row.with("result",result.with("current_event_window_context",DriverJson.object(StrictJson.canonical(window),DriverJson.MAX_NATIVE_BYTES))));}
        Set<OperationKey> steps=Set.of(new OperationKey("select-event-option-1"),new OperationKey("select-event-option-2"),new OperationKey("select-event-option-3"),new OperationKey("query-war-entry-assessments-v1-1-84"));
        var direct=new EventDecisionInput(h.before.identity(),h.before.source(),h.before.sessionId(),typedSnapshot,history,steps,Set.of(),original.deadline(),typedWindow,Optional.empty());
        var knowledge=org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load();var required=PublicEventResolution.plan(direct,knowledge,h.trusted);
        assertEquals(OpportunityJson.Nil.INSTANCE,required.get("selected_step"));assertEquals(new OpportunityJson.Text("query-war-entry-assessments-v1-1-84"),required.get("required_step"));
        assertEquals(new OpportunityJson.Text("dedicated-native-event-v1"),((OpportunityJson.Obj)required.get("public_event_resolution")).get("selection_strategy"));
        var focused=new EventDecisionInput(direct.before(),direct.source(),direct.sessionId(),direct.snapshot(),direct.history(),direct.actionSteps(),direct.bridgeCapabilities(),direct.deadline(),direct.currentWindow(),Optional.of("succession"));
        var declined=PublicEventResolution.plan(focused,knowledge,h.trusted);assertEquals(new OpportunityJson.Text("select-event-option-3"),declined.get("selected_step"));
        assertEquals(new OpportunityJson.Text("dedicated-native-event-v1"),((OpportunityJson.Obj)declined.get("public_event_resolution")).get("selection_strategy"));
    }

    @Test void directDataCannotSelectFromAnotherWindowAndDisabledFirstRemainsBlocked()throws Exception {
        var h=new Harness(temporary.resolve("direct-blocked"),false,true);var original=h.request(h.before,17);var window=h.context(h.before,17);var knowledge=org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.load();
        var view=new EventDecisionInput(h.before.identity(),h.before.source(),h.before.sessionId(),h.before.semantic(),original.observations().history(),original.observations().actionSteps(),Set.of(),original.deadline(),RetainedJson.object(RetainedJson.parse(StrictJson.canonical(window))),Optional.empty());
        assertEquals(OpportunityJson.Nil.INSTANCE,PublicEventResolution.plan(view,knowledge,h.trusted).get("selected_step"));
        window.put("current_event_instance_id",18);var crossed=new EventDecisionInput(view.before(),view.source(),view.sessionId(),view.snapshot(),view.history(),view.actionSteps(),view.bridgeCapabilities(),view.deadline(),RetainedJson.object(RetainedJson.parse(StrictJson.canonical(window))),view.focus());
        assertThrows(IllegalArgumentException.class,()->PublicEventResolution.plan(crossed,knowledge,h.trusted));
    }

    @Test void actualWindowAdvancementSurvivesUnavailablePrivateMaterialAndArchiveDoesNotResolveAbsentRead()throws Exception {
        var h=new Harness(temporary.resolve("private-material"),true,false);
        var original=assertInstanceOf(OrdinaryPolicy.Replace.class,h.policy(h.before,17).evaluate(h.request(h.before,17),OrdinaryPolicy.Draft.empty())).draft().command().orElseThrow();
        // Deliberately unavailable typed software expectation: this probes effect projection, not
        // qualification of a Bookmark choice or a private Root EVENT token.
        var beforeMaterial=org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material.observe(DriverJson.toNode(h.before.semantic()),null,null);
        var expected=new org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material.Expectation(
                org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material.Status.UNAVAILABLE,beforeMaterial,BigInteger.valueOf(17),"private material reader unavailable");
        var materialExpectation=DriverJson.object(org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material.encode(expected),DriverJson.MAX_NATIVE_BYTES);
        var command=ActionCodec.decodeCommand(ActionCodec.encodeCommand(new ActionCommand(original.actionId(),original.before(),original.source(),original.sessionId(),original.operation(),
                original.arguments().with("event_material_postcondition",materialExpectation),original.expected(),original.claims(),original.deadline())));
        var prepared=EventActionPreparation.prepare(command);var attempt=h.attempt(command,prepared);
        var dispatch=new NativeActionPort.Unknown(attempt.requestId(),"software lost result; no action is retried",new byte[]{1},Optional.empty());
        var resolved=new AtomicInteger();var restored=new AtomicInteger();var selected=new AtomicInteger();
        EventMaterialQuerySource<RawJson> ordinaryOnly=new EventMaterialQuerySource<>() {
            @Override public OperationKey operation(){return new OperationKey("query-player-army-strengths-v1");}
            @Override public EventMaterialQuerySource.Resolved<RawJson> resolve(EventMaterialQuerySource.Frame frame){resolved.incrementAndGet();throw new AssertionError("ordinary material reader is absent from private scope");}
            @Override public EventMaterialQuerySource.Resolved<RawJson> restore(EventMaterialQuerySource.Frame frame,PlanningReadReceipt read,Optional<ExactRef> context,ActionPorts.OutcomeArchive archive){restored.incrementAndGet();throw new AssertionError("no original material read exists to restore");}
        };
        var ordinaryQueries=new NativeEventEffects.MaterialQueries(Optional.of(ordinaryOnly),Optional.empty());
        var effects=new NativeEventEffects(new NativeEffectSnapshots(h.held,h.archive),NO_READS,(NativeEventEffects.MaterialQuerySelection)c->{
            assertSame(command,c);selected.incrementAndGet();return h.material();
        },NativeEventEffects.ObservedAfter.none());
        assertInstanceOf(ActionPorts.Pending.class,effects.observe(command,attempt,dispatch).result());assertEquals(0,selected.get(),"unchanged window must not request extra material");
        h.advance.set(true);var projected=effects.observe(command,attempt,dispatch);var proof=assertInstanceOf(ActionPorts.EffectObserved.class,projected.result()).observation();
        assertEquals(1,selected.get());assertEquals(0,resolved.get());
        var result=StrictJson.parse(projected.compatibleResult().orElseThrow().bytes(),1<<20);
        assertTrue(result.path("event_selection").path("postcondition_verified").booleanValue());assertTrue(result.path("active_event").isNull());assertFalse(result.has("accepted"));
        assertEquals("unavailable",result.path("event_material_postcondition").path("status").textValue());assertTrue(result.path("event_material_postcondition").path("material_change_observed").isNull());
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.Applied(proof)));
        NativeEventEffects.archivedVerifier(command.operation(),command.source().sourceRef(),new DriverFrameEvidenceLoader(new DriverObservationAssembler()),ordinaryQueries)
                .verifier().verify(null,receipt,h.archive);
        assertEquals(0,resolved.get());assertEquals(0,restored.get(),"archive replay uses full registered providers only for original recorded reads");
    }

    private static final class Harness {
        final OfflineInteractionCorpus f;final Archive archive;final HeldDriverObservationPort held;final DriverObservationAssembler.Complete before;
        final EpisodeIncidentJournal journal;final EpisodeIncidentJournal.Binding binding;final TrustedEventSourceContext trusted;
        final boolean enabled;final AtomicInteger blocked=new AtomicInteger();
        final AtomicBoolean advance;
        String eventKey=EVENT;
        Harness(Path root,boolean enabled,boolean advanced)throws Exception {
            f=new OfflineInteractionCorpus(root);this.enabled=enabled;advance=new AtomicBoolean(advanced);archive=new Archive(Files.createDirectory(f.root.resolve("archive")));trusted=TrustedEventSourceContext.open(f.sources);
            var position=new AtomicInteger();held=new HeldDriverObservationPort(deadline->{int n=position.getAndIncrement();return observed(9+n,17,n>0&&advance.get());},
                    actual->new DriverObservationFacts.Known(facts(actual)),archive::preserveNativeFrame,new DriverObservationAssembler(),8);
            before=held.observe(DEADLINE);binding=new EpisodeIncidentJournal.Binding(before.identity(),before.source(),before.sessionId());
            var scope=IncidentJournalLayout.scope(f.incidents,f.scans,binding.before().machineId(),binding.before().game(),binding.sessionId(),binding.before().frame().episodeRunId(),binding.source().sourceRef());
            Files.createDirectory(scope.incidentRoot());Files.createDirectory(scope.scanRoot());Files.createDirectories(f.knowledge);Files.createDirectories(f.grants.getParent());
            journal=EpisodeIncidentJournal.initialize(new EpisodeIncidentJournal.Configuration(scope.incidentRoot(),scope.scanRoot(),Clock.fixed(OfflineInteractionCorpus.NOW,ZoneOffset.UTC),
                    size->{if(size<0||size>(1<<20))throw new IOException("finite original fixture journal output cap");},Optional.of(trusted)),binding);
        }
        DriverObservationAssembler.Complete complete(int revision,int instance,boolean advanced) {
            var actual=observed(revision,instance,advanced);var result=new DriverObservationAssembler().assemble(actual,facts(actual),archive.preserveNativeFrame(actual));
            return assertInstanceOf(DriverObservationAssembler.Complete.class,result);
        }
        PlanningRequest request(DriverObservationAssembler.Complete frame,int instance) {
            ObjectNode context=context(frame,instance);ObjectNode result=StrictJson.object().put("step","query-current-event-window-context-v1").put("accepted",true).put("status","available")
                    .put("queried_snapshot_id",frame.identity().frame().snapshotId()).put("queried_revision",frame.identity().frame().revision())
                    .put("queried_native_revision",frame.identity().frame().identity().nativeRevision())
                    .put("snapshot_revision",frame.identity().frame().identity().nativeRevision()).put("current_event_instance_id",instance).put("date_raw",NATIVE_DATE);result.set("current_event_window_context",context);
            ObjectNode history=StrictJson.object().put("command","query-current-event-window-context-v1").put("ok",true);history.set("result",result);
            return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),DEADLINE,new PlanningObservation(frame.semantic(),List.of(object(history)),
                    Set.of(new OperationKey("select-event-option-1"),new OperationKey("select-event-option-2")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        }
        OrdinaryPolicy policy(DriverObservationAssembler.Complete frame,int instance) {
            var expected=new NativeEventPostconditionPort((command,deadline)->{throw new AssertionError("expectation construction must not perform a second observation");});
            return EventPolicies.policies(frame.source().sourceRef(),Optional.of(trusted),expected,NO_READS,List.of(),(request,raw)->{
                var decoded=EventWindowCodec.decode(new RawJson(RetainedJson.encode(raw)),new EventWindowModels.Binding(EventWindowModels.Build.CROZIER4,
                        request.before().frame().identity().nativeRevision(),request.before().frame().identity().dateRaw().intValueExact(),instance));
                return Optional.of(RetainedJson.object(RetainedJson.parse(EventWindowCodec.encode(decoded).bytes())));
            },(request,plan)->{blocked.incrementAndGet();journal.captureBlocked(request,plan,frame.originalEvidence());},
                    (request,operation,args,plan,purpose,domain)->{throw new AssertionError("event continuation uses its dedicated actual event preparation");})
                    .stream().filter(row->row.stage()==PlanningStage.EVENT_AND_INTERACTION_CONTINUATION).findFirst().orElseThrow();
        }
        ActionState.Attempt attempt(ActionCommand command,NativeRequest prepared) {
            var guard=new GuardEvidence(before.identity(),before.source(),before.sessionId(),before.connectionGeneration(),command.operation(),before.originalEvidence(),before.originalEvidence(),
                    "software-original-native-window-collector",before.observedAt(),DEADLINE);
            return new ActionState.Attempt("unknown-event-original-request",before.observedAt(),guard,prepared);
        }
        NativeEventEffects.MaterialQueries material(){return new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.empty());}
        NativeObservationPort.ObservedFrame observed(int revision,int instance,boolean advanced) {
            String active=advanced?"null":"{\"instance_id\":"+instance+",\"option_count\":2}";
            String state="{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":"+NATIVE_DATE+",\"played_character\":{\"character_id\":73,\"alive\":true,\"stress_points\":10},\"active_event\":"+active+",\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}}";
            byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"event-frame-"+revision+"\",\"revision\":"+revision+",\"state\":"+state+"}");
            byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(f.sources.machineId(),new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))),BigInteger.valueOf(5),"event-held-session"),
                    "event-frame-"+revision,BigInteger.valueOf(revision),new RawJson(bytes(state)),packet,OfflineInteractionCorpus.NOW.plusSeconds(revision));
        }
        DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual) {
            String original="{\"format_version\":2,\"pipe_name\":\"event-test-pipe\",\"bridge_pid\":42,\"episode_character_id\":73,\"episode_run_id\":\"event-chain-episode\",\"last_checkpoint\":null,\"command_history\":[],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}";
            RawJson full=new RawJson(DriverStateSnapshot.decodeComplete(bytes(original)).encode());ExactRef fullRef=archive.preserveMaterial(full);
            var known=DriverFactsRepository.imported(fullRef,full.bytes(),3,7,actual.session().game(),new OpportunityJson.Obj(Map.of()));
            OpportunityJson.Obj diagnostics=OpportunityJson.object(DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES).get("diagnostics"),"original fixture diagnostics")
                    .with("connection_generation",new OpportunityJson.IntegerValue(actual.session().connectionGeneration()))
                    .with("bridge_pid",new OpportunityJson.IntegerValue(BigInteger.valueOf(actual.session().game().pid())));
            OpportunityJson.Obj semantic=new OpportunityJson.Obj(Map.of("diagnostics",diagnostics));
            RawJson manifest=DriverObservationEvidenceReader.encode(known,actual,actual.nativeRevision().add(BigInteger.valueOf(1000)),1,f.binding.source(),semantic,fullRef);
            return DriverObservationEvidenceReader.decode(archive.preserveMaterial(manifest),manifest,full,actual);
        }
        ObjectNode context(DriverObservationAssembler.Complete frame,int instance) {
            var build=EventWindowModels.Build.CROZIER4;
            ObjectNode c=StrictJson.object().put("schema","current-event-window-context-v1").put("schema_version",1).put("status","available")
                    .put("snapshot_revision",frame.identity().frame().identity().nativeRevision()).put("date_raw",NATIVE_DATE).put("current_event_instance_id",instance)
                    .put("window_match_count",1).putNull("unavailable_reason").put("event_definition_key",eventKey).put("calculated_event_id",20001).put("runtime_stats_ordinal",1);
            ObjectNode root=c.putObject("root_scope").put("status","available").put("raw_type_index",4).put("type_key","character").put("subtype",0);
            root.putObject("typed_identity").put("status","available").put("kind","character").put("character_id",73);c.putArray("saved_scopes");
            var options=c.putArray("options");
            for(int rendered=0;rendered<2;rendered++) {
                var row=options.addObject().put("rendered_index",rendered).put("native_option_index",1-rendered).put("shown",true)
                        .put("enabled",rendered!=0||enabled).put("fallback",false).put("cancel",false).put("resolved_name","synthetic displayed "+rendered).put("unavailable_reason","");
                row.putObject("effect_indicators").put("status","available").put("coverage",build.coverage()).put("complete_effect_set",false).putArray("rows");
                row.putObject("effect_preview").put("status","unavailable").put("reason","indicator_subset_has_no_completeness_signal");
                row.putObject("resource_deltas").put("status","unavailable");row.putObject("relationship_deltas").put("status","unavailable");
            }
            c.putObject("readiness").put("event_definition_identity_ready",true).put("root_scope_ready",true).put("saved_scopes_ready",true)
                    .put("option_presentation_ready",true).put("effect_indicators_ready",true).put("effect_preview_ready",false).put("semantic_decision_ready",false);
            c.putObject("provenance").put("backend_id",build.backend()).put("root",build.root()).put("idler_vtable_rva",build.vtable()).put("manager_offset","+0x28");
            EventWindowCodec.decode(new RawJson(StrictJson.canonical(c)),new EventWindowModels.Binding(build,frame.identity().frame().identity().nativeRevision(),NATIVE_DATE,instance));
            return c;
        }
        OfflineAnalysisFiles.Port io(NativeCheckpointFiles files) {
            return new OfflineAnalysisFiles.Port() {
                @Override public void directories(Path path)throws IOException{Files.createDirectories(path);}
                @Override public ExactRef createNew(Path path,byte[] raw)throws IOException{return files.createNew(path,raw).reference();}
                @Override public ExactRef replace(Path path,byte[] raw)throws IOException{return files.replace(path,raw).reference();}
                @Override public void beforeLock(Path path){assertTrue(path.startsWith(f.root));}
                @Override public void beforeLink(Path path,long count){assertTrue(path.startsWith(f.root));assertTrue(count>0);}
            };
        }
    }

    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Path root;
        private final Map<NativeActionPort.DispatchOutcome,ExactRef> dispatches=new HashMap<>();
        Archive(Path root){this.root=root;}
        private ExactRef save(String role,byte[] raw) {
            try {Path path=root.resolve(role+"-"+ActionCodec.sha256(raw)+".bin");if(!Files.exists(path))Files.write(path,raw);return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));}
            catch(IOException error){throw new UncheckedIOException(error);}
        }
        @Override public ExactRef preserveMaterial(RawJson raw){return save("material",raw.bytes());}
        @Override public RawJson loadMaterial(ExactRef ref){try{return new RawJson(Files.readAllBytes(Path.of(ref.path())));}catch(IOException error){throw new UncheckedIOException(error);}}
        @Override public RawJson loadFullMaterial(ExactRef ref) {
            StrictJson.require(ref.bytes()>0 && ref.bytes()<=RawJson.MAXIMUM_BYTES
                    && Path.of(ref.path()).equals(root.resolve("material-"+ref.sha256()+".bin")), "fixture full material must be its original archive object");
            try(var input=Files.newInputStream(Path.of(ref.path()))) {
                byte[] raw=input.readNBytes(Math.toIntExact(ref.bytes())+1);
                StrictJson.require(raw.length==ref.bytes() && ActionCodec.sha256(raw).equals(ref.sha256()), "fixture full material changed");
                return RawJson.fullMaterial(raw);
            } catch(IOException error){throw new UncheckedIOException(error);}
        }
        @Override public ExactRef materialReferenceOf(RawJson raw){return save("material",raw.bytes());}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame frame){return save("native",frame.originalPacket());}
        @Override public byte[] loadNativeFrame(ExactRef ref){try{return Files.readAllBytes(Path.of(ref.path()));}catch(IOException error){throw new UncheckedIOException(error);}}
        // Opaque software archive port retains the actual synthetic native packet, never writer/Game authority.
        // Root production obtains this reference from its already-persisted canonical dispatch archive.
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw){
            byte[] packet=raw instanceof NativeActionPort.AckReceived ack?ack.originalPacket():((NativeActionPort.Unknown)raw).originalRequestPacket();
            ExactRef ref=save("software-original-dispatch-"+raw.requestId(),packet);dispatches.put(raw,ref);return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return dispatches.entrySet().stream().filter(row->row.getValue().equals(ref)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        @Override public ExactRef preserveRequest(NativeRequest raw){throw new AssertionError("fixture does not dispatch");}
        @Override public NativeRequest loadRequest(ExactRef ref){throw new AssertionError("no request archive");}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw){return java.util.Objects.requireNonNull(dispatches.get(raw));}
        @Override public ExactRef requestReferenceOf(NativeRequest raw){throw new AssertionError("no request archive");}
        @Override public ExactRef preserveRead(PlanningReadReceipt raw){throw new AssertionError("already original window result");}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){throw new AssertionError("no material query");}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw){throw new AssertionError("no material query");}
        @Override public ExactRef preserveRecord(ActionRecord raw){throw new AssertionError("no writer");}
        @Override public ActionRecord loadRecord(ExactRef ref){throw new AssertionError("no writer");}
        @Override public ExactRef recordReferenceOf(ActionRecord raw){throw new AssertionError("no writer");}
        @Override public ExactRef preserveReceipt(ActionReceipt raw){throw new AssertionError("no writer");}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw new AssertionError("no writer");}
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw){throw new AssertionError("no writer");}
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ObjectNode node(OpportunityJson.Obj value){return (ObjectNode)StrictJson.parse(DriverJson.encode(value),1<<20);}
    private static OpportunityJson.Obj object(JsonNode value){return DriverJson.object(StrictJson.canonical(value,1<<20),1<<20);}
}
