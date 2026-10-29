package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiPublicMetadata;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual software packet/manifest/assembler/public-context DATA chain. No Root, Native or gameplay grants. */
final class GuiNativeCampaignMetadataTest {
    private static final String MARKER = "xar_java_snapshot_projection";
    private static final Instant NOW = Instant.parse("2026-10-24T23:00:00Z");
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"fixture-pipe","bridge_pid":42,"episode_character_id":311,"episode_run_id":"private-fixture-stage",
         "last_checkpoint":null,"command_history":[{"index":1,"command":"original-query","ok":true,"result":{"metric":12.00}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"succession_lifecycle":null,
         "campaign_goal":{"original":"retained"},"rollback_war_failures":[]}
        """;
    private record Original(DriverObservationAssembler.Complete complete, RawJson snapshot, RawJson diagnostics) { }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] wire) {
        return new ExactRef("D:/fixture-data/gui-original", wire.length, DriverJson.sha256(wire));
    }
    private static RawJson raw(ObjectNode value) { return PublicDataJson.encodeFullMaterial(value); }
    private static Original original(String episodeFields) {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var auxiliary = new Obj(Map.of("episode_projection", new Text("native_campaign"),
                "original_auxiliary", new DecimalValue("-0.00")));
        var before = DriverFactsRepository.imported(ref(bytes(DRIVER)), bytes(DRIVER), 7, 3, game, auxiliary);
        String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,"
                + "\"played_character\":{\"character_id\":922,\"alive\":true},\"active_event\":null,"
                + "\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{}"
                + episodeFields + "}";
        byte[] body = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"actual-gui-fixture-read\",\"revision\":9,\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(body.length).put(body).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(
                "fixture-machine", game, BigInteger.valueOf(5), "fixture-session"),
                "actual-gui-fixture-read", BigInteger.valueOf(9), new RawJson(bytes(state)), packet, NOW);
        var projected = InitialDriverState.fixtureActorProjection(before, actual, before.auxiliary());
        var source = new G2Source("fixture-machine", NOW.toString(), "actual-gui-fixture-source",
                ref(bytes("original fixture sources")));
        var manifest = DriverObservationEvidenceReader.encode(projected, actual, BigInteger.valueOf(12),
                DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION, source,
                projected.auxiliary(), ref(projected.driver().encode()));
        var restored = DriverObservationEvidenceReader.nativeFrame(ref(manifest.bytes()), manifest, packet);
        var driver = RawJson.fullMaterial(projected.driver().encode());
        var facts = DriverObservationEvidenceReader.decode(ref(manifest.bytes()), manifest, driver, restored);
        var complete = assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(restored, facts, ref(packet)));
        var exported = DriverPublicContext.from(complete);
        return new Original(complete, exported.snapshot(), exported.diagnostics());
    }
    private static GuiModels.Context context(DriverObservationAssembler.Complete actual) {
        return new GuiModels.Context(actual.identity(), actual.source(), actual.sessionId(),
                actual.connectionGeneration(), GuiModels.Build.CROZIER4, NOW.plusSeconds(60));
    }
    private static RawJson bundle(Original actual) {
        return GuiPublicMetadata.beforeSource(actual.snapshot(), actual.diagnostics());
    }
    @Test void realProfileFourPublicContextUsesOriginalGetSemanticsAcrossGuiWrappers() {
        for (String fields : List.of("", ",\"episode_run_id\":null",
                ",\"episode_run_id\":\"original-native-episode\"")) {
            var actual = original(fields);
            var context = context(actual.complete());
            byte[] originalBytes = actual.snapshot().bytes();
            var source = bundle(actual);
            var snapshot = PublicDataJson.object(actual.snapshot());
            JsonNode expected = snapshot.has("episode_run_id") ? snapshot.get("episode_run_id") : NullNode.instance;
            assertEquals("private-fixture-stage", context.before().frame().episodeRunId());
            assertEquals(4, context.before().observationVersion());
            assertEquals(new Text("native_campaign"), PublicSnapshotCodec.decode(actual.snapshot()).get("episode_projection"));
            assertEquals(expected, GuiPublicMetadata.episodeRunId(context, source));
            for (ObjectNode result : List.of(
                    GuiPublicMetadata.queryFrame(StrictJson.object().put("original", true), context, source),
                    GuiPublicMetadata.decisionFrame(StrictJson.object(), context, source),
                    GuiPublicMetadata.readFrame(StrictJson.object(), context, source))) {
                assertTrue(result.has("episode_run_id"));
                assertEquals(expected, result.get("episode_run_id"));
                assertNotEquals("private-fixture-stage", result.get("episode_run_id").textValue());
                assertEquals(BigInteger.valueOf(12), result.get("queried_revision").bigIntegerValue());
                assertEquals(expected, PublicDataJson.object(raw(result)).get("episode_run_id"));
            }
            assertArrayEquals(originalBytes, actual.snapshot().bytes());
            assertEquals(!fields.isEmpty(), PublicDataJson.object(actual.snapshot()).has("episode_run_id"));
            var query = GuiPublicMetadata.queryFrame(StrictJson.object(), context, source);
            assertEquals("actual-gui-fixture-read", query.get("queried_snapshot_id").textValue());
            assertEquals(BigInteger.valueOf(9), query.get("queried_native_revision").bigIntegerValue());
            var read = GuiPublicMetadata.readFrame(StrictJson.object(), context, source);
            assertTrue(read.get("read_only").booleanValue());
            assertFalse(read.get("uses_mouse").booleanValue());
        }
    }
    @Test void actualProfileFourRejectsMissingMalformedAndCrossedSnapshotRepresentation() {
        var actual = original(",\"episode_run_id\":null");
        var context = context(actual.complete());
        var snapshot = PublicDataJson.object(actual.snapshot());
        var missing = snapshot.deepCopy(); missing.remove(MARKER);
        var malformed = snapshot.deepCopy();
        ((ObjectNode) malformed.get(MARKER)).put("observation_version", "4");
        var crossed = snapshot.deepCopy().put("snapshot_id", "another-original-frame");
        var wrongProfile = snapshot.deepCopy().put("episode_projection", "ordinary");
        for (ObjectNode wrong : List.of(missing, malformed, crossed, wrongProfile)) {
            RawJson bad = GuiPublicMetadata.beforeSource(raw(wrong), actual.diagnostics());
            assertThrows(IllegalArgumentException.class, () -> GuiPublicMetadata.queryFrame(StrictJson.object(), context, bad));
            assertThrows(IllegalArgumentException.class, () -> GuiPublicMetadata.decisionFrame(StrictJson.object(), context, bad));
            assertThrows(IllegalArgumentException.class, () -> GuiPublicMetadata.readFrame(StrictJson.object(), context, bad));
        }
        assertThrows(IllegalArgumentException.class,
                () -> GuiPublicMetadata.episodeRunId(context, actual.snapshot()));
    }
    @Test void ordinaryVersionsKeepTechnicalEpisodeAndCannotBorrowProfileFourMarker() {
        var actual = original("");
        var complete = actual.complete();
        var snapshot = StrictJson.object().put("snapshot_id", complete.identity().frame().snapshotId())
                .put("revision", complete.identity().frame().revision())
                .put("native_revision", complete.identity().frame().identity().nativeRevision());
        for (int version : List.of(1, 2, 3)) {
            var ordinary = new ObservationIdentity(complete.identity().machineId(), complete.identity().game(),
                    complete.identity().frame(), version);
            var context = new GuiModels.Context(ordinary, complete.source(), complete.sessionId(),
                    complete.connectionGeneration(), GuiModels.Build.CROZIER4, NOW.plusSeconds(60));
            var source = GuiPublicMetadata.beforeSource(raw(snapshot), actual.diagnostics());
            assertEquals("private-fixture-stage", GuiPublicMetadata.episodeRunId(context, source).textValue());
            assertEquals("private-fixture-stage", GuiPublicMetadata.queryFrame(StrictJson.object(), context, source)
                    .get("episode_run_id").textValue());
            assertEquals("private-fixture-stage", GuiPublicMetadata.decisionFrame(StrictJson.object(), context, source)
                    .get("episode_run_id").textValue());
            assertThrows(IllegalArgumentException.class,
                    () -> GuiPublicMetadata.episodeRunId(context, bundle(actual)));
        }
    }
}
