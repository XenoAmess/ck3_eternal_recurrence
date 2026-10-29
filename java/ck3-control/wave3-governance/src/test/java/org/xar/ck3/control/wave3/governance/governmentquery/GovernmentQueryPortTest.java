package org.xar.ck3.control.wave3.governance.governmentquery;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryPort.QueryRejectedException;

final class GovernmentQueryPortTest {
    @TestFactory
    Stream<DynamicTest> originalRealQueryProducerBeforeEnvelopeAndAfterGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(17, golden.get("cases").size());
        assertTrue(golden.get("source_refs_unchanged").booleanValue());
        assertEquals(7, golden.get("original_unittest").get("tests").intValue());
        assertEquals(0, golden.get("original_unittest").get("skipped").intValue());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(
                row.get("name").textValue(), () -> {
                    ObjectNode prepare = patched(golden.get("base_prepare"), row.get("prepare_patch"));
                    JsonNode expectedRequest = row.get("expected_request");
                    if (expectedRequest.isNull()) {
                        assertEquals(0, row.get("native_read_request_count").intValue());
                        QueryRejectedException failure = assertThrows(QueryRejectedException.class,
                                () -> GovernmentQueryCodec.prepare(raw(prepare)));
                        assertEquals(row.get("failure").get("message").textValue(), failure.getMessage());
                        return;
                    }
                    assertEquals(1, row.get("native_read_request_count").intValue());
                    assertEquals(expectedRequest, StrictJson.parse(GovernmentQueryCodec.prepare(raw(prepare))));
                    ObjectNode consume = patched(golden.get("base_consume"), row.get("consume_patch"));
                    if (!row.get("failure").isNull()) {
                        QueryRejectedException failure = assertThrows(QueryRejectedException.class,
                                () -> GovernmentQueryCodec.consume(raw(consume)));
                        assertEquals(row.get("failure").get("message").textValue(), failure.getMessage());
                    } else {
                        JsonNode actual = StrictJson.parse(GovernmentQueryCodec.consume(raw(consume)));
                        assertEquals(row.get("expected_status"), actual.get("status"));
                        assertEquals(row.get("expected_output_sha256").textValue(), sha256(StrictJson.canonical(actual)),
                                "complete actual original query result, not a selected ready flag");
                    }
                }));
    }

    @Test
    void projectionAdapterMarksOnlyDeclaredCoreRefusals() throws IOException {
        ObjectNode disabled = base("base_prepare"); disabled.put("query_enabled", false);
        QueryRejectedException original = assertThrows(QueryRejectedException.class, () -> GovernmentQueryCodec.prepare(raw(disabled)));
        ProjectionDomainRejection refusal = assertThrows(ProjectionDomainRejection.class, () -> GovernmentQueryCodec.prepareProjection(raw(disabled)));
        assertEquals(original.getMessage(), refusal.getMessage());
        ObjectNode crossed = base("base_consume");
        ((ObjectNode) crossed.get("after_snapshot").get("played_character")).put("alive", false);
        assertThrows(ProjectionDomainRejection.class, () -> GovernmentQueryCodec.consumeProjection(raw(crossed)));
        ObjectNode malformed = base("base_prepare"); malformed.put("expected_revision", true);
        assertThrows(ProjectionDomainRejection.class, () -> GovernmentQueryCodec.prepareProjection(raw(malformed)));
    }

    @Test
    void exactPublicAndNativeRevisionTokenTypesAreChecked() throws IOException {
        String valid = new String(raw(base("base_prepare")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "702.0", "\"702\"")) {
            String rawExpected = valid.replace("\"expected_revision\":702", "\"expected_revision\":" + token);
            assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.prepare(rawExpected.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode request = base("base_prepare");
        ObjectNode before = (ObjectNode) request.get("before_snapshot");
        before.put("native_revision", 701.0);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.prepare(raw(request)));
        before.put("native_revision", 701);
        ((ObjectNode) before.get("played_character")).put("character_id", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.prepare(raw(request)));
    }

    @Test
    void actualEnvelopeFlagsAndOptionalProtocolVersionRejectCoercion() throws IOException {
        for (String field : List.of("accepted", "private_build", "read_only", "advertised")) {
            ObjectNode request = base("base_consume");
            ((ObjectNode) request.get("command_result").get("result")).put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(request)), field);
        }
        ObjectNode request = base("base_consume");
        ((ObjectNode) request.get("command_result")).put("protocol_version", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(request)));
        ((ObjectNode) request.get("command_result")).put("protocol_version", 1.0);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(request)));
    }

    @Test
    void historicMissingProtocolFieldRetainsExistingAdmission() throws IOException {
        ObjectNode original = base("base_consume");
        JsonNode expected = StrictJson.parse(GovernmentQueryCodec.consume(raw(original)));
        ((ObjectNode) original.get("command_result")).remove("protocol_version");
        assertEquals(expected, StrictJson.parse(GovernmentQueryCodec.consume(raw(original))));
    }

    @Test
    void fullActorComparisonIgnoresKeyOrderAndKeepsEveryField() throws IOException {
        ObjectNode request = base("base_consume");
        ObjectNode before = (ObjectNode) request.get("before_snapshot");
        ObjectNode after = (ObjectNode) request.get("after_snapshot");
        ObjectNode actor = (ObjectNode) before.get("played_character");
        ObjectNode reordered = StrictJson.object().put("alive", true).put("character_id", actor.get("character_id").bigIntegerValue());
        after.set("played_character", reordered);
        JsonNode actual = StrictJson.parse(GovernmentQueryCodec.consume(raw(request)));
        assertEquals("available", actual.get("status").textValue());
        actor.put("unconsumed_numeric_metadata", 1);
        reordered.put("unconsumed_numeric_metadata", 1.0);
        assertEquals("available", StrictJson.parse(GovernmentQueryCodec.consume(raw(request))).get("status").textValue());
        reordered.put("character_id", actor.get("character_id").doubleValue());
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(request)));
        reordered.put("character_id", actor.get("character_id").bigIntegerValue());
        reordered.put("new_observed_actor_field", "changed");
        QueryRejectedException error = assertThrows(QueryRejectedException.class, () -> GovernmentQueryCodec.consume(raw(request)));
        assertEquals(GovernmentQueryPort.Rejection.CROSSED_PAUSED_FRAME, error.rejection());
    }

    @Test
    void strictWrappersRejectUnknownMissingNullAndMalformedBytes() throws IOException {
        ObjectNode prepare = base("base_prepare"); prepare.put("native_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.prepare(raw(prepare)));
        ObjectNode missingAfter = base("base_consume"); missingAfter.remove("after_snapshot");
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(missingAfter)));
        ObjectNode nullCommand = base("base_consume"); nullCommand.putNull("command_result");
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(raw(nullCommand)));
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.prepare(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.consume(new byte[65_537]));
    }

    @Test
    void preparingAndConsumingNeverMutatesTheHeldInputEvidence() throws IOException {
        ObjectNode prepare = base("base_prepare"); String beforePrepare = prepare.toString();
        GovernmentQueryCodec.prepare(raw(prepare)); assertEquals(beforePrepare, prepare.toString());
        ObjectNode consume = base("base_consume"); String beforeConsume = consume.toString();
        byte[] first = GovernmentQueryCodec.consume(raw(consume));
        assertEquals(beforeConsume, consume.toString());
        assertEquals(StrictJson.parse(first), StrictJson.parse(GovernmentQueryCodec.consume(raw(consume))));
    }

    @Test
    void responsePrevalidationRequiresNoAfterFrameAndDoesNotGrantOne() throws IOException {
        ObjectNode consume = base("base_consume");
        ObjectNode response = consume.deepCopy();
        response.remove("after_snapshot");
        response.put("schema", GovernmentQueryCodec.VALIDATE_RESPONSE_SCHEMA);
        JsonNode admitted = StrictJson.parse(GovernmentQueryCodec.validateResponse(raw(response)));
        assertEquals(GovernmentQueryCodec.VALIDATED_RESPONSE_SCHEMA, admitted.get("schema").textValue());
        assertEquals("validated", admitted.get("status").textValue());
        assertEquals(response.get("request_id"), admitted.get("request_id"));
        assertEquals(response.get("expected_revision"), admitted.get("expected_revision"));
        assertEquals(4, admitted.size());
        ((ObjectNode) consume.get("after_snapshot").get("played_character")).put("alive", false);
        QueryRejectedException crossed = assertThrows(QueryRejectedException.class,
                () -> GovernmentQueryCodec.consume(raw(consume)));
        assertEquals(GovernmentQueryPort.Rejection.CROSSED_PAUSED_FRAME, crossed.rejection());
        assertEquals(admitted, StrictJson.parse(GovernmentQueryCodec.validateResponse(raw(response))));
        response.set("after_snapshot", consume.get("after_snapshot"));
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.validateResponse(raw(response)));
    }

    @Test
    void responsePrevalidationPreservesCommandAndSourceRejections() throws IOException {
        ObjectNode response = base("base_consume");
        response.remove("after_snapshot");
        response.put("schema", GovernmentQueryCodec.VALIDATE_RESPONSE_SCHEMA);
        ((ObjectNode) response.get("command_result")).put("ok", false);
        QueryRejectedException command = assertThrows(QueryRejectedException.class,
                () -> GovernmentQueryCodec.validateResponse(raw(response)));
        assertEquals(GovernmentQueryPort.Rejection.COMMAND_RESULT_UNAVAILABLE, command.rejection());
        ((ObjectNode) response.get("command_result")).put("ok", true);
        ((ObjectNode) response.get("command_result").get("result")).putNull("government_runtime_adapter");
        QueryRejectedException source = assertThrows(QueryRejectedException.class,
                () -> GovernmentQueryCodec.validateResponse(raw(response)));
        assertEquals(GovernmentQueryPort.Rejection.SOURCE_UNAVAILABLE, source.rejection());
        ((ObjectNode) response.get("command_result")).put("protocol_version", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentQueryCodec.validateResponse(raw(response)));
    }

    private static ObjectNode patched(JsonNode base, JsonNode patches) {
        ObjectNode result = (ObjectNode) base.deepCopy();
        for (JsonNode patch : patches) {
            String pointer = patch.get("path").textValue(); int last = pointer.lastIndexOf('/');
            JsonNode parent = last == 0 ? result : result.at(pointer.substring(0, last));
            assertTrue(parent.isObject());
            String key = pointer.substring(last + 1).replace("~1", "/").replace("~0", "~");
            if ("remove".equals(patch.get("op").textValue())) { ((ObjectNode) parent).remove(key); }
            else { assertEquals("set", patch.get("op").textValue()); ((ObjectNode) parent).set(key, patch.get("value").deepCopy()); }
        }
        return result;
    }
    private static JsonNode golden() throws IOException {
        try (InputStream source = GovernmentQueryPortTest.class.getResourceAsStream("/governmentquery/original-producer-golden.json")) {
            assertNotNull(source, "original query producer golden is mandatory; no legacy fallback");
            return StrictJson.parse(source.readAllBytes());
        }
    }
    private static ObjectNode base(String field) throws IOException { return (ObjectNode) golden().get(field).deepCopy(); }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] raw) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
}
