package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import static org.junit.jupiter.api.Assertions.*;

/** Real software Native/Driver/archive joins verify the production DATA coherence check.
 * This fixture grants no private restored Root or Managed Game source qualification. */
final class RootRestorePhysicalIdentityTest {
    @TempDir Path directory;
    private record Inputs(DriverBootstrap.Seed seed,String pipe,FullSnapshot full,DriverSnapshotFacts.Known known,Complete frame) { }
    @FunctionalInterface private interface DataWork {void run(Inputs actual)throws IOException;}

    @Test void differentSessionValueTypesJoinThroughActualAssemblerAndDriverSerde()throws Exception {
        withData("different-session-types",actual->{
            assertNotEquals(actual.known().driver().session(),actual.seed().expectedSession(),
                    "Driver and transport session records describe different fields");
            check(actual,actual.seed(),actual.pipe(),actual.frame());
            var original=actual.known();
            var decoded=DriverStateSnapshot.decodeComplete(original.driver().encode());
            var roundTrip=new DriverSnapshotFacts.Known(decoded,original.stamp(),original.originalHistoryBasis(),original.actionRows(),
                    original.auxiliary(),original.loop(),original.observation());
            RootRestoreAdapters.requireRestoredPhysicalIdentity(actual.seed(),actual.seed().expectedSession(),actual.pipe(),actual.full(),roundTrip,actual.frame());
            assertArrayEquals(original.driver().encode(),roundTrip.driver().encode());
        });
    }
    @Test void samePidDifferentBirthConnectionSessionOrMachineCannotReplaceTheActualOwner()throws Exception {
        withData("transport-identity",actual->{
            var transport=actual.seed().expectedSession();
            var otherBirth=new GameGeneration(transport.game().pid(),new PythonOnlyUInt64(transport.game().creationFiletime().value().add(BigInteger.ONE)));
            for(var foreign:java.util.List.of(
                    new TransportSession(transport.machineId(),otherBirth,transport.connectionGeneration(),transport.sessionId()),
                    new TransportSession(transport.machineId(),transport.game(),transport.connectionGeneration().add(BigInteger.ONE),transport.sessionId()),
                    new TransportSession(transport.machineId(),transport.game(),transport.connectionGeneration(),transport.sessionId()+"-foreign"),
                    new TransportSession(transport.machineId()+"-foreign",transport.game(),transport.connectionGeneration(),transport.sessionId()))) {
                var seed=copy(actual.seed(),foreign,actual.seed().driverVersion(),actual.seed().episodeEpoch());
                assertThrows(IllegalArgumentException.class,()->check(actual,seed,actual.pipe(),actual.frame()));
            }
        });
    }
    @Test void actualPipeEpochVersionActorAndEpisodeAreCheckedIndependently()throws Exception {
        withData("driver-owner",actual->{
            assertThrows(IllegalArgumentException.class,()->check(actual,actual.seed(),actual.pipe()+"-foreign",actual.frame()));
            for(var seed:java.util.List.of(
                    copy(actual.seed(),actual.seed().expectedSession(),actual.seed().driverVersion()+1,actual.seed().episodeEpoch()),
                    copy(actual.seed(),actual.seed().expectedSession(),actual.seed().driverVersion(),actual.seed().episodeEpoch()+1)))
                assertThrows(IllegalArgumentException.class,()->check(actual,seed,actual.pipe(),actual.frame()));
            var original=actual.frame().identity();var proposal=original.frame();var basic=proposal.identity();
            var foreignActor=new JointBudgetSelector.Frame(basic.player().add(BigInteger.ONE),basic.nativeRevision(),basic.dateRaw());
            for(var changed:java.util.List.of(
                    new JointBudgetSelector.ProposalFrame(foreignActor,proposal.snapshotId(),proposal.revision(),proposal.episodeRunId()),
                    new JointBudgetSelector.ProposalFrame(basic,proposal.snapshotId(),proposal.revision(),proposal.episodeRunId()+"-foreign"))) {
                var identity=new ObservationIdentity(original.machineId(),original.game(),changed,original.observationVersion());
                var frame=copy(actual.frame(),identity,actual.frame().fullBindingSha256());
                assertThrows(IllegalArgumentException.class,()->check(actual,actual.seed(),actual.pipe(),frame));
            }
        });
    }
    @Test void actualRawSnapshotAndFullSemanticBindingCannotBeSubstituted()throws Exception {
        withData("raw-full-binding",actual->{
            var original=actual.frame().identity();var proposal=original.frame();
            var changed=new JointBudgetSelector.ProposalFrame(proposal.identity(),proposal.snapshotId()+"-foreign",proposal.revision(),proposal.episodeRunId());
            var identity=new ObservationIdentity(original.machineId(),original.game(),changed,original.observationVersion());
            var hash=actual.frame().fullBindingSha256().equals("a".repeat(64))?"b".repeat(64):"a".repeat(64);
            for(var frame:java.util.List.of(copy(actual.frame(),identity,actual.frame().fullBindingSha256()),copy(actual.frame(),original,hash)))
                assertThrows(IllegalArgumentException.class,()->check(actual,actual.seed(),actual.pipe(),frame));
        });
    }
    @Test void laterReadPublicationKeepsCompleteDriverButMustMatchItsExactCurrentPacket()throws Exception {
        withData("restore-publication-occurrences",actual->{
            var base=actual.full().actual().nativeRevision();
            var second=publicationData(actual,base.add(BigInteger.ONE),"restore-read-two");
            var third=publicationData(actual,base.add(BigInteger.TWO),"restore-read-three");
            RootRestoreAdapters.requireCurrentPublicationData(second.published(),third.published(),third.candidate());
            assertThrows(IllegalArgumentException.class,()->RootRestoreAdapters.requireCurrentPublicationData(second.published(),second.published(),third.candidate()));
            var fourth=publicationData(actual,base.add(BigInteger.valueOf(3)),"unrelated-read-four");
            assertThrows(IllegalArgumentException.class,()->RootRestoreAdapters.requireCurrentPublicationData(second.published(),fourth.published(),third.candidate()));
            var original=third.published();
            var wrongEpoch=new RestoreCheckpointService.PublishedDriver(original.driver(),original.episodeEpoch()+1,
                    original.originalHistoryBasis(),original.readiness(),original.semantic());
            assertThrows(IllegalArgumentException.class,()->RootRestoreAdapters.requireCurrentPublicationData(second.published(),wrongEpoch,third.candidate()));
        });
    }
    /** Explicit occurrence DATA from real fixture Driver/raw fields; these records mint no receiver or RestoreBinding. */
    private record PublicationData(RestoreCheckpointService.PublishedDriver published,RestoreCheckpointService.NativeCandidate candidate) { }
    private static PublicationData publicationData(Inputs input,BigInteger revision,String snapshot)throws IOException {
        var original=input.full().actual();var old=input.frame().identity();var basic=old.frame().identity();
        var proposal=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(basic.player(),revision,basic.dateRaw()),
                snapshot,old.frame().revision(),old.frame().episodeRunId());
        var identity=new ObservationIdentity(old.machineId(),old.game(),proposal,old.observationVersion());
        var envelope=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(java.util.Arrays.copyOfRange(original.originalPacket(),4,original.originalPacket().length),DriverJson.MAX_NATIVE_BYTES);
        envelope.put("snapshot_id",snapshot).put("revision",revision);
        var player=envelope.path("state").path("played_character");
        if(player.isObject()&&player.has("event_trait_membership"))((com.fasterxml.jackson.databind.node.ObjectNode)player.get("event_trait_membership")).put("snapshot_revision",revision);
        byte[] packet=NativeWire.packet(FullJsonTree.encode(envelope,DriverJson.MAX_NATIVE_BYTES));
        var nativeRef=new ExactRef(input.full().originalEvidence().path()+"."+revision,packet.length,DriverJson.sha256(packet));
        var at=original.observedAt().plusMillis(revision.subtract(original.nativeRevision()).longValueExact());
        var raw=new NativeObservationPort.ObservedFrame(original.session(),snapshot,revision,new RawJson(FullJsonTree.encode(envelope.get("state"),DriverJson.MAX_NATIVE_BYTES)),packet,at);
        var semantic=new SessionPorts.SemanticEvidence(identity,input.seed().fullDriver(),nativeRef,input.seed().fullDriver(),input.seed().fullDriver(),at);
        var ready=new CheckpointRequest.Readiness(identity,input.frame().source(),original.session().sessionId(),"restore-publication-data",
                true,true,true,"DATA comparison only",nativeRef,at);
        var published=new RestoreCheckpointService.PublishedDriver(input.known().driver(),input.known().stamp().episodeEpoch(),input.known().originalHistoryBasis(),ready,semantic);
        return new PublicationData(published,new RestoreCheckpointService.NativeCandidate(raw,input.frame().source(),ready.lineageId(),nativeRef));
    }
    private void withData(String name,DataWork work)throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve(name),false)) {
            fixture.preserveInitialObservationData();
            fixture.ready();var physical=fixture.physicalInputs();
            fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->{
                var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());var facts=known.observation().orElseThrow();
                var raw=physical.transport().currentSnapshot(Instant.now().plusSeconds(20));
                var scoped=fixture.archive.withSession(same);var nativeRef=scoped.preserveNativeFrame(raw);
                var full=physical.observationAssembler().projectFull(raw,facts,nativeRef);
                var frame=assertInstanceOf(Complete.class,physical.observationAssembler().assemble(raw,facts,nativeRef));
                var driverRef=scoped.preserveMaterial(new RawJson(known.driver().encode()));
                var seed=new DriverBootstrap.Seed(driverRef,known.originalHistoryBasis(),known.stamp().driverVersion(),known.stamp().episodeEpoch(),
                        raw.session(),known.auxiliary(),known.loop());
                int reads=fixture.nativePacketReads(),writes=fixture.nativeActionWrites();String head=same.head().digest();
                work.run(new Inputs(seed,physical.transport().pipeName(),full,known,frame));
                assertEquals(reads,fixture.nativePacketReads());assertEquals(writes,fixture.nativeActionWrites());assertEquals(head,same.head().digest());
                return null;
            }));
        }
    }
    private static void check(Inputs actual,DriverBootstrap.Seed seed,String pipe,Complete frame) {
        RootRestoreAdapters.requireRestoredPhysicalIdentity(seed,seed.expectedSession(),pipe,actual.full(),actual.known(),frame);
    }
    private static DriverBootstrap.Seed copy(DriverBootstrap.Seed seed,TransportSession transport,long version,long epoch) {
        return new DriverBootstrap.Seed(seed.fullDriver(),seed.originalHistoryBasis(),version,epoch,transport,seed.auxiliary(),seed.loop());
    }
    private static Complete copy(Complete frame,ObservationIdentity identity,String binding) {
        return new Complete(identity,frame.source(),frame.sessionId(),frame.connectionGeneration(),frame.semantic(),frame.originalEvidence(),frame.observedAt(),binding);
    }
}
