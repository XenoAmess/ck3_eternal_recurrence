package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
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

/** Actual manifest encoder and disk/native codecs feed the public facts model; no private authority is minted. */
final class DriverSnapshotGameIdentityTest {
    @TempDir Path temporary;
    private static final BigInteger BIRTH=new BigInteger("134055108000000017");
    private static final Instant TIME=Instant.parse("2026-10-23T23:25:00.123456789Z");

    @Test void originalObservationSurvivesDiskReplayWithFullUnsignedProcessBirth() throws Exception {
        var original=fixture(new BigInteger("18446744073709551615"));
        var replay=persistAndReplay(original,"same");
        var accepted=withObservation(original.known(),replay);
        assertEquals(original.known().stamp().game(),accepted.observation().orElseThrow().transport().game());
        assertEquals("18446744073709551615",accepted.stamp().game().creationFiletime().value().toString());
        assertArrayEquals(original.known().driver().encode(),accepted.observation().orElseThrow().driver().encode());
        assertEquals(original.known().stamp().episodeEpoch(),accepted.observation().orElseThrow().episodeEpoch());
    }

    @Test void realOtherBirthManifestCannotBeAttachedToRetainedKnownWithSamePid() throws Exception {
        var retained=fixture(BIRTH);var anotherProcess=fixture(BIRTH.add(BigInteger.ONE));
        var replay=persistAndReplay(anotherProcess,"other-process");
        assertEquals(retained.known().stamp().game().pid(),replay.transport().game().pid());
        assertArrayEquals(retained.known().driver().encode(),replay.driver().encode());
        assertEquals(retained.known().stamp().driverVersion(),replay.driverVersion());
        assertEquals(retained.known().stamp().episodeEpoch(),replay.episodeEpoch());
        assertNotEquals(retained.known().stamp().game(),replay.transport().game());
        assertThrows(IllegalArgumentException.class,()->withObservation(retained.known(),replay));
        assertDoesNotThrow(()->withObservation(anotherProcess.known(),replay));
    }

    @Test void replayedFactsStillRequireOriginalVersionAndEpochWhileAbsentObservationStaysAbsent() throws Exception {
        var original=fixture(BIRTH);var replay=persistAndReplay(original,"version");
        var basis=original.known();var old=basis.stamp();
        for(var crossed:List.of(new DriverSnapshotFacts.Stamp(old.driverVersion()+1,old.episodeEpoch(),old.game(),old.episodeRunId(),old.driverSha256()),
                new DriverSnapshotFacts.Stamp(old.driverVersion(),old.episodeEpoch()+1,old.game(),old.episodeRunId(),old.driverSha256()))) {
            assertThrows(IllegalArgumentException.class,()->new DriverSnapshotFacts.Known(basis.driver(),crossed,basis.originalHistoryBasis(),
                    basis.actionRows(),basis.auxiliary(),basis.loop(),Optional.of(replay)));
        }
        assertTrue(basis.observation().isEmpty());
        assertTrue(new DriverSnapshotFacts.Known(basis.driver(),old,basis.originalHistoryBasis(),basis.actionRows(),basis.auxiliary(),basis.loop(),Optional.empty()).observation().isEmpty());
    }

    private record Fixture(DriverSnapshotFacts.Known known,ObservedFrame raw,RawJson manifest,ExactRef reference) { }
    private static Fixture fixture(BigInteger birth) {
        byte[] json=bytes("""
            {"format_version":2,"pipe_name":"core-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"identity-episode","last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
            """);
        var driver=DriverStateSnapshot.decodeComplete(json);var driverRef=ref(driver.encode());
        var game=new GameGeneration(42,new PythonOnlyUInt64(birth));
        var stamp=new DriverSnapshotFacts.Stamp(4,8,game,"identity-episode",DriverJson.sha256(driver.encode()));
        var known=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),new OpportunityJson.Obj(Map.of()),Optional.empty(),Optional.empty());
        String state="{\"date_raw\":53144328,\"paused\":true,\"map_ready\":true,\"speed\":3,\"played_character\":{\"character_id\":73,\"alive\":true}}";
        byte[] packet=bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"actual-core\",\"revision\":9,\"state\":"+state+"}");
        byte[] framed=ByteBuffer.allocate(packet.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(packet.length).put(packet).array();
        var raw=new ObservedFrame(new TransportSession("fixture-machine",game,BigInteger.valueOf(2),"identity-session"),"actual-core",BigInteger.valueOf(9),new RawJson(bytes(state)),framed,TIME);
        var source=new G2Source("fixture-machine",TIME.toString(),"identity-fixture-data-only",driverRef);
        var manifest=DriverObservationEvidenceReader.encode(known,raw,BigInteger.valueOf(22),2,source,new OpportunityJson.Obj(Map.of()),driverRef);
        return new Fixture(known,raw,manifest,ref(manifest.bytes()));
    }
    private DriverObservationFacts persistAndReplay(Fixture fixture,String prefix) throws Exception {
        Path manifest=temporary.resolve(prefix+"-manifest.json"),driver=temporary.resolve(prefix+"-driver.json"),packet=temporary.resolve(prefix+"-native.bin");
        Files.write(manifest,fixture.manifest().bytes());Files.write(driver,fixture.known().driver().encode());Files.write(packet,fixture.raw().originalPacket());
        var saved=new RawJson(Files.readAllBytes(manifest));
        var raw=DriverObservationEvidenceReader.nativeFrame(fixture.reference(),saved,Files.readAllBytes(packet));
        return DriverObservationEvidenceReader.decode(fixture.reference(),saved,new RawJson(Files.readAllBytes(driver)),raw);
    }
    private static DriverSnapshotFacts.Known withObservation(DriverSnapshotFacts.Known basis,DriverObservationFacts observation) {
        return new DriverSnapshotFacts.Known(basis.driver(),basis.stamp(),basis.originalHistoryBasis(),basis.actionRows(),basis.auxiliary(),basis.loop(),Optional.of(observation));
    }
    private static ExactRef ref(byte[] raw) {return new ExactRef("fixture/"+DriverJson.sha256(raw),raw.length,DriverJson.sha256(raw));}
    private static byte[] bytes(String text) {return text.getBytes(StandardCharsets.UTF_8);}
}
