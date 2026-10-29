package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real framed input/manifest/Driver/stamp -> sole independent verifier. A read-only test Head grants no runtime authority. */
final class NativeCampaignSemanticReplayTest {
    private record Originals(DriverObservationAssembler.Complete frame,SessionPorts.SemanticEvidence evidence,Map<ExactRef,byte[]> bytes) { }
    private static ExactRef ref(byte[] raw){return new ExactRef(Path.of("target","semantic-replay-fixture",DriverJson.sha256(raw)+".bin").toAbsolutePath().toString(),raw.length,DriverJson.sha256(raw));}
    private static Originals originals(String episode){return originals(episode,DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION);}
    private static Originals originals(String episode,long version){
        String raw=DriverObservationAssemblerTest.STATE.strip();
        raw=raw.substring(0,raw.length()-1)+episode+"}";
        raw=raw.replace("\"original\":\"retained\"","\"original\":\"retained\",\"bridge_pid\":42,\"connection_generation\":5");
        var actual=DriverObservationAssemblerTest.actual(raw);var base=DriverStateAssemblerTest.known();var old=base.driver();
        var driver=new DriverStateSnapshot.Complete(old.session(),old.commandHistory(),old.lastCheckpoint(),old.rollbackWarFailure(),
                old.managedRestoreTransaction(),old.successionExpectation(),new DriverStateSnapshot.NullValue(),old.campaignGoal(),old.rollbackWarFailures());
        var stamp=new DriverSnapshotFacts.Stamp(base.stamp().driverVersion(),base.stamp().episodeEpoch(),base.stamp().game(),
                base.stamp().episodeRunId(),DriverJson.sha256(driver.encode()));
        var auxiliary=new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign")));
        var known=new DriverSnapshotFacts.Known(driver,stamp,base.originalHistoryBasis(),base.actionRows(),auxiliary,base.loop(),Optional.empty());
        var driverRef=ref(driver.encode());
        var manifest=DriverObservationEvidenceReader.encode(known,actual,java.math.BigInteger.valueOf(2),
                version,DriverStateAssemblerTest.source(),auxiliary,driverRef);
        var manifestRef=ref(manifest.bytes());
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(driver.encode()),actual);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,ref(actual.originalPacket())));
        var observed=new DriverSnapshotFacts.Known(driver,stamp,base.originalHistoryBasis(),base.actionRows(),auxiliary,base.loop(),Optional.of(facts));
        byte[] semantic=DriverJson.encode(complete.semantic()),stampBytes=NativeDriverStamp.encode(complete,observed);
        var semanticRef=ref(semantic);var stampRef=ref(stampBytes);var nativeRef=ref(actual.originalPacket());
        var originals=new HashMap<ExactRef,byte[]>();originals.put(driverRef,driver.encode());originals.put(manifestRef,manifest.bytes());
        originals.put(semanticRef,semantic);originals.put(stampRef,stampBytes);originals.put(nativeRef,actual.originalPacket());
        return new Originals(complete,new SessionPorts.SemanticEvidence(complete.identity(),semanticRef,nativeRef,stampRef,driverRef,actual.observedAt()),originals);
    }

    @Test void originalMissingNullAndRetainedEpisodeFieldsReplayThroughTheSameManifestAndVerifier()throws IOException {
        for(String episode:List.of("",",\"episode_run_id\":null,\"succession_lifecycle\":null",
                ",\"episode_run_id\":\"original-native-run\",\"episode_character_id\":922,\"succession_lifecycle\":{\"retained\":true}")){
            var actual=originals(episode);var reads=new java.util.ArrayList<ExactRef>();var session=new ReadOnlyHead();
            var verifier=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
                assertSame(session,same);reads.add(reference);return actual.bytes().get(reference).clone();
            });
            var verified=verifier.verify(session,new SessionPorts.SessionIdentity(actual.frame().identity().machineId(),
                    actual.frame().identity().game(),actual.frame().sessionId()),actual.evidence());
            assertEquals(actual.frame().identity(),verified.frame());
            assertEquals(1,reads.stream().filter(actual.evidence().originalDriver()::equals).count(),"one actual read for identical original Driver ref");
            assertTrue(reads.contains(DriverObservationEvidenceReader.reference(actual.frame().semantic().get("java_driver_facts_evidence"))));
        }
    }

    @Test void forgedEpisodeFieldOrChangedManifestCannotPassByOnlyKeepingTheNativeCampaignMarker(){
        for(boolean manifest:List.of(true,false)){
            var actual=originals("");var altered=new HashMap<>(actual.bytes());var evidence=actual.evidence();
            if(manifest){
                var manifestRef=DriverObservationEvidenceReader.reference(actual.frame().semantic().get("java_driver_facts_evidence"));
                byte[] changed=altered.get(manifestRef).clone();changed[0]^=1;altered.put(manifestRef,changed);
            }else{
                var value=DriverJson.object(altered.get(evidence.semantic()),RawJson.MAXIMUM_BYTES)
                        .with("episode_run_id",new OpportunityJson.Text("invented-ordinary-run"));
                byte[] changed=DriverJson.encode(value);var changedRef=ref(changed);altered.put(changedRef,changed);
                evidence=new SessionPorts.SemanticEvidence(evidence.frame(),changedRef,evidence.originalNativePacket(),evidence.driverStamp(),evidence.originalDriver(),evidence.observedAt());
            }
            var verifier=new NativeSemanticEvidenceVerifier((same,reference,maximum)->altered.get(reference).clone());
            var original=evidence;
            assertThrows(IOException.class,()->verifier.verify(new ReadOnlyHead(),new SessionPorts.SessionIdentity(
                    actual.frame().identity().machineId(),actual.frame().identity().game(),actual.frame().sessionId()),original));
        }
    }

    @Test void distinctOriginalDriverRefStillReadsManifestDriverAndRejectsChangedBytes()throws IOException {
        for(boolean corrupt:List.of(false,true)){
            var actual=originals("");var old=actual.evidence();
            var alias=new ExactRef(Path.of("target","semantic-replay-fixture","distinct-original-driver.json").toAbsolutePath().toString(),old.originalDriver().bytes(),old.originalDriver().sha256());
            var refs=new java.util.ArrayList<ExactRef>();
            var evidence=new SessionPorts.SemanticEvidence(old.frame(),old.semantic(),old.originalNativePacket(),old.driverStamp(),alias,old.observedAt());
            var verifier=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
                refs.add(reference);byte[] bytes=actual.bytes().get(reference.equals(alias)?old.originalDriver():reference).clone();
                if(corrupt&&reference.equals(old.originalDriver()))bytes[0]^=1;
                return bytes;
            });
            var session=new ReadOnlyHead();var identity=new SessionPorts.SessionIdentity(actual.frame().identity().machineId(),actual.frame().identity().game(),actual.frame().sessionId());
            if(corrupt)assertThrows(IOException.class,()->verifier.verify(session,identity,evidence));
            else assertEquals(actual.frame().identity(),verifier.verify(session,identity,evidence).frame());
            assertEquals(1,refs.stream().filter(alias::equals).count());
            assertEquals(1,refs.stream().filter(old.originalDriver()::equals).count(),"different ref still requires its actual read/hash");
        }
    }
    @Test void canonicalVersionThreeStillReplaysWithoutAnUnusedFullProjection()throws IOException {
        var actual=originals("",DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION);
        assertTrue(actual.frame().originalProjection().isEmpty());
        var verifier=new NativeSemanticEvidenceVerifier((same,reference,maximum)->actual.bytes().get(reference).clone());
        assertEquals(actual.frame().identity(),verifier.verify(new ReadOnlyHead(),new SessionPorts.SessionIdentity(
                actual.frame().identity().machineId(),actual.frame().identity().game(),actual.frame().sessionId()),actual.evidence()).frame());
    }
    private static final class ReadOnlyHead implements ContinuityStorePort.Session {
        private final WriterContracts.Head head;
        ReadOnlyHead(){
            byte[] bytes=DriverStateAssemblerTest.bytes("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine\",\"sequence\":0,\"window_id\":1,\"start_date_raw\":0,\"target_date_raw\":24,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":0}");
            head=new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(bytes,65536),"test-machine"),List.of(),List.of(),List.of(),false);
        }
        @Override public WriterContracts.Head head(){return head;}
        @Override public void requireWriter(Path lock){throw new AssertionError("read-only DATA test grants no writer");}
        @Override public WriterContracts.Pin capturePin(ExactRef reference,int maximum){throw new AssertionError("read-only DATA test grants no pin");}
        @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("read-only DATA test grants no pin");}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("verifier cannot preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("verifier cannot commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("DATA test has no physical head");}
    }
}
