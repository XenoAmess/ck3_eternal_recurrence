package org.xar.ck3.control.wave2.military.prewaradmission;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class OrdinaryPrewarAdmissionTest {
    @Test
    void originalProducerAndAllOriginalPytestConsumerCasesWereActuallyCaptured() throws IOException {
        JsonNode golden = golden();
        assertEquals(0, golden.path("original_pytest").path("exit_code").intValue());
        assertTrue(golden.path("original_pytest").path("tests").intValue() >= 30);
        assertEquals(0, golden.path("original_pytest").path("failures").intValue());
        assertEquals(0, golden.path("original_pytest").path("skipped").intValue());
        assertTrue(golden.path("cases").size() >= 50);
        for (JsonNode row : golden.path("cases")) {
            ObjectNode request = request(golden, row);
            if (row.path("wire_rejection").booleanValue()) {
                assertThrows(ContractViolationException.class, () -> PrewarAdmissionCodec.decodeProjected(request), name(row));
                continue;
            }
            var input = PrewarAdmissionCodec.decodeProjected(request);
            JsonNode actual = StrictJson.parse(OrdinaryPrewarAdmission.encodeResult(OrdinaryPrewarAdmission.assess(input)));
            JsonNode expected = row.path("expected");
            if (expected.has("diagnostic")) {
                assertTrue(actual.path("diagnostic").isTextual() && !actual.path("diagnostic").textValue().isEmpty(), name(row));
                ObjectNode actualStable = ((ObjectNode) actual).deepCopy();
                ObjectNode expectedStable = ((ObjectNode) expected).deepCopy();
                actualStable.remove("diagnostic"); expectedStable.remove("diagnostic");
                assertEquals(expectedStable, actualStable, name(row));
            } else {
                assertEquals(expected, actual, name(row));
            }
        }
    }

    @Test
    void allThreeActualPlannerPathsUseTheSameQualifiedForceResult() throws IOException {
        JsonNode golden = golden();
        int observedDeclarePaths = 0;
        for (JsonNode row : golden.path("cases")) {
            if (!row.has("actual_original_planner")) { continue; }
            boolean oldDeclared = row.path("actual_original_planner").path("decision").path("outcome").asText().equals("DECLARE");
            var result = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, row)));
            assertEquals(oldDeclared, result.declareAdmitted(), name(row));
            if (oldDeclared) { observedDeclarePaths++; }
        }
        assertEquals(3, observedDeclarePaths);
    }

    @Test
    void acceptedIntegerInputsRoundTripWithMissingNullAndEmptyPreserved() throws IOException {
        JsonNode golden = golden();
        for (JsonNode row : golden.path("cases")) {
            ObjectNode request = request(golden, row);
            if (row.path("wire_rejection").booleanValue() || containsFloating(request)) { continue; }
            var input = PrewarAdmissionCodec.decodeProjected(request);
            byte[] encoded = PrewarAdmissionCodec.encode(input);
            assertEquals(request, StrictJson.parse(encoded), name(row));
            assertEquals(input, PrewarAdmissionCodec.decode(encoded), name(row));
        }
        var absent = PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, "query-absent")));
        var nullable = PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, "query-null")));
        assertNotEquals(absent, nullable);
        assertEquals(absent.snapshot().value().query().presence(), PrewarAdmissionInput.Presence.MISSING);
        assertEquals(nullable.snapshot().value().query().presence(), PrewarAdmissionInput.Presence.NULL);
    }

    @Test
    void decimalAndExponentTokensReachTheStrictProductionEntryDirectly() throws IOException {
        String base = new String(StrictJson.canonical(golden().path("base_request")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "6.0", "6e0", "\"6\"")) {
            String raw = base.replace("\"revision\":6", "\"revision\":" + token);
            assertNotEquals(base, raw, "fixture revision token exists");
            assertThrows(ContractViolationException.class,
                    () -> PrewarAdmissionCodec.decode(raw.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String token : List.of("true", "29829.0", "2.9829e4", "\"29829\"")) {
            String raw = base.replace("\"character_id\":29829", "\"character_id\":" + token);
            assertNotEquals(base, raw, "fixture actor token exists");
            assertThrows(ContractViolationException.class,
                    () -> PrewarAdmissionCodec.decode(raw.getBytes(StandardCharsets.UTF_8)), token);
        }
    }

    @Test
    void malformedDomainFloatCannotBePromotedByJsonReserialization() throws IOException {
        JsonNode golden = golden();
        ObjectNode request = request(golden, find(golden, "floating-floor"));
        var input = PrewarAdmissionCodec.decodeProjected(request);
        assertTrue(input.snapshot().value().query().value().coverage().value().copy().get("actor_lower_soldiers").isFloatingPointNumber());
        var result = OrdinaryPrewarAdmission.assess(input);
        assertFalse(result.declareAdmitted());
        assertEquals(OrdinaryPrewarAdmission.Reason.FORCE_COALITION_COVERAGE_INVALID, result.reason());
        assertThrows(ContractViolationException.class, () -> PrewarAdmissionCodec.encode(input));
    }

    @Test
    void independentReceiptAndCompleteOwnerValidationCannotBeReplacedByShape() throws IOException {
        JsonNode golden = golden();
        for (String name : List.of("outer-receipt-wrong-epoch", "duplicate-owner", "duplicate-participant", "missing-enemy-owner",
                "ally-domain-incomplete", "mobilization-absent", "unproven-component-sum", "selected-title-mismatch")) {
            var result = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, name))));
            assertFalse(result.declareAdmitted(), name);
            assertEquals(OrdinaryPrewarAdmission.Reason.FORCE_COALITION_COVERAGE_INVALID, result.reason(), name);
            assertTrue(result.diagnostic().hasValue(), name);
        }
    }

    @Test
    void onlyAbsentQueryRequestsPrefetchAndPartialOrUnknownResultsAreNotReplayed() throws IOException {
        JsonNode golden = golden();
        for (String name : List.of("present-partial-no-requery", "present-failed-no-requery", "query-not-accepted",
                "domain-null", "missing-outer-episode", "receipt-extra-request-id")) {
            var result = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, name))));
            assertFalse(result.declareAdmitted(), name);
            assertEquals(null, result.requiredQuery(), name);
        }
        var absent = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, "query-absent"))));
        assertEquals("909-17-0", absent.requiredQuery().declarationId());
        assertEquals(BigInteger.valueOf(6), absent.requiredQuery().expectedRevision());
        assertEquals("v2", absent.requiredQuery().profile());
    }

    @Test
    void nullableEpisodeDoesNotMeanMissingOuterLeaseAndInputCopiesAreDetached() throws IOException {
        JsonNode golden = golden();
        for (String name : List.of("nullable-episode", "missing-snapshot-episode-known-null")) {
            var result = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, name))));
            assertTrue(result.declareAdmitted(), name);
        }
        var input = PrewarAdmissionCodec.decodeProjected(golden.path("base_request"));
        var copy = input.snapshot().value().query().value().coverage().value().copy();
        copy.put("actor_lower_soldiers", 0);
        assertTrue(OrdinaryPrewarAdmission.assess(input).declareAdmitted());
        assertThrows(UnsupportedOperationException.class, () -> input.snapshot().value().declarableWars().value().clear());
        assertThrows(UnsupportedOperationException.class, () -> input.declaration().targetTitleIds().value().clear());
    }

    @Test
    void requiredEnvelopeUnknownFieldsDuplicatesUtf8AndTrailingTokensAreRejected() {
        String valid = "{\"schema\":\"" + PrewarAdmissionCodec.SCHEMA + "\",\"snapshot\":null,\"declaration\":{}}";
        assertEquals(OrdinaryPrewarAdmission.Reason.CURRENT_SNAPSHOT_REQUIRED,
                OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decode(valid.getBytes(StandardCharsets.UTF_8))).reason());
        for (String raw : List.of("{}", valid + " {}", valid.replace("\"snapshot\":null", "\"snapshot\":null,\"snapshot\":{}"),
                valid.replace("\"declaration\":{}", "\"declaration\":{},\"force_risk_qualified\":true"),
                valid.replace(PrewarAdmissionCodec.SCHEMA, "wrong"))) {
            assertThrows(ContractViolationException.class, () -> PrewarAdmissionCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> PrewarAdmissionCodec.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void finalNativeCanSendIsRequiredEvenAfterTheForcePolicyQualified() throws IOException {
        JsonNode golden = golden();
        for (String name : List.of("final-can-send-false", "final-can-send-null")) {
            var result = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeProjected(request(golden, find(golden, name))));
            assertTrue(result.forceRiskQualified(), name);
            assertFalse(result.declareAdmitted(), name);
            assertEquals(OrdinaryPrewarAdmission.Status.UNKNOWN, result.status());
            assertEquals(OrdinaryPrewarAdmission.Reason.CURRENT_SELECTED_NATIVE_DECLARATION_LEGALITY_REQUIRED, result.reason());
        }
    }

    private static String name(JsonNode row) { return row.path("name").textValue(); }

    private static JsonNode golden() throws IOException {
        try (InputStream input = OrdinaryPrewarAdmissionTest.class.getResourceAsStream("/prewaradmission/original-producer-golden.json")) {
            if (input == null) { throw new IOException("missing actual original-producer golden; capture was not executed"); }
            return StrictJson.parse(input.readAllBytes());
        }
    }

    private static JsonNode find(JsonNode golden, String name) {
        for (JsonNode row : golden.path("cases")) { if (name(row).equals(name)) { return row; } }
        throw new IllegalArgumentException("missing actual producer case " + name);
    }

    private static ObjectNode request(JsonNode golden, JsonNode row) {
        ObjectNode request = ((ObjectNode) golden.path("base_request")).deepCopy();
        for (JsonNode patch : row.path("patches")) {
            JsonNode path = patch.path("path");
            ObjectNode owner = request;
            for (int index = 0; index < path.size() - 1; index++) { owner = (ObjectNode) owner.get(path.get(index).textValue()); }
            String key = path.get(path.size() - 1).textValue();
            if (patch.path("op").textValue().equals("remove")) { owner.remove(key); }
            else { owner.set(key, StrictJson.parse(patch.path("value_json").textValue().getBytes(StandardCharsets.UTF_8))); }
        }
        return request;
    }

    private static boolean containsFloating(JsonNode node) {
        if (node.isFloatingPointNumber()) { return true; }
        for (JsonNode child : node) { if (containsFloating(child)) { return true; } }
        return false;
    }
}
