package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.observation.ObservationReuse;

/** New Java signed-domain regressions over the committed native-normalizer producer input.
 * Negative cases are not old Python-oracle parity, physical observation or action qualification.
 */
final class WarObservationNativeActorTest {
    private static final String RESOURCE = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
    private static final int CORPUS_MAX_BYTES = 2 * 1024 * 1024;

    @Test void nativeSnapshotFrameAndActualProjectorPreserveSignedIdentityThroughJson() throws IOException {
        var projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        for (int actor : new int[] {Integer.MIN_VALUE, -2_000_000_000, -2, 0, 1, Integer.MAX_VALUE}) {
            ObjectNode request = input(actor);
            ObjectNode snapshot = object(request, "snapshot");
            WarObservationFrame frame = WarObservationFrame.fromSnapshot(snapshot);
            assertEquals(actor, frame.playedCharacterId());
            JsonNode encoded = StrictJson.parse(StrictJson.canonical(frame.toJson()));
            assertTrue(encoded.path("played_character_id").isIntegralNumber());
            assertEquals(actor, NativeCharacterId.fromJson(encoded.get("played_character_id")).value());
            JsonNode restoredSnapshot = StrictJson.parse(StrictJson.canonical(snapshot));
            assertEquals(frame, WarObservationFrame.fromSnapshot(restoredSnapshot));

            // The specific campaign-root query still requires its own positive actor inputs.
            // Its genuinely unavailable result makes this observation UNKNOWN, never Ready.
            request.set("campaign_root", StrictJson.object().put("status", "unavailable"));
            byte[] coldRequest = StrictJson.canonical(StrictJson.parse(StrictJson.canonical(request)));
            byte[] resultBytes = projector.project(coldRequest);
            JsonNode result = StrictJson.parse(resultBytes);
            assertEquals("unknown", result.path("status").textValue());
            assertEquals("exact_build_campaign_root_not_observed", result.path("reason").textValue());
            assertEquals(BigInteger.valueOf(actor), result.path("source_frame").path("played_character_id").bigIntegerValue());
            assertTrue(result.path("source_frame").path("played_character_id").isIntegralNumber());
            assertFalse(result.path("actual_effects_verified").booleanValue());
            assertFalse(result.path("material_terms_complete").booleanValue());
            assertFalse(result.path("automatic_surrender_qualified").booleanValue());
            assertTrue(result.path("continue_legal_war_processing").booleanValue());
            assertTrue(result.path("selected_action").isNull());
            assertArrayEquals(resultBytes, projector.project(coldRequest));
        }
    }

    @Test void actualScopedConsumerPreservesNegativeUnknownAndRejectsDifferentSignedActor() throws IOException {
        ObjectNode request = input(-2);
        request.set("campaign_root", StrictJson.object().put("status", "unavailable"));
        var frame = WarObservationFrame.fromSnapshot(request.get("snapshot"));
        var source = ObservationContext.fromJson(request.get("observation_context"));
        var owner = new ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult>("war-actor-test", 8);
        var version = new ObservationReuse.WriterVersion("war-actor-test", BigInteger.ONE);
        var token = owner.bindFresh(new ObservationReuse.Scope<>(source, frame, version));
        var projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        var consumer = new ScopedWarOutcomeStakesProjector(projector, owner);
        byte[] captured = StrictJson.canonical(request);
        var actual = consumer.project(token, captured);
        assertInstanceOf(ObservationReuse.Unknown.class, actual.outcome());
        assertEquals(-2, actual.outcome().value().frame().playedCharacterId());
        assertArrayEquals(projector.project(captured), actual.outcome().value().toCanonicalBytes());
        assertEquals(0, owner.retainedEntryCount());
        assertThrows(IllegalStateException.class, () -> consumer.project(token, captured));

        var driftOwner = new ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult>("war-actor-drift", 8);
        var driftToken = driftOwner.bindFresh(new ObservationReuse.Scope<>(source, frame,
            new ObservationReuse.WriterVersion("war-actor-drift", BigInteger.ONE)));
        var driftConsumer = new ScopedWarOutcomeStakesProjector(projector, driftOwner);
        object(object(request, "snapshot"), "played_character").put("character_id", -3);
        assertThrows(ContractViolationException.class, () -> driftConsumer.project(driftToken, StrictJson.canonical(request)));
        assertEquals(ObservationReuse.Invalidation.FRAME_CHANGED, driftOwner.lastInvalidation());
        assertThrows(IllegalStateException.class, () -> driftOwner.requireCurrent(driftToken));
        assertEquals(0, driftOwner.retainedEntryCount());
    }

