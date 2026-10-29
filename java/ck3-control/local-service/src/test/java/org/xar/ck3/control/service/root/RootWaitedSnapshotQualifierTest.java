package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Actual held WAIT/NGT/Driver/archive -> the qualifier's sole DATA verifier -> full export codec.
 * The fixture's explicitly controlled source proof is DATA, never a managed Root physical-source qualification. */
final class RootWaitedSnapshotQualifierTest {
    @TempDir Path directory;
    private record SourceData(ExactRef hello,ExactRef heartbeat,ExactRef source) { }
    private record Inputs(FullSnapshot full,ObservedFrame current,DriverObservationFacts facts,RawJson manifest,RawJson driver,
            SourceData source,DriverObservationAssembler assembler,ActionPorts.OutcomeArchive actualArchive) { }
    @FunctionalInterface private interface DataWork {void run(Inputs data)throws IOException;}

    @Test void alreadyWaitedOriginalRebuildsThroughActualDriverAndFullCodecWithoutAnotherNativeReadOrWriterEvent()throws Exception {
        withData("actual-wait",data->{
            FullSnapshot checked=verify(data,data.full(),data.current(),data.facts(),data.manifest(),data.driver());
            assertEquals(data.full().semantic(),checked.semantic());assertEquals(data.full().fullBindingSha256(),checked.fullBindingSha256());
            var originals=new PublicSnapshotCodec.FullSnapshotOriginals(checked,data.source().hello(),data.source().heartbeat(),data.source().source(),data.manifest(),data.driver());
            for(boolean history:List.of(true,false)) {
                var exported=PublicSnapshotCodec.exportFull(originals,history);
                assertEquals(exported.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(exported)));
                assertSame(originals,exported.originals());
            }
            assertEquals(0,RootWaitedSnapshotQualifier.Qualified.class.getConstructors().length,
                    "no public constructor may turn FullSnapshot DATA into a qualified current Root scope");
        });
    }
    @Test void anyCachedFramePacketConnectionRevisionTimeOrFullSemanticDriftRejectsTheCallerFullSnapshot()throws Exception {
        withData("frame-rejections",data->{
            var actual=data.current();byte[] changed=actual.originalPacket();changed[changed.length-1]^=1;
            var otherSession=new TransportSession(actual.session().machineId(),actual.session().game(),actual.session().connectionGeneration().add(BigInteger.ONE),actual.session().sessionId());
            List<ObservedFrame> changes=List.of(
                    new ObservedFrame(otherSession,actual.snapshotId(),actual.nativeRevision(),actual.state(),actual.originalPacket(),actual.observedAt()),
                    new ObservedFrame(actual.session(),actual.snapshotId()+"-changed",actual.nativeRevision(),actual.state(),actual.originalPacket(),actual.observedAt()),
                    new ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision().add(BigInteger.ONE),actual.state(),actual.originalPacket(),actual.observedAt()),
                    new ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),actual.state(),actual.originalPacket(),actual.observedAt().plusNanos(1)),
                    new ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),actual.state(),changed,actual.observedAt()),
                    new ObservedFrame(actual.session(),actual.snapshotId(),actual.nativeRevision(),raw("{}"),actual.originalPacket(),actual.observedAt()));
            for(var changedCurrent:changes)assertThrows(IOException.class,()->verify(data,data.full(),changedCurrent,data.facts(),data.manifest(),data.driver()));
            var full=data.full();var semantic=full.semantic().with("map_ready",new OpportunityJson.Bool(false));
            assertThrows(IOException.class,()->verify(data,new FullSnapshot(full.actual(),full.facts(),semantic,full.originalEvidence(),full.fullBindingSha256()),actual,data.facts(),data.manifest(),data.driver()));
            assertThrows(IOException.class,()->verify(data,new FullSnapshot(full.actual(),full.facts(),full.semantic(),full.originalEvidence(),"b".repeat(64)),actual,data.facts(),data.manifest(),data.driver()));
            var wrongReference=new ExactRef(full.originalEvidence().path(),full.originalEvidence().bytes()+1,full.originalEvidence().sha256());
            assertThrows(IOException.class,()->verify(data,new FullSnapshot(full.actual(),full.facts(),full.semantic(),wrongReference,full.fullBindingSha256()),actual,data.facts(),data.manifest(),data.driver()));
        });
    }
    @Test void authoritativeVersionManifestAndDriverAreRequiredAndCannotBeReplacedByCallerFacts()throws Exception {
        withData("facts-rejections",data->{
            var facts=data.facts();var changed=new DriverObservationFacts(facts.driver(),facts.driverVersion()+1,facts.episodeEpoch(),facts.transport(),facts.snapshotId(),facts.nativeRevision(),
                    facts.nativeStateSha256(),facts.publicRevision(),facts.observationVersion(),facts.source(),facts.originalSemanticFields(),facts.semanticFactsEvidence());
            assertThrows(IOException.class,()->verify(data,data.full(),data.current(),changed,data.manifest(),data.driver()));
            assertThrows(IOException.class,()->verify(data,data.full(),data.current(),facts,raw("{}"),data.driver()));
            assertThrows(IOException.class,()->verify(data,data.full(),data.current(),facts,data.manifest(),raw("{}")));
            var partial=new FullSnapshot(data.full().actual(),null,data.full().semantic(),data.full().originalEvidence(),data.full().fullBindingSha256());
            assertThrows(IOException.class,()->verify(data,partial,data.current(),facts,data.manifest(),data.driver()));
            assertThrows(IOException.class,()->verify(data,data.full(),data.current(),facts,null,data.driver()));
        });
    }
    @Test void nullPlayerTerminalFullDataNeverNeedsAnInventedCompleteOrSuccessorIdentity()throws Exception {
        withData("terminal-data",data->{
            var old=data.current();ObjectNode state=PublicDataJson.object(old.state());state.putNull("played_character");
            state.put("one_life_terminal",true).put("one_life_terminal_reason","controlled-terminal-data");
            var packet=PublicDataJson.object(raw(new String(Arrays.copyOfRange(old.originalPacket(),4,old.originalPacket().length),StandardCharsets.UTF_8)));
            packet.set("state",state);
            var terminal=new ObservedFrame(old.session(),old.snapshotId(),old.nativeRevision(),PublicDataJson.encode(state),NativeWire.packet(PublicDataJson.encode(packet).bytes()),old.observedAt());
            // Re-encode through the original shared producer for this explicit DATA boundary. No current Driver is replaced.
            var driverRef=DriverObservationEvidenceReader.currentDriverReference(data.facts().semanticFactsEvidence(),data.manifest());
            var known=DriverFactsRepository.imported(driverRef,data.driver().bytes(),data.facts().driverVersion(),data.facts().episodeEpoch(),terminal.session().game(),new OpportunityJson.Obj(java.util.Map.of()));
            RawJson manifest=DriverObservationEvidenceReader.encode(known,terminal,data.facts().publicRevision(),data.facts().observationVersion(),data.facts().source(),data.facts().originalSemanticFields(),driverRef);
            ExactRef manifestRef=data.actualArchive().preserveMaterial(manifest);
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,data.driver(),terminal);
            ExactRef original=data.actualArchive().preserveNativeFrame(terminal);
            FullSnapshot full=data.assembler().projectFull(terminal,facts,original);
            FullSnapshot checked=verify(data,full,terminal,facts,manifest,data.driver());
            assertInstanceOf(DriverObservationAssembler.Incomplete.class,data.assembler().assemble(terminal,facts,original));
            var originals=new PublicSnapshotCodec.FullSnapshotOriginals(checked,data.source().hello(),data.source().heartbeat(),data.source().source(),manifest,data.driver());
            var exported=PublicSnapshotCodec.exportFull(originals,true);var decoded=PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(exported));
            assertEquals(OpportunityJson.Nil.INSTANCE,decoded.get("played_character"));assertEquals(checked.semantic(),decoded);
        });
    }
    private void withData(String name,DataWork work)throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve(name),false)) {
            var ready=fixture.ready();var physical=fixture.physicalInputs();
            fixture.writer.locked(same->{
                var source=fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),
                        lease->new SourceData(lease.originalHello(),lease.originalHeartbeat(),lease.originalSourceQualification()));
                var held=new HeldDriverObservationPort(physical.transport(),fixture.driverAuthority(),actual->fixture.archive.withSession(same).preserveNativeFrame(actual),physical.observationAssembler(),8);
                int before=fixture.nativePacketReads();String head=same.head().digest();
                Instant wait=Instant.now().plusSeconds(20),capture=wait.plusSeconds(20);FullSnapshot actual;
                try{actual=held.waitForChangeFull(BigInteger.ZERO,wait,capture);}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                assertEquals(before,fixture.nativePacketReads(),"already-new WAIT must use the actual accepted cache without another Native read");
                fixture.driverAuthority().withFrozenFacts(same,frozen->{
                    var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());var facts=known.observation().orElseThrow();
                    var archive=fixture.archive.withSession(same);var manifest=archive.loadMaterial(facts.semanticFactsEvidence());
                    var driver=archive.loadMaterial(DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest));
                    var cached=physical.transport().currentSnapshot(capture);
                    work.run(new Inputs(actual,cached,facts,manifest,driver,source,physical.observationAssembler(),archive));return null;
                });
                assertEquals(before,fixture.nativePacketReads(),"qualifier DATA verification/export must not observe or read the Native stream");
                assertEquals(head,same.head().digest());assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    private static FullSnapshot verify(Inputs data,FullSnapshot supplied,ObservedFrame current,DriverObservationFacts facts,RawJson manifest,RawJson driver)throws IOException {
        return RootWaitedSnapshotQualifier.verifyData(supplied,current,facts,manifest,driver,data.assembler());
    }
    private static RawJson raw(String json){return new RawJson(json.getBytes(StandardCharsets.UTF_8));}
}
