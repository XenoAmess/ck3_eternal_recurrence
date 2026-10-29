package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation.Metric;

final class ScoreInputsTest {
    @Test void actualProducerCasesCoverMatchedRejectedAndAllUnknownMetricUnits() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java-scoreinputs-producer-golden/v1", golden.path("schema").asText());
        assertEquals(48, golden.path("cases").size());
        int matched = 0;
        int unknown = 0;
        for (JsonNode row : golden.path("cases")) {
            JsonNode actual = ScoreInputCodec.evaluate(row.get("request"));
            assertEquals(row.path("expected").get("value"), StrictJson.parse(StrictJson.canonical(actual)), row.path("id").asText());
            assertEquals(actual, StrictJson.parse(StrictJson.canonical(actual)), row.path("id").asText());
            if (actual.isNull()) { matched++; }
            if (row.path("request").path("operation").asText().equals("unknown_metric")) { unknown++; }
        }
        assertTrue(matched >= 3);
        assertEquals(21, unknown);
    }

    @Test void completeBindingRoundTripKeepsOpaqueUint64AndZeroConnectionIdentity() throws IOException {
        ObjectNode request = request("cash-matched");
        ObjectNode source = (ObjectNode) request.get("source");
        ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        BigInteger opaque = new BigInteger("18446744073709551615");
        source.put("revision", opaque); snapshot.put("revision", opaque);
        source.put("connection_generation", 0);
        ((ObjectNode) snapshot.get("diagnostics")).put("connection_generation", 0);
        ScoreInputFrameAssessment.Matched matched = assertInstanceOf(ScoreInputFrameAssessment.Matched.class,
                ScoreInputFrameAssessment.assess(snapshot, source));
        ScoreInputFrame restored = ScoreInputFrame.fromJson(StrictJson.parse(StrictJson.canonical(matched.source().toJson())));
        assertEquals(matched.source(), restored);
        assertEquals(opaque, restored.revision());
        assertEquals(BigInteger.ZERO, restored.connectionGeneration());
        ScoreInputFrame changed = new ScoreInputFrame(restored.snapshotId(), restored.revision(), restored.nativeRevision(),
                restored.dateRaw(), restored.episodeRunId(), restored.actorCharacterId(), restored.bridgePid(), BigInteger.ONE);
        assertThrows(IllegalArgumentException.class, () -> new ScoreInputFrameAssessment.Matched(restored, changed));
    }

    @Test void pythonBooleanFloatEqualityCannotImpersonateRevisionDateOrActorIdentity() throws IOException {
        for (String field : List.of("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation")) {
            for (String token : List.of("true", "1.0", "\"1\"")) {
                ObjectNode request = request("cash-matched");
                ObjectNode source = (ObjectNode) request.get("source");
                ObjectNode snapshot = (ObjectNode) request.get("snapshot");
                JsonNode raw = StrictJson.parse(bytes(token));
                source.set(field, raw);
                if (field.equals("actor_character_id")) { ((ObjectNode) snapshot.get("played_character")).set("character_id", raw); }
                else if (field.equals("bridge_pid") || field.equals("connection_generation")) {
                    ((ObjectNode) snapshot.get("diagnostics")).set(field, raw);
                } else { snapshot.set(field, raw); }
                assertEquals("existing_planning_source_frame_changed:" + field, ScoreInputCodec.evaluate(request).textValue());
            }
        }
    }

    @Test void strictEntryRejectsMissingUnknownDuplicateAndWrongTokens() {
        for (String invalid : List.of(
                "{\"operation\":\"frame_reason\",\"snapshot\":{}}",
                "{\"operation\":\"frame_reason\",\"snapshot\":{},\"source\":null,\"extra\":0}",
                "{\"operation\":\"frame_reason\",\"snapshot\":true,\"source\":null}",
                "{\"operation\":\"unknown_metric\",\"metric\":\"gold\",\"reason\":null}",
                "{\"operation\":\"unknown_metric\",\"metric\":\"gold\",\"reason\":true}",
                "{\"operation\":\"unknown_metric\",\"metric\":\"not-a-metric\",\"reason\":\"missing\"}",
                "{\"operation\":\"unknown_metric\",\"metric\":\"gold\",\"reason\":\"a\",\"reason\":\"b\"}")) {
            assertThrows(IllegalArgumentException.class, () -> ScoreInputCodec.evaluate(bytes(invalid)));
        }
        assertThrows(IllegalArgumentException.class, () -> ScoreInputCodec.evaluate(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test void oldSdkExtensionFieldsRemainAProjectionRatherThanAnExactContainerSchema() throws IOException {
        ObjectNode request = request("cash-matched");
        ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        ObjectNode source = (ObjectNode) request.get("source");
        snapshot.put("unused_decimal", 0.125);
        source.putObject("unused_context").put("arbitrary", "允许扩展");
        assertTrue(ScoreInputCodec.evaluate(request).isNull());
        snapshot.put("paused", "true");
        assertEquals("current_paused_player_frame_unavailable", ScoreInputCodec.evaluate(request).textValue());
    }

    @Test void unknownMetricPreservesNullSourceAndNeverTurnsMissingIntoZero() {
        JsonNode unknown = new UnknownScoreMetric(Metric.GROSS_INCOME, "").toJson();
        assertTrue(unknown.get("value").isNull());
        assertTrue(unknown.get("source_ref").isNull());
        assertEquals("unknown", unknown.path("availability").asText());
        assertEquals("gold/month", unknown.path("unit").asText());
        assertEquals("", unknown.path("reason_zh").textValue());
        assertThrows(IllegalArgumentException.class, () -> new UnknownScoreMetric(null, "missing"));
        assertThrows(IllegalArgumentException.class, () -> new UnknownScoreMetric(Metric.GOLD, null));
        ObjectNode invalid = StrictJson.object();
        invalid.set("revision", JsonNodeFactory.instance.booleanNode(true));
        assertThrows(IllegalArgumentException.class, () -> ScoreInputFrame.fromJson(invalid));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ScoreInputsTest.class.getResourceAsStream("/scoreinputs/producer-golden.json")) {
            if (stream == null) { throw new IOException("original producer capture required; missing fixture is never skipped"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode request(String id) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (row.path("id").asText().equals(id)) { return ((ObjectNode) row.get("request")).deepCopy(); }
        }
        throw new IOException("required actual producer case missing: " + id);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
