package org.xar.ck3.control.wave3.runtime.childexports;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ChildExportCallbackAdapterTest {
    private static final int PURE_CORPUS_MAX_BYTES = 98_304;
    private static final int CALLBACK_CORPUS_MAX_BYTES = 49_152;
    @Test void registeredTypedPortKeepsTheBase64WrapperSeparateFromThePrivateWireBudget() {
        ChildExportProjectionPort port = new ChildExportProjectionPort();
        assertEquals(org.xar.ck3.control.contracts.projection.ProjectionOperation.CHILD_EXPORT_PROJECT, port.operation());
        assertEquals(32_768, port.inputMaximumBytes());
        assertEquals(32_768, port.outputMaximumBytes());
        String prefix = "{\"kind\":\"actual_child_exports\",\"exports\":[]}";
        byte[] exact = bytes(prefix + " ".repeat(ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES - prefix.length() - 1) + "\n");
        byte[] outer = StrictJson.canonical(wirePayload("MCPApp", exact), port.inputMaximumBytes());
        assertTrue(outer.length > ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES);
        ChildExportCallbackAdapter.Result result = port.project(port.decode(outer));
        JsonNode reply = StrictJson.parse(port.encode(result), port.outputMaximumBytes());
        assertEquals(0, reply.get("export_count").intValue());
        assertEquals(1, new ChildExportProjectionCatalog().registrations().size());
        assertThrows(ContractViolationException.class,
                () -> port.decode(StrictJson.canonical(wirePayload("MCPApp",
                        bytes(new String(exact, StandardCharsets.UTF_8) + " ")), port.inputMaximumBytes())),
                "private byte cap including the final LF belongs to input decode");
    }

    @Test void originalProducerWireEntersTypedCallbackAndReturnsOriginalConsumerBytes() throws IOException {
        JsonNode golden = golden("/childexports/child-exports-golden.json");
        for (JsonNode row : golden.get("producer_cases")) {
            if (!row.get("accepted").booleanValue()) { continue; }
            byte[] original = bytes(row.get("expected_wire_json").textValue());
            ObjectNode reply = ChildExportCallbackAdapter.handle(wirePayload(row.get("role").textValue(), original));
            assertEquals(ChildExportCallbackAdapter.RESULT_SCHEMA, reply.get("schema").textValue());
            assertEquals("CANONICALIZE_WIRE", reply.get("operation").textValue());
            assertArrayEquals(original, Base64.getDecoder().decode(reply.get("wire_base64").textValue()));
        }
    }

    @Test void javaProducerConsumesExactLocationDecimalsAndMatchesActualOriginalProducerBytes() throws IOException {
        JsonNode golden = golden("/childexports/child-exports-golden.json");
        for (JsonNode row : golden.get("producer_cases")) {
            ObjectNode payload = StrictJson.object();
            payload.put("schema", ChildExportCallbackAdapter.INPUT_SCHEMA);
            payload.put("operation", "PRODUCE_WIRE");
            payload.put("retained_role", row.get("role").textValue());
            com.fasterxml.jackson.databind.node.ArrayNode locations = payload.putArray("location_decimals");
            for (JsonNode location : row.get("locations")) { locations.add(location.bigIntegerValue().toString()); }
            if (row.get("accepted").booleanValue()) {
                ObjectNode reply = ChildExportCallbackAdapter.handle(payload);
                assertEquals("PRODUCE_WIRE", reply.get("operation").textValue());
                assertArrayEquals(bytes(row.get("expected_wire_json").textValue()),
                        Base64.getDecoder().decode(reply.get("wire_base64").textValue()));
            } else {
                assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(payload));
            }
        }
        for (String token : List.of("true", "1.0", "\"01\"", "\"-1\"", "\"0\"")) {
            String wire = "{\"schema\":\"" + ChildExportCallbackAdapter.INPUT_SCHEMA
                    + "\",\"operation\":\"PRODUCE_WIRE\",\"retained_role\":\"Queue\",\"location_decimals\":[" + token + "]}";
            assertThrows(ContractViolationException.class,
                    () -> ChildExportCallbackAdapter.handle(StrictJson.parse(bytes(wire))));
        }
        ChildExportProjectionPort port = new ChildExportProjectionPort();
        ObjectNode maximum = StrictJson.object();
        maximum.put("schema", ChildExportCallbackAdapter.INPUT_SCHEMA);
        maximum.put("operation", "PRODUCE_WIRE");
        maximum.put("retained_role", "owner");
        maximum.putArray("location_decimals").add("1".repeat(4_300)).add("2".repeat(4_300));
        ChildExportCallbackAdapter.Request typed = port.decode(StrictJson.canonical(maximum, port.inputMaximumBytes()));
        JsonNode reply = StrictJson.parse(port.encode(port.project(typed)), port.outputMaximumBytes());
        assertTrue(Base64.getDecoder().decode(reply.get("wire_base64").textValue()).length
                < ChildExportCodec.PRIVATE_MESSAGE_MAX_BYTES);
        ObjectNode tooManyDigits = maximum.deepCopy();
        tooManyDigits.putArray("location_decimals").add("1".repeat(4_301)).add("2");
        assertThrows(ContractViolationException.class,
                () -> port.decode(StrictJson.canonical(tooManyDigits, port.inputMaximumBytes())),
                "private producer input rejection must occur before project and its encoder");
    }

    @Test void originalSignedIntegerAndRawWrongTokensReachThePrivateDecoderWithoutNormalization() throws IOException {
        JsonNode golden = golden("/childexports/child-exports-golden.json");
        for (JsonNode row : golden.get("numeric_boundary_cases")) {
            ObjectNode payload = wirePayload("Queue", bytes(row.get("wire_json").textValue()));
            if (row.get("accepted").booleanValue()) {
                ObjectNode result = ChildExportCallbackAdapter.handle(payload);
                assertArrayEquals(bytes(row.get("wire_json").textValue()),
                        Base64.getDecoder().decode(result.get("wire_base64").textValue()));
            } else {
                assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(payload));
            }
        }
        for (String token : List.of("true", "false", "1.0", "501.0", "\"501\"", "null", "-1")) {
            String raw = "{\"kind\":\"actual_child_exports\",\"exports\":[{\"role\":\"MCPApp\",\"location\":" + token + "}]}\n";
            assertThrows(ContractViolationException.class,
                    () -> ChildExportCallbackAdapter.handle(wirePayload("Queue", bytes(raw))));
            ChildExportProjectionPort port = new ChildExportProjectionPort();
            assertThrows(ContractViolationException.class,
                    () -> port.decode(StrictJson.canonical(wirePayload("Queue", bytes(raw)), port.inputMaximumBytes())),
                    "wrong private input token must fail in decode, never be recast from a project/encoder failure");
        }
    }

    @Test void readbacksRemainAfterActualReaderValuesAndRejectPidAliasesAndWrongTypes() {
        String first = "[71,\"134368602545256921\",\"c:/own/python.exe\"]";
        String second = "[72,\"134368602545256922\",\"c:/own/python.exe\"]";
        ObjectNode good = keysPayload("Queue", "[" + first + "," + second + "]");
        assertEquals(2, ChildExportCallbackAdapter.handle(good).get("process_count").intValue());
        String alias = "[71,\"134368602545256922\",\"c:/own/python.exe\"]";
        assertThrows(ContractViolationException.class,
                () -> ChildExportCallbackAdapter.handle(keysPayload("Queue", "[" + first + "," + alias + "]")));
        assertThrows(ContractViolationException.class,
                () -> ChildExportCallbackAdapter.handle(keysPayload("MCPApp", "[[71.0,\"134368602545256921\",\"c:/own/python.exe\"]]")));
        ChildExportProjectionPort port = new ChildExportProjectionPort();
        assertThrows(ContractViolationException.class, () -> port.decode(StrictJson.canonical(
                keysPayload("Queue", "[" + first + "," + alias + "]"), port.inputMaximumBytes())),
                "private readback PID alias is an input failure before project");
        assertThrows(ContractViolationException.class, () -> port.decode(StrictJson.canonical(
                keysPayload("MCPApp", "[[71.0,\"134368602545256921\",\"c:/own/python.exe\"]]"), port.inputMaximumBytes())),
                "private readback scalar coercion is an input failure before project");
    }

    @Test void hostPayloadRejectsExtraMissingMalformedAndOversizedBytesAndKeepsDefaultMapProfile() {
        byte[] app = bytes("{\"kind\":\"actual_child_exports\",\"exports\":[]}\n");
        ObjectNode valid = wirePayload("MCPApp", app);
        ObjectNode extra = valid.deepCopy(); extra.put("source_verified", true);
        assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(extra));
        for (String field : List.of("schema", "operation", "retained_role", "wire_base64")) {
            ObjectNode missing = valid.deepCopy(); missing.remove(field);
            assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(missing));
            ObjectNode nullable = valid.deepCopy(); nullable.putNull(field);
            assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(nullable));
        }
        for (String encoded : List.of("%%", "YQ", "YQ==\n", "AA==".repeat(8_000))) {
            ObjectNode malformed = valid.deepCopy(); malformed.put("wire_base64", encoded);
            assertThrows(ContractViolationException.class, () -> ChildExportCallbackAdapter.handle(malformed));
            ChildExportProjectionPort port = new ChildExportProjectionPort();
            assertThrows(ContractViolationException.class,
                    () -> port.decode(StrictJson.canonical(malformed, port.inputMaximumBytes())),
                    "invalid base64 must be rejected before project");
        }
        assertThrows(ContractViolationException.class,
                () -> ChildExportCallbackAdapter.handle(wirePayload("MCPApp", new byte[] {(byte) 0xff})));
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse(bytes("{\"location\":1" + "0".repeat(1_099) + "}")));
    }

    @Test void actualSdkCallbackChainRequiresIndependentGoldenAndReplaysEveryJavaPayload() throws IOException {
        JsonNode golden = golden("/childexports/child-exports-callback-chain-golden.json");
        assertEquals("xar.java.actual-child-exports-callback-chain-golden/v1", golden.get("schema").textValue());
        assertEquals(0, golden.get("game_rpc_calls").intValue());
        assertEquals(0, golden.get("native_os_calls").intValue());
        assertTrue(golden.get("callback_rows").isArray());
        assertTrue(golden.get("callback_rows").size() >= 6, "App/Queue/owner bytes and all three original readbacks required");
        for (JsonNode row : golden.get("callback_rows")) {
            assertCallbackResult(row);
        }
        assertEquals("/childexports/child-exports-golden.json", golden.get("independent_python_baseline_resource").textValue());
        assertEquals(9, golden.get("production_projection_post_calls").intValue());
        JsonNode production = golden.get("production_callback_rows");
        assertTrue(production.isArray());
        assertEquals(9, production.size());
        for (JsonNode row : production) { assertCallbackResult(row); }
        assertEquals(List.of("app_export:PRODUCE_WIRE:MCPApp",
                        "queue_export:CANONICALIZE_WIRE:MCPApp", "queue_export:VALIDATE_READBACKS:MCPApp", "queue_export:PRODUCE_WIRE:Queue",
                        "owner_export:CANONICALIZE_WIRE:Queue", "owner_export:VALIDATE_READBACKS:Queue", "owner_export:PRODUCE_WIRE:owner",
                        "supervisor_bind:CANONICALIZE_WIRE:owner", "supervisor_bind:VALIDATE_READBACKS:owner"),
                java.util.stream.StreamSupport.stream(production.spliterator(), false)
                        .map(row -> row.get("stage").textValue() + ":" + row.get("payload").get("operation").textValue()
                                + ":" + row.get("payload").get("retained_role").textValue()).toList());
        JsonNode stages = golden.get("production_stages");
        assertTrue(stages.isArray());
        assertEquals(4, stages.size());
        assertEquals(List.of("app_export:1", "queue_export:3", "owner_export:3", "supervisor_bind:2"),
                java.util.stream.StreamSupport.stream(stages.spliterator(), false).map(row -> {
                    assertEquals(row.get("attempted_callbacks").intValue(), row.get("completed_callbacks").intValue());
                    return row.get("stage").textValue() + ":" + row.get("attempted_callbacks").intValue();
                }).toList());
        assertEquals(List.of(71, 72, 73),
                java.util.stream.StreamSupport.stream(golden.get("final_pids").spliterator(), false)
                        .map(JsonNode::intValue).toList());
    }

    @Test void actualSdkUnavailableAndUnsupportedPathsRequireIndependentFailureGolden() throws IOException {
        JsonNode golden = golden("/childexports/child-exports-callback-failure-golden.json");
        assertEquals("xar.java.child-export-callback-failure-golden/v1", golden.get("schema").textValue());
        assertTrue(golden.get("synthetic_error_injection").booleanValue());
        assertFalse(golden.get("actual_projection_http_failure_proved").booleanValue());
        assertEquals("injected-test/v1", golden.get("error_transport_kind").textValue());
        assertEquals(0, golden.get("native_os_calls").intValue());
        assertEquals(0, golden.get("game_rpc_calls").intValue());
        assertEquals(0, golden.get("ledger_writes").intValue());
        JsonNode cases = golden.get("cases");
        assertTrue(cases.isArray());
        assertEquals(4, cases.size());
        java.util.Set<String> observed = new java.util.HashSet<>();
        for (JsonNode row : cases) {
            assertTrue(observed.add(row.get("name").textValue() + ":" + row.get("phase").textValue()));
            assertTrue(row.get("propagated_original_exception").booleanValue());
            assertEquals(0, row.get("native_duplicate_calls").intValue());
            assertEquals(0, row.get("native_send_calls").intValue());
            switch (row.get("phase").textValue()) {
                case "preflight" -> assertEquals(0, row.get("native_read_calls").intValue());
                case "after_private_receive" -> {
                    assertEquals(1, row.get("synthetic_private_reads").intValue());
                    assertEquals(1, row.get("original_outer_cleanup_calls").intValue());
                    assertEquals(1, row.get("projection_calls").intValue());
                }
                default -> fail("unknown original callback failure phase");
            }
        }
        assertEquals(java.util.Set.of("unavailable:preflight", "unsupported:preflight",
                "unavailable:after_private_receive", "unsupported:after_private_receive"), observed);
    }

    /** Shared canonical form preserves JSON integer kind, booleans, null and array order; floats reject. */
    private static void assertCallbackResult(JsonNode row) {
        assertArrayEquals(StrictJson.canonical(row.get("java_result"), 32_768),
                StrictJson.canonical(ChildExportCallbackAdapter.handle(row.get("payload")), 32_768));
    }

    private static ObjectNode wirePayload(String role, byte[] raw) {
        ObjectNode payload = StrictJson.object(); payload.put("schema", ChildExportCallbackAdapter.INPUT_SCHEMA); payload.put("operation", "CANONICALIZE_WIRE");
        payload.put("retained_role", role); payload.put("wire_base64", Base64.getEncoder().encodeToString(raw));
        return payload;
    }

    private static ObjectNode keysPayload(String role, String wire) {
        ObjectNode payload = StrictJson.object(); payload.put("schema", ChildExportCallbackAdapter.INPUT_SCHEMA); payload.put("operation", "VALIDATE_READBACKS");
        payload.put("retained_role", role); payload.put("keys_json_base64", Base64.getEncoder().encodeToString(bytes(wire)));
        return payload;
    }

    private static JsonNode golden(String path) throws IOException {
        try (InputStream input = ChildExportCallbackAdapterTest.class.getResourceAsStream(path)) {
            if (input == null) { throw new IOException("actual original child callback golden required; never skip: " + path); }
            int maximumBytes = switch (path) {
                case "/childexports/child-exports-golden.json" -> PURE_CORPUS_MAX_BYTES;
                case "/childexports/child-exports-callback-chain-golden.json",
                        "/childexports/child-exports-callback-failure-golden.json" -> CALLBACK_CORPUS_MAX_BYTES;
                default -> throw new IOException("unknown finite child callback corpus: " + path);
            };
            byte[] raw = input.readNBytes(maximumBytes + 1);
            StrictJson.require(raw.length <= maximumBytes, "bounded independent child callback corpus required");
            return StrictJson.parse(raw, maximumBytes,
                    StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300);
        }
    }

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}

