package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import static org.junit.jupiter.api.Assertions.*;

/** Real warm producer and immutable originals -> pure cold archived reconstruction. No Root recovery
 * issuer, canonical child permission, Ready or live native command is manufactured by these fixtures. */
final class RootPendingUiEventRecoveryTest {
    private static final Instant DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static ObjectNode original;
    @TempDir Path temporary;
    @BeforeAll static void actualOriginalInputs()throws Exception {original=PendingUiEventOriginalTestInputs.load();}

    @Test void originalDisplayedNativeFourReopensAfterWindowDisappearsWithNoReadPrepareOrArchiveWrite()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("event-cold"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                Data data=event(fixture,"original-event",1);var gone=fixture.next(data.current());
                assertSame(OpportunityJson.Nil.INSTANCE,gone.frame().semantic().get("active_event"));
                byte[] bytes=ActionCodec.encodeCommand(data.prepared().command());int admissions=data.livePreparations().get(),queries=fixture.requests;
                long writes=disk.guard.successfulBatches();
                var recovered=recovered(RootPendingUiEventRecovery.recover(data.inputs(),data.originals(),new ArchiveOriginalEvidencePort(disk.archive),same));
                assertEquals(data.prepared(),recovered);assertArrayEquals(bytes,ActionCodec.encodeCommand(recovered.command()));
                var presentation=assertInstanceOf(EventActionPreparation.EventPresentation.class,recovered.presentation());
                assertEquals(3,presentation.selected().nativeOptionIndex());assertEquals(0,presentation.selected().renderedIndex());assertEquals("select-event-option-4",recovered.command().operation().value());
                assertEquals("xar_test.0001",presentation.context().definition().key());assertEquals(2,presentation.context().savedScopes().size());
                assertEquals(admissions,data.livePreparations().get());assertEquals(queries,fixture.requests);assertEquals(writes,disk.guard.successfulBatches());
                // Cold originals keep the old window/frame, even when the actual current UI has gone.
                assertEquals(data.current().frame().identity(),recovered.command().before());assertNotEquals(gone.frame().identity(),recovered.command().before());
                return null;
            });
        }
    }

    @Test void originalLeftReplyAndNotificationAckKeepTheirSameNativeContextAndIntentCodecThroughColdReplay()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("interaction-cold"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                for(String name:List.of("normal","notification")) {
                    Data data=interaction(fixture,name,"original-"+name,1);
                    var intent=intent(data,Optional.empty());byte[] serialized=NaturalClockOriginals.encodeEventIntent(intent);
                    var parsed=NaturalClockOriginals.decodeEventIntent(serialized);assertEquals(intent,parsed);
                    var cold=new RootPendingUiEventRecovery.Original(parsed.command(),parsed.originalRead(),parsed.interaction()?RootPendingUiEventRecovery.Kind.INTERACTION:RootPendingUiEventRecovery.Kind.EVENT,parsed.instanceId(),parsed.sourceOriginals());
                    int queryCount=fixture.requests,prepares=data.livePreparations().get();long writes=disk.guard.successfulBatches();
                    var result=recovered(RootPendingUiEventRecovery.recover(data.inputs(),cold,new ArchiveOriginalEvidencePort(disk.archive),same));
                    assertEquals(data.prepared(),result);assertEquals(-2130706399,result.presentation().instanceId());
                    assertEquals(name.equals("notification")?"acknowledge-pending-character-interaction":"reject-pending-character-interaction",result.command().operation().value());
                    var presentation=assertInstanceOf(EventActionPreparation.InteractionPresentation.class,result.presentation());
                    assertEquals(name.equals("notification")?1:2,presentation.current().buttons().size());
                    assertEquals(queryCount,fixture.requests);assertEquals(prepares,data.livePreparations().get());assertEquals(writes,disk.guard.successfulBatches());
                    assertEquals(EventActionPreparation.prepare(data.prepared().command()),EventActionPreparation.prepare(result.command()));
                    for(String field:List.of("instance_id","interaction","source_originals")) {
                        ObjectNode malformed=(ObjectNode)StrictJson.parse(serialized);malformed.remove(field);
                        assertThrows(RuntimeException.class,()->NaturalClockOriginals.decodeEventIntent(DriverJson.encodeNode(malformed)));
                    }
                    ObjectNode wrong=(ObjectNode)StrictJson.parse(serialized);wrong.put("instance_id",true);
                    assertThrows(IllegalArgumentException.class,()->NaturalClockOriginals.decodeEventIntent(DriverJson.encodeNode(wrong)));
                }
                return null;
            });
        }
    }

    @Test void lostSourcesReadIdentityFrameKindAndExactPresentationRemainMissingRatherThanSelectingAgain()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("missing-originals"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                Data event=event(fixture,"event-negative",1),reply=interaction(fixture,"normal","reply-negative",1);
                var reader=new ArchiveOriginalEvidencePort(disk.archive);
                var missingRead=new RootPendingUiEventRecovery.Original(event.originals().command(),new ExactRef(temporary.resolve("not-in-archive.json").toString(),1,"a".repeat(64)),RootPendingUiEventRecovery.Kind.EVENT,17,event.originals().sourceOriginals());
                assertEquals(RootPendingUiEventRecovery.Reason.READ_ORIGINAL,missing(RootPendingUiEventRecovery.recover(event.inputs(),missingRead,reader,same)).reason());
                var differentKind=new RootPendingUiEventRecovery.Original(event.originals().command(),event.originals().originalRead(),RootPendingUiEventRecovery.Kind.INTERACTION,17,event.originals().sourceOriginals());
                assertEquals(RootPendingUiEventRecovery.Reason.READ_BINDING,missing(RootPendingUiEventRecovery.recover(event.inputs(),differentKind,reader,same)).reason());
                var differentInstance=new RootPendingUiEventRecovery.Original(event.originals().command(),event.originals().originalRead(),RootPendingUiEventRecovery.Kind.EVENT,18,event.originals().sourceOriginals());
                assertEquals(RootPendingUiEventRecovery.Reason.READ_BINDING,missing(RootPendingUiEventRecovery.recover(event.inputs(),differentInstance,reader,same)).reason());
                var switchedRead=new RootPendingUiEventRecovery.Original(event.originals().command(),reply.originals().originalRead(),RootPendingUiEventRecovery.Kind.EVENT,17,event.originals().sourceOriginals());
                assertEquals(RootPendingUiEventRecovery.Reason.SOURCE_ORIGINALS,missing(RootPendingUiEventRecovery.recover(event.inputs(),switchedRead,reader,same)).reason());
                ObjectNode lostMetadata=tree(event.prepared().command().arguments());lostMetadata.remove("pending_ui_event_source");
                assertEquals(RootPendingUiEventRecovery.Reason.SOURCE_ORIGINALS,missing(recoverChanged(event,lostMetadata,fixture)).reason());
                ObjectNode lostPresentation=tree(reply.prepared().command().arguments());
                ((ObjectNode)lostPresentation.path("unhandled_interaction_fallback").path("gui_binding")).remove("current_presentation");
                assertEquals(RootPendingUiEventRecovery.Reason.PRESENTATION,missing(recoverChanged(reply,lostPresentation,fixture)).reason());
                ObjectNode wrongOption=tree(event.prepared().command().arguments());wrongOption.put("native_option_index",0);
                assertEquals(RootPendingUiEventRecovery.Reason.PRESENTATION,missing(recoverChanged(event,wrongOption,fixture)).reason());
                ObjectNode changedDisplay=tree(event.prepared().command().arguments());((ObjectNode)changedDisplay.get("selected_native_event_option")).put("resolved_name","changed caption");
                assertEquals(RootPendingUiEventRecovery.Reason.PRESENTATION,missing(recoverChanged(event,changedDisplay,fixture)).reason());
                ObjectNode changedSender=tree(reply.prepared().command().arguments());((ObjectNode)changedSender.path("unhandled_interaction_fallback").path("context").path("roles")).put("actor_character_id",true);
                assertEquals(RootPendingUiEventRecovery.Reason.PRESENTATION,missing(recoverChanged(reply,changedSender,fixture)).reason());
                var reordered=new ArrayList<>(event.originals().sourceOriginals());java.util.Collections.swap(reordered,0,1);
                var badClosure=new RootPendingUiEventRecovery.Original(event.originals().command(),event.originals().originalRead(),RootPendingUiEventRecovery.Kind.EVENT,17,reordered);
                assertEquals(RootPendingUiEventRecovery.Reason.SOURCE_ORIGINALS,missing(RootPendingUiEventRecovery.recover(event.inputs(),badClosure,reader,same)).reason());
                // Same bytes/hash at an uncommitted path are not archive custody. Keep the original.
                var originalSource=event.originals().sourceOriginals().getFirst();byte[] bytes=reader.read(same,originalSource,1024*1024);
                Path foreign=temporary.resolve("same-bytes-foreign.json");Files.write(foreign,bytes);var foreignRef=new ExactRef(foreign.toString(),bytes.length,DriverJson.sha256(bytes));
                ObjectNode foreignArgs=tree(event.prepared().command().arguments());var source=(ObjectNode)foreignArgs.get("pending_ui_event_source");
                var declared=(com.fasterxml.jackson.databind.node.ArrayNode)source.get("source_originals");declared.set(0,foreignRef.toJson());
                var changedCommand=changed(event.prepared().command(),foreignArgs);var changedReference=fixture.archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(changedCommand)));
                var closure=new ArrayList<>(event.originals().sourceOriginals());closure.set(0,foreignRef);
                var foreignOriginal=new RootPendingUiEventRecovery.Original(changedReference,event.originals().originalRead(),RootPendingUiEventRecovery.Kind.EVENT,17,closure);
                var denied=missing(RootPendingUiEventRecovery.recover(event.inputs(),foreignOriginal,reader,same));
                assertEquals(RootPendingUiEventRecovery.Reason.SOURCE_ORIGINALS,denied.reason());assertTrue(denied.detail().contains(foreign.toString()));
                assertNotEquals(originalSource,foreignRef);assertArrayEquals(bytes,reader.read(same,originalSource,1024*1024));
                return null;
            });
        }
    }

    @Test void originalUnknownReceiptAndCompleteCommandRemainUnchangedAcrossRepeatedColdDataReplays()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("unknown-cold"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                Data data=event(fixture,"unknown-original-event",1);var later=fixture.later(data.current(),false);
                ActionReceipt unknown=fixture.effect(data.prepared(),data.current(),later,false);assertFalse(unknown.settled());assertTrue(unknown.applied().isEmpty());
                ExactRef originalReceipt=fixture.archive.receiptReferenceOf(unknown);var serialized=ActionReceiptCodec.encodeReceipt(unknown,fixture.archive);
                var recorded=intent(data,Optional.of(originalReceipt));var roundtrip=NaturalClockOriginals.decodeEventIntent(NaturalClockOriginals.encodeEventIntent(recorded));
                var retained=new RootPendingUiEventRecovery.Original(roundtrip.command(),roundtrip.originalRead(),RootPendingUiEventRecovery.Kind.EVENT,roundtrip.instanceId(),roundtrip.sourceOriginals());
                int reads=fixture.requests,admissions=data.livePreparations().get();long writes=disk.guard.successfulBatches();
                for(int repeat=0;repeat<3;repeat++) {
                    var recovered=recovered(RootPendingUiEventRecovery.recover(data.inputs(),retained,new ArchiveOriginalEvidencePort(disk.archive),same));
                    assertArrayEquals(ActionCodec.encodeCommand(unknown.command()),ActionCodec.encodeCommand(recovered.command()));
                    assertEquals(unknown,fixture.archive.loadReceipt(originalReceipt));assertArrayEquals(serialized,ActionReceiptCodec.encodeReceipt(unknown,fixture.archive));
                }
                assertEquals(reads,fixture.requests);assertEquals(admissions,data.livePreparations().get());assertEquals(writes,disk.guard.successfulBatches());
                assertFalse(unknown.settled());assertEquals(ActionReceipt.Outcome.UNRESOLVED,unknown.outcome());
                return null;
            });
        }
    }

    @Test void actualPendingDriverRetainsPredecessorGoalFocusWithoutAdvancingGoalAndForeignGoalKeepsOriginalReadDiagnosis()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("retained-goal"),24*1024*1024)) {
            disk.writer.locked(same->{
                var fixture=new PendingUiEventPreparationTest.Inputs(disk,disk.archive.withSession(same),same);
                Data initial=event(fixture,"no-goal-original",1);
                var absent=OpportunityJson.object(initial.prepared().command().arguments().get("pending_ui_focus_evidence"),"private focus diagnostic");
                assertEquals(new OpportunityJson.Text("goal_absent"),absent.get("status"));assertSame(OpportunityJson.Nil.INSTANCE,absent.get("focus"));
                long predecessor=initial.current().originalParent().lifecycleBefore().subject().characterId().longValueExact();
                var oldGoal=OrdinaryCampaignGoal.newGoal("actual-software-retained-campaign",predecessor);
                var current=withGoal(fixture,initial.current(),GoalCodec.encodeGoal(oldGoal));
                assertNotEquals(BigInteger.valueOf(oldGoal.currentCharacterId()),current.frame().identity().frame().identity().player());
                var prepared=eventPrepared(fixture,current,initial.inputs().eventWindow(),"with-original-retained-goal",2);
                var evidence=OpportunityJson.object(prepared.command().arguments().get("pending_ui_focus_evidence"),"same old goal DATA");
                assertEquals(new OpportunityJson.Text("retained_parent_goal"),evidence.get("status"));assertEquals(new OpportunityJson.Text("marriage"),evidence.get("focus"));
                assertEquals(new OpportunityJson.Bool(false),evidence.get("goal_progress_advanced"));
                assertEquals(oldGoal,GoalCodec.decodeGoal(DriverJson.encode(evidence.get("retained_goal"))));
                assertEquals(0,oldGoal.progress().reconciledSuccessions());assertTrue(oldGoal.progress().lastSuccession().isEmpty());
                assertEquals(oldGoal,GoalCodec.decodeGoal(((DriverStateSnapshot.Value)current.known().driver().campaignGoal()).json()));
                Data retained=data(fixture,current,prepared,initial.inputs(),initial.livePreparations());
                assertEquals(prepared,recovered(RootPendingUiEventRecovery.recover(retained.inputs(),retained.originals(),new ArchiveOriginalEvidencePort(disk.archive),same)));
                var premature=OrdinaryCampaignGoal.newGoal("actual-software-retained-campaign",current.frame().identity().frame().identity().player().longValueExact());
                var wrong=withGoal(fixture,initial.current(),GoalCodec.encodeGoal(premature));
                var denied=assertThrows(EventActionPreparation.PendingSelectionRejected.class,()->eventPrepared(fixture,wrong,initial.inputs().eventWindow(),"foreign-goal",3));
                assertEquals(new OpportunityJson.Text("pending_event_retained_campaign_goal_mismatch"),denied.diagnosis().get("phase"));
                assertSame(OpportunityJson.Nil.INSTANCE,denied.diagnosis().get("selected_step"));assertTrue(denied.originalRead().bytes()>0);
                assertEquals(0,premature.progress().reconciledSuccessions());
                return null;
            });
        }
    }

    private record Data(RootPendingUiEventRecovery.Inputs inputs,PendingUiEvent.Current current,
            EventActionPreparation.PendingPrepared prepared,RootPendingUiEventRecovery.Original originals,AtomicInteger livePreparations){ }
    private static Data event(PendingUiEventPreparationTest.Inputs fixture,String id,long sequence)throws IOException {
        var state=(ObjectNode)pending("normal").path("packet").path("state").deepCopy();var snapshot=original.path("event_snapshot");
        state.put("date_raw",snapshot.path("date_raw").intValue()).put("paused",true).put("map_ready",true).put("local_player_id",42).putNull("pending_character_interaction");
        ((ObjectNode)state.get("played_character")).put("character_id",42).put("alive",true);state.set("active_event",snapshot.get("active_event").deepCopy());
        var current=fixture.frame(state,17,42,0);var count=new AtomicInteger();
        var event=counted(EventWindowRead.contract(fixture.disk.pin,request->assertEquals(current.frame().identity(),request.before())),count);
        var pending=counted(PendingInteractionContracts.pending(fixture.disk.pin),count);
        var prepared=eventPrepared(fixture,current,event,id,sequence);
        return data(fixture,current,prepared,new RootPendingUiEventRecovery.Inputs(event,pending),count);
    }
    private static EventActionPreparation.PendingPrepared eventPrepared(PendingUiEventPreparationTest.Inputs fixture,PendingUiEvent.Current current,
            ReadContract<EventPolicies.ReadPublication> event,String id,long sequence)throws IOException {
        ObjectNode context=(ObjectNode)original.get("event").deepCopy();((ObjectNode)context.path("options").get(0)).put("enabled",true).put("unavailable_reason","");
        var result=StrictJson.object().put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",sequence).put("snapshot_revision",17).put("backend_id","native-headless");result.set("current_event_window_context",context);
        var request=new PlanningReadRequest(current.frame().identity(),current.frame().source(),current.frame().sessionId(),event.operation(),current.frame().semantic(),DEADLINE);
        var read=read(fixture,current,event,request,result);
        return PendingUiEventPreparation.event(current,read,EventWindowModels.Build.TOURS,Set.of(new OperationKey("select-event-option-1"),new OperationKey("select-event-option-2"),new OperationKey("select-event-option-3"),new OperationKey("select-event-option-4")),id,DEADLINE,RegisteredEventKnowledge.load(),fixture.trusted);
    }
    private static PendingUiEvent.Current withGoal(PendingUiEventPreparationTest.Inputs fixture,PendingUiEvent.Current original,byte[] goal)throws IOException {
        ObjectNode driver=(ObjectNode)DriverJson.toNode(DriverJson.object(original.known().driver().encode(),DriverJson.MAX_NATIVE_BYTES));driver.set("campaign_goal",StrictJson.parse(goal));
        byte[] bytes=DriverStateSnapshot.decodeComplete(DriverJson.encodeNode(driver)).encode();ExactRef reference=fixture.archive.preserveMaterial(new RawJson(bytes));
        var actual=DriverFactsRepository.imported(reference,bytes,original.known().stamp().driverVersion(),original.known().stamp().episodeEpoch(),original.known().stamp().game(),original.known().auxiliary());
        var nativeFrame=original.full().actual();var manifest=DriverObservationEvidenceReader.encode(actual,nativeFrame,original.frame().identity().frame().revision(),original.frame().identity().observationVersion(),original.frame().source(),original.full().facts().originalSemanticFields(),reference);
        ExactRef manifestRef=fixture.archive.preserveMaterial(manifest);var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(bytes),nativeFrame);var assembler=new DriverObservationAssembler();
        var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,assembler.assemble(nativeFrame,facts,original.frame().originalEvidence()));
        return new PendingUiEvent.Current(original.originalParent(),assembler.projectFull(nativeFrame,facts,original.frame().originalEvidence()),actual,frame,reference,actual.originalHistoryBasis(),original.canonicalPublication(),original.canonicalDomain(),original.qualifiedCause(),original.bridgeCapabilities());
    }
    private static Data interaction(PendingUiEventPreparationTest.Inputs fixture,String name,String id,long sequence)throws IOException {
        var row=pending(name);var current=fixture.pending(row);var count=new AtomicInteger();
        var event=counted(EventWindowRead.contract(fixture.disk.pin,request->assertEquals(current.frame().identity(),request.before())),count);
        var pending=counted(PendingInteractionContracts.pending(fixture.disk.pin),count);
        var context=new RootInteractionContextProjection(InteractionModels.Build.WANDERER6).project(current.frame(),DEADLINE);
        var request=new PlanningReadRequest(current.frame().identity(),current.frame().source(),current.frame().sessionId(),pending.operation(),PendingInteractionReadArguments.current(context),DEADLINE);
        var result=(ObjectNode)row.get("query").deepCopy();result.put("query_sequence",sequence);var read=read(fixture,current,pending,request,result);
        var steps=new java.util.HashSet<OperationKey>();row.path("steps").forEach(value->steps.add(new OperationKey(value.textValue())));
        var prepared=PendingUiEventPreparation.interaction(current,read,context,Set.copyOf(steps),id,DEADLINE,fixture.trusted);
        return data(fixture,current,prepared,new RootPendingUiEventRecovery.Inputs(event,pending),count);
    }
    private static Data data(PendingUiEventPreparationTest.Inputs fixture,PendingUiEvent.Current current,EventActionPreparation.PendingPrepared prepared,
            RootPendingUiEventRecovery.Inputs inputs,AtomicInteger count) {
        var command=fixture.archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(prepared.command())));
        var retained=new RootPendingUiEventRecovery.Original(command,prepared.originalReadRef(),prepared.presentation() instanceof EventActionPreparation.InteractionPresentation?RootPendingUiEventRecovery.Kind.INTERACTION:RootPendingUiEventRecovery.Kind.EVENT,prepared.presentation().instanceId(),prepared.sourceOriginals());
        return new Data(inputs,current,prepared,retained,count);
    }
    private static <T>PlanningReadResult.Known<T> read(PendingUiEventPreparationTest.Inputs fixture,PendingUiEvent.Current current,
            ReadContract<T> contract,PlanningReadRequest request,ObjectNode result)throws IOException {
        var original=fixture.read(current,contract,request,result);
        // The shared early fixture's HELLO advertises only the event query. Retain a complete
        // software HELLO for both actual native families, before this warm preparation is captured.
        var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",4242).put("connection_generation",3)
                .put("bridge_version","original-wire-fixture").put("expected_ck3_sha256",EventWindowModels.Build.TOURS.sha256())
                .put("game_adapter_id","ck3-"+EventWindowModels.Build.TOURS.version()+"-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
        hello.putArray("capabilities").add(EventWindowRead.CAPABILITY).add(PendingContextCodec.CAPABILITY);
        ExactRef retainedHello=fixture.disk.archive.preserveArtifact(fixture.same,NativeWire.packet(DriverJson.encodeNode(hello)),NativeWire.MAXIMUM_FRAME_BYTES+4);
        var receipt=original.receipt();var first=helloGuard(receipt.before(),retainedHello);var second=helloGuard(receipt.after(),retainedHello);
        var complete=new PlanningReadReceipt(receipt.request(),receipt.contractId(),receipt.requestId(),first,second,receipt.original());
        ExactRef reference=fixture.archive.preserveRead(complete);return new PlanningReadResult.Known<>(contract.decode(complete),complete,reference);
    }
    private static PlanningReadGuard helloGuard(PlanningReadGuard original,ExactRef hello) {
        var old=original.binding();var actual=new GuardEvidence(old.origin(),old.source(),old.sessionId(),old.connectionGeneration(),old.operation(),old.nativeEvidence(),hello,
                old.authorityId(),old.observedAt(),old.validUntil(),old.supportingEvidence());
        return new PlanningReadGuard(actual,original.paused(),original.mapReady(),original.playerAlive(),original.originalBindingSha256());
    }
    private static <T>ReadContract<T> counted(ReadContract<T> actual,AtomicInteger live) {
        // Instrument the real family's preparation, while retaining its original live decoder and
        // explicit pure replay. This grants no installed Root or read permission in the fixture.
        return new ReadContract<>(actual.contractId(),actual.operation(),actual.requiredCapability(),actual.permissionKey(),actual.permissionMode(),actual.wireProfile(),actual.guardMode(),actual.sourceRef(),
                (request,id)->{live.incrementAndGet();return actual.prepare(request,id);},actual::decode,actual::replay);
    }
    private static NaturalClockOriginals.EventIntent intent(Data data,Optional<ExactRef> receipt) {
        return new NaturalClockOriginals.EventIntent(data.prepared().command().before().machineId(),1,data.prepared().command().actionId(),ActionCodec.bodySha256(data.prepared().command()),data.originals().command(),data.originals().originalRead(),data.originals().instanceId(),data.originals().kind()==RootPendingUiEventRecovery.Kind.INTERACTION,data.originals().sourceOriginals(),Optional.empty(),receipt,Optional.empty(),data.current().frame().observedAt());
    }
    private static RootPendingUiEventRecovery.Result recoverChanged(Data original,ObjectNode arguments,PendingUiEventPreparationTest.Inputs fixture)throws IOException {
        var command=changed(original.prepared().command(),arguments);ExactRef ref=fixture.archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(command)));
        var retained=new RootPendingUiEventRecovery.Original(ref,original.originals().originalRead(),original.originals().kind(),original.originals().instanceId(),original.originals().sourceOriginals());
        return RootPendingUiEventRecovery.recover(original.inputs(),retained,new ArchiveOriginalEvidencePort(fixture.disk.archive),fixture.same);
    }
    private static ActionCommand changed(ActionCommand original,ObjectNode args) {
        return new ActionCommand(original.actionId(),original.origin(),original.source(),original.sessionId(),original.operation(),DriverJson.object(DriverJson.encodeNode(args),ActionCommand.MAX_ARGUMENT_BYTES),original.expectation(),original.claims(),original.deadline());
    }
    private static EventActionPreparation.PendingPrepared recovered(RootPendingUiEventRecovery.Result result) {
        return assertInstanceOf(RootPendingUiEventRecovery.Recovered.class,result).prepared();
    }
    private static RootPendingUiEventRecovery.Missing missing(RootPendingUiEventRecovery.Result result) {return assertInstanceOf(RootPendingUiEventRecovery.Missing.class,result);}
    private static ObjectNode tree(OpportunityJson.Obj object){return (ObjectNode)DriverJson.toNode(object);}
    private static ObjectNode pending(String name){for(JsonNode row:original.path("pending"))if(name.equals(row.path("name").textValue()))return (ObjectNode)row.deepCopy();throw new AssertionError(name);}
}
