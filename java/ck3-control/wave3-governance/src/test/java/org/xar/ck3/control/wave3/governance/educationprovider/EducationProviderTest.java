package org.xar.ck3.control.wave3.governance.educationprovider;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.TreeMap;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Validation;
import static org.junit.jupiter.api.Assertions.*;

/** Default regression reads only the tracked actual original outputs; it never starts Python or a game. */
final class EducationProviderTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode fixture() throws IOException {
        try (InputStream input = EducationProviderTest.class.getResourceAsStream("/educationprovider/producer-consumer-golden.json.gz")) {
            assertNotNull(input, "actual original education-provider golden must be captured and tracked");
            try (GZIPInputStream gzip = new GZIPInputStream(input)) {
                byte[] bytes = gzip.readNBytes(768_001); assertTrue(bytes.length <= 768_000, "bounded original golden required");
                return JSON.readTree(bytes);
            }
        }
    }
    private static byte[] capturedInput(JsonNode item) {
        JsonNode wire = item.get("input_json");
        assertNotNull(wire, "one canonical original input is mandatory");
        assertTrue(wire.isTextual(), "captured input must be the original UTF8 JSON text");
        assertFalse(item.has("request"), "a re-encoded parallel request must not replace canonical input");
        return wire.textValue().getBytes(StandardCharsets.UTF_8);
    }
    private static ObjectNode base() throws IOException { return (ObjectNode) JSON.readTree(capturedInput(fixture().get("cases").get(0))); }
    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }
    private static JsonNode provider(ObjectNode request) { return request.get("value"); }

    @Test void actualOriginalValidatorCompleteAcceptedAndRejectedVectors() throws IOException {
        int accepted = 0, rejected = 0;
        for (JsonNode item : fixture().get("cases")) {
            if (item.get("accepted").booleanValue()) {
                assertEquals(item.get("expected"), JSON.readTree(EducationProviderConsumerPort.validateAndEncode(capturedInput(item))), item.get("name").textValue()); accepted++;
            } else { assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.validateAndEncode(capturedInput(item)), item.get("name").textValue()); rejected++; }
            if (item.get("name").textValue().equals("native_revision_float")) {
                assertTrue(new String(capturedInput(item), StandardCharsets.UTF_8).contains("\"native_revision\":100.0"), "negative float token must reach the real Java boundary unchanged");
            }
        }
        assertTrue(accepted >= 8); assertTrue(rejected >= 10);
    }
    @Test void registeredTypedProviderPortConsumesAllOriginalVectorsWithSeparateBounds() throws IOException {
        EducationProviderProjectionPort port = new EducationProviderProjectionPort();
        assertEquals(org.xar.ck3.control.contracts.projection.ProjectionOperation.EDUCATION_PROVIDER, port.operation());
        assertEquals(8_388_608, port.inputMaximumBytes()); assertEquals(65_536, port.outputMaximumBytes());
        for (JsonNode item : fixture().get("cases")) {
            if (item.get("name").textValue().equals("qualified_false")) {
                assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                        () -> port.project(port.decode(capturedInput(item))));
            }
            if (item.get("accepted").booleanValue()) {
                Validation validated = port.project(port.decode(capturedInput(item)));
                assertFalse(validated.sourceAdmissionGranted()); assertFalse(validated.actionAuthorityGranted());
                assertEquals(item.get("expected"), JSON.readTree(port.encode(validated)), item.get("name").textValue());
            } else { assertThrows(IllegalArgumentException.class, () -> port.project(port.decode(capturedInput(item))), item.get("name").textValue()); }
        }
    }
    @Test void actualOriginalProviderToDecisionToNeedsWholeOutput() throws IOException, NoSuchAlgorithmException {
        int count = 0; boolean noHeirLinked = false;
        for (JsonNode item : fixture().get("cases")) {
            if (item.has("needs_expected")) {
                JsonNode inputs = item.get("needs_inputs"); byte[] output = EducationProviderConsumerPort.composeNeeds(capturedInput(item), bytes(inputs.get("decision")), null, bytes(inputs.get("source")));
                byte[] canonical = canonical(JSON.readTree(output));
                assertEquals(item.get("needs_expected").get("bytes").intValue(), canonical.length);
                assertEquals(item.get("needs_expected").get("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical))); count++;
                if (item.get("name").textValue().equals("no_heir_empty")) { noHeirLinked = true; }
            }
        }
        assertTrue(count >= 5); assertTrue(noHeirLinked, "the accepted no-heir provider must retain its real original needs-consumer chain");
    }
    @Test void rawTokensRejectBooleanFloatAndStringIdentitiesBeforeAnyRewrite() throws IOException {
        String source = new String(bytes(base()), StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "100.0", "\"100\"")) {
            String changed = source.replaceFirst("\"native_revision\":100", "\"native_revision\":" + wrong);
            assertNotEquals(source, changed); assertTrue(changed.contains("\"native_revision\":" + wrong));
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(changed.getBytes(StandardCharsets.UTF_8)));
            assertTrue(error.getMessage().contains("integer token"), error.getMessage());
        }
    }
    @Test void unknownAuthorityRemainsNullAndNeverGrantsSourceAdmission() throws IOException {
        Validation result = EducationProviderConsumerPort.analyze(bytes(base()));
        assertFalse(result.sourceAdmissionGranted()); assertFalse(result.actionAuthorityGranted());
        assertNull(result.provider().rows().get(0).guardianFullId()); assertNull(result.provider().rows().get(0).guardianCultureParameter());
        for (String field : List.of("guardian_full_id", "guardian_culture_parameter", "rite_parameters", "education_type", "education_progress")) {
            ObjectNode request = base(); ((ObjectNode) provider(request).get("rows").get(0)).put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(request)));
        }
    }
    @Test void missingAndNullOptionalLeafRetainsUnknownEvenWithoutPrerequisiteObservations() throws IOException {
        ObjectNode request = base(); request.putNull("value").putNull("family_result").putNull("qualified").putNull("actor");
        assertEquals("null", new String(EducationProviderConsumerPort.validateAndEncode(bytes(request)), StandardCharsets.UTF_8));
        request.remove("value"); assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(request)));
    }
    @Test void stableFirstOccurrenceRawFull32AndImmutableGroups() throws IOException {
        Validation result = EducationProviderConsumerPort.analyze(bytes(base()));
        assertEquals(List.of(0, 2), result.expectedChildren().get(0).occurrenceIndices());
        assertEquals(0x8000_0033L, result.expectedChildren().get(0).childFullId());
        assertEquals(600, result.expectedChildren().get(1).childFullId());
        assertThrows(UnsupportedOperationException.class, () -> result.expectedChildren().add(result.expectedChildren().get(0)));
        assertThrows(UnsupportedOperationException.class, () -> result.provider().rows().get(0).occurrenceIndices().add(9));
    }
    @Test void sameQueryIdentityFrameAndOriginalQualificationRemainMandatory() throws IOException {
        for (String field : List.of("request_id", "native_revision", "date_raw", "played_character_full_id", "heir_character_full_id")) {
            ObjectNode request = base(); ObjectNode leaf = (ObjectNode) provider(request);
            if (field.equals("request_id")) { leaf.put(field, "other-request"); } else { leaf.put(field, leaf.get(field).longValue() + 1); }
            assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(request)));
        }
        ObjectNode unqualified = base(); unqualified.put("qualified", false);
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(unqualified)));
        ObjectNode alias = base(); alias.put("qualified", 1);
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(alias)));
    }
    @Test void actualProviderRoundTripPreservesCompleteKnownFieldContract() throws IOException {
        ObjectNode request = base(); byte[] output = EducationProviderConsumerPort.validateAndEncode(bytes(request));
        request.set("value", JSON.readTree(output)); assertArrayEquals(output, EducationProviderConsumerPort.validateAndEncode(bytes(request)));
        ObjectNode row = (ObjectNode) provider(request).get("rows").get(0); row.put("guardian_role_equivalence_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(request)));
    }
    @Test void providerBoundIsIndependentOfTheLargerFamilyEnvelope() throws IOException {
        ObjectNode request = base(); ((ObjectNode) request.get("family_result")).put("unconsumed_sdk_extension", "x".repeat(70_000));
        EducationProviderConsumerPort.analyze(bytes(request));
        ((ObjectNode) provider(request)).put("request_id", "x".repeat(66_000));
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(bytes(request)));
        assertTrue(error.getMessage().contains("65536"));
    }
    @Test void rawUnicodeDuplicateKeysTrailingJsonAndWrongShapeAreRejected() throws IOException {
        String source = new String(bytes(base()), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze((source + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(source.replaceFirst("\"schema\":", "\"schema\":\"duplicate\",\"schema\":").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> EducationProviderConsumerPort.analyze(new byte[EducationProviderCodec.REQUEST_LIMIT + 1]));
    }
    private static byte[] canonical(JsonNode value) throws IOException { return JSON.writeValueAsBytes(sorted(value)); }
    private static Object sorted(JsonNode value) {
        if (value.isObject()) { TreeMap<String, Object> result = new TreeMap<>(); value.properties().forEach(entry -> result.put(entry.getKey(), sorted(entry.getValue()))); return result; }
        if (value.isArray()) { List<Object> result = new ArrayList<>(); value.forEach(item -> result.add(sorted(item))); return result; }
        return value;
    }
}
