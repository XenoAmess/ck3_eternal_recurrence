package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual complete Native snapshot bytes. Transport and ordinary lifecycle configuration are Java seams. */
final class SwayNativeWholeSnapshotDataTest {
    @Test void actualWholeSnapshotRetainsStressSentinelAsIncompleteAfterFullDriverAndManifestDecode() throws Exception {
        byte[] original=actualSnapshot();byte[] framed=actualFrame();assertArrayEquals(NativeWire.packet(original),framed);
        var decoded=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(framed));
        var game=new GameGeneration(73,new PythonOnlyUInt64(new BigInteger("134370000000000074")));
        var transport=new NativeObservationPort.TransportSession("xenoamess-full-tower-eb9d2c1186",game,BigInteger.ONE,"software-native-whole-snapshot-session");
        var actual=new NativeObservationPort.ObservedFrame(transport,decoded.snapshotId(),decoded.revision(),new RawJson(decoded.state().value()),framed,Instant.parse("2026-10-30T00:00:00Z"));
        assertEquals(-2,DriverObservationAssembler.originalNativeState(actual).get("played_character") instanceof OpportunityJson.Obj player
                ?OpportunityJson.integer(player.get("character_id"),"character_id").longValueExact():Long.MAX_VALUE);
        // Ordinary lifecycle configuration is explicit Java business DATA, with no source/environment qualification.
        ObjectNode lifecycle=StrictJson.object();lifecycle.put("schema","xar.ck3.succession-lifecycle-binding/v1");lifecycle.put("lifecycle","ordinary_campaign_succession");
        lifecycle.putNull("xar_enabled");lifecycle.put("pact_contract","software_owned_fixture_no_pact");lifecycle.put("source","software_owned_fixture");lifecycle.putNull("environment_sha256");
        var policy=InitialEpisodePolicy.ordinary(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,new RawJson(StrictJson.canonical(lifecycle)));
        var produced=InitialDriverState.create(actual,"software-owned-pipe-metadata","software-owned-whole-snapshot-episode",policy);
        var driver=produced.driver();assertEquals(BigInteger.valueOf(-2),driver.session().actorId());assertEquals(0,driver.commandHistory().size());
        byte[] full=driver.encode();assertArrayEquals(full,DriverStateSnapshot.decodeComplete(full).encode());
        var ref=ref("software:whole-native-snapshot-driver",full);var sourceRef=ref("software:whole-native-snapshot-original",framed);
        var source=new G2Source(transport.machineId(),actual.observedAt().toString(),"1.20.0.4",sourceRef);
        var stamp=new DriverSnapshotFacts.Stamp(0,0,game,driver.session().episodeRunId(),ActionCodec.sha256(full));
        var known=new DriverSnapshotFacts.Known(driver,stamp,ref,List.of(),produced.auxiliary(),Optional.empty(),Optional.empty());
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(9),DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION,source,produced.auxiliary(),ref);
        var facts=DriverObservationEvidenceReader.decode(ref("software:whole-native-snapshot-manifest",manifest.bytes()),manifest,new RawJson(full),actual);
        assertArrayEquals(full,facts.driver().encode());assertEquals(actual.snapshotId(),facts.snapshotId());assertEquals(ActionCodec.sha256(actual.state().bytes()),facts.nativeStateSha256());
        assertFalse(policy.optionalEnvironment().isPresent());assertFalse(policy.optionalSource().isPresent());
        // Assembly/canonical context require their complete actual extras. No missing Native field or HELLO diagnostic is filled here.
        var assembled=new DriverObservationAssembler().assemble(actual,facts,sourceRef);
        var incomplete=assertInstanceOf(DriverObservationAssembler.Incomplete.class,assembled);
        assertEquals(List.of("native_driver_fact_join: original stress_points must be a nonnegative integer token, not bool/float/string"),incomplete.reasons());
        JsonNode nativeState=StrictJson.parse(decoded.state().value());assertEquals(-1,nativeState.at("/played_character/stress_points").intValue());
    }
    private static byte[] actualSnapshot() throws Exception {
        try(var in=SwayNativeWholeSnapshotDataTest.class.getResourceAsStream("/sway/m6-native-current4-full-snapshot.json")) {
            assertNotNull(in,"mandatory actual Native StateSnapshotFrame original; do not substitute a hand-authored snapshot");
            JsonNode row=StrictJson.parse(in.readAllBytes());byte[] original=row.get("original_utf8").textValue().getBytes(StandardCharsets.UTF_8);
            assertEquals(row.get("sha256").textValue(),ActionCodec.sha256(original));return original;
        }
    }
    private static byte[] actualFrame() throws Exception {
        try(var in=SwayNativeWholeSnapshotDataTest.class.getResourceAsStream("/sway/m6-native-current4-full-snapshot.json")) {
            assertNotNull(in);JsonNode row=StrictJson.parse(in.readAllBytes());byte[] frame=java.util.Base64.getDecoder().decode(row.get("frame_base64").textValue());
            assertEquals(row.get("frame_sha256").textValue(),ActionCodec.sha256(frame));return frame;
        }
    }
    private static ExactRef ref(String name,byte[] value){return new ExactRef(name,value.length,ActionCodec.sha256(value));}
}
