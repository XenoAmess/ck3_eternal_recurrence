package org.xar.ck3.control.military.declarationpriority;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.Declaration;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.LeafInput;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority.SelectionInput;

final class DeclarationObjectivePriorityTest {
    private static final String LEAF_PREFIX = "{\"schema\":\"" + DeclarationPriorityCodec.LEAF_SCHEMA
            + "\",\"actor_character_id\":31254,\"declaration\":";

    @Test
    void originalLeafProducerGoldenMatches() throws IOException {
        JsonNode golden = golden();
        assertEquals(7, golden.path("original_unittest").path("tests").intValue());
        assertEquals(0, golden.path("original_unittest").path("skipped").intValue());
        assertTrue(golden.path("leaf_cases").size() >= 30);
        for (JsonNode row : golden.path("leaf_cases")) {
            LeafInput input = DeclarationPriorityCodec.decodeLeaf(StrictJson.canonical(row.get("request")));
            assertEquals(row.path("expected_priority").intValue(),
                    DeclarationObjectivePriority.priority(input).rank(), row.path("name").textValue());
        }
    }

    @Test
    void originalConsumerGoldenRetainsPowerOrderAndFirstExactTie() throws IOException {
        JsonNode golden = golden();
        assertTrue(golden.path("selection_cases").size() >= 20);
        for (JsonNode row : golden.path("selection_cases")) {
            SelectionInput input = DeclarationPriorityCodec.decodeSelection(StrictJson.canonical(row.get("request")));
            var chosen = DeclarationObjectivePriority.preferredIndex(input);
            String name = row.path("name").textValue();
            if (row.get("expected_index").isNull()) {
                assertTrue(chosen.isEmpty(), name);
            } else {
                assertEquals(row.path("expected_index").intValue(), chosen.orElseThrow(), name);
                assertEquals(row.path("expected_declaration_id").textValue(),
                        input.declarations().get(chosen.orElseThrow()).declarationId().value(), name);
            }
        }
    }

