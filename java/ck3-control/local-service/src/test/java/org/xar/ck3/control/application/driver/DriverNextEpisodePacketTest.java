package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Persisted source DATA is replayed by real codecs; it never mints private adoption or Game authority. */
final class DriverNextEpisodePacketTest {
    @TempDir Path temporary;
    private static final String STATE="""
        {"date_raw":53144328,"paused":true,"map_ready":true,"speed":3,"played_character":{"character_id":73,"alive":true},"active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"active_wars":[],"player_armies":[],"diagnostics":{},"lexical_metric":1.0}
        """.strip();
    private static final Instant OBSERVED=Instant.parse("2026-10-23T22:25:00.123456789Z");

    @Test void persistedOriginalManifestAndFramedPacketReplayTheSameFirstObservation() throws Exception {
        var original=frame();var fixture=fixture(original);
        Path manifest=temporary.resolve("manifest.json"),packet=temporary.resolve("first-packet.bin"),driver=temporary.resolve("driver.json");
        Files.write(manifest,fixture.manifest().bytes());Files.write(packet,original.originalPacket());Files.write(driver,fixture.driver().bytes());
        var stored=new RawJson(Files.readAllBytes(manifest));
        var replay=DriverObservationEvidenceReader.nativeFrame(fixture.reference(),stored,Files.readAllBytes(packet));
        DriverBootstrap.requireSameNextRaw(original,replay);
        var facts=DriverObservationEvidenceReader.decode(fixture.reference(),stored,new RawJson(Files.readAllBytes(driver)),replay);
        assertArrayEquals(original.state().bytes(),replay.state().bytes());
        assertTrue(new String(replay.state().bytes(),StandardCharsets.UTF_8).contains("\"lexical_metric\":1.0"));
        assertEquals(new BigInteger("134055108000000017"),facts.transport().game().creationFiletime().value());
        assertEquals(new BigInteger("18446744073709551615"),facts.transport().connectionGeneration());
        assertEquals(8,facts.episodeEpoch());assertEquals(OBSERVED,replay.observedAt());
    }

    @Test void crossingAnyOriginalPacketFieldIsRejectedEvenWhenJsonMeaningMatches() {
        var original=frame();var different=new ArrayList<ObservedFrame>();
        different.add(copy(new TransportSession("other-machine",original.session().game(),original.session().connectionGeneration(),original.session().sessionId()),original.snapshotId(),original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(new TransportSession(original.session().machineId(),new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000018"))),original.session().connectionGeneration(),original.session().sessionId()),original.snapshotId(),original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(new TransportSession(original.session().machineId(),original.session().game(),BigInteger.ONE,original.session().sessionId()),original.snapshotId(),original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(new TransportSession(original.session().machineId(),original.session().game(),original.session().connectionGeneration(),"other-session"),original.snapshotId(),original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(original.session(),"later-snapshot",original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(original.session(),original.snapshotId(),BigInteger.TEN,original.state(),original.originalPacket(),OBSERVED));
        different.add(copy(original.session(),original.snapshotId(),original.nativeRevision(),new RawJson(bytes(STATE.replace("1.0","1"))),original.originalPacket(),OBSERVED));
        byte[] changed=original.originalPacket();changed[changed.length-1]^=1;
        different.add(copy(original.session(),original.snapshotId(),original.nativeRevision(),original.state(),changed,OBSERVED));
        different.add(copy(original.session(),original.snapshotId(),original.nativeRevision(),original.state(),original.originalPacket(),OBSERVED.plusNanos(1)));
        for(var actual:different)assertThrows(IllegalArgumentException.class,()->DriverBootstrap.requireSameNextRaw(original,actual));
    }

    @Test void persistedManifestRejectsWrongFieldMissingNullBoolAndFloatRevisions() {
        var original=frame();var fixture=fixture(original);
        String wire=new String(fixture.manifest().bytes(),StandardCharsets.UTF_8);
        for(String invalid:List.of(wire.replace("\"native_revision\":9","\"native_revision\":true"),
                wire.replace("\"native_revision\":9","\"native_revision\":9.0"),
                wire.replace("\"native_revision\":9","\"native_revision\":null"),
                wire.replace("\"native_revision\":9,",""),wire.replace("\"native_revision\":9","\"native_revision_wrong\":9"))) {
            assertNotEquals(wire,invalid,"negative fixture must change the actual manifest");
            var raw=new RawJson(bytes(invalid));
            assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.nativeFrame(ref(raw.bytes()),raw,original.originalPacket()));
        }
    }

    @Test void callerArrayMutationCannotChangeRetainedFirstPacket() {
        var original=frame();byte[] caller=original.originalPacket();
        var retained=copy(original.session(),original.snapshotId(),original.nativeRevision(),original.state(),caller,OBSERVED);
        caller[caller.length-1]^=1;byte[] returned=retained.originalPacket();returned[0]^=1;
        assertDoesNotThrow(()->DriverBootstrap.requireSameNextRaw(original,retained));
    }

    private record Fixture(RawJson driver,RawJson manifest,ExactRef reference) { }
    private static Fixture fixture(ObservedFrame actual) {
        String json="""
            {"format_version":2,"pipe_name":"next-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"next-episode","last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
            """;
        var driver=DriverStateSnapshot.decodeComplete(bytes(json));var full=new RawJson(driver.encode());var reference=ref(full.bytes());
        var stamp=new DriverSnapshotFacts.Stamp(4,8,actual.session().game(),"next-episode",DriverJson.sha256(full.bytes()));
        var known=new DriverSnapshotFacts.Known(driver,stamp,reference,List.of(),new OpportunityJson.Obj(Map.of()),Optional.empty(),Optional.empty());
        var source=new G2Source(actual.session().machineId(),OBSERVED.toString(),"fixture-source-data-only",reference);
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(22),2,source,new OpportunityJson.Obj(Map.of()),reference);
        return new Fixture(full,manifest,ref(manifest.bytes()));
    }
    private static ObservedFrame frame() {
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134055108000000017")));
        var session=new TransportSession("fixture-machine",game,new BigInteger("18446744073709551615"),"next-session");
        byte[] payload=bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"first-snapshot\",\"revision\":9,\"state\":"+STATE+"}");
        byte[] framed=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        return new ObservedFrame(session,"first-snapshot",BigInteger.valueOf(9),new RawJson(bytes(STATE)),framed,OBSERVED);
    }
    private static ObservedFrame copy(TransportSession session,String snapshot,BigInteger revision,RawJson state,byte[] packet,Instant observed) {
        return new ObservedFrame(session,snapshot,revision,state,packet,observed);
    }
    private static ExactRef ref(byte[] raw) { return new ExactRef("fixture/"+DriverJson.sha256(raw),raw.length,DriverJson.sha256(raw)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
