package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
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
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public archived semantic replay only: map-backed originals and a read-only Head grant no live permission. */
final class SemanticDriverReuse366Test {
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained","bridge_pid":42,"connection_generation":5}}
        """;
    private record Originals(DriverObservationAssembler.Complete frame, SessionPorts.SemanticEvidence evidence,
            Map<ExactRef,byte[]> bytes, DriverStateSnapshot.Complete driver,
            RawJson manifest, ExactRef manifestRef, NativeObservationPort.ObservedFrame nativeFrame) { }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) {
        return new ExactRef(Path.of("target","semantic-driver366",DriverJson.sha256(raw)+".bin").toAbsolutePath().toString(),
                raw.length,DriverJson.sha256(raw));
    }
    private static Originals originals(long version,boolean wide) {
        String driverText=wide?DRIVER.replace("\"last_checkpoint\":null","\"last_checkpoint\":{\"opaque\":"+"7".repeat(4301)+"}"):DRIVER;
        var driver=DriverStateSnapshot.decodeComplete(bytes(driverText));
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        String state=STATE.strip();
        byte[] payload=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",game,BigInteger.valueOf(5),"held-session"),
                "snapshot-9",BigInteger.valueOf(9),new RawJson(bytes(state)),packet,Instant.parse("2026-10-23T16:00:00Z"));
        var stamp=new DriverSnapshotFacts.Stamp(3,7,game,driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
        var auxiliary=new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign")));
        var driverRef=ref(driver.encode());
        var known=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.empty());
        var source=new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source")));
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),version,source,auxiliary,driverRef);
        var manifestRef=ref(manifest.bytes());
        // The old public raw path constructs the independent original observation DATA, including wide material.
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(driver.encode()),actual);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,ref(packet)));
        var observed=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.of(facts));
        byte[] semantic=DriverJson.encode(complete.semantic()),stampBytes=NativeDriverStamp.encode(complete,observed);
        var semanticRef=ref(semantic);var stampRef=ref(stampBytes);var nativeRef=ref(packet);
        var originals=new HashMap<ExactRef,byte[]>();originals.put(driverRef,driver.encode());originals.put(manifestRef,manifest.bytes());
        originals.put(semanticRef,semantic);originals.put(stampRef,stampBytes);originals.put(nativeRef,packet);
        return new Originals(complete,new SessionPorts.SemanticEvidence(complete.identity(),semanticRef,nativeRef,stampRef,driverRef,actual.observedAt()),
                originals,driver,manifest,manifestRef,actual);
    }
    private static SessionPorts.SessionIdentity owner(Originals actual) {
        return new SessionPorts.SessionIdentity(actual.frame().identity().machineId(),actual.frame().identity().game(),actual.frame().sessionId());
    }

    @Test void sameCallCanonicalReplayKeepsWideMaterialAndDistinctOriginalReads() throws IOException {
        for(long version:List.of(DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION,DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)) {
            for(boolean wide:List.of(false,true)) {
                var actual=originals(version,wide);
                if(wide)assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.decodeTypedDriver(
                        actual.manifestRef(),actual.manifest(),actual.driver(),actual.nativeFrame()),"existing typed helper has a narrower numeric profile");
                for(boolean distinct:List.of(false,true)) {
                    var original=actual.evidence();
                    var originalDriver=distinct?new ExactRef(Path.of("target","semantic-driver366","distinct-driver.json").toAbsolutePath().toString(),
                            original.originalDriver().bytes(),original.originalDriver().sha256()):original.originalDriver();
                    var evidence=new SessionPorts.SemanticEvidence(original.frame(),original.semantic(),original.originalNativePacket(),original.driverStamp(),originalDriver,original.observedAt());
                    var reads=new ArrayList<ExactRef>();var same=new ReadOnlyHead();
                    var verifier=new NativeSemanticEvidenceVerifier((borrowed,reference,maximum)->{
                        assertSame(same,borrowed);reads.add(reference);
                        return actual.bytes().get(reference.equals(originalDriver)?original.originalDriver():reference).clone();
                    });
                    var verified=verifier.verify(same,owner(actual),evidence);
                    assertEquals(actual.frame().identity(),verified.frame());assertEquals(actual.frame().observedAt(),verified.observedAt());
                    assertEquals(1,reads.stream().filter(originalDriver::equals).count());
                    assertEquals(1,reads.stream().filter(actual.manifestRef()::equals).count());
                    assertEquals(1,reads.stream().filter(original.originalDriver()::equals).count(),"different ref still has its real manifest Driver read");
                    assertEquals(distinct?6:5,reads.size(),"all five original reads plus any distinct Driver original remain");
                }
            }
        }
    }

    @Test void archiveMutationAndFailuresCannotReuseStaleDriverOrAuthority() throws IOException {
        var actual=originals(DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,false);
        byte[] borrowedDriver=actual.bytes().get(actual.evidence().originalDriver()).clone();
        boolean[] changed={false};
        var mutating=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef())) { borrowedDriver[0]='!';changed[0]=true; }
            return reference.equals(actual.evidence().originalDriver())?borrowedDriver:actual.bytes().get(reference).clone();
        });
        assertThrows(IOException.class,()->mutating.verify(new ReadOnlyHead(),owner(actual),actual.evidence()));
        assertTrue(changed[0],"the later manifest callback actually changed the previously decoded borrowed bytes");

        var marker=new IOException("actual manifest original I/O marker");
        var unavailable=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef()))throw marker;
            return actual.bytes().get(reference).clone();
        });
        assertSame(marker,assertThrows(IOException.class,()->unavailable.verify(new ReadOnlyHead(),owner(actual),actual.evidence())));

        var changedHead=new ReadOnlyHead();
        var drifting=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            if(reference.equals(actual.manifestRef()))changedHead.changed=true;
            return actual.bytes().get(reference).clone();
        });
        var drift=assertThrows(IOException.class,()->drifting.verify(changedHead,owner(actual),actual.evidence()));
        assertTrue(drift.getMessage().contains("writer changed during same-lock semantic verification"));

        var badManifest=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{
            byte[] raw=actual.bytes().get(reference).clone();if(reference.equals(actual.manifestRef()))raw[0]^=1;return raw;
        });
        assertThrows(IOException.class,()->badManifest.verify(new ReadOnlyHead(),owner(actual),actual.evidence()));
    }
    private static final class ReadOnlyHead implements ContinuityStorePort.Session {
        private final WriterContracts.Head head=head(0),next=head(1);boolean changed;
        private static WriterContracts.Head head(int sequence) {
            byte[] raw=bytes("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine\",\"sequence\":"+sequence+",\"window_id\":1,\"start_date_raw\":0,\"target_date_raw\":24,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":0}");
            return new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(raw,65536),"test-machine"),List.of(),List.of(),List.of(),false);
        }
        @Override public WriterContracts.Head head(){return changed?next:head;}
        @Override public void requireWriter(Path lock){throw new AssertionError("DATA test grants no writer");}
        @Override public WriterContracts.Pin capturePin(ExactRef reference,int maximum){throw new AssertionError("DATA test grants no pin");}
        @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("DATA test grants no pin");}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("verifier cannot preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("verifier cannot commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("DATA test has no physical head");}
    }
}
