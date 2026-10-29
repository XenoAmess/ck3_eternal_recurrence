package org.xar.ck3.control.nativebridge;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;
import static org.junit.jupiter.api.Assertions.*;

/** The sole SAVE composition fixture and actual software writer/material consumers. No private Core or Managed ticket is fabricated. */
public final class RootSaveCheckpointCommandProducerTest {
    @TempDir Path temporary;
    private static CheckpointRequestFactory factory(CheckpointSourceCompositionTest.Fixture f) {
        return new CheckpointRequestFactory(f.request.expectedSavePath(),f.actual.collector.checkpoint(f.request.lineageId()));
    }
    @Test void actualTypedProducerDispatchesOneCanonicalSaveAndCommitsItsOriginalPreSaveMaterial()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("planned-confirmed"),false)){
            var observation=f.actual.collector.observe(f.owner,Instant.now().plusSeconds(60));
            var before=assertInstanceOf(SessionPorts.Ready.class,observation,observation::toString);
            String id=ActionIds.forDecision(before.request().sessionId(),before.request().before(),"actual-baseline-save");
            var prepared=RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),before.request(),id);
            assertEquals(id,prepared.saveCommand().actionId());assertTrue(prepared.saveCommand().arguments().members().isEmpty());
            assertArrayEquals(ActionCodec.encodeCommand(prepared.saveCommand()),ActionCodec.encodeCommand(ActionCodec.decodeCommand(ActionCodec.encodeCommand(prepared.saveCommand()))));
            var materials=new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
            var pending=f.actual.writer.locked(same->materials.begin(same,f.owner,before.semanticEvidence().orElseThrow(),prepared));
            assertEquals(0,f.actual.nativeActionWrites());
            var checkpointResult=f.service.checkpoint(prepared);
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,checkpointResult,()->checkpointResult+"; actual reconciliation failure: "+reconciliationFailure(f));
            assertEquals(1,f.actual.nativeActionWrites());assertEquals(prepared.saveCommand(),confirmed.action().command());
            assertEquals(confirmed.pair(),CheckpointPairCodec.decode(CheckpointPairCodec.encode(confirmed.pair())));
            f.actual.writer.locked(same->{
                var captured=materials.confirm(same,pending,confirmed);assertTrue(pending.materialConfirmed());captured.requirePhysical(same);
                assertEquals(SavedCheckpointMaterial.Kind.ORDINARY,captured.material().kind());
                assertEquals(before.semanticEvidence().orElseThrow(),captured.material().sourceSemantic());
                assertEquals(captured.material().reference(),f.sources.loadRetainedOriginal(same,captured.material().witness(),confirmed.pair()).reference());
                assertSame(captured,materials.confirm(same,pending,confirmed));return null;
            });
            assertEquals(1,f.actual.nativeActionWrites(),"material confirmation cannot issue another SAVE");
        }
    }
    @Test void originalUnknownUsesItsExactQueryAndNeverPreparesOrWritesAnotherSave()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("planned-unknown"),true)){
            var observation=f.actual.collector.observe(f.owner,Instant.now().plusSeconds(60));
            var before=assertInstanceOf(SessionPorts.Ready.class,observation,observation::toString);
            var prepared=RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),before.request(),"actual-planned-unknown");
            var materials=new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
            var pending=f.actual.writer.locked(same->materials.begin(same,f.owner,before.semanticEvidence().orElseThrow(),prepared));
            var initialResult=f.service.checkpoint(prepared);
            assertInstanceOf(CheckpointResult.Unknown.class,initialResult);
            for(int i=0;i<2;i++)assertInstanceOf(CheckpointResult.Unknown.class,f.service.queryOriginal(prepared.saveCommand().actionId(),Instant.now().plusSeconds(5)));
            assertEquals(1,f.actual.nativeActionWrites(),initialResult::toString);assertFalse(pending.materialConfirmed());
            assertFalse(Files.exists(f.actual.root.resolve("saved-driver.json")));
            f.actual.writer.locked(same->{
                var original=ContinuityActionJournal.lookup(same.head().state(),prepared.saveCommand().actionId(),f.actual.archive.withSession(same)).orElseThrow();
                assertFalse(original.settled());assertEquals(prepared.saveCommand(),original.command());return null;
            });
        }
    }
    @Test void actualFactoryRefusesAChangedOriginalSessionBeforeAnySaveDispatch()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("planned-foreign"),false)){
            PlanningRequest before=f.actual.ready().request();
            var foreign=new PlanningRequest(before.before(),before.source(),"foreign-planned-session",before.deadline(),before.observations());
            assertThrows(RuntimeException.class,()->RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),foreign,"foreign-save"));
            assertEquals(0,f.actual.nativeActionWrites());
        }
    }
    @Test void actualTypedFactoryFeedsEveryOriginalCheckpointChoiceWhilePostwarMetadataStaysOutsideNativeArguments()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("planned-choices"),false)){
            var ready=f.actual.ready();
            PlanningRequest original=ready.request();
            var request=RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),original,"actual-choice-save");
            for(String phase:List.of("baseline","periodic_checkpoint","post_milestone_checkpoint","native_postwar_checkpoint")){
                var arguments=phase.equals("native_postwar_checkpoint")?obj(StrictJson.object().put("postwar_disband_history_index",7)):obj(StrictJson.object());
                var detail=arguments.with("policy",new OpportunityJson.Text("one-life-turn-v1")).with("phase",new OpportunityJson.Text(phase))
                        .with("reason",new OpportunityJson.Text("actual original checkpoint choice")).with("selected_step",new OpportunityJson.Text("save-checkpoint"));
                var select=new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,"actual original checkpoint choice",request.saveCommand().operation(),arguments,OrdinaryPolicy.Purpose.WORLD_ACTION,detail);
                var owned=MilitaryPlanningDecision.PreparedSelection.checkpoint(request.saveCommand().actionId(),original,select,request);
                assertSame(request.saveCommand(),owned.requireOriginalChoice(original,select.operation(),arguments,detail));
                assertTrue(owned.command().arguments().members().isEmpty());
                assertThrows(IllegalArgumentException.class,()->owned.requireOriginalChoice(original,select.operation(),arguments,detail.with("reason",new OpportunityJson.Text("changed choice"))));
            }
            for(var wrong:List.of(StrictJson.object().put("postwar_disband_history_index",true),StrictJson.object().put("postwar_disband_history_index",7.0),
                    StrictJson.object().put("postwar_disband_history_index",0),StrictJson.object().put("postwar_disband_history_index",7).put("extra",true))){
                assertThrows(IllegalArgumentException.class,()->{
                    var arguments=obj(wrong);
                    var detail=arguments.with("policy",new OpportunityJson.Text("one-life-turn-v1")).with("phase",new OpportunityJson.Text("native_postwar_checkpoint"))
                            .with("reason",new OpportunityJson.Text("invalid metadata")).with("selected_step",new OpportunityJson.Text("save-checkpoint"));
                    var select=new MilitaryPlanningDecision.Select("one-life-turn-v1","native_postwar_checkpoint","invalid metadata",request.saveCommand().operation(),arguments,OrdinaryPolicy.Purpose.WORLD_ACTION,detail);
                    MilitaryPlanningDecision.PreparedSelection.checkpoint(request.saveCommand().actionId(),original,select,request);
                });
            }
            var wrongPhaseDetail=obj(StrictJson.object().put("phase","baseline").put("postwar_disband_history_index",7))
                    .with("policy",new OpportunityJson.Text("one-life-turn-v1")).with("reason",new OpportunityJson.Text("wrong phase"))
                    .with("selected_step",new OpportunityJson.Text(request.saveCommand().operation().value()));
            var wrongPhase=new MilitaryPlanningDecision.Select("one-life-turn-v1","baseline","wrong phase",request.saveCommand().operation(),
                    obj(StrictJson.object().put("postwar_disband_history_index",7)),OrdinaryPolicy.Purpose.WORLD_ACTION,wrongPhaseDetail);
            assertThrows(IllegalArgumentException.class,()->MilitaryPlanningDecision.PreparedSelection.checkpoint(request.saveCommand().actionId(),original,wrongPhase,request));
            assertEquals(0,f.actual.nativeActionWrites(),"choice preparation never dispatches its SAVE");
        }
    }

    @Test void preparationKeepsTheOriginalReceivedFrameWhilePostsaveObservationConsumesTheNextFrame()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("received-before"),false)){
            var before=f.actual.ready();var transport=f.actual.physicalInputs().transport();
            var original=transport.currentSnapshot(Instant.now().plusSeconds(20));
            f.actual.enqueueSoftwareNativePacket(nextSnapshot(original,true));
            var prepared=RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),before.request(),"received-before-save");
            assertEquals(before.request().before(),prepared.saveCommand().before());
            assertEquals(before.request().before(),prepared.saveCommand().expected().before());
            assertArrayEquals(original.originalPacket(),transport.currentSnapshot(Instant.now().plusSeconds(20)).originalPacket(),
                    "preparation must not consume a later native occurrence");
            assertEquals(0,f.actual.nativeActionWrites());
            var after=f.actual.collector.checkpoint(f.request.lineageId()).observe(Instant.now().plusSeconds(60));
            assertTrue(after.observed().frame().identity().nativeRevision().compareTo(before.request().before().frame().identity().nativeRevision())>0,
                    "the independent observation still receives the next actual frame");
            assertThrows(RuntimeException.class,()->RootSaveCheckpointCommandProducer.prepareOriginalRequest(factory(f),before.request(),"stale-received-save"));
            assertEquals(0,f.actual.nativeActionWrites());
        }
    }
    @Test void preparationRefusesTheActualCurrentUnpausedFrameBeforeDispatch()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("received-unpaused"),false)){
            f.actual.ready();var transport=f.actual.physicalInputs().transport();
            f.actual.enqueueSoftwareNativePacket(nextSnapshot(transport.currentSnapshot(Instant.now().plusSeconds(20)),false));
            var unsafe=f.actual.collector.checkpoint(f.request.lineageId()).observe(Instant.now().plusSeconds(60));
            assertFalse(unsafe.paused());assertFalse(unsafe.saveEligible());
            assertThrows(RuntimeException.class,()->factory(f).prepare(unsafe.observed(),unsafe.source(),unsafe.sessionId(),
                    Optional.empty(),Instant.now().plusSeconds(60),"unpaused-received-save"));
            assertEquals(0,f.actual.nativeActionWrites());
        }
    }
    private static byte[] nextSnapshot(NativeObservationPort.ObservedFrame original,boolean paused)throws Exception {
        var snapshot=(NativeWire.Snapshot)NativeWire.decode(original.originalPacket());
        var node=StrictJson.object().put("type","state_snapshot").put("protocol_version",1)
                .put("snapshot_id",snapshot.snapshotId()+"-next").put("revision",snapshot.revision().add(java.math.BigInteger.ONE));
        var state=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.FullJsonTree.parse(
                snapshot.state().value(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        state.put("paused",paused);
        var membership=state.path("played_character").path("event_trait_membership");
        if(membership instanceof com.fasterxml.jackson.databind.node.ObjectNode object&&object.has("snapshot_revision"))
            object.put("snapshot_revision",snapshot.revision().add(java.math.BigInteger.ONE));
        node.set("state",state);
        return NativeWire.packet(org.xar.ck3.control.contracts.FullJsonTree.encode(node,
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES));
    }
    /** Existing qualified Root fixture hook inside its ordinary planning call, after physical freeze unwinds; missing admission is NOT_RUN. */
    public static ActionCommand actualRootBaseline(OrdinaryCorePolicy actualCore,RootRuntimeCommands sameCommands,
            RootRuntimeContext actualContext,PlanningRequest actualOriginal)throws Exception {
        var selected=assertInstanceOf(OrdinaryPolicy.Replace.class,actualCore.evaluate(actualOriginal,OrdinaryPolicy.Draft.empty()));
        assertEquals("baseline",selected.draft().phase());ActionCommand command=selected.draft().command().orElseThrow();
        assertTrue(RootSaveCheckpointCommandProducer.supports(command.operation()));
        assertSame(command,sameCommands.requireActualStrong(actualOriginal,command));
        assertEquals(actualContext.source(),command.source());assertEquals(actualContext.game().sessionId(),command.sessionId());
        assertEquals(actualContext.game().generation(),command.before().game());return command;
    }
    private static String reconciliationFailure(CheckpointSourceCompositionTest.Fixture fixture) {
        var failure=fixture.retainedReconciliationFailure.get();
        if(failure==null)return "none";
        var text=new java.io.StringWriter();
        failure.printStackTrace(new java.io.PrintWriter(text));
        return text.toString();
    }
    private static OpportunityJson.Obj obj(com.fasterxml.jackson.databind.JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"original checkpoint choice");}
}
