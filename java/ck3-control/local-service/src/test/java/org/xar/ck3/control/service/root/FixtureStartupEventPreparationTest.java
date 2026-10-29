package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FixtureStartupHandler;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Original Python/native event packets and real source/archive codecs exercise pure preparation.
 * No PendingUiEvent ticket, fake read port, sealed fixture scope, Managed or live qualification is constructed. */
final class FixtureStartupEventPreparationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T22:00:00Z"),DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final BigInteger PUBLIC=new BigInteger("9007199254740993");
    private static ObjectNode original;
    @TempDir Path temporary;
    @BeforeAll static void originalProducers()throws Exception{original=PendingUiEventOriginalTestInputs.load();}

    @Test void originalFirstDisplayedNativeFourUsesSharedPolicyAndRetainsReadParentPolicyAndSerde()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("first"),16*1024*1024)){
            disk.writer.locked(same->{
                var f=new Inputs(disk,disk.archive.withSession(same),same);var data=f.event(true);var origin=f.origin(Optional.empty());
                var command=EventRuntimeInstaller.prepareFixtureEventData(data,origin,Optional.empty(),"fixture-child-1",DEADLINE,RegisteredEventKnowledge.load(),f.trusted);
                assertEquals("select-event-option-4",command.operation().value());assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
                assertEquals(PUBLIC,command.before().frame().revision());
                var metadata=OpportunityJson.object(command.arguments().get("fixture_startup_event_source"),"fixture source");
                assertEquals(new OpportunityJson.Text(origin.parentActionId()),metadata.get("original_parent_action_id"));
                assertEquals(disk.pin,ExactRef.fromJson(DriverJson.toNode(metadata.get("policy_source"))));
                assertEquals(data.original().originalReceipt(),ExactRef.fromJson(DriverJson.toNode(metadata.get("original_read"))));
                assertEquals(data.original().receipt(),f.archive.loadRead(data.original().originalReceipt()));
                NativeRequest nativeRequest=EventActionPreparation.prepare(command);
                var request=NativeWire.decodeExecuteRequest(NativeWire.execute("fixture-child-wire",nativeRequest.step(),command.before().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes()));
                assertEquals("select-event-option-4",request.step());assertTrue(DriverJson.object(request.normalizedAdditionalFields().value(),65536).members().isEmpty());
                assertFalse(command.arguments().members().containsKey("pending_ui_event_source"));return null;
            });
        }
    }
    @Test void typedHandlerSourceAndDecisionRemainInTheSameSharedAutomaticSelection()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("handler"),16*1024*1024)){
            disk.writer.locked(same->{
                var f=new Inputs(disk,disk.archive.withSession(same),same);var data=f.event(true);
                FixtureStartupHandler.Decision decision=new FixtureStartupHandler.AutomaticSharedPolicy(disk.pin);
                assertEquals(decision,FixtureStartupHandler.decodeDecision(FixtureStartupHandler.encodeDecision(decision)));
                var observe=new FixtureStartupHandler.ObserveOnly(disk.pin);
                assertEquals(observe,FixtureStartupHandler.decodeDecision(FixtureStartupHandler.encodeDecision(observe)));
                var origin=new EventRuntimeInstaller.FixtureDecisionOrigin("actual-software-fixture-parent",disk.pin,Optional.of(disk.pin),
                        FixtureStartupHandler.decisionSources(decision),Optional.of(FixtureStartupHandler.encodeDecision(decision)));
                var command=EventRuntimeInstaller.prepareFixtureEventData(data,origin,Optional.empty(),"fixture-handler-child",DEADLINE,RegisteredEventKnowledge.load(),f.trusted);
                assertEquals("select-event-option-4",command.operation().value());
                assertEquals(FixtureStartupHandler.encodeDecision(decision),command.arguments().get("fixture_startup_handler_decision"));
                assertEquals(disk.pin,ExactRef.fromJson(DriverJson.toNode(command.arguments().get("fixture_startup_handler_source"))));
                assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));return null;
            });
        }
    }
    @Test void typedDisplayedSelectionKeepsActualLogScopeAndCanonicalWideOffsetsThroughCommandSerde()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("displayed"),16*1024*1024)){
            disk.writer.locked(same->{
                var f=new Inputs(disk,disk.archive.withSession(same),same);var data=f.event(true);
                long instance=OpportunityJson.integer(OpportunityJson.object(data.frame().semantic().get("active_event"),"actual event").get("instance_id"),"actual instance").longValueExact();
                // Deliberately wide DATA-only codec offsets; this does not qualify a physical log range or a live scope.
                var scope=new FixtureStartupHandler.ActorScope(42,"software-fixture-actor","root",1,2,3,9007199254740993L,9007199254741093L,disk.pin.sha256());
                var decision=new FixtureStartupHandler.SelectDisplayedOption(instance,4,new FixtureStartupHandler.ScopeEvidence(disk.pin,List.of(scope),false),disk.pin);
                var encoded=FixtureStartupHandler.encodeDecision(decision);
                assertEquals(decision,FixtureStartupHandler.decodeDecision(encoded));
                var proof=OpportunityJson.object(encoded.get("proof"),"actual typed scope proof");
                var retainedScope=OpportunityJson.object(((OpportunityJson.Arr)proof.get("scopes")).items().getFirst(),"actual typed scope");
                assertEquals(new OpportunityJson.Text("9007199254740993"),retainedScope.get("byte_start"));
                var origin=new EventRuntimeInstaller.FixtureDecisionOrigin("actual-software-fixture-parent",disk.pin,Optional.of(disk.pin),FixtureStartupHandler.decisionSources(decision),Optional.of(encoded));
                var command=EventRuntimeInstaller.prepareFixtureEventData(data,origin,Optional.of(4),"fixture-displayed-child",DEADLINE,RegisteredEventKnowledge.load(),f.trusted);
                assertEquals("select-event-option-4",command.operation().value());
                var roundtrip=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
                assertEquals(decision,FixtureStartupHandler.decodeDecision(OpportunityJson.object(roundtrip.arguments().get("fixture_startup_handler_decision"),"retained typed handler decision")));
                var wrong=encoded.with("event_instance_id",new OpportunityJson.Text("0"+instance));
                assertThrows(IllegalArgumentException.class,()->FixtureStartupHandler.decodeDecision(wrong));return null;
            });
        }
    }
    @Test void disabledOriginalDisplayAndForeignActualReadNeverPrepareAnotherAction()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("rejected"),16*1024*1024)){
            disk.writer.locked(same->{
                var f=new Inputs(disk,disk.archive.withSession(same),same);var disabled=f.event(false);
                assertThrows(EventRuntimeInstaller.PublicSelectionRejected.class,()->EventRuntimeInstaller.prepareFixtureEventData(disabled,f.origin(Optional.empty()),Optional.empty(),"disabled-child",DEADLINE,RegisteredEventKnowledge.load(),f.trusted));
                var actual=f.event(true);var request=actual.original().receipt().request();
                var wrongRequest=new PlanningReadRequest(request.before(),request.source(),request.sessionId()+"-foreign",request.operation(),request.arguments(),request.deadline());
                var old=actual.original().receipt();
                assertThrows(IllegalArgumentException.class,()->{
                    var foreignReceipt=new PlanningReadReceipt(wrongRequest,old.contractId(),old.requestId(),old.before(),old.after(),old.original());
                    var foreign=new PlanningReadResult.Known<>(actual.original().value(),foreignReceipt,actual.original().originalReceipt());
                    var changed=new EventRuntimeInstaller.FixtureEventData(actual.frame(),foreign,actual.build(),actual.history(),actual.actionSteps(),actual.bridgeCapabilities(),actual.sourceOriginals(),actual.focus());
                    EventRuntimeInstaller.prepareFixtureEventData(changed,f.origin(Optional.empty()),Optional.empty(),"foreign-child",DEADLINE,RegisteredEventKnowledge.load(),f.trusted);
                });return null;
            });
        }
    }
    private static final class Inputs {
        private final CoaSourceArchiveBoundaryTest.Fixture disk;
        private final ActionPorts.OutcomeArchive archive;
        private final Session same;
        private final TrustedEventSourceContext trusted;
        private int sequence;
        private Inputs(CoaSourceArchiveBoundaryTest.Fixture disk,ActionPorts.OutcomeArchive archive,Session same)throws IOException{
            this.disk=disk;this.archive=archive;this.same=same;
            Path stock=Files.createDirectory(disk.directory.resolve("fixture-stock")),state=Files.createDirectory(disk.directory.resolve("fixture-state"));
            byte[] gui;try(var stream=getClass().getResourceAsStream("/unknownnotification/interaction_notification_window.gui")){assertNotNull(stream);gui=stream.readAllBytes();}
            assertEquals(InteractionFallback.GUI_SHA256,DriverJson.sha256(gui));Path file=stock.resolve(InteractionFallback.GUI_SOURCE);Files.createDirectories(file.getParent());Files.write(file,gui);
            trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext(disk.source.machineId(),state,stock));
        }
        private EventRuntimeInstaller.FixtureDecisionOrigin origin(Optional<ExactRef> handler){
            assertTrue(handler.isEmpty());return new EventRuntimeInstaller.FixtureDecisionOrigin("actual-software-fixture-parent",disk.pin,Optional.empty(),List.of(),Optional.empty());
        }
        private EventRuntimeInstaller.FixtureEventData event(boolean enabled)throws IOException{
            var state=(ObjectNode)original.path("pending").get(0).path("packet").path("state").deepCopy();var snapshot=original.path("event_snapshot");
            state.put("date_raw",snapshot.path("date_raw").intValue()).put("paused",true).put("map_ready",true).put("local_player_id",42).putNull("pending_character_interaction");
            ((ObjectNode)state.get("played_character")).put("character_id",42).put("alive",true);state.set("active_event",snapshot.get("active_event").deepCopy());
            var driver=StrictJson.object().put("format_version",2).put("pipe_name","fixture-startup-software").put("bridge_pid",4242).put("episode_character_id",42).put("episode_run_id","fixture-startup-episode");
            for(String key:List.of("last_checkpoint","rollback_war_failure","managed_restore_transaction","succession_expectation","succession_lifecycle","campaign_goal"))driver.putNull(key);driver.putArray("command_history");driver.putArray("rollback_war_failures");
            byte[] driverBytes=DriverStateSnapshot.decodeComplete(DriverJson.encodeNode(driver)).encode();ExactRef driverRef=archive.preserveMaterial(new RawJson(driverBytes));
            var known=DriverFactsRepository.imported(driverRef,driverBytes,3,7,disk.origin().game(),new OpportunityJson.Obj(Map.of()));
            var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:17").put("revision",17);packet.set("state",state);
            var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(disk.source.machineId(),disk.origin().game(),BigInteger.valueOf(3),"fixture-startup-session"),"native:17",BigInteger.valueOf(17),raw(state),NativeWire.packet(DriverJson.encodeNode(packet)),NOW);
            ExactRef nativeRef=archive.preserveNativeFrame(actual);var extras=StrictJson.object();var diagnostics=extras.putObject("diagnostics").put("bridge_pid",4242).put("connection_generation",3);
            diagnostics.putObject("hello").put("expected_ck3_version",EventWindowModels.Build.TOURS.version()).put("expected_ck3_sha256",EventWindowModels.Build.TOURS.sha256());
            var manifest=DriverObservationEvidenceReader.encode(known,actual,PUBLIC,1,disk.source,obj(extras),driverRef);ExactRef manifestRef=archive.preserveMaterial(manifest);
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(driverBytes),actual);var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,nativeRef));
            var context=(ObjectNode)original.get("event").deepCopy();((ObjectNode)context.path("options").get(0)).put("enabled",enabled).put("unavailable_reason",enabled?"":"Not today");
            var contract=EventWindowRead.contract(disk.pin,request->assertEquals(frame.identity(),request.before()));var request=new PlanningReadRequest(frame.identity(),disk.source,frame.sessionId(),contract.operation(),frame.semantic(),DEADLINE);
            String id="fixture-original-event-read-"+(++sequence);var prepared=contract.prepare(request,id);byte[] outbound=NativeWire.execute(id,prepared.step(),frame.identity().frame().identity().nativeRevision(),prepared.additionalFields().bytes());
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",4242).put("connection_generation",3).put("bridge_version","fixture-original-event").put("expected_ck3_sha256",EventWindowModels.Build.TOURS.sha256()).put("game_adapter_id","ck3-1.19.0.6-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(EventWindowRead.CAPABILITY);
            ExactRef helloRef=disk.archive.preserveArtifact(same,NativeWire.packet(DriverJson.encodeNode(hello)),NativeWire.MAXIMUM_FRAME_BYTES+4);
            var guard=new PlanningReadGuard(new GuardEvidence(frame.identity(),disk.source,frame.sessionId(),BigInteger.valueOf(3),contract.operation(),frame.originalEvidence(),helloRef,"software-fixture-event-data",NOW,DEADLINE),true,true,true,frame.fullBindingSha256());
            var result=StrictJson.object().put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",sequence).put("snapshot_revision",17).put("backend_id","native-headless");result.set("current_event_window_context",context);
            var returned=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);returned.set("result",result);
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(raw(result)),raw(returned),NativeWire.packet(DriverJson.encodeNode(returned)),Optional.of(new NativeActionPort.OutboundPacket(id,outbound)));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);ExactRef ref=archive.preserveRead(receipt);var read=new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
            // This source-only fixture's imported driver genuinely has no prior command history;
            // the actual production hook separately consumes sealedScope.history(same).
            var history=new ArrayList<OpportunityJson.Obj>();
            assertTrue(known.driver().commandHistory().isEmpty());
            return new EventRuntimeInstaller.FixtureEventData(frame,read,EventWindowModels.Build.TOURS,history,
                    Set.of(new OperationKey("select-event-option-1"),new OperationKey("select-event-option-2"),new OperationKey("select-event-option-3"),new OperationKey("select-event-option-4")),
                    Set.of(EventActionPreparation.EVENT_CAPABILITY),List.of(disk.pin,helloRef,nativeRef,manifestRef,ref),Optional.empty());
        }
    }
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}
    private static OpportunityJson.Obj obj(JsonNode value){return DriverJson.object(DriverJson.encodeNode(value),DriverJson.MAX_NATIVE_BYTES);}
}