    @Test void absentSentinelWrongTokensOverflowAndUnsignedAliasesAreRejectedAtBothEntrypoints() throws IOException {
        var projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        List<JsonNode> wrong = List.of(IntNode.valueOf(-1), BooleanNode.TRUE, BooleanNode.FALSE,
            DoubleNode.valueOf(-2.0), TextNode.valueOf("-2"), NullNode.getInstance(),
            BigIntegerNode.valueOf(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
            BigIntegerNode.valueOf(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),
            BigIntegerNode.valueOf(new BigInteger("4294967294")), StrictJson.object());
        for (JsonNode actor : wrong) {
            ObjectNode request = input(1);
            object(object(request, "snapshot"), "played_character").set("character_id", actor);
            assertThrows(ContractViolationException.class, () -> WarObservationFrame.fromSnapshot(request.get("snapshot")));
            assertThrows(ContractViolationException.class, () -> projector.project(StrictJson.canonical(request)));
        }
        ObjectNode missing = input(1);
        object(object(missing, "snapshot"), "played_character").remove("character_id");
        assertThrows(ContractViolationException.class, () -> WarObservationFrame.fromSnapshot(missing.get("snapshot")));
        assertThrows(ContractViolationException.class, () -> projector.project(StrictJson.canonical(missing)));
        WarObservationFrame frame = WarObservationFrame.fromSnapshot(input(-2).get("snapshot"));
        assertThrows(ContractViolationException.class, () -> new WarObservationFrame(frame.snapshotId(), frame.revision(),
            frame.nativeRevision(), frame.dateRaw(), frame.episodeRunId(), -1, frame.bridgePid(), frame.connectionGeneration()));
        assertEquals(frame, new WarObservationFrame(frame.snapshotId(), frame.revision(), frame.nativeRevision(),
            frame.dateRaw(), frame.episodeRunId(), -2, frame.bridgePid(), frame.connectionGeneration()));
    }

    @Test void warPidRevisionAndSpecificCampaignRootPositiveDomainsRemainStrict() throws IOException {
        for (long pid : new long[] {0, -2, 4_294_967_296L}) {
            ObjectNode request = input(-2);
            object(object(request, "snapshot"), "diagnostics").put("bridge_pid", pid);
            assertThrows(ContractViolationException.class, () -> WarObservationFrame.fromSnapshot(request.get("snapshot")));
        }
        ObjectNode zeroRevision = input(-2); object(zeroRevision, "snapshot").put("revision", 0);
        assertThrows(ContractViolationException.class, () -> WarObservationFrame.fromSnapshot(zeroRevision.get("snapshot")));
        var projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());
        for (int war : new int[] {0, -2}) {
            ObjectNode request = input(-2); request.put("war_id", war);
            assertThrows(ContractViolationException.class, () -> projector.project(StrictJson.canonical(request)));
        }
        ObjectNode specificRoot = input(1);
        object(specificRoot, "campaign_root").put("player_character_id", -2);
        assertThrows(ContractViolationException.class, () -> projector.project(StrictJson.canonical(specificRoot)));
    }

    private static ObjectNode input(int actor) throws IOException {
        try (InputStream stream = WarObservationNativeActorTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) throw new IOException("committed actual native-normalizer input corpus is missing");
            byte[] raw = stream.readNBytes(CORPUS_MAX_BYTES + 1);
            if (raw.length == 0 || raw.length > CORPUS_MAX_BYTES) throw new IOException("native-normalizer corpus byte bound differs");
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            for (String line : text.split("\n")) {
                JsonNode vector = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
                if ("result".equals(vector.path("expected_kind").textValue())
                        && "test_actual_normalizer_cache_and_json_roundtrip_claim_defender".equals(vector.path("test_method").textValue())) {
                    JsonNode original = StrictJson.parse(StrictJson.text(vector.get("input_json")).getBytes(StandardCharsets.UTF_8));
                    if (!(original instanceof ObjectNode request)) throw new IOException("native-normalizer input must be object");
                    object(object(request, "snapshot"), "played_character").put("character_id", actor);
                    return request;
                }
            }
            throw new IOException("actual native-normalizer successful input is absent; cannot skip signed-domain regression");
        }
    }

    private static ObjectNode object(ObjectNode parent, String key) {
        if (parent.get(key) instanceof ObjectNode object) return object;
        throw new IllegalArgumentException("object absent: " + key);
    }
}
