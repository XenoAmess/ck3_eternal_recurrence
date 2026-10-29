package org.xar.ck3.control.wave2.planning.swayretention;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class SwayTerminalRetentionTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = SwayTerminalRetentionTest.class.getResourceAsStream("/swayretention/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual producer golden required; no oracle fallback or skip"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static byte[] bytes(JsonNode node) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = new ObjectMapper().getFactory().createGenerator(output)) { token(node, generator); }
            return output.toByteArray();
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void token(JsonNode node, JsonGenerator writer) throws IOException {
        if (node.isObject()) {
            writer.writeStartObject();
            for (var field : node.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); }
            writer.writeEndObject();
        } else if (node.isArray()) {
            writer.writeStartArray(); for (JsonNode item : node) { token(item, writer); } writer.writeEndArray();
        } else if (node.isFloatingPointNumber()) {
            String value = node.decimalValue().toString();
            if (!value.contains(".") && !value.contains("E") && !value.contains("e")) { value += ".0"; }
            writer.writeNumber(value);
        } else { writer.writeTree(node); }
    }
    private static void mutations(ObjectNode input, JsonNode changes) {
        for (JsonNode change : changes) {
            JsonNode path = change.get("path"); ObjectNode parent = input;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode child = parent.get(path.get(index).textValue());
                if (!(child instanceof ObjectNode nested)) { throw new IllegalArgumentException("golden mutation is not an object path"); }
                parent = nested;
            }
            String field = path.get(path.size() - 1).textValue();
            if (change.has("remove") && change.get("remove").isBoolean() && change.get("remove").booleanValue()) { parent.remove(field); }
            else { parent.set(field, change.get("value")); }
        }
    }

    @Test
    void originalCausalWriterFollowingConsumerAndRetentionVectorsMatchWholeSnapshots() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.java.sway-retention-producer-golden.v1", fixture.get("schema").textValue());
        assertEquals(24, fixture.get("cases").size());
        assertEquals(0, fixture.get("game_rpc_count").intValue());
        assertEquals(0, fixture.get("canonical_ledger_write_count").intValue());
        assertFalse(fixture.get("production_cutover").booleanValue());
        for (JsonNode vector : fixture.get("cases")) {
            ObjectNode input = fixture.get("base").deepCopy(); mutations(input, vector.get("mutations"));
            byte[] original = bytes(input);
            SwayTerminalRetention.Result result = SwayTerminalRetention.evaluate(original);
            String selected = vector.get("expected_result_ref").textValue();
            assertEquals(selected.equals("previous") ? SwayTerminalRetention.Selection.HISTORICAL_TERMINAL
                    : SwayTerminalRetention.Selection.CURRENT_OBSERVATION, result.selection(), vector.get("id").textValue());
            assertEquals(input.get(selected), StrictJson.parse(result.snapshot().toJson()), vector.get("id").textValue());
            assertEquals(vector.get("original_result_canonical_sha256").textValue(), sha256(result.snapshot().toJson()),
                    "captured canonical result digest: " + vector.get("id").textValue());
            assertArrayEquals(original, bytes(input), "pure leaf must not mutate either source");
            if (vector.get("id").textValue().equals("float-status")) {
                assertTrue(new String(original, StandardCharsets.UTF_8).contains("\"native_status_raw\":1.0"),
                        "the real float token must reach the production decoder");
            }
        }
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("required JDK SHA-256 missing", impossible); }
    }

    @Test
    void consumedHistoryIsCopiedWholeAndNeverRearmedOrAttributedToCurrentRead() throws IOException {
        ObjectNode input = golden().get("base").deepCopy();
        SwayTerminalRetention.Result result = SwayTerminalRetention.evaluate(bytes(input));
        assertEquals(SwayTerminalRetention.Selection.HISTORICAL_TERMINAL, result.selection());
        JsonNode selected = StrictJson.parse(result.snapshot().toJson());
        assertTrue(selected.get("next_turn_consumed").booleanValue());
        assertEquals(802, selected.get("following_native_revision").intValue());
        assertEquals(53290132, selected.get("following_date_raw").intValue());
        assertEquals(input.get("previous").get("causal_observation"), selected.get("causal_observation"));
        assertFalse(input.get("observation").get("terminal_cause_observed").booleanValue());
        assertFalse(result.consumptionRearmed()); assertFalse(result.freshReadCauseAttributed()); assertFalse(result.submissionAuthorized());
    }

    @Test
    void immutableSnapshotDoesNotExposeItsByteArrayOrTrackLaterInputMutations() throws IOException {
        ObjectNode input = golden().get("base").deepCopy();
        SwayTerminalRetention.Snapshot snapshot = SwayTerminalRetention.evaluate(bytes(input)).snapshot();
        byte[] original = snapshot.toJson(), exposed = snapshot.toJson(); exposed[0] = 0;
        ((ObjectNode) input.get("previous")).put("next_turn_consumed", false);
        assertArrayEquals(original, snapshot.toJson());
    }

    @Test
    void malformedFloatBooleanOrStringIdentityCannotReceiveHistoricalAttribution() throws IOException {
        for (JsonNode bad : List.of(new ObjectMapper().getNodeFactory().numberNode(117440593.0),
                new ObjectMapper().getNodeFactory().booleanNode(true), new ObjectMapper().getNodeFactory().textNode("117440593"))) {
            ObjectNode input = golden().get("base").deepCopy();
            ((ObjectNode) input.get("observation")).set("scheme_instance_id", bad);
            ((ObjectNode) input.get("observation").get("native_observation")).set("scheme_instance_id", bad);
            assertEquals(SwayTerminalRetention.Selection.CURRENT_OBSERVATION, SwayTerminalRetention.evaluate(bytes(input)).selection());
        }
    }

    @Test
    void unconsumedJsonExtensionsPreserveFloatTokenAndArbitraryIntegerWithoutCoercion() {
        byte[] raw = "{\"previous\":null,\"observation\":{\"extension_float\":1.0,\"extension_integer\":18446744073709551616000001,\"extension_null\":null,\"extension_empty\":[]}}"
                .getBytes(StandardCharsets.UTF_8);
        byte[] result = SwayTerminalRetention.compose(raw);
        assertTrue(new String(result, StandardCharsets.UTF_8).contains("\"extension_float\":1.0"));
        JsonNode value = StrictJson.parse(result);
        assertTrue(value.get("extension_float").isFloatingPointNumber());
        assertEquals(new BigInteger("18446744073709551616000001"), value.get("extension_integer").bigIntegerValue());
        assertTrue(value.get("extension_null").isNull()); assertTrue(value.get("extension_empty").isArray());
        assertFalse(value.has("missing_extension"));
    }

    @Test
    void exactOuterContractRejectsDuplicateUnknownMalformedAndNonObjectObservation() throws IOException {
        ObjectNode input = golden().get("base").deepCopy(); input.put("admitted", true);
        assertThrows(ContractViolationException.class, () -> SwayTerminalRetention.evaluate(bytes(input)));
        for (String raw : List.of("{\"previous\":{},\"previous\":{},\"observation\":{}}", "{} {}", "null", "[]",
                "{\"previous\":{},\"observation\":null}", "{\"previous\":{},\"observation\":[]}")) {
            assertThrows(ContractViolationException.class,
                    () -> SwayTerminalRetention.evaluate(raw.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> SwayTerminalRetention.evaluate(new byte[] {(byte) 0xc3, 0x28}));
    }
}