    @Test
    void malformedWireTypesAreRejectedRatherThanSilentlyCoerced() throws IOException {
        for (JsonNode row : golden().path("wire_rejections")) {
            assertEquals(1, row.path("legacy_priority").intValue());
            assertTrue(row.path("raw_request_json").isTextual(), "capture must retain the original JSON tokens");
            byte[] originalWire = row.path("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8);
            assertThrows(ContractViolationException.class,
                    () -> DeclarationPriorityCodec.decodeLeaf(originalWire),
                    row.path("name").textValue());
        }
    }

    @Test
    void floatingIntegerTokensReachTheProductionDecoderUnmodified() {
        String own = LEAF_PREFIX + "{\"source\":\"native\",\"casus_belli_key\":\"claim_cb\","
                + "\"claimant_character_id\":31254,\"target_title_ids\":[7219]}}";
        for (String raw : List.of(
                own.replace("\"actor_character_id\":31254", "\"actor_character_id\":31254.0"),
                own.replace("\"actor_character_id\":31254", "\"actor_character_id\":3.1254e4"),
                own.replace("\"claimant_character_id\":31254", "\"claimant_character_id\":31254.0"),
                own.replace("[7219]", "[7219.0]"))) {
            assertThrows(ContractViolationException.class,
                    () -> DeclarationPriorityCodec.decodeLeaf(raw.getBytes(StandardCharsets.UTF_8)), raw);
        }
        assertEquals(0, DeclarationObjectivePriority.priority(
                DeclarationPriorityCodec.decodeLeaf(own.getBytes(StandardCharsets.UTF_8))).rank());
    }

    @Test
    void committedGoldenRoundTripsInTheExactJsonIntegerDomain() throws IOException {
        JsonNode golden = golden();
        for (JsonNode row : golden.path("leaf_cases")) {
            byte[] original = StrictJson.canonical(row.get("request"));
            LeafInput parsed = DeclarationPriorityCodec.decodeLeaf(original);
            byte[] encoded = DeclarationPriorityCodec.encodeLeaf(parsed);
            assertEquals(StrictJson.parse(original), StrictJson.parse(encoded), row.path("name").textValue());
            assertEquals(parsed, DeclarationPriorityCodec.decodeLeaf(encoded));
        }
        for (JsonNode row : golden.path("selection_cases")) {
            byte[] original = StrictJson.canonical(row.get("request"));
            SelectionInput parsed = DeclarationPriorityCodec.decodeSelection(original);
            byte[] encoded = DeclarationPriorityCodec.encodeSelection(parsed);
            assertEquals(StrictJson.parse(original), StrictJson.parse(encoded), row.path("name").textValue());
            assertEquals(parsed, DeclarationPriorityCodec.decodeSelection(encoded));
        }
    }

    @Test
    void missingNullAndEmptyAreDistinctAndUnknownIsNotPromoted() {
        LeafInput missing = decode("{}");
        LeafInput explicitNull = decode("{\"target_title_ids\":null}");
        LeafInput empty = decode("{\"target_title_ids\":[]}");
        assertNotEquals(missing, explicitNull);
        assertNotEquals(explicitNull, empty);
        assertEquals(JsonField.Presence.MISSING, missing.declaration().value().targetTitleIds().presence());
        assertEquals(JsonField.Presence.NULL, explicitNull.declaration().value().targetTitleIds().presence());
        assertTrue(empty.declaration().value().targetTitleIds().value().isEmpty());
        for (LeafInput input : List.of(missing, explicitNull, empty)) {
            assertEquals(1, DeclarationObjectivePriority.priority(input).rank());
            assertEquals(input, DeclarationPriorityCodec.decodeLeaf(DeclarationPriorityCodec.encodeLeaf(input)));
        }
    }

    @Test
    void requiredEnvelopeUnknownFieldsDuplicateKeysAndMalformedUtf8AreRejected() {
        List<String> malformed = List.of("{}", LEAF_PREFIX + "{}} {}",
                LEAF_PREFIX + "{\"source\":\"native\",\"source\":\"synthetic\"}}",
                LEAF_PREFIX + "{\"expected_title_transfer\":true}}",
                "{\"schema\":\"wrong\",\"actor_character_id\":31254,\"declaration\":{}}",
                "{\"schema\":\"" + DeclarationPriorityCodec.LEAF_SCHEMA + "\",\"declaration\":{}}",
                "{\"schema\":\"" + DeclarationPriorityCodec.LEAF_SCHEMA + "\",\"actor_character_id\":31254}");
        for (String raw : malformed) {
            assertThrows(ContractViolationException.class,
                    () -> DeclarationPriorityCodec.decodeLeaf(raw.getBytes(StandardCharsets.UTF_8)), raw);
        }
        assertThrows(ContractViolationException.class,
                () -> DeclarationPriorityCodec.decodeLeaf(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void assessmentFieldsCannotBeMissingNullFractionalOrDuplicated() throws IOException {
        JsonNode request = golden().path("selection_cases").get(3).path("request");
        ObjectNode missing = ((ObjectNode) request).deepCopy();
        ((ObjectNode) missing.path("war_entry_assessments").get(0)).remove("distance_raw");
        assertThrows(ContractViolationException.class,
                () -> DeclarationPriorityCodec.decodeSelection(StrictJson.canonical(missing)));
        ObjectNode fractional = ((ObjectNode) request).deepCopy();
        ((ObjectNode) fractional.path("war_entry_assessments").get(0)).put("actual_power_ratio_raw", 1.0);
        assertThrows(ContractViolationException.class, () -> DeclarationPriorityCodec.decodeSelection(
                fractional.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode nullable = ((ObjectNode) request).deepCopy();
        ((ObjectNode) nullable.path("war_entry_assessments").get(0)).putNull("distance_raw");
        assertThrows(ContractViolationException.class,
                () -> DeclarationPriorityCodec.decodeSelection(StrictJson.canonical(nullable)));
        ObjectNode duplicate = ((ObjectNode) request).deepCopy();
        var assessments = (com.fasterxml.jackson.databind.node.ArrayNode) duplicate.path("war_entry_assessments");
        assessments.add(assessments.get(0).deepCopy());
        assertThrows(IllegalArgumentException.class,
                () -> DeclarationPriorityCodec.decodeSelection(StrictJson.canonical(duplicate)));
    }

    @Test
    void integerPrecisionIsPreservedAboveUint64AndAcrossRiskSubtraction() throws IOException {
        for (JsonNode row : golden().path("leaf_cases")) {
            if (row.path("name").textValue().equals("python-exact-integer-beyond-uint64")) {
                LeafInput input = DeclarationPriorityCodec.decodeLeaf(StrictJson.canonical(row.get("request")));
                assertTrue(input.actorCharacterId().value().compareTo(StrictJson.UINT64_MAX) > 0);
                assertEquals(0, DeclarationObjectivePriority.priority(input).rank());
                assertEquals(BigInteger.ONE.shiftLeft(128).add(BigInteger.valueOf(51)), input.actorCharacterId().value());
            }
        }
        for (JsonNode row : golden().path("selection_cases")) {
            if (row.path("name").textValue().equals("beyond-signed64-subtraction")) {
                assertEquals(1, DeclarationObjectivePriority.preferredIndex(
                        DeclarationPriorityCodec.decodeSelection(StrictJson.canonical(row.get("request")))).orElseThrow());
            }
        }
    }

    @Test
    void domainCollectionsAreImmutableAndAssessmentPresenceRoundTrips() {
        ArrayList<BigInteger> titles = new ArrayList<>(List.of(BigInteger.ONE));
        Declaration declaration = new Declaration(JsonField.missing(), JsonField.missing(), JsonField.missing(),
                JsonField.of("claim_cb"), JsonField.missing(), JsonField.of(BigInteger.ONE),
                JsonField.of(titles), JsonField.of("native"));
        titles.clear();
        assertEquals(List.of(BigInteger.ONE), declaration.targetTitleIds().value());
        assertThrows(UnsupportedOperationException.class, () -> declaration.targetTitleIds().value().clear());
        SelectionInput absent = new SelectionInput(JsonField.nullValue(), List.of(declaration), JsonField.missing());
        SelectionInput explicitNull = new SelectionInput(JsonField.nullValue(), List.of(declaration), JsonField.nullValue());
        SelectionInput empty = new SelectionInput(JsonField.nullValue(), List.of(declaration), JsonField.of(List.of()));
        assertNotEquals(absent, explicitNull);
        assertNotEquals(explicitNull, empty);
        for (SelectionInput input : List.of(absent, explicitNull, empty)) {
            assertEquals(input, DeclarationPriorityCodec.decodeSelection(DeclarationPriorityCodec.encodeSelection(input)));
        }
    }

    private static LeafInput decode(String declaration) {
        return DeclarationPriorityCodec.decodeLeaf((LEAF_PREFIX + declaration + "}").getBytes(StandardCharsets.UTF_8));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = DeclarationObjectivePriorityTest.class.getResourceAsStream(
                "/declarationpriority/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("missing committed producer golden"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
