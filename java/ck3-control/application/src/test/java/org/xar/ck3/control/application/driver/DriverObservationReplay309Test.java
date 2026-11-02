package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Incomplete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverFactsRepository;

public class DriverObservationReplay309Test {

    private static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;

    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"},"original_metric":1.00}
        """;

    private static byte[] bytes(String text) {
        return text.getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }

    private static ExactRef ref(byte[] raw) {
        return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw));
    }

    private static GameGeneration game() {
        return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    }

    private static Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of()));
    }

    private static G2Source source() {
        return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source")));
    }

    private static byte[] packet(String state) {
        String json = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}";
        byte[] jsonBytes = bytes(json);
        ByteBuffer buffer = ByteBuffer.allocate(jsonBytes.length + 4).order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(jsonBytes.length);
        buffer.put(jsonBytes);
        return buffer.array();
    }

    private static NativeObservationPort.ObservedFrame actual(String state) {
        var session = new NativeObservationPort.TransportSession("test-machine", game(), BigInteger.valueOf(5), "held-session");
        var rawState = new RawJson(bytes(state.strip()));
        var framed = packet(state);
        return new NativeObservationPort.ObservedFrame(session, "snapshot-9", BigInteger.valueOf(9), rawState, framed, Instant.parse("2026-10-23T16:00:00Z"));
    }

    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual) {
        var k = known();
        return new DriverObservationFacts(k.driver(), 3, 7, actual.session(), actual.snapshotId(), actual.nativeRevision(),
                DriverJson.sha256(actual.state().bytes()), BigInteger.valueOf(2), 1, source(),
                new OpportunityJson.Obj(Map.of()), ref(bytes("actual-facts")));
    }

    @Test
    public void testReplayOriginalsMatchesPublicPathAndPreservesOwnership() {
        var actual = actual(STATE);
        var k = known();
        var driverBytes = k.driver().encode();
        var driverRef = ref(driverBytes);
        var manifest = DriverObservationEvidenceReader.encode(k, actual, BigInteger.valueOf(2), 1, source(), new OpportunityJson.Obj(Map.of()), driverRef);
        var manifestRef = ref(manifest.bytes());
        var fullDriver = new RawJson(driverBytes);
        var framedNative = actual.originalPacket();
        var nativeRef = ref(framedNative);

        // Old public path
        var oldFrame = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, framedNative);
        assertArrayEquals(actual.state().bytes(), oldFrame.state().bytes());
        var oldFacts = DriverObservationEvidenceReader.decode(manifestRef, manifest, fullDriver, oldFrame);
        var oldResult = new DriverObservationAssembler().assemble(oldFrame, oldFacts, nativeRef);
        assertInstanceOf(Complete.class, oldResult);
        var oldComplete = (Complete) oldResult;

        // New replay path
        var newResult = DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, fullDriver, framedNative, nativeRef);
        assertInstanceOf(Complete.class, newResult);
        var newComplete = (Complete) newResult;

        // Compare fields
        assertEquals(oldComplete.identity(), newComplete.identity());
        assertEquals(oldComplete.source(), newComplete.source());
        assertEquals(oldComplete.sessionId(), newComplete.sessionId());
        assertEquals(oldComplete.connectionGeneration(), newComplete.connectionGeneration());
        assertEquals(oldComplete.semantic(), newComplete.semantic());
        assertEquals(oldComplete.originalEvidence(), newComplete.originalEvidence());
        assertEquals(oldComplete.observedAt(), newComplete.observedAt());
        assertEquals(oldComplete.fullBindingSha256(), newComplete.fullBindingSha256());
        assertEquals(oldComplete.originalProjection(), newComplete.originalProjection());

        // Verify lexical preservation of 1.00 in semantic
        var semantic = newComplete.semantic();
        var originalMetric = semantic.get("original_metric");
        assertInstanceOf(OpportunityJson.DecimalValue.class, originalMetric);
        assertEquals("1.00", ((OpportunityJson.DecimalValue) originalMetric).token());

        // Verify command history preservation
        var history = semantic.get("native_command_history");
        assertInstanceOf(OpportunityJson.Arr.class, history);
        assertEquals(2, ((OpportunityJson.Arr) history).items().size());

        // Verify manifest-ref semantic binding
        var manifestRefInSemantic = semantic.get("java_driver_facts_evidence");
        assertInstanceOf(OpportunityJson.Obj.class, manifestRefInSemantic);
        assertEquals(manifestRef, DriverObservationEvidenceReader.reference((OpportunityJson.Obj) manifestRefInSemantic));

        // Verify large creation FILETIME
        assertEquals(new BigInteger("9007199254740993"), newComplete.identity().game().creationFiletime().value());

        // Mutate the actual caller input after return; compare the entire captured DATA result.
        byte[] semanticBeforeMutation = DriverJson.encode(newComplete.semantic());
        framedNative[0] ^= 1;
        assertEquals(oldComplete, newComplete);
        assertArrayEquals(semanticBeforeMutation, DriverJson.encode(newComplete.semantic()));
        assertEquals(nativeRef, newComplete.originalEvidence());
    }

    @Test
    public void testReplayOriginalsRejectsInvalidManifestsAndData() {
        var actual = actual(STATE);
        var k = known();
        var driverBytes = k.driver().encode();
        var driverRef = ref(driverBytes);
        var manifest = DriverObservationEvidenceReader.encode(k, actual, BigInteger.valueOf(2), 1, source(), new OpportunityJson.Obj(Map.of()), driverRef);
        var manifestRef = ref(manifest.bytes());
        var fullDriver = new RawJson(driverBytes);
        var framedNative = actual.originalPacket();
        var nativeRef = ref(framedNative);

        // 1. Wrong manifest SHA
        var wrongManifestRef = new ExactRef("memory/test-original.json", manifest.bytes().length, "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(wrongManifestRef, manifest, fullDriver, framedNative, nativeRef));

        // 2. Changed Driver bytes vs manifest
        var changedDriver = new RawJson(bytes(new String(driverBytes, java.nio.charset.StandardCharsets.UTF_8).replace("campaign-original", "changed-campaign")));
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, changedDriver, framedNative, nativeRef));

        // 3. Changed framed native bytes
        var changedPacket = framedNative.clone();
        changedPacket[changedPacket.length - 2] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, fullDriver, changedPacket, nativeRef));

        // 4. Inconsistent transport PID vs full Driver (modify manifest transport pid to 43)
        var manifestObj = DriverJson.object(manifest.bytes(), DriverJson.MAX_NATIVE_BYTES);
        var transport = (OpportunityJson.Obj) manifestObj.get("transport");
        var modifiedTransport = transport.with("pid", new OpportunityJson.IntegerValue(BigInteger.valueOf(43)));
        var modifiedManifestObj = manifestObj.with("transport", modifiedTransport);
        var modifiedManifestBytes = DriverJson.encode(modifiedManifestObj);
        var modifiedManifestRef = ref(modifiedManifestBytes);
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(modifiedManifestRef, new RawJson(modifiedManifestBytes), fullDriver, framedNative, nativeRef));

        // 5. Unexpected MANIFEST field
        var unexpectedFieldManifestObj = manifestObj.with("unexpected", new OpportunityJson.IntegerValue(BigInteger.ONE));
        var unexpectedFieldManifestBytes = DriverJson.encode(unexpectedFieldManifestObj);
        var unexpectedFieldManifestRef = ref(unexpectedFieldManifestBytes);
        assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(unexpectedFieldManifestRef, new RawJson(unexpectedFieldManifestBytes), fullDriver, framedNative, nativeRef));

        // 6. Bad nativeRef (wrong evidence) -> Incomplete from assemble
        var badNativeRef = ref(bytes("bad-evidence"));
        var result = DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, fullDriver, framedNative, badNativeRef);
        assertInstanceOf(Incomplete.class, result);
    }
}