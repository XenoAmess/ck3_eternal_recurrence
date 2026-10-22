package org.xar.ck3.control.military.projectedcontact;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Scope;

final class ProjectedContactPolicyTest {
    private static final ObjectMapper WIRE = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private static JsonNode golden() throws IOException {
        try (InputStream input = ProjectedContactPolicyTest.class.getResourceAsStream("/projectedcontact/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("checked-in projected contact producer golden missing"); }
            // Entire corpus can exceed one request budget; each actual request retains the shared 64 KiB limit.
            return WIRE.readTree(input);
        }
    }

    private static ObjectNode input() throws IOException {
        return (ObjectNode) golden().get("cases").get(0).get("input").deepCopy();
    }

    private static byte[] wire(JsonNode value) throws IOException {
        // Preserve erroneous floating tokens until the production decoder actually rejects them.
        return WIRE.writeValueAsBytes(value);
    }

    @Test void actualProducerGoldenAllCases() throws IOException {
        JsonNode cases = golden().get("cases");
        assertEquals(30, cases.size());
        for (JsonNode item : cases) {
            byte[] request = wire(item.get("input"));
            JsonNode result = StrictJson.parse(ProjectedContactCodec.select(request));
            assertEquals(item.get("expected"), result, item.get("name").asText());
        }
    }

    @Test void scopeAndSelectionSerializationRoundTripRetainsNativeOrder() throws IOException {
        ProjectedContactCodec.Input value = ProjectedContactCodec.decode(wire(input()));
        Available available = (Available) ProjectedContactPolicy.select(value.snapshot(), value.queryRows(), value.request());
        Scope scope = available.projection();
        assertEquals(List.of(22, 21), scope.defenderArmyIds());
        assertEquals(scope, ProjectedContactCodec.decodeScope(StrictJson.parse(
                StrictJson.canonical(ProjectedContactCodec.encodeScope(scope)))));
        assertFalse(available.actualArrivalObserved()); assertFalse(available.futureContactAuthorized());
        assertTrue(available.incomingAttackerGeometryReady());
        assertThrows(UnsupportedOperationException.class, () -> scope.defenderArmyIds().add(99));
    }

    @Test void requestRejectsBooleanFloatingStringAndOutOfRangeIdentities() throws IOException {
        for (String token : List.of("true", "11.0", "\"11\"", "-1", "2147483648", "null")) {
            ObjectNode value = input();
            ((ObjectNode) value.get("request")).set("subject_army_id", WIRE.readTree(token));
            byte[] request = wire(value);
            assertTrue(new String(request, StandardCharsets.UTF_8).contains("\"subject_army_id\":" + token),
                    "negative token must reach production unchanged: " + token);
            assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(request), token);
        }
    }

    @Test void requiredNullableOwnerDistinguishesMissingAndNull() throws IOException {
        ObjectNode value = input(); ((ObjectNode) value.get("request")).remove("subject_owner_character_id");
        byte[] missing = wire(value);
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(missing));
        ((ObjectNode) value.get("request")).putNull("subject_owner_character_id");
        assertEquals(null, ProjectedContactCodec.decode(wire(value)).request().subjectOwnerCharacterId());
    }

    @Test void captureRejectsWrongNumericTypesAndOverflow() throws IOException {
        for (String token : List.of("true", "9.0", "\"9\"", "0", "18446744073709551616")) {
            ObjectNode value = input();
            ((ObjectNode) value.get("snapshot")).set("native_revision", WIRE.readTree(token));
            byte[] request = wire(value);
            assertTrue(new String(request, StandardCharsets.UTF_8).contains("\"native_revision\":" + token),
                    "negative token must reach production unchanged: " + token);
            assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(request), token);
        }
    }

    @Test void originalFloatBytesReachTheProductionIntegerGuard() throws IOException {
        String baseline = new String(wire(input()), StandardCharsets.UTF_8);
        String subjectFloat = baseline.replace("\"subject_army_id\":11", "\"subject_army_id\":11.0");
        assertTrue(subjectFloat.contains("\"subject_army_id\":11.0"));
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(
                subjectFloat.getBytes(StandardCharsets.UTF_8)));
        String revisionFloat = baseline.replace("\"native_revision\":9", "\"native_revision\":9.0");
        assertTrue(revisionFloat.contains("\"native_revision\":9.0"));
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(
                revisionFloat.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void strictJsonRejectsDuplicateUnknownRootAndInvalidUtf8() throws IOException {
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(
                "{\"snapshot\":{},\"snapshot\":{},\"query_rows\":[],\"request\":{}}".getBytes(StandardCharsets.UTF_8)));
        ObjectNode value = input(); value.put("unmigrated_alias", true);
        byte[] unknown = wire(value);
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(unknown));
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void scopeRejectsMissingRequiredNullableAndMalformedNativeMembership() throws IOException {
        ObjectNode input = input();
        ObjectNode scope = (ObjectNode) input.get("query_rows").get(0).get("result").get("projected_contact_scope");
        scope.remove("selected_current_combat_id");
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decodeScope(scope));
        scope.putNull("selected_current_combat_id"); scope.putArray("projected_defender_army_ids").add(11);
        assertThrows(ContractViolationException.class, () -> ProjectedContactCodec.decodeScope(scope));
    }

    @Test void canonicalQueryTokensPreservePublicSlotZeroAndRejectLeadingZeros() {
        assertTrue(ProjectedContactPolicy.parseStep("query-projected-contact-scope-v1-0-to-31-from-30").isPresent());
        for (String token : List.of("query-projected-contact-scope-v1-00-to-31-from-30",
                "query-projected-contact-scope-v1-11-to-031-from-30",
                "query-projected-contact-scope-v1-11-to-31-from-31",
                "query-projected-contact-scope-v1-2147483648-to-31-from-30",
                "query-projected-contact-scope-v1-١١-to-31-from-30")) {
            assertTrue(ProjectedContactPolicy.parseStep(token).isEmpty(), token);
        }
    }

    @Test void uint64DomainIsExactBeyondJavascriptSafeIntegers() throws IOException {
        ObjectNode value = input();
        BigInteger max = StrictJson.UINT64_MAX;
        ((ObjectNode) value.get("snapshot")).put("native_revision", max);
        ObjectNode result = (ObjectNode) value.get("query_rows").get(0).get("result");
        result.put("queried_native_revision", max);
        ((ObjectNode) result.get("projected_contact_scope")).put("snapshot_revision", max);
        JsonNode selected = StrictJson.parse(ProjectedContactCodec.select(wire(value)));
        assertEquals(max, selected.get("projection").get("snapshot_revision").bigIntegerValue());
    }
}
